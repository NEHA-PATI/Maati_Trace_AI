from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlparse

from cryptography.fernet import Fernet


class AuthConfigurationError(RuntimeError):
    pass


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


def _bool(name: str, default: bool = False) -> bool:
    value = _env(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    value = _env(name)
    return int(value) if value is not None else default


def _float(name: str, default: float) -> float:
    value = _env(name)
    return float(value) if value is not None else default


def _csv(name: str, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    value = _env(name)
    if not value:
        return default
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class AuthConfig:
    app_env: str
    jwt_secret: str
    jwt_algorithm: str
    jwt_issuer: str
    jwt_audience: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    token_hmac_secret: str
    audit_hmac_secret: str
    rate_limit_hmac_secret: str
    email_payload_encryption_key: str

    frontend_public_url: str
    frontend_password_reset_path: str
    frontend_invitation_accept_path: str
    cors_allowed_origins: tuple[str, ...]
    trusted_hosts: tuple[str, ...]

    refresh_cookie_name: str
    refresh_cookie_path: str
    csrf_cookie_name: str
    cookie_domain: str | None
    cookie_secure: bool
    cookie_same_site: str

    google_enabled: bool
    google_client_id: str | None
    google_allowed_domain: str | None
    google_auto_link_verified_email: bool

    mail_enabled: bool
    mail_from_email: str | None
    microsoft_tenant_id: str | None
    microsoft_client_id: str | None
    microsoft_client_secret: str | None
    microsoft_graph_scope: str
    microsoft_graph_timeout_seconds: int
    email_worker_batch_size: int
    email_worker_poll_seconds: float
    email_worker_max_attempts: int
    email_worker_lock_timeout_seconds: int

    redis_url: str | None
    rate_limit_enabled: bool

    signup_otp_expire_minutes: int
    signup_otp_resend_cooldown_seconds: int
    signup_otp_max_resends: int
    signup_otp_max_attempts: int
    password_reset_expire_minutes: int
    invitation_expire_hours: int

    pwned_passwords_enabled: bool
    pwned_passwords_timeout_seconds: int
    pwned_passwords_fail_closed: bool

    @classmethod
    def from_env(cls) -> "AuthConfig":
        app_env = (_env("APP_ENV", "local") or "local").lower()
        return cls(
            app_env=app_env,
            jwt_secret=_env("JWT_SECRET", "") or "",
            jwt_algorithm=_env("JWT_ALGORITHM", "HS256") or "HS256",
            jwt_issuer=_env("JWT_ISSUER", "maatitrace-auth") or "maatitrace-auth",
            jwt_audience=_env("JWT_AUDIENCE", "maatitrace-web") or "maatitrace-web",
            access_token_expire_minutes=_int("ACCESS_TOKEN_EXPIRE_MINUTES", 15),
            refresh_token_expire_days=_int("REFRESH_TOKEN_EXPIRE_DAYS", 30),
            token_hmac_secret=_env("TOKEN_HMAC_SECRET", "") or "",
            audit_hmac_secret=_env("AUDIT_HMAC_SECRET", "") or "",
            rate_limit_hmac_secret=_env("RATE_LIMIT_HMAC_SECRET", "") or "",
            email_payload_encryption_key=_env("EMAIL_PAYLOAD_ENCRYPTION_KEY", "") or "",
            frontend_public_url=_env("FRONTEND_PUBLIC_URL", "http://localhost:5173") or "",
            frontend_password_reset_path=_env("FRONTEND_PASSWORD_RESET_PATH", "/reset-password") or "/reset-password",
            frontend_invitation_accept_path=_env("FRONTEND_INVITATION_ACCEPT_PATH", "/accept-invitation") or "/accept-invitation",
            cors_allowed_origins=_csv("CORS_ALLOWED_ORIGINS", ("http://localhost:5173",)),
            trusted_hosts=_csv("TRUSTED_HOSTS", ("localhost", "127.0.0.1")),
            refresh_cookie_name=_env("REFRESH_COOKIE_NAME", "maatitrace_refresh") or "maatitrace_refresh",
            refresh_cookie_path=_env("REFRESH_COOKIE_PATH", "/v1/auth") or "/v1/auth",
            csrf_cookie_name=_env("CSRF_COOKIE_NAME", "maatitrace_csrf") or "maatitrace_csrf",
            cookie_domain=_env("COOKIE_DOMAIN"),
            cookie_secure=_bool("COOKIE_SECURE", app_env == "production"),
            cookie_same_site=(_env("COOKIE_SAME_SITE", "lax") or "lax").lower(),
            google_enabled=_bool("GOOGLE_AUTH_ENABLED", False),
            google_client_id=_env("GOOGLE_CLIENT_ID"),
            google_allowed_domain=_env("GOOGLE_ALLOWED_DOMAIN"),
            google_auto_link_verified_email=_bool("GOOGLE_AUTO_LINK_VERIFIED_EMAIL", True),
            mail_enabled=_bool("MAIL_ENABLED", False),
            mail_from_email=_env("MAIL_FROM_EMAIL"),
            microsoft_tenant_id=_env("MICROSOFT_TENANT_ID"),
            microsoft_client_id=_env("MICROSOFT_CLIENT_ID"),
            microsoft_client_secret=_env("MICROSOFT_CLIENT_SECRET"),
            microsoft_graph_scope=_env("MICROSOFT_GRAPH_SCOPE", "https://graph.microsoft.com/.default") or "https://graph.microsoft.com/.default",
            microsoft_graph_timeout_seconds=_int("MICROSOFT_GRAPH_TIMEOUT_SECONDS", 20),
            email_worker_batch_size=_int("EMAIL_WORKER_BATCH_SIZE", 10),
            email_worker_poll_seconds=_float("EMAIL_WORKER_POLL_SECONDS", 3.0),
            email_worker_max_attempts=_int("EMAIL_WORKER_MAX_ATTEMPTS", 6),
            email_worker_lock_timeout_seconds=_int("EMAIL_WORKER_LOCK_TIMEOUT_SECONDS", 300),
            redis_url=_env("REDIS_URL", "redis://127.0.0.1:6379/0"),
            rate_limit_enabled=_bool("RATE_LIMIT_ENABLED", False),
            signup_otp_expire_minutes=_int("SIGNUP_OTP_EXPIRE_MINUTES", 10),
            signup_otp_resend_cooldown_seconds=_int("SIGNUP_OTP_RESEND_COOLDOWN_SECONDS", 60),
            signup_otp_max_resends=_int("SIGNUP_OTP_MAX_RESENDS", 3),
            signup_otp_max_attempts=_int("SIGNUP_OTP_MAX_ATTEMPTS", 5),
            password_reset_expire_minutes=_int("PASSWORD_RESET_EXPIRE_MINUTES", 30),
            invitation_expire_hours=_int("INVITATION_EXPIRE_HOURS", 72),
            pwned_passwords_enabled=_bool("PWNED_PASSWORDS_ENABLED", True),
            pwned_passwords_timeout_seconds=_int("PWNED_PASSWORDS_TIMEOUT_SECONDS", 4),
            pwned_passwords_fail_closed=_bool("PWNED_PASSWORDS_FAIL_CLOSED", app_env == "production"),
        )


_WEAK_SECRET_MARKERS = {
    "secret",
    "changeme",
    "change-me",
    "development",
    "default",
    "password",
    "maatitrace",
}


def _validate_secret(name: str, value: str, errors: list[str]) -> None:
    lowered = value.lower()
    if len(value.encode("utf-8")) < 32:
        errors.append(f"{name} must contain at least 32 bytes")
    if any(marker in lowered for marker in _WEAK_SECRET_MARKERS):
        errors.append(f"{name} contains a known weak/default marker")


def _validate_path(name: str, value: str, errors: list[str]) -> None:
    if not value.startswith("/") or value.startswith("//"):
        errors.append(f"{name} must be an application-relative path beginning with one /")
    if "?" in value or "#" in value:
        errors.append(f"{name} must not contain a query string or fragment")


def validate_auth_config(config: AuthConfig) -> None:
    errors: list[str] = []

    for name, value in (
        ("JWT_SECRET", config.jwt_secret),
        ("TOKEN_HMAC_SECRET", config.token_hmac_secret),
        ("AUDIT_HMAC_SECRET", config.audit_hmac_secret),
        ("RATE_LIMIT_HMAC_SECRET", config.rate_limit_hmac_secret),
    ):
        _validate_secret(name, value, errors)

    if len({config.jwt_secret, config.token_hmac_secret, config.audit_hmac_secret, config.rate_limit_hmac_secret}) != 4:
        errors.append("JWT, token, audit, and rate-limit secrets must be different")

    if config.jwt_algorithm != "HS256":
        errors.append("JWT_ALGORITHM must be HS256 for this implementation")
    if not config.jwt_issuer:
        errors.append("JWT_ISSUER is required")
    if not config.jwt_audience:
        errors.append("JWT_AUDIENCE is required")
    if config.cookie_same_site not in {"lax", "strict", "none"}:
        errors.append("COOKIE_SAME_SITE must be lax, strict, or none")
    if config.cookie_same_site == "none" and not config.cookie_secure:
        errors.append("SameSite=None requires COOKIE_SECURE=true")
    if not config.refresh_cookie_path.startswith("/"):
        errors.append("REFRESH_COOKIE_PATH must begin with /")
    if "*" in config.cors_allowed_origins:
        errors.append("Wildcard CORS origin is forbidden when credentials are enabled")
    if not config.trusted_hosts:
        errors.append("TRUSTED_HOSTS must not be empty")

    parsed_frontend = urlparse(config.frontend_public_url)
    if parsed_frontend.scheme not in {"http", "https"} or not parsed_frontend.netloc:
        errors.append("FRONTEND_PUBLIC_URL must be an absolute http(s) URL")
    if parsed_frontend.path not in {"", "/"} or parsed_frontend.query or parsed_frontend.fragment:
        errors.append("FRONTEND_PUBLIC_URL must contain only the frontend origin")
    if config.app_env == "production" and parsed_frontend.scheme != "https":
        errors.append("FRONTEND_PUBLIC_URL must use HTTPS in production")
    if config.app_env == "production" and not config.cookie_secure:
        errors.append("COOKIE_SECURE must be true in production")

    _validate_path("FRONTEND_PASSWORD_RESET_PATH", config.frontend_password_reset_path, errors)
    _validate_path("FRONTEND_INVITATION_ACCEPT_PATH", config.frontend_invitation_accept_path, errors)

    if config.google_enabled and not config.google_client_id:
        errors.append("GOOGLE_CLIENT_ID is required when Google auth is enabled")

    if config.mail_enabled:
        for name, value in (
            ("MAIL_FROM_EMAIL", config.mail_from_email),
            ("MICROSOFT_TENANT_ID", config.microsoft_tenant_id),
            ("MICROSOFT_CLIENT_ID", config.microsoft_client_id),
            ("MICROSOFT_CLIENT_SECRET", config.microsoft_client_secret),
        ):
            if not value:
                errors.append(f"{name} is required when mail is enabled")

    if config.rate_limit_enabled and not config.redis_url:
        errors.append("REDIS_URL is required when rate limiting is enabled")
    if config.app_env == "production" and not config.rate_limit_enabled:
        errors.append("RATE_LIMIT_ENABLED must be true in production")
    if config.app_env == "production" and not config.mail_enabled:
        errors.append("MAIL_ENABLED must be true in production")

    try:
        Fernet(config.email_payload_encryption_key.encode("ascii"))
    except Exception:
        errors.append("EMAIL_PAYLOAD_ENCRYPTION_KEY must be a valid Fernet key")

    positive_values = {
        "ACCESS_TOKEN_EXPIRE_MINUTES": config.access_token_expire_minutes,
        "REFRESH_TOKEN_EXPIRE_DAYS": config.refresh_token_expire_days,
        "SIGNUP_OTP_EXPIRE_MINUTES": config.signup_otp_expire_minutes,
        "SIGNUP_OTP_RESEND_COOLDOWN_SECONDS": config.signup_otp_resend_cooldown_seconds,
        "SIGNUP_OTP_MAX_ATTEMPTS": config.signup_otp_max_attempts,
        "PASSWORD_RESET_EXPIRE_MINUTES": config.password_reset_expire_minutes,
        "INVITATION_EXPIRE_HOURS": config.invitation_expire_hours,
        "MICROSOFT_GRAPH_TIMEOUT_SECONDS": config.microsoft_graph_timeout_seconds,
        "EMAIL_WORKER_BATCH_SIZE": config.email_worker_batch_size,
        "EMAIL_WORKER_MAX_ATTEMPTS": config.email_worker_max_attempts,
        "EMAIL_WORKER_LOCK_TIMEOUT_SECONDS": config.email_worker_lock_timeout_seconds,
    }
    for name, value in positive_values.items():
        if value < 1:
            errors.append(f"{name} must be at least 1")
    if config.signup_otp_max_resends < 0:
        errors.append("SIGNUP_OTP_MAX_RESENDS cannot be negative")
    if config.email_worker_poll_seconds <= 0:
        errors.append("EMAIL_WORKER_POLL_SECONDS must be greater than zero")

    if errors:
        raise AuthConfigurationError("Auth configuration is invalid:\n- " + "\n- ".join(errors))


@lru_cache(maxsize=1)
def get_auth_config() -> AuthConfig:
    config = AuthConfig.from_env()
    validate_auth_config(config)
    return config


def reset_auth_config_cache() -> None:
    get_auth_config.cache_clear()