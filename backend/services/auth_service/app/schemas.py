from __future__ import annotations

from typing import Any, Literal
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
    email: EmailStr | None = None
    phone_number: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole
    fpo_id: str | None = Field(default=None, max_length=100)
    invite_code: str | None = Field(default=None, max_length=100)
    consent_terms: bool = Field(default=False)

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


class SignupStartRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    phone_number: str = Field(..., min_length=10, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole
    fpo_id: str | None = None
    invite_code: str | None = None
    consent_terms: bool = Field(default=False)

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value: str) -> str:
        return normalize_role_value(value)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return str(value).strip().lower()

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        cleaned = "".join(ch for ch in str(value).strip() if ch.isdigit() or ch == "+")
        return cleaned


class SignupStartResponse(BaseModel):
    signup_session_id: UUID
    dev_otp: str | None = None


class SignupVerifyRequest(BaseModel):
    signup_session_id: UUID
    otp: str = Field(..., min_length=6, max_length=6)


class SignupVerifyResponse(BaseModel):
    signup_session_id: UUID
    verified: bool


class FarmerProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    phone_number: str | None = None
    email: EmailStr | None = None
    gender: str | None = None
    date_of_birth: str | None = None
    preferred_language: str | None = None
    aadhaar_last4: str | None = None
    kisan_pehchan_patra_document_url: str | None = None
    state_name: str | None = None
    district_name: str | None = None
    district_code: int | None = None
    block_name: str | None = None
    block_code: int | None = None
    village_name: str | None = None
    gram_panchayat: str | None = None
    pincode: str | None = None
    fpo_id: str | None = None
    farmer_type: str | None = None
    total_landholding_acres: float | None = None
    cultivated_area_acres: float | None = None
    primary_crop: str | None = None
    irrigation_status: str | None = None
    consent_location_use: bool | None = None
    consent_data_processing: bool | None = None
    consent_advisory_messages: bool | None = None
    consent_fpo_data_sharing: bool | None = None


class FpoProfileUpdateRequest(BaseModel):
    fpo_name: str | None = None
    registration_number: str | None = None
    registration_type: str | None = None
    date_of_registration: str | None = None
    promoted_by: str | None = None
    promoting_institution_name: str | None = None
    state_name: str | None = None
    district_name: str | None = None
    block_name: str | None = None
    block_code: int | None = None
    village_name: str | None = None
    pincode: str | None = None
    office_address: str | None = None
    contact_person_name: str | None = None
    contact_person_designation: str | None = None
    contact_phone: str | None = None
    alternate_phone: str | None = None
    contact_email: EmailStr | None = None
    main_commodities: list[str] | None = None
    member_count: int | None = None
    active_member_count: int | None = None
    services_provided: list[str] | None = None
    onboarding_status: str | None = None
    verification_status: str | None = None


class SignupCompleteRequest(BaseModel):
    signup_session_id: UUID
    role: UserRole
    profile: dict[str, Any] = Field(default_factory=dict)

class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=100)