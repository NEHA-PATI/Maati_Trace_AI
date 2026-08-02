from __future__ import annotations


class ProfileError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        *,
        internal_message: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.internal_message = internal_message

    def detail(self, correlation_id: str) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "correlation_id": correlation_id,
        }