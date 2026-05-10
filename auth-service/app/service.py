import os
import uuid
from datetime import datetime, timedelta, timezone

import redis
from fastapi import HTTPException, status
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.repository import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    get_all_users
)


JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = int(os.getenv("TOKEN_TTL_SECONDS", "3600"))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "auth-service")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def register_user(email: str, username: str, password: str):
    existing_user = get_user_by_email(email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )

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
        "exp": int(expires_at.timestamp())
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    redis_key = f"auth_token:{token_id}"
    redis_client.setex(redis_key, TOKEN_TTL_SECONDS, str(user_id))

    return token


def login_user(email: str, password: str):
    user = get_user_by_email(email)

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token(user.id, user.email)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "instance": INSTANCE_NAME
    }


def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
        email = payload.get("email")
        token_id = payload.get("jti")

        if not token_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        redis_key = f"auth_token:{token_id}"
        stored_user_id = redis_client.get(redis_key)

        if stored_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is expired or logged out"
            )

        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return {
            "valid": True,
            "user_id": user_id,
            "email": email,
            "instance": INSTANCE_NAME
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


def logout_user(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        token_id = payload.get("jti")

        if token_id:
            redis_key = f"auth_token:{token_id}"
            redis_client.delete(redis_key)

        return {
            "message": "Logged out successfully",
            "instance": INSTANCE_NAME
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    


def get_current_user_profile(token: str):
    data = verify_token(token)
    user = get_user_by_id(data["user_id"])

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "instance": INSTANCE_NAME
    }


def get_user_by_username_service(username: str):
    user = get_user_by_username(username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username
    }


def get_all_users_service():
    users = get_all_users()

    return [
        {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
        for user in users
    ]