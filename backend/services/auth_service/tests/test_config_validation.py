from __future__ import annotations

import pytest

from services.auth_service.app.config_validation import (
    AuthConfig,
    AuthConfigurationError,
    validate_auth_config,
)


def test_secure_test_configuration_is_valid():
    validate_auth_config(AuthConfig.from_env())


def test_production_rejects_wildcard_cors(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("FRONTEND_PUBLIC_URL", "https://app.maatitrace.in")
    monkeypatch.setenv("COOKIE_SECURE", "true")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "*")
    monkeypatch.setenv("MAIL_ENABLED", "true")
    monkeypatch.setenv("MAIL_FROM_EMAIL", "auth@maatitrace.in")
    monkeypatch.setenv("MICROSOFT_TENANT_ID", "tenant")
    monkeypatch.setenv("MICROSOFT_CLIENT_ID", "client")
    monkeypatch.setenv("MICROSOFT_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")

    with pytest.raises(AuthConfigurationError, match="Wildcard CORS"):
        validate_auth_config(AuthConfig.from_env())


def test_weak_secret_is_rejected(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "changeme")
    with pytest.raises(AuthConfigurationError, match="JWT_SECRET"):
        validate_auth_config(AuthConfig.from_env())