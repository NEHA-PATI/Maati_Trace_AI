from __future__ import annotations

import base64
import os
from urllib.parse import urlparse

import pytest
from sqlalchemy import create_engine, text

from services.auth_service.app.config_validation import reset_auth_config_cache
from services.auth_service.app.rate_limit import set_rate_limiter_for_tests


@pytest.fixture(autouse=True)
def secure_test_environment(monkeypatch):
    fernet_key = base64.urlsafe_b64encode(b"0" * 32).decode("ascii")
    values = {
        "APP_ENV": "test",
        "JWT_SECRET": "J" * 64,
        "TOKEN_HMAC_SECRET": "T" * 64,
        "AUDIT_HMAC_SECRET": "A" * 64,
        "RATE_LIMIT_HMAC_SECRET": "R" * 64,
        "EMAIL_PAYLOAD_ENCRYPTION_KEY": fernet_key,
        "JWT_ALGORITHM": "HS256",
        "JWT_ISSUER": "maatitrace-auth-test",
        "JWT_AUDIENCE": "maatitrace-web-test",
        "FRONTEND_PUBLIC_URL": "http://localhost:5173",
        "FRONTEND_PASSWORD_RESET_PATH": "/reset-password",
        "FRONTEND_INVITATION_ACCEPT_PATH": "/accept-invitation",
        "CORS_ALLOWED_ORIGINS": "http://localhost:5173",
        "TRUSTED_HOSTS": "localhost,127.0.0.1,testserver",
        "GOOGLE_AUTH_ENABLED": "false",
        "MAIL_ENABLED": "false",
        "RATE_LIMIT_ENABLED": "false",
        "PWNED_PASSWORDS_ENABLED": "false",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    reset_auth_config_cache()
    set_rate_limiter_for_tests(None)
    yield
    reset_auth_config_cache()
    set_rate_limiter_for_tests(None)


@pytest.fixture
def mail_enabled(monkeypatch):
    values = {
        "MAIL_ENABLED": "true",
        "MAIL_FROM_EMAIL": "auth@maatitrace.test",
        "MICROSOFT_TENANT_ID": "test-tenant",
        "MICROSOFT_CLIENT_ID": "test-client",
        "MICROSOFT_CLIENT_SECRET": "M" * 64,
        "MICROSOFT_GRAPH_SCOPE": "https://graph.microsoft.com/.default",
        "MICROSOFT_GRAPH_TIMEOUT_SECONDS": "2",
        "EMAIL_WORKER_BATCH_SIZE": "5",
        "EMAIL_WORKER_MAX_ATTEMPTS": "3",
        "EMAIL_WORKER_LOCK_TIMEOUT_SECONDS": "60",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    reset_auth_config_cache()
    yield
    reset_auth_config_cache()


@pytest.fixture
def postgres_test_engine(monkeypatch):
    database_url = os.getenv("AUTH_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set AUTH_TEST_DATABASE_URL to a dedicated PostgreSQL auth test database")

    parsed = urlparse(database_url)
    database_name = parsed.path.rsplit("/", 1)[-1].lower()
    if "test" not in database_name:
        pytest.fail("AUTH_TEST_DATABASE_URL database name must contain 'test'")

    test_engine = create_engine(database_url, pool_pre_ping=True, future=True)
    with test_engine.connect() as conn:
        required = conn.execute(
            text(
                """
                SELECT count(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN (
                      'users', 'signup_otp_sessions', 'refresh_tokens',
                      'auth_identities', 'email_outbox', 'password_reset_sessions',
                      'auth_audit_events', 'fpo_access_requests', 'account_invitations'
                  );
                """
            )
        ).scalar_one()
    if int(required) != 9:
        pytest.fail("Apply the base schema, Phase 1 SQL, and Phase 2 SQL to AUTH_TEST_DATABASE_URL")

    from services.auth_service.app import audit, email_worker, service

    monkeypatch.setattr(service, "engine", test_engine)
    monkeypatch.setattr(audit, "engine", test_engine)
    monkeypatch.setattr(email_worker, "engine", test_engine)

    with test_engine.begin() as conn:
        conn.execute(
            text(
                """
                TRUNCATE TABLE
                    email_outbox,
                    auth_audit_events,
                    password_reset_sessions,
                    account_invitations,
                    fpo_access_requests,
                    refresh_tokens,
                    auth_identities,
                    signup_otp_sessions,
                    users
                RESTART IDENTITY CASCADE;
                """
            )
        )

    yield test_engine

    with test_engine.begin() as conn:
        conn.execute(
            text(
                """
                TRUNCATE TABLE
                    email_outbox,
                    auth_audit_events,
                    password_reset_sessions,
                    account_invitations,
                    fpo_access_requests,
                    refresh_tokens,
                    auth_identities,
                    signup_otp_sessions,
                    users
                RESTART IDENTITY CASCADE;
                """
            )
        )
    test_engine.dispose()