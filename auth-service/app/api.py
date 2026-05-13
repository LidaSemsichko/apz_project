from fastapi import APIRouter, Header

from common.auth_client import extract_bearer_token
from app.models import (
    AuthResponse,
    HealthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
    VerifyResponse,
)
from app.service import (
    INSTANCE_NAME,
    get_all_users_service,
    get_current_user_profile,
    get_health_dependencies,
    get_user_by_username_service,
    login_user,
    logout_user,
    register_user,
    verify_token,
)


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    dependencies = get_health_dependencies()
    status = "ok" if all(value == "ok" for value in dependencies.values()) else "degraded"
    return {
        "status": status,
        "service": "auth-service",
        "instance": INSTANCE_NAME,
        "dependencies": dependencies,
    }


@router.post("/register", response_model=UserResponse)
def register(payload: RegisterRequest):
    user = register_user(
        email=payload.email,
        username=payload.username,
        password=payload.password,
    )

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "instance": INSTANCE_NAME,
    }


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    return login_user(
        email=payload.email,
        password=payload.password,
    )


@router.get("/verify", response_model=VerifyResponse)
def verify(authorization: str | None = Header(default=None)):
    token = extract_bearer_token(authorization)
    return verify_token(token)


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)):
    token = extract_bearer_token(authorization)
    return logout_user(token)


@router.get("/me")
def me(authorization: str | None = Header(default=None)):
    token = extract_bearer_token(authorization)
    return get_current_user_profile(token)


@router.get("/users")
def users(authorization: str | None = Header(default=None)):
    token = extract_bearer_token(authorization)
    verify_token(token)
    return get_all_users_service()


@router.get("/users/by-username/{username}")
def user_by_username(username: str, authorization: str | None = Header(default=None)):
    token = extract_bearer_token(authorization)
    verify_token(token)
    return get_user_by_username_service(username)
