from __future__ import annotations

import argparse
import logging
import random
import signal
import socket
import sys
import time
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine
from shared.logging.json_logging import configure_json_logging
from services.auth_service.app.config_validation import get_auth_config, validate_auth_config
from services.auth_service.app.logging_context import get_logger, log_event, new_correlation_id, set_correlation_id, reset_correlation_id
from services.auth_service.app.mail import MailServiceError, render_queued_email, send_rendered_email
from services.auth_service.app.repository import (
    claim_email_outbox_batch,
    mark_email_outbox_failed,
    mark_email_outbox_sent,
)


SERVICE_NAME = "auth_email_worker"
configure_json_logging(SERVICE_NAME)
logger = get_logger(__name__)


@dataclass(slots=True)
class WorkerState:
    stopping: bool = False


STATE = WorkerState()


def _signal_handler(signum, _frame) -> None:
    STATE.stopping = True
    log_event(logger, logging.INFO, "email_worker_stop_requested", signal=signum)


def _worker_id() -> str:
    return f"{socket.gethostname()}:{os_getpid_safe()}:{uuid4()}"


def os_getpid_safe() -> int:
    try:
        import os

        return os.getpid()
    except Exception:
        return 0


def _retry_delay_seconds(attempts: int) -> int:
    base = min(3600, 30 * (2 ** max(0, attempts - 1)))
    jitter = random.randint(0, max(1, base // 5))
    return base + jitter


def _safe_error_message(exc: MailServiceError) -> str:
    return f"{exc.code}: {str(exc)}"[:2000]


def process_claimed_email(row: dict, *, max_attempts: int) -> bool:
    email_id = str(row["email_outbox_id"])
    attempts = int(row.get("attempts") or 0)
    correlation_token = set_correlation_id(new_correlation_id())
    try:
        rendered = render_queued_email(row["template_key"], row.get("encrypted_payload"))
        result = send_rendered_email(
            to_email=row["to_email"],
            to_name=row.get("to_name"),
            rendered=rendered,
        )
        with engine.begin() as conn:
            mark_email_outbox_sent(
                conn,
                email_outbox_id=email_id,
                provider_request_id=result.provider_request_id,
                provider_status_code=result.status_code,
            )
        log_event(
            logger,
            logging.INFO,
            "email_outbox_sent",
            email_outbox_id=email_id,
            template_key=row["template_key"],
            attempts=attempts,
            provider_status_code=result.status_code,
            provider_request_id=result.provider_request_id,
        )
        return True
    except MailServiceError as exc:
        dead = (not exc.transient) or attempts >= max_attempts
        retry_after = 0 if dead else _retry_delay_seconds(attempts)
        with engine.begin() as conn:
            mark_email_outbox_failed(
                conn,
                email_outbox_id=email_id,
                error_code=exc.code,
                error_message=_safe_error_message(exc),
                provider_status_code=exc.status_code,
                dead=dead,
                retry_after_seconds=retry_after,
            )
        log_event(
            logger,
            logging.ERROR if dead else logging.WARNING,
            "email_outbox_dead" if dead else "email_outbox_retry_scheduled",
            email_outbox_id=email_id,
            template_key=row.get("template_key"),
            attempts=attempts,
            error_code=exc.code,
            provider_status_code=exc.status_code,
            retry_after_seconds=retry_after,
        )
        return False
    except Exception as exc:
        dead = attempts >= max_attempts
        retry_after = 0 if dead else _retry_delay_seconds(attempts)
        with engine.begin() as conn:
            mark_email_outbox_failed(
                conn,
                email_outbox_id=email_id,
                error_code="EMAIL_WORKER_UNEXPECTED_ERROR",
                error_message=type(exc).__name__,
                provider_status_code=None,
                dead=dead,
                retry_after_seconds=retry_after,
            )
        logger.exception("Unexpected email worker failure", extra={"email_outbox_id": email_id})
        return False
    finally:
        reset_correlation_id(correlation_token)


def run_once(*, worker_id: str, batch_size: int) -> int:
    config = get_auth_config()
    try:
        with engine.begin() as conn:
            rows = claim_email_outbox_batch(
                conn,
                worker_id=worker_id,
                batch_size=batch_size,
                lock_timeout_seconds=config.email_worker_lock_timeout_seconds,
            )
    except SQLAlchemyError:
        logger.exception("Email worker could not claim queue rows")
        return 0

    if rows:
        log_event(logger, logging.INFO, "email_outbox_batch_claimed", count=len(rows), worker_id=worker_id)
    for row in rows:
        if STATE.stopping:
            break
        process_claimed_email(row, max_attempts=config.email_worker_max_attempts)
    return len(rows)


def run_forever(*, worker_id: str, batch_size: int, poll_seconds: float) -> None:
    log_event(
        logger,
        logging.INFO,
        "email_worker_started",
        worker_id=worker_id,
        batch_size=batch_size,
        poll_seconds=poll_seconds,
    )
    while not STATE.stopping:
        claimed = run_once(worker_id=worker_id, batch_size=batch_size)
        if claimed == 0:
            time.sleep(poll_seconds)
    log_event(logger, logging.INFO, "email_worker_stopped", worker_id=worker_id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MaatiTrace Microsoft Graph email outbox worker")
    parser.add_argument("--once", action="store_true", help="Process one batch and exit")
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--poll-seconds", type=float, default=None)
    args = parser.parse_args(argv)

    config = get_auth_config()
    validate_auth_config(config)
    if not config.mail_enabled:
        raise RuntimeError("MAIL_ENABLED must be true before the email worker can start")

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    worker_id = _worker_id()
    batch_size = args.batch_size or config.email_worker_batch_size
    poll_seconds = args.poll_seconds or config.email_worker_poll_seconds
    if args.once:
        run_once(worker_id=worker_id, batch_size=batch_size)
        return 0
    run_forever(worker_id=worker_id, batch_size=batch_size, poll_seconds=poll_seconds)
    return 0


if __name__ == "__main__":
    sys.exit(main())