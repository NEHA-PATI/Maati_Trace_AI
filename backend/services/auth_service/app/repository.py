from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection


USER_SELECT = """
    u.user_id AS user_id,
    u.full_name AS full_name,
    u.email AS email,
    u.phone_number AS phone_number,
    u.password_hash AS password_hash,
    u.role AS role,
    u.is_active AS is_active,
    COALESCE(u.is_verified, FALSE) AS is_verified,
    u.onboarding_status AS onboarding_status,
    u.profile_image_url AS profile_image_url
"""


def _dict(row: Any) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def get_user_by_email(conn: Connection, email: str, *, for_update: bool = False) -> dict[str, Any] | None:
    lock = " FOR UPDATE" if for_update else ""
    row = conn.execute(
        text(
            f"""
            SELECT {USER_SELECT}
            FROM users u
            WHERE lower(u.email) = lower(:email)
            LIMIT 1{lock};
            """
        ),
        {"email": email},
    ).mappings().first()
    return _dict(row)


def get_user_by_phone(conn: Connection, phone_number: str, *, for_update: bool = False) -> dict[str, Any] | None:
    lock = " FOR UPDATE" if for_update else ""
    row = conn.execute(
        text(
            f"""
            SELECT {USER_SELECT}
            FROM users u
            WHERE u.phone_number = :phone_number
            LIMIT 1{lock};
            """
        ),
        {"phone_number": phone_number},
    ).mappings().first()
    return _dict(row)


def get_user_by_id(conn: Connection, user_id: UUID | str, *, for_update: bool = False) -> dict[str, Any] | None:
    lock = " FOR UPDATE" if for_update else ""
    row = conn.execute(
        text(
            f"""
            SELECT {USER_SELECT}
            FROM users u
            WHERE u.user_id = :user_id
            LIMIT 1{lock};
            """
        ),
        {"user_id": str(user_id)},
    ).mappings().first()
    return _dict(row)


def create_user(
    conn: Connection,
    *,
    full_name: str,
    email: str,
    phone_number: str | None,
    password_hash: str | None,
    role: str,
    is_verified: bool,
    profile_image_url: str | None = None,
) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            INSERT INTO users (
                full_name,
                email,
                phone_number,
                password_hash,
                role,
                is_active,
                is_verified,
                onboarding_status,
                profile_image_url,
                updated_at
            )
            VALUES (
                :full_name,
                :email,
                :phone_number,
                :password_hash,
                :role,
                TRUE,
                :is_verified,
                'pending',
                :profile_image_url,
                now()
            )
            RETURNING
                user_id,
                full_name,
                email,
                phone_number,
                password_hash,
                role,
                is_active,
                COALESCE(is_verified, FALSE) AS is_verified,
                onboarding_status,
                profile_image_url;
            """
        ),
        {
            "full_name": full_name,
            "email": email,
            "phone_number": phone_number,
            "password_hash": password_hash,
            "role": role,
            "is_verified": is_verified,
            "profile_image_url": profile_image_url,
        },
    ).mappings().one()

    return dict(row)

def create_farmer_profile_stub(
    conn: Connection,
    *,
    user_id: UUID | str,
    full_name: str,
    phone_number: str | None,
) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            INSERT INTO farmer_profiles (
                farmer_id,
                user_id,
                fpo_id,
                full_name,
                phone_number,
                gender,
                state_name,
                district_name,
                district_code,
                block_name,
                block_code,
                village_name,
                is_active
            )
            VALUES (
                gen_random_uuid(),
                :user_id,
                NULL,
                :full_name,
                :phone_number,
                NULL,
                'Odisha',
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                TRUE
            )
            ON CONFLICT (user_id)
            DO UPDATE SET
                full_name = COALESCE(
                    NULLIF(farmer_profiles.full_name, ''),
                    EXCLUDED.full_name
                ),
                phone_number = COALESCE(
                    farmer_profiles.phone_number,
                    EXCLUDED.phone_number
                ),
                is_active = TRUE
            RETURNING
                farmer_id,
                user_id,
                full_name,
                phone_number,
                state_name,
                district_name,
                block_name,
                block_code,
                village_name,
                is_active;
            """
        ),
        {
            "user_id": str(user_id),
            "full_name": full_name,
            "phone_number": phone_number,
        },
    ).mappings().one()

    return dict(row)


def update_password_hash(conn: Connection, user_id: UUID | str, password_hash: str) -> None:
    conn.execute(
        text(
            """
            UPDATE users
            SET password_hash = :password_hash,
                updated_at = now()
            WHERE user_id = :user_id;
            """
        ),
        {"password_hash": password_hash, "user_id": str(user_id)},
    )


def mark_user_login(conn: Connection, user_id: UUID | str) -> None:
    conn.execute(
        text(
            """
            UPDATE users
            SET last_login_at = now(),
                updated_at = now()
            WHERE user_id = :user_id;
            """
        ),
        {"user_id": str(user_id)},
    )


def invalidate_active_signup_sessions(
    conn: Connection,
    *,
    email: str,
    phone_number: str,
    reason: str,
    superseded_by_session_id: UUID | str | None,
) -> int:
    result = conn.execute(
        text(
            """
            UPDATE signup_otp_sessions
            SET invalidated_at = now(),
                invalidated_reason = :reason,
                superseded_by_session_id = :superseded_by_session_id
            WHERE completed_at IS NULL
              AND invalidated_at IS NULL
              AND (lower(email) = lower(:email) OR phone_number = :phone_number);
            """
        ),
        {
            "email": email,
            "phone_number": phone_number,
            "reason": reason,
            "superseded_by_session_id": str(superseded_by_session_id) if superseded_by_session_id else None,
        },
    )
    return int(result.rowcount or 0)


def create_signup_session(
    conn: Connection,
    *,
    signup_session_id: UUID | str,
    full_name: str,
    email: str,
    phone_number: str,
    password_hash: str,
    otp_hash: str,
    otp_expires_at: datetime,
    created_ip: str | None,
    device_id_hash: str | None,
    correlation_id: str,
) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            INSERT INTO signup_otp_sessions (
                signup_session_id,
                full_name,
                phone_number,
                email,
                password_hash,
                role,
                otp_hash,
                otp_expires_at,
                attempts,
                resend_count,
                last_sent_at,
                created_ip,
                device_id_hash,
                correlation_id
            )
            VALUES (
                :signup_session_id,
                :full_name,
                :phone_number,
                :email,
                :password_hash,
                'farmer',
                :otp_hash,
                :otp_expires_at,
                0,
                0,
                now(),
                CAST(:created_ip AS inet),
                :device_id_hash,
                :correlation_id
            )
            RETURNING *;
            """
        ),
        {
            "signup_session_id": str(signup_session_id),
            "full_name": full_name,
            "phone_number": phone_number,
            "email": email,
            "password_hash": password_hash,
            "otp_hash": otp_hash,
            "otp_expires_at": otp_expires_at,
            "created_ip": created_ip,
            "device_id_hash": device_id_hash,
            "correlation_id": correlation_id,
        },
    ).mappings().one()
    return dict(row)


def get_signup_session(
    conn: Connection,
    signup_session_id: UUID | str,
    *,
    for_update: bool = False,
) -> dict[str, Any] | None:
    lock = " FOR UPDATE" if for_update else ""
    row = conn.execute(
        text(
            f"""
            SELECT
                signup_session_id,
                full_name,
                phone_number,
                email,
                password_hash,
                role,
                otp_hash,
                otp_expires_at,
                attempts,
                resend_count,
                last_sent_at,
                verified_at,
                completed_at,
                locked_at,
                invalidated_at,
                invalidated_reason,
                superseded_by_session_id,
                created_ip,
                device_id_hash,
                correlation_id
            FROM signup_otp_sessions
            WHERE signup_session_id = :signup_session_id
            LIMIT 1{lock};
            """
        ),
        {"signup_session_id": str(signup_session_id)},
    ).mappings().first()
    return _dict(row)


def update_signup_otp_for_resend(
    conn: Connection,
    *,
    signup_session_id: UUID | str,
    otp_hash: str,
    otp_expires_at: datetime,
) -> None:
    conn.execute(
        text(
            """
            UPDATE signup_otp_sessions
            SET otp_hash = :otp_hash,
                otp_expires_at = :otp_expires_at,
                attempts = 0,
                locked_at = NULL,
                resend_count = COALESCE(resend_count, 0) + 1,
                last_sent_at = now()
            WHERE signup_session_id = :signup_session_id;
            """
        ),
        {
            "signup_session_id": str(signup_session_id),
            "otp_hash": otp_hash,
            "otp_expires_at": otp_expires_at,
        },
    )


def register_invalid_otp_attempt(
    conn: Connection,
    *,
    signup_session_id: UUID | str,
    lock: bool,
) -> None:
    conn.execute(
        text(
            """
            UPDATE signup_otp_sessions
            SET attempts = COALESCE(attempts, 0) + 1,
                last_attempt_at = now(),
                locked_at = CASE WHEN :lock THEN now() ELSE locked_at END
            WHERE signup_session_id = :signup_session_id;
            """
        ),
        {"signup_session_id": str(signup_session_id), "lock": lock},
    )


def mark_signup_verified(conn: Connection, signup_session_id: UUID | str) -> None:
    conn.execute(
        text(
            """
            UPDATE signup_otp_sessions
            SET verified_at = now()
            WHERE signup_session_id = :signup_session_id;
            """
        ),
        {"signup_session_id": str(signup_session_id)},
    )


def mark_signup_completed(conn: Connection, signup_session_id: UUID | str) -> None:
    conn.execute(
        text(
            """
            UPDATE signup_otp_sessions
            SET completed_at = now()
            WHERE signup_session_id = :signup_session_id;
            """
        ),
        {"signup_session_id": str(signup_session_id)},
    )


def invalidate_signup_session(conn: Connection, signup_session_id: UUID | str, reason: str) -> None:
    conn.execute(
        text(
            """
            UPDATE signup_otp_sessions
            SET invalidated_at = COALESCE(invalidated_at, now()),
                invalidated_reason = COALESCE(invalidated_reason, :reason)
            WHERE signup_session_id = :signup_session_id
              AND completed_at IS NULL;
            """
        ),
        {"signup_session_id": str(signup_session_id), "reason": reason},
    )


def get_auth_identity(
    conn: Connection,
    *,
    provider: str,
    provider_subject: str,
    for_update: bool = False,
) -> dict[str, Any] | None:
    lock = " FOR UPDATE OF ai, u" if for_update else ""
    row = conn.execute(
        text(
            f"""
            SELECT
                ai.auth_identity_id AS auth_identity_id,
                ai.provider AS provider,
                ai.provider_subject AS provider_subject,
                ai.email AS provider_email,
                {USER_SELECT}
            FROM auth_identities ai
            JOIN users u ON u.user_id = ai.user_id
            WHERE ai.provider = :provider
              AND ai.provider_subject = :provider_subject
            LIMIT 1{lock};
            """
        ),
        {"provider": provider, "provider_subject": provider_subject},
    ).mappings().first()
    return _dict(row)


def link_auth_identity(
    conn: Connection,
    *,
    user_id: UUID | str,
    provider: str,
    provider_subject: str,
    email: str | None,
    email_verified: bool,
    raw_profile: dict[str, Any],
) -> None:
    conn.execute(
        text(
            """
            INSERT INTO auth_identities (
                user_id,
                provider,
                provider_subject,
                email,
                email_verified,
                raw_profile,
                updated_at
            )
            VALUES (
                :user_id,
                :provider,
                :provider_subject,
                :email,
                :email_verified,
                CAST(:raw_profile AS jsonb),
                now()
            )
            ON CONFLICT (provider, provider_subject)
            DO UPDATE SET
                email = EXCLUDED.email,
                email_verified = EXCLUDED.email_verified,
                raw_profile = EXCLUDED.raw_profile,
                updated_at = now();
            """
        ),
        {
            "user_id": str(user_id),
            "provider": provider,
            "provider_subject": provider_subject,
            "email": email,
            "email_verified": email_verified,
            "raw_profile": json.dumps(raw_profile),
        },
    )


def create_refresh_token(
    conn: Connection,
    *,
    user_id: UUID | str,
    token_hash: str,
    expires_at: datetime,
    token_family_id: UUID | str,
    session_id: UUID | str,
    parent_refresh_token_id: UUID | str | None,
    device_id_hash: str | None,
    issued_ip: str | None,
    user_agent_hash: str | None,
) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            INSERT INTO refresh_tokens (
                user_id,
                token_hash,
                expires_at,
                token_family_id,
                session_id,
                parent_refresh_token_id,
                device_id_hash,
                issued_ip,
                last_used_ip,
                user_agent_hash,
                last_used_at,
                created_at
            )
            VALUES (
                :user_id,
                :token_hash,
                :expires_at,
                :token_family_id,
                :session_id,
                :parent_refresh_token_id,
                :device_id_hash,
                CAST(:issued_ip AS inet),
                CAST(:issued_ip AS inet),
                :user_agent_hash,
                now(),
                now()
            )
            RETURNING refresh_token_id, user_id, token_family_id, session_id, expires_at;
            """
        ),
        {
            "user_id": str(user_id),
            "token_hash": token_hash,
            "expires_at": expires_at,
            "token_family_id": str(token_family_id),
            "session_id": str(session_id),
            "parent_refresh_token_id": str(parent_refresh_token_id) if parent_refresh_token_id else None,
            "device_id_hash": device_id_hash,
            "issued_ip": issued_ip,
            "user_agent_hash": user_agent_hash,
        },
    ).mappings().one()
    return dict(row)


def get_refresh_token_for_update(conn: Connection, token_hash: str) -> dict[str, Any] | None:
    row = conn.execute(
        text(
            """
            SELECT
                refresh_token_id,
                user_id,
                token_hash,
                expires_at,
                revoked_at,
                token_family_id,
                session_id,
                parent_refresh_token_id,
                replaced_by_refresh_token_id,
                reused_at,
                device_id_hash
            FROM refresh_tokens
            WHERE token_hash = :token_hash
            LIMIT 1
            FOR UPDATE;
            """
        ),
        {"token_hash": token_hash},
    ).mappings().first()
    return _dict(row)


def rotate_refresh_token(
    conn: Connection,
    *,
    old_refresh_token_id: UUID | str,
    replacement_refresh_token_id: UUID | str,
    replacement_token_hash: str,
    last_used_ip: str | None,
) -> None:
    conn.execute(
        text(
            """
            UPDATE refresh_tokens
            SET revoked_at = now(),
                revocation_reason = 'rotated',
                replaced_by_refresh_token_id = :replacement_refresh_token_id,
                replaced_by_token_hash = :replacement_token_hash,
                last_used_ip = CAST(:last_used_ip AS inet),
                last_used_at = now()
            WHERE refresh_token_id = :old_refresh_token_id;
            """
        ),
        {
            "old_refresh_token_id": str(old_refresh_token_id),
            "replacement_refresh_token_id": str(replacement_refresh_token_id),
            "replacement_token_hash": replacement_token_hash,
            "last_used_ip": last_used_ip,
        },
    )


def mark_refresh_reused_and_revoke_family(
    conn: Connection,
    *,
    refresh_token_id: UUID | str,
    token_family_id: UUID | str,
) -> None:
    conn.execute(
        text(
            """
            UPDATE refresh_tokens
            SET reused_at = COALESCE(reused_at, now())
            WHERE refresh_token_id = :refresh_token_id;
            """
        ),
        {"refresh_token_id": str(refresh_token_id)},
    )
    revoke_refresh_family(conn, token_family_id=token_family_id, reason="reuse_detected")


def revoke_refresh_family(conn: Connection, *, token_family_id: UUID | str, reason: str) -> None:
    conn.execute(
        text(
            """
            UPDATE refresh_tokens
            SET revoked_at = COALESCE(revoked_at, now()),
                revocation_reason = COALESCE(revocation_reason, :reason)
            WHERE token_family_id = :token_family_id;
            """
        ),
        {"token_family_id": str(token_family_id), "reason": reason},
    )


def revoke_refresh_session(conn: Connection, *, session_id: UUID | str, reason: str) -> None:
    conn.execute(
        text(
            """
            UPDATE refresh_tokens
            SET revoked_at = COALESCE(revoked_at, now()),
                revocation_reason = COALESCE(revocation_reason, :reason)
            WHERE session_id = :session_id;
            """
        ),
        {"session_id": str(session_id), "reason": reason},
    )


def revoke_all_refresh_tokens_for_user(conn: Connection, *, user_id: UUID | str, reason: str) -> None:
    conn.execute(
        text(
            """
            UPDATE refresh_tokens
            SET revoked_at = COALESCE(revoked_at, now()),
                revocation_reason = COALESCE(revocation_reason, :reason)
            WHERE user_id = :user_id;
            """
        ),
        {"user_id": str(user_id), "reason": reason},
    )

# ============================================================================
# Phase 2: password reset, FPO access, invitations, and email outbox worker
# ============================================================================


def invalidate_active_password_reset_sessions(
    conn: Connection,
    *,
    user_id: UUID | str,
) -> int:
    result = conn.execute(
        text(
            """
            UPDATE password_reset_sessions
            SET invalidated_at = now()
            WHERE user_id = :user_id
              AND used_at IS NULL
              AND invalidated_at IS NULL;
            """
        ),
        {"user_id": str(user_id)},
    )
    return int(result.rowcount or 0)


def create_password_reset_session(
    conn: Connection,
    *,
    user_id: UUID | str,
    token_hash: str,
    expires_at: datetime,
    requested_ip: str | None,
    device_id_hash: str | None,
    correlation_id: str,
) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            INSERT INTO password_reset_sessions (
                password_reset_session_id,
                user_id,
                token_hash,
                expires_at,
                requested_ip,
                device_id_hash,
                correlation_id,
                created_at
            )
            VALUES (
                gen_random_uuid(),
                :user_id,
                :token_hash,
                :expires_at,
                CAST(:requested_ip AS inet),
                :device_id_hash,
                :correlation_id,
                now()
            )
            RETURNING password_reset_session_id, user_id, expires_at, created_at;
            """
        ),
        {
            "user_id": str(user_id),
            "token_hash": token_hash,
            "expires_at": expires_at,
            "requested_ip": requested_ip,
            "device_id_hash": device_id_hash,
            "correlation_id": correlation_id,
        },
    ).mappings().one()
    return dict(row)


def get_password_reset_session_for_update(
    conn: Connection,
    *,
    token_hash: str,
) -> dict[str, Any] | None:
    row = conn.execute(
        text(
            """
            SELECT
                password_reset_session_id,
                user_id,
                token_hash,
                expires_at,
                used_at,
                invalidated_at,
                requested_ip,
                completed_ip,
                device_id_hash,
                correlation_id,
                created_at
            FROM password_reset_sessions
            WHERE token_hash = :token_hash
            LIMIT 1
            FOR UPDATE;
            """
        ),
        {"token_hash": token_hash},
    ).mappings().first()
    return _dict(row)


def mark_password_reset_used(
    conn: Connection,
    *,
    password_reset_session_id: UUID | str,
    completed_ip: str | None,
) -> None:
    conn.execute(
        text(
            """
            UPDATE password_reset_sessions
            SET used_at = now(),
                completed_ip = CAST(:completed_ip AS inet)
            WHERE password_reset_session_id = :password_reset_session_id;
            """
        ),
        {
            "password_reset_session_id": str(password_reset_session_id),
            "completed_ip": completed_ip,
        },
    )


def create_fpo_access_request(
    conn: Connection,
    *,
    organisation_name: str,
    registration_number: str | None,
    contact_person_name: str,
    contact_email: str,
    contact_phone: str,
    state_name: str | None,
    district_name: str | None,
    message: str | None,
    created_ip: str | None,
    device_id_hash: str | None,
    correlation_id: str,
) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            INSERT INTO fpo_access_requests (
                request_id,
                organisation_name,
                registration_number,
                contact_person_name,
                contact_email,
                contact_phone,
                state_name,
                district_name,
                message,
                status,
                created_ip,
                device_id_hash,
                correlation_id,
                created_at,
                updated_at
            )
            VALUES (
                gen_random_uuid(),
                :organisation_name,
                :registration_number,
                :contact_person_name,
                :contact_email,
                :contact_phone,
                :state_name,
                :district_name,
                :message,
                'pending',
                CAST(:created_ip AS inet),
                :device_id_hash,
                :correlation_id,
                now(),
                now()
            )
            RETURNING
                request_id,
                organisation_name,
                registration_number,
                contact_person_name,
                contact_email,
                contact_phone,
                state_name,
                district_name,
                message,
                status,
                reviewed_by,
                reviewed_at,
                review_note,
                created_at,
                updated_at;
            """
        ),
        {
            "organisation_name": organisation_name,
            "registration_number": registration_number,
            "contact_person_name": contact_person_name,
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "state_name": state_name,
            "district_name": district_name,
            "message": message,
            "created_ip": created_ip,
            "device_id_hash": device_id_hash,
            "correlation_id": correlation_id,
        },
    ).mappings().one()
    return dict(row)


def list_fpo_access_requests(
    conn: Connection,
    *,
    status_filter: str | None,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            SELECT
                request_id,
                organisation_name,
                registration_number,
                contact_person_name,
                contact_email,
                contact_phone,
                state_name,
                district_name,
                message,
                status,
                reviewed_by,
                reviewed_at,
                review_note,
                created_at,
                updated_at
            FROM fpo_access_requests
            WHERE (:status_filter IS NULL OR status = :status_filter)
            ORDER BY created_at DESC
            LIMIT :limit
            OFFSET :offset;
            """
        ),
        {"status_filter": status_filter, "limit": limit, "offset": offset},
    ).mappings().all()
    return [dict(row) for row in rows]


def count_fpo_access_requests(conn: Connection, *, status_filter: str | None) -> int:
    value = conn.execute(
        text(
            """
            SELECT count(*)
            FROM fpo_access_requests
            WHERE (:status_filter IS NULL OR status = :status_filter);
            """
        ),
        {"status_filter": status_filter},
    ).scalar_one()
    return int(value)


def get_fpo_access_request_for_update(
    conn: Connection,
    *,
    request_id: UUID | str,
) -> dict[str, Any] | None:
    row = conn.execute(
        text(
            """
            SELECT
                request_id,
                organisation_name,
                registration_number,
                contact_person_name,
                contact_email,
                contact_phone,
                state_name,
                district_name,
                message,
                status,
                reviewed_by,
                reviewed_at,
                review_note,
                created_at,
                updated_at
            FROM fpo_access_requests
            WHERE request_id = :request_id
            LIMIT 1
            FOR UPDATE;
            """
        ),
        {"request_id": str(request_id)},
    ).mappings().first()
    return _dict(row)


def review_fpo_access_request(
    conn: Connection,
    *,
    request_id: UUID | str,
    status: str,
    review_note: str | None,
    reviewed_by: UUID | str,
) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            UPDATE fpo_access_requests
            SET status = :status,
                review_note = :review_note,
                reviewed_by = :reviewed_by,
                reviewed_at = now(),
                updated_at = now()
            WHERE request_id = :request_id
            RETURNING
                request_id,
                organisation_name,
                registration_number,
                contact_person_name,
                contact_email,
                contact_phone,
                state_name,
                district_name,
                message,
                status,
                reviewed_by,
                reviewed_at,
                review_note,
                created_at,
                updated_at;
            """
        ),
        {
            "request_id": str(request_id),
            "status": status,
            "review_note": review_note,
            "reviewed_by": str(reviewed_by),
        },
    ).mappings().one()
    return dict(row)


def invalidate_active_invitations(
    conn: Connection,
    *,
    email: str,
    role: str,
) -> int:
    result = conn.execute(
        text(
            """
            UPDATE account_invitations
            SET revoked_at = now(),
                updated_at = now()
            WHERE lower(email) = lower(:email)
              AND role = :role
              AND accepted_at IS NULL
              AND revoked_at IS NULL;
            """
        ),
        {"email": email, "role": role},
    )
    return int(result.rowcount or 0)


def create_account_invitation(
    conn: Connection,
    *,
    email: str,
    role: str,
    token_hash: str,
    invited_by: UUID | str,
    expires_at: datetime,
    metadata: dict[str, Any],
    created_ip: str | None,
    device_id_hash: str | None,
    correlation_id: str,
) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            INSERT INTO account_invitations (
                invitation_id,
                email,
                role,
                token_hash,
                invited_by,
                expires_at,
                metadata,
                created_ip,
                device_id_hash,
                correlation_id,
                created_at,
                updated_at
            )
            VALUES (
                gen_random_uuid(),
                :email,
                :role,
                :token_hash,
                :invited_by,
                :expires_at,
                CAST(:metadata AS jsonb),
                CAST(:created_ip AS inet),
                :device_id_hash,
                :correlation_id,
                now(),
                now()
            )
            RETURNING invitation_id, email, role, invited_by, expires_at, created_at;
            """
        ),
        {
            "email": email,
            "role": role,
            "token_hash": token_hash,
            "invited_by": str(invited_by),
            "expires_at": expires_at,
            "metadata": json.dumps(metadata),
            "created_ip": created_ip,
            "device_id_hash": device_id_hash,
            "correlation_id": correlation_id,
        },
    ).mappings().one()
    return dict(row)


def get_account_invitation_by_hash(
    conn: Connection,
    *,
    token_hash: str,
    for_update: bool = False,
) -> dict[str, Any] | None:
    lock = " FOR UPDATE" if for_update else ""
    row = conn.execute(
        text(
            f"""
            SELECT
                invitation_id,
                email,
                role,
                token_hash,
                invited_by,
                expires_at,
                accepted_at,
                revoked_at,
                accepted_by_user_id,
                metadata,
                created_at,
                updated_at
            FROM account_invitations
            WHERE token_hash = :token_hash
            LIMIT 1{lock};
            """
        ),
        {"token_hash": token_hash},
    ).mappings().first()
    return _dict(row)


def mark_account_invitation_accepted(
    conn: Connection,
    *,
    invitation_id: UUID | str,
    accepted_by_user_id: UUID | str,
    accepted_ip: str | None,
) -> None:
    conn.execute(
        text(
            """
            UPDATE account_invitations
            SET accepted_at = now(),
                accepted_by_user_id = :accepted_by_user_id,
                accepted_ip = CAST(:accepted_ip AS inet),
                updated_at = now()
            WHERE invitation_id = :invitation_id;
            """
        ),
        {
            "invitation_id": str(invitation_id),
            "accepted_by_user_id": str(accepted_by_user_id),
            "accepted_ip": accepted_ip,
        },
    )


def claim_email_outbox_batch(
    conn: Connection,
    *,
    worker_id: str,
    batch_size: int,
    lock_timeout_seconds: int,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            WITH candidates AS (
                SELECT email_outbox_id
                FROM email_outbox
                WHERE (
                    status IN ('queued', 'failed')
                    AND COALESCE(next_attempt_at, created_at, now()) <= now()
                ) OR (
                    status = 'sending'
                    AND locked_at < now() - (:lock_timeout_seconds * interval '1 second')
                )
                ORDER BY COALESCE(next_attempt_at, created_at, now()), created_at
                FOR UPDATE SKIP LOCKED
                LIMIT :batch_size
            )
            UPDATE email_outbox AS e
            SET status = 'sending',
                locked_at = now(),
                locked_by = :worker_id,
                attempts = COALESCE(e.attempts, 0) + 1,
                last_attempt_at = now(),
                updated_at = now()
            FROM candidates c
            WHERE e.email_outbox_id = c.email_outbox_id
            RETURNING
                e.email_outbox_id,
                e.to_email,
                e.to_name,
                e.subject,
                e.template_key,
                e.provider,
                e.status,
                e.encrypted_payload,
                e.attempts,
                e.metadata,
                e.created_at;
            """
        ),
        {
            "worker_id": worker_id,
            "batch_size": batch_size,
            "lock_timeout_seconds": lock_timeout_seconds,
        },
    ).mappings().all()
    return [dict(row) for row in rows]


def mark_email_outbox_sent(
    conn: Connection,
    *,
    email_outbox_id: UUID | str,
    provider_request_id: str | None,
    provider_status_code: int,
) -> None:
    conn.execute(
        text(
            """
            UPDATE email_outbox
            SET status = 'sent',
                provider_request_id = :provider_request_id,
                provider_status_code = :provider_status_code,
                sent_at = now(),
                failed_at = NULL,
                last_error_code = NULL,
                last_error_message = NULL,
                locked_at = NULL,
                locked_by = NULL,
                next_attempt_at = NULL,
                updated_at = now()
            WHERE email_outbox_id = :email_outbox_id;
            """
        ),
        {
            "email_outbox_id": str(email_outbox_id),
            "provider_request_id": provider_request_id,
            "provider_status_code": provider_status_code,
        },
    )


def mark_email_outbox_failed(
    conn: Connection,
    *,
    email_outbox_id: UUID | str,
    error_code: str,
    error_message: str,
    provider_status_code: int | None,
    dead: bool,
    retry_after_seconds: int,
) -> None:
    conn.execute(
        text(
            """
            UPDATE email_outbox
            SET status = CASE WHEN :dead THEN 'dead' ELSE 'failed' END,
                failed_at = CASE WHEN :dead THEN now() ELSE failed_at END,
                last_error_code = :error_code,
                last_error_message = :error_message,
                provider_status_code = :provider_status_code,
                next_attempt_at = CASE
                    WHEN :dead THEN NULL
                    ELSE now() + (:retry_after_seconds * interval '1 second')
                END,
                locked_at = NULL,
                locked_by = NULL,
                updated_at = now()
            WHERE email_outbox_id = :email_outbox_id;
            """
        ),
        {
            "email_outbox_id": str(email_outbox_id),
            "error_code": error_code,
            "error_message": error_message[:2000],
            "provider_status_code": provider_status_code,
            "dead": dead,
            "retry_after_seconds": retry_after_seconds,
        },
    )