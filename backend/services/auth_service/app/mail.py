from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text
from sqlalchemy.engine import Connection

from services.auth_service.app.config_validation import get_auth_config
from services.auth_service.app.email_templates import RenderedEmail, render_email
from services.auth_service.app.logging_context import get_logger, log_event


logger = get_logger(__name__)


class MailServiceError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "MAIL_SEND_FAILED",
        transient: bool = True,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.transient = transient
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class GraphSendResult:
    provider_request_id: str | None
    status_code: int


@dataclass(slots=True)
class _CachedGraphToken:
    access_token: str
    expires_monotonic: float


_TOKEN_LOCK = threading.Lock()
_CACHED_TOKEN: _CachedGraphToken | None = None


def _fernet() -> Fernet:
    return Fernet(get_auth_config().email_payload_encryption_key.encode("ascii"))


def _encrypt_template_data(template_data: dict[str, Any]) -> bytes:
    return _fernet().encrypt(json.dumps(template_data).encode("utf-8"))


def decrypt_template_data(encrypted_payload: bytes | memoryview | None) -> dict[str, Any]:
    if encrypted_payload is None:
        raise MailServiceError(
            "Email payload is missing",
            code="EMAIL_PAYLOAD_MISSING",
            transient=False,
        )
    raw = bytes(encrypted_payload)
    try:
        decrypted = _fernet().decrypt(raw)
        value = json.loads(decrypted.decode("utf-8"))
    except (InvalidToken, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MailServiceError(
            "Email payload could not be decrypted",
            code="EMAIL_PAYLOAD_INVALID",
            transient=False,
        ) from exc
    if not isinstance(value, dict):
        raise MailServiceError(
            "Email payload has an invalid shape",
            code="EMAIL_PAYLOAD_INVALID",
            transient=False,
        )
    return value


def queue_email(
    conn: Connection,
    *,
    to_email: str,
    to_name: str | None,
    template_key: str,
    template_data: dict[str, Any],
    public_metadata: dict[str, Any] | None = None,
) -> str:
    rendered = render_email(template_key, template_data)
    row = conn.execute(
        text(
            """
            INSERT INTO email_outbox (
                email_outbox_id,
                to_email,
                to_name,
                subject,
                template_key,
                provider,
                status,
                metadata,
                payload,
                encrypted_payload,
                attempts,
                next_attempt_at,
                created_at,
                updated_at
            )
            VALUES (
                gen_random_uuid(),
                :to_email,
                :to_name,
                :subject,
                :template_key,
                'microsoft_graph',
                'queued',
                CAST(:metadata AS jsonb),
                CAST(:payload AS jsonb),
                :encrypted_payload,
                0,
                now(),
                now(),
                now()
            )
            RETURNING email_outbox_id;
            """
        ),
        {
            "to_email": to_email,
            "to_name": to_name,
            "subject": rendered.subject,
            "template_key": template_key,
            "metadata": json.dumps(public_metadata or {}),
            "payload": json.dumps({"template_version": 1}),
            "encrypted_payload": _encrypt_template_data(template_data),
        },
    ).scalar_one()
    return str(row)


def render_queued_email(template_key: str, encrypted_payload: bytes | memoryview | None) -> RenderedEmail:
    return render_email(template_key, decrypt_template_data(encrypted_payload))


def _graph_access_token(force_refresh: bool = False) -> str:
    global _CACHED_TOKEN
    config = get_auth_config()
    if not config.mail_enabled:
        raise MailServiceError(
            "Microsoft Graph mail is disabled",
            code="MAIL_NOT_CONFIGURED",
            transient=False,
        )

    now = time.monotonic()
    with _TOKEN_LOCK:
        if not force_refresh and _CACHED_TOKEN and _CACHED_TOKEN.expires_monotonic > now + 60:
            return _CACHED_TOKEN.access_token

        token_url = (
            "https://login.microsoftonline.com/"
            f"{quote(config.microsoft_tenant_id or '', safe='')}/oauth2/v2.0/token"
        )
        try:
            response = requests.post(
                token_url,
                data={
                    "client_id": config.microsoft_client_id,
                    "client_secret": config.microsoft_client_secret,
                    "scope": config.microsoft_graph_scope,
                    "grant_type": "client_credentials",
                },
                timeout=config.microsoft_graph_timeout_seconds,
            )
        except requests.RequestException as exc:
            raise MailServiceError(
                "Microsoft token request failed",
                code="GRAPH_TOKEN_NETWORK_ERROR",
                transient=True,
            ) from exc

        if response.status_code >= 500 or response.status_code == 429:
            raise MailServiceError(
                "Microsoft token service is temporarily unavailable",
                code="GRAPH_TOKEN_TEMPORARY_ERROR",
                transient=True,
                status_code=response.status_code,
            )
        if not response.ok:
            raise MailServiceError(
                "Microsoft token configuration was rejected",
                code="GRAPH_TOKEN_CONFIGURATION_ERROR",
                transient=False,
                status_code=response.status_code,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise MailServiceError(
                "Microsoft token response was not JSON",
                code="GRAPH_TOKEN_INVALID_RESPONSE",
                transient=True,
                status_code=response.status_code,
            ) from exc

        access_token = payload.get("access_token")
        expires_in = int(payload.get("expires_in") or 3600)
        if not access_token:
            raise MailServiceError(
                "Microsoft token response omitted access_token",
                code="GRAPH_TOKEN_INVALID_RESPONSE",
                transient=True,
                status_code=response.status_code,
            )

        _CACHED_TOKEN = _CachedGraphToken(
            access_token=str(access_token),
            expires_monotonic=now + max(120, expires_in),
        )
        log_event(logger, logging.INFO, "microsoft_graph_token_acquired", expires_in_seconds=expires_in)
        return _CACHED_TOKEN.access_token


def reset_graph_token_cache() -> None:
    global _CACHED_TOKEN
    with _TOKEN_LOCK:
        _CACHED_TOKEN = None


def send_rendered_email(
    *,
    to_email: str,
    to_name: str | None,
    rendered: RenderedEmail,
) -> GraphSendResult:
    config = get_auth_config()
    sender = quote(config.mail_from_email or "", safe="@._-+")
    send_url = f"https://graph.microsoft.com/v1.0/users/{sender}/sendMail"

    payload = {
        "message": {
            "subject": rendered.subject,
            "body": {"contentType": "HTML", "content": rendered.html_body},
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": to_email,
                        **({"name": to_name} if to_name else {}),
                    }
                }
            ],
        },
        "saveToSentItems": True,
    }

    def perform(access_token: str) -> requests.Response:
        return requests.post(
            send_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=config.microsoft_graph_timeout_seconds,
        )

    try:
        response = perform(_graph_access_token())
        if response.status_code == 401:
            reset_graph_token_cache()
            response = perform(_graph_access_token(force_refresh=True))
    except requests.RequestException as exc:
        raise MailServiceError(
            "Microsoft Graph send request failed",
            code="GRAPH_SEND_NETWORK_ERROR",
            transient=True,
        ) from exc

    request_id = response.headers.get("request-id") or response.headers.get("client-request-id")
    if response.status_code == 202:
        return GraphSendResult(provider_request_id=request_id, status_code=202)

    if response.status_code == 429 or response.status_code >= 500:
        raise MailServiceError(
            "Microsoft Graph temporarily rejected the email",
            code="GRAPH_SEND_TEMPORARY_ERROR",
            transient=True,
            status_code=response.status_code,
        )

    raise MailServiceError(
        "Microsoft Graph permanently rejected the email",
        code="GRAPH_SEND_PERMANENT_ERROR",
        transient=False,
        status_code=response.status_code,
    )