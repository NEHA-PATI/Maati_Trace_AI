from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
from uuid import uuid4

import httpx
from sqlalchemy import text

from shared.db.postgres import engine


logger = logging.getLogger("auth_fpo_event_worker")
stopping = False


def _stop(_signum, _frame) -> None:
    global stopping
    stopping = True


def _claim(batch_size: int) -> list[dict]:
    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                WITH candidates AS (
                    SELECT event_id
                    FROM public.auth_outbox_events
                    WHERE event_type = 'auth.user.created'
                      AND payload->>'account_type' = 'fpo'
                      AND (
                        (status IN ('queued', 'failed') AND available_at <= now())
                        OR (status = 'publishing' AND locked_at < now() - interval '5 minutes')
                      )
                    ORDER BY available_at, created_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT :batch_size
                )
                UPDATE public.auth_outbox_events AS e
                SET status = 'publishing', locked_at = now(),
                    attempts = e.attempts + 1, updated_at = now()
                FROM candidates
                WHERE e.event_id = candidates.event_id
                RETURNING e.event_id, e.event_type, e.event_version, e.subject_id,
                          e.correlation_id, e.payload, e.created_at, e.attempts;
            """),
            {"batch_size": batch_size},
        ).mappings().all()
    return [dict(row) for row in rows]


def _acknowledge(event_id: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE public.auth_outbox_events
                SET status = 'published', published_at = now(), last_error = NULL,
                    locked_at = NULL, updated_at = now()
                WHERE event_id = :event_id;
            """),
            {"event_id": event_id},
        )


def _schedule_retry(event_id: str, error_code: str, attempts: int) -> None:
    delay = min(3600, 30 * (2 ** min(max(attempts - 1, 0), 7)))
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE public.auth_outbox_events
                SET status = 'failed', last_error = :error_code, locked_at = NULL,
                    available_at = now() + (:delay * interval '1 second'), updated_at = now()
                WHERE event_id = :event_id;
            """),
            {"event_id": event_id, "error_code": error_code[:120], "delay": delay},
        )


def _deliver(event: dict, *, endpoint: str, token: str) -> bool:
    event_id = str(event["event_id"])
    envelope = {
        "event_id": event_id,
        "event_type": event["event_type"],
        "event_version": int(event["event_version"]),
        "occurred_at": event["created_at"].isoformat(),
        "correlation_id": str(event["correlation_id"]),
        "subject_id": str(event["subject_id"]),
        "payload": event["payload"],
    }
    try:
        response = httpx.post(
            endpoint,
            json=envelope,
            headers={
                "X-Internal-Service-Token": token,
                "X-Correlation-ID": str(event["correlation_id"]),
            },
            timeout=10,
        )
        if response.status_code in {200, 202}:
            _acknowledge(event_id)
            logger.info("fpo_auth_event_delivered", extra={"event_id": event_id})
            return True
        _schedule_retry(event_id, f"FPO_EVENT_HTTP_{response.status_code}", int(event["attempts"]))
        logger.warning(
            "fpo_auth_event_delivery_rejected",
            extra={"event_id": event_id, "status_code": response.status_code},
        )
    except httpx.HTTPError as exc:
        _schedule_retry(event_id, "FPO_EVENT_DELIVERY_UNAVAILABLE", int(event["attempts"]))
        logger.warning(
            "fpo_auth_event_delivery_failed",
            extra={"event_id": event_id, "error_type": type(exc).__name__},
        )
    return False


def run_once(*, batch_size: int, endpoint: str, token: str) -> int:
    events = _claim(batch_size)
    for event in events:
        if stopping:
            break
        _deliver(event, endpoint=endpoint, token=token)
    return len(events)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish FPO account-created Auth outbox events")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--poll-seconds", type=float, default=5)
    args = parser.parse_args(argv)
    endpoint = os.getenv(
        "FPO_EVENT_INGESTION_URL",
        "http://127.0.0.1:8016/v1/internal/events/auth-user-created",
    ).strip()
    token = os.getenv("FPO_EVENT_DELIVERY_TOKEN", "").strip()
    if len(token.encode("utf-8")) < 32:
        raise RuntimeError("FPO_EVENT_DELIVERY_TOKEN must contain at least 32 bytes")
    if not endpoint.startswith(("http://", "https://")):
        raise RuntimeError("FPO_EVENT_INGESTION_URL must be an HTTP(S) URL")

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    worker_id = str(uuid4())
    logger.info("auth_fpo_event_worker_started", extra={"worker_id": worker_id})
    if args.once:
        run_once(batch_size=max(args.batch_size, 1), endpoint=endpoint, token=token)
        return 0
    while not stopping:
        if run_once(batch_size=max(args.batch_size, 1), endpoint=endpoint, token=token) == 0:
            time.sleep(max(args.poll_seconds, 1))
    logger.info("auth_fpo_event_worker_stopped", extra={"worker_id": worker_id})
    return 0


if __name__ == "__main__":
    sys.exit(main())
