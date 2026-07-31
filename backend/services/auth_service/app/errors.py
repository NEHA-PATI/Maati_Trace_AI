from __future__ import annotations

from dataclasses import dataclass

from services.auth_service.app.logging_context import get_correlation_id


@dataclass(slots=True)
class AuthError(RuntimeError):
    code: str
    public_message: str
    status_code: int = 400
    internal_message: str | None = None
    retry_after: int | None = None

    def __post_init__(self) -> None:
        RuntimeError.__init__(self, self.internal_message or self.public_message)

    def detail(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.public_message,
            "correlation_id": get_correlation_id(),
        }