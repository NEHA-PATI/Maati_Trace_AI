from __future__ import annotations

import json
from typing import Any, Callable
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from shared.db.postgres import engine
from services.profile_service.app.dependencies import RequestContext
from services.profile_service.app.errors import ProfileError
from services.profile_service.app.repository import (
    create_fpo_service_area,
    get_fpo_memberships,
    list_fpo_commodities,
    list_fpo_service_areas,
    list_fpo_services,
    retire_fpo_commodity,
    retire_fpo_service,
    retire_fpo_service_area,
    upsert_fpo_commodity,
    upsert_fpo_service,
    get_fpo_by_id,
    list_profile_history,
)
from services.profile_service.app.service import FPO_WRITE_ROLES, _select_fpo_membership


def _profile_id(context: RequestContext) -> UUID:
    if context.principal.role != "fpo":
        raise ProfileError("FPO_ROLE_REQUIRED", "Only FPO accounts can manage an FPO profile.", 403)
    with engine.connect() as conn:
        membership = _select_fpo_membership(
            get_fpo_memberships(conn, context.principal.user_id),
            context.fpo_context_id,
        )
    if membership is None:
        raise ProfileError("FPO_PROFILE_NOT_FOUND", "The FPO profile was not found.", 404)
    return UUID(str(membership["fpo_id"]))


def _require_write(context: RequestContext) -> UUID:
    profile_id = _profile_id(context)
    with engine.connect() as conn:
        membership = _select_fpo_membership(
            get_fpo_memberships(conn, context.principal.user_id),
            context.fpo_context_id,
        )
    if membership["fpo_role"] not in FPO_WRITE_ROLES:
        raise ProfileError("FPO_WRITE_FORBIDDEN", "Your FPO role cannot update this profile.", 403)
    return profile_id


def get_structured_profile(context: RequestContext) -> dict[str, list[dict[str, Any]]]:
    profile_id = _profile_id(context)
    with engine.connect() as conn:
        return {
            "commodities": list_fpo_commodities(conn, profile_id),
            "services": list_fpo_services(conn, profile_id),
            "service_areas": list_fpo_service_areas(conn, profile_id),
        }


def get_profile_readiness(context: RequestContext) -> dict[str, Any]:
    profile_id = _profile_id(context)
    with engine.begin() as conn:
        profile = get_fpo_by_id(conn, profile_id) or {}
        commodities = list_fpo_commodities(conn, profile_id)
        services = list_fpo_services(conn, profile_id)
        areas = list_fpo_service_areas(conn, profile_id)

    blocking: list[dict[str, Any]] = []
    checks = (
        ("LEGAL_NAME_REQUIRED", "LEGAL_IDENTITY", "legal_name"),
        ("REGISTRATION_NUMBER_REQUIRED", "LEGAL_IDENTITY", "registration_number"),
        ("REGISTRATION_TYPE_REQUIRED", "LEGAL_IDENTITY", "registration_type"),
        ("REGISTRATION_DATE_REQUIRED", "LEGAL_IDENTITY", "date_of_registration"),
        ("CONTACT_PHONE_REQUIRED", "REPRESENTATIVE", "contact_phone"),
        ("CONTACT_EMAIL_REQUIRED", "REPRESENTATIVE", "contact_email"),
    )
    for code, section, field in checks:
        if not profile.get(field):
            blocking.append({"code": code, "section": section, "field": field})
    if not any(item.get("is_primary") for item in commodities):
        blocking.append({"code": "PRIMARY_COMMODITY_REQUIRED", "section": "COMMODITIES", "field": None})
    if not areas:
        blocking.append({"code": "SERVICE_AREA_REQUIRED", "section": "SERVICE_AREAS", "field": None})
    percentage = max(0, 100 - min(100, len(blocking) * 10))
    # Readiness is the canonical FPO onboarding gate. Keep the persisted
    # profile and organization projections aligned with the same calculation
    # so the header, portal boundary, and verification page cannot disagree.
    conn.execute(text("""
        UPDATE public.fpos
        SET verification_readiness_percentage = :percentage,
            readiness_calculation_version = 'fpo-profile-readiness-v2',
            readiness_calculated_at = now(),
            updated_at = now()
        WHERE fpo_id = :profile_id
          AND (verification_readiness_percentage IS DISTINCT FROM :percentage
               OR readiness_calculated_at IS NULL)
    """), {"percentage": percentage, "profile_id": str(profile_id)})
    conn.execute(text("""
        UPDATE public.fpo_organizations
        SET verification_status = CASE
              WHEN :ready AND verification_status IN ('PROFILE_INCOMPLETE', 'READY_TO_SUBMIT')
                THEN 'READY_TO_SUBMIT'
              WHEN NOT :ready AND verification_status = 'READY_TO_SUBMIT'
                THEN 'PROFILE_INCOMPLETE'
              ELSE verification_status
            END,
            updated_at = now(), version = version + 1
        WHERE profile_fpo_id = :profile_id
          AND ((:ready AND verification_status = 'PROFILE_INCOMPLETE')
               OR (NOT :ready AND verification_status = 'READY_TO_SUBMIT'))
    """), {"ready": not blocking, "profile_id": str(profile_id)})
    return {
        "ready": not blocking,
        "percentage": percentage,
        "calculation_version": "fpo-profile-readiness-v2",
        "blocking_requirements": blocking,
        "warnings": ([{"code": "DECLARED_AREA_NOT_RECONCILED", "section": "OPERATIONS", "field": "declared_area_acres"}]
                      if profile.get("declared_area_acres") is not None else []),
        "profile_version": profile.get("profile_version") or 1,
    }


def get_admin_profile(context: RequestContext, profile_id: UUID, limit: int = 100) -> dict[str, Any]:
    if context.principal.role != "admin":
        raise ProfileError("ADMIN_REQUIRED", "Administrator access is required.", 403)
    with engine.begin() as conn:
        profile = get_fpo_by_id(conn, profile_id)
        if profile is None:
            raise ProfileError("FPO_PROFILE_NOT_FOUND", "The FPO profile was not found.", 404)
        history = list_profile_history(conn, profile_id, limit)
        submission = conn.execute(text("""
            SELECT profile_snapshot, status, submitted_at, reviewed_at
            FROM public.fpo_verification_submissions
            WHERE fpo_id = :organization_id
            ORDER BY submitted_at DESC
            LIMIT 1
        """), {"organization_id": str(profile.get("organization_id"))}).mappings().first()
        organization = {
            key: profile.get(key)
            for key in ("organization_id", "public_fpo_id", "provisioning_status", "lifecycle_status",
                        "organization_verification_status", "class_code", "commercial_status")
        }
        current_fields = {key: profile.get(key) for key in profile.keys()}
        snapshot = dict(submission["profile_snapshot"]) if submission and submission.get("profile_snapshot") else None
        changed = sorted(key for key, value in current_fields.items() if snapshot and snapshot.get(key) != value)
        reverification = sorted(set(changed) & {"legal_name", "organisation_type", "registration_type", "registration_number", "registration_authority", "date_of_registration", "cin", "pan_masked", "state_code"})
        return {
            "organization": organization,
            "profile": profile,
            "readiness": _readiness_for_profile(conn, profile),
            "history": history,
            "submitted_snapshot": snapshot,
            "changed_after_submission": changed,
            "reverification_fields": reverification,
        }


def _readiness_for_profile(conn, profile: dict[str, Any]) -> dict[str, Any]:
    commodities = list_fpo_commodities(conn, profile["fpo_id"])
    areas = list_fpo_service_areas(conn, profile["fpo_id"])
    blocking = []
    for code, section, field in (("LEGAL_NAME_REQUIRED", "LEGAL_IDENTITY", "legal_name"), ("REGISTRATION_NUMBER_REQUIRED", "LEGAL_IDENTITY", "registration_number"), ("REGISTRATION_DATE_REQUIRED", "LEGAL_IDENTITY", "date_of_registration"), ("CONTACT_PHONE_REQUIRED", "REPRESENTATIVE", "contact_phone"), ("CONTACT_EMAIL_REQUIRED", "REPRESENTATIVE", "contact_email")):
        if not profile.get(field):
            blocking.append({"code": code, "section": section, "field": field})
    if not any(item.get("is_primary") for item in commodities):
        blocking.append({"code": "PRIMARY_COMMODITY_REQUIRED", "section": "COMMODITIES", "field": None})
    if not areas:
        blocking.append({"code": "SERVICE_AREA_REQUIRED", "section": "SERVICE_AREAS", "field": None})
    return {"ready": not blocking, "percentage": max(0, 100 - min(100, len(blocking) * 10)), "calculation_version": "fpo-profile-readiness-v2", "blocking_requirements": blocking, "warnings": [], "profile_version": profile.get("profile_version") or 1}


def mutate_structured_profile(
    context: RequestContext,
    operation: Callable[..., dict[str, Any] | None],
    values: dict[str, Any],
    *,
    resource: str,
) -> dict[str, Any]:
    profile_id = _require_write(context)
    try:
        with engine.begin() as conn:
            result = operation(conn, profile_id, values)
        return result or {"status": "retired", "resource": resource}
    except IntegrityError as exc:
        raise ProfileError(
            f"FPO_{resource.upper()}_CONFLICT",
            f"The {resource} already exists or is invalid.",
            409,
            internal_message=str(exc),
        ) from exc


def add_commodity(context: RequestContext, values: dict[str, Any]) -> dict[str, Any]:
    return mutate_structured_profile(context, upsert_fpo_commodity, values, resource="commodity")


def remove_commodity(context: RequestContext, commodity_code: str) -> dict[str, Any]:
    profile_id = _require_write(context)
    with engine.begin() as conn:
        retire_fpo_commodity(conn, profile_id, commodity_code)
    return {"status": "retired", "commodity_code": commodity_code}


def add_service(context: RequestContext, values: dict[str, Any]) -> dict[str, Any]:
    if values.get("active_from") is not None:
        values = {**values, "active_from": values["active_from"].isoformat()}
    return mutate_structured_profile(context, upsert_fpo_service, values, resource="service")


def remove_service(context: RequestContext, service_code: str) -> dict[str, Any]:
    profile_id = _require_write(context)
    with engine.begin() as conn:
        retire_fpo_service(conn, profile_id, service_code)
    return {"status": "retired", "service_code": service_code}


def add_service_area(context: RequestContext, values: dict[str, Any]) -> dict[str, Any]:
    return mutate_structured_profile(context, create_fpo_service_area, values, resource="service_area")


def remove_service_area(context: RequestContext, service_area_id: UUID) -> dict[str, Any]:
    profile_id = _require_write(context)
    with engine.begin() as conn:
        retire_fpo_service_area(conn, profile_id, service_area_id)
    return {"status": "retired", "service_area_id": str(service_area_id)}
