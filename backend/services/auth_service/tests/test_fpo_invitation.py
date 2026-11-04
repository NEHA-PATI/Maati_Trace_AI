from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from services.auth_service.app import service as auth_service
from services.auth_service.app import dependencies as auth_dependencies
from services.auth_service.app.dependencies import RequestContext
from services.auth_service.app.errors import AuthError
from services.auth_service.app.schemas import InvitationAcceptRequest
from services.fpo_management_service.app.repository import validate_auth_user_created_event


class FakeResult:
    def __init__(self, row=None):
        self.row = row

    def mappings(self):
        return self

    def first(self):
        return self.row


class FakeConnection:
    def execute(self, statement, params=None):
        sql = str(statement)
        params = params or {}
        if "FROM public.states" in sql:
            if params.get("state_name", "").lower() == "odisha":
                return FakeResult({"state_code": 21, "state_name": "Odisha"})
            return FakeResult()
        if "FROM public.districts" in sql:
            if (
                params.get("state_code") == 21
                and params.get("district_name", "").lower() == "puri"
            ):
                return FakeResult({"district_code": 344, "district_name": "Puri"})
            return FakeResult()
        raise AssertionError(f"Unexpected query: {sql}")


class FakeEngine:
    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def begin(self):
        yield self.connection


def test_fpo_invitation_accept_builds_canonical_provisioning_event(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(auth_service, "engine", FakeEngine(connection))
    monkeypatch.setattr(auth_service, "assert_password_policy", lambda _password: None)
    monkeypatch.setattr(auth_service, "assert_password_not_breached", lambda _password: None)
    monkeypatch.setattr(auth_service, "hash_invitation_token", lambda _token: "hashed-token")
    monkeypatch.setattr(auth_service, "utc_now", lambda: datetime.now(timezone.utc))
    monkeypatch.setattr(
        auth_service,
        "get_account_invitation_by_hash",
        lambda *_args, **_kwargs: {
            "invitation_id": uuid4(),
            "email": "fpo@example.com",
            "role": "fpo",
            "invited_by": uuid4(),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "metadata": {
                "organisation_name": "Growers Producer Company",
                "registration_number": "FPO-001",
                "state_name": "Odisha",
                "district_name": "Puri",
            },
        },
    )
    monkeypatch.setattr(auth_service, "get_user_by_email", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(auth_service, "get_user_by_phone", lambda *_args, **_kwargs: None)
    user_id = uuid4()
    monkeypatch.setattr(
        auth_service,
        "create_user",
        lambda *_args, **_kwargs: {
            "user_id": user_id,
            "full_name": "FPO Representative",
            "email": "fpo@example.com",
            "phone_number": "+919876543210",
        },
    )
    captured = {}
    monkeypatch.setattr(
        auth_service,
        "create_auth_outbox_event",
        lambda _conn, **kwargs: captured.update(kwargs),
    )
    monkeypatch.setattr(auth_service, "mark_account_invitation_accepted", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(auth_service, "mark_user_login", lambda *_args, **_kwargs: None)
    issued_session = SimpleNamespace(session_id=str(uuid4()))
    monkeypatch.setattr(auth_service, "_issue_session", lambda *_args, **_kwargs: issued_session)
    monkeypatch.setattr(auth_service, "record_audit_event", lambda **_kwargs: None)

    result = auth_service.accept_invitation(
        InvitationAcceptRequest(
            token="t" * 60,
            full_name="FPO Representative",
            phone_number="9876543210",
            password="SecurePassword123!",
        ),
        RequestContext(
            ip_address="127.0.0.1",
            device_id_hash=None,
            user_agent_hash=None,
            correlation_id=str(uuid4()),
        ),
    )

    assert result is issued_session
    assert captured["event_version"] == 2
    assert captured["correlation_id"]
    assert captured["payload"]["signup_profile"] == {
        "organisation_name": "Growers Producer Company",
        "registration_type": "other",
        "registration_number": "FPO-001",
        "state_code": 21,
        "state_name": "Odisha",
        "district_code": 344,
        "district_name": "Puri",
    }
    validate_auth_user_created_event(
        {
            "event_id": str(uuid4()),
            "event_type": captured["event_type"],
            "event_version": captured["event_version"],
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "correlation_id": captured["correlation_id"],
            "subject_id": str(user_id),
            "payload": captured["payload"],
        }
    )


def test_invalid_fpo_invitation_location_is_rejected_before_account_creation():
    try:
        auth_service._build_fpo_invitation_signup_profile(
            FakeConnection(),
            metadata={
                "organisation_name": "Growers Producer Company",
                "registration_number": "FPO-001",
                "state_name": "Invalid state",
            },
            full_name="FPO Representative",
        )
    except AuthError as exc:
        assert exc.code == "FPO_INVITATION_LOCATION_INVALID"
        assert exc.status_code == 422
    else:
        raise AssertionError("Invalid invitation location must be rejected.")


def test_event_correlation_id_is_always_a_uuid():
    context = RequestContext(
        ip_address=None,
        device_id_hash=None,
        user_agent_hash=None,
        correlation_id="browser-correlation",
    )

    assert auth_service._event_correlation_id(context)
    from uuid import UUID

    UUID(auth_service._event_correlation_id(context))


def test_request_context_carries_middleware_correlation_id(monkeypatch):
    correlation_id = str(uuid4())
    monkeypatch.setattr(auth_dependencies, "get_correlation_id", lambda: correlation_id)
    monkeypatch.setattr(auth_dependencies, "hash_device_id", lambda _value: None)
    monkeypatch.setattr(auth_dependencies, "hash_user_agent", lambda _value: None)

    context = auth_dependencies.get_request_context(
        type(
            "FakeRequest",
            (),
            {
                "headers": {"User-Agent": "test"},
                "client": type("Client", (), {"host": "127.0.0.1"})(),
            },
        )(),
        x_device_id=None,
    )

    assert context.correlation_id == correlation_id
