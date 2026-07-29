from __future__ import annotations

from typing import Any

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from services.auth_service.app.config_validation import get_auth_config
from services.auth_service.app.errors import AuthError


def verify_google_id_token(token: str) -> dict[str, Any]:
    config = get_auth_config()
    if not config.google_enabled or not config.google_client_id:
        raise AuthError("GOOGLE_AUTH_DISABLED", "Google sign-in is not available.", 503)
    if token.count(".") != 2:
        raise AuthError("INVALID_GOOGLE_CREDENTIAL", "Google sign-in could not be verified.", 401)

    try:
        claims = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            config.google_client_id,
        )
    except Exception as exc:
        raise AuthError(
            "INVALID_GOOGLE_CREDENTIAL",
            "Google sign-in could not be verified.",
            401,
        ) from exc

    if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise AuthError("INVALID_GOOGLE_ISSUER", "Google sign-in could not be verified.", 401)
    if not claims.get("sub"):
        raise AuthError("INVALID_GOOGLE_SUBJECT", "Google sign-in could not be verified.", 401)
    if not claims.get("email") or claims.get("email_verified") is not True:
        raise AuthError("GOOGLE_EMAIL_NOT_VERIFIED", "A verified Google email is required.", 401)
    if config.google_allowed_domain and claims.get("hd") != config.google_allowed_domain:
        raise AuthError("GOOGLE_DOMAIN_NOT_ALLOWED", "This Google account is not allowed.", 403)
    return claims