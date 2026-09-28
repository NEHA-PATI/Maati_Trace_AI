from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.concurrency import run_in_threadpool
from sqlalchemy import text
from shared.db.postgres import engine

from services.fpo_management_service.app.config import FpoManagementConfig
from services.fpo_management_service.app.service import (
    bootstrap_status,
    portal_bootstrap,
    review_verification_request,
    submit_verification_request,
    verification_queue,
    verification_status,
    decide_relationship,
    discover_fpo_directory,
    farmer_relationships,
    fpo_relationships,
    request_farmer_relationship,
    revoke_relationship,
    assign_class,
    feature_catalogue,
    fpo_entitlements,
    create_fpo_feature_override,
    fpo_feature_overrides,
    run_fpo_reconciliation,
    portfolio_report,
    operational_alerts,
    acknowledge_alert,
    dashboard_read_model,
    farmer_directory,
)
from shared.security.local_auth import (
    CurrentUserUnavailableError,
    InvalidAccessTokenError,
    MissingAuthorizationError,
    load_current_user,
)

config = FpoManagementConfig.from_env()
app = FastAPI(title="MaatiTrace FPO Management Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(config.cors_allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(config.trusted_hosts))


def current_user(authorization: str | None = Header(default=None, alias="Authorization")):
    try:
        user = load_current_user(authorization)
    except (CurrentUserUnavailableError, InvalidAccessTokenError, MissingAuthorizationError) as exc:
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED", "message": "Authentication is required."}) from exc
    if user.get("role") not in {"fpo", "farmer", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_OR_FARMER_ROLE_REQUIRED", "message": "This endpoint is not available for the current account role."})
    return user


class RelationshipRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fpo_id: UUID


class RelationshipDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: str = Field(pattern="^(ACTIVE|REJECTED)$")


class ClassAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    class_code: str = Field(pattern="^(A|B|C|a|b|c)$")


class FeatureOverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    feature_key: str = Field(min_length=2, max_length=100)
    enabled: bool
    reason: str = Field(min_length=3, max_length=1000)
    expires_at: datetime | None = None


@app.get("/health/live")
def live():
    return {"service": "fpo_management_service", "status": "live", "environment": config.app_env}


@app.get("/health/ready")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"service": "fpo_management_service", "status": "ready"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"service": "fpo_management_service", "status": "not_ready", "message": str(exc)[:200]}) from exc


@app.get("/v1/fpo-portal/bootstrap-status")
async def read_bootstrap_status(user=Depends(current_user)):
    return await run_in_threadpool(bootstrap_status, user["user_id"])


@app.get("/v1/fpo-portal/bootstrap")
@app.get("/v1/fpo/me/bootstrap")
async def read_portal_bootstrap(user=Depends(current_user)):
    return await run_in_threadpool(portal_bootstrap, user["user_id"])


@app.get("/v1/fpo-portal/verification")
async def read_verification(user=Depends(current_user)):
    return await run_in_threadpool(verification_status, user["user_id"])


@app.post("/v1/fpo-portal/verification/submit", status_code=201)
async def submit_verification(user=Depends(current_user)):
    try:
        return await run_in_threadpool(submit_verification_request, user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_VERIFICATION_NOT_READY", "message": str(exc)}) from exc


@app.patch("/v1/fpo-portal/admin/organizations/{fpo_id}/verification")
async def decide_verification(fpo_id: str, payload: dict, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    try:
        return await run_in_threadpool(
            review_verification_request,
            fpo_id,
            user["user_id"],
            str(payload.get("status", "")).upper(),
            payload.get("note"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_VERIFICATION_REVIEW_FAILED", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/admin/verification-queue")
async def read_verification_queue(status: str | None = None, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    return await run_in_threadpool(verification_queue, status)


@app.get("/v1/fpo-portal/discover")
async def discover_fpo(query: str | None = None, limit: int = Query(default=25, ge=1, le=100), user=Depends(current_user)):
    if user.get("role") not in {"farmer", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmers can discover an FPO."})
    return await run_in_threadpool(discover_fpo_directory, query, limit)


@app.get("/v1/farmer/fpo-relationships")
async def read_farmer_relationships(user=Depends(current_user)):
    if user.get("role") not in {"farmer", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmers can read their FPO relationships."})
    return await run_in_threadpool(farmer_relationships, user["user_id"])


@app.post("/v1/farmer/fpo-relationships", status_code=201)
async def create_farmer_relationship(payload: RelationshipRequest, user=Depends(current_user)):
    if user.get("role") != "farmer":
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmer accounts can request an FPO relationship."})
    try:
        return await run_in_threadpool(request_farmer_relationship, user["user_id"], payload.fpo_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_RELATIONSHIP_REQUEST_FAILED", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/relationships")
async def read_fpo_relationships(user=Depends(current_user)):
    if user.get("role") not in {"fpo", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read relationship requests."})
    try:
        return await run_in_threadpool(fpo_relationships, user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=403, detail={"code": "FPO_FEATURE_DISABLED", "message": str(exc)}) from exc


@app.patch("/v1/fpo-portal/relationships/{relationship_id}")
async def update_fpo_relationship(relationship_id: UUID, payload: RelationshipDecision, user=Depends(current_user)):
    if user.get("role") != "fpo":
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can decide relationship requests."})
    try:
        return await run_in_threadpool(decide_relationship, user["user_id"], relationship_id, payload.decision)
    except ValueError as exc:
        code = "FPO_FEATURE_DISABLED" if "Feature" in str(exc) else "FPO_RELATIONSHIP_DECISION_FAILED"
        raise HTTPException(status_code=403 if code == "FPO_FEATURE_DISABLED" else 409, detail={"code": code, "message": str(exc)}) from exc


@app.delete("/v1/farmer/fpo-relationships/{relationship_id}")
async def revoke_fpo_relationship(relationship_id: UUID, user=Depends(current_user)):
    if user.get("role") != "farmer":
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmers can revoke their relationship."})
    try:
        return await run_in_threadpool(revoke_relationship, user["user_id"], relationship_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_RELATIONSHIP_REVOKE_FAILED", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/entitlements")
@app.get("/v1/fpo/me/entitlements")
async def read_fpo_entitlements(user=Depends(current_user)):
    if user.get("role") not in {"fpo", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read entitlements."})
    return await run_in_threadpool(fpo_entitlements, user["user_id"])


@app.get("/v1/fpo-portal/reports/portfolio")
async def read_portfolio_report(user=Depends(current_user)):
    if user.get("role") not in {"fpo", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read portfolio reports."})
    try:
        return await run_in_threadpool(portfolio_report, user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=403, detail={"code": "FPO_FEATURE_DISABLED", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/dashboard")
@app.get("/v1/fpo/me/dashboard")
async def read_dashboard(user=Depends(current_user)):
    if user.get("role") not in {"fpo", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read the dashboard."})
    try:
        return await run_in_threadpool(dashboard_read_model, user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=403, detail={"code": "FPO_FEATURE_DISABLED", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/farmers")
@app.get("/v1/fpo/me/farmers")
async def read_farmer_directory(
    query: str | None = None,
    district_code: int | None = None,
    block_code: int | None = None,
    relationship_status: str | None = None,
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    user=Depends(current_user),
):
    if user.get("role") not in {"fpo", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read the farmer directory."})
    try:
        return await run_in_threadpool(farmer_directory, user["user_id"], query, district_code, block_code, relationship_status, cursor, limit)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail={"code": "FPO_FEATURE_DISABLED", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/alerts")
async def read_operational_alerts(status: str | None = Query(default=None), user=Depends(current_user)):
    if user.get("role") not in {"fpo", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read alerts."})
    try:
        return await run_in_threadpool(operational_alerts, user["user_id"], status)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail={"code": "FPO_FEATURE_DISABLED", "message": str(exc)}) from exc


@app.patch("/v1/fpo-portal/alerts/{alert_id}/acknowledge")
async def mark_alert_acknowledged(alert_id: UUID, user=Depends(current_user)):
    if user.get("role") != "fpo":
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can acknowledge alerts."})
    try:
        return await run_in_threadpool(acknowledge_alert, user["user_id"], alert_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_ALERT_ACKNOWLEDGE_FAILED", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/admin/features/catalogue")
async def read_feature_catalogue(user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    return await run_in_threadpool(feature_catalogue)


@app.patch("/v1/fpo-portal/admin/organizations/{fpo_id}/class")
async def update_fpo_class(fpo_id: UUID, payload: ClassAssignment, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    try:
        return await run_in_threadpool(assign_class, fpo_id, payload.class_code, user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_CLASS_ASSIGNMENT_FAILED", "message": str(exc)}) from exc


@app.post("/v1/fpo-portal/admin/organizations/{fpo_id}/feature-overrides", status_code=201)
async def create_override(fpo_id: UUID, payload: FeatureOverrideRequest, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    try:
        return await run_in_threadpool(
            create_fpo_feature_override,
            fpo_id,
            payload.feature_key,
            payload.enabled,
            payload.reason,
            payload.expires_at,
            user["user_id"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_FEATURE_OVERRIDE_FAILED", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/admin/organizations/{fpo_id}/feature-overrides")
async def read_overrides(fpo_id: UUID, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    return await run_in_threadpool(fpo_feature_overrides, fpo_id)


@app.post("/v1/fpo-portal/admin/reconciliation/run")
async def run_reconciliation(user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    return await run_in_threadpool(run_fpo_reconciliation, user["user_id"])
