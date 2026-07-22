from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from shared.db.postgres import engine

class AuthRepositoryError(RuntimeError):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_identifier(identifier: str) -> str:
    return identifier.strip()


def create_user(data: dict[str, Any]) -> dict[str, Any]:
    query = text(
        """
        INSERT INTO users (
            full_name,
            email,
            phone_number,
            password_hash,
            role,
            is_active,
            is_verified
        )
        VALUES (
            :full_name,
            :email,
            :phone_number,
            :password_hash,
            :role,
            TRUE,
            TRUE
        )
        RETURNING
            user_id,
            full_name,
            email,
            phone_number,
            role,
            is_active,
            is_verified;
        """
    )

    payload = {
        "full_name": " ".join(data["full_name"].strip().split()),
        "email": normalize_email(data["email"]),
        "phone_number": data.get("phone_number"),
        "password_hash": data["password_hash"],
        "role": data["role"],
    }

    try:
        with engine.begin() as conn:
            row = conn.execute(query, payload).mappings().one()
    except IntegrityError as exc:
        raise AuthRepositoryError("User already exists with this email or phone number") from exc
    except SQLAlchemyError as exc:
        raise AuthRepositoryError(f"Failed to create user: {exc}") from exc

    return dict(row)


def create_signup_session(data: dict[str, Any], otp_hash: str, otp_expires_at: datetime) -> dict[str, Any]:
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
        RETURNING signup_session_id;
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


def mark_signup_session_verified(signup_session_id: UUID | str) -> None:
    query = text(
        "UPDATE signup_otp_sessions SET verified_at = now() WHERE signup_session_id = :signup_session_id;"
    )
    with engine.begin() as conn:
        conn.execute(query, {"signup_session_id": str(signup_session_id)})


def mark_signup_session_completed(signup_session_id: UUID | str) -> None:
    query = text(
        "UPDATE signup_otp_sessions SET completed_at = now() WHERE signup_session_id = :signup_session_id;"
    )
    with engine.begin() as conn:
        conn.execute(query, {"signup_session_id": str(signup_session_id)})


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
            existing = conn.execute(
                exists_query,
                {"user_id": str(user["user_id"])},
            ).mappings().first()

            if existing is None:
                conn.execute(
                    insert_query,
                    {
                        "user_id": str(user["user_id"]),
                        "full_name": user["full_name"],
                        "phone_number": user.get("phone_number"),
                    },
                )
    except SQLAlchemyError as exc:
        raise AuthRepositoryError(
            f"Failed to provision farmer profile for user: {exc}"
        ) from exc


def get_user_by_identifier(identifier: str) -> dict[str, Any] | None:
    cleaned = normalize_identifier(identifier)

    query = text(
        """
        SELECT
            user_id,
            full_name,
            email,
            phone_number,
            password_hash,
            role,
            is_active,
            is_verified
        FROM users
        WHERE lower(email) = lower(:identifier)
           OR phone_number = :identifier
        LIMIT 1;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query, {"identifier": cleaned}).mappings().first()

    return dict(row) if row else None


def get_user_by_id(user_id: UUID | str) -> dict[str, Any] | None:
    query = text(
        """
        SELECT
            user_id,
            full_name,
            email,
            phone_number,
            role,
            is_active,
            is_verified
        FROM users
        WHERE user_id = :user_id
        LIMIT 1;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query, {"user_id": str(user_id)}).mappings().first()

    return dict(row) if row else None


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
        SELECT
            refresh_token_id,
            user_id,
            token_hash,
            expires_at,
            revoked_at
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


def revoke_refresh_token(token_hash: str) -> None:
    query = text(
        """
        UPDATE refresh_tokens
        SET revoked_at = now()
        WHERE token_hash = :token_hash
          AND revoked_at IS NULL;
        """
    )

    with engine.begin() as conn:
        conn.execute(query, {"token_hash": token_hash})


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

def record_failed_otp_attempt(
    signup_session_id: UUID | str,
    max_attempts: int,
) -> None:
    query = text("""
        UPDATE signup_otp_sessions
        SET
            attempts = attempts + 1,
            last_attempt_at = now(),
            locked_at = CASE
                WHEN attempts + 1 >= :max_attempts THEN now()
                ELSE locked_at
            END
        WHERE signup_session_id = :signup_session_id
          AND verified_at IS NULL
          AND completed_at IS NULL;
    """)

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "signup_session_id": str(signup_session_id),
                "max_attempts": max_attempts,
            },
        )