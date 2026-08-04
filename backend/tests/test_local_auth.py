from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from jose import jwt

from shared.config.settings import settings
from shared.security import local_auth


class FakeResult:
    def __init__(self, row):
        self.row = row

    def mappings(self):
        return self

    def first(self):
        return self.row


class FakeConnection:
    def __init__(self, row):
        self.row = row
        self.parameters = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, _statement, parameters):
        self.parameters = parameters
        return FakeResult(self.row)


class FakeEngine:
    def __init__(self, row):
        self.connection = FakeConnection(row)

    def connect(self):
        return self.connection


def _authorization(*, audience: str | None = None) -> tuple[str, str]:
    user_id = str(uuid4())
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": user_id,
            "role": "farmer",
            "type": "access",
            "session_id": str(uuid4()),
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "iss": settings.jwt_issuer,
            "aud": audience or settings.jwt_audience,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return f"Bearer {token}", user_id


def test_load_current_user_validates_token_and_loads_current_account(monkeypatch) -> None:
    authorization, user_id = _authorization()
    engine = FakeEngine(
        {
            "user_id": user_id,
            "full_name": None,
            "email": "farmer@example.com",
            "phone_number": None,
            "role": "farmer",
            "is_active": True,
            "is_verified": True,
            "onboarding_status": "completed",
            "profile_image_url": None,
        }
    )
    monkeypatch.setattr(local_auth, "engine", engine)

    principal = local_auth.load_current_user(authorization)

    assert principal["user_id"] == user_id
    assert principal["full_name"] == "farmer@example.com"
    assert engine.connection.parameters == {"user_id": user_id}


def test_load_current_user_rejects_wrong_audience_before_database_lookup(
    monkeypatch,
) -> None:
    authorization, _ = _authorization(audience="wrong-audience")
    engine = FakeEngine(None)
    monkeypatch.setattr(local_auth, "engine", engine)

    with pytest.raises(local_auth.InvalidAccessTokenError):
        local_auth.load_current_user(authorization)

    assert engine.connection.parameters is None


def test_load_current_user_rejects_inactive_account(monkeypatch) -> None:
    authorization, user_id = _authorization()
    engine = FakeEngine(
        {
            "user_id": user_id,
            "full_name": "Inactive Farmer",
            "email": "inactive@example.com",
            "phone_number": None,
            "role": "farmer",
            "is_active": False,
            "is_verified": True,
            "onboarding_status": "completed",
            "profile_image_url": None,
        }
    )
    monkeypatch.setattr(local_auth, "engine", engine)

    with pytest.raises(local_auth.CurrentUserUnavailableError):
        local_auth.load_current_user(authorization)
