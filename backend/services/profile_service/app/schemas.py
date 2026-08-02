from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from services.profile_service.app.normalization import (
    normalize_indian_mobile,
    normalize_pincode,
    normalize_text,
    normalize_text_list,
)


UserRole = Literal["admin", "fpo", "farmer"]
FpoRole = Literal[
    "owner",
    "admin",
    "manager",
    "analyst",
    "viewer",
]
VerificationStatus = Literal[
    "pending",
    "under_review",
    "verified",
    "rejected",
    "suspended",
]
KycStatus = Literal[
    "pending",
    "under_review",
    "verified",
    "rejected",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class HealthResponse(StrictModel):
    service: str
    status: Literal["live", "ready"]
    environment: str


class AuthenticatedUser(StrictModel):
    user_id: UUID
    full_name: str
    email: EmailStr | None = None
    phone_number: str | None = None
    role: UserRole
    is_active: bool
    is_verified: bool
    onboarding_status: str | None = None
    profile_image_url: str | None = None


class FarmerProfileUpdate(StrictModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    phone_number: str | None = None
    gender: Literal[
        "male",
        "female",
        "other",
        "prefer_not_to_say",
    ] | None = None
    date_of_birth: date | None = None
    preferred_language: Literal[
        "en",
        "hi",
        "or",
    ] | None = None
    aadhaar_last4: str | None = Field(
        default=None,
        pattern=r"^[0-9]{4}$",
    )

    state_name: str | None = Field(
        default=None,
        max_length=100,
    )
    district_name: str | None = Field(
        default=None,
        max_length=100,
    )
    block_name: str | None = Field(
        default=None,
        max_length=100,
    )
    block_code: int | None = Field(
        default=None,
        ge=1,
    )
    village_name: str | None = Field(
        default=None,
        max_length=150,
    )
    gram_panchayat: str | None = Field(
        default=None,
        max_length=150,
    )
    pincode: str | None = None

    farmer_type: str | None = Field(
        default=None,
        max_length=50,
    )
    total_landholding_acres: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=4,
    )
    cultivated_area_acres: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=4,
    )
    primary_crop: str | None = Field(
        default=None,
        max_length=100,
    )
    irrigation_status: str | None = Field(
        default=None,
        max_length=50,
    )

    consent_location_use: bool | None = None
    consent_data_processing: bool | None = None
    consent_advisory_messages: bool | None = None
    consent_fpo_data_sharing: bool | None = None

    profile_image_url: str | None = Field(
        default=None,
        max_length=2000,
    )

    @field_validator(
        "full_name",
        "state_name",
        "district_name",
        "block_name",
        "village_name",
        "gram_panchayat",
        "farmer_type",
        "primary_crop",
        "irrigation_status",
        "profile_image_url",
    )
    @classmethod
    def clean_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_text(value)

    @field_validator(
        "phone_number",
        mode="before",
    )
    @classmethod
    def clean_phone(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_indian_mobile(value)

    @field_validator(
        "pincode",
        mode="before",
    )
    @classmethod
    def clean_pincode(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_pincode(value)

    @field_validator("date_of_birth")
    @classmethod
    def validate_birth_date(
        cls,
        value: date | None,
    ) -> date | None:
        if value is not None and value > date.today():
            raise ValueError(
                "Date of birth cannot be in the future."
            )

        return value

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError(
                "At least one profile field must be supplied."
            )

        if (
            self.total_landholding_acres is not None
            and self.cultivated_area_acres is not None
            and self.cultivated_area_acres
            > self.total_landholding_acres
        ):
            raise ValueError(
                "Cultivated area cannot exceed total landholding."
            )

        return self


class FarmerProfileResponse(StrictModel):
    farmer_id: UUID
    user_id: UUID
    fpo_id: UUID | None = None

    full_name: str
    email: EmailStr | None = None
    phone_number: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    preferred_language: str

    aadhaar_last4: str | None = None
    kyc_status: KycStatus

    state_name: str
    district_name: str | None = None
    district_code: int | None = None
    block_name: str | None = None
    block_code: int | None = None
    village_name: str | None = None
    gram_panchayat: str | None = None
    pincode: str | None = None

    farmer_type: str | None = None
    total_landholding_acres: Decimal | None = None
    cultivated_area_acres: Decimal | None = None
    primary_crop: str | None = None
    irrigation_status: str | None = None

    consent_location_use: bool
    consent_data_processing: bool
    consent_advisory_messages: bool
    consent_fpo_data_sharing: bool

    profile_image_url: str | None = None
    is_active: bool
    onboarding_completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    profile_version: int


class FpoProfileSetupRequest(StrictModel):
    fpo_name: str = Field(
        min_length=2,
        max_length=200,
    )
    registration_number: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    registration_type: str | None = Field(
        default=None,
        max_length=100,
    )
    date_of_registration: date | None = None
    promoted_by: str | None = Field(
        default=None,
        max_length=200,
    )
    promoting_institution_name: str | None = Field(
        default=None,
        max_length=200,
    )

    contact_person_name: str = Field(
        min_length=2,
        max_length=200,
    )
    contact_person_designation: str | None = Field(
        default=None,
        max_length=100,
    )
    contact_phone: str
    alternate_phone: str | None = None
    contact_email: EmailStr

    state_name: str = Field(
        default="Odisha",
        max_length=100,
    )
    district_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    block_name: str | None = Field(
        default=None,
        max_length=100,
    )
    block_code: int | None = Field(
        default=None,
        ge=1,
    )
    village_name: str | None = Field(
        default=None,
        max_length=150,
    )
    gram_panchayat: str | None = Field(
        default=None,
        max_length=150,
    )
    pincode: str | None = None
    office_address: str | None = Field(
        default=None,
        min_length=5,
        max_length=1000,
    )

    main_commodities: list[str] = Field(
        default_factory=list,
        max_length=50,
    )
    member_count: int | None = Field(
        default=None,
        ge=0,
    )
    active_member_count: int | None = Field(
        default=None,
        ge=0,
    )
    services_provided: list[str] = Field(
        default_factory=list,
        max_length=50,
    )
    profile_image_url: str | None = Field(
        default=None,
        max_length=2000,
    )

    @field_validator(
        "fpo_name",
        "registration_number",
        "registration_type",
        "promoted_by",
        "promoting_institution_name",
        "contact_person_name",
        "contact_person_designation",
        "state_name",
        "district_name",
        "block_name",
        "village_name",
        "gram_panchayat",
        "office_address",
        "profile_image_url",
        mode="before",
    )
    @classmethod
    def clean_text(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_text(value)

    @field_validator(
        "contact_phone",
        "alternate_phone",
        mode="before",
    )
    @classmethod
    def clean_phone(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_indian_mobile(value)

    @field_validator(
        "pincode",
        mode="before",
    )
    @classmethod
    def clean_pincode(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_pincode(value)

    @field_validator(
        "main_commodities",
        "services_provided",
        mode="before",
    )
    @classmethod
    def clean_lists(cls, value):
        if value is None:
            return []

        if isinstance(value, str):
            value = value.split(",")

        return normalize_text_list(value)

    @model_validator(mode="after")
    def validate_counts(self):
        if (
            self.member_count is not None
            and self.active_member_count is not None
            and self.active_member_count
            > self.member_count
        ):
            raise ValueError(
                "Active member count cannot exceed member count."
            )

        return self


class FpoProfileUpdate(FpoProfileSetupRequest):
    fpo_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    registration_number: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    contact_person_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    district_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    office_address: str | None = Field(
        default=None,
        min_length=5,
        max_length=1000,
    )

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError(
                "At least one profile field must be supplied."
            )

        if (
            self.member_count is not None
            and self.active_member_count is not None
            and self.active_member_count
            > self.member_count
        ):
            raise ValueError(
                "Active member count cannot exceed member count."
            )

        return self


class FpoProfileResponse(StrictModel):
    fpo_id: UUID
    fpo_name: str
    registration_number: str | None = None
    registration_type: str | None = None
    date_of_registration: date | None = None
    promoted_by: str | None = None
    promoting_institution_name: str | None = None

    contact_person_name: str | None = None
    contact_person_designation: str | None = None
    contact_phone: str | None = None
    alternate_phone: str | None = None
    contact_email: EmailStr | None = None

    state_name: str
    district_name: str | None = None
    district_code: int | None = None
    block_name: str | None = None
    block_code: int | None = None
    village_name: str | None = None
    gram_panchayat: str | None = None
    pincode: str | None = None
    office_address: str | None = None

    main_commodities: list[str]
    member_count: int | None = None
    active_member_count: int | None = None
    services_provided: list[str]

    verification_status: VerificationStatus
    profile_image_url: str | None = None
    is_active: bool
    onboarding_completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    profile_version: int
    current_user_fpo_role: str | None = None


class FarmerProfileEnvelope(StrictModel):
    profile_type: Literal["farmer"] = "farmer"
    onboarding_status: Literal[
        "pending",
        "completed",
    ]
    completion_percentage: int = Field(
        ge=0,
        le=100,
    )
    missing_fields: list[str]
    setup_required: bool = False
    profile: FarmerProfileResponse


class FpoProfileEnvelope(StrictModel):
    profile_type: Literal["fpo"] = "fpo"
    onboarding_status: Literal[
        "pending",
        "completed",
    ]
    completion_percentage: int = Field(
        ge=0,
        le=100,
    )
    missing_fields: list[str]
    setup_required: bool
    profile: FpoProfileResponse | None = None


ProfileEnvelope = Annotated[
    FarmerProfileEnvelope | FpoProfileEnvelope,
    Field(discriminator="profile_type"),
]


class ProfileExportResponse(StrictModel):
    exported_at: datetime
    profile_type: Literal["farmer", "fpo"]
    data: dict[str, Any]


class FarmerValidationResponse(StrictModel):
    farmer_id: UUID
    user_id: UUID | None = None
    fpo_id: UUID | None = None
    is_active: bool
    profile_complete: bool
    onboarding_status: str


class FpoValidationResponse(StrictModel):
    fpo_id: UUID
    is_active: bool
    verification_status: str
    profile_complete: bool
