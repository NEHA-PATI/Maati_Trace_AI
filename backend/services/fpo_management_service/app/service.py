from __future__ import annotations

import logging

from shared.db.postgres import engine
from services.fpo_management_service.app.config import FpoManagementConfig
from services.fpo_management_service.app.repository import (
    claim_events,
    get_bootstrap_status,
    mark_failed,
    mark_published,
    provision_fpo,
    get_verification_for_user,
    list_verification_queue,
    review_verification,
    submit_verification,
)

logger = logging.getLogger("fpo_management_service")


def process_batch(batch_size: int) -> int:
    processed = 0
    with engine.begin() as conn:
        events = claim_events(conn, batch_size=batch_size)
    for event in events:
        try:
            with engine.begin() as conn:
                if event["event_type"] == "auth.user.created":
                    payload = event["payload"] if isinstance(event["payload"], dict) else {}
                    if payload.get("account_type") == "fpo":
                        provision_fpo(conn, payload)
                mark_published(conn, event["event_id"])
                processed += 1
        except Exception as exc:
            logger.exception("fpo_provisioning_failed", extra={"event_id": str(event["event_id"])})
            with engine.begin() as conn:
                mark_failed(conn, event["event_id"], str(exc))
    return processed


def bootstrap_status(user_id):
    with engine.connect() as conn:
        return get_bootstrap_status(conn, user_id)


def verification_status(user_id):
    with engine.connect() as conn:
        return get_verification_for_user(conn, user_id)


def submit_verification_request(user_id):
    with engine.begin() as conn:
        return submit_verification(conn, user_id)


def review_verification_request(fpo_id, reviewer_user_id, status, note):
    with engine.begin() as conn:
        return review_verification(
            conn,
            fpo_id=fpo_id,
            reviewer_user_id=reviewer_user_id,
            status=status,
            note=note,
        )


def verification_queue(status: str | None = None):
    with engine.connect() as conn:
        return list_verification_queue(conn, status=status)
