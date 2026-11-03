from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

from services.auth_service.app import service as auth_service
from services.auth_service.app.dependencies import RequestContext
from services.auth_service.app.schemas import (
    FpoAccessRequestCreate,
    FpoAccessRequestPublicResponse,
)


class FakeResult:
    def __init__(self, row=None):
        self.row = row

    def mappings(self):
        return self

    def first(self):
        return self.row


class FakeConnection:
    def __init__(self, existing_request):
        self.existing_request = existing_request
        self.statements = []

    def execute(self, statement, params=None):
        sql = str(statement)
        self.statements.append(sql)
        if "pg_advisory_xact_lock" in sql:
            return FakeResult()
        if "FROM public.fpo_access_requests r" in sql:
            return FakeResult(self.existing_request)
        raise AssertionError(f"Unexpected query: {sql}")


class FakeEngine:
    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def begin(self):
        yield self.connection


def test_repeat_after_expired_invitation_reuses_request_without_another_email(monkeypatch):
    request_id = uuid4()
    connection = FakeConnection(
        {
            "request_id": request_id,
            "organisation_name": "Growers Producer Company",
            "contact_person_name": "FPO Representative",
            "contact_email": "fpo@example.com",
            "contact_phone": "+919876543210",
            "status": "closed",
            "invitation_status": "expired",
            "invitation_expires_at": datetime(2026, 10, 1, tzinfo=timezone.utc),
            "already_exists": True,
        }
    )
    audit_events = []
    queued_emails = []
    monkeypatch.setattr(auth_service, "engine", FakeEngine(connection))
    monkeypatch.setattr(auth_service, "get_correlation_id", lambda: "request-correlation")
    monkeypatch.setattr(auth_service, "record_audit_event", lambda **kwargs: audit_events.append(kwargs))
    monkeypatch.setattr(auth_service, "queue_email", lambda *args, **kwargs: queued_emails.append(kwargs))

    response = auth_service.submit_fpo_access_request(
        FpoAccessRequestCreate(
            organisation_name="Growers Producer Company",
            contact_person_name="FPO Representative",
            contact_email="FPO@example.com",
            contact_phone="9876543210",
        ),
        RequestContext(
            ip_address="127.0.0.1",
            device_id_hash=None,
            user_agent_hash=None,
            correlation_id="request-correlation",
        ),
    )

    assert response["request_id"] == request_id
    assert response["status"] == "closed"
    assert response["already_exists"] is True
    assert "administrator can resend it" in response["message"]
    FpoAccessRequestPublicResponse.model_validate(response)
    assert not queued_emails
    assert audit_events[0]["event_type"] == "fpo_access_request_deduplicated"
    assert any("pg_advisory_xact_lock" in sql for sql in connection.statements)


def test_active_request_query_is_locked_by_normalized_email():
    request_id = uuid4()
    connection = FakeConnection(
        {
            "request_id": request_id,
            "contact_email": "fpo@example.com",
            "status": "approved",
            "invitation_status": None,
            "already_exists": True,
        }
    )

    response = auth_service.create_fpo_access_request(
        connection,
        organisation_name="Growers Producer Company",
        registration_number=None,
        contact_person_name="FPO Representative",
        contact_email="fpo@example.com",
        contact_phone="+919876543210",
        state_name="Odisha",
        district_name=None,
        message=None,
        created_ip=None,
        device_id_hash=None,
        correlation_id="request-correlation",
    )

    assert response["request_id"] == request_id
    assert response["status"] == "approved"
    assert response["already_exists"] is True
