from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from services.farm_registry_service.app import external_clients, profile_client, repository
from services.farm_registry_service.app.area_calculator import (
    FarmGeometryError,
    calculate_area_acres,
)
from services.farm_registry_service.app.dependencies import RequestContext
from services.farm_registry_service.app.errors import (
    FarmRegistryError,
    FarmRegistryRepositoryError,
)
from services.farm_registry_service.app.schemas import FarmRegisterRequest


@dataclass(frozen=True)
class ActorScope:
    role: str
    user_id: UUID
    farmer_id: UUID | None = None
    fpo_id: UUID | None = None
    fpo_role: str | None = None
    onboarding_status: str | None = None


def _repository_failure(exc: FarmRegistryRepositoryError) -> FarmRegistryError:
    return FarmRegistryError(
        exc.code,
        exc.message,
        exc.status_code,
        internal_message=exc.internal_message,
    )


def _unwrap_profile(envelope: dict[str, Any], expected_type: str) -> dict[str, Any]:
    if envelope.get("profile_type") != expected_type or not envelope.get("profile"):
        raise FarmRegistryError(
            "PROFILE_REQUIRED",
            f"Complete your {expected_type} profile before managing farms.",
            409,
        )
    return envelope["profile"]


def resolve_actor(context: RequestContext) -> ActorScope:
    principal = context.principal
    role = principal.role.strip().lower()

    if not principal.is_active:
        raise FarmRegistryError("ACCOUNT_INACTIVE", "This account is inactive.", 403)

    if role == "admin":
        return ActorScope(
            role="admin",
            user_id=principal.user_id,
            onboarding_status=principal.onboarding_status,
        )

    if role not in {"farmer", "fpo"}:
        raise FarmRegistryError(
            "ROLE_NOT_SUPPORTED",
            "This account role cannot manage farms.",
            403,
        )

    envelope = profile_client.get_my_profile(
        authorization=context.authorization,
        correlation_id=context.correlation_id,
        fpo_context_id=context.fpo_context_id,
    )

    if role == "farmer":
        profile = _unwrap_profile(envelope, "farmer")
        if envelope.get("onboarding_status") != "completed":
            raise FarmRegistryError(
                "FARMER_PROFILE_INCOMPLETE",
                "Complete your farmer profile before managing farms.",
                409,
            )
        if not profile.get("is_active", True):
            raise FarmRegistryError("FARMER_PROFILE_INACTIVE", "Your farmer profile is inactive.", 403)
        return ActorScope(
            role="farmer",
            user_id=principal.user_id,
            farmer_id=UUID(str(profile["farmer_id"])),
            fpo_id=UUID(str(profile["fpo_id"])) if profile.get("fpo_id") else None,
            onboarding_status=envelope.get("onboarding_status"),
        )

    profile = _unwrap_profile(envelope, "fpo")
    if envelope.get("onboarding_status") != "completed":
        raise FarmRegistryError(
            "FPO_PROFILE_INCOMPLETE",
            "Complete your FPO profile before managing farms.",
            409,
        )
    if not profile.get("is_active", True):
        raise FarmRegistryError("FPO_PROFILE_INACTIVE", "Your FPO profile is inactive.", 403)
    return ActorScope(
        role="fpo",
        user_id=principal.user_id,
        fpo_id=UUID(str(profile["fpo_id"])),
        fpo_role=profile.get("current_user_fpo_role"),
        onboarding_status=envelope.get("onboarding_status"),
    )


def _authorize_target_farmer(
    actor: ActorScope,
    target: profile_client.FarmerValidation,
    *,
    write: bool,
) -> None:
    if not target.is_active:
        raise FarmRegistryError("FARMER_PROFILE_INACTIVE", "The farmer profile is inactive.", 403)

    if actor.role == "admin":
        return

    if actor.role == "farmer":
        if actor.farmer_id != target.farmer_id:
            raise FarmRegistryError(
                "FARMER_ACCESS_FORBIDDEN",
                "You cannot manage another farmer's farms.",
                403,
            )
        return

    if actor.role == "fpo":
        if actor.fpo_id is None or target.fpo_id != actor.fpo_id:
            raise FarmRegistryError(
                "FPO_FARMER_ACCESS_FORBIDDEN",
                "The farmer profile is not linked to this FPO.",
                403,
            )
        if write and actor.fpo_role not in {"owner", "admin", "manager"}:
            raise FarmRegistryError(
                "FPO_ROLE_CANNOT_REGISTER_FARM",
                "Your FPO role cannot register member farms.",
                403,
            )
        return

    raise FarmRegistryError("FARM_ACCESS_FORBIDDEN", "You cannot access this farm.", 403)


def _authorize_farm_read(actor: ActorScope, farm: dict[str, Any]) -> None:
    if actor.role == "admin":
        return
    if actor.role == "farmer":
        if str(farm["farmer_id"]) != str(actor.farmer_id):
            raise FarmRegistryError("FARM_ACCESS_FORBIDDEN", "You cannot access this farm.", 403)
        return
    if actor.role == "fpo":
        if farm.get("fpo_id") is None or str(farm["fpo_id"]) != str(actor.fpo_id):
            raise FarmRegistryError("FARM_ACCESS_FORBIDDEN", "You cannot access this farm.", 403)
        return
    raise FarmRegistryError("FARM_ACCESS_FORBIDDEN", "You cannot access this farm.", 403)


def register_farm(context: RequestContext, payload: FarmRegisterRequest) -> dict[str, Any]:
    actor = resolve_actor(context)
    target = profile_client.validate_farmer_internal(
        payload.farmer_id,
        context.correlation_id,
    )
    _authorize_target_farmer(actor, target, write=True)

    if not target.profile_complete:
        raise FarmRegistryError(
            "FARMER_PROFILE_INCOMPLETE",
            "Complete the farmer profile before registering a farm.",
            409,
        )

    authoritative_fpo_id = target.fpo_id
    if payload.fpo_id is not None and payload.fpo_id != authoritative_fpo_id:
        raise FarmRegistryError(
            "FARM_FPO_MISMATCH",
            "The submitted FPO does not match the farmer profile.",
            409,
        )

    crop_profile = repository.get_active_crop_registration_option(payload.crop_code)
    if crop_profile is None:
        raise FarmRegistryError(
            "FARM_CROP_UNSUPPORTED",
            "Select an active crop configured by the MaatiTrace administrator.",
            422,
        )

    try:
        area_acres = calculate_area_acres(payload.polygon)
    except FarmGeometryError as exc:
        raise FarmRegistryError("FARM_GEOMETRY_ERROR", str(exc), 422) from exc

    location = external_clients.validate_location(
        state_name=payload.state_name,
        district_name=payload.district_name,
        block_name=payload.block_name,
        block_code=payload.block_code,
        correlation_id=context.correlation_id,
    )
    h3_result = external_clients.create_h3_preview(
        polygon=payload.polygon,
        resolution=payload.h3_resolution,
        correlation_id=context.correlation_id,
    )

    try:
        return repository.create_farm(
            {
                "farmer_id": target.farmer_id,
                "fpo_id": authoritative_fpo_id,
                "farm_name": payload.farm_name,
                "survey_number": payload.survey_number,
                "state_name": location["state_name"],
                "district_name": location["district_name"],
                "district_code": location.get("district_code"),
                "block_name": location.get("block_name"),
                "block_code": location.get("block_code"),
                "village_name": payload.village_name,
                "crop_code": crop_profile["crop_code"],
                "crop_name": crop_profile["crop_name"],
                "crop_variety": payload.crop_variety,
                "crop_stage": payload.crop_stage,
                "planting_date": payload.planting_date,
                "polygon_geojson": payload.polygon,
                "h3_resolution": h3_result["resolution"],
                "h3_cells": h3_result["h3_cells_bigint"],
                "h3_cell_count": h3_result["cell_count"],
                "area_acres": area_acres,
                "bbox": h3_result.get("bbox"),
            }
        )
    except FarmRegistryRepositoryError as exc:
        raise _repository_failure(exc) from exc


def get_farm_for_requester(context: RequestContext, farm_id: UUID) -> dict[str, Any]:
    farm = repository.get_farm(farm_id)
    if farm is None:
        raise FarmRegistryError("FARM_NOT_FOUND", "Farm was not found.", 404)
    _authorize_farm_read(resolve_actor(context), farm)
    return farm


def list_farms_for_requester(
    context: RequestContext,
    *,
    fpo_id: UUID | None,
    farmer_id: UUID | None,
    district_name: str | None,
    block_name: str | None,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    actor = resolve_actor(context)
    effective_fpo_id = fpo_id
    effective_farmer_id = farmer_id

    if actor.role == "farmer":
        if farmer_id is not None and farmer_id != actor.farmer_id:
            raise FarmRegistryError(
                "FARMER_FILTER_FORBIDDEN",
                "You cannot list another farmer's farms.",
                403,
            )
        if fpo_id is not None:
            raise FarmRegistryError(
                "FPO_FILTER_FORBIDDEN",
                "Farmer accounts cannot list every farm of an FPO.",
                403,
            )
        effective_farmer_id = actor.farmer_id
        effective_fpo_id = None

    elif actor.role == "fpo":
        if fpo_id is not None and fpo_id != actor.fpo_id:
            raise FarmRegistryError(
                "FPO_FILTER_FORBIDDEN",
                "You cannot list another FPO's farms.",
                403,
            )
        effective_fpo_id = actor.fpo_id
        if farmer_id is not None:
            target = profile_client.validate_farmer_internal(
                farmer_id,
                context.correlation_id,
            )
            _authorize_target_farmer(actor, target, write=False)

    return repository.list_farms(
        fpo_id=effective_fpo_id,
        farmer_id=effective_farmer_id,
        district_name=district_name,
        block_name=block_name,
        limit=limit,
        offset=offset,
    )


def list_farmer_farms_for_requester(context: RequestContext, farmer_id: UUID) -> list[dict[str, Any]]:
    actor = resolve_actor(context)
    target = profile_client.validate_farmer_internal(farmer_id, context.correlation_id)
    _authorize_target_farmer(actor, target, write=False)
    return repository.list_farms_by_farmer(farmer_id)


def get_farmer_summary_for_requester(context: RequestContext, farmer_id: UUID) -> dict[str, Any]:
    actor = resolve_actor(context)
    target = profile_client.validate_farmer_internal(farmer_id, context.correlation_id)
    _authorize_target_farmer(actor, target, write=False)
    return repository.get_farmer_summary(farmer_id)


def _authorize_fpo_scope(
    actor: ActorScope,
    fpo_id: UUID,
    *,
    allow_linked_farmer_summary: bool,
) -> None:
    if actor.role == "admin":
        return
    if actor.role == "fpo" and actor.fpo_id == fpo_id:
        return
    if allow_linked_farmer_summary and actor.role == "farmer" and actor.fpo_id == fpo_id:
        return
    raise FarmRegistryError(
        "FPO_ACCESS_FORBIDDEN",
        "You cannot access this FPO farm information.",
        403,
    )


def list_fpo_farms_for_requester(context: RequestContext, fpo_id: UUID) -> list[dict[str, Any]]:
    actor = resolve_actor(context)
    fpo = profile_client.validate_fpo_internal(fpo_id, context.correlation_id)
    if not fpo.is_active:
        raise FarmRegistryError("FPO_PROFILE_INACTIVE", "The FPO profile is inactive.", 403)
    _authorize_fpo_scope(actor, fpo_id, allow_linked_farmer_summary=False)
    return repository.list_farms_by_fpo(fpo_id)


def get_fpo_summary_for_requester(context: RequestContext, fpo_id: UUID) -> dict[str, Any]:
    actor = resolve_actor(context)
    fpo = profile_client.validate_fpo_internal(fpo_id, context.correlation_id)
    if not fpo.is_active:
        raise FarmRegistryError("FPO_PROFILE_INACTIVE", "The FPO profile is inactive.", 403)
    _authorize_fpo_scope(actor, fpo_id, allow_linked_farmer_summary=True)
    return repository.get_fpo_summary(fpo_id)


def get_internal_farm(farm_id: UUID) -> dict[str, Any]:
    farm = repository.get_complete_farm(farm_id)
    if farm is None:
        raise FarmRegistryError("FARM_NOT_FOUND", "Farm was not found.", 404)
    return farm
