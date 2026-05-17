import os
import uuid
from datetime import datetime, timedelta, timezone

import redis
from redis.sentinel import Sentinel
from jose import JWTError, jwt
from passlib.context import CryptContext

from common.errors import ConflictError, NotFoundError, UnauthorizedError
from app.repository import (
    create_user,
    get_all_users,
    get_database_health,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
)


JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = int(os.getenv("TOKEN_TTL_SECONDS", "3600"))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis-master:6379/0")
REDIS_SENTINEL_HOSTS = os.getenv("REDIS_SENTINEL_HOSTS", "")
REDIS_MASTER_NAME = os.getenv("REDIS_MASTER_NAME", "mymaster")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "auth-service")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_redis_sentinel = None
_redis_direct_client = None


def _parse_sentinel_hosts(raw: str):
    pairs = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        host, _, port = token.partition(":")
        pairs.append((host, int(port or 26379)))
    return pairs


def get_redis_client():
    """Return a Redis client. Uses a Sentinel-managed master if REDIS_SENTINEL_HOSTS
    is set, otherwise falls back to a direct connection (legacy mode for local dev).

    Sentinel mode transparently re-resolves the current master on every call,
    so an in-flight failover only costs a couple of retries - not a restart.
    """
    global _redis_sentinel, _redis_direct_client

    if REDIS_SENTINEL_HOSTS:
        if _redis_sentinel is None:
            _redis_sentinel = Sentinel(
                _parse_sentinel_hosts(REDIS_SENTINEL_HOSTS),
                socket_timeout=1.0,
                socket_connect_timeout=1.0,
            )
        return _redis_sentinel.master_for(
            REDIS_MASTER_NAME,
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
            db=REDIS_DB,
            decode_responses=True,
        )

    if _redis_direct_client is None:
        _redis_direct_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_direct_client


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def register_user(email: str, username: str, password: str):
    if get_user_by_email(email):
        raise ConflictError("User with this email already exists")

    if get_user_by_username(username):
        raise ConflictError("User with this username already exists")

    password_hash = hash_password(password)
    return create_user(email=email, username=username, password_hash=password_hash)


def create_access_token(user_id: int, email: str) -> str:
    token_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=TOKEN_TTL_SECONDS)

    payload = {
        "sub": str(user_id),
        "email": email,
        "jti": token_id,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    redis_key = f"auth_token:{token_id}"
    get_redis_client().setex(redis_key, TOKEN_TTL_SECONDS, str(user_id))

    return token


def login_user(email: str, password: str):
    user = get_user_by_email(email)

    if not user or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")

    token = create_access_token(user.id, user.email)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "instance": INSTANCE_NAME,
    }


def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
        email = payload.get("email")
        token_id = payload.get("jti")

        if not token_id:
            raise UnauthorizedError("Invalid token")

        redis_key = f"auth_token:{token_id}"
        stored_user_id = get_redis_client().get(redis_key)

        if stored_user_id is None:
            raise UnauthorizedError("Token is expired or logged out")

        if stored_user_id != str(user_id):
            raise UnauthorizedError("Token user mismatch")

        user = get_user_by_id(user_id)
        if not user:
            raise UnauthorizedError("User not found")

        return {
            "valid": True,
            "user_id": user_id,
            "email": email,
            "instance": INSTANCE_NAME,
        }

    except JWTError as error:
        raise UnauthorizedError("Invalid or expired token") from error


def logout_user(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        token_id = payload.get("jti")

        if token_id:
            redis_key = f"auth_token:{token_id}"
            get_redis_client().delete(redis_key)

        return {
            "message": "Logged out successfully",
            "instance": INSTANCE_NAME,
        }

    except JWTError as error:
        raise UnauthorizedError("Invalid token") from error


def get_current_user_profile(token: str):
    data = verify_token(token)
    user = get_user_by_id(data["user_id"])

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "instance": INSTANCE_NAME,
    }


def get_user_by_username_service(username: str):
    user = get_user_by_username(username)

    if not user:
        raise NotFoundError("User not found")

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
    }


def get_all_users_service():
    users = get_all_users()

    return [
        {
            "id": user.id,
            "email": user.email,
            "username": user.username,
        }
        for user in users
    ]


def get_health_dependencies():
    dependencies = {
        "postgres": get_database_health(),
        "redis": "unavailable",
    }

    try:
        get_redis_client().ping()
        dependencies["redis"] = "ok"
        if REDIS_SENTINEL_HOSTS and _redis_sentinel is not None:
            try:
                host, port = _redis_sentinel.discover_master(REDIS_MASTER_NAME)
                dependencies["redis_master"] = f"{host}:{port}"
                dependencies["redis_mode"] = "sentinel"
            except Exception:
                dependencies["redis_mode"] = "sentinel"
        else:
            dependencies["redis_mode"] = "direct"
    except Exception:
        dependencies["redis"] = "unavailable"

    return dependencies
