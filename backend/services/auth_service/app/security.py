from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from shared.config.settings import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthSecurityError(RuntimeError):
    pass


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user: dict[str, Any]) -> str:
    expires_at = utc_now() + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": str(user["user_id"]),
        "email": user["email"],
        "role": user["role"],
        "type": "access",
        "exp": expires_at,
        "iat": utc_now(),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise AuthSecurityError("Invalid or expired access token") from exc

    if payload.get("type") != "access":
        raise AuthSecurityError("Invalid token type")

    return payload


def create_refresh_token_plain() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_token_expiry() -> datetime:
    return utc_now() + timedelta(days=settings.refresh_token_expire_days)