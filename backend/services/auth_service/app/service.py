from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import os
import secrets

from services.auth_service.app.repository import (
    AuthRepositoryError,
    create_refresh_token,
    create_user,
    create_signup_session,
    ensure_farmer_profile_for_user,
    get_active_refresh_token,
    get_user_by_id,
    get_user_by_identifier,
    get_signup_session,
    mark_signup_session_completed,
    mark_signup_session_verified,
    revoke_refresh_token,
    record_failed_otp_attempt,
)
from services.auth_service.app.schemas import (
    FarmerProfileUpdateRequest,
    FpoProfileUpdateRequest,
    LoginRequest,
    SignupCompleteRequest,
    SignupRequest,
    SignupStartRequest,
    SignupVerifyRequest,
)
from shared.config.settings import settings
from services.auth_service.app.security import (
    create_access_token,
    create_refresh_token_plain,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)

from services.auth_service.app.mail import (
    MailServiceError,
    send_signup_otp_email,
)


class AuthServiceError(RuntimeError):
    pass


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_id": user["user_id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "phone_number": user.get("phone_number"),
        "role": user["role"],
        "is_active": user["is_active"],
        "is_verified": user["is_verified"],
    }


def _issue_tokens(user: dict[str, Any]) -> dict[str, Any]:
    access_token = create_access_token(user)

    refresh_token_plain = create_refresh_token_plain()
    refresh_token_hash = hash_refresh_token(refresh_token_plain)

    create_refresh_token(
        user_id=user["user_id"],
        token_hash=refresh_token_hash,
        expires_at=refresh_token_expiry(),
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_plain,
        "token_type": "bearer",
        "user": _public_user(user),
    }


def signup(payload: SignupRequest) -> dict[str, Any]:
    try:
        user = create_user(
            {
                "full_name": payload.full_name,
                "email": str(payload.email),
                "phone_number": payload.phone_number,
                "password_hash": hash_password(payload.password),
                "role": payload.role,
            }
        )
        if payload.role == "farmer":
            ensure_farmer_profile_for_user(user)
    except AuthRepositoryError as exc:
        raise AuthServiceError(str(exc)) from exc

    return _issue_tokens(user)


def start_signup(payload: SignupStartRequest) -> dict[str, Any]:
    if payload.role != "farmer":
        raise AuthServiceError(
            "Public signup currently supports farmer accounts only"
        )

    if not payload.consent_terms:
        raise AuthServiceError("Terms consent is required")

    if not payload.email:
        raise AuthServiceError(
            "Email is required for OTP verification"
        )

    email = str(payload.email).strip().lower()

    if get_user_by_identifier(email):
        raise AuthServiceError(
            "An account already exists with this email"
        )

    if get_user_by_identifier(payload.phone_number):
        raise AuthServiceError(
            "An account already exists with this phone number"
        )

    otp = f"{secrets.randbelow(900000) + 100000}"

    session = create_signup_session(
        {
            "full_name": payload.full_name,
            "phone_number": payload.phone_number,
            "email": email,
            "password_hash": hash_password(payload.password),
            "role": "farmer",
            "fpo_id": payload.fpo_id,
            "invite_code": payload.invite_code,
        },
        otp_hash=hash_password(otp),
        otp_expires_at=(
            datetime.now(timezone.utc)
            + timedelta(minutes=settings.signup_otp_expire_minutes)
        ),
    )

    try:
        send_signup_otp_email(
            to_email=email,
            full_name=payload.full_name,
            otp=otp,
        )
    except MailServiceError as exc:
        raise AuthServiceError(str(exc)) from exc

    response = {
        "signup_session_id": session["signup_session_id"],
    }

    if (
        settings.app_env == "local"
        and settings.mail_provider == "console"
    ):
        response["dev_otp"] = otp

    return response


def verify_signup_otp(
    payload: SignupVerifyRequest,
) -> dict[str, Any]:
    session = get_signup_session(payload.signup_session_id)

    if session is None:
        raise AuthServiceError("Signup session not found")

    if session.get("completed_at"):
        raise AuthServiceError(
            "Signup session is already completed"
        )

    if session.get("verified_at"):
        return {
            "signup_session_id": payload.signup_session_id,
            "verified": True,
        }

    if session.get("locked_at"):
        raise AuthServiceError(
            "OTP session is locked. Start signup again."
        )

    now = datetime.now(timezone.utc)

    if session["otp_expires_at"] <= now:
        raise AuthServiceError(
            "OTP has expired. Start signup again."
        )

    attempts = int(session.get("attempts") or 0)

    if attempts >= settings.signup_otp_max_attempts:
        raise AuthServiceError(
            "Too many OTP attempts. Start signup again."
        )

    if not verify_password(payload.otp, session["otp_hash"]):
        record_failed_otp_attempt(
            payload.signup_session_id,
            settings.signup_otp_max_attempts,
        )
        raise AuthServiceError("Invalid OTP")

    mark_signup_session_verified(payload.signup_session_id)

    return {
        "signup_session_id": payload.signup_session_id,
        "verified": True,
    }


def complete_signup(payload: SignupCompleteRequest) -> dict[str, Any]:
    session = get_signup_session(payload.signup_session_id)
    if session is None:
        raise AuthServiceError("Signup session not found")
    if not session.get("verified_at"):
        raise AuthServiceError("OTP verification required")

    try:
        user = create_user({
            "full_name": session["full_name"],
            "email": session["email"] or f"{session['phone_number']}@maatitrace.local",
            "phone_number": session["phone_number"],
            "password_hash": session["password_hash"],
            "role": payload.role,
        })
        if payload.role == "farmer":
            ensure_farmer_profile_for_user(user)
        mark_signup_session_completed(payload.signup_session_id)
    except AuthRepositoryError as exc:
        raise AuthServiceError(str(exc)) from exc
    return {"success": True, "user_id": user["user_id"]}


def login(payload: LoginRequest) -> dict[str, Any]:
    try:
        identifier = payload.resolved_identifier()
    except ValueError as exc:
        raise AuthServiceError("identifier, email, or phone_number is required") from exc

    user = get_user_by_identifier(identifier)

    if user is None:
        raise AuthServiceError("Invalid login credentials")

    if not user.get("is_active"):
        raise AuthServiceError("User account is inactive")

    if not verify_password(payload.password, user["password_hash"]):
        raise AuthServiceError("Invalid login credentials")

    if user.get("role") == "farmer":
        try:
            ensure_farmer_profile_for_user(user)
        except AuthRepositoryError as exc:
            raise AuthServiceError(str(exc)) from exc

    return _issue_tokens(user)


def refresh(refresh_token_plain: str) -> dict[str, Any]:
    token_hash = hash_refresh_token(refresh_token_plain)
    refresh_row = get_active_refresh_token(token_hash)

    if refresh_row is None:
        raise AuthServiceError("Invalid or expired refresh token")

    user = get_user_by_id(refresh_row["user_id"])

    if user is None or not user.get("is_active"):
        raise AuthServiceError("User account is inactive or missing")

    revoke_refresh_token(token_hash)

    return _issue_tokens(user)


def logout(refresh_token_plain: str) -> dict[str, bool]:
    token_hash = hash_refresh_token(refresh_token_plain)
    revoke_refresh_token(token_hash)
    return {"logged_out": True}


def get_current_user_from_id(user_id: str) -> dict[str, Any]:
    user = get_user_by_id(user_id)

    if user is None:
        raise AuthServiceError("User not found")

    if not user.get("is_active"):
        raise AuthServiceError("User account is inactive")

    return _public_user(user)
