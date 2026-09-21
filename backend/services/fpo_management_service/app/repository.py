from __future__ import annotations

from typing import Any
from uuid import UUID
import json

from sqlalchemy import text
from sqlalchemy.engine import Connection


STATE_CODES = {21: "OD", 9: "UP", 27: "MH", 29: "KA", 33: "TN", 32: "KL", 19: "WB"}
CHECK_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ"


def public_fpo_id(state_code: int, sequence_number: int) -> str:
    state = STATE_CODES.get(int(state_code), f"S{int(state_code):02d}")[:3].upper()
    check = CHECK_ALPHABET[sequence_number % len(CHECK_ALPHABET)]
    return f"MTFPO-{state}-{__import__('datetime').datetime.now().year % 100:02d}-{sequence_number:06d}-{check}"


def claim_events(conn: Connection, *, batch_size: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            WITH candidates AS (
                SELECT event_id
                FROM public.auth_outbox_events
                WHERE (status IN ('queued', 'failed') AND available_at <= now())
                   OR (status = 'publishing' AND locked_at < now() - interval '5 minutes')
                ORDER BY available_at, created_at
                FOR UPDATE SKIP LOCKED
                LIMIT :batch_size
            )
            UPDATE public.auth_outbox_events AS e
            SET status = 'publishing', locked_at = now(), attempts = e.attempts + 1, updated_at = now()
            FROM candidates
            WHERE e.event_id = candidates.event_id
            RETURNING e.*;
            """
        ),
        {"batch_size": batch_size},
    ).mappings().all()
    return [dict(row) for row in rows]


def mark_published(conn: Connection, event_id: UUID | str) -> None:
    conn.execute(
        text(
            """
            UPDATE public.auth_outbox_events
            SET status = 'published', published_at = now(), locked_at = NULL, updated_at = now()
            WHERE event_id = :event_id;
            """
        ),
        {"event_id": str(event_id)},
    )


def mark_failed(conn: Connection, event_id: UUID | str, error: str) -> None:
    conn.execute(
        text(
            """
            UPDATE public.auth_outbox_events
            SET status = 'failed', last_error = :error, locked_at = NULL,
                available_at = now() + interval '30 seconds', updated_at = now()
            WHERE event_id = :event_id;
            """
        ),
        {"event_id": str(event_id), "error": error[:2000]},
    )


def provision_fpo(conn: Connection, payload: dict[str, Any]) -> dict[str, Any]:
    user_id = str(payload["user_id"])
    basics = payload.get("signup_profile") or {}
    existing = conn.execute(
        text("SELECT fpo_id, public_fpo_id, provisioning_status FROM public.fpo_organizations WHERE auth_user_id = :user_id FOR UPDATE"),
        {"user_id": user_id},
    ).mappings().first()
    if existing and existing["provisioning_status"] == "READY":
        return dict(existing)

    if existing:
        org = dict(existing)
    else:
        sequence = int(conn.execute(text("SELECT nextval('public.fpo_public_number_seq')")).scalar_one())
        public_id = public_fpo_id(int(basics.get("state_code") or 0), sequence)
        org = dict(conn.execute(
            text(
                """
                INSERT INTO public.fpo_organizations (auth_user_id, public_fpo_id, provisioning_status)
                VALUES (:user_id, :public_fpo_id, 'PROFILE_PENDING')
                RETURNING fpo_id, public_fpo_id, provisioning_status;
                """
            ),
            {"user_id": user_id, "public_fpo_id": public_id},
        ).mappings().one())

    linked_profile = conn.execute(
        text("SELECT profile_fpo_id FROM public.fpo_organizations WHERE fpo_id = :fpo_id"),
        {"fpo_id": str(org["fpo_id"])},
    ).scalar_one_or_none()
    if linked_profile:
        return {**org, "profile_fpo_id": linked_profile, "provisioning_status": "READY"}

    fpo = conn.execute(
        text(
            """
            INSERT INTO public.fpos (
                fpo_name, registration_number, registration_type,
                contact_person_name, contact_phone, contact_email,
                state_name, district_name, district_code,
                main_commodities, services_provided, verification_status,
                profile_version, is_active
            ) VALUES (
                :fpo_name, :registration_number, :registration_type,
                :contact_person_name, :contact_phone, :contact_email,
                :state_name, 'Pending', :district_code,
                ARRAY[]::text[], ARRAY[]::text[], 'pending', 1, TRUE
            )
            RETURNING fpo_id;
            """
        ),
        {
            "fpo_name": basics.get("organisation_name") or payload.get("full_name") or "New FPO",
            "registration_number": basics.get("registration_number"),
            "registration_type": basics.get("registration_type"),
            "contact_person_name": payload.get("full_name") or "FPO Representative",
            "contact_phone": payload.get("phone_number"),
            "contact_email": payload.get("email"),
            "state_name": STATE_CODES.get(int(basics.get("state_code") or 0), "Pending"),
            "district_code": basics.get("district_code"),
        },
    ).mappings().one()

    conn.execute(
        text(
            """
            INSERT INTO public.fpo_users (fpo_id, user_id, fpo_role, role, is_active, created_at, updated_at)
            VALUES (:fpo_id, :user_id, 'owner', 'owner', TRUE, now(), now())
            ON CONFLICT DO NOTHING;
            """
        ),
        {"fpo_id": str(fpo["fpo_id"]), "user_id": user_id},
    )
    conn.execute(
        text(
            """
            UPDATE public.fpo_organizations
            SET profile_fpo_id = :profile_fpo_id,
                provisioning_status = 'READY', updated_at = now(), version = version + 1
            WHERE fpo_id = :fpo_id;
            """
        ),
        {"fpo_id": str(org["fpo_id"]), "profile_fpo_id": str(fpo["fpo_id"])},
    )
    return {**dict(org), "profile_fpo_id": fpo["fpo_id"], "provisioning_status": "READY"}


def get_bootstrap_status(conn: Connection, user_id: UUID | str) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.public_fpo_id, o.provisioning_status,
                   o.lifecycle_status, o.verification_status,
                   o.profile_fpo_id,
                   p.fpo_id AS linked_profile_fpo_id
            FROM public.fpo_organizations o
            LEFT JOIN public.fpo_users u ON u.user_id = o.auth_user_id AND u.is_active = TRUE
            LEFT JOIN public.fpos p ON p.fpo_id = u.fpo_id AND p.is_active = TRUE
            WHERE o.auth_user_id = :user_id
            LIMIT 1;
            """
        ),
        {"user_id": str(user_id)},
    ).mappings().first()
    if not row:
        return {"status": "PENDING", "fpo_id": None, "public_fpo_id": None}
    result = dict(row)
    result["status"] = "READY" if result.get("provisioning_status") == "READY" else result.get("provisioning_status", "PENDING")
    return result


def get_verification_for_user(conn: Connection, user_id: UUID | str) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.public_fpo_id, o.verification_status,
                   o.verification_level, o.discoverable,
                   s.submission_id, s.status AS submission_status,
                   s.reviewer_note, s.reviewed_at, s.created_at AS submitted_at
            FROM public.fpo_organizations o
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


def submit_verification(conn: Connection, user_id: UUID | str) -> dict[str, Any]:
    org = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.public_fpo_id, o.verification_status,
                   o.profile_fpo_id, p.onboarding_completed_at,
                   p.fpo_name, p.registration_number, p.registration_type,
                   p.state_name, p.district_name, p.district_code,
                   p.contact_person_name, p.contact_phone, p.contact_email,
                   p.main_commodities, p.services_provided, p.member_count
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
    if org["verification_status"] in {"SUBMITTED", "UNDER_REVIEW", "APPROVED"}:
        raise ValueError("This FPO verification is already submitted")

    snapshot = {
        key: org.get(key)
        for key in (
            "fpo_name", "registration_number", "registration_type", "state_name",
            "district_name", "district_code", "contact_person_name", "contact_phone",
            "contact_email", "main_commodities", "services_provided", "member_count",
        )
    }
    submission = conn.execute(
        text(
            """
            INSERT INTO public.fpo_verification_submissions
                (fpo_id, submitted_by, status, profile_snapshot)
            VALUES (:fpo_id, :submitted_by, 'SUBMITTED', CAST(:snapshot AS jsonb))
            RETURNING submission_id, status, created_at;
            """
        ),
        {"fpo_id": str(org["fpo_id"]), "submitted_by": str(user_id), "snapshot": json.dumps(snapshot, default=str)},
    ).mappings().one()
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
    return {"fpo_id": org["fpo_id"], "public_fpo_id": org["public_fpo_id"], **dict(submission)}


def review_verification(
    conn: Connection,
    *,
    fpo_id: UUID | str,
    reviewer_user_id: UUID | str,
    status: str,
    note: str | None,
) -> dict[str, Any]:
    allowed = {"UNDER_REVIEW", "APPROVED", "CHANGES_REQUIRED", "REJECTED", "SUSPENDED"}
    if status not in allowed:
        raise ValueError("Unsupported verification decision")
    submission = conn.execute(
        text(
            """
            SELECT submission_id FROM public.fpo_verification_submissions
            WHERE fpo_id = :fpo_id AND status IN ('SUBMITTED', 'UNDER_REVIEW')
            ORDER BY created_at DESC LIMIT 1 FOR UPDATE;
            """
        ),
        {"fpo_id": str(fpo_id)},
    ).mappings().first()
    if not submission:
        raise ValueError("No open verification submission exists")
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
    return {"fpo_id": fpo_id, "verification_status": status, "reviewer_note": note}


def list_verification_queue(conn: Connection, *, status: str | None = None) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.public_fpo_id, o.profile_fpo_id,
                   o.verification_status, o.provisioning_status,
                   o.lifecycle_status, o.created_at,
                   p.fpo_name, p.registration_number, p.registration_type,
                   p.state_name, p.district_name, p.contact_person_name,
                   p.contact_email, p.contact_phone,
                   s.submission_id, s.status AS submission_status,
                   s.submitted_by, s.created_at AS submitted_at,
                   s.reviewer_note, s.reviewed_at
            FROM public.fpo_organizations o
            LEFT JOIN public.fpos p ON p.fpo_id = o.profile_fpo_id
            LEFT JOIN LATERAL (
                SELECT * FROM public.fpo_verification_submissions
                WHERE fpo_id = o.fpo_id
                ORDER BY created_at DESC LIMIT 1
            ) s ON TRUE
            WHERE (:status IS NULL OR o.verification_status = :status)
            ORDER BY COALESCE(s.created_at, o.created_at) DESC, o.fpo_id;
            """
        ),
        {"status": status.upper() if status else None},
    ).mappings().all()
    return [dict(row) for row in rows]
