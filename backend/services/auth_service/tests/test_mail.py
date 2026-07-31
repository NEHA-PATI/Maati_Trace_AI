from __future__ import annotations

import pytest

from services.auth_service.app.email_templates import render_email
from services.auth_service.app.mail import (
    MailServiceError,
    decrypt_template_data,
    reset_graph_token_cache,
    send_rendered_email,
)


class FakeResponse:
    def __init__(self, status_code, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}
        self.ok = 200 <= status_code < 300

    def json(self):
        return self._payload


def test_graph_send_accepts_202(monkeypatch, mail_enabled):
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        if "oauth2/v2.0/token" in url:
            return FakeResponse(200, {"access_token": "graph-token", "expires_in": 3600})
        return FakeResponse(202, headers={"request-id": "request-123"})

    reset_graph_token_cache()
    monkeypatch.setattr("services.auth_service.app.mail.requests.post", fake_post)
    rendered = render_email("password_changed", {"full_name": "Neha"})
    result = send_rendered_email(
        to_email="neha@example.com",
        to_name="Neha",
        rendered=rendered,
    )
    assert result.status_code == 202
    assert result.provider_request_id == "request-123"
    assert len(calls) == 2


def test_graph_permanent_rejection_is_not_retried(monkeypatch, mail_enabled):
    def fake_post(url, **kwargs):
        if "oauth2/v2.0/token" in url:
            return FakeResponse(200, {"access_token": "graph-token", "expires_in": 3600})
        return FakeResponse(403)

    reset_graph_token_cache()
    monkeypatch.setattr("services.auth_service.app.mail.requests.post", fake_post)
    rendered = render_email("password_changed", {"full_name": "Neha"})
    with pytest.raises(MailServiceError) as exc_info:
        send_rendered_email(
            to_email="neha@example.com",
            to_name="Neha",
            rendered=rendered,
        )
    assert exc_info.value.transient is False
    assert exc_info.value.status_code == 403


def test_decrypt_rejects_missing_payload():
    with pytest.raises(MailServiceError) as exc_info:
        decrypt_template_data(None)
    assert exc_info.value.code == "EMAIL_PAYLOAD_MISSING"