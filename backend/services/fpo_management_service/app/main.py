from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.concurrency import run_in_threadpool

from services.fpo_management_service.app.config import FpoManagementConfig
from services.fpo_management_service.app.service import (
    bootstrap_status,
    review_verification_request,
    submit_verification_request,
    verification_queue,
    verification_status,
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
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(config.trusted_hosts))


def current_user(authorization: str | None = Header(default=None, alias="Authorization")):
    try:
        user = load_current_user(authorization)
    except (CurrentUserUnavailableError, InvalidAccessTokenError, MissingAuthorizationError) as exc:
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED", "message": "Authentication is required."}) from exc
    if user.get("role") not in {"fpo", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can access this workspace."})
    return user


@app.get("/health/live")
def live():
    return {"service": "fpo_management_service", "status": "live", "environment": config.app_env}


@app.get("/v1/fpo-portal/bootstrap-status")
async def read_bootstrap_status(user=Depends(current_user)):
    return await run_in_threadpool(bootstrap_status, user["user_id"])


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
