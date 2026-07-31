from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection

from shared.db.postgres import engine
from services.auth_service.app.logging_context import get_correlation_id, get_logger, log_event, redact
from services.auth_service.app.security import hash_audit_identifier


logger = get_logger(__name__)


def record_audit_event(
    *,
    event_type: str,
    outcome: str,
    user_id: UUID | str | None = None,
    actor_user_id: UUID | str | None = None,
    identifier: str | None = None,
    signup_session_id: UUID | str | None = None,
    auth_session_id: UUID | str | None = None,
    ip_address: str | None = None,
    device_id_hash: str | None = None,
    user_agent_hash: str | None = None,
    metadata: dict[str, Any] | None = None,
    conn: Connection | None = None,
) -> None:
    payload = redact(metadata or {})
    params = {
        "event_type": event_type,
        "outcome": outcome,
        "user_id": str(user_id) if user_id else None,
        "actor_user_id": str(actor_user_id) if actor_user_id else None,
        "identifier_hash": hash_audit_identifier(identifier) if identifier else None,
        "signup_session_id": str(signup_session_id) if signup_session_id else None,
        "auth_session_id": str(auth_session_id) if auth_session_id else None,
        "ip_address": ip_address,
        "device_id_hash": device_id_hash,
        "user_agent_hash": user_agent_hash,
        "correlation_id": get_correlation_id(),
        "metadata": json.dumps(payload),
    }
    query = text(
        """
        INSERT INTO auth_audit_events (
            event_type,
            outcome,
            user_id,
            actor_user_id,
            identifier_hash,
            signup_session_id,
            auth_session_id,
            ip_address,
            device_id_hash,
            user_agent_hash,
            correlation_id,
            metadata
        )
        VALUES (
            :event_type,
            :outcome,
            :user_id,
            :actor_user_id,
            :identifier_hash,
            :signup_session_id,
            :auth_session_id,
            CAST(:ip_address AS inet),
            :device_id_hash,
            :user_agent_hash,
            :correlation_id,
            CAST(:metadata AS jsonb)
        );
        """
    )

    if conn is not None:
        conn.execute(query, params)
    else:
        with engine.begin() as transaction:
            transaction.execute(query, params)

    log_event(
        logger,
        logging.INFO,
        "auth_audit_event_recorded",
        event_type=event_type,
        outcome=outcome,
        user_id=str(user_id) if user_id else None,
        auth_session_id=str(auth_session_id) if auth_session_id else None,
    )