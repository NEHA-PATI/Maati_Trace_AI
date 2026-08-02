from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from shared.db.postgres import engine

from services.profile_service.app.dependencies import (
    RequestContext,
)
from services.profile_service.app.errors import ProfileError
from services.profile_service.app.location_client import (
    validate_location,
)
from services.profile_service.app.repository import (
    create_fpo_with_membership,
    ensure_farmer_profile,
    get_farmer_by_id,
    get_farmer_by_user_id,
    get_fpo_by_id,
    get_fpo_memberships,
    list_fpo_farmers,
    record_profile_audit_event,
    update_farmer_profile,
    update_fpo_profile,
    update_user_onboarding_status,
    update_user_profile_projection,
)
from services.profile_service.app.schemas import (
    FarmerProfileResponse,
    FarmerProfileUpdate,
    FpoProfileResponse,
    FpoProfileSetupRequest,
    FpoProfileUpdate,
)

from services.profile_service.app.normalization import (
    is_pending_location_value,
    public_location_value,
)

FARMER_REQUIRED_FIELDS = (
    "full_name",
    "phone_number",
    "consent_data_processing",
)

FARMER_DISPLAY_FIELDS = (
    "full_name",
    "email",
    "phone_number",
    "gender",
    "date_of_birth",
    "preferred_language",
    "aadhaar_last4",
    "state_name",
    "district_name",
    "block_name",
    "block_code",
    "village_name",
    "gram_panchayat",
    "pincode",
    "farmer_type",
    "total_landholding_acres",
    "cultivated_area_acres",
    "primary_crop",
    "irrigation_status",
    "consent_location_use",
    "consent_data_processing",
    "consent_advisory_messages",
    "consent_fpo_data_sharing",
)

FPO_REQUIRED_FIELDS = (
    "fpo_name",
    "contact_person_name",
    "contact_phone",
    "contact_email",
)

FPO_DISPLAY_FIELDS = (
    "fpo_name",
    "registration_number",
    "registration_type",
    "date_of_registration",
    "promoted_by",
    "promoting_institution_name",
    "contact_person_name",
    "contact_person_designation",
    "contact_phone",
    "alternate_phone",
    "contact_email",
    "state_name",
    "district_name",
    "block_name",
    "block_code",
    "village_name",
    "gram_panchayat",
    "pincode",
    "office_address",
    "main_commodities",
    "member_count",
    "active_member_count",
    "services_provided",
)

FPO_WRITE_ROLES = {
    "owner",
    "admin",
    "manager",
}


def profile_progress(
    values: dict[str, Any],
    required_fields: tuple[str, ...],
    percentage_fields: tuple[str, ...] | None = None,
) -> tuple[bool, int, list[str]]:
    missing: list[str] = []
    fields_for_percentage = (
        percentage_fields
        or required_fields
    )

    location_fields = {
        "district_name",
        "block_name",
        "village_name",
    }

    for field in required_fields:
        value = values.get(field)

        if field.startswith("consent_"):
            if value is not True:
                missing.append(field)

            continue

        if field in location_fields:
            if is_pending_location_value(
                value
            ):
                missing.append(field)

            continue

        if value is None:
            missing.append(field)
            continue

        if (
            isinstance(value, str)
            and not value.strip()
        ):
            missing.append(field)

    completed_count = sum(
        0 if _field_is_missing(
            values,
            field,
        ) else 1
        for field in fields_for_percentage
    )

    percentage = round(
        completed_count
        / len(fields_for_percentage)
        * 100
    ) if fields_for_percentage else 100

    return (
        not missing,
        percentage,
        missing,
    )


def _field_is_missing(
    values: dict[str, Any],
    field: str,
) -> bool:
    value = values.get(field)

    if field.startswith("consent_"):
        return value is not True

    if field in {
        "district_name",
        "block_name",
        "village_name",
    }:
        return is_pending_location_value(
            value
        )

    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    if isinstance(value, list):
        return not value

    return False

def _public_farmer_profile(
    profile: dict[str, Any],
) -> dict[str, Any]:
    """
    Return only fields allowed by FarmerProfileResponse.

    This prevents repository-only fields from accidentally
    becoming part of the public API response.
    """

    public_profile = {
        field_name: profile.get(field_name)
        for field_name
        in FarmerProfileResponse.model_fields
    }

    public_profile["district_name"] = (
        public_location_value(
            profile.get("district_name")
        )
    )

    public_profile["block_name"] = (
        public_location_value(
            profile.get("block_name")
        )
    )

    public_profile["village_name"] = (
        public_location_value(
            profile.get("village_name")
        )
    )

    validated = (
        FarmerProfileResponse.model_validate(
            public_profile
        )
    )

    return validated.model_dump()


def _public_fpo_profile(
    profile: dict[str, Any],
) -> dict[str, Any]:
    public_profile = {
        field_name: profile.get(field_name)
        for field_name
        in FpoProfileResponse.model_fields
    }

    public_profile["main_commodities"] = (
        profile.get("main_commodities")
        or []
    )

    public_profile["services_provided"] = (
        profile.get("services_provided")
        or []
    )

    public_profile["district_name"] = (
        public_location_value(
            profile.get("district_name")
        )
    )

    public_profile["block_name"] = (
        public_location_value(
            profile.get("block_name")
        )
    )

    public_profile["village_name"] = (
        public_location_value(
            profile.get("village_name")
        )
    )

    validated = (
        FpoProfileResponse.model_validate(
            public_profile
        )
    )

    return validated.model_dump()


def farmer_profile_progress(
    values: dict[str, Any],
) -> tuple[bool, int, list[str]]:
    return profile_progress(
        values,
        FARMER_REQUIRED_FIELDS,
        FARMER_DISPLAY_FIELDS,
    )


def fpo_profile_progress(
    values: dict[str, Any],
) -> tuple[bool, int, list[str]]:
    return profile_progress(
        values,
        FPO_REQUIRED_FIELDS,
        FPO_DISPLAY_FIELDS,
    )


def _farmer_envelope(
    profile: dict[str, Any],
) -> dict[str, Any]:
    complete, percentage, missing = (
        farmer_profile_progress(profile)
    )

    return {
        "profile_type": "farmer",
        "onboarding_status": (
            "completed"
            if complete
            else "pending"
        ),
        "completion_percentage": (
            percentage
        ),
        "missing_fields": missing,
        "setup_required": False,
        "profile": _public_farmer_profile(
            profile
        ),
    }

def _fpo_envelope(
    profile: dict[str, Any] | None,
) -> dict[str, Any]:
    if profile is None:
        return {
            "profile_type": "fpo",
            "onboarding_status": "pending",
            "completion_percentage": 0,
            "missing_fields": list(
                FPO_REQUIRED_FIELDS
            ),
            "setup_required": True,
            "profile": None,
        }

    complete, percentage, missing = (
        fpo_profile_progress(profile)
    )

    return {
        "profile_type": "fpo",
        "onboarding_status": (
            "completed"
            if complete
            else "pending"
        ),
        "completion_percentage": percentage,
        "missing_fields": missing,
        "setup_required": False,
        "profile": _public_fpo_profile(
            profile
        ),
    }


def _select_fpo_membership(
    memberships: list[dict[str, Any]],
    fpo_context_id: UUID | None,
) -> dict[str, Any] | None:
    if not memberships:
        return None

    if fpo_context_id is not None:
        for membership in memberships:
            if str(membership["fpo_id"]) == str(
                fpo_context_id
            ):
                return membership

        raise ProfileError(
            "FPO_CONTEXT_FORBIDDEN",
            "You are not linked to the selected FPO.",
            403,
        )

    if len(memberships) > 1:
        raise ProfileError(
            "FPO_CONTEXT_REQUIRED",
            "Select an FPO context using the X-FPO-ID header.",
            409,
        )

    return memberships[0]


def get_my_profile(
    context: RequestContext,
) -> dict[str, Any]:
    principal = context.principal

    if principal.role == "farmer":
        try:
            with engine.begin() as conn:
                profile = get_farmer_by_user_id(
                    conn,
                    principal.user_id,
                    for_update=True,
                )

                if profile is None:
                    profile = ensure_farmer_profile(
                        conn,
                        principal.user_id,
                    )

                if profile is None:
                    raise ProfileError(
                        "FARMER_PROFILE_NOT_AVAILABLE",
                        "Your farmer profile could not be prepared.",
                        500,
                    )

            return _farmer_envelope(profile)

        except ProfileError:
            raise
        except SQLAlchemyError as exc:
            raise ProfileError(
                "FARMER_PROFILE_READ_FAILED",
                "Your farmer profile could not be loaded.",
                500,
                internal_message=str(exc),
            ) from exc

    if principal.role == "fpo":
        try:
            with engine.connect() as conn:
                memberships = get_fpo_memberships(
                    conn,
                    principal.user_id,
                )

                membership = _select_fpo_membership(
                    memberships,
                    context.fpo_context_id,
                )

                if membership is None:
                    return _fpo_envelope(None)

                profile = get_fpo_by_id(
                    conn,
                    membership["fpo_id"],
                )

                if profile is None:
                    return _fpo_envelope(None)

                profile["current_user_fpo_role"] = (
                    membership["fpo_role"]
                )

            return _fpo_envelope(profile)

        except ProfileError:
            raise
        except SQLAlchemyError as exc:
            raise ProfileError(
                "FPO_PROFILE_READ_FAILED",
                "Your FPO profile could not be loaded.",
                500,
                internal_message=str(exc),
            ) from exc

    raise ProfileError(
        "PROFILE_NOT_AVAILABLE_FOR_ROLE",
        "A profile is not available for this account role.",
        403,
    )


async def update_my_farmer_profile(
    context: RequestContext,
    payload: FarmerProfileUpdate,
) -> dict[str, Any]:
    principal = context.principal

    if principal.role != "farmer":
        raise ProfileError(
            "FARMER_ROLE_REQUIRED",
            "Only farmer accounts can update farmer profiles.",
            403,
        )

    changes = payload.model_dump(
        exclude_unset=True,
    )

    try:
        with engine.begin() as conn:
            existing = get_farmer_by_user_id(
                conn,
                principal.user_id,
                for_update=True,
            )

            if existing is None:
                existing = ensure_farmer_profile(
                    conn,
                    principal.user_id,
                )

            if existing is None:
                raise ProfileError(
                    "FARMER_PROFILE_NOT_AVAILABLE",
                    "Your farmer profile could not be prepared.",
                    500,
                )

        merged = {
            **existing,
            **changes,
        }

        location_fields = {
            "state_name",
            "district_name",
            "block_name",
            "block_code",
        }

        if location_fields.intersection(
            changes.keys()
        ):
            district_name_for_validation = (
                public_location_value(
                    merged.get("district_name")
                )
            )

            if not district_name_for_validation:
                raise ProfileError(
                    "DISTRICT_REQUIRED",
                    "Select a district before saving "
                    "location details.",
                    422,
                )

            location = await validate_location(
                state_name=(
                    merged.get("state_name")
                    or "Odisha"
                    ),
                district_name=(
                    district_name_for_validation
                    ),
                block_name=public_location_value(
                    merged.get("block_name")
                    ),
                block_code=merged.get(
                    "block_code"
                    ),
)

            merged["state_name"] = (
                location["state_name"]
            )
            merged["district_name"] = (
                location["district_name"]
            )
            merged["district_code"] = (
                location.get("district_code")
            )
            merged["block_name"] = (
                location.get("block_name")
            )
            merged["block_code"] = (
                location.get("block_code")
            )

        total_area = merged.get(
            "total_landholding_acres"
        )
        cultivated_area = merged.get(
            "cultivated_area_acres"
        )

        if (
            total_area is not None
            and cultivated_area is not None
            and cultivated_area > total_area
        ):
            raise ProfileError(
                "INVALID_CULTIVATED_AREA",
                "Cultivated area cannot exceed total landholding.",
                422,
            )

        complete, _, _ = (
            farmer_profile_progress(merged)
        )

        repository_values = {
            "full_name": merged["full_name"],
            "phone_number": merged.get(
                "phone_number"
            ),
            "gender": merged.get("gender"),
            "date_of_birth": merged.get(
                "date_of_birth"
            ),
            "preferred_language": (
                merged.get("preferred_language")
                or "en"
            ),
            "aadhaar_last4": merged.get(
                "aadhaar_last4"
            ),

            "state_name": (
                merged.get("state_name")
                or "Odisha"
            ),
            "district_name": merged.get(
                "district_name"
            ),
            "district_code": merged.get(
                "district_code"
            ),
            "block_name": merged.get(
                "block_name"
            ),
            "block_code": merged.get(
                "block_code"
            ),
            "village_name": merged.get(
                "village_name"
            ),
            "gram_panchayat": merged.get(
                "gram_panchayat"
            ),
            "pincode": merged.get("pincode"),

            "farmer_type": merged.get(
                "farmer_type"
            ),
            "total_landholding_acres": (
                merged.get(
                    "total_landholding_acres"
                )
            ),
            "cultivated_area_acres": (
                merged.get(
                    "cultivated_area_acres"
                )
            ),
            "primary_crop": merged.get(
                "primary_crop"
            ),
            "irrigation_status": merged.get(
                "irrigation_status"
            ),

            "consent_location_use": bool(
                merged.get(
                    "consent_location_use"
                )
            ),
            "consent_data_processing": bool(
                merged.get(
                    "consent_data_processing"
                )
            ),
            "consent_advisory_messages": bool(
                merged.get(
                    "consent_advisory_messages"
                )
            ),
            "consent_fpo_data_sharing": bool(
                merged.get(
                    "consent_fpo_data_sharing"
                )
            ),

            "profile_image_url": merged.get(
                "profile_image_url"
            ),
        }

        with engine.begin() as conn:
            locked = get_farmer_by_user_id(
                conn,
                principal.user_id,
                for_update=True,
            )

            if locked is None:
                raise ProfileError(
                    "FARMER_PROFILE_NOT_FOUND",
                    "Your farmer profile was not found.",
                    404,
                )

            updated = update_farmer_profile(
                conn,
                user_id=principal.user_id,
                values=repository_values,
                profile_complete=complete,
            )

            if updated is None:
                raise ProfileError(
                    "FARMER_PROFILE_UPDATE_FAILED",
                    "Your farmer profile could not be saved.",
                    500,
                )

            update_user_profile_projection(
                conn,
                user_id=principal.user_id,
                full_name=updated["full_name"],
                phone_number=updated.get(
                    "phone_number"
                ),
                profile_image_url=updated.get(
                    "profile_image_url"
                ),
                onboarding_status=(
                    "completed"
                    if complete
                    else "pending"
                ),
            )

            record_profile_audit_event(
                conn,
                entity_type="farmer",
                entity_id=updated["farmer_id"],
                subject_user_id=principal.user_id,
                actor_user_id=principal.user_id,
                event_type="farmer_profile_updated",
                changed_fields=list(
                    changes.keys()
                ),
                correlation_id=(
                    context.correlation_id
                ),
                ip_address=context.ip_address,
            )

        return _farmer_envelope(updated)

    except ProfileError:
        raise
    except IntegrityError as exc:
        raise ProfileError(
            "PROFILE_CONFLICT",
            "The phone number or profile details are already in use.",
            409,
            internal_message=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        raise ProfileError(
            "FARMER_PROFILE_UPDATE_FAILED",
            "Your farmer profile could not be saved.",
            500,
            internal_message=str(exc),
        ) from exc


async def setup_my_fpo_profile(
    context: RequestContext,
    payload: FpoProfileSetupRequest,
) -> dict[str, Any]:
    principal = context.principal

    if principal.role != "fpo":
        raise ProfileError(
            "FPO_ROLE_REQUIRED",
            "Only FPO accounts can create an FPO profile.",
            403,
        )

    if (
        not payload.district_name
        and (
            payload.block_name
            or payload.block_code
        )
    ):
        raise ProfileError(
            "LOCATION_CONTEXT_REQUIRED",
            "Select a district before selecting a block.",
            422,
        )

    if payload.district_name:
        location = await validate_location(
            state_name=payload.state_name,
            district_name=payload.district_name,
            block_name=payload.block_name,
            block_code=payload.block_code,
        )
    else:
        location = {
            "state_name": (
                payload.state_name
                or "Odisha"
            ),
            "district_name": "Pending",
            "district_code": None,
            "block_name": None,
            "block_code": None,
        }

    values = payload.model_dump()

    values["state_name"] = (
        location["state_name"]
    )
    values["district_name"] = (
        location["district_name"]
    )
    values["district_code"] = (
        location.get("district_code")
    )
    values["block_name"] = (
        location.get("block_name")
    )
    values["block_code"] = (
        location.get("block_code")
    )

    complete, _, _ = fpo_profile_progress(
        values
    )
    values["profile_complete"] = complete

    try:
        with engine.begin() as conn:
            memberships = get_fpo_memberships(
                conn,
                principal.user_id,
            )

            if memberships:
                raise ProfileError(
                    "FPO_PROFILE_ALREADY_EXISTS",
                    "This account is already linked to an FPO.",
                    409,
                )

            profile = create_fpo_with_membership(
                conn,
                user_id=principal.user_id,
                values=values,
            )

            update_user_onboarding_status(
                conn,
                user_id=principal.user_id,
                onboarding_status=(
                    "completed"
                    if complete
                    else "pending"
                ),
            )

            record_profile_audit_event(
                conn,
                entity_type="fpo",
                entity_id=profile["fpo_id"],
                subject_user_id=principal.user_id,
                actor_user_id=principal.user_id,
                event_type="fpo_profile_created",
                changed_fields=list(
                    payload.model_fields_set
                ),
                correlation_id=(
                    context.correlation_id
                ),
                ip_address=context.ip_address,
            )

        return _fpo_envelope(profile)

    except ProfileError:
        raise
    except IntegrityError as exc:
        raise ProfileError(
            "FPO_PROFILE_CONFLICT",
            "An FPO with this registration number already exists.",
            409,
            internal_message=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        raise ProfileError(
            "FPO_PROFILE_CREATE_FAILED",
            "The FPO profile could not be created.",
            500,
            internal_message=str(exc),
        ) from exc


async def update_my_fpo_profile(
    context: RequestContext,
    payload: FpoProfileUpdate,
) -> dict[str, Any]:
    principal = context.principal

    if principal.role != "fpo":
        raise ProfileError(
            "FPO_ROLE_REQUIRED",
            "Only FPO accounts can update an FPO profile.",
            403,
        )

    changes = payload.model_dump(
        exclude_unset=True,
    )

    try:
        with engine.connect() as conn:
            memberships = get_fpo_memberships(
                conn,
                principal.user_id,
            )

            membership = _select_fpo_membership(
                memberships,
                context.fpo_context_id,
            )

            if membership is None:
                raise ProfileError(
                    "FPO_PROFILE_NOT_FOUND",
                    "Create the FPO profile before updating it.",
                    404,
                )

            if membership["fpo_role"] not in (
                FPO_WRITE_ROLES
            ):
                raise ProfileError(
                    "FPO_WRITE_FORBIDDEN",
                    "Your FPO role cannot update this profile.",
                    403,
                )

            existing = get_fpo_by_id(
                conn,
                membership["fpo_id"],
            )

            if existing is None:
                raise ProfileError(
                    "FPO_PROFILE_NOT_FOUND",
                    "The FPO profile was not found.",
                    404,
                )

        if (
            "registration_number" in changes
            and existing.get(
                "verification_status"
            )
            not in {"pending", "rejected"}
        ):
            raise ProfileError(
                "REGISTRATION_NUMBER_LOCKED",
                "Registration number cannot be changed after verification review begins.",
                409,
            )

        merged = {
            **existing,
            **changes,
        }

        location_fields = {
            "state_name",
            "district_name",
            "block_name",
            "block_code",
        }

        if location_fields.intersection(
            changes.keys()
        ):
            district_name_for_validation = (
                public_location_value(
                    merged.get("district_name")
                )
            )

            if (
                not district_name_for_validation
                and (
                    merged.get("block_name")
                    or merged.get("block_code")
                )
            ):
                raise ProfileError(
                    "LOCATION_CONTEXT_REQUIRED",
                    "Select a district before selecting a block.",
                    422,
                )

            if district_name_for_validation:
                location = await validate_location(
                    state_name=(
                        merged.get("state_name")
                        or "Odisha"
                    ),
                    district_name=(
                        district_name_for_validation
                    ),
                    block_name=public_location_value(
                        merged.get("block_name")
                    ),
                    block_code=merged.get(
                        "block_code"
                    ),
                )
            else:
                location = {
                    "state_name": (
                        merged.get("state_name")
                        or "Odisha"
                    ),
                    "district_name": "Pending",
                    "district_code": None,
                    "block_name": None,
                    "block_code": None,
                }

            merged["state_name"] = (
                location["state_name"]
            )
            merged["district_name"] = (
                location["district_name"]
            )
            merged["district_code"] = (
                location.get("district_code")
            )
            merged["block_name"] = (
                location.get("block_name")
            )
            merged["block_code"] = (
                location.get("block_code")
            )

        member_count = merged.get(
            "member_count"
        )
        active_member_count = merged.get(
            "active_member_count"
        )

        if (
            member_count is not None
            and active_member_count is not None
            and active_member_count > member_count
        ):
            raise ProfileError(
                "INVALID_MEMBER_COUNTS",
                "Active member count cannot exceed member count.",
                422,
            )

        complete, _, _ = fpo_profile_progress(
            merged
        )

        repository_values = {
            field: merged.get(field)
            for field in (
                "fpo_name",
                "registration_number",
                "registration_type",
                "date_of_registration",
                "promoted_by",
                "promoting_institution_name",
                "contact_person_name",
                "contact_person_designation",
                "contact_phone",
                "alternate_phone",
                "contact_email",
                "state_name",
                "district_name",
                "district_code",
                "block_name",
                "block_code",
                "village_name",
                "gram_panchayat",
                "pincode",
                "office_address",
                "main_commodities",
                "member_count",
                "active_member_count",
                "services_provided",
                "profile_image_url",
            )
        }

        with engine.begin() as conn:
            updated = update_fpo_profile(
                conn,
                fpo_id=membership["fpo_id"],
                values=repository_values,
                profile_complete=complete,
            )

            if updated is None:
                raise ProfileError(
                    "FPO_PROFILE_UPDATE_FAILED",
                    "The FPO profile could not be saved.",
                    500,
                )

            updated[
                "current_user_fpo_role"
            ] = membership["fpo_role"]

            update_user_onboarding_status(
                conn,
                user_id=principal.user_id,
                onboarding_status=(
                    "completed"
                    if complete
                    else "pending"
                ),
            )

            record_profile_audit_event(
                conn,
                entity_type="fpo",
                entity_id=updated["fpo_id"],
                subject_user_id=principal.user_id,
                actor_user_id=principal.user_id,
                event_type="fpo_profile_updated",
                changed_fields=list(
                    changes.keys()
                ),
                correlation_id=(
                    context.correlation_id
                ),
                ip_address=context.ip_address,
            )

        return _fpo_envelope(updated)

    except ProfileError:
        raise
    except IntegrityError as exc:
        raise ProfileError(
            "FPO_PROFILE_CONFLICT",
            "The registration number or profile details are already in use.",
            409,
            internal_message=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        raise ProfileError(
            "FPO_PROFILE_UPDATE_FAILED",
            "The FPO profile could not be saved.",
            500,
            internal_message=str(exc),
        ) from exc


def export_my_profile(
    context: RequestContext,
) -> dict[str, Any]:
    envelope = get_my_profile(context)

    return {
        "exported_at": datetime.now(
            timezone.utc
        ),
        "profile_type": envelope[
            "profile_type"
        ],
        "data": envelope,
    }


def get_farmer_for_requester(
    context: RequestContext,
    farmer_id: UUID,
) -> dict[str, Any]:
    principal = context.principal

    with engine.connect() as conn:
        profile = get_farmer_by_id(
            conn,
            farmer_id,
        )

        if profile is None:
            raise ProfileError(
                "FARMER_PROFILE_NOT_FOUND",
                "Farmer profile was not found.",
                404,
            )

        if principal.role == "admin":
            return _farmer_envelope(profile)

        if (
            principal.role == "farmer"
            and str(profile["user_id"])
            == str(principal.user_id)
        ):
            return _farmer_envelope(profile)

        if principal.role == "fpo":
            memberships = get_fpo_memberships(
                conn,
                principal.user_id,
            )

            allowed_fpo_ids = {
                str(item["fpo_id"])
                for item in memberships
            }

            if (
                profile.get("fpo_id")
                and str(profile["fpo_id"])
                in allowed_fpo_ids
            ):
                return _farmer_envelope(
                    profile
                )

    raise ProfileError(
        "FARMER_PROFILE_FORBIDDEN",
        "You cannot access this farmer profile.",
        403,
    )


def get_fpo_for_requester(
    context: RequestContext,
    fpo_id: UUID,
) -> dict[str, Any]:
    principal = context.principal

    with engine.connect() as conn:
        profile = get_fpo_by_id(
            conn,
            fpo_id,
        )

        if profile is None:
            raise ProfileError(
                "FPO_PROFILE_NOT_FOUND",
                "FPO profile was not found.",
                404,
            )

        if principal.role == "admin":
            return _fpo_envelope(profile)

        if principal.role == "fpo":
            memberships = get_fpo_memberships(
                conn,
                principal.user_id,
            )

            for membership in memberships:
                if str(
                    membership["fpo_id"]
                ) == str(fpo_id):
                    profile[
                        "current_user_fpo_role"
                    ] = membership[
                        "fpo_role"
                    ]
                    return _fpo_envelope(
                        profile
                    )

        if (
            principal.role == "farmer"
        ):
            farmer = get_farmer_by_user_id(
                conn,
                principal.user_id,
            )

            if (
                farmer
                and farmer.get("fpo_id")
                and str(farmer["fpo_id"])
                == str(fpo_id)
            ):
                return _fpo_envelope(profile)

    raise ProfileError(
        "FPO_PROFILE_FORBIDDEN",
        "You cannot access this FPO profile.",
        403,
    )


def get_fpo_farmers_for_requester(
    context: RequestContext,
    fpo_id: UUID,
) -> list[dict[str, Any]]:
    principal = context.principal

    with engine.connect() as conn:
        fpo = get_fpo_by_id(
            conn,
            fpo_id,
        )

        if fpo is None:
            raise ProfileError(
                "FPO_PROFILE_NOT_FOUND",
                "FPO profile was not found.",
                404,
            )

        if principal.role == "admin":
            farmers = list_fpo_farmers(
                conn,
                fpo_id,
            )

            return [
                _public_farmer_profile(
                    profile
                )
                for profile in farmers
            ]

        if principal.role != "fpo":
            raise ProfileError(
                "FPO_FARMER_LIST_FORBIDDEN",
                "You cannot access this FPO's farmer list.",
                403,
            )

        memberships = get_fpo_memberships(
            conn,
            principal.user_id,
        )

        membership = next(
            (
                item
                for item in memberships
                if str(item["fpo_id"])
                == str(fpo_id)
            ),
            None,
        )

        if membership is None:
            raise ProfileError(
                "FPO_FARMER_LIST_FORBIDDEN",
                "You cannot access this FPO's farmer list.",
                403,
            )

        farmers = list_fpo_farmers(
            conn,
            fpo_id,
        )

        return [
            _public_farmer_profile(
                profile
            )
            for profile in farmers
        ]


def validate_farmer_internal(
    farmer_id: UUID,
) -> dict[str, Any]:
    with engine.connect() as conn:
        profile = get_farmer_by_id(
            conn,
            farmer_id,
        )

    if profile is None:
        raise ProfileError(
            "FARMER_PROFILE_NOT_FOUND",
            "Farmer profile was not found.",
            404,
        )

    complete, _, _ = (
        farmer_profile_progress(profile)
    )

    return {
        "farmer_id": profile["farmer_id"],
        "user_id": profile.get("user_id"),
        "fpo_id": profile.get("fpo_id"),
        "is_active": bool(
            profile["is_active"]
        ),
        "profile_complete": complete,
        "onboarding_status": (
            "completed"
            if complete
            else "pending"
        ),
    }


def validate_fpo_internal(
    fpo_id: UUID,
) -> dict[str, Any]:
    with engine.connect() as conn:
        profile = get_fpo_by_id(
            conn,
            fpo_id,
        )

    if profile is None:
        raise ProfileError(
            "FPO_PROFILE_NOT_FOUND",
            "FPO profile was not found.",
            404,
        )

    complete, _, _ = (
        fpo_profile_progress(profile)
    )

    return {
        "fpo_id": profile["fpo_id"],
        "is_active": bool(
            profile["is_active"]
        ),
        "verification_status": profile[
            "verification_status"
        ],
        "profile_complete": complete,
    }
