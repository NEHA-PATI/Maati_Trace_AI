from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query

from shared.security.local_auth import (
    CurrentUserUnavailableError,
    InvalidAccessTokenError,
    MissingAuthorizationError,
    PrincipalLookupError,
    load_current_user,
)
from services.analytics_query_service.app.feature_engine import repository
from services.analytics_query_service.app.feature_engine.schemas import (
    CalculationMaterializeRequest,
    CloneCropRequest,
    CloneVersionRequest,
    CropProfileCreateRequest,
    CropProfileUpdateRequest,
    FeatureMaterializeRequest,
    FormulaCreateRequest,
    FormulaUpdateRequest,
    IntelligenceMaterializeRequest,
    SeedFormulasRequest,
)
from services.analytics_query_service.app.feature_engine.service import (
    FeatureEngineError,
    materialize_calculations,
    materialize_features,
    materialize_intelligence,
    validate_formula_components,
)

router = APIRouter()


def _raise_feature_error(exc: Exception):
    if isinstance(exc, FeatureEngineError):
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}) from exc
    if isinstance(exc, repository.FeatureEngineRepositoryError):
        raise HTTPException(status_code=400, detail={"code": "FEATURE_ENGINE_REPOSITORY_ERROR", "message": str(exc)}) from exc
    raise exc


def _admin(authorization: str | None) -> dict:
    try:
        user = load_current_user(authorization)
    except MissingAuthorizationError as exc:
        raise HTTPException(status_code=401, detail="Authentication is required") from exc
    except (InvalidAccessTokenError, CurrentUserUnavailableError) as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except PrincipalLookupError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access is required")
    return user


@router.get("/v1/analytics/crop-profiles")
def crop_profiles():
    return {"items": repository.list_public_crop_profiles()}


@router.get("/v1/analytics/formulas")
def formulas(crop_code: str | None = Query(default=None)):
    return {"items": repository.list_public_formulas(crop_code)}


@router.get("/v1/analytics/components")
def components():
    return {"items": repository.get_component_catalog()}


@router.post("/v1/analytics/farms/{farm_id}/features/materialize")
def features_materialize(farm_id: UUID, payload: FeatureMaterializeRequest):
    try:
        return materialize_features(
            farm_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            latest_only=payload.latest_only,
            force_refresh=payload.force_refresh,
        )
    except Exception as exc:
        _raise_feature_error(exc)


@router.post("/v1/analytics/farms/{farm_id}/calculations/materialize")
def calculations_materialize(farm_id: UUID, payload: CalculationMaterializeRequest):
    try:
        return materialize_calculations(
            farm_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            latest_only=payload.latest_only,
        )
    except Exception as exc:
        _raise_feature_error(exc)


@router.post("/v1/analytics/farms/{farm_id}/intelligence/materialize")
def intelligence_materialize(farm_id: UUID, payload: IntelligenceMaterializeRequest):
    try:
        return materialize_intelligence(
            farm_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            latest_only=payload.latest_only,
            force_refresh=payload.force_refresh,
        )
    except Exception as exc:
        _raise_feature_error(exc)


@router.get("/v1/analytics/farms/{farm_id}/features/latest")
def latest_features(farm_id: UUID):
    return {"farm_id": str(farm_id), "items": repository.get_engineered_features(farm_id, latest_only=True)}


@router.get("/v1/analytics/farms/{farm_id}/calculations/latest")
def latest_calculations(
    farm_id: UUID,
    scope: str = Query(default="farm", pattern="^(farm|h3)$"),
    prediction_key: str | None = Query(default=None),
):
    return {
        "farm_id": str(farm_id),
        "scope": scope,
        "items": repository.get_calculated_predictions(
            farm_id, scope=scope, latest_only=True, prediction_key=prediction_key
        ),
    }


@router.get("/v1/analytics/farms/{farm_id}/grid-calculations/latest")
def latest_grid_calculations(farm_id: UUID):
    return {
        "farm_id": str(farm_id),
        "grid_semantics": "Scores are H3 formula results projected to the existing display grid with H3/grid overlap weights; they are not independent 10 m measurements.",
        "items": repository.get_latest_grid_calculations(farm_id),
    }


@router.get("/v1/analytics/farms/{farm_id}/grid-cells/{grid_cell_id}/calculations")
def grid_cell_calculations(farm_id: UUID, grid_cell_id: UUID):
    return {
        "farm_id": str(farm_id),
        "grid_cell_id": str(grid_cell_id),
        "items": repository.get_grid_cell_calculations(farm_id, grid_cell_id),
    }


# ---------------- Admin crop / formula configuration ----------------
@router.get("/v1/analytics/admin/crop-profiles")
def admin_profiles(
    include_inactive: bool = Query(default=True),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    _admin(authorization)
    return {"items": repository.admin_list_profiles(include_inactive)}


@router.post("/v1/analytics/admin/crop-profiles", status_code=201)
def admin_create_profile(
    payload: CropProfileCreateRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user = _admin(authorization)
    try:
        return repository.admin_create_profile(payload.model_dump(), user["user_id"])
    except Exception as exc:
        _raise_feature_error(exc)


@router.put("/v1/analytics/admin/crop-profiles/{profile_id}")
def admin_update_profile(
    profile_id: UUID,
    payload: CropProfileUpdateRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user = _admin(authorization)
    try:
        return repository.admin_update_profile(profile_id, payload.model_dump(), user["user_id"])
    except Exception as exc:
        _raise_feature_error(exc)


@router.post("/v1/analytics/admin/crop-profiles/{profile_id}/publish")
def admin_publish_profile(
    profile_id: UUID,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user = _admin(authorization)
    try:
        return repository.admin_publish_profile(profile_id, user["user_id"])
    except Exception as exc:
        _raise_feature_error(exc)


@router.post("/v1/analytics/admin/crop-profiles/{profile_id}/clone", status_code=201)
def admin_clone_profile(
    profile_id: UUID,
    payload: CloneVersionRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user = _admin(authorization)
    try:
        return repository.admin_clone_profile(profile_id, payload.new_version, user["user_id"])
    except Exception as exc:
        _raise_feature_error(exc)


@router.post("/v1/analytics/admin/crop-profiles/{profile_id}/seed-formulas", status_code=201)
def admin_seed_formulas(
    profile_id: UUID,
    payload: SeedFormulasRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user = _admin(authorization)
    try:
        return repository.admin_seed_formulas_for_profile(
            profile_id,
            payload.source_crop_code,
            user["user_id"],
            payload.formula_version_suffix,
        )
    except Exception as exc:
        _raise_feature_error(exc)


@router.post("/v1/analytics/admin/crop-profiles/{profile_id}/publish-formulas")
def admin_publish_all_formulas(
    profile_id: UUID,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user = _admin(authorization)
    try:
        return repository.admin_publish_all_formulas_for_profile(profile_id, user["user_id"])
    except Exception as exc:
        _raise_feature_error(exc)


@router.delete("/v1/analytics/admin/crop-profiles/{profile_id}")
def admin_delete_profile(
    profile_id: UUID,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user = _admin(authorization)
    try:
        return repository.admin_delete_profile(profile_id, user["user_id"])
    except Exception as exc:
        _raise_feature_error(exc)


@router.delete("/v1/analytics/admin/formulas/{formula_id}")
def admin_delete_formula(
    formula_id: UUID,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user = _admin(authorization)
    try:
        return repository.admin_delete_formula(formula_id, user["user_id"])
    except Exception as exc:
        _raise_feature_error(exc)


@router.get("/v1/analytics/admin/formulas")
def admin_formulas(
    crop_code: str | None = Query(default=None),
    include_inactive: bool = Query(default=True),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    _admin(authorization)
    return {"items": repository.admin_list_formulas(include_inactive, crop_code)}


@router.post("/v1/analytics/admin/formulas", status_code=201)
def admin_create_formula(
    payload: FormulaCreateRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user = _admin(authorization)
    try:
        validate_formula_components(payload.component_weights)
        return repository.admin_create_formula(payload.model_dump(), user["user_id"])
    except Exception as exc:
        _raise_feature_error(exc)


@router.put("/v1/analytics/admin/formulas/{formula_id}")
def admin_update_formula(
    formula_id: UUID,
    payload: FormulaUpdateRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user = _admin(authorization)
    try:
        validate_formula_components(payload.component_weights)
        return repository.admin_update_formula(formula_id, payload.model_dump(), user["user_id"])
    except Exception as exc:
        _raise_feature_error(exc)


@router.post("/v1/analytics/admin/formulas/{formula_id}/publish")
def admin_publish_formula(
    formula_id: UUID,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user = _admin(authorization)
    try:
        return repository.admin_publish_formula(formula_id, user["user_id"])
    except Exception as exc:
        _raise_feature_error(exc)


@router.post("/v1/analytics/admin/formulas/{formula_id}/clone", status_code=201)
def admin_clone_formula(
    formula_id: UUID,
    payload: CloneVersionRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user = _admin(authorization)
    try:
        return repository.admin_clone_formula(formula_id, payload.new_version, user["user_id"])
    except Exception as exc:
        _raise_feature_error(exc)


@router.post("/v1/analytics/admin/crops/clone", status_code=201)
def admin_clone_crop(
    payload: CloneCropRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user = _admin(authorization)
    try:
        return repository.admin_clone_crop(
            payload.source_crop_code,
            target_crop_code=payload.target_crop_code,
            target_crop_name=payload.target_crop_name,
            target_profile_version=payload.target_profile_version,
            formula_version_suffix=payload.formula_version_suffix,
            actor_user_id=user["user_id"],
        )
    except Exception as exc:
        _raise_feature_error(exc)
