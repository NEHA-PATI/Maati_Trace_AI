from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

from services.auth_service.app import fpo_event_worker


class FakeResult:
    def __init__(self, rows=None):
        self.rows = rows or []

    def mappings(self):
        return self

    def all(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.statement = ""
        self.params = {}

    def execute(self, statement, params=None):
        self.statement = str(statement)
        self.params = params or {}
        return FakeResult(self.rows)


class FakeEngine:
    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def begin(self):
        yield self.connection


def test_claim_only_selects_fpo_events_and_recovers_stale_publisher_lock(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(fpo_event_worker, "engine", FakeEngine(connection))

    assert fpo_event_worker._claim(15) == []

    assert "event_type = 'auth.user.created'" in connection.statement
    assert "payload->>'account_type' = 'fpo'" in connection.statement
    assert "status IN ('queued', 'failed')" in connection.statement
    assert "status = 'publishing' AND locked_at" in connection.statement
    assert "attempts = e.attempts + 1" in connection.statement
    assert connection.params == {"batch_size": 15}


def test_delivery_acknowledges_only_after_fpo_accepts_event(monkeypatch):
    event_id = uuid4()
    correlation_id = uuid4()
    acknowledged = []
    sent = {}

    class Accepted:
        status_code = 202

    def fake_post(endpoint, **kwargs):
        sent["endpoint"] = endpoint
        sent.update(kwargs)
        return Accepted()

    monkeypatch.setattr(fpo_event_worker.httpx, "post", fake_post)
    monkeypatch.setattr(fpo_event_worker, "_acknowledge", acknowledged.append)

    delivered = fpo_event_worker._deliver(
        {
            "event_id": event_id,
            "event_type": "auth.user.created",
            "event_version": 2,
            "subject_id": uuid4(),
            "correlation_id": correlation_id,
            "created_at": datetime(2026, 11, 2, tzinfo=timezone.utc),
            "attempts": 1,
            "payload": {"account_type": "fpo"},
        },
        endpoint="http://fpo-management/internal/events",
        token="x" * 32,
    )

    assert delivered is True
    assert acknowledged == [str(event_id)]
    assert sent["json"]["correlation_id"] == str(correlation_id)
    assert sent["headers"]["X-Internal-Service-Token"] == "x" * 32


def test_delivery_schedules_retry_when_fpo_rejects_event(monkeypatch):
    scheduled = []

    class Rejected:
        status_code = 503

    monkeypatch.setattr(fpo_event_worker.httpx, "post", lambda *_args, **_kwargs: Rejected())
    monkeypatch.setattr(
        fpo_event_worker,
        "_schedule_retry",
        lambda event_id, error_code, attempts: scheduled.append(
            (event_id, error_code, attempts)
        ),
    )

    delivered = fpo_event_worker._deliver(
        {
            "event_id": uuid4(),
            "event_type": "auth.user.created",
            "event_version": 2,
            "subject_id": uuid4(),
            "correlation_id": uuid4(),
            "created_at": datetime(2026, 11, 2, tzinfo=timezone.utc),
            "attempts": 3,
            "payload": {"account_type": "fpo"},
        },
        endpoint="http://fpo-management/internal/events",
        token="x" * 32,
    )

    assert delivered is False
    assert scheduled[0][1:] == ("FPO_EVENT_HTTP_503", 3)
