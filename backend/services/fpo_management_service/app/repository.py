from __future__ import annotations

from typing import Any
from uuid import UUID
import json
import base64

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
            SET status = 'published', published_at = now(), last_error = NULL,
                locked_at = NULL, updated_at = now()
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

    existing_profile = conn.execute(
        text(
            """
            SELECT p.fpo_id, p.contact_email, fu.user_id AS bound_user_id
            FROM public.fpos p
            LEFT JOIN public.fpo_users fu
              ON fu.fpo_id = p.fpo_id AND fu.is_active = TRUE
            WHERE p.registration_number = :registration_number
            LIMIT 1;
            """
        ),
        {"registration_number": basics.get("registration_number")},
    ).mappings().first()

    if existing_profile:
        same_owner = (
            str(existing_profile.get("bound_user_id")) == user_id
            and str(existing_profile.get("contact_email", "")).lower() == str(payload.get("email", "")).lower()
        )
        if not same_owner:
            error = "FPO registration number is already linked to another account"
            conn.execute(
                text("UPDATE public.fpo_organizations SET provisioning_status = 'FAILED', provisioning_error = :error, updated_at = now(), version = version + 1 WHERE fpo_id = :fpo_id"),
                {"fpo_id": str(org["fpo_id"]), "error": error},
            )
            return {**org, "provisioning_status": "FAILED", "provisioning_error": error}
        conn.execute(
            text(
                """
                UPDATE public.fpos
                SET fpo_name = COALESCE(:fpo_name, fpo_name),
                    registration_type = COALESCE(:registration_type, registration_type),
                    contact_person_name = COALESCE(:contact_person_name, contact_person_name),
                    contact_phone = COALESCE(:contact_phone, contact_phone),
                    contact_email = COALESCE(:contact_email, contact_email),
                    district_code = COALESCE(:district_code, district_code),
                    updated_at = now(), profile_version = profile_version + 1
                WHERE fpo_id = :fpo_id;
                """
            ),
            {
                "fpo_id": str(existing_profile["fpo_id"]),
                "fpo_name": basics.get("organisation_name"),
                "registration_type": basics.get("registration_type"),
                "contact_person_name": payload.get("full_name"),
                "contact_phone": payload.get("phone_number"),
                "contact_email": payload.get("email"),
                "district_code": basics.get("district_code"),
            },
        )
        fpo = dict(existing_profile)
    else:
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
                provisioning_status = 'READY', provisioning_error = NULL,
                updated_at = now(), version = version + 1
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


def get_portal_bootstrap(conn: Connection, user_id: UUID | str) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.public_fpo_id, o.lifecycle_status, o.verification_status,
                   o.verification_level, o.commercial_status, o.approved_at,
                   o.provisioning_status, p.display_name, p.fpo_name,
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
        "organization": {"fpo_id": row["fpo_id"], "public_fpo_id": row["public_fpo_id"], "display_name": row["display_name"] or row["fpo_name"], "lifecycle_status": row["lifecycle_status"]},
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
    if status == "APPROVED":
        conn.execute(
            text(
                """
                INSERT INTO public.fpo_class_assignments
                    (fpo_id, class_code, configuration_version, assigned_by)
                VALUES (:fpo_id, 'A', 1, :assigned_by)
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


def create_farmer_relationship_request(conn: Connection, *, farmer_user_id: UUID | str, fpo_id: UUID | str) -> dict[str, Any]:
    target = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.profile_fpo_id, o.verification_status, o.lifecycle_status,
                   fp.farmer_id
            FROM public.fpo_organizations o
            LEFT JOIN public.farmer_profiles fp ON fp.user_id = :farmer_user_id
            WHERE o.fpo_id = :fpo_id
              AND o.verification_status = 'APPROVED'
              AND o.lifecycle_status = 'ACTIVE'
              AND o.discoverable = TRUE;
            """
        ),
        {"fpo_id": str(fpo_id), "farmer_user_id": str(farmer_user_id)},
    ).mappings().first()
    if not target:
        raise ValueError("This FPO is not available for farmer association")
    active = conn.execute(
        text(
            """
            SELECT relationship_id FROM public.fpo_farmer_relationships
            WHERE farmer_user_id = :farmer_user_id AND status = 'ACTIVE'
            LIMIT 1;
            """
        ),
        {"farmer_user_id": str(farmer_user_id)},
    ).scalar_one_or_none()
    if active:
        raise ValueError("You already have an active primary FPO")
    relationship = conn.execute(
        text(
            """
            INSERT INTO public.fpo_farmer_relationships
                (fpo_id, farmer_user_id, farmer_profile_id, relationship_type, status, initiated_by, farmer_consented_at)
            VALUES (:fpo_id, :farmer_user_id, :farmer_profile_id, 'PRIMARY', 'PENDING_FPO_ACCEPTANCE', 'FARMER', now())
            RETURNING relationship_id, fpo_id, farmer_user_id, status, farmer_consented_at, created_at;
            """
        ),
        {"fpo_id": str(fpo_id), "farmer_user_id": str(farmer_user_id), "farmer_profile_id": target["farmer_id"]},
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
    return dict(relationship)


def list_farmer_relationships(conn: Connection, *, farmer_user_id: UUID | str) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            SELECT r.relationship_id, r.fpo_id, r.status, r.relationship_type,
                   r.farmer_consented_at, r.fpo_accepted_at, r.created_at,
                   o.public_fpo_id, p.fpo_name, p.state_name, p.district_name
            FROM public.fpo_farmer_relationships r
            JOIN public.fpo_organizations o ON o.fpo_id = r.fpo_id
            LEFT JOIN public.fpos p ON p.fpo_id = o.profile_fpo_id
            WHERE r.farmer_user_id = :farmer_user_id
            ORDER BY r.created_at DESC;
            """
        ),
        {"farmer_user_id": str(farmer_user_id)},
    ).mappings().all()
    return [dict(row) for row in rows]


def list_fpo_relationships(conn: Connection, *, fpo_user_id: UUID | str) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            SELECT r.relationship_id, r.fpo_id, r.farmer_user_id, r.status,
                   r.relationship_type, r.farmer_consented_at, r.created_at,
                   fp.farmer_id, fp.full_name, fp.state_name, fp.district_name,
                   u.email, u.phone_number
            FROM public.fpo_farmer_relationships r
            JOIN public.fpo_organizations o ON o.fpo_id = r.fpo_id AND o.auth_user_id = :fpo_user_id
            LEFT JOIN public.farmer_profiles fp ON fp.farmer_id = r.farmer_profile_id
            JOIN public.users u ON u.user_id = r.farmer_user_id
            ORDER BY r.created_at DESC;
            """
        ),
        {"fpo_user_id": str(fpo_user_id)},
    ).mappings().all()
    return [dict(row) for row in rows]


def decide_farmer_relationship(conn: Connection, *, fpo_user_id: UUID | str, relationship_id: UUID | str, decision: str) -> dict[str, Any]:
    if decision not in {"ACTIVE", "REJECTED"}:
        raise ValueError("Relationship decision must be ACTIVE or REJECTED")
    row = conn.execute(
        text(
            """
            SELECT r.relationship_id, r.fpo_id, r.farmer_user_id, r.farmer_profile_id, r.status,
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
    event = "ACCEPTED" if decision == "ACTIVE" else "REJECTED"
    conn.execute(
        text("INSERT INTO public.fpo_farmer_relationship_events (relationship_id, event_type, actor_user_id) VALUES (:relationship_id, :event_type, :actor_user_id)"),
        {"relationship_id": str(relationship_id), "event_type": event, "actor_user_id": str(fpo_user_id)},
    )
    if decision == "ACTIVE":
        conn.execute(
            text(
                """
                UPDATE public.farmer_profiles
                SET fpo_id = :profile_fpo_id, updated_at = now()
                WHERE farmer_id = :farmer_profile_id;
                """
            ),
            {"profile_fpo_id": str(row["profile_fpo_id"]), "farmer_profile_id": str(row["farmer_profile_id"])},
        )
    record_fpo_audit_event(
        conn,
        fpo_id=row["fpo_id"],
        actor_user_id=fpo_user_id,
        action="FPO_RELATIONSHIP_DECIDED",
        target_type="farmer_relationship",
        target_id=relationship_id,
        metadata={"decision": decision, "farmer_user_id": str(row["farmer_user_id"])},
    )
    return {"relationship_id": relationship_id, "status": decision}


def revoke_farmer_relationship(conn: Connection, *, farmer_user_id: UUID | str, relationship_id: UUID | str) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            SELECT relationship_id, fpo_id, farmer_profile_id FROM public.fpo_farmer_relationships
            WHERE relationship_id = :relationship_id AND farmer_user_id = :farmer_user_id AND status = 'ACTIVE'
            FOR UPDATE;
            """
        ),
        {"relationship_id": str(relationship_id), "farmer_user_id": str(farmer_user_id)},
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
        text("UPDATE public.farmer_profiles SET fpo_id = NULL, updated_at = now() WHERE farmer_id = :farmer_profile_id AND fpo_id IS NOT NULL"),
        {"farmer_profile_id": str(row["farmer_profile_id"])},
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
    return {"relationship_id": relationship_id, "status": "REVOKED"}


def resolve_fpo_entitlements(conn: Connection, *, user_id: UUID | str) -> dict[str, Any]:
    org = conn.execute(
        text(
            """
            SELECT o.fpo_id, o.public_fpo_id, o.verification_status,
                   a.class_code, a.configuration_version
            FROM public.fpo_organizations o
            LEFT JOIN public.fpo_class_assignments a
              ON a.fpo_id = o.fpo_id AND a.is_active = TRUE
             AND (a.expires_at IS NULL OR a.expires_at > now())
            WHERE o.auth_user_id = :user_id
            LIMIT 1;
            """
        ),
        {"user_id": str(user_id)},
    ).mappings().first()
    if not org:
        return {"fpo_id": None, "class_code": None, "features": {}, "status": "PENDING_PROVISIONING"}
    class_code = org.get("class_code") or "A"
    version = org.get("configuration_version") or 1
    rows = conn.execute(
        text(
            """
            SELECT c.feature_key, c.display_name, c.description, c.category,
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
        }
        for row in rows
    }
    return {
        "fpo_id": org["fpo_id"],
        "public_fpo_id": org["public_fpo_id"],
        "class_code": class_code,
        "configuration_version": version,
        "verification_status": org["verification_status"],
        "features": features,
    }


def list_feature_catalogue(conn: Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            SELECT c.feature_key, c.display_name, c.description, c.category, c.is_active,
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
            VALUES (:fpo_id, :class_code, 1, :assigned_by)
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
        metadata={"class_code": class_code, "configuration_version": 1},
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
                COUNT(*) FILTER (WHERE r.status = 'ACTIVE') AS active_relationships,
                COUNT(*) FILTER (WHERE r.status = 'PENDING_FPO_ACCEPTANCE') AS pending_relationships,
                COUNT(*) FILTER (WHERE r.status = 'REJECTED') AS rejected_relationships,
                COUNT(DISTINCT r.farmer_user_id) FILTER (WHERE r.status = 'ACTIVE') AS active_farmers,
                COUNT(DISTINCT r.farmer_profile_id) FILTER (WHERE r.status = 'ACTIVE') AS linked_profiles
            FROM public.fpo_farmer_relationships r
            WHERE r.fpo_id = :fpo_id;
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
            SELECT :fpo_id, fp.farmer_id, COALESCE(fp.full_name, 'Unnamed farmer'),
                   CASE WHEN length(u.phone_number) > 4 THEN repeat('*', length(u.phone_number) - 4) || right(u.phone_number, 4) ELSE u.phone_number END,
                   fp.district_code, fp.district_name, fp.block_code, fp.block_name, fp.village_name,
                   COUNT(DISTINCT f.farm_id)::integer, COALESCE(SUM(f.area_acres), 0),
                   COALESCE(array_agg(DISTINCT f.crop_code) FILTER (WHERE f.crop_code IS NOT NULL), '{}'),
                   MAX(fa.severity), COUNT(DISTINCT fa.alert_id)::integer, r.status
            FROM public.fpo_farmer_relationships r
            JOIN public.farmer_profiles fp ON fp.farmer_id = r.farmer_profile_id
            LEFT JOIN public.users u ON u.user_id = fp.user_id
            LEFT JOIN public.farms f ON f.farmer_id = fp.farmer_id AND f.is_active = TRUE AND f.fpo_id = :profile_fpo_id
            LEFT JOIN public.farm_alerts fa ON fa.farm_id = f.farm_id AND fa.acknowledged_at IS NULL
            WHERE r.fpo_id = :fpo_id AND r.status IN ('ACTIVE', 'PENDING_FPO_ACCEPTANCE')
            GROUP BY fp.farmer_id, fp.full_name, u.phone_number, fp.district_code, fp.district_name,
                     fp.block_code, fp.block_name, fp.village_name, r.status
        """), {"fpo_id": oid, "profile_fpo_id": str(profile_fpo_id) if profile_fpo_id else None})
        conn.execute(text("""
            INSERT INTO public.fpo_portfolio_summary
                (fpo_id, active_farmer_count, pending_farmer_count, active_farm_count,
                 registered_area_acres, active_crop_count, district_count, block_count,
                 village_count, open_alert_count, attention_farm_count, critical_farm_count,
                 data_through, updated_at)
            SELECT :fpo_id,
                COUNT(*) FILTER (WHERE relationship_status = 'ACTIVE')::integer,
                COUNT(*) FILTER (WHERE relationship_status = 'PENDING_FPO_ACCEPTANCE')::integer,
                COALESCE(SUM(farm_count) FILTER (WHERE relationship_status = 'ACTIVE'), 0)::integer,
                COALESCE(SUM(area_acres) FILTER (WHERE relationship_status = 'ACTIVE'), 0),
                COALESCE((SELECT COUNT(DISTINCT f.crop_code) FROM public.farms f WHERE f.fpo_id = :profile_fpo_id AND f.is_active = TRUE AND f.crop_code IS NOT NULL), 0)::integer,
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
    return dict(row) if row else {"fpo_id": entitlements["fpo_id"], "updated_at": None, "calculation_version": "fpo-portfolio-v1"}


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
          AND (:query IS NULL OR lower(farmer_name) LIKE lower(:pattern) OR farmer_id::text = :query)
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
