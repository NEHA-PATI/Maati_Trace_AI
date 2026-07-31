from __future__ import annotations

from contextlib import contextmanager

from services.auth_service.app import email_worker
from services.auth_service.app.email_templates import RenderedEmail
from services.auth_service.app.mail import GraphSendResult, MailServiceError


class FakeEngine:
    @contextmanager
    def begin(self):
        yield object()


def test_worker_marks_success(monkeypatch, mail_enabled):
    recorded = {}
    monkeypatch.setattr(email_worker, "engine", FakeEngine())
    monkeypatch.setattr(
        email_worker,
        "render_queued_email",
        lambda key, payload: RenderedEmail("Subject", "<p>Body</p>", "Body"),
    )
    monkeypatch.setattr(
        email_worker,
        "send_rendered_email",
        lambda **kwargs: GraphSendResult("graph-request", 202),
    )

    def mark_sent(conn, **kwargs):
        recorded.update(kwargs)

    monkeypatch.setattr(email_worker, "mark_email_outbox_sent", mark_sent)
    result = email_worker.process_claimed_email(
        {
            "email_outbox_id": "11111111-1111-1111-1111-111111111111",
            "to_email": "neha@example.com",
            "to_name": "Neha",
            "template_key": "password_changed",
            "encrypted_payload": b"encrypted",
            "attempts": 1,
        },
        max_attempts=3,
    )
    assert result is True
    assert recorded["provider_status_code"] == 202


def test_worker_dead_letters_permanent_failure(monkeypatch, mail_enabled):
    recorded = {}
    monkeypatch.setattr(email_worker, "engine", FakeEngine())
    monkeypatch.setattr(
        email_worker,
        "render_queued_email",
        lambda key, payload: RenderedEmail("Subject", "<p>Body</p>", "Body"),
    )

    def fail(**kwargs):
        raise MailServiceError(
            "forbidden",
            code="GRAPH_SEND_PERMANENT_ERROR",
            transient=False,
            status_code=403,
        )

    monkeypatch.setattr(email_worker, "send_rendered_email", fail)

    def mark_failed(conn, **kwargs):
        recorded.update(kwargs)

    monkeypatch.setattr(email_worker, "mark_email_outbox_failed", mark_failed)
    result = email_worker.process_claimed_email(
        {
            "email_outbox_id": "11111111-1111-1111-1111-111111111111",
            "to_email": "neha@example.com",
            "to_name": "Neha",
            "template_key": "password_changed",
            "encrypted_payload": b"encrypted",
            "attempts": 1,
        },
        max_attempts=3,
    )
    assert result is False
    assert recorded["dead"] is True
    assert recorded["provider_status_code"] == 403