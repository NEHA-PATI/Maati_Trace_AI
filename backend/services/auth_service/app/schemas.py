from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


UserRole = Literal["admin", "fpo", "farmer"]


def normalize_role_value(value: str) -> str:
    cleaned = str(value or "").strip().lower()

    role_aliases = {
        "admin": "admin",
        "administrator": "admin",
        "fpo": "fpo",
        "fpo_admin": "fpo",
        "fpo_manager": "fpo",
        "farmer": "farmer",
        "krushak": "farmer",
    }

    return role_aliases.get(cleaned, cleaned)


class HealthResponse(BaseModel):
    service: str
    status: Literal["live", "ready"]
    environment: str


class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    phone_number: str | None = Field(default=None, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value: str) -> str:
        return normalize_role_value(value)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return str(value or "").strip().lower()

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = "".join(ch for ch in str(value).strip() if ch.isdigit() or ch == "+")
        return cleaned or None


class LoginRequest(BaseModel):
    identifier: str | None = Field(default=None, min_length=3, max_length=200)
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, max_length=20)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return str(value).strip().lower()

    @field_validator("identifier", mode="before")
    @classmethod
    def normalize_identifier(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = "".join(ch for ch in str(value).strip() if ch.isdigit() or ch == "+")
        return cleaned or None

    def resolved_identifier(self) -> str:
        if self.identifier:
            return self.identifier.strip()
        if self.email:
            return str(self.email).strip().lower()
        if self.phone_number:
            return self.phone_number.strip()

        raise ValueError("identifier, email, or phone_number is required")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20)


class UserPublic(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    phone_number: str | None
    role: UserRole
    is_active: bool
    is_verified: bool


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserPublic