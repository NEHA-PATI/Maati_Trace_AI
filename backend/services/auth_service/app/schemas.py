from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator

from services.auth_service.app.security import normalize_email, normalize_indian_mobile


UserRole = Literal["admin", "fpo", "farmer"]
FpoAccessStatus = Literal["pending", "approved", "rejected", "closed"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class HealthResponse(StrictModel):
    service: str
    status: Literal["live", "ready"]
    environment: str


class UserPublic(StrictModel):
    user_id: UUID
    full_name: str
    email: str | None = None
    phone_number: str | None = None
    role: UserRole
    is_active: bool
    is_verified: bool
    onboarding_status: str | None = None
    profile_image_url: str | None = None


class AuthResponse(StrictModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in_seconds: int
    user: UserPublic


class SignupStartRequest(StrictModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone_number: str
    password: str = Field(min_length=12, max_length=128)
    consent_terms: bool

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Full name is required")
        return cleaned

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("phone_number", mode="before")
    @classmethod
    def clean_phone(cls, value: str) -> str:
        return normalize_indian_mobile(value)

    @field_validator("consent_terms")
    @classmethod
    def require_consent(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Terms and privacy consent is required")
        return value


class SignupStartResponse(StrictModel):
    signup_session_id: UUID
    expires_in_seconds: int
    resend_available_in_seconds: int
    masked_email: str


class SignupResendRequest(StrictModel):
    signup_session_id: UUID


class SignupResendResponse(StrictModel):
    signup_session_id: UUID
    expires_in_seconds: int
    resend_available_in_seconds: int
    resends_remaining: int


class SignupVerifyRequest(StrictModel):
    signup_session_id: UUID
    otp: str = Field(pattern=r"^\d{6}$")


class SignupVerifyResponse(StrictModel):
    signup_session_id: UUID
    verified: bool


class SignupCancelRequest(StrictModel):
    signup_session_id: UUID
    reason: str = Field(default="user_changed_details", max_length=100)


class SignupCompleteRequest(StrictModel):
    signup_session_id: UUID


class LoginRequest(StrictModel):
    identifier: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    def resolved_identifier(self) -> str:
        cleaned = self.identifier.strip()
        if "@" in cleaned:
            return normalize_email(cleaned)
        return normalize_indian_mobile(cleaned)


class GoogleAuthRequest(StrictModel):
    id_token: str = Field(
        min_length=100,
        validation_alias=AliasChoices("id_token", "credential"),
    )


class PasswordForgotRequest(StrictModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value: str) -> str:
        return normalize_email(value)


class PasswordResetRequest(StrictModel):
    token: str = Field(min_length=40, max_length=512)
    new_password: str = Field(min_length=12, max_length=128)


class FpoAccessRequestCreate(StrictModel):
    organisation_name: str = Field(min_length=2, max_length=250)
    registration_number: str | None = Field(default=None, max_length=100)
    contact_person_name: str = Field(min_length=2, max_length=200)
    contact_email: EmailStr
    contact_phone: str
    state_name: str | None = Field(default="Odisha", max_length=100)
    district_name: str | None = Field(default=None, max_length=100)
    message: str | None = Field(default=None, max_length=2000)

    @field_validator("organisation_name", "contact_person_name")
    @classmethod
    def clean_names(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("registration_number", "state_name", "district_name", "message")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        return cleaned or None

    @field_validator("contact_email", mode="before")
    @classmethod
    def clean_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("contact_phone", mode="before")
    @classmethod
    def clean_phone(cls, value: str) -> str:
        return normalize_indian_mobile(value)


class FpoAccessRequestPublicResponse(StrictModel):
    request_id: UUID
    status: Literal["pending"]
    message: str
    correlation_id: str


class FpoAccessRequestAdminView(StrictModel):
    request_id: UUID
    organisation_name: str
    registration_number: str | None = None
    contact_person_name: str
    contact_email: str
    contact_phone: str
    state_name: str | None = None
    district_name: str | None = None
    message: str | None = None
    status: FpoAccessStatus
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    created_at: datetime
    updated_at: datetime


class FpoAccessRequestListResponse(StrictModel):
    items: list[FpoAccessRequestAdminView]
    total: int
    limit: int
    offset: int


class FpoAccessReviewRequest(StrictModel):
    status: Literal["approved", "rejected", "closed"]
    review_note: str | None = Field(default=None, max_length=2000)


class InvitationCreateRequest(StrictModel):
    email: EmailStr
    role: Literal["admin", "fpo"] = "fpo"
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value: str) -> str:
        return normalize_email(value)


class InvitationCreateResponse(StrictModel):
    invitation_id: UUID
    email: str
    role: Literal["admin", "fpo"]
    expires_at: datetime
    message: str


class InvitationValidationResponse(StrictModel):
    valid: bool
    masked_email: str | None = None
    role: Literal["admin", "fpo"] | None = None
    expires_at: datetime | None = None


class InvitationAcceptRequest(StrictModel):
    token: str = Field(min_length=40, max_length=512)
    full_name: str = Field(min_length=2, max_length=200)
    phone_number: str
    password: str = Field(min_length=12, max_length=128)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("phone_number", mode="before")
    @classmethod
    def clean_phone(cls, value: str) -> str:
        return normalize_indian_mobile(value)


class MessageResponse(StrictModel):
    message: str
    correlation_id: str