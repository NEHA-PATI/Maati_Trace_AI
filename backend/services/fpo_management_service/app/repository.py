from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any
from uuid import UUID
import json
import base64
import re
import os
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Connection


CHECK_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ"


def public_fpo_id(state_code: int, sequence_number: int, occurred_at: datetime | None = None) -> str:
    if state_code <= 0 or sequence_number <= 0:
        raise ValueError("FPO_PUBLIC_ID_INPUT_INVALID")
    event_time = occurred_at or datetime.now(timezone.utc)
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)
    state = f"S{int(state_code):02d}"
    check = CHECK_ALPHABET[sequence_number % len(CHECK_ALPHABET)]
    return f"MTFPO-{state}-{event_time.year % 100:02d}-{sequence_number:06d}-{check}"


def validate_auth_user_created_event(event: dict[str, Any]) -> dict[str, Any]:
    if set(event) - {
        "event_id", "event_type", "event_version", "occurred_at",
        "correlation_id", "subject_id", "payload",
    }:
        raise ValueError("FPO_EVENT_ENVELOPE_FIELDS_INVALID")
    if event.get("event_type") != "auth.user.created" or int(event.get("event_version") or 0) not in {1, 2}:
        raise ValueError("FPO_EVENT_TYPE_OR_VERSION_UNSUPPORTED")
    payload = event.get("payload")
    if not isinstance(payload, dict) or payload.get("account_type") != "fpo":
        raise ValueError("FPO_EVENT_PAYLOAD_INVALID")
    if set(payload) - {
        "user_id", "account_type", "authorised_fpo_representative",
        "email", "phone_number", "full_name", "signup_profile",
    }:
        raise ValueError("FPO_EVENT_PAYLOAD_FIELDS_INVALID")
    user_id = payload.get("user_id")
    if not user_id or str(event.get("subject_id")) != str(user_id):
        raise ValueError("FPO_EVENT_SUBJECT_MISMATCH")
    if payload.get("authorised_fpo_representative") is not True:
        raise ValueError("FPO_REPRESENTATIVE_AUTHORITY_REQUIRED")
    profile = payload.get("signup_profile")
    if not isinstance(profile, dict):
        raise ValueError("FPO_SIGNUP_PROFILE_REQUIRED")
    if set(profile) - {
        "organisation_name", "registration_type", "registration_number",
        "state_code", "state_name", "district_code", "district_name",
    }:
        raise ValueError("FPO_SIGNUP_PROFILE_FIELDS_INVALID")
    if not str(profile.get("organisation_name") or "").strip():
        raise ValueError("FPO_ORGANISATION_NAME_REQUIRED")
    if not str(profile.get("registration_number") or "").strip():
        raise ValueError("FPO_REGISTRATION_NUMBER_REQUIRED")
    try:
        UUID(str(user_id))
        UUID(str(event.get("event_id")))
        UUID(str(event.get("correlation_id")))
        occurred_at = datetime.fromisoformat(
            str(event.get("occurred_at")).replace("Z", "+00:00")
        )
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError("FPO_EVENT_TIMESTAMP_TIMEZONE_REQUIRED")
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("FPO_EVENT_ENVELOPE_INVALID") from exc
    return payload


def claim_provisioning_events(conn: Connection, *, batch_size: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            WITH candidates AS (
                SELECT inbox_id
                FROM public.fpo_event_inbox
                WHERE consumer_name = 'fpo_management_service'
                  AND event_type = 'auth.user.created'
                  AND (
                    (status IN ('RECEIVED', 'FAILED') AND available_at <= now())
                    OR (status = 'PROCESSING' AND locked_at < now() - interval '5 minutes')
                  )
                ORDER BY available_at, created_at
                FOR UPDATE SKIP LOCKED
                LIMIT :batch_size
            )
            UPDATE public.fpo_event_inbox AS e
            SET status = 'PROCESSING', locked_at = now(),
                attempts = e.attempts + 1,
                attempts_in_cycle = e.attempts_in_cycle + 1,
                updated_at = now()
            FROM candidates
            WHERE e.inbox_id = candidates.inbox_id
            RETURNING e.*;
            """
        ),
        {"batch_size": batch_size},
    ).mappings().all()
    return [
        {
            **dict(row),
            "payload": row["event_payload"] or {},
            "event_id": row["event_id"],
        }
        for row in rows
    ]


def record_event_inbox(conn: Connection, event: dict[str, Any], *, consumer_name: str = "fpo_management_service") -> str:
    payload = validate_auth_user_created_event(event)
    payload_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    inserted_id = conn.execute(
        text(
            """
            INSERT INTO public.fpo_event_inbox
                (consumer_name, event_id, event_type, event_version, subject_id,
                 payload_hash, event_payload, correlation_id, occurred_at, status, attempts,
                 delivery_count, poison_count)
            VALUES (:consumer, :event_id, :event_type, :event_version, :subject_id,
                    :payload_hash, CAST(:event_payload AS jsonb), :correlation_id,
                    CAST(:occurred_at AS timestamptz), 'RECEIVED', 0, 1, 0)
            ON CONFLICT (consumer_name, event_id) DO NOTHING
            RETURNING inbox_id;
            """
        ),
        {
            "consumer": consumer_name,
            "event_id": str(event["event_id"]),
            "event_type": event["event_type"],
            "event_version": int(event["event_version"]),
            "subject_id": event["subject_id"],
            "payload_hash": payload_hash,
            "event_payload": json.dumps(payload),
            "correlation_id": str(event["correlation_id"]),
            "occurred_at": event["occurred_at"],
        },
    ).scalar_one_or_none()
    if inserted_id:
        return "ACCEPTED"

    existing = conn.execute(
        text("""
            SELECT inbox_id, payload_hash, status
            FROM public.fpo_event_inbox
            WHERE consumer_name = :consumer AND event_id = :event_id
            FOR UPDATE;
        """),
        {"consumer": consumer_name, "event_id": str(event["event_id"])},
    ).mappings().one()
    if existing["payload_hash"] == payload_hash:
        conn.execute(
            text("""
                UPDATE public.fpo_event_inbox
                SET delivery_count = delivery_count + 1, updated_at = now()
                WHERE inbox_id = :inbox_id;
            """),
            {"inbox_id": existing["inbox_id"]},
        )
        return "DUPLICATE"

    conn.execute(
        text("""
            UPDATE public.fpo_event_inbox
            SET status = 'DEAD', error_code = 'POISON_EVENT',
                delivery_count = delivery_count + 1, poison_count = poison_count + 1,
                last_error = 'Event ID was delivered again with a different payload hash.',
                locked_at = NULL, updated_at = now()
            WHERE inbox_id = :inbox_id;
        """),
        {"inbox_id": existing["inbox_id"]},
    )
    return "POISON_EVENT"


def mark_event_inbox_processed(conn: Connection, event_id: UUID | str, *, consumer_name: str = "fpo_management_service") -> None:
    conn.execute(
        text("""
            UPDATE public.fpo_event_inbox
            SET status = 'PROCESSED', processed_at = now(), locked_at = NULL, updated_at = now()
            WHERE consumer_name = :consumer AND event_id = :event_id
              AND status = 'PROCESSING';
        """),
        {"consumer": consumer_name, "event_id": str(event_id)},
    )


def mark_event_inbox_failed(conn: Connection, event_id: UUID | str, error: str, *, consumer_name: str = "fpo_management_service") -> None:
    conn.execute(
        text("""
            UPDATE public.fpo_event_inbox
            SET status = CASE WHEN attempts_in_cycle >= 10 THEN 'DEAD' ELSE 'FAILED' END,
                error_code = CASE WHEN attempts_in_cycle >= 10 THEN 'PROVISIONING_ATTEMPTS_EXHAUSTED' ELSE 'PROVISIONING_RETRYABLE' END,
                last_error = :error, locked_at = NULL,
                available_at = now() + interval '30 seconds', updated_at = now()
            WHERE consumer_name = :consumer AND event_id = :event_id
              AND status = 'PROCESSING';
        """),
        {"consumer": consumer_name, "event_id": str(event_id), "error": error[:2000]},
    )


def record_provisioning_status_event(
    conn: Connection,
    *,
    fpo_id: UUID | str,
    status_from: dict[str, Any],
    status_to: dict[str, Any],
    reason: str,
    correlation_id: UUID | str | None = None,
) -> None:
    conn.execute(
        text("""
            INSERT INTO public.fpo_organization_status_events
                (fpo_id, status_from, status_to, reason, metadata)
            VALUES (:fpo_id, CAST(:status_from AS jsonb), CAST(:status_to AS jsonb),
                    :reason, CAST(:metadata AS jsonb));
        """),
        {
            "fpo_id": str(fpo_id),
            "status_from": json.dumps(status_from),
            "status_to": json.dumps(status_to),
            "reason": reason,
            "metadata": json.dumps(
                {"correlation_id": str(correlation_id) if correlation_id else None}
            ),
        },
    )


def set_provisioning_error(
    conn: Connection,
    *,
    user_id: UUID | str,
    error_code: str,
    error: str,
    correlation_id: UUID | str | None,
) -> None:
    current = conn.execute(
        text("""
            SELECT fpo_id, provisioning_status, provisioning_step
            FROM public.fpo_organizations
            WHERE auth_user_id = :user_id
            FOR UPDATE;
        """),
        {"user_id": str(user_id)},
    ).mappings().first()
    if not current:
        return
    conn.execute(
        text("""
            UPDATE public.fpo_organizations
            SET provisioning_status = 'FAILED',
                provisioning_step = 'FAILED',
                provisioning_error_code = :error_code,
                provisioning_error = :error,
                provisioning_correlation_id = COALESCE(:correlation_id, provisioning_correlation_id),
                updated_at = now(), version = version + 1
            WHERE auth_user_id = :user_id;
        """),
        {
            "user_id": str(user_id),
            "error_code": error_code,
            "error": error[:500],
            "correlation_id": str(correlation_id) if correlation_id else None,
        },
    )
    if current["provisioning_status"] != "FAILED" or current["provisioning_step"] != "FAILED":
        record_provisioning_status_event(
            conn,
            fpo_id=current["fpo_id"],
            status_from={
                "provisioning_status": current["provisioning_status"],
                "provisioning_step": current["provisioning_step"],
            },
            status_to={"provisioning_status": "FAILED", "provisioning_step": "FAILED"},
            reason=error_code,
            correlation_id=correlation_id,
        )


def provision_fpo(conn: Connection, payload: dict[str, Any]) -> dict[str, Any]:
    user_id = str(payload["user_id"])
    basics = payload.get("signup_profile") or {}
    if payload.get("authorised_fpo_representative") is not True:
        raise ValueError("FPO_REPRESENTATIVE_AUTHORITY_REQUIRED")
    try:
        state_code = int(basics.get("state_code"))
    except (TypeError, ValueError) as exc:
        raise ValueError("FPO_STATE_CODE_INVALID") from exc
    state = conn.execute(
        text("SELECT state_name FROM public.states WHERE state_code = :state_code"),
        {"state_code": state_code},
    ).mappings().first()
    if not state:
        raise ValueError("FPO_STATE_CODE_INVALID")
    user = conn.execute(
        text("SELECT role, is_active, is_verified FROM public.users WHERE user_id = :user_id"),
        {"user_id": user_id},
    ).mappings().first()
    if not user or user["role"] != "fpo" or not user["is_active"] or not user["is_verified"]:
        raise ValueError("FPO_AUTH_USER_INVALID")
    existing = conn.execute(
        text("SELECT fpo_id, public_fpo_id, provisioning_status, provisioning_step, profile_fpo_id FROM public.fpo_organizations WHERE auth_user_id = :user_id FOR UPDATE"),
        {"user_id": user_id},
    ).mappings().first()

    if existing:
        org = dict(existing)
        next_status = "PROFILE_PENDING" if org.get("profile_fpo_id") is None else org["provisioning_status"]
        next_step = "CREATING_PROFILE" if org.get("profile_fpo_id") is None else org["provisioning_step"]
        conn.execute(
            text("""
                UPDATE public.fpo_organizations
                SET provisioning_status = CASE WHEN profile_fpo_id IS NULL THEN 'PROFILE_PENDING' ELSE provisioning_status END,
                    provisioning_step = CASE WHEN profile_fpo_id IS NULL THEN 'CREATING_PROFILE' ELSE provisioning_step END,
                    provisioning_correlation_id = COALESCE(provisioning_correlation_id, :correlation_id),
                    updated_at = now()
                WHERE fpo_id = :fpo_id;
            """),
            {"fpo_id": str(org["fpo_id"]), "correlation_id": payload.get("_correlation_id")},
        )
        if org["provisioning_status"] != next_status or org["provisioning_step"] != next_step:
            record_provisioning_status_event(
                conn,
                fpo_id=org["fpo_id"],
                status_from={
                    "provisioning_status": org["provisioning_status"],
                    "provisioning_step": org["provisioning_step"],
                },
                status_to={
                    "provisioning_status": next_status,
                    "provisioning_step": next_step,
                },
                reason="FPO provisioning resumed",
                correlation_id=payload.get("_correlation_id"),
            )
            org["provisioning_status"] = next_status
            org["provisioning_step"] = next_step
    else:
        sequence = int(conn.execute(text("SELECT nextval('public.fpo_public_number_seq')")).scalar_one())
        occurred_at = datetime.fromisoformat(str(payload.get("_occurred_at") or datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00"))
        public_id = public_fpo_id(state_code, sequence, occurred_at)
        org = dict(conn.execute(
            text(
                """
                INSERT INTO public.fpo_organizations
                    (auth_user_id, public_fpo_id, provisioning_status, provisioning_step, provisioning_correlation_id)
                VALUES (:user_id, :public_fpo_id, 'PROFILE_PENDING', 'CREATING_PROFILE', :correlation_id)
                RETURNING fpo_id, public_fpo_id, provisioning_status, provisioning_step, profile_fpo_id;
                """
            ),
            {"user_id": user_id, "public_fpo_id": public_id, "correlation_id": payload.get("_correlation_id")},
        ).mappings().one())
        record_provisioning_status_event(
            conn,
            fpo_id=org["fpo_id"],
            status_from={"provisioning_status": "PENDING", "provisioning_step": None},
            status_to={
                "provisioning_status": "PROFILE_PENDING",
                "provisioning_step": "CREATING_PROFILE",
            },
            reason="FPO account provisioning started",
            correlation_id=payload.get("_correlation_id"),
        )
    return {**org, "auth_user_id": user_id, "signup_profile": basics}


def complete_fpo_provisioning(
    conn: Connection,
    *,
    user_id: UUID | str,
    profile_fpo_id: UUID | str,
    correlation_id: UUID | str,
) -> dict[str, Any]:
    org = conn.execute(
        text("""
            SELECT fpo_id, public_fpo_id, provisioning_status, provisioning_step, profile_fpo_id
            FROM public.fpo_organizations
            WHERE auth_user_id = :user_id
            FOR UPDATE;
        """),
        {"user_id": str(user_id)},
    ).mappings().first()
    if not org:
        raise ValueError("FPO_ORGANIZATION_NOT_FOUND")
    if org["profile_fpo_id"] and str(org["profile_fpo_id"]) != str(profile_fpo_id):
        raise ValueError("FPO_PROFILE_LINK_CONFLICT")
    conn.execute(
        text(
            """
            UPDATE public.fpo_organizations
            SET profile_fpo_id = :profile_fpo_id,
                provisioning_status = 'READY', provisioning_step = 'COMPLETED',
                provisioning_error = NULL, provisioning_error_code = NULL,
                provisioning_correlation_id = :correlation_id,
                updated_at = now(), version = version + 1
            WHERE fpo_id = :fpo_id;
            """
        ),
        {
            "fpo_id": str(org["fpo_id"]),
            "profile_fpo_id": str(profile_fpo_id),
            "correlation_id": str(correlation_id),
        },
    )
    if org["provisioning_status"] != "READY":
        record_provisioning_status_event(
            conn,
            fpo_id=org["fpo_id"],
            status_from={
                "provisioning_status": org["provisioning_status"],
                "provisioning_step": org["provisioning_step"],
            },
            status_to={
                "provisioning_status": "READY",
                "provisioning_step": "COMPLETED",
                "profile_fpo_id": str(profile_fpo_id),
            },
            reason="FPO account provisioning completed",
            correlation_id=correlation_id,
        )
    return {**dict(org), "profile_fpo_id": str(profile_fpo_id), "provisioning_status": "READY"}


def get_bootstrap_status(conn: Connection, user_id: UUID | str) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.public_fpo_id, o.provisioning_status, o.provisioning_step,
                   o.provisioning_error_code, o.provisioning_error,
                   o.lifecycle_status, o.verification_status,
                   o.profile_fpo_id,
                   p.fpo_id AS linked_profile_fpo_id,
                   p.fpo_name AS display_name,
                   o.provisioning_correlation_id AS correlation_id,
                   e.attempts AS attempt_count
            FROM public.fpo_organizations o
            LEFT JOIN public.fpo_users u ON u.user_id = o.auth_user_id AND u.is_active = TRUE
            LEFT JOIN public.fpos p ON p.fpo_id = u.fpo_id AND p.is_active = TRUE
            LEFT JOIN LATERAL (
                SELECT attempts FROM public.fpo_event_inbox
                WHERE subject_id = o.auth_user_id
                  AND consumer_name = 'fpo_management_service'
                ORDER BY created_at DESC LIMIT 1
            ) e ON TRUE
            WHERE o.auth_user_id = :user_id
            LIMIT 1;
            """
        ),
        {"user_id": str(user_id)},
    ).mappings().first()
    if not row:
        event = conn.execute(
            text("""
                SELECT status, error_code, correlation_id, attempts,
                       event_payload->'signup_profile'->>'organisation_name' AS organization_name
                FROM public.fpo_event_inbox
                WHERE subject_id = :user_id
                  AND consumer_name = 'fpo_management_service'
                ORDER BY created_at DESC LIMIT 1;
            """),
            {"user_id": str(user_id)},
        ).mappings().first()
        if event and event["status"] in {"FAILED", "DEAD"}:
            return {
                "schema_version": 2,
                "status": "FAILED",
                "step": "FAILED",
                "retryable": event.get("error_code") != "POISON_EVENT",
                "next_poll_after_seconds": None,
                "correlation_id": str(event["correlation_id"]) if event.get("correlation_id") else None,
                "organization": None,
                "organization_name": event.get("organization_name"),
                "attempt_count": int(event.get("attempts") or 0),
                "error": {
                    "code": event.get("error_code") or "PROVISIONING_FAILED",
                    "message": "We could not finish setting up your organization. Contact support with the reference ID.",
                },
            }
        if event:
            return {
                "schema_version": 2,
                "status": "PROCESSING",
                "step": "CREATING_ORGANIZATION",
                "retryable": False,
                "next_poll_after_seconds": 2,
                "correlation_id": str(event["correlation_id"]) if event.get("correlation_id") else None,
                "organization": None,
                "organization_name": event.get("organization_name"),
                "attempt_count": int(event.get("attempts") or 0),
                "error": None,
            }
        return {
            "schema_version": 2,
            "status": "PENDING",
            "step": "WAITING_FOR_EVENT",
            "retryable": True,
            "next_poll_after_seconds": 2,
            "correlation_id": None,
            "organization": None,
            "organization_name": None,
            "error": None,
        }
    result = dict(row)
    status = result.get("provisioning_status") or "PENDING"
    ready = status == "READY"
    failed = status == "FAILED"
    return {
        "schema_version": 2,
        "status": status,
        "step": result.get("provisioning_step") or ("COMPLETED" if ready else "CREATING_ORGANIZATION"),
        "retryable": failed,
        "next_poll_after_seconds": None if ready or failed else 5,
        "correlation_id": str(result["correlation_id"]) if result.get("correlation_id") else None,
        "organization": {
            "fpo_id": str(result["fpo_id"]),
            "profile_fpo_id": str(result["profile_fpo_id"]) if result.get("profile_fpo_id") else None,
            "public_fpo_id": result["public_fpo_id"],
            "display_name": result.get("display_name"),
            "provisioning_status": status,
            "lifecycle_status": result.get("lifecycle_status"),
            "verification_status": result.get("verification_status"),
        },
        "attempt_count": int(result.get("attempt_count") or 0),
        "error": (
            {"code": result.get("provisioning_error_code") or "PROVISIONING_FAILED",
             "message": result.get("provisioning_error") or "We could not finish setting up your organization."}
            if failed else None
        ),
        "next_action": (
            {"code": "COMPLETE_PROFILE", "route": "/fpo/profile"}
            if ready and result.get("verification_status") == "PROFILE_INCOMPLETE"
            else None
        ),
    }


def list_provisioning_cases(
    conn: Connection,
    *,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        text("""
            SELECT e.event_id, e.subject_id AS auth_user_id, e.status AS event_status,
                   e.error_code, e.attempts, e.correlation_id, e.created_at, e.updated_at,
                   o.fpo_id, o.public_fpo_id, o.provisioning_status,
                   o.provisioning_step, o.provisioning_error_code,
                   o.provisioning_error, o.updated_at AS organization_updated_at,
                   e.event_payload->'signup_profile'->>'organisation_name' AS organization_name
            FROM public.fpo_event_inbox e
            LEFT JOIN public.fpo_organizations o ON o.auth_user_id = e.subject_id
            WHERE e.consumer_name = 'fpo_management_service'
              AND (:status IS NULL OR e.status = :status)
            ORDER BY e.created_at DESC
            LIMIT :limit OFFSET :offset;
        """),
        {"status": status, "limit": limit, "offset": offset},
    ).mappings().all()
    return [dict(row) for row in rows]


def get_provisioning_case(conn: Connection, fpo_id: UUID | str) -> dict[str, Any] | None:
    row = conn.execute(
        text("""
            SELECT e.event_id, e.subject_id AS auth_user_id, e.event_type, e.event_version,
                   e.status AS event_status, e.error_code, e.attempts, e.correlation_id,
                   e.created_at, e.updated_at, o.fpo_id, o.profile_fpo_id,
                   o.public_fpo_id, o.provisioning_status, o.provisioning_step,
                   o.provisioning_error_code, o.provisioning_error,
                   o.lifecycle_status, o.verification_status,
                   e.event_payload->'signup_profile'->>'organisation_name' AS organization_name
            FROM public.fpo_organizations o
            LEFT JOIN LATERAL (
                SELECT * FROM public.fpo_event_inbox
                WHERE subject_id = o.auth_user_id
                  AND consumer_name = 'fpo_management_service'
                ORDER BY created_at DESC LIMIT 1
            ) e ON TRUE
            WHERE o.fpo_id = :fpo_id;
        """),
        {"fpo_id": str(fpo_id)},
    ).mappings().first()
    return dict(row) if row else None


def retry_provisioning_event(
    conn: Connection,
    *,
    event_id: UUID | str,
    actor_user_id: UUID | str,
    reason: str,
) -> dict[str, Any]:
    event = conn.execute(
        text("""
            SELECT inbox_id, subject_id, status, attempts, error_code, correlation_id
            FROM public.fpo_event_inbox
            WHERE event_id = :event_id AND consumer_name = 'fpo_management_service'
            FOR UPDATE;
        """),
        {"event_id": str(event_id)},
    ).mappings().first()
    if not event:
        raise ValueError("FPO_PROVISIONING_EVENT_NOT_FOUND")
    if event["status"] not in {"FAILED", "DEAD"}:
        raise ValueError("FPO_PROVISIONING_EVENT_NOT_RETRYABLE")
    if event.get("error_code") == "POISON_EVENT":
        raise ValueError("FPO_POISON_EVENT_NOT_RETRYABLE")
    conn.execute(
        text("""
            UPDATE public.fpo_event_inbox
            SET status = 'RECEIVED', error_code = NULL, last_error = NULL,
                attempts_in_cycle = 0, available_at = now(), locked_at = NULL, updated_at = now()
            WHERE inbox_id = :inbox_id;
        """),
        {"inbox_id": event["inbox_id"]},
    )
    previous_org = conn.execute(
        text("""
            SELECT fpo_id, provisioning_status, provisioning_step
            FROM public.fpo_organizations
            WHERE auth_user_id = :user_id
            FOR UPDATE;
        """),
        {"user_id": str(event["subject_id"])},
    ).mappings().first()
    organization = conn.execute(
        text("""
            UPDATE public.fpo_organizations
            SET provisioning_status = 'PROFILE_PENDING',
                provisioning_step = 'RETRY_QUEUED',
                provisioning_error = NULL, provisioning_error_code = NULL,
                updated_at = now(), version = version + 1
            WHERE auth_user_id = :user_id AND provisioning_status <> 'READY'
            RETURNING fpo_id;
        """),
        {"user_id": str(event["subject_id"])},
    ).mappings().first()
    if organization and previous_org:
        record_provisioning_status_event(
            conn,
            fpo_id=organization["fpo_id"],
            status_from={
                "provisioning_status": previous_org["provisioning_status"],
                "provisioning_step": previous_org["provisioning_step"],
            },
            status_to={
                "provisioning_status": "PROFILE_PENDING",
                "provisioning_step": "RETRY_QUEUED",
            },
            reason="FPO provisioning retry requested",
            correlation_id=event["correlation_id"],
        )
    conn.execute(
        text("""
            INSERT INTO public.fpo_audit_events
                (fpo_id, actor_user_id, action, target_type, target_id, metadata)
            VALUES (:fpo_id, :actor_user_id, 'FPO_PROVISIONING_RETRY', 'FPO_EVENT', :event_id,
                    CAST(:metadata AS jsonb));
        """),
        {
            "fpo_id": str(organization["fpo_id"]) if organization else None,
            "actor_user_id": str(actor_user_id),
            "event_id": str(event_id),
            "metadata": json.dumps(
                {
                    "reason": reason.strip(),
                    "previous_status": event["status"],
                    "previous_attempts": int(event["attempts"]),
                }
            ),
        },
    )
    return {"event_id": str(event_id), "status": "RECEIVED", "fpo_id": str(organization["fpo_id"]) if organization else None}


def retry_fpo_provisioning(
    conn: Connection,
    *,
    fpo_id: UUID | str,
    actor_user_id: UUID | str,
    reason: str,
) -> dict[str, Any]:
    event_id = conn.execute(
        text("""
            SELECT e.event_id
            FROM public.fpo_organizations o
            JOIN LATERAL (
                SELECT event_id FROM public.fpo_event_inbox
                WHERE subject_id = o.auth_user_id
                  AND consumer_name = 'fpo_management_service'
                ORDER BY created_at DESC LIMIT 1
            ) e ON TRUE
            WHERE o.fpo_id = :fpo_id;
        """),
        {"fpo_id": str(fpo_id)},
    ).scalar_one_or_none()
    if not event_id:
        raise ValueError("FPO_PROVISIONING_EVENT_NOT_FOUND")
    return retry_provisioning_event(
        conn,
        event_id=event_id,
        actor_user_id=actor_user_id,
        reason=reason,
    )


def fpo_provisioning_metrics(conn: Connection) -> dict[str, float | int]:
    row = conn.execute(
        text("""
            SELECT
                COALESCE(SUM(delivery_count), 0) AS events_received,
                COALESCE(SUM(GREATEST(delivery_count - 1, 0)), 0) AS duplicates,
                COALESCE(SUM(poison_count), 0) AS poison,
                COALESCE(SUM(attempts), 0) AS attempts,
                COUNT(*) FILTER (WHERE status = 'PROCESSED') AS completed,
                COUNT(*) FILTER (WHERE status IN ('FAILED', 'DEAD')) AS failed,
                COALESCE(SUM(GREATEST(attempts - 1, 0)), 0) AS retries,
                COALESCE(AVG(EXTRACT(EPOCH FROM (processed_at - created_at)))
                    FILTER (WHERE status = 'PROCESSED'), 0) AS avg_duration_seconds,
                COUNT(*) FILTER (WHERE status IN ('RECEIVED', 'FAILED')) AS queue_depth,
                COALESCE(
                    MAX(EXTRACT(EPOCH FROM (now() - created_at)))
                        FILTER (WHERE status IN ('RECEIVED', 'FAILED')),
                    0
                ) AS oldest_event_age_seconds
            FROM public.fpo_event_inbox
            WHERE consumer_name = 'fpo_management_service';
        """)
    ).mappings().one()
    return {key: float(value) if key == "avg_duration_seconds" else int(value) for key, value in row.items()}


def get_portal_bootstrap(conn: Connection, user_id: UUID | str) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.public_fpo_id, o.lifecycle_status, o.verification_status,
                   o.verification_level, o.commercial_status, o.approved_at,
                   o.provisioning_status, o.provisioning_step, o.provisioning_error_code,
                   o.provisioning_error, o.provisioning_correlation_id,
                   o.profile_fpo_id, p.display_name, p.fpo_name,
                   p.profile_completion_percentage
            FROM public.fpo_organizations o
            LEFT JOIN public.fpos p ON p.fpo_id = o.profile_fpo_id
            WHERE o.auth_user_id = :user_id
            LIMIT 1;
            """
        ),
        {"user_id": str(user_id)},
    ).mappings().first()
    if not row:
        return {"status": "PENDING", "organization": None, "profile": None, "verification": None, "class": None, "entitlements": {}}
    entitlements = resolve_fpo_entitlements(conn, user_id=user_id)
    return {
        "status": "READY" if row["provisioning_status"] == "READY" else row["provisioning_status"],
        "organization": {
            "fpo_id": str(row["fpo_id"]),
            "profile_fpo_id": str(row["profile_fpo_id"]) if row.get("profile_fpo_id") else None,
            "public_fpo_id": row["public_fpo_id"],
            "display_name": row["display_name"] or row["fpo_name"],
            "provisioning_status": row["provisioning_status"],
            "provisioning_step": row["provisioning_step"],
            "provisioning_error_code": row["provisioning_error_code"],
            "provisioning_error": row["provisioning_error"],
            "correlation_id": str(row["provisioning_correlation_id"]) if row.get("provisioning_correlation_id") else None,
            "lifecycle_status": row["lifecycle_status"],
        },
        "profile": {"completion_percentage": row["profile_completion_percentage"] or 0, "missing_fields": []},
        "verification": {"status": row["verification_status"], "level": row["verification_level"], "approved_at": row["approved_at"]},
        "class": {"code": entitlements.get("class_code"), "commercial_status": row["commercial_status"]},
        "entitlements": entitlements.get("features", {}),
    }


def get_verification_for_user(conn: Connection, user_id: UUID | str) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.public_fpo_id, o.verification_status,
                   o.verification_level, o.discoverable,
                   s.submission_id, s.status AS submission_status,
                   s.reviewer_note, s.reviewed_at, s.created_at AS submitted_at,
                   p.profile_version
            FROM public.fpo_organizations o
            LEFT JOIN public.fpos p ON p.fpo_id = o.profile_fpo_id
            LEFT JOIN LATERAL (
                SELECT * FROM public.fpo_verification_submissions
                WHERE fpo_id = o.fpo_id
                ORDER BY created_at DESC LIMIT 1
            ) s ON TRUE
            WHERE o.auth_user_id = :user_id
            LIMIT 1;
            """
        ),
        {"user_id": str(user_id)},
    ).mappings().first()
    return dict(row) if row else {"verification_status": "PROFILE_INCOMPLETE", "submission_id": None}


ALLOWED_VERIFICATION_DOCUMENT_TYPES = {
    "REGISTRATION_CERTIFICATE", "PAN_CARD", "GST_CERTIFICATE",
    "AUTHORIZED_REPRESENTATIVE_DECLARATION", "ADDRESS_PROOF", "BANK_PROOF",
}
ALLOWED_VERIFICATION_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_VERIFICATION_DOCUMENT_BYTES = 20 * 1024 * 1024


def create_document_upload_intent(
    conn: Connection, *, user_id: UUID | str, document_type: str,
    filename: str, mime_type: str, size_bytes: int, checksum: str,
) -> dict[str, Any]:
    normalized_type = document_type.strip().upper()
    if normalized_type not in ALLOWED_VERIFICATION_DOCUMENT_TYPES:
        raise ValueError("Unsupported verification document type")
    if mime_type.lower() not in ALLOWED_VERIFICATION_MIME_TYPES:
        raise ValueError("Only PDF, JPEG, and PNG documents are accepted")
    if size_bytes <= 0 or size_bytes > MAX_VERIFICATION_DOCUMENT_BYTES:
        raise ValueError("Document must be between 1 byte and 20 MB")
    if not re.fullmatch(r"[A-Fa-f0-9]{32,128}", checksum or ""):
        raise ValueError("A hexadecimal document checksum is required")
    org = conn.execute(text("""
        SELECT o.fpo_id, s.submission_id
        FROM public.fpo_organizations o
        LEFT JOIN LATERAL (
            SELECT submission_id FROM public.fpo_verification_submissions
            WHERE fpo_id = o.fpo_id
            ORDER BY created_at DESC LIMIT 1
        ) s ON TRUE
        WHERE o.auth_user_id = :user_id AND o.provisioning_status = 'READY'
    """), {"user_id": str(user_id)}).mappings().first()
    if not org:
        raise ValueError("FPO_PROVISIONING_PENDING")
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename.strip())[:180] or "document"
    object_key = f"fpo/{org['fpo_id']}/verification/{uuid4()}/{safe_name}"
    row = conn.execute(text("""
        INSERT INTO public.fpo_verification_documents
            (fpo_id, submission_id, document_type, object_key, original_filename,
             mime_type, declared_mime_type, size_bytes, checksum, declared_checksum,
             uploaded_by, upload_status, scan_status, validation_status)
        VALUES (:fpo_id, :submission_id, :document_type, :object_key, :filename,
                :mime_type, :mime_type, :size_bytes, :checksum, :checksum, :uploaded_by, 'UPLOADING', 'PENDING', 'PENDING')
        RETURNING document_id, fpo_id, submission_id, document_type, object_key,
                  original_filename, mime_type, size_bytes, checksum, upload_status,
                  scan_status, validation_status, created_at
    """), {
        "fpo_id": str(org["fpo_id"]), "submission_id": org["submission_id"],
        "document_type": normalized_type, "object_key": object_key,
        "filename": safe_name, "mime_type": mime_type.lower(), "size_bytes": size_bytes,
        "checksum": checksum.lower(), "uploaded_by": str(user_id),
    }).mappings().one()
    return {**dict(row), "upload_url": None, "upload_url_status": "STORAGE_ADAPTER_REQUIRED"}


def create_document_replacement_intent(conn: Connection, *, user_id: UUID | str, document_id: UUID | str, filename: str, mime_type: str, size_bytes: int, checksum: str) -> dict[str, Any]:
    old = conn.execute(text("""
        SELECT d.* FROM public.fpo_verification_documents d
        JOIN public.fpo_organizations o ON o.fpo_id = d.fpo_id AND o.auth_user_id = :user_id
        WHERE d.document_id = :document_id AND d.deleted_at IS NULL
        FOR UPDATE
    """), {"user_id": str(user_id), "document_id": str(document_id)}).mappings().first()
    if not old:
        raise ValueError("FPO_DOCUMENT_NOT_FOUND")
    if old["upload_status"] != "AVAILABLE" or old["scan_status"] not in {"CLEAN", "QUARANTINED", "DEAD"}:
        raise ValueError("FPO_DOCUMENT_NOT_READY_FOR_REPLACEMENT")
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename.strip())[:180] or "document"
    new_id = uuid4()
    row = conn.execute(text("""
        INSERT INTO public.fpo_verification_documents
            (document_id, fpo_id, document_type, document_version, object_key, original_filename,
             mime_type, declared_mime_type, size_bytes, checksum, declared_checksum,
             uploaded_by, upload_status, scan_status, validation_status, supersedes_document_id)
        VALUES (:document_id, :fpo_id, :document_type, :document_version, :object_key, :filename,
                :mime_type, :mime_type, :size_bytes, :checksum, :checksum,
                :uploaded_by, 'UPLOADING', 'PENDING', 'PENDING', :supersedes)
        RETURNING document_id, fpo_id, document_type, document_version, object_key,
                  original_filename, mime_type, size_bytes, checksum, upload_status,
                  scan_status, validation_status, created_at
    """), {
        "document_id": str(new_id), "fpo_id": str(old["fpo_id"]), "document_type": old["document_type"],
        "document_version": int(old.get("document_version") or 1) + 1,
        "object_key": f"fpo-verification/{old['fpo_id']}/{new_id}/{int(old.get('document_version') or 1) + 1}/source",
        "filename": safe_name, "mime_type": mime_type.lower(), "size_bytes": size_bytes,
        "checksum": checksum.lower(), "uploaded_by": str(user_id), "supersedes": str(old["document_id"]),
    }).mappings().one()
    conn.execute(text("""
        UPDATE public.fpo_verification_documents
        SET replaced_by_document_id = :replacement, updated_at = now()
        WHERE document_id = :document_id
    """), {"replacement": str(new_id), "document_id": str(document_id)})
    return {**dict(row), "supersedes_document_id": old["document_id"]}


def finalize_document_upload(conn: Connection, *, user_id: UUID | str, document_id: UUID | str, checksum: str) -> dict[str, Any]:
    row = conn.execute(text("""
        UPDATE public.fpo_verification_documents d
        SET upload_status = 'AVAILABLE',
            scan_status = 'QUEUED',
            storage_version = storage_version + 1,
            updated_at = now()
        FROM public.fpo_organizations o
        WHERE d.document_id = :document_id AND d.fpo_id = o.fpo_id
          AND o.auth_user_id = :user_id AND d.upload_status = 'UPLOADING'
          AND d.checksum = :checksum
        RETURNING d.document_id, d.upload_status, d.scan_status, d.validation_status,
                  d.checksum, d.object_key, d.updated_at
    """), {"document_id": str(document_id), "user_id": str(user_id), "checksum": checksum.lower()}).mappings().first()
    if not row:
        raise ValueError("Upload intent was not found or is no longer active")
    return {**dict(row), "next_step": "MALWARE_SCAN_AND_VALIDATION"}


def get_document_upload_target(conn: Connection, *, user_id: UUID | str, document_id: UUID | str) -> dict[str, Any]:
    row = conn.execute(text("""
        SELECT d.document_id, d.object_key, d.mime_type, d.size_bytes, d.upload_status
        FROM public.fpo_verification_documents d
        JOIN public.fpo_organizations o ON o.fpo_id = d.fpo_id
        WHERE d.document_id = :document_id
          AND o.auth_user_id = :user_id
          AND d.deleted_at IS NULL
    """), {"document_id": str(document_id), "user_id": str(user_id)}).mappings().first()
    if not row:
        raise ValueError("Verification document was not found")
    if row["upload_status"] != "UPLOADING":
        raise ValueError("Verification document is no longer accepting content")
    return dict(row)


def list_verification_documents(conn: Connection, *, user_id: UUID | str) -> list[dict[str, Any]]:
    rows = conn.execute(text("""
        SELECT d.document_id, d.submission_id, d.document_type, d.original_filename,
               d.mime_type, d.size_bytes, d.document_version, d.upload_status, d.scan_status,
               d.verified_checksum,
               d.validation_status, d.validation_reason, d.created_at
        FROM public.fpo_verification_documents d
        JOIN public.fpo_organizations o ON o.fpo_id = d.fpo_id AND o.auth_user_id = :user_id
        WHERE d.deleted_at IS NULL
        ORDER BY d.created_at DESC
    """), {"user_id": str(user_id)}).mappings().all()
    return [dict(row) for row in rows]


def delete_verification_document(conn: Connection, *, user_id: UUID | str, document_id: UUID | str) -> dict[str, Any]:
    row = conn.execute(text("""
        UPDATE public.fpo_verification_documents d
        SET deleted_at = now(), deletion_status = 'QUEUED', deleted_by = :user_id,
            deletion_reason = 'OWNER_REQUEST', updated_at = now()
        FROM public.fpo_organizations o
        WHERE d.document_id = :document_id
          AND d.fpo_id = o.fpo_id
          AND o.auth_user_id = :user_id
          AND d.deleted_at IS NULL
          AND o.verification_status NOT IN ('SUBMITTED','UNDER_REVIEW','APPROVED')
        RETURNING d.document_id, d.object_key, d.original_filename
    """), {"document_id": str(document_id), "user_id": str(user_id)}).mappings().first()
    if not row:
        raise ValueError("This document cannot be removed after verification submission, or it was not found")
    conn.execute(text("""
        INSERT INTO public.fpo_verification_storage_deletions (document_id, object_key)
        VALUES (:document_id, :object_key)
    """), {"document_id": str(row["document_id"]), "object_key": row["object_key"]})
    return dict(row)


def list_admin_verification_documents(conn: Connection, *, fpo_id: UUID | str) -> list[dict[str, Any]]:
    rows = conn.execute(text("""
        SELECT d.document_id, d.fpo_id, d.submission_id, d.document_type, d.original_filename,
               d.mime_type, d.size_bytes, d.storage_version, d.checksum, d.verified_checksum,
               d.upload_status, d.scan_status, d.scan_error, d.validation_status,
               d.validation_reason, d.created_at, d.updated_at
        FROM public.fpo_verification_documents d
        WHERE d.fpo_id = :fpo_id AND d.deleted_at IS NULL
        ORDER BY d.created_at DESC
    """), {"fpo_id": str(fpo_id)}).mappings().all()
    return [dict(row) for row in rows]


def get_admin_verification_document_target(conn: Connection, *, document_id: UUID | str) -> dict[str, Any]:
    row = conn.execute(text("""
        SELECT document_id, object_key, original_filename, mime_type
        FROM public.fpo_verification_documents
        WHERE document_id = :document_id AND deleted_at IS NULL
    """), {"document_id": str(document_id)}).mappings().first()
    if not row:
        raise ValueError("Verification document was not found")
    return dict(row)


def list_verification_checklist(conn: Connection, *, fpo_id: UUID | str) -> list[dict[str, Any]]:
    rows = conn.execute(text("""
        SELECT r.checklist_result_id, r.case_id, r.checklist_key, r.result, r.note,
               r.checked_by, r.checked_at, c.submission_id
        FROM public.fpo_verification_checklist_results r
        JOIN public.fpo_verification_cases c ON c.case_id = r.case_id
        WHERE c.fpo_id = :fpo_id AND c.status IN ('OPEN','CLAIMED','UNDER_REVIEW','CHANGES_REQUIRED')
        ORDER BY r.checklist_key
    """), {"fpo_id": str(fpo_id)}).mappings().all()
    return [dict(row) for row in rows]


def update_verification_checklist(conn: Connection, *, admin_user_id: UUID | str, result_id: UUID | str, result: str, note: str | None) -> dict[str, Any]:
    if result not in {"PENDING", "PASS", "FAIL", "NOT_APPLICABLE"}:
        raise ValueError("Unsupported checklist result")
    row = conn.execute(text("""
        UPDATE public.fpo_verification_checklist_results r
        SET result = :result, note = :note, checked_by = :admin_user_id,
            checked_at = now()
        FROM public.fpo_verification_cases c
        WHERE r.checklist_result_id = :result_id AND c.case_id = r.case_id
          AND c.status = 'UNDER_REVIEW' AND c.assigned_reviewer_id = :admin_user_id
        RETURNING r.checklist_result_id, r.case_id, r.checklist_key, r.result, r.note, r.checked_by, r.checked_at, c.fpo_id
    """), {"result_id": str(result_id), "result": result, "note": note, "admin_user_id": str(admin_user_id)}).mappings().first()
    if not row:
        raise ValueError("Verification checklist item was not found")
    record_fpo_audit_event(conn, fpo_id=row["fpo_id"], actor_user_id=admin_user_id, action="FPO_VERIFICATION_CHECKLIST_UPDATED", target_type="verification_checklist", target_id=result_id, metadata={"result": result, "note": note})
    return dict(row)


def validate_verification_document(conn: Connection, *, admin_user_id: UUID | str, document_id: UUID | str, validation_status: str, reason: str | None, case_id: UUID | str | None = None, expected_case_version: int | None = None) -> dict[str, Any]:
    if validation_status not in {"VALID", "INVALID", "REPLACEMENT_REQUIRED"}:
        raise ValueError("FPO_DOCUMENT_VALIDATION_STATUS_INVALID")
    if validation_status != "VALID" and not reason:
        raise ValueError("FPO_DOCUMENT_VALIDATION_REASON_REQUIRED")
    row = conn.execute(text("""
        UPDATE public.fpo_verification_documents
        SET validation_status = :validation_status,
            validated_by = :admin_user_id, validated_at = now(), validation_reason = :reason,
            updated_at = now()
        WHERE document_id = :document_id AND upload_status = 'AVAILABLE' AND deleted_at IS NULL
          AND (:case_id IS NULL OR EXISTS (
              SELECT 1 FROM public.fpo_verification_submission_documents sd
              JOIN public.fpo_verification_cases c ON c.submission_id = sd.submission_id
              WHERE sd.document_id = public.fpo_verification_documents.document_id
                AND c.case_id = :case_id
                AND (:expected_case_version IS NULL OR c.case_version = :expected_case_version)
          ))
          AND (:validation_status <> 'VALID' OR scan_status = 'CLEAN')
        RETURNING document_id, fpo_id, scan_status, validation_status, validation_reason, validated_at
    """), {"document_id": str(document_id), "admin_user_id": str(admin_user_id), "validation_status": validation_status, "reason": reason, "case_id": str(case_id) if case_id else None, "expected_case_version": expected_case_version}).mappings().first()
    if not row:
        raise ValueError("Available verification document was not found")
    record_fpo_audit_event(conn, fpo_id=row["fpo_id"], actor_user_id=admin_user_id, action="FPO_DOCUMENT_VALIDATED", target_type="verification_document", target_id=document_id, metadata={"validation_status": validation_status, "reason": reason})
    return dict(row)


def claim_document_scan_batch(conn: Connection, *, batch_size: int) -> list[dict[str, Any]]:
    conn.execute(text("""
        INSERT INTO public.fpo_verification_document_events (document_id, fpo_id, event_type, metadata)
        SELECT document_id, fpo_id, 'SCAN_LEASE_EXPIRED',
               jsonb_build_object('previous_worker_id', scan_worker_id, 'previous_lease_expires_at', scan_lease_expires_at)
        FROM public.fpo_verification_documents
        WHERE upload_status = 'AVAILABLE' AND deleted_at IS NULL
          AND scan_status = 'SCANNING' AND scan_lease_expires_at < now()
    """))
    rows = conn.execute(text("""
        WITH candidates AS (
            SELECT document_id
            FROM public.fpo_verification_documents
            WHERE upload_status = 'AVAILABLE' AND deleted_at IS NULL
              AND scan_attempts < 5
              AND (
                  (scan_status IN ('PENDING','QUEUED','RETRY','FAILED') AND scan_next_attempt_at <= now())
                  OR (scan_status = 'SCANNING' AND scan_lease_expires_at < now())
              )
            ORDER BY created_at
            FOR UPDATE SKIP LOCKED LIMIT :batch_size
        )
        UPDATE public.fpo_verification_documents d
        SET scan_attempts = d.scan_attempts + 1,
            scan_status = 'SCANNING', scan_locked_at = now(), scan_worker_id = :worker_id,
            scan_lease_expires_at = now() + interval '5 minutes', updated_at = now()
        FROM candidates c
        WHERE d.document_id = c.document_id
        RETURNING d.document_id, d.object_key, d.size_bytes, d.mime_type, d.checksum,
                  d.scan_attempts, d.scan_worker_id
    """), {"batch_size": max(1, min(batch_size, 100)), "worker_id": os.getenv("HOSTNAME", "fpo-document-worker")}).mappings().all()
    return [dict(row) for row in rows]


def mark_document_scan_result(conn: Connection, *, document_id: UUID | str, scan_status: str, error: str | None = None, verified_checksum: str | None = None) -> None:
    if scan_status in {"CLEAN", "NOT_REQUIRED"}:
        conn.execute(text("""
            UPDATE public.fpo_verification_documents
        SET scan_status = :scan_status, verified_checksum = :verified_checksum,
            scan_engine = :scan_engine, scan_engine_version = :scan_engine_version,
            scan_signature_version = :scan_signature_version,
            scan_error = NULL, scanned_at = now(), scan_locked_at = NULL, scan_worker_id = NULL, scan_lease_expires_at = NULL, updated_at = now()
            WHERE document_id = :document_id
        """), {"document_id": str(document_id), "scan_status": scan_status, "verified_checksum": verified_checksum, "scan_engine": os.getenv("FPO_CLAMAV_HOST", "clamav"), "scan_engine_version": os.getenv("FPO_CLAMAV_VERSION", "configured"), "scan_signature_version": "magic-v1"})
        return
    if scan_status in {"INFECTED", "QUARANTINED"}:
        conn.execute(text("""
            UPDATE public.fpo_verification_documents
            SET scan_status = :scan_status, verified_checksum = :verified_checksum,
                scan_engine = :scan_engine, scan_engine_version = :scan_engine_version,
                scan_signature_version = 'magic-v1', scan_error = :error, scanned_at = now(), scan_locked_at = NULL, scan_worker_id = NULL, scan_lease_expires_at = NULL, updated_at = now()
            WHERE document_id = :document_id
        """), {"document_id": str(document_id), "scan_status": scan_status, "verified_checksum": verified_checksum, "error": (error or "Document quarantined")[:1000], "scan_engine": os.getenv("FPO_CLAMAV_HOST", "clamav"), "scan_engine_version": os.getenv("FPO_CLAMAV_VERSION", "configured")})
        return
    next_status = "DEAD" if scan_status not in {"CLEAN", "INFECTED", "QUARANTINED"} and int((conn.execute(text("SELECT scan_attempts FROM public.fpo_verification_documents WHERE document_id = :document_id"), {"document_id": str(document_id)}).scalar() or 0)) >= 5 else scan_status
    conn.execute(text("""
        UPDATE public.fpo_verification_documents
        SET scan_status = :scan_status, scan_error = :error, scan_error_code = :error_code, scanned_at = now(),
            scan_locked_at = NULL, scan_worker_id = NULL, scan_lease_expires_at = NULL,
            scan_next_attempt_at = CASE
                WHEN :scan_status = 'DEAD' THEN NULL
                ELSE now() + make_interval(secs => CASE scan_attempts WHEN 1 THEN 30 WHEN 2 THEN 120 WHEN 3 THEN 600 WHEN 4 THEN 1800 ELSE 1800 END)
            END,
            updated_at = now()
        WHERE document_id = :document_id
    """), {"document_id": str(document_id), "scan_status": next_status, "error": (error or "Scan failed")[:1000], "error_code": "SCAN_MAX_ATTEMPTS" if next_status == "DEAD" else "SCAN_TEMPORARY_FAILURE"})


def submit_verification(conn: Connection, user_id: UUID | str, *, expected_profile_version: int | None = None) -> dict[str, Any]:
    org = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.public_fpo_id, o.verification_status,
                   o.profile_fpo_id, p.onboarding_completed_at,
            p.fpo_name, p.legal_name, p.display_name, p.registration_number, p.registration_type,
            p.cin, p.gstin, p.operating_since_year,
                   p.state_name, p.district_name, p.district_code,
                   p.contact_person_name, p.contact_phone, p.contact_email,
                   p.main_commodities, p.services_provided, p.member_count,
                   p.profile_version
            FROM public.fpo_organizations o
            LEFT JOIN public.fpos p ON p.fpo_id = o.profile_fpo_id
            WHERE o.auth_user_id = :user_id
            FOR UPDATE OF o;
            """
        ),
        {"user_id": str(user_id)},
    ).mappings().first()
    if not org:
        raise ValueError("FPO organization has not been provisioned")
    if not org.get("profile_fpo_id") or not org.get("onboarding_completed_at"):
        raise ValueError("Complete the FPO profile before submitting verification")
    if expected_profile_version is not None and int(org.get("profile_version") or 0) != int(expected_profile_version):
        raise ValueError("FPO_PROFILE_VERSION_CONFLICT")
    if org["verification_status"] in {"SUBMITTED", "UNDER_REVIEW", "APPROVED"}:
        raise ValueError("This FPO verification is already submitted")
    required_documents = conn.execute(text("""
        SELECT document_type FROM public.fpo_required_document_policies
        WHERE is_required = TRUE AND status = 'PUBLISHED'
          AND effective_from <= now() AND (effective_until IS NULL OR effective_until > now())
          AND registration_type IN ('DEFAULT', COALESCE(:registration_type, 'DEFAULT'))
    """), {"registration_type": org.get("registration_type")}).scalars().all()
    # The submission creates the admin review case. Document validation is
    # performed by the administrator after submission, so it cannot be a
    # prerequisite here.
    document_state = conn.execute(text("""
        SELECT count(*) AS total,
               count(*) FILTER (WHERE upload_status = 'AVAILABLE' AND scan_status = 'CLEAN' AND verified_checksum IS NOT NULL) AS ready
        FROM public.fpo_verification_documents
        WHERE fpo_id = :fpo_id AND deleted_at IS NULL
    """), {"fpo_id": str(org["fpo_id"])}).mappings().one()
    if document_state["total"] == 0:
        raise ValueError("Upload at least one verification document before submitting")
    if document_state["total"] != document_state["ready"]:
        raise ValueError("All verification documents must be uploaded and scan-safe before submitting")
    missing_documents = conn.execute(text("""
        SELECT required.document_type
        FROM unnest(CAST(:required_documents AS text[])) AS required(document_type)
        WHERE NOT EXISTS (
            SELECT 1 FROM public.fpo_verification_documents d
            WHERE d.fpo_id = :fpo_id AND d.deleted_at IS NULL
              AND d.document_type = required.document_type
              AND d.upload_status = 'AVAILABLE'
              AND d.scan_status = 'CLEAN' AND d.verified_checksum IS NOT NULL
        )
    """), {"required_documents": required_documents or [], "fpo_id": str(org["fpo_id"])}).scalars().all()
    if missing_documents:
        raise ValueError(f"Required verification documents are missing: {', '.join(missing_documents)}")

    snapshot = {
        key: org.get(key)
        for key in (
            "fpo_name", "legal_name", "display_name", "registration_number", "registration_type",
            "cin", "gstin", "operating_since_year", "state_name",
            "district_name", "district_code", "contact_person_name", "contact_phone",
            "contact_email", "main_commodities", "services_provided", "member_count",
        )
    }
    previous = conn.execute(text("""
        SELECT submission_id, submission_version
        FROM public.fpo_verification_submissions
        WHERE fpo_id = :fpo_id
        ORDER BY created_at DESC
        LIMIT 1
    """), {"fpo_id": str(org["fpo_id"])}).mappings().first()
    submission = conn.execute(
        text(
            """
            INSERT INTO public.fpo_verification_submissions
                (fpo_id, profile_id, profile_version, submitted_by, status, profile_snapshot,
                 profile_snapshot_hash, required_document_policy_version, checklist_policy_version,
                 submitted_at, submission_number, submission_version, previous_submission_id)
            VALUES (:fpo_id, :profile_id, :profile_version, :submitted_by, 'SUBMITTED', CAST(:snapshot AS jsonb),
                    encode(digest(CAST(:snapshot AS jsonb)::text, 'sha256'), 'hex'), 'fpo-documents-v1',
                    'fpo-verification-v1', now(),
                    'FPOVER-' || to_char(now(), 'YYYY') || '-' || right(replace(gen_random_uuid()::text, '-', ''), 8),
                    :submission_version, :previous_submission_id)
            RETURNING submission_id, status, created_at, submission_number;
            """
        ),
        {"fpo_id": str(org["fpo_id"]), "profile_id": str(org["profile_fpo_id"]), "profile_version": org.get("profile_version"), "submitted_by": str(user_id), "snapshot": json.dumps(snapshot, default=str), "submission_version": int(previous["submission_version"] or 0) + 1 if previous else 1, "previous_submission_id": str(previous["submission_id"]) if previous else None},
    ).mappings().one()
    conn.execute(text("""
        INSERT INTO public.fpo_verification_submission_documents
            (submission_id, document_id, storage_version, checksum)
        SELECT :submission_id, document_id, storage_version, COALESCE(verified_checksum, checksum)
        FROM public.fpo_verification_documents
        WHERE fpo_id = :fpo_id AND deleted_at IS NULL
          AND upload_status = 'AVAILABLE'
              AND scan_status = 'CLEAN' AND verified_checksum IS NOT NULL
        ON CONFLICT (submission_id, document_id) DO NOTHING
    """), {"submission_id": str(submission["submission_id"]), "fpo_id": str(org["fpo_id"])})
    conn.execute(
        text(
            """
            UPDATE public.fpo_organizations
            SET verification_status = 'SUBMITTED', updated_at = now(), version = version + 1
            WHERE fpo_id = :fpo_id;
            """
        ),
        {"fpo_id": str(org["fpo_id"])},
    )
    case_id = conn.execute(
        text("""
            INSERT INTO public.fpo_verification_cases
                (fpo_id, submission_id, status, case_number, checklist_policy_version, case_version)
            VALUES (:fpo_id, :submission_id, 'OPEN',
                    'FPOCASE-' || to_char(now(), 'YYYY') || '-' || right(replace(gen_random_uuid()::text, '-', ''), 8),
                    'fpo-verification-v1', 1)
            RETURNING case_id
        """),
        {"fpo_id": str(org["fpo_id"]), "submission_id": str(submission["submission_id"])},
    ).scalar_one()
    for checklist_key in ("LEGAL_NAME_MATCH", "REGISTRATION_NUMBER_MATCH", "REGISTRATION_TYPE_MATCH", "REGISTRATION_CERTIFICATE_VALID", "PAN_MATCH", "AUTHORIZED_REPRESENTATIVE_CONFIRMED", "REGISTERED_ADDRESS_MATCH", "CONTACT_DETAILS_VERIFIED", "REQUIRED_DOCUMENTS_PRESENT", "DOCUMENTS_SCAN_SAFE", "DOCUMENTS_ADMIN_VALID", "PROFILE_SNAPSHOT_CURRENT", "DUPLICATE_ORGANIZATION_CHECK", "RISK_FLAGS_REVIEWED"):
        conn.execute(text("""
            INSERT INTO public.fpo_verification_checklist_results (case_id, checklist_key, policy_version)
            VALUES (:case_id, :checklist_key, 'fpo-verification-v1') ON CONFLICT (case_id, checklist_key) DO NOTHING
        """), {"case_id": str(case_id), "checklist_key": checklist_key})
    _case_event(conn, case_id=case_id, event_type="CASE_CREATED", actor_user_id=user_id, metadata={"submission_id": str(submission["submission_id"])})
    return {"fpo_id": org["fpo_id"], "public_fpo_id": org["public_fpo_id"], **dict(submission)}


def review_verification(
    conn: Connection,
    *,
    fpo_id: UUID | str,
    reviewer_user_id: UUID | str,
    status: str,
    note: str | None,
) -> dict[str, Any]:
    # The old organization-level endpoint is retained only for compatibility.
    # All FPO-03 decisions must use the case-scoped decision endpoint so that
    # assignment, checklist, snapshot and optimistic-lock rules cannot be bypassed.
    raise ValueError("FPO_DEDICATED_DECISION_REQUIRED")
    conn.execute(
        text(
            """
            UPDATE public.fpo_verification_submissions
            SET status = :status, reviewer_user_id = :reviewer_user_id,
                reviewer_note = :note, reviewed_at = now(), updated_at = now()
            WHERE submission_id = :submission_id;
            """
        ),
        {"status": status, "reviewer_user_id": str(reviewer_user_id), "note": note, "submission_id": str(submission["submission_id"])},
    )
    conn.execute(
        text(
            """
            UPDATE public.fpo_organizations
            SET verification_status = :status,
                lifecycle_status = CASE WHEN :status = 'APPROVED' THEN 'ACTIVE' ELSE lifecycle_status END,
                discoverable = CASE WHEN :status = 'APPROVED' THEN TRUE ELSE FALSE END,
                approved_at = CASE WHEN :status = 'APPROVED' THEN now() ELSE approved_at END,
                approved_by = CASE WHEN :status = 'APPROVED' THEN :reviewer_user_id ELSE approved_by END,
                updated_at = now(), version = version + 1
            WHERE fpo_id = :fpo_id;
            """
        ),
        {"status": status, "reviewer_user_id": str(reviewer_user_id), "fpo_id": str(fpo_id)},
    )
    conn.execute(text("""
        UPDATE public.fpo_verification_cases
        SET status = CASE WHEN :status = 'APPROVED' THEN 'APPROVED'
                          WHEN :status = 'CHANGES_REQUIRED' THEN 'CHANGES_REQUIRED'
                          WHEN :status = 'REJECTED' THEN 'REJECTED' ELSE 'CLAIMED' END,
            assigned_reviewer_id = :reviewer_user_id, updated_at = now()
        WHERE submission_id = :submission_id
    """), {"status": status, "reviewer_user_id": str(reviewer_user_id), "submission_id": str(submission["submission_id"])})
    if status == "APPROVED":
        conn.execute(
            text(
                """
                INSERT INTO public.fpo_class_assignments
                    (fpo_id, class_code, configuration_version, assigned_by)
                VALUES (:fpo_id, 'A', COALESCE((SELECT MAX(version) FROM public.fpo_plan_versions WHERE class_code='A' AND status='PUBLISHED'), 1), :assigned_by)
                ON CONFLICT DO NOTHING;
                """
            ),
            {"fpo_id": str(fpo_id), "assigned_by": str(reviewer_user_id)},
        )
    record_fpo_audit_event(
        conn,
        fpo_id=fpo_id,
        actor_user_id=reviewer_user_id,
        action="FPO_VERIFICATION_REVIEWED",
        target_type="verification_submission",
        target_id=submission["submission_id"],
        metadata={"status": status, "note": note},
    )
    return {"fpo_id": fpo_id, "verification_status": status, "reviewer_note": note}


def list_verification_queue(conn: Connection, *, status: str | None = None) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.public_fpo_id, o.profile_fpo_id,
                   o.verification_status, o.provisioning_status,
                   o.lifecycle_status, o.created_at,
                   p.fpo_name, p.legal_name, p.display_name, p.registration_number, p.registration_type,
                   p.state_name, p.district_name, p.district_code, p.contact_person_name,
                   p.contact_email, p.contact_phone, p.main_commodities,
                   p.services_provided, p.member_count, p.organisation_description,
                   p.website_url, p.cin, p.gstin, p.operating_since_year,
                   a.class_code,
                   s.submission_id, s.status AS submission_status,
                   s.submitted_by, s.created_at AS submitted_at,
                   s.reviewer_note, s.reviewed_at,
                   c.case_id, c.case_number, c.status AS case_status,
                   c.case_version, c.assigned_reviewer_id, c.priority, c.sla_due_at,
                   c.risk_flags
            FROM public.fpo_organizations o
            LEFT JOIN public.fpos p ON p.fpo_id = o.profile_fpo_id
            LEFT JOIN LATERAL (
                SELECT class_code
                FROM public.fpo_class_assignments
                WHERE fpo_id = o.fpo_id AND is_active = TRUE
                ORDER BY assigned_at DESC
                LIMIT 1
            ) a ON TRUE
            LEFT JOIN LATERAL (
                SELECT * FROM public.fpo_verification_submissions
                WHERE fpo_id = o.fpo_id
                ORDER BY created_at DESC LIMIT 1
            ) s ON TRUE
            LEFT JOIN public.fpo_verification_cases c ON c.submission_id = s.submission_id
            -- Only submitted organizations are verification cases. Profile
            -- onboarding is not actionable by the verification reviewer and
            -- must not expose Accept/Reject controls.
            WHERE s.submission_id IS NOT NULL
              AND (:status IS NULL OR o.verification_status = :status)
            ORDER BY COALESCE(s.created_at, o.created_at) DESC, o.fpo_id;
            """
        ),
        {"status": status.upper() if status else None},
    ).mappings().all()
    return [dict(row) for row in rows]


def _case_event(conn: Connection, *, case_id: UUID | str, event_type: str, actor_user_id: UUID | str | None, reason: str | None = None, metadata: dict[str, Any] | None = None) -> None:
    conn.execute(text("""
        INSERT INTO public.fpo_verification_case_events
            (case_id, event_type, actor_user_id, reason, metadata)
        VALUES (:case_id, :event_type, :actor_user_id, :reason, CAST(:metadata AS jsonb))
    """), {
        "case_id": str(case_id), "event_type": event_type,
        "actor_user_id": str(actor_user_id) if actor_user_id else None,
        "reason": reason, "metadata": json.dumps(metadata or {}, default=str),
    })


def claim_verification_case(conn: Connection, *, case_id: UUID | str, reviewer_user_id: UUID | str) -> dict[str, Any]:
    row = conn.execute(text("""
        UPDATE public.fpo_verification_cases
        SET status = 'UNDER_REVIEW', assigned_reviewer_id = :reviewer,
            assigned_at = now(), review_started_at = COALESCE(review_started_at, now()),
            case_version = case_version + 1, updated_at = now()
        WHERE case_id = :case_id AND status IN ('OPEN','CLAIMED')
          AND assigned_reviewer_id IS NULL
        RETURNING *
    """), {"case_id": str(case_id), "reviewer": str(reviewer_user_id)}).mappings().first()
    if not row:
        raise ValueError("FPO_VERIFICATION_CASE_ALREADY_ASSIGNED_OR_CLOSED")
    _case_event(conn, case_id=case_id, event_type="CASE_CLAIMED", actor_user_id=reviewer_user_id)
    return dict(row)


def assign_verification_case(conn: Connection, *, case_id: UUID | str, reviewer_user_id: UUID | str, assigned_by: UUID | str, reason: str) -> dict[str, Any]:
    if not reason or len(reason.strip()) < 3:
        raise ValueError("FPO_CASE_ASSIGNMENT_REASON_REQUIRED")
    row = conn.execute(text("""
        UPDATE public.fpo_verification_cases
        SET status = CASE WHEN status = 'OPEN' THEN 'CLAIMED' ELSE status END,
            assigned_reviewer_id = :reviewer, assigned_at = now(),
            case_version = case_version + 1, updated_at = now()
        WHERE case_id = :case_id AND status IN ('OPEN','CLAIMED','UNDER_REVIEW')
        RETURNING *
    """), {"case_id": str(case_id), "reviewer": str(reviewer_user_id)}).mappings().first()
    if not row:
        raise ValueError("FPO_VERIFICATION_CASE_NOT_ASSIGNABLE")
    _case_event(conn, case_id=case_id, event_type="CASE_ASSIGNED", actor_user_id=assigned_by, reason=reason, metadata={"reviewer_user_id": str(reviewer_user_id)})
    return dict(row)


def release_verification_case(conn: Connection, *, case_id: UUID | str, reviewer_user_id: UUID | str, reason: str) -> dict[str, Any]:
    if not reason or len(reason.strip()) < 3:
        raise ValueError("FPO_CASE_RELEASE_REASON_REQUIRED")
    row = conn.execute(text("""
        UPDATE public.fpo_verification_cases
        SET status = 'OPEN', assigned_reviewer_id = NULL, assigned_at = NULL,
            case_version = case_version + 1, updated_at = now()
        WHERE case_id = :case_id AND assigned_reviewer_id = :reviewer
          AND status IN ('CLAIMED','UNDER_REVIEW')
        RETURNING *
    """), {"case_id": str(case_id), "reviewer": str(reviewer_user_id)}).mappings().first()
    if not row:
        raise ValueError("FPO_VERIFICATION_CASE_RELEASE_NOT_ALLOWED")
    _case_event(conn, case_id=case_id, event_type="CASE_RELEASED", actor_user_id=reviewer_user_id, reason=reason)
    return dict(row)


def escalate_verification_case(conn: Connection, *, case_id: UUID | str, actor_user_id: UUID | str, reason: str) -> dict[str, Any]:
    if not reason or len(reason.strip()) < 3:
        raise ValueError("FPO_CASE_ESCALATION_REASON_REQUIRED")
    row = conn.execute(text("""
        UPDATE public.fpo_verification_cases
        SET priority = 'HIGH', escalated_at = now(),
            case_version = case_version + 1, updated_at = now()
        WHERE case_id = :case_id AND status NOT IN ('CLOSED','APPROVED','REJECTED')
        RETURNING *
    """), {"case_id": str(case_id)}).mappings().first()
    if not row:
        raise ValueError("FPO_VERIFICATION_CASE_NOT_ESCALATABLE")
    _case_event(conn, case_id=case_id, event_type="CASE_ESCALATED", actor_user_id=actor_user_id, reason=reason)
    return dict(row)


def decide_verification_case(conn: Connection, *, case_id: UUID | str, reviewer_user_id: UUID | str, decision: str, reason_code: str, note: str, expected_case_version: int, required_actions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if decision not in {"APPROVE", "CHANGES_REQUIRED", "REJECT"}:
        raise ValueError("FPO_VERIFICATION_DECISION_INVALID")
    if not reason_code or not note or len(note.strip()) < 3:
        raise ValueError("FPO_VERIFICATION_DECISION_REASON_REQUIRED")
    case = conn.execute(text("""
        SELECT c.*, s.status AS submission_status, s.profile_snapshot,
               s.profile_snapshot_hash,
               encode(digest(s.profile_snapshot::text, 'sha256'), 'hex') AS calculated_snapshot_hash,
               s.submission_id, s.fpo_id
        FROM public.fpo_verification_cases c
        JOIN public.fpo_verification_submissions s ON s.submission_id = c.submission_id
        WHERE c.case_id = :case_id
        FOR UPDATE OF c, s
    """), {"case_id": str(case_id)}).mappings().first()
    if not case:
        raise ValueError("FPO_VERIFICATION_CASE_NOT_FOUND")
    if case["assigned_reviewer_id"] != UUID(str(reviewer_user_id)):
        raise ValueError("FPO_VERIFICATION_CASE_REVIEWER_REQUIRED")
    if case["status"] != "UNDER_REVIEW":
        raise ValueError("FPO_VERIFICATION_CASE_NOT_UNDER_REVIEW")
    if int(case["case_version"]) != int(expected_case_version):
        raise ValueError("FPO_VERIFICATION_CASE_VERSION_CONFLICT")
    if case["profile_snapshot_hash"] != case["calculated_snapshot_hash"]:
        raise ValueError("FPO_VERIFICATION_SNAPSHOT_HASH_INVALID")
    live_profile = conn.execute(text("""
        SELECT fpo_name, legal_name, display_name, registration_number, registration_type,
               cin, gstin, operating_since_year, state_name, district_name, district_code,
               contact_person_name, contact_phone, contact_email, main_commodities,
               services_provided, member_count
        FROM public.fpos f
        JOIN public.fpo_organizations o ON o.profile_fpo_id = f.fpo_id
        WHERE o.fpo_id = :fpo_id
    """), {"fpo_id": str(case["fpo_id"])}).mappings().first()
    if not live_profile:
        raise ValueError("FPO_PROFILE_NOT_FOUND")
    identity_fields = (
        "fpo_name", "legal_name", "display_name", "registration_number", "registration_type",
        "cin", "gstin", "operating_since_year", "state_name", "district_name", "district_code",
        "contact_person_name", "contact_phone", "contact_email", "main_commodities",
        "services_provided", "member_count",
    )
    if any(case["profile_snapshot"].get(field) != live_profile.get(field) for field in identity_fields):
        raise ValueError("FPO_VERIFICATION_SNAPSHOT_STALE")
    if decision == "APPROVE":
        checks = conn.execute(text("""
            SELECT count(*) AS total, count(*) FILTER (WHERE result IN ('PASS','NOT_APPLICABLE')) AS complete,
                   count(*) FILTER (WHERE result = 'FAIL') AS failed
            FROM public.fpo_verification_checklist_results WHERE case_id = :case_id
        """), {"case_id": str(case_id)}).mappings().one()
        if int(checks["total"]) == 0 or int(checks["complete"]) != int(checks["total"]) or int(checks["failed"]) > 0:
            raise ValueError("FPO_VERIFICATION_CHECKLIST_INCOMPLETE")
        docs = conn.execute(text("""
            SELECT count(*) AS total,
                   count(*) FILTER (WHERE d.validation_status = 'VALID' AND d.scan_status = 'CLEAN' AND d.verified_checksum IS NOT NULL) AS valid
            FROM public.fpo_verification_submission_documents sd
            JOIN public.fpo_verification_documents d ON d.document_id = sd.document_id
            WHERE sd.submission_id = :submission_id AND d.deleted_at IS NULL
        """), {"submission_id": str(case["submission_id"])}).mappings().one()
        if int(docs["total"]) == 0 or int(docs["valid"]) != int(docs["total"]):
            raise ValueError("FPO_VERIFICATION_DOCUMENT_VALIDATION_INCOMPLETE")
    next_submission_status = {"APPROVE": "APPROVED", "CHANGES_REQUIRED": "CHANGES_REQUIRED", "REJECT": "REJECTED"}[decision]
    conn.execute(text("""
        UPDATE public.fpo_verification_submissions
        SET status = :status, decision_reason_code = :reason_code, decision_note = :note,
            decided_by = :reviewer, decided_at = now(), reviewer_user_id = :reviewer,
            reviewer_note = :note, reviewed_at = now(), updated_at = now()
        WHERE submission_id = :submission_id
    """), {"status": next_submission_status, "reason_code": reason_code, "note": note, "reviewer": str(reviewer_user_id), "submission_id": str(case["submission_id"])})
    conn.execute(text("""
        UPDATE public.fpo_verification_cases
        SET status = :case_status, closed_at = now(), case_version = case_version + 1, updated_at = now()
        WHERE case_id = :case_id AND case_version = :expected
    """), {"case_status": "CLOSED", "case_id": str(case_id), "expected": expected_case_version})
    org_status = {"APPROVE": "APPROVED", "CHANGES_REQUIRED": "CHANGES_REQUIRED", "REJECT": "REJECTED"}[decision]
    conn.execute(text("""
        UPDATE public.fpo_organizations
        SET verification_status = :status,
            verification_level = CASE WHEN :status = 'APPROVED' THEN 'STANDARD' ELSE verification_level END,
            approved_at = CASE WHEN :status = 'APPROVED' THEN now() ELSE approved_at END,
            approved_by = CASE WHEN :status = 'APPROVED' THEN :reviewer ELSE approved_by END,
            updated_at = now(), version = version + 1
        WHERE fpo_id = :fpo_id
    """), {"status": org_status, "reviewer": str(reviewer_user_id), "fpo_id": str(case["fpo_id"])})
    _case_event(conn, case_id=case_id, event_type=f"DECISION_{decision}", actor_user_id=reviewer_user_id, reason=note, metadata={"reason_code": reason_code, "required_actions": required_actions or []})
    record_fpo_audit_event(conn, fpo_id=case["fpo_id"], actor_user_id=reviewer_user_id, action=f"FPO_VERIFICATION_{decision}", target_type="verification_case", target_id=case_id, metadata={"reason_code": reason_code})
    return {"case_id": case_id, "submission_id": case["submission_id"], "decision": decision, "verification_status": org_status, "required_actions": required_actions or []}


def get_admin_overview(conn: Connection) -> dict[str, Any]:
    row = conn.execute(text("""
        SELECT
          (SELECT count(*) FROM public.fpo_organizations) AS total_organizations,
          (SELECT count(*) FROM public.fpo_organizations WHERE verification_status IN ('SUBMITTED','UNDER_REVIEW')) AS verification_queue_depth,
          (SELECT count(*) FROM public.fpo_organizations WHERE provisioning_status = 'FAILED') AS provisioning_failures,
          (SELECT count(*) FROM public.fpo_organizations WHERE lifecycle_status = 'ACTIVE') AS active_organizations,
          (SELECT count(*) FROM public.fpo_organizations WHERE verification_status = 'APPROVED') AS approved_organizations,
          (SELECT count(*) FROM public.fpo_operational_alerts WHERE status = 'OPEN' AND severity = 'CRITICAL') AS critical_alerts,
          now() AS generated_at
    """)).mappings().one()
    return dict(row)


def discover_fpos(conn: Connection, *, query: str | None = None, limit: int = 25) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.public_fpo_id, o.profile_fpo_id,
                   p.fpo_name, p.state_name, p.district_name,
                   p.registration_type, p.main_commodities
            FROM public.fpo_organizations o
            JOIN public.fpos p ON p.fpo_id = o.profile_fpo_id AND p.is_active = TRUE
            WHERE o.lifecycle_status = 'ACTIVE'
              AND o.verification_status = 'APPROVED'
              AND o.discoverable = TRUE
              AND (:query IS NULL OR lower(p.fpo_name) LIKE lower(:pattern)
                   OR lower(COALESCE(p.district_name, '')) LIKE lower(:pattern)
                   OR lower(o.public_fpo_id) LIKE lower(:pattern))
            ORDER BY p.fpo_name, o.fpo_id
            LIMIT :limit;
            """
        ),
        {"query": query, "pattern": f"%{query}%" if query else "%", "limit": max(1, min(limit, 100))},
    ).mappings().all()
    return [dict(row) for row in rows]


def normalize_consent_language(value: str | None) -> str:
    return (value or "en").split(",", 1)[0].split("-", 1)[0].strip().lower() or "en"


def get_current_fpo_consent_policy(conn: Connection, *, language_code: str = "en") -> dict[str, Any]:
    language = normalize_consent_language(language_code)
    row = conn.execute(text("""
        SELECT policy_code, version AS policy_version, language_code, content, content_hash,
               mandatory_scopes, optional_scopes, effective_from, effective_until
        FROM public.fpo_consent_policies
        WHERE policy_code='FPO_DATA_SHARING' AND status='PUBLISHED'
          AND (language_code=:language OR language_code='en')
          AND effective_from<=now() AND (effective_until IS NULL OR effective_until>now())
        ORDER BY CASE WHEN language_code=:language THEN 0 ELSE 1 END, effective_from DESC
        LIMIT 1
    """), {"language": language}).mappings().first()
    if not row:
        raise ValueError("No published FPO data-sharing consent policy is available")
    return dict(row)


def create_farmer_relationship_request(
    conn: Connection, *, farmer_user_id: UUID | str, fpo_id: UUID | str,
    farm_id: UUID | str,
    policy_code: str, policy_version: str, accepted: bool, selected_optional_scopes: list[str],
    language_code: str, correlation_id: str | None, ip_address: str | None,
) -> dict[str, Any]:
    if not accepted:
        raise ValueError("Consent must be accepted before requesting an FPO relationship")
    requested_language = normalize_consent_language(language_code)
    policy = conn.execute(text("""
        SELECT policy_code, version, language_code, content, content_hash, mandatory_scopes, optional_scopes
        FROM public.fpo_consent_policies
        WHERE policy_code = :policy_code AND version = :policy_version
          AND status = 'PUBLISHED'
          AND (language_code = :language_code OR (language_code = 'en' AND :language_code <> 'en'))
          AND effective_from <= now() AND (effective_until IS NULL OR effective_until > now())
        ORDER BY CASE WHEN language_code = :language_code THEN 0 ELSE 1 END
        LIMIT 1
    """), {"policy_code": policy_code.strip(), "policy_version": policy_version.strip(), "language_code": requested_language}).mappings().first()
    if not policy:
        raise ValueError("The selected consent policy is not published")
    optional = list(selected_optional_scopes or [])
    unknown = set(optional) - set(policy["optional_scopes"] or [])
    if unknown:
        raise ValueError("The consent request contains an unsupported scope")
    scopes = list(policy["mandatory_scopes"] or []) + optional
    purpose = "Consent-backed FPO portfolio access"
    target = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.profile_fpo_id, o.verification_status, o.lifecycle_status,
                   fp.farmer_id, f.farm_id, f.farmer_id AS farm_farmer_id
            FROM public.fpo_organizations o
            LEFT JOIN public.farmer_profiles fp ON fp.user_id = :farmer_user_id
            JOIN public.farms f ON f.farm_id = :farm_id
            WHERE o.fpo_id = :fpo_id
              AND f.farmer_id = fp.farmer_id
              AND f.is_active = TRUE
              AND o.verification_status = 'APPROVED'
              AND o.lifecycle_status = 'ACTIVE'
              AND o.discoverable = TRUE;
            """
        ),
        {"fpo_id": str(fpo_id), "farmer_user_id": str(farmer_user_id), "farm_id": str(farm_id)},
    ).mappings().first()
    if not target:
        raise ValueError("This FPO is not available for farmer association")
    conn.execute(text("SELECT farm_id FROM public.farms WHERE farm_id=:farm_id FOR UPDATE"), {"farm_id": str(farm_id)}).first()
    existing = conn.execute(
        text(
            """
            SELECT relationship_id, fpo_id, farmer_user_id, farm_id, status,
                   farmer_consented_at, created_at
            FROM public.fpo_farmer_relationships
            WHERE farm_id = :farm_id AND fpo_id = :fpo_id
              AND status = 'PENDING_FPO_ACCEPTANCE'
            LIMIT 1;
            """
        ),
        {"farm_id": str(farm_id), "fpo_id": str(fpo_id)},
    ).mappings().first()
    if existing:
        # A repeated click or a stale client should not create a second request
        # or surface a misleading conflict. Return the canonical pending row.
        return {**dict(existing), "already_requested": True}
    active = conn.execute(text("""
        SELECT relationship_id FROM public.fpo_farmer_relationships
        WHERE farm_id=:farm_id AND fpo_id=:fpo_id AND status='ACTIVE' LIMIT 1
    """), {"farm_id": str(farm_id), "fpo_id": str(fpo_id)}).scalar_one_or_none()
    if active:
        raise ValueError("This farm is already connected to this FPO")
    relationship = conn.execute(
        text(
            """
            INSERT INTO public.fpo_farmer_relationships
                (fpo_id, farmer_user_id, farmer_profile_id, farm_id, relationship_type, status, initiated_by, farmer_consented_at)
            VALUES (:fpo_id, :farmer_user_id, :farmer_profile_id, :farm_id, 'PRIMARY', 'PENDING_FPO_ACCEPTANCE', 'FARMER', now())
            RETURNING relationship_id, fpo_id, farmer_user_id, farm_id, status, farmer_consented_at, created_at;
            """
        ),
        {"fpo_id": str(fpo_id), "farmer_user_id": str(farmer_user_id), "farmer_profile_id": target["farmer_id"], "farm_id": str(farm_id)},
    ).mappings().one()
    conn.execute(
        text(
            """
            INSERT INTO public.fpo_farmer_relationship_events (relationship_id, event_type, actor_user_id)
            VALUES (:relationship_id, 'REQUESTED', :actor_user_id),
                   (:relationship_id, 'CONSENT_RECORDED', :actor_user_id);
            """
        ),
        {"relationship_id": str(relationship["relationship_id"]), "actor_user_id": str(farmer_user_id)},
    )
    conn.execute(
        text("""
            INSERT INTO public.fpo_farmer_relationship_consents
                (relationship_id, policy_code, policy_version, purpose, scopes,
                 language_code, capture_channel, consent_content_hash, captured_by,
                 evidence_metadata)
            VALUES (:relationship_id, :policy_code, :policy_version, :purpose, :scopes,
                    :language_code, 'WEB', :content_hash, :captured_by,
                    CAST(:evidence AS jsonb))
        """),
        {
            "relationship_id": str(relationship["relationship_id"]),
            "policy_code": policy["policy_code"], "policy_version": policy["version"],
            "purpose": purpose, "scopes": scopes,
            "language_code": policy["language_code"],
            "content_hash": policy["content_hash"], "captured_by": str(farmer_user_id),
            "evidence": json.dumps({"policy_content_hash": policy["content_hash"], "correlation_id": correlation_id, "ip_address": ip_address, "capture_channel": "WEB"}),
        },
    )
    return dict(relationship)


def list_farmer_relationships(conn: Connection, *, farmer_user_id: UUID | str, farm_id: UUID | str | None = None) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            SELECT r.relationship_id, r.fpo_id, r.farm_id, r.status, r.relationship_type,
                   r.farmer_consented_at, r.fpo_accepted_at, r.created_at,
                   o.public_fpo_id, p.fpo_name, p.state_name, p.district_name,
                   f.farm_name, f.area_acres, f.village_name, f.block_name,
                   f.district_name AS farm_district_name, f.state_name AS farm_state_name,
                   f.crop_name, f.crop_code, f.is_active AS farm_is_active,
                   c.policy_code, c.policy_version, c.scopes, c.language_code,
                   c.captured_at AS consent_captured_at, c.expires_at AS consent_expires_at
            FROM public.fpo_farmer_relationships r
            JOIN public.fpo_organizations o ON o.fpo_id = r.fpo_id
            LEFT JOIN public.fpos p ON p.fpo_id = o.profile_fpo_id
            LEFT JOIN public.farms f ON f.farm_id = r.farm_id
            LEFT JOIN LATERAL (
                SELECT policy_code, policy_version, scopes, language_code, captured_at, expires_at
                FROM public.fpo_farmer_relationship_consents
                WHERE relationship_id=r.relationship_id
                ORDER BY captured_at DESC LIMIT 1
            ) c ON TRUE
            WHERE r.farmer_user_id = :farmer_user_id
              AND (:farm_id IS NULL OR r.farm_id = :farm_id)
            ORDER BY r.created_at DESC;
            """
        ),
        {"farmer_user_id": str(farmer_user_id), "farm_id": str(farm_id) if farm_id else None},
    ).mappings().all()
    return [dict(row) for row in rows]


def list_fpo_relationships(conn: Connection, *, fpo_user_id: UUID | str) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            SELECT r.relationship_id, r.fpo_id, r.farm_id, r.farmer_user_id, r.status,
                   r.relationship_type, r.farmer_consented_at, r.created_at,
                   fp.farmer_id, fp.full_name, fp.state_name, fp.district_name,
                   fp.block_name,
                   CASE WHEN position('@' IN u.email) > 3 THEN left(u.email, 2) || '•••' || substring(u.email FROM position('@' IN u.email)) ELSE '•••' END AS email_masked,
                   CASE WHEN length(u.phone_number) > 4 THEN repeat('*', greatest(length(u.phone_number) - 4, 1)) || right(u.phone_number, 4) ELSE '****' END AS phone_masked,
                   f.farm_name, f.area_acres, f.village_name,
                   f.block_name AS farm_block_name, f.district_name AS farm_district_name,
                   f.state_name AS farm_state_name, f.crop_name, f.crop_code,
                   f.is_active AS farm_is_active, f.polygon_geojson,
                   f.survey_number,
                   c.policy_code, c.policy_version, c.scopes, c.language_code,
                   c.captured_at AS consent_captured_at, c.expires_at AS consent_expires_at,
                   c.revoked_at AS consent_revoked_at
            FROM public.fpo_farmer_relationships r
            JOIN public.fpo_organizations o ON o.fpo_id = r.fpo_id AND o.auth_user_id = :fpo_user_id
            LEFT JOIN public.farmer_profiles fp ON fp.farmer_id = r.farmer_profile_id
            JOIN public.users u ON u.user_id = r.farmer_user_id
            LEFT JOIN public.farms f ON f.farm_id = r.farm_id
            LEFT JOIN LATERAL (
                SELECT policy_code, policy_version, scopes, language_code, captured_at, expires_at, revoked_at
                FROM public.fpo_farmer_relationship_consents
                WHERE relationship_id = r.relationship_id
                ORDER BY captured_at DESC LIMIT 1
            ) c ON TRUE
            WHERE r.farm_id IS NOT NULL
            ORDER BY r.created_at DESC;
            """
        ),
        {"fpo_user_id": str(fpo_user_id)},
    ).mappings().all()
    return [dict(row) for row in rows]


def decide_farmer_relationship(conn: Connection, *, fpo_user_id: UUID | str, relationship_id: UUID | str, decision: str, note: str = "") -> dict[str, Any]:
    if decision not in {"ACTIVE", "REJECTED"}:
        raise ValueError("Relationship decision must be ACTIVE or REJECTED")
    row = conn.execute(
        text(
            """
            SELECT r.relationship_id, r.fpo_id, r.farm_id, r.farmer_user_id, r.farmer_profile_id, r.status,
                   o.profile_fpo_id
            FROM public.fpo_farmer_relationships r
            JOIN public.fpo_organizations o ON o.fpo_id = r.fpo_id AND o.auth_user_id = :fpo_user_id
            WHERE r.relationship_id = :relationship_id
            FOR UPDATE;
            """
        ),
        {"fpo_user_id": str(fpo_user_id), "relationship_id": str(relationship_id)},
    ).mappings().first()
    if not row or row["status"] != "PENDING_FPO_ACCEPTANCE":
        raise ValueError("Open relationship request was not found")
    if decision == "ACTIVE" and not row["farm_id"]:
        raise ValueError("Legacy farmer-level requests cannot be accepted; the farmer must request access for a specific farm")
    if decision == "ACTIVE" and row.get("farm_id"):
        conn.execute(text("SELECT farm_id FROM public.farms WHERE farm_id=:farm_id FOR UPDATE"), {"farm_id": str(row["farm_id"])}).first()
        valid_consent = conn.execute(text("""
            SELECT 1 FROM public.fpo_farmer_relationship_consents
            WHERE relationship_id=:relationship_id AND revoked_at IS NULL
              AND (expires_at IS NULL OR expires_at>now())
              AND 'PROFILE_READ'=ANY(scopes) AND 'FARM_READ'=ANY(scopes)
              AND 'LAND_INTELLIGENCE_READ'=ANY(scopes)
            ORDER BY captured_at DESC LIMIT 1
        """), {"relationship_id": str(relationship_id)}).scalar_one_or_none()
        active_farm = conn.execute(text("""
            SELECT 1 FROM public.farms
            WHERE farm_id=:farm_id AND farmer_id=:farmer_id AND is_active=TRUE
        """), {"farm_id": str(row["farm_id"]), "farmer_id": str(row["farmer_profile_id"])}).scalar_one_or_none()
        if not valid_consent:
            raise ValueError("The farmer's farm-sharing consent is no longer valid; ask them to submit a new request")
        if not active_farm:
            raise ValueError("This farm is no longer active or owned by the requesting farmer")
        already_active = conn.execute(text("""
            SELECT relationship_id FROM public.fpo_farmer_relationships
            WHERE farm_id=:farm_id AND fpo_id=:fpo_id AND status='ACTIVE' AND relationship_id<>:relationship_id
            LIMIT 1
        """), {"farm_id": str(row["farm_id"]), "fpo_id": str(row["fpo_id"]), "relationship_id": str(relationship_id)}).scalar_one_or_none()
        if already_active:
            raise ValueError("This farm is already connected to this FPO")
    conn.execute(
        text(
            """
            UPDATE public.fpo_farmer_relationships
            SET status = :decision,
                fpo_accepted_at = CASE WHEN :decision = 'ACTIVE' THEN now() ELSE NULL END,
                fpo_accepted_by = :fpo_user_id,
                updated_at = now()
            WHERE relationship_id = :relationship_id;
            """
        ),
        {"decision": decision, "fpo_user_id": str(fpo_user_id), "relationship_id": str(relationship_id)},
    )
    if decision == "REJECTED":
        conn.execute(text("""
            UPDATE public.fpo_farmer_relationship_consents
            SET revoked_at=now(), revoked_by=:actor, revocation_reason='FPO rejected farm connection request'
            WHERE relationship_id=:relationship_id AND revoked_at IS NULL
        """), {"actor": str(fpo_user_id), "relationship_id": str(relationship_id)})
    event = "ACCEPTED" if decision == "ACTIVE" else "REJECTED"
    conn.execute(
        text("INSERT INTO public.fpo_farmer_relationship_events (relationship_id, event_type, actor_user_id, metadata) VALUES (:relationship_id, :event_type, :actor_user_id, CAST(:metadata AS jsonb))"),
        {"relationship_id": str(relationship_id), "event_type": event, "actor_user_id": str(fpo_user_id), "metadata": json.dumps({"note": note.strip()})},
    )
    record_fpo_audit_event(
        conn,
        fpo_id=row["fpo_id"],
        actor_user_id=fpo_user_id,
        action="FPO_RELATIONSHIP_DECIDED",
        target_type="farmer_relationship",
        target_id=relationship_id,
        metadata={"decision": decision, "farmer_user_id": str(row["farmer_user_id"]), "note": note.strip()},
    )
    return {"relationship_id": relationship_id, "fpo_id": row["fpo_id"], "status": decision}


def revoke_farmer_relationship(conn: Connection, *, farmer_user_id: UUID | str, relationship_id: UUID | str, farm_id: UUID | str | None = None) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            SELECT relationship_id, fpo_id, farmer_profile_id FROM public.fpo_farmer_relationships
            WHERE relationship_id = :relationship_id AND farmer_user_id = :farmer_user_id
              AND (:farm_id IS NULL OR farm_id = :farm_id) AND status = 'ACTIVE'
            FOR UPDATE;
            """
        ),
        {"relationship_id": str(relationship_id), "farmer_user_id": str(farmer_user_id), "farm_id": str(farm_id) if farm_id else None},
    ).mappings().first()
    if not row:
        raise ValueError("Active relationship was not found")
    conn.execute(
        text("UPDATE public.fpo_farmer_relationships SET status = 'REVOKED', revoked_at = now(), revoked_by = :user_id, updated_at = now() WHERE relationship_id = :relationship_id"),
        {"user_id": str(farmer_user_id), "relationship_id": str(relationship_id)},
    )
    conn.execute(
        text("INSERT INTO public.fpo_farmer_relationship_events (relationship_id, event_type, actor_user_id) VALUES (:relationship_id, 'REVOKED', :actor_user_id)"),
        {"relationship_id": str(relationship_id), "actor_user_id": str(farmer_user_id)},
    )
    conn.execute(
        text("""
            UPDATE public.fpo_farmer_relationship_consents
            SET revoked_at = now(), revoked_by = :actor, revocation_reason = 'Farmer revoked relationship'
            WHERE relationship_id = :relationship_id AND revoked_at IS NULL
        """),
        {"relationship_id": str(relationship_id), "actor": str(farmer_user_id)},
    )
    record_fpo_audit_event(
        conn,
        fpo_id=row["fpo_id"],
        actor_user_id=farmer_user_id,
        action="FPO_RELATIONSHIP_REVOKED",
        target_type="farmer_relationship",
        target_id=relationship_id,
        metadata={},
    )
    return {"relationship_id": relationship_id, "fpo_id": row["fpo_id"], "status": "REVOKED"}


def cancel_farmer_relationship_request(conn: Connection, *, farmer_user_id: UUID | str, relationship_id: UUID | str) -> dict[str, Any]:
    row = conn.execute(text("""
        UPDATE public.fpo_farmer_relationships
        SET status = 'CANCELLED', revoked_at = now(), revoked_by = :actor,
            revocation_reason = 'Farmer cancelled pending request', updated_at = now()
        WHERE relationship_id = :relationship_id AND farmer_user_id = :actor
          AND status = 'PENDING_FPO_ACCEPTANCE'
        RETURNING relationship_id, fpo_id
    """), {"relationship_id": str(relationship_id), "actor": str(farmer_user_id)}).mappings().first()
    if not row:
        raise ValueError("Pending relationship request was not found")
    conn.execute(text("""
        INSERT INTO public.fpo_farmer_relationship_events (relationship_id, event_type, actor_user_id)
        VALUES (:relationship_id, 'REQUEST_CANCELLED', :actor)
    """), {"relationship_id": str(relationship_id), "actor": str(farmer_user_id)})
    conn.execute(text("""
        UPDATE public.fpo_farmer_relationship_consents
        SET revoked_at = now(), revoked_by = :actor, revocation_reason = 'Farmer cancelled pending request'
        WHERE relationship_id = :relationship_id AND revoked_at IS NULL
    """), {"relationship_id": str(relationship_id), "actor": str(farmer_user_id)})
    return {"relationship_id": relationship_id, "fpo_id": row["fpo_id"], "status": "CANCELLED"}


def terminate_farmer_relationship(conn: Connection, *, fpo_user_id: UUID | str, relationship_id: UUID | str, reason: str) -> dict[str, Any]:
    row = conn.execute(text("""
        SELECT r.relationship_id, r.fpo_id, r.farmer_profile_id
        FROM public.fpo_farmer_relationships r
        JOIN public.fpo_organizations o ON o.fpo_id = r.fpo_id AND o.auth_user_id = :actor
        WHERE r.relationship_id = :relationship_id AND r.status = 'ACTIVE'
        FOR UPDATE
    """), {"relationship_id": str(relationship_id), "actor": str(fpo_user_id)}).mappings().first()
    if not row:
        raise ValueError("Active relationship was not found")
    conn.execute(text("""
        UPDATE public.fpo_farmer_relationships
        SET status = 'REVOKED', revoked_at = now(), revoked_by = :actor,
            revocation_reason = :reason, updated_at = now()
        WHERE relationship_id = :relationship_id
    """), {"relationship_id": str(relationship_id), "actor": str(fpo_user_id), "reason": reason.strip()})
    conn.execute(text("""
        INSERT INTO public.fpo_farmer_relationship_events (relationship_id, event_type, actor_user_id, metadata)
        VALUES (:relationship_id, 'TERMINATED_BY_FPO', :actor, CAST(:metadata AS jsonb))
    """), {"relationship_id": str(relationship_id), "actor": str(fpo_user_id), "metadata": json.dumps({"reason": reason.strip()})})
    conn.execute(text("""
        UPDATE public.fpo_farmer_relationship_consents
        SET revoked_at = now(), revoked_by = :actor, revocation_reason = :reason
        WHERE relationship_id = :relationship_id AND revoked_at IS NULL
    """), {"relationship_id": str(relationship_id), "actor": str(fpo_user_id), "reason": reason.strip()})
    return {"relationship_id": relationship_id, "fpo_id": row["fpo_id"], "status": "TERMINATED"}


def resolve_fpo_entitlements(conn: Connection, *, user_id: UUID | str) -> dict[str, Any]:
    org = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.public_fpo_id, o.verification_status,
                   a.class_code,
                   CASE
                       WHEN pv.plan_version_id IS NOT NULL THEN a.configuration_version
                       ELSE COALESCE(latest.version, a.configuration_version)
                   END AS configuration_version
            FROM public.fpo_organizations o
            LEFT JOIN public.fpo_class_assignments a
              ON a.fpo_id = o.fpo_id AND a.is_active = TRUE
             AND (a.expires_at IS NULL OR a.expires_at > now())
            LEFT JOIN public.fpo_plan_versions pv
              ON pv.class_code = a.class_code
             AND pv.version = a.configuration_version
             AND pv.status = 'PUBLISHED'
            LEFT JOIN LATERAL (
                SELECT MAX(version) AS version
                FROM public.fpo_plan_versions
                WHERE class_code = a.class_code AND status = 'PUBLISHED'
            ) latest ON TRUE
            WHERE o.auth_user_id = :user_id
            LIMIT 1;
            """
        ),
        {"user_id": str(user_id)},
    ).mappings().first()
    if not org:
        return {"fpo_id": None, "class_code": None, "features": {}, "status": "PENDING_PROVISIONING"}
    class_code = org.get("class_code")
    version = org.get("configuration_version")
    if not class_code or not version:
        return {
            "fpo_id": org["fpo_id"], "public_fpo_id": org["public_fpo_id"],
            "class_code": None, "configuration_version": None,
            "verification_status": org["verification_status"], "features": {},
            "error_code": "FPO_PLAN_NOT_ASSIGNED",
        }
    rows = conn.execute(
        text(
            """
            SELECT c.feature_key, c.display_name, c.description, c.category,
                   c.configuration_schema, c.dependencies, c.risk_level,
                   c.navigation_key, c.sort_order,
                   COALESCE(v.enabled, FALSE) AS class_enabled,
                   v.configuration,
                   ov.enabled AS override_enabled
            FROM public.fpo_feature_catalogue c
            LEFT JOIN public.fpo_class_feature_versions v
              ON v.feature_key = c.feature_key
             AND v.class_code = :class_code
             AND v.version = :version
             AND v.published_at IS NOT NULL
            LEFT JOIN LATERAL (
                SELECT enabled
                FROM public.fpo_feature_overrides
                WHERE fpo_id = :fpo_id
                  AND feature_key = c.feature_key
                  AND starts_at <= now()
                  AND (expires_at IS NULL OR expires_at > now())
                ORDER BY created_at DESC
                LIMIT 1
            ) ov ON TRUE
            WHERE c.is_active = TRUE
            ORDER BY c.category, c.feature_key;
            """
        ),
        {"fpo_id": str(org["fpo_id"]), "class_code": class_code, "version": version},
    ).mappings().all()
    features = {
        row["feature_key"]: {
            "enabled": row["override_enabled"] if row["override_enabled"] is not None else row["class_enabled"],
            "display_name": row["display_name"],
            "description": row["description"],
            "category": row["category"],
            "source": "override" if row["override_enabled"] is not None else "class",
            "configuration": row["configuration"] or {},
            "configuration_schema": row["configuration_schema"] or {},
            "dependencies": row["dependencies"] or [],
            "risk_level": row["risk_level"],
            "navigation_key": row["navigation_key"],
            "sort_order": row["sort_order"],
            "plan_version": version,
        }
        for row in rows
    }
    for feature in features.values():
        configuration = feature["configuration"]
        if isinstance(configuration, dict) and (
            configuration.get("enabled") is False or configuration.get("emergency_disable") is True
        ):
            feature["enabled"] = False
        feature["dependencies_satisfied"] = all(features.get(dep, {}).get("enabled", False) for dep in feature["dependencies"])
        if feature["source"] == "class":
            feature["source"] = f"CLASS_{class_code}_VERSION_{version}"
        if feature["enabled"] and not feature["dependencies_satisfied"]:
            feature["enabled"] = False
    return {
        "fpo_id": org["fpo_id"],
        "public_fpo_id": org["public_fpo_id"],
        "class_code": class_code,
        "configuration_version": version,
        "verification_status": org["verification_status"],
        "features": features,
    }


def get_fpo_access_context(conn: Connection, *, user_id: UUID | str) -> dict[str, Any]:
    row = conn.execute(text("""
        SELECT o.fpo_id, o.profile_fpo_id, o.public_fpo_id, o.provisioning_status, o.verification_status,
               o.lifecycle_status, o.commercial_status, a.class_code, a.configuration_version
        FROM public.fpo_organizations o
        LEFT JOIN public.fpo_class_assignments a
          ON a.fpo_id = o.fpo_id AND a.is_active = TRUE
         AND (a.expires_at IS NULL OR a.expires_at > now())
        WHERE o.auth_user_id = :user_id
        LIMIT 1
    """), {"user_id": str(user_id)}).mappings().first()
    if not row:
        raise ValueError("FPO_PROVISIONING_PENDING")
    context = dict(row)
    if context["provisioning_status"] != "READY":
        raise ValueError("FPO_PROVISIONING_PENDING")
    if context["verification_status"] == "PROFILE_INCOMPLETE":
        raise ValueError("FPO_PROFILE_INCOMPLETE")
    if context["verification_status"] in {"SUBMITTED", "UNDER_REVIEW"}:
        raise ValueError("FPO_VERIFICATION_PENDING")
    if context["verification_status"] == "CHANGES_REQUIRED":
        raise ValueError("FPO_CHANGES_REQUIRED")
    if context["verification_status"] == "REJECTED":
        raise ValueError("FPO_REJECTED")
    if context["lifecycle_status"] == "SUSPENDED" or context["verification_status"] == "SUSPENDED":
        raise ValueError("FPO_SUSPENDED")
    if context["verification_status"] != "APPROVED" or context["lifecycle_status"] != "ACTIVE":
        raise ValueError("FPO_VERIFICATION_PENDING")
    if not context.get("class_code") or not context.get("configuration_version"):
        raise ValueError("FPO_PLAN_NOT_ASSIGNED")
    return context


def list_feature_catalogue(conn: Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            SELECT c.feature_key, c.display_name, c.description, c.category, c.is_active,
                   c.configuration_schema, c.dependencies, c.risk_level, c.navigation_key, c.sort_order,
                   v.class_code, v.version, v.enabled, v.configuration, v.published_at
            FROM public.fpo_feature_catalogue c
            LEFT JOIN public.fpo_class_feature_versions v ON v.feature_key = c.feature_key
            ORDER BY c.category, c.feature_key, v.class_code, v.version;
            """
        )
    ).mappings().all()
    return [dict(row) for row in rows]


def assign_fpo_class(conn: Connection, *, fpo_id: UUID | str, class_code: str, admin_user_id: UUID | str) -> dict[str, Any]:
    class_code = class_code.upper()
    if class_code not in {"A", "B", "C"}:
        raise ValueError("Class must be A, B, or C")
    exists = conn.execute(
        text("SELECT fpo_id FROM public.fpo_organizations WHERE fpo_id = :fpo_id"),
        {"fpo_id": str(fpo_id)},
    ).scalar_one_or_none()
    if not exists:
        raise ValueError("FPO organization was not found")
    conn.execute(
        text("UPDATE public.fpo_class_assignments SET is_active = FALSE WHERE fpo_id = :fpo_id AND is_active = TRUE"),
        {"fpo_id": str(fpo_id)},
    )
    row = conn.execute(
        text(
            """
            INSERT INTO public.fpo_class_assignments
                (fpo_id, class_code, configuration_version, assigned_by)
            VALUES (:fpo_id, :class_code,
                    COALESCE((SELECT MAX(version) FROM public.fpo_plan_versions
                              WHERE class_code = :class_code AND status = 'PUBLISHED'), 1),
                    :assigned_by)
            RETURNING assignment_id, fpo_id, class_code, configuration_version, assigned_at;
            """
        ),
        {"fpo_id": str(fpo_id), "class_code": class_code, "assigned_by": str(admin_user_id)},
    ).mappings().one()
    record_fpo_audit_event(
        conn,
        fpo_id=fpo_id,
        actor_user_id=admin_user_id,
        action="FPO_CLASS_ASSIGNED",
        target_type="fpo_class_assignment",
        target_id=row["assignment_id"],
        metadata={"class_code": class_code, "configuration_version": row["configuration_version"]},
    )
    return dict(row)


def record_fpo_audit_event(
    conn: Connection,
    *,
    action: str,
    fpo_id: UUID | str | None = None,
    actor_user_id: UUID | str | None = None,
    target_type: str | None = None,
    target_id: UUID | str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        text(
            """
            INSERT INTO public.fpo_audit_events
                (fpo_id, actor_user_id, action, target_type, target_id, metadata)
            VALUES (:fpo_id, :actor_user_id, :action, :target_type, :target_id, CAST(:metadata AS jsonb));
            """
        ),
        {
            "fpo_id": str(fpo_id) if fpo_id else None,
            "actor_user_id": str(actor_user_id) if actor_user_id else None,
            "action": action,
            "target_type": target_type,
            "target_id": str(target_id) if target_id else None,
            "metadata": json.dumps(metadata or {}, default=str),
        },
    )


def require_fpo_feature(conn: Connection, *, user_id: UUID | str, feature_key: str) -> dict[str, Any]:
    get_fpo_access_context(conn, user_id=user_id)
    entitlements = resolve_fpo_entitlements(conn, user_id=user_id)
    feature = entitlements.get("features", {}).get(feature_key)
    if not entitlements.get("fpo_id"):
        raise ValueError("FPO organization is not provisioned")
    if not feature or not feature.get("enabled"):
        raise ValueError(f"Feature {feature_key} is not enabled for this FPO")
    return entitlements


def create_feature_override(
    conn: Connection,
    *,
    fpo_id: UUID | str,
    feature_key: str,
    enabled: bool,
    reason: str,
    expires_at: Any | None,
    admin_user_id: UUID | str,
) -> dict[str, Any]:
    if not reason or len(reason.strip()) < 3:
        raise ValueError("A meaningful reason is required for a feature override")
    if not conn.execute(text("SELECT 1 FROM public.fpo_organizations WHERE fpo_id = :fpo_id"), {"fpo_id": str(fpo_id)}).scalar_one_or_none():
        raise ValueError("FPO organization was not found")
    if not conn.execute(text("SELECT 1 FROM public.fpo_feature_catalogue WHERE feature_key = :feature_key AND is_active = TRUE"), {"feature_key": feature_key}).scalar_one_or_none():
        raise ValueError("Feature was not found or is inactive")
    row = conn.execute(
        text(
            """
            INSERT INTO public.fpo_feature_overrides
                (fpo_id, feature_key, enabled, reason, expires_at, created_by)
            VALUES (:fpo_id, :feature_key, :enabled, :reason, :expires_at, :created_by)
            RETURNING override_id, fpo_id, feature_key, enabled, reason, starts_at, expires_at, created_at;
            """
        ),
        {"fpo_id": str(fpo_id), "feature_key": feature_key, "enabled": enabled, "reason": reason.strip(), "expires_at": expires_at, "created_by": str(admin_user_id)},
    ).mappings().one()
    record_fpo_audit_event(conn, fpo_id=fpo_id, actor_user_id=admin_user_id, action="FPO_FEATURE_OVERRIDE_CREATED", target_type="feature_override", target_id=row["override_id"], metadata={"feature_key": feature_key, "enabled": enabled, "reason": reason.strip()})
    return dict(row)


def list_feature_overrides(conn: Connection, *, fpo_id: UUID | str) -> list[dict[str, Any]]:
    rows = conn.execute(text("SELECT override_id, fpo_id, feature_key, enabled, reason, starts_at, expires_at, created_by, created_at FROM public.fpo_feature_overrides WHERE fpo_id = :fpo_id ORDER BY created_at DESC"), {"fpo_id": str(fpo_id)}).mappings().all()
    return [dict(row) for row in rows]


def reconcile_fpo_data(conn: Connection, *, admin_user_id: UUID | str) -> dict[str, Any]:
    run = conn.execute(text("INSERT INTO public.fpo_reconciliation_runs (started_by) VALUES (:user_id) RETURNING run_id"), {"user_id": str(admin_user_id)}).scalar_one()
    try:
        repaired = conn.execute(text("""
            UPDATE public.farmer_profiles fp
            SET fpo_id = o.profile_fpo_id, updated_at = now()
            FROM public.fpo_farmer_relationships r
            JOIN public.fpo_organizations o ON o.fpo_id = r.fpo_id
            WHERE r.status = 'ACTIVE' AND r.farmer_profile_id = fp.farmer_id
              AND o.profile_fpo_id IS NOT NULL AND fp.fpo_id IS DISTINCT FROM o.profile_fpo_id
            RETURNING fp.farmer_id
        """)).all()
        cleared = conn.execute(text("""
            UPDATE public.farmer_profiles fp SET fpo_id = NULL, updated_at = now()
            WHERE fp.fpo_id IS NOT NULL
              AND EXISTS (SELECT 1 FROM public.fpo_organizations o WHERE o.profile_fpo_id = fp.fpo_id)
              AND NOT EXISTS (SELECT 1 FROM public.fpo_farmer_relationships r WHERE r.farmer_profile_id = fp.farmer_id AND r.status = 'ACTIVE')
            RETURNING fp.farmer_id
        """)).all()
        orphan_orgs = conn.execute(text("SELECT count(*) FROM public.fpo_organizations WHERE provisioning_status = 'READY' AND profile_fpo_id IS NULL")).scalar_one()
        read_models = refresh_portfolio_read_models(conn)
        result = {"run_id": run, "repaired_farmer_projections": len(repaired), "cleared_stale_projections": len(cleared), "orphaned_organizations": int(orphan_orgs), **read_models, "status": "COMPLETED"}
        conn.execute(text("UPDATE public.fpo_reconciliation_runs SET status = 'COMPLETED', completed_at = now(), repaired_farmer_projections = :repaired, cleared_stale_projections = :cleared, orphaned_organizations = :orphans WHERE run_id = :run_id"), {"run_id": str(run), "repaired": len(repaired), "cleared": len(cleared), "orphans": int(orphan_orgs)})
        record_fpo_audit_event(conn, actor_user_id=admin_user_id, action="FPO_RECONCILIATION_COMPLETED", target_type="reconciliation_run", target_id=run, metadata=result)
        return result
    except Exception as exc:
        conn.execute(text("UPDATE public.fpo_reconciliation_runs SET status = 'FAILED', completed_at = now(), error_message = :error WHERE run_id = :run_id"), {"run_id": str(run), "error": str(exc)[:2000]})
        raise


def fpo_portfolio_report(conn: Connection, *, user_id: UUID | str) -> dict[str, Any]:
    entitlements = require_fpo_feature(conn, user_id=user_id, feature_key="BASIC_REPORTS")
    row = conn.execute(
        text(
            """
            SELECT
                COUNT(*) FILTER (WHERE r.status = 'ACTIVE' AND c.consent_id IS NOT NULL
                    AND 'PROFILE_READ'=ANY(c.scopes) AND 'FARM_READ'=ANY(c.scopes)) AS active_relationships,
                COUNT(*) FILTER (WHERE r.status = 'PENDING_FPO_ACCEPTANCE' AND c.consent_id IS NOT NULL
                    AND 'PROFILE_READ'=ANY(c.scopes) AND 'FARM_READ'=ANY(c.scopes)) AS pending_relationships,
                COUNT(*) FILTER (WHERE r.status = 'REJECTED') AS rejected_relationships,
                COUNT(DISTINCT r.farmer_user_id) FILTER (WHERE r.status = 'ACTIVE' AND c.consent_id IS NOT NULL
                    AND 'PROFILE_READ'=ANY(c.scopes) AND 'FARM_READ'=ANY(c.scopes)) AS active_farmers,
                COUNT(DISTINCT r.farmer_profile_id) FILTER (WHERE r.status = 'ACTIVE' AND c.consent_id IS NOT NULL
                    AND 'PROFILE_READ'=ANY(c.scopes) AND 'FARM_READ'=ANY(c.scopes)) AS linked_profiles
            FROM public.fpo_farmer_relationships r
            LEFT JOIN LATERAL (
                SELECT consent_id, scopes FROM public.fpo_farmer_relationship_consents
                WHERE relationship_id=r.relationship_id AND revoked_at IS NULL
                  AND (expires_at IS NULL OR expires_at>now())
                ORDER BY captured_at DESC LIMIT 1
            ) c ON TRUE
            WHERE r.fpo_id = :fpo_id AND r.farm_id IS NOT NULL;
            """
        ),
        {"fpo_id": str(entitlements["fpo_id"])},
    ).mappings().one()
    alerts = conn.execute(
        text("SELECT COUNT(*) FILTER (WHERE status = 'OPEN') AS open_alerts, COUNT(*) FILTER (WHERE severity = 'CRITICAL' AND status <> 'RESOLVED') AS critical_alerts FROM public.fpo_operational_alerts WHERE fpo_id = :fpo_id"),
        {"fpo_id": str(entitlements["fpo_id"])},
    ).mappings().one()
    return {
        "fpo_id": entitlements["fpo_id"],
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        "class_code": entitlements.get("class_code"),
        "relationships": {key: row[key] for key in row.keys()},
        "alerts": {key: alerts[key] for key in alerts.keys()},
    }


def list_fpo_alerts(conn: Connection, *, user_id: UUID | str, status: str | None = None) -> list[dict[str, Any]]:
    entitlements = require_fpo_feature(conn, user_id=user_id, feature_key="BASIC_ALERTS")
    rows = conn.execute(
        text(
            """
            SELECT alert_id, fpo_id, alert_type, severity, title, message, source,
                   status, metadata, acknowledged_by, acknowledged_at, created_at, updated_at
            FROM public.fpo_operational_alerts
            WHERE fpo_id = :fpo_id AND (:status IS NULL OR status = :status)
            ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'WARNING' THEN 2 ELSE 3 END, created_at DESC;
            """
        ),
        {"fpo_id": str(entitlements["fpo_id"]), "status": status.upper() if status else None},
    ).mappings().all()
    return [dict(row) for row in rows]


def acknowledge_fpo_alert(conn: Connection, *, user_id: UUID | str, alert_id: UUID | str) -> dict[str, Any]:
    entitlements = require_fpo_feature(conn, user_id=user_id, feature_key="BASIC_ALERTS")
    row = conn.execute(
        text(
            """
            UPDATE public.fpo_operational_alerts
            SET status = 'ACKNOWLEDGED', acknowledged_by = :user_id,
                acknowledged_at = now(), updated_at = now()
            WHERE alert_id = :alert_id AND fpo_id = :fpo_id AND status = 'OPEN'
            RETURNING alert_id, fpo_id, status, acknowledged_by, acknowledged_at;
            """
        ),
        {"alert_id": str(alert_id), "fpo_id": str(entitlements["fpo_id"]), "user_id": str(user_id)},
    ).mappings().first()
    if not row:
        raise ValueError("Open alert was not found for this FPO")
    record_fpo_audit_event(conn, fpo_id=entitlements["fpo_id"], actor_user_id=user_id, action="FPO_ALERT_ACKNOWLEDGED", target_type="operational_alert", target_id=alert_id, metadata={})
    return dict(row)


def refresh_portfolio_read_models(conn: Connection, *, fpo_id: UUID | str | None = None) -> dict[str, int]:
    params = {"fpo_id": str(fpo_id) if fpo_id else None}
    orgs = conn.execute(text("SELECT fpo_id, profile_fpo_id FROM public.fpo_organizations WHERE (:fpo_id IS NULL OR fpo_id = :fpo_id)"), params).mappings().all()
    refreshed = 0
    for org in orgs:
        oid = str(org["fpo_id"])
        profile_fpo_id = org["profile_fpo_id"]
        conn.execute(text("DELETE FROM public.fpo_farmer_portfolio WHERE fpo_id = :fpo_id"), {"fpo_id": oid})
        conn.execute(text("""
            INSERT INTO public.fpo_farmer_portfolio
                (fpo_id, farmer_id, farmer_name, phone_masked, district_code, district_name,
                 block_code, block_name, village_name, farm_count, area_acres, active_crop_codes,
                 highest_alert_severity, open_alert_count, relationship_status)
            WITH valid_relationships AS (
                SELECT DISTINCT r.fpo_id, r.relationship_id, r.farmer_profile_id AS farmer_id,
                       r.status, r.farm_id
                FROM public.fpo_farmer_relationships r
                JOIN public.fpo_farmer_relationship_consents c
                  ON c.relationship_id=r.relationship_id AND c.revoked_at IS NULL
                 AND (c.expires_at IS NULL OR c.expires_at>now())
                 AND 'PROFILE_READ'=ANY(c.scopes) AND 'FARM_READ'=ANY(c.scopes)
                WHERE r.fpo_id=:fpo_id AND r.farm_id IS NOT NULL AND r.status='ACTIVE'
            ), farm_metrics AS (
                SELECT f.farmer_id, COUNT(DISTINCT f.farm_id)::integer AS farm_count,
                       COALESCE(SUM(f.area_acres), 0) AS area_acres,
                       COALESCE(array_agg(DISTINCT f.crop_code) FILTER (WHERE f.crop_code IS NOT NULL), '{}') AS crop_codes,
                       COUNT(DISTINCT f.district_code)::integer AS district_count
                FROM public.farms f
                WHERE f.is_active=TRUE AND EXISTS (SELECT 1 FROM valid_relationships vr WHERE vr.status='ACTIVE' AND vr.farm_id=f.farm_id)
                GROUP BY f.farmer_id
            ), alert_metrics AS (
                SELECT f.farmer_id, COUNT(DISTINCT fa.alert_id)::integer AS open_alert_count,
                       CASE MAX(CASE fa.severity WHEN 'CRITICAL' THEN 3 WHEN 'WARNING' THEN 2 WHEN 'INFO' THEN 1 ELSE 0 END)
                         WHEN 3 THEN 'CRITICAL' WHEN 2 THEN 'WARNING' WHEN 1 THEN 'INFO' ELSE NULL END AS highest_alert_severity
                FROM public.farms f
                JOIN public.farm_alerts fa ON fa.farm_id = f.farm_id AND fa.acknowledged_at IS NULL
                WHERE f.is_active=TRUE AND EXISTS (SELECT 1 FROM valid_relationships vr WHERE vr.status='ACTIVE' AND vr.farm_id=f.farm_id)
                GROUP BY f.farmer_id
            )
            SELECT :fpo_id, fp.farmer_id, COALESCE(fp.full_name, 'Unnamed farmer'),
                   CASE WHEN length(u.phone_number) > 4 THEN repeat('*', length(u.phone_number) - 4) || right(u.phone_number, 4) ELSE u.phone_number END,
                   fp.district_code, fp.district_name, fp.block_code, fp.block_name, fp.village_name,
                   COALESCE(fm.farm_count, 0), COALESCE(fm.area_acres, 0), COALESCE(fm.crop_codes, '{}'),
                   am.highest_alert_severity, COALESCE(am.open_alert_count, 0),
                   'ACTIVE'
            FROM valid_relationships r
            JOIN public.farmer_profiles fp ON fp.farmer_id = r.farmer_id
            LEFT JOIN public.users u ON u.user_id = fp.user_id
            LEFT JOIN farm_metrics fm ON fm.farmer_id = fp.farmer_id
            LEFT JOIN alert_metrics am ON am.farmer_id = fp.farmer_id
            GROUP BY fp.farmer_id, fp.full_name, u.phone_number, fp.district_code, fp.district_name,
                     fp.block_code, fp.block_name, fp.village_name, fm.farm_count,
                     fm.area_acres, fm.crop_codes, am.highest_alert_severity, am.open_alert_count
        """), {"fpo_id": oid, "profile_fpo_id": str(profile_fpo_id) if profile_fpo_id else None})
        conn.execute(text("""
            INSERT INTO public.fpo_portfolio_summary
                (fpo_id, active_farmer_count, pending_farmer_count, active_farm_count,
                 registered_area_acres, active_crop_count, district_count, block_count,
                 village_count, open_alert_count, attention_farm_count, critical_farm_count,
                 data_through, updated_at)
            SELECT :fpo_id,
                COUNT(*) FILTER (WHERE relationship_status = 'ACTIVE')::integer,
                (SELECT COUNT(DISTINCT r.farmer_profile_id)::integer
                 FROM public.fpo_farmer_relationships r
                 JOIN public.fpo_farmer_relationship_consents c ON c.relationship_id=r.relationship_id
                   AND c.revoked_at IS NULL AND (c.expires_at IS NULL OR c.expires_at>now())
                   AND 'PROFILE_READ'=ANY(c.scopes) AND 'FARM_READ'=ANY(c.scopes)
                 WHERE r.fpo_id=:fpo_id AND r.farm_id IS NOT NULL AND r.status='PENDING_FPO_ACCEPTANCE'),
                COALESCE(SUM(farm_count) FILTER (WHERE relationship_status = 'ACTIVE'), 0)::integer,
                COALESCE(SUM(area_acres) FILTER (WHERE relationship_status = 'ACTIVE'), 0),
                COALESCE((SELECT COUNT(DISTINCT f.crop_code) FROM public.farms f JOIN public.fpo_farmer_relationships fr ON fr.farm_id=f.farm_id AND fr.fpo_id=:fpo_id AND fr.status='ACTIVE' JOIN public.fpo_farmer_relationship_consents c ON c.relationship_id=fr.relationship_id AND c.revoked_at IS NULL AND (c.expires_at IS NULL OR c.expires_at>now()) AND 'FARM_READ'=ANY(c.scopes) WHERE f.is_active=TRUE AND f.crop_code IS NOT NULL), 0)::integer,
                COUNT(DISTINCT district_code) FILTER (WHERE relationship_status = 'ACTIVE')::integer,
                COUNT(DISTINCT block_code) FILTER (WHERE relationship_status = 'ACTIVE')::integer,
                COUNT(DISTINCT village_name) FILTER (WHERE relationship_status = 'ACTIVE')::integer,
                COALESCE(SUM(open_alert_count) FILTER (WHERE relationship_status = 'ACTIVE'), 0)::integer,
                COUNT(*) FILTER (WHERE relationship_status = 'ACTIVE' AND open_alert_count > 0)::integer,
                COUNT(*) FILTER (WHERE relationship_status = 'ACTIVE' AND highest_alert_severity = 'CRITICAL')::integer,
                now(), now()
            FROM public.fpo_farmer_portfolio WHERE fpo_id = :fpo_id
            ON CONFLICT (fpo_id) DO UPDATE SET
                active_farmer_count = EXCLUDED.active_farmer_count,
                pending_farmer_count = EXCLUDED.pending_farmer_count,
                active_farm_count = EXCLUDED.active_farm_count,
                registered_area_acres = EXCLUDED.registered_area_acres,
                active_crop_count = EXCLUDED.active_crop_count,
                district_count = EXCLUDED.district_count,
                block_count = EXCLUDED.block_count,
                village_count = EXCLUDED.village_count,
                open_alert_count = EXCLUDED.open_alert_count,
                attention_farm_count = EXCLUDED.attention_farm_count,
                critical_farm_count = EXCLUDED.critical_farm_count,
                data_through = EXCLUDED.data_through,
                updated_at = now()
        """), {"fpo_id": oid, "profile_fpo_id": str(profile_fpo_id) if profile_fpo_id else None})
        refreshed += 1
    return {"organizations_refreshed": refreshed}


def get_fpo_dashboard_read_model(conn: Connection, *, user_id: UUID | str) -> dict[str, Any]:
    entitlements = require_fpo_feature(conn, user_id=user_id, feature_key="BASIC_REPORTS")
    row = conn.execute(text("SELECT * FROM public.fpo_portfolio_summary WHERE fpo_id = :fpo_id"), {"fpo_id": str(entitlements["fpo_id"])}).mappings().first()
    organization = conn.execute(text("""
        SELECT o.fpo_id, o.public_fpo_id, o.verification_status, o.lifecycle_status,
               o.commercial_status, a.class_code, p.display_name, p.fpo_name
        FROM public.fpo_organizations o
        LEFT JOIN public.fpo_class_assignments a ON a.fpo_id = o.fpo_id AND a.is_active = TRUE
        LEFT JOIN public.fpos p ON p.fpo_id = o.profile_fpo_id
        WHERE o.fpo_id = :fpo_id
    """), {"fpo_id": str(entitlements["fpo_id"])}).mappings().first() or {}
    row = dict(row) if row else {}
    stale = row.get("updated_at") is None or (row.get("updated_at") and (__import__("datetime").datetime.now(__import__("datetime").timezone.utc) - row["updated_at"]).total_seconds() > 86400)
    return {
        "schema_version": 2,
        "organization": {"fpo_id": organization.get("fpo_id", entitlements["fpo_id"]), "public_fpo_id": organization.get("public_fpo_id"), "display_name": organization.get("display_name") or organization.get("fpo_name"), "class_code": organization.get("class_code"), "verification_status": organization.get("verification_status"), "lifecycle_status": organization.get("lifecycle_status"), "commercial_status": organization.get("commercial_status")},
        "portfolio": {"active_farmer_count": row.get("active_farmer_count", 0), "pending_farmer_count": row.get("pending_farmer_count", 0), "active_farm_count": row.get("active_farm_count", 0), "registered_area_acres": row.get("registered_area_acres", 0), "active_crop_count": row.get("active_crop_count", 0)},
        "coverage": {"district_count": row.get("district_count", 0), "block_count": row.get("block_count", 0), "village_count": row.get("village_count", 0)},
        "attention": {"open_alert_count": row.get("open_alert_count", 0), "critical_alert_count": row.get("critical_farm_count", 0), "attention_farm_count": row.get("attention_farm_count", 0)},
        "data_freshness": {"data_through": row.get("data_through"), "calculation_version": row.get("calculation_version", "fpo-portfolio-v2"), "stale": bool(stale)},
    }


def list_fpo_farmer_portfolio(
    conn: Connection,
    *,
    user_id: UUID | str,
    query: str | None = None,
    district_code: int | None = None,
    block_code: int | None = None,
    relationship_status: str | None = None,
    cursor: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    entitlements = require_fpo_feature(conn, user_id=user_id, feature_key="FARMER_DIRECTORY")
    after_name = after_id = None
    if cursor:
        try:
            decoded = base64.urlsafe_b64decode(cursor.encode()).decode().split("|", 1)
            after_name, after_id = decoded
        except Exception as exc:
            raise ValueError("Invalid farmer directory cursor") from exc
    rows = conn.execute(text("""
        SELECT farmer_id, farmer_name, phone_masked, district_code, district_name, block_code,
               block_name, village_name, farm_count, area_acres, active_crop_codes,
               condition_status, highest_alert_severity, open_alert_count, latest_observation_at,
               latest_analysis_date, relationship_status, updated_at
        FROM public.fpo_farmer_portfolio
        WHERE fpo_id = :fpo_id
          AND EXISTS (
              SELECT 1 FROM public.fpo_farmer_relationships r
              JOIN public.fpo_farmer_relationship_consents c ON c.relationship_id=r.relationship_id
              WHERE r.fpo_id=:fpo_id AND r.farmer_profile_id=fpo_farmer_portfolio.farmer_id
                AND r.farm_id IS NOT NULL AND r.status='ACTIVE'
                AND c.revoked_at IS NULL AND (c.expires_at IS NULL OR c.expires_at>now())
                AND 'PROFILE_READ'=ANY(c.scopes) AND 'FARM_READ'=ANY(c.scopes)
          )
          AND (:query IS NULL OR lower(farmer_name) LIKE lower(:pattern) OR lower(COALESCE(phone_masked, '')) LIKE lower(:pattern) OR farmer_id::text = :query)
          AND (:district_code IS NULL OR district_code = :district_code)
          AND (:block_code IS NULL OR block_code = :block_code)
          AND (:relationship_status IS NULL OR relationship_status = :relationship_status)
          AND (:after_name IS NULL OR (farmer_name, farmer_id::text) > (:after_name, :after_id))
        ORDER BY farmer_name, farmer_id
        LIMIT :limit
    """), {"fpo_id": str(entitlements["fpo_id"]), "query": query, "pattern": f"%{query}%" if query else "%", "district_code": district_code, "block_code": block_code, "relationship_status": relationship_status.upper() if relationship_status else None, "after_name": after_name, "after_id": after_id, "limit": max(1, min(limit, 100)) + 1}).mappings().all()
    has_more = len(rows) > max(1, min(limit, 100))
    page = rows[:max(1, min(limit, 100))]
    next_cursor = None
    if has_more and page:
        last = page[-1]
        next_cursor = base64.urlsafe_b64encode(f"{last['farmer_name']}|{last['farmer_id']}".encode()).decode()
    return {"items": [dict(row) for row in page], "next_cursor": next_cursor, "limit": max(1, min(limit, 100))}


def record_sensitive_access(conn: Connection, *, fpo_id: UUID | str, actor_user_id: UUID | str, farmer_id: UUID | str | None, operation: str, scopes: list[str]) -> None:
    conn.execute(text("""
        INSERT INTO public.fpo_sensitive_access_events (fpo_id, actor_user_id, farmer_id, operation, scopes)
        VALUES (:fpo_id, :actor, :farmer_id, :operation, :scopes)
    """), {"fpo_id": str(fpo_id), "actor": str(actor_user_id), "farmer_id": str(farmer_id) if farmer_id else None, "operation": operation, "scopes": scopes})


def get_fpo_farmer_detail(conn: Connection, *, user_id: UUID | str, farmer_id: UUID | str) -> dict[str, Any]:
    org = get_fpo_access_context(conn, user_id=user_id)
    require_fpo_feature(conn, user_id=user_id, feature_key="FARMER_DETAIL")
    row = conn.execute(text("""
        SELECT r.relationship_id, r.fpo_id, r.status AS relationship_status,
               fp.farmer_id, fp.full_name, u.email,
               COALESCE(portfolio.phone_masked, 'Not available') AS phone_number,
               COALESCE(fp.profile_image_url, u.profile_image_url) AS profile_image_url,
               fp.gender, fp.aadhaar_last4, fp.kyc_status,
               fp.state_name, fp.district_name, fp.block_name, fp.village_name,
               fp.total_landholding_acres, fp.cultivated_area_acres,
               fp.primary_crop, fp.profile_version,
               c.consent_id, c.policy_code, c.policy_version, c.purpose,
               c.scopes, c.language_code, c.captured_at, c.expires_at
        FROM public.fpo_farmer_relationships r
        JOIN public.fpo_organizations o ON o.fpo_id = r.fpo_id AND o.auth_user_id = :user_id
        JOIN public.farmer_profiles fp ON fp.farmer_id = r.farmer_profile_id
        LEFT JOIN public.users u ON u.user_id = fp.user_id
        LEFT JOIN public.fpo_farmer_portfolio portfolio
          ON portfolio.fpo_id = r.fpo_id AND portfolio.farmer_id = fp.farmer_id
        LEFT JOIN LATERAL (
            SELECT * FROM public.fpo_farmer_relationship_consents
            WHERE relationship_id = r.relationship_id AND revoked_at IS NULL
              AND (expires_at IS NULL OR expires_at > now())
            ORDER BY captured_at DESC LIMIT 1
        ) c ON TRUE
        WHERE fp.farmer_id = :farmer_id AND r.status = 'ACTIVE'
          AND r.farm_id IS NOT NULL AND 'PROFILE_READ'=ANY(c.scopes)
          AND 'FARM_READ'=ANY(c.scopes)
          AND 'CONTACT_MASKED_READ'=ANY(c.scopes)
        LIMIT 1
    """), {"user_id": str(user_id), "farmer_id": str(farmer_id)}).mappings().first()
    if not row:
        raise ValueError("FPO_RELATIONSHIP_REQUIRED")
    if not row["consent_id"]:
        raise ValueError("FPO_CONSENT_REQUIRED")
    record_sensitive_access(conn, fpo_id=org["fpo_id"], actor_user_id=user_id, farmer_id=farmer_id, operation="FARMER_DETAIL_READ", scopes=row["scopes"] or [])
    return dict(row)


def list_fpo_farmer_farms(conn: Connection, *, user_id: UUID | str, farmer_id: UUID | str) -> list[dict[str, Any]]:
    org = get_fpo_access_context(conn, user_id=user_id)
    require_fpo_feature(conn, user_id=user_id, feature_key="FARM_PORTFOLIO_READ")
    access = conn.execute(text("""
        SELECT r.relationship_id, r.farm_id, c.consent_id, c.scopes
        FROM public.fpo_farmer_relationships r
        JOIN public.fpo_organizations o ON o.fpo_id = r.fpo_id AND o.auth_user_id = :user_id
        JOIN public.fpo_farmer_relationship_consents c ON c.relationship_id = r.relationship_id
          AND c.revoked_at IS NULL AND (c.expires_at IS NULL OR c.expires_at > now())
        WHERE r.farmer_profile_id = :farmer_id AND r.fpo_id=:fpo_id
          AND r.status = 'ACTIVE' AND r.farm_id IS NOT NULL
          AND 'FARM_READ'=ANY(c.scopes)
        ORDER BY c.captured_at DESC LIMIT 1
    """), {"user_id": str(user_id), "farmer_id": str(farmer_id), "fpo_id": str(org["fpo_id"])}).mappings().first()
    if not access:
        raise ValueError("FPO_CONSENT_REQUIRED")
    if "FARM_READ" not in (access["scopes"] or []):
        raise ValueError("FPO_FARM_SCOPE_FORBIDDEN")
    rows = conn.execute(text("""
        SELECT f.farm_id, f.farmer_id, f.farm_name, f.survey_number, f.state_name, f.district_name,
               district_code, block_name, block_code, village_name, crop_code, crop_name,
               crop_variety, crop_stage, planting_date, area_acres, h3_resolution,
               h3_cell_count, polygon_geojson, is_active, created_at, updated_at
        FROM public.farms f
        WHERE f.farmer_id = :farmer_id AND f.is_active = TRUE
          AND f.farm_id IN (
              SELECT r.farm_id
              FROM public.fpo_farmer_relationships r
              JOIN public.fpo_farmer_relationship_consents c ON c.relationship_id = r.relationship_id
              WHERE r.farmer_profile_id = :farmer_id AND r.fpo_id = :fpo_id
                AND r.status = 'ACTIVE' AND r.farm_id IS NOT NULL
                AND c.revoked_at IS NULL AND (c.expires_at IS NULL OR c.expires_at > now())
                AND 'FARM_READ' = ANY(c.scopes)
          )
        ORDER BY created_at DESC, farm_id
    """), {"farmer_id": str(farmer_id), "fpo_id": str(org["fpo_id"])}).mappings().all()
    record_sensitive_access(conn, fpo_id=org["fpo_id"], actor_user_id=user_id, farmer_id=farmer_id, operation="FARM_LIST_READ", scopes=access["scopes"] or [])
    return [dict(row) for row in rows]


def list_fpo_farm_monitoring(conn: Connection, *, user_id: UUID | str, query: str | None = None) -> list[dict[str, Any]]:
    """Return consent-scoped farms for the FPO monitoring workspace."""
    org = get_fpo_access_context(conn, user_id=user_id)
    require_fpo_feature(conn, user_id=user_id, feature_key="FARM_PORTFOLIO_READ")
    rows = conn.execute(text("""
        WITH permitted AS (
            SELECT DISTINCT ON (f.farm_id)
                   f.farm_id, f.farmer_id, f.farm_name, f.state_name, f.district_name,
                   f.block_name, f.village_name, f.crop_code, f.crop_name, f.crop_stage,
                   f.area_acres, f.polygon_geojson, f.updated_at
            FROM public.farms f
            JOIN public.fpo_farmer_relationships r
              ON r.farm_id=f.farm_id AND r.fpo_id=:fpo_id AND r.status='ACTIVE'
            JOIN public.fpo_farmer_relationship_consents c
              ON c.relationship_id=r.relationship_id
             AND c.revoked_at IS NULL
             AND (c.expires_at IS NULL OR c.expires_at > now())
             AND 'FARM_READ'=ANY(c.scopes)
            WHERE f.is_active=TRUE
              AND (:query IS NULL OR lower(f.farm_name) LIKE lower(:pattern)
                   OR lower(COALESCE(f.crop_name,'')) LIKE lower(:pattern)
                   OR lower(COALESCE(f.village_name,'')) LIKE lower(:pattern)
                   OR EXISTS (
                       SELECT 1 FROM public.fpo_farmer_portfolio search_fp
                       WHERE search_fp.fpo_id=:fpo_id
                         AND search_fp.farmer_id=f.farmer_id
                         AND lower(COALESCE(search_fp.farmer_name,'')) LIKE lower(:pattern)
                   )
                   OR EXISTS (
                       SELECT 1 FROM public.fpo_farmer_portfolio search_phone
                       WHERE search_phone.fpo_id=:fpo_id
                         AND search_phone.farmer_id=f.farmer_id
                         AND lower(COALESCE(search_phone.phone_masked,'')) LIKE lower(:pattern)
                   ))
            ORDER BY f.farm_id, c.captured_at DESC
        ), latest_predictions AS (
            SELECT p.*
            FROM public.farm_calculated_predictions p
            JOIN (SELECT farm_id, MAX(result_date) AS result_date
                  FROM public.farm_calculated_predictions
                  WHERE result_scope='farm' GROUP BY farm_id) latest
              ON latest.farm_id=p.farm_id AND latest.result_date=p.result_date
            WHERE p.result_scope='farm'
        ), prediction_rollup AS (
            SELECT farm_id, MAX(result_date) AS latest_analysis_date,
                   jsonb_agg(jsonb_build_object(
                     'prediction_key', prediction_key, 'display_name', display_name,
                     'score', score, 'status_label', status_label, 'result_date', result_date
                   ) ORDER BY prediction_key) AS predictions,
                   CASE WHEN bool_or(status_label='critical') THEN 'CRITICAL'
                        WHEN bool_or(status_label IN ('high','attention','poor')) THEN 'NEEDS_ATTENTION'
                        WHEN bool_or(status_label IN ('watch','fair')) THEN 'WATCH'
                        WHEN COUNT(*) > 0 THEN 'NORMAL' ELSE 'NO_DATA' END AS overall_status
            FROM latest_predictions GROUP BY farm_id
        ), alert_rollup AS (
            SELECT farm_id, COUNT(*)::integer AS open_alert_count,
                   MAX(severity) AS highest_alert_severity
            FROM public.fpo_operational_alerts
            WHERE fpo_id=:fpo_id AND status IN ('OPEN','ACKNOWLEDGED','IN_PROGRESS')
            GROUP BY farm_id
        ), observations AS (
            SELECT farm_id, MAX(snapshot_date) AS latest_observation_date
            FROM public.h3_sentinel2_features GROUP BY farm_id
        )
        SELECT p.farm_id, p.farmer_id, COALESCE(fp.farmer_name, 'Farmer') AS farmer_name, fp.phone_masked, p.farm_name, p.state_name, p.district_name,
               p.block_name, p.village_name, p.crop_code, p.crop_name, p.crop_stage,
               p.area_acres, p.polygon_geojson, p.updated_at, pr.latest_analysis_date, o.latest_observation_date,
               COALESCE(pr.overall_status, 'NO_DATA') AS overall_status,
               COALESCE(ar.open_alert_count, 0) AS open_alert_count,
               ar.highest_alert_severity, COALESCE(pr.predictions, '[]'::jsonb) AS predictions
        FROM permitted p
        LEFT JOIN public.fpo_farmer_portfolio fp ON fp.fpo_id=:fpo_id AND fp.farmer_id=p.farmer_id
        LEFT JOIN prediction_rollup pr ON pr.farm_id=p.farm_id
        LEFT JOIN alert_rollup ar ON ar.farm_id=p.farm_id
        LEFT JOIN observations o ON o.farm_id=p.farm_id
        ORDER BY p.farm_name;
    """), {"fpo_id": str(org["fpo_id"]), "query": query, "pattern": f"%{query}%" if query else "%"}).mappings().all()
    record_sensitive_access(conn, fpo_id=org["fpo_id"], actor_user_id=user_id, farmer_id=None, operation="FARM_MONITORING_READ", scopes=["FARM_READ"])
    return [dict(row) for row in rows]


def authorize_fpo_farm_intelligence(conn: Connection, *, user_id: UUID | str, farmer_id: UUID | str, farm_id: UUID | str) -> dict[str, Any]:
    org = get_fpo_access_context(conn, user_id=user_id)
    entitlements = require_fpo_feature(conn, user_id=user_id, feature_key="LAND_INTELLIGENCE_BASIC")
    row = conn.execute(text("""
        SELECT f.farm_id, f.farmer_id, f.farm_name, f.crop_name, f.crop_stage, f.area_acres,
               f.state_name, f.district_name, f.block_name, f.village_name, f.polygon_geojson,
               r.relationship_id, c.scopes
        FROM public.farms f
        JOIN public.fpo_farmer_relationships r
          ON r.farm_id = f.farm_id AND r.fpo_id = :fpo_id AND r.status = 'ACTIVE'
        JOIN public.fpo_farmer_relationship_consents c
          ON c.relationship_id = r.relationship_id AND c.revoked_at IS NULL
         AND (c.expires_at IS NULL OR c.expires_at > now())
        WHERE f.farm_id = :farm_id AND f.farmer_id = :farmer_id
          AND f.is_active = TRUE
        ORDER BY c.captured_at DESC LIMIT 1
    """), {"fpo_id": str(entitlements["fpo_id"]), "profile_fpo_id": str(org["profile_fpo_id"]), "farmer_id": str(farmer_id), "farm_id": str(farm_id)}).mappings().first()
    if not row:
        raise ValueError("FPO_FARM_SCOPE_FORBIDDEN")
    scopes = row["scopes"] or []
    if "FARM_READ" not in scopes or "LAND_INTELLIGENCE_READ" not in scopes:
        raise ValueError("FPO_CONSENT_REQUIRED")
    record_sensitive_access(conn, fpo_id=entitlements["fpo_id"], actor_user_id=user_id, farmer_id=farmer_id, operation="FARM_INTELLIGENCE_READ", scopes=scopes)
    return dict(row)


def create_support_ticket(
    conn: Connection, *, farmer_user_id: UUID | str, farm_id: UUID | str | None,
    fpo_id: UUID | str | None, category: str, subject: str, description: str,
) -> dict[str, Any]:
    if farm_id:
        owned = conn.execute(text("SELECT 1 FROM public.farms WHERE farm_id = :farm_id AND farmer_id = (SELECT farmer_id FROM public.farmer_profiles WHERE user_id = :user_id) AND is_active = TRUE"), {"farm_id": str(farm_id), "user_id": str(farmer_user_id)}).scalar_one_or_none()
        if not owned:
            raise ValueError("The selected farm is not owned by this farmer")
    row = conn.execute(text("""
        INSERT INTO public.fpo_support_tickets
            (farmer_user_id, farm_id, fpo_id, category, subject, description)
        VALUES (:farmer_user_id, :farm_id, :fpo_id, :category, :subject, :description)
        RETURNING ticket_id, farmer_user_id, farm_id, fpo_id, category, subject, description, status, created_at
    """), {"farmer_user_id": str(farmer_user_id), "farm_id": str(farm_id) if farm_id else None, "fpo_id": str(fpo_id) if fpo_id else None, "category": category, "subject": subject.strip(), "description": description.strip()}).mappings().one()
    return dict(row)


def list_support_tickets(conn: Connection, *, farmer_user_id: UUID | str) -> list[dict[str, Any]]:
    rows = conn.execute(text("""
        SELECT ticket_id, farm_id, fpo_id, category, subject, description, status, created_at, updated_at
        FROM public.fpo_support_tickets
        WHERE farmer_user_id = :farmer_user_id
        ORDER BY created_at DESC
    """), {"farmer_user_id": str(farmer_user_id)}).mappings().all()
    return [dict(row) for row in rows]
