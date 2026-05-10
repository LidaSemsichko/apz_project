from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    instance: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    instance: str


class VerifyResponse(BaseModel):
    valid: bool
    user_id: int
    email: str
    instance: str


class HealthResponse(BaseModel):
    status: str
    service: str
    instance: str

class UserLookupResponse(BaseModel):
    id: int
    email: str
    username: str