class FarmRegistryError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        *,
        fields: list[dict] | None = None,
        internal_message: str | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.fields = fields or []
        self.internal_message = internal_message

    def detail(self, correlation_id: str) -> dict:
        payload = {
            "code": self.code,
            "message": self.message,
            "correlation_id": correlation_id,
        }
        if self.fields:
            payload["fields"] = self.fields
        return payload


class FarmRegistryRepositoryError(FarmRegistryError):
    def __init__(self, message: str):
        super().__init__(
            "FARM_REGISTRY_REPOSITORY_ERROR",
            "The farm request could not be saved or read.",
            500,
            internal_message=message,
        )
