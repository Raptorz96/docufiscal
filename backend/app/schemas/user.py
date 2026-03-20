"""User-related Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, field_validator


class UserCreate(BaseModel):
    """Schema for user creation request."""
    email: EmailStr
    password: str
    nome: str
    cognome: str


class UserLogin(BaseModel):
    """Schema for user login request."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nome: str
    cognome: str
    role: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str


class UserUpdate(BaseModel):
    """Schema for user profile update. All fields optional — only non-None are applied."""
    nome: str | None = None
    cognome: str | None = None
    email: EmailStr | None = None

    @field_validator('nome', 'cognome')
    @classmethod
    def not_empty(cls, v: str | None) -> str | None:
        if v is not None and v.strip() == '':
            raise ValueError('Il campo non può essere vuoto')
        return v


class PasswordChange(BaseModel):
    """Schema for password change. Length validation is in the route handler (→ 400)."""
    current_password: str
    new_password: str