from __future__ import annotations

from typing import Any

from services.auth_service.app.repository import (
    AuthRepositoryError,
    create_refresh_token,
    create_user,
    ensure_farmer_profile_for_user,
    get_active_refresh_token,
    get_user_by_id,
    get_user_by_identifier,
    revoke_refresh_token,
)
from services.auth_service.app.schemas import LoginRequest, SignupRequest
from services.auth_service.app.security import (
    create_access_token,
    create_refresh_token_plain,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
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
