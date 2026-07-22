from __future__ import annotations

import json
import secrets
from typing import Any

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from shared.config.settings import settings
from shared.db.postgres import engine
from services.auth_service.app.repository import ensure_farmer_profile_for_user
from services.auth_service.app.security import hash_password


class GoogleOAuthError(RuntimeError):
    pass


def verify_google_id_token(token: str) -> dict[str, Any]:
    if not settings.google_client_id:
        raise GoogleOAuthError("GOOGLE_CLIENT_ID is missing")
    try:
        claims = id_token.verify_oauth2_token(
            token, google_requests.Request(), settings.google_client_id
        )
    except Exception as exc:
        raise GoogleOAuthError("Invalid or expired Google credential") from exc

    if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise GoogleOAuthError("Invalid Google issuer")
    if not claims.get("sub") or not claims.get("email") or not claims.get("email_verified"):
        raise GoogleOAuthError("Google account email is not verified")
    if settings.google_allowed_domain and claims.get("hd") != settings.google_allowed_domain:
        raise GoogleOAuthError("Google account domain is not allowed")
    return claims


def find_or_create_google_user(claims: dict[str, Any]) -> dict[str, Any]:
    email = str(claims["email"]).strip().lower()
    subject = str(claims["sub"])
    profile = json.dumps(claims)
    select_identity = text("""
        SELECT u.user_id, u.full_name, u.email, u.phone_number, u.role,
               u.is_active, u.is_verified, u.onboarding_status, u.profile_image_url
        FROM auth_identities ai JOIN users u ON u.user_id = ai.user_id
        WHERE ai.provider = 'google' AND ai.provider_subject = :subject LIMIT 1
    """)
    select_email = text("""
        SELECT user_id, full_name, email, phone_number, role, is_active,
               is_verified, onboarding_status, profile_image_url
        FROM users WHERE lower(email) = :email LIMIT 1
    """)
    insert_user = text("""
        INSERT INTO users(full_name, email, password_hash, role, is_active,
                          is_verified, profile_image_url, onboarding_status, updated_at)
        VALUES (:name, :email, :password_hash, 'farmer', TRUE, TRUE,
                :picture, 'pending', now())
        RETURNING user_id, full_name, email, phone_number, role, is_active,
                  is_verified, onboarding_status, profile_image_url
    """)
    insert_identity = text("""
        INSERT INTO auth_identities(user_id, provider, provider_subject, email,
                                    email_verified, raw_profile)
        VALUES (:user_id, 'google', :subject, :email, TRUE, CAST(:profile AS jsonb))
        ON CONFLICT(provider, provider_subject) DO UPDATE SET
            email = EXCLUDED.email, email_verified = EXCLUDED.email_verified,
            raw_profile = EXCLUDED.raw_profile, updated_at = now()
    """)
    try:
        with engine.begin() as conn:
            row = conn.execute(select_identity, {"subject": subject}).mappings().first()
            if row:
                user = dict(row)
            else:
                row = conn.execute(select_email, {"email": email}).mappings().first()
                if row:
                    user = dict(row)
                else:
                    user = dict(conn.execute(insert_user, {
                        "name": claims.get("name") or email,
                        "email": email,
                        "password_hash": hash_password(secrets.token_urlsafe(48)),
                        "picture": claims.get("picture"),
                    }).mappings().one())
                conn.execute(insert_identity, {
                    "user_id": str(user["user_id"]), "subject": subject,
                    "email": email, "profile": profile,
                })
            conn.execute(text("UPDATE users SET last_login_at=now(), updated_at=now() WHERE user_id=:id"), {"id": str(user["user_id"])})
    except (IntegrityError, SQLAlchemyError) as exc:
        raise GoogleOAuthError("Could not link Google account") from exc

    if not user.get("is_active"):
        raise GoogleOAuthError("User account is inactive")
    if user.get("role") == "farmer":
        ensure_farmer_profile_for_user(user)
    return user