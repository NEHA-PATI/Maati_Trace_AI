from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import phonenumbers
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from argon2.low_level import Type
from jose import JWTError, jwt
from passlib.context import CryptContext
from phonenumbers import PhoneNumberFormat, PhoneNumberType

from services.auth_service.app.config_validation import get_auth_config
from services.auth_service.app.errors import AuthError


_ARGON2 = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)
_BCRYPT = CryptContext(schemes=["bcrypt"], deprecated="auto")
_COMMON_PASSWORDS = {
    "password",
    "password123",
    "123456789012",
    "qwertyuiop12",
    "letmein123456",
    "adminadmin123",
    "maatitrace123",
}


class AuthSecurityError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PasswordVerification:
    valid: bool
    needs_rehash: bool = False


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def assert_password_policy(password: str) -> None:
    if len(password) < 12:
        raise AuthError(
            "PASSWORD_TOO_SHORT",
            "Use at least 12 characters for your password.",
            422,
        )
    if len(password) > 128:
        raise AuthError(
            "PASSWORD_TOO_LONG",
            "Use no more than 128 characters for your password.",
            422,
        )
    if password.casefold() in _COMMON_PASSWORDS:
        raise AuthError(
            "PASSWORD_TOO_COMMON",
            "Choose a less common password or a longer passphrase.",
            422,
        )


def hash_password(password: str, *, enforce_policy: bool = True) -> str:
    if enforce_policy:
        assert_password_policy(password)
    return _ARGON2.hash(password)


def verify_password_detailed(password: str, password_hash: str | None) -> PasswordVerification:
    if not password_hash:
        return PasswordVerification(False, False)

    if password_hash.startswith("$argon2id$"):
        try:
            valid = _ARGON2.verify(password_hash, password)
        except (VerifyMismatchError, InvalidHashError):
            return PasswordVerification(False, False)
        return PasswordVerification(bool(valid), _ARGON2.check_needs_rehash(password_hash))

    if password_hash.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            valid = _BCRYPT.verify(password, password_hash)
        except Exception:
            return PasswordVerification(False, False)
        return PasswordVerification(bool(valid), bool(valid))

    return PasswordVerification(False, False)


def verify_password(password: str, password_hash: str | None) -> bool:
    return verify_password_detailed(password, password_hash).valid


def normalize_indian_mobile(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise AuthError("INVALID_PHONE", "Enter a valid Indian mobile number.", 422)

    if raw.startswith("0") and not raw.startswith("00"):
        raw = raw[1:]

    try:
        parsed = phonenumbers.parse(raw, "IN")
    except phonenumbers.NumberParseException as exc:
        raise AuthError("INVALID_PHONE", "Enter a valid Indian mobile number.", 422) from exc

    number_type = phonenumbers.number_type(parsed)
    if (
        parsed.country_code != 91
        or not phonenumbers.is_possible_number(parsed)
        or not phonenumbers.is_valid_number(parsed)
        or number_type not in {PhoneNumberType.MOBILE, PhoneNumberType.FIXED_LINE_OR_MOBILE}
    ):
        raise AuthError("INVALID_PHONE", "Enter a valid Indian mobile number.", 422)

    return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)


def normalize_email(value: str) -> str:
    return str(value or "").strip().lower()


def create_access_token(user: dict[str, Any], session_id: UUID | str) -> str:
    config = get_auth_config()
    issued_at = utc_now()
    expires_at = issued_at + timedelta(minutes=config.access_token_expire_minutes)
    payload = {
        "sub": str(user["user_id"]),
        "role": str(user["role"]),
        "type": "access",
        "session_id": str(session_id),
        "jti": str(uuid4()),
        "iat": issued_at,
        "exp": expires_at,
        "iss": config.jwt_issuer,
        "aud": config.jwt_audience,
    }
    return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    config = get_auth_config()
    try:
        payload = jwt.decode(
            token,
            config.jwt_secret,
            algorithms=[config.jwt_algorithm],
            audience=config.jwt_audience,
            issuer=config.jwt_issuer,
            options={"require_exp": True, "require_iat": True, "require_sub": True},
        )
    except JWTError as exc:
        raise AuthSecurityError("Invalid or expired access token") from exc

    if payload.get("type") != "access":
        raise AuthSecurityError("Invalid token type")
    if not payload.get("sub") or not payload.get("session_id"):
        raise AuthSecurityError("Invalid token subject or session")
    return payload


def create_refresh_token_plain() -> str:
    return secrets.token_urlsafe(64)


def create_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def create_opaque_token() -> str:
    return secrets.token_urlsafe(64)


def create_six_digit_otp() -> str:
    return f"{secrets.randbelow(900000) + 100000:06d}"


def _hmac_digest(secret: str, purpose: str, value: str) -> str:
    message = f"{purpose}:{value}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def hash_refresh_token(token: str) -> str:
    return _hmac_digest(get_auth_config().token_hmac_secret, "refresh", token)


def hash_otp(signup_session_id: UUID | str, otp: str) -> str:
    return _hmac_digest(
        get_auth_config().token_hmac_secret,
        f"signup-otp:{signup_session_id}",
        otp,
    )


def verify_otp_hash(signup_session_id: UUID | str, otp: str, expected_hash: str) -> bool:
    candidate = hash_otp(signup_session_id, otp)
    return hmac.compare_digest(candidate, expected_hash)


def hash_password_reset_token(token: str) -> str:
    return _hmac_digest(get_auth_config().token_hmac_secret, "password-reset", token)


def hash_invitation_token(token: str) -> str:
    return _hmac_digest(get_auth_config().token_hmac_secret, "invitation", token)


def hash_audit_identifier(value: str) -> str:
    return _hmac_digest(get_auth_config().audit_hmac_secret, "audit-identifier", value.strip().lower())


def hash_device_id(value: str | None) -> str | None:
    if not value:
        return None
    return _hmac_digest(get_auth_config().audit_hmac_secret, "device", value)


def hash_user_agent(value: str | None) -> str | None:
    if not value:
        return None
    return _hmac_digest(get_auth_config().audit_hmac_secret, "user-agent", value)


def refresh_token_expiry() -> datetime:
    return utc_now() + timedelta(days=get_auth_config().refresh_token_expire_days)


def password_reset_expiry() -> datetime:
    return utc_now() + timedelta(minutes=get_auth_config().password_reset_expire_minutes)


def invitation_expiry() -> datetime:
    return utc_now() + timedelta(hours=get_auth_config().invitation_expire_hours)


def secure_equals(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    return hmac.compare_digest(left, right)
