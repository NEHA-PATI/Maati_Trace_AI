# from __future__ import annotations

# from datetime import datetime
# from typing import Any
# from uuid import UUID

# from sqlalchemy import text
# from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# from shared.db.postgres import engine

# class AuthRepositoryError(RuntimeError):
#     pass


# def normalize_email(email: str) -> str:
#     return email.strip().lower()


# def normalize_identifier(identifier: str) -> str:
#     return identifier.strip()


# def create_user(data: dict[str, Any]) -> dict[str, Any]:
#     query = text(
#         """
#         INSERT INTO users (
#             full_name,
#             email,
#             phone_number,
#             password_hash,
#             role,
#             is_active,
#             is_verified
#         )
#         VALUES (
#             :full_name,
#             :email,
#             :phone_number,
#             :password_hash,
#             :role,
#             TRUE,
#             TRUE
#         )
#         RETURNING
#             user_id,
#             full_name,
#             email,
#             phone_number,
#             role,
#             is_active,
#             is_verified;
#         """
#     )

#     payload = {
#         "full_name": " ".join(data["full_name"].strip().split()),
#         "email": normalize_email(data["email"]),
#         "phone_number": data.get("phone_number"),
#         "password_hash": data["password_hash"],
#         "role": data["role"],
#     }

#     try:
#         with engine.begin() as conn:
#             row = conn.execute(query, payload).mappings().one()
#     except IntegrityError as exc:
#         raise AuthRepositoryError("User already exists with this email or phone number") from exc
#     except SQLAlchemyError as exc:
#         raise AuthRepositoryError(f"Failed to create user: {exc}") from exc

#     return dict(row)


# def create_signup_session(data: dict[str, Any], otp_hash: str, otp_expires_at: datetime) -> dict[str, Any]:
#     query = text(
#         """
#         INSERT INTO signup_otp_sessions (
#             full_name,
#             phone_number,
#             email,
#             password_hash,
#             role,
#             fpo_id,
#             invite_code,
#             otp_hash,
#             otp_expires_at
#         )
#         VALUES (
#             :full_name,
#             :phone_number,
#             :email,
#             :password_hash,
#             :role,
#             :fpo_id,
#             :invite_code,
#             :otp_hash,
#             :otp_expires_at
#         )
#         RETURNING signup_session_id;
#         """
#     )

#     try:
#         with engine.begin() as conn:
#             row = conn.execute(
#                 query,
#                 {**data, "otp_hash": otp_hash, "otp_expires_at": otp_expires_at},
#             ).mappings().one()
#     except SQLAlchemyError as exc:
#         raise AuthRepositoryError(f"Failed to create signup session: {exc}") from exc

#     return dict(row)


# def get_signup_session(signup_session_id: UUID | str) -> dict[str, Any] | None:
#     query = text(
#         """
#         SELECT *
#         FROM signup_otp_sessions
#         WHERE signup_session_id = :signup_session_id
#         LIMIT 1;
#         """
#     )
#     with engine.connect() as conn:
#         row = conn.execute(query, {"signup_session_id": str(signup_session_id)}).mappings().first()
#     return dict(row) if row else None


# def mark_signup_session_verified(signup_session_id: UUID | str) -> None:
#     query = text(
#         "UPDATE signup_otp_sessions SET verified_at = now() WHERE signup_session_id = :signup_session_id;"
#     )
#     with engine.begin() as conn:
#         conn.execute(query, {"signup_session_id": str(signup_session_id)})


# def mark_signup_session_completed(signup_session_id: UUID | str) -> None:
#     query = text(
#         "UPDATE signup_otp_sessions SET completed_at = now() WHERE signup_session_id = :signup_session_id;"
#     )
#     with engine.begin() as conn:
#         conn.execute(query, {"signup_session_id": str(signup_session_id)})


# def ensure_farmer_profile_for_user(user: dict[str, Any]) -> None:
#     exists_query = text(
#         """
#         SELECT farmer_id
#         FROM farmer_profiles
#         WHERE user_id = :user_id
#         LIMIT 1;
#         """
#     )

#     insert_query = text(
#         """
#         INSERT INTO farmer_profiles (
#             user_id,
#             fpo_id,
#             full_name,
#             phone_number,
#             gender,
#             state_name,
#             district_name,
#             district_code,
#             block_name,
#             block_code,
#             village_name,
#             is_active
#         )
#         VALUES (
#             :user_id,
#             NULL,
#             :full_name,
#             :phone_number,
#             NULL,
#             'Odisha',
#             'Unassigned',
#             NULL,
#             NULL,
#             NULL,
#             NULL,
#             TRUE
#         );
#         """
#     )

#     try:
#         with engine.begin() as conn:
#             existing = conn.execute(
#                 exists_query,
#                 {"user_id": str(user["user_id"])},
#             ).mappings().first()

#             if existing is None:
#                 conn.execute(
#                     insert_query,
#                     {
#                         "user_id": str(user["user_id"]),
#                         "full_name": user["full_name"],
#                         "phone_number": user.get("phone_number"),
#                     },
#                 )
#     except SQLAlchemyError as exc:
#         raise AuthRepositoryError(
#             f"Failed to provision farmer profile for user: {exc}"
#         ) from exc


# def get_user_by_identifier(identifier: str) -> dict[str, Any] | None:
#     cleaned = normalize_identifier(identifier)

#     query = text(
#         """
#         SELECT
#             user_id,
#             full_name,
#             email,
#             phone_number,
#             password_hash,
#             role,
#             is_active,
#             is_verified
#         FROM users
#         WHERE lower(email) = lower(:identifier)
#            OR phone_number = :identifier
#         LIMIT 1;
#         """
#     )

#     with engine.connect() as conn:
#         row = conn.execute(query, {"identifier": cleaned}).mappings().first()

#     return dict(row) if row else None


# def get_user_by_id(user_id: UUID | str) -> dict[str, Any] | None:
#     query = text(
#         """
#         SELECT
#             user_id,
#             full_name,
#             email,
#             phone_number,
#             role,
#             is_active,
#             is_verified
#         FROM users
#         WHERE user_id = :user_id
#         LIMIT 1;
#         """
#     )

#     with engine.connect() as conn:
#         row = conn.execute(query, {"user_id": str(user_id)}).mappings().first()

#     return dict(row) if row else None


# def create_refresh_token(
#     user_id: UUID | str,
#     token_hash: str,
#     expires_at: datetime,
# ) -> None:
#     query = text(
#         """
#         INSERT INTO refresh_tokens (
#             user_id,
#             token_hash,
#             expires_at
#         )
#         VALUES (
#             :user_id,
#             :token_hash,
#             :expires_at
#         );
#         """
#     )

#     try:
#         with engine.begin() as conn:
#             conn.execute(
#                 query,
#                 {
#                     "user_id": str(user_id),
#                     "token_hash": token_hash,
#                     "expires_at": expires_at,
#                 },
#             )
#     except SQLAlchemyError as exc:
#         raise AuthRepositoryError(f"Failed to create refresh token: {exc}") from exc


# def get_active_refresh_token(token_hash: str) -> dict[str, Any] | None:
#     query = text(
#         """
#         SELECT
#             refresh_token_id,
#             user_id,
#             token_hash,
#             expires_at,
#             revoked_at
#         FROM refresh_tokens
#         WHERE token_hash = :token_hash
#           AND revoked_at IS NULL
#           AND expires_at > now()
#         LIMIT 1;
#         """
#     )

#     with engine.connect() as conn:
#         row = conn.execute(query, {"token_hash": token_hash}).mappings().first()

#     return dict(row) if row else None


# def revoke_refresh_token(token_hash: str) -> None:
#     query = text(
#         """
#         UPDATE refresh_tokens
#         SET revoked_at = now()
#         WHERE token_hash = :token_hash
#           AND revoked_at IS NULL;
#         """
#     )

#     with engine.begin() as conn:
#         conn.execute(query, {"token_hash": token_hash})


# def revoke_all_refresh_tokens_for_user(user_id: UUID | str) -> None:
#     query = text(
#         """
#         UPDATE refresh_tokens
#         SET revoked_at = now()
#         WHERE user_id = :user_id
#           AND revoked_at IS NULL;
#         """
#     )

#     with engine.begin() as conn:
#         conn.execute(query, {"user_id": str(user_id)})

# def record_failed_otp_attempt(
#     signup_session_id: UUID | str,
#     max_attempts: int,
# ) -> None:
#     query = text("""
#         UPDATE signup_otp_sessions
#         SET
#             attempts = attempts + 1,
#             last_attempt_at = now(),
#             locked_at = CASE
#                 WHEN attempts + 1 >= :max_attempts THEN now()
#                 ELSE locked_at
#             END
#         WHERE signup_session_id = :signup_session_id
#           AND verified_at IS NULL
#           AND completed_at IS NULL;
#     """)

#     with engine.begin() as connection:
#         connection.execute(
#             query,
#             {
#                 "signup_session_id": str(signup_session_id),
#                 "max_attempts": max_attempts,
#             },
#         )





























from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from shared.db.postgres import engine


class AuthRepositoryError(RuntimeError):
    pass


USER_COLUMNS = """
    user_id,
    full_name,
    email,
    phone_number,
    password_hash,
    role,
    is_active,
    COALESCE(is_verified, is_email_verified, FALSE) AS is_verified,
    onboarding_status,
    profile_image_url
"""


def normalize_email(email: str | None) -> str | None:
    if email is None:
        return None
    cleaned = str(email).strip().lower()
    return cleaned or None


def normalize_identifier(identifier: str) -> str:
    return str(identifier or "").strip()


def get_user_by_identifier(identifier: str) -> dict[str, Any] | None:
    cleaned = normalize_identifier(identifier)
    query = text(
        f"""
        SELECT {USER_COLUMNS}
        FROM users
        WHERE lower(email) = lower(:identifier)
           OR phone_number = :identifier
        LIMIT 1;
        """
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"identifier": cleaned}).mappings().first()
    return dict(row) if row else None


def get_user_by_email(email: str) -> dict[str, Any] | None:
    query = text(f"SELECT {USER_COLUMNS} FROM users WHERE lower(email) = lower(:email) LIMIT 1;")
    with engine.connect() as conn:
        row = conn.execute(query, {"email": normalize_email(email)}).mappings().first()
    return dict(row) if row else None


def get_user_by_id(user_id: UUID | str) -> dict[str, Any] | None:
    query = text(f"SELECT {USER_COLUMNS} FROM users WHERE user_id = :user_id LIMIT 1;")
    with engine.connect() as conn:
        row = conn.execute(query, {"user_id": str(user_id)}).mappings().first()
    return dict(row) if row else None


def create_user(data: dict[str, Any]) -> dict[str, Any]:
    query = text(
        f"""
        INSERT INTO users (
            full_name,
            email,
            phone_number,
            password_hash,
            role,
            is_active,
            is_verified,
            is_email_verified,
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
            :is_email_verified,
            :onboarding_status,
            :profile_image_url,
            now()
        )
        RETURNING {USER_COLUMNS};
        """
    )
    payload = {
        "full_name": " ".join(str(data["full_name"]).strip().split()),
        "email": normalize_email(data.get("email")),
        "phone_number": data.get("phone_number"),
        "password_hash": data.get("password_hash"),
        "role": data["role"],
        "is_verified": bool(data.get("is_verified", False)),
        "is_email_verified": bool(data.get("is_email_verified", False)),
        "onboarding_status": data.get("onboarding_status") or "pending",
        "profile_image_url": data.get("profile_image_url"),
    }
    try:
        with engine.begin() as conn:
            row = conn.execute(query, payload).mappings().one()
    except IntegrityError as exc:
        raise AuthRepositoryError("User already exists with this email or phone number") from exc
    except SQLAlchemyError as exc:
        raise AuthRepositoryError(f"Failed to create user: {exc}") from exc
    return dict(row)


def mark_user_login(user_id: UUID | str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE users SET last_login_at = now(), updated_at = now() WHERE user_id = :user_id;"),
            {"user_id": str(user_id)},
        )


def ensure_farmer_profile_for_user(user: dict[str, Any]) -> None:
    exists_query = text(
        """
        SELECT farmer_id
        FROM farmer_profiles
        WHERE user_id = :user_id
        LIMIT 1;
        """
    )
    insert_query = text(
        """
        INSERT INTO farmer_profiles (
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
            :user_id,
            NULL,
            :full_name,
            :phone_number,
            NULL,
            'Odisha',
            'Unassigned',
            NULL,
            NULL,
            NULL,
            NULL,
            TRUE
        );
        """
    )
    try:
        with engine.begin() as conn:
            existing = conn.execute(exists_query, {"user_id": str(user["user_id"])}).mappings().first()
            if existing is None:
                conn.execute(
                    insert_query,
                    {
                        "user_id": str(user["user_id"]),
                        "full_name": user.get("full_name") or user.get("email") or "Farmer",
                        "phone_number": user.get("phone_number"),
                    },
                )
    except SQLAlchemyError as exc:
        raise AuthRepositoryError(f"Failed to provision farmer profile for user: {exc}") from exc


def create_signup_session(
    data: dict[str, Any],
    otp_hash: str,
    otp_expires_at: datetime,
) -> dict[str, Any]:
    query = text(
        """
        INSERT INTO signup_otp_sessions (
            full_name,
            phone_number,
            email,
            password_hash,
            role,
            fpo_id,
            invite_code,
            otp_hash,
            otp_expires_at
        )
        VALUES (
            :full_name,
            :phone_number,
            :email,
            :password_hash,
            :role,
            :fpo_id,
            :invite_code,
            :otp_hash,
            :otp_expires_at
        )
        RETURNING signup_session_id, otp_expires_at;
        """
    )
    try:
        with engine.begin() as conn:
            row = conn.execute(
                query,
                {**data, "otp_hash": otp_hash, "otp_expires_at": otp_expires_at},
            ).mappings().one()
    except SQLAlchemyError as exc:
        raise AuthRepositoryError(f"Failed to create signup session: {exc}") from exc
    return dict(row)


def get_signup_session(signup_session_id: UUID | str) -> dict[str, Any] | None:
    query = text(
        """
        SELECT *
        FROM signup_otp_sessions
        WHERE signup_session_id = :signup_session_id
        LIMIT 1;
        """
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"signup_session_id": str(signup_session_id)}).mappings().first()
    return dict(row) if row else None


def increment_signup_attempts(signup_session_id: UUID | str, *, lock: bool) -> None:
    query = text(
        """
        UPDATE signup_otp_sessions
        SET attempts = COALESCE(attempts, 0) + 1,
            last_attempt_at = now(),
            locked_at = CASE WHEN :lock THEN now() ELSE locked_at END
        WHERE signup_session_id = :signup_session_id;
        """
    )
    with engine.begin() as conn:
        conn.execute(query, {"signup_session_id": str(signup_session_id), "lock": lock})


def mark_signup_session_verified(signup_session_id: UUID | str) -> None:
    query = text(
        """
        UPDATE signup_otp_sessions
        SET verified_at = now()
        WHERE signup_session_id = :signup_session_id;
        """
    )
    with engine.begin() as conn:
        conn.execute(query, {"signup_session_id": str(signup_session_id)})


def mark_signup_session_completed(signup_session_id: UUID | str) -> None:
    query = text(
        """
        UPDATE signup_otp_sessions
        SET completed_at = now()
        WHERE signup_session_id = :signup_session_id;
        """
    )
    with engine.begin() as conn:
        conn.execute(query, {"signup_session_id": str(signup_session_id)})


def get_auth_identity(provider: str, provider_subject: str) -> dict[str, Any] | None:
    query = text(
        f"""
        SELECT
            ai.auth_identity_id,
            ai.user_id,
            ai.provider,
            ai.provider_subject,
            ai.email AS provider_email,
            {USER_COLUMNS}
        FROM auth_identities ai
        JOIN users u ON u.user_id = ai.user_id
        WHERE ai.provider = :provider
          AND ai.provider_subject = :provider_subject
        LIMIT 1;
        """
    )
    with engine.connect() as conn:
        row = conn.execute(
            query,
            {"provider": provider, "provider_subject": provider_subject},
        ).mappings().first()
    return dict(row) if row else None


def link_auth_identity(
    *,
    user_id: UUID | str,
    provider: str,
    provider_subject: str,
    email: str | None,
    email_verified: bool,
    raw_profile: dict[str, Any],
) -> None:
    query = text(
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
        ON CONFLICT(provider, provider_subject)
        DO UPDATE SET
            email = EXCLUDED.email,
            email_verified = EXCLUDED.email_verified,
            raw_profile = EXCLUDED.raw_profile,
            updated_at = now();
        """
    )
    try:
        with engine.begin() as conn:
            conn.execute(
                query,
                {
                    "user_id": str(user_id),
                    "provider": provider,
                    "provider_subject": provider_subject,
                    "email": normalize_email(email),
                    "email_verified": bool(email_verified),
                    "raw_profile": json.dumps(raw_profile),
                },
            )
    except SQLAlchemyError as exc:
        raise AuthRepositoryError("Could not link auth identity") from exc


def create_refresh_token(
    user_id: UUID | str,
    token_hash: str,
    expires_at: datetime,
) -> None:
    query = text(
        """
        INSERT INTO refresh_tokens (
            user_id,
            token_hash,
            expires_at
        )
        VALUES (
            :user_id,
            :token_hash,
            :expires_at
        );
        """
    )
    try:
        with engine.begin() as conn:
            conn.execute(
                query,
                {
                    "user_id": str(user_id),
                    "token_hash": token_hash,
                    "expires_at": expires_at,
                },
            )
    except SQLAlchemyError as exc:
        raise AuthRepositoryError(f"Failed to create refresh token: {exc}") from exc


def get_active_refresh_token(token_hash: str) -> dict[str, Any] | None:
    query = text(
        """
        SELECT refresh_token_id, user_id, token_hash, expires_at, revoked_at
        FROM refresh_tokens
        WHERE token_hash = :token_hash
          AND revoked_at IS NULL
          AND expires_at > now()
        LIMIT 1;
        """
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"token_hash": token_hash}).mappings().first()
    return dict(row) if row else None


def revoke_refresh_token(token_hash: str, replaced_by_token_hash: str | None = None) -> None:
    query = text(
        """
        UPDATE refresh_tokens
        SET revoked_at = now(),
            replaced_by_token_hash = COALESCE(:replaced_by_token_hash, replaced_by_token_hash)
        WHERE token_hash = :token_hash
          AND revoked_at IS NULL;
        """
    )
    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "token_hash": token_hash,
                "replaced_by_token_hash": replaced_by_token_hash,
            },
        )


def revoke_all_refresh_tokens_for_user(user_id: UUID | str) -> None:
    query = text(
        """
        UPDATE refresh_tokens
        SET revoked_at = now()
        WHERE user_id = :user_id
          AND revoked_at IS NULL;
        """
    )
    with engine.begin() as conn:
        conn.execute(query, {"user_id": str(user_id)})