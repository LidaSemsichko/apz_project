from fastapi import APIRouter, Header, HTTPException, status

from app.models import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
    VerifyResponse,
    HealthResponse
)
from app.service import (
    register_user,
    login_user,
    verify_token,
    logout_user,
    INSTANCE_NAME,
    get_current_user_profile,
    get_user_by_username_service,
    get_all_users_service
)


router = APIRouter()


def extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing"
        )

    parts = authorization.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    return parts[1]


@router.get("/health", response_model=HealthResponse)
def health():
    return {
        "status": "ok",
        "service": "auth-service",
        "instance": INSTANCE_NAME
    }


@router.post("/register", response_model=UserResponse)
def register(payload: RegisterRequest):
    user = register_user(
        email=payload.email,
        username=payload.username,
        password=payload.password
    )

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "instance": INSTANCE_NAME
    }


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    return login_user(
        email=payload.email,
        password=payload.password
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
def users():
    return get_all_users_service()


@router.get("/users/by-username/{username}")
def user_by_username(username: str):
    return get_user_by_username_service(username)