from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.user import RoleEnum


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: RoleEnum
    user_id: int
    full_name: str
    roll_number: Optional[str] = None
    employee_id: Optional[str] = None


class TokenPayload(BaseModel):
    sub: str  # user email
    user_id: int
    role: RoleEnum
    exp: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: RoleEnum
    phone: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: RoleEnum
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
