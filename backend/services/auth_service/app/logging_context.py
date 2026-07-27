from __future__ import annotations

import contextvars
import logging
from collections.abc import Mapping
from typing import Any
from uuid import uuid4


_correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "auth_correlation_id",
    default="",
)

_SENSITIVE_FRAGMENTS = (
    "password",
    "token",
    "otp",
    "credential",
    "secret",
    "authorization",
    "cookie",
)


def new_correlation_id() -> str:
    return str(uuid4())


def get_correlation_id() -> str:
    return _correlation_id.get() or "unassigned"


def set_correlation_id(value: str) -> contextvars.Token[str]:
    return _correlation_id.set(value)


def reset_correlation_id(token: contextvars.Token[str]) -> None:
    _correlation_id.reset(token)


def redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            result[str(key)] = "[REDACTED]" if any(fragment in lowered for fragment in _SENSITIVE_FRAGMENTS) else redact(item)
        return result
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    return value


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    payload = {
        "event": event,
        "correlation_id": get_correlation_id(),
        **redact(fields),
    }
    logger.log(level, event, extra={"event_data": payload})