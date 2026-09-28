from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FpoManagementConfig:
    app_env: str
    service_port: int
    cors_allowed_origins: tuple[str, ...]
    trusted_hosts: tuple[str, ...]
    worker_batch_size: int
    worker_poll_seconds: float

    @classmethod
    def from_env(cls) -> "FpoManagementConfig":
        return cls(
            app_env=os.getenv("APP_ENV", "development").strip().lower(),
            service_port=int(os.getenv("FPO_SERVICE_PORT", "8016")),
            cors_allowed_origins=tuple(item.strip() for item in os.getenv("FPO_CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if item.strip()),
            trusted_hosts=tuple(item.strip() for item in os.getenv("FPO_TRUSTED_HOSTS", "localhost,127.0.0.1").split(",") if item.strip()),
            worker_batch_size=max(1, int(os.getenv("FPO_OUTBOX_BATCH_SIZE", "25"))),
            worker_poll_seconds=max(1.0, float(os.getenv("FPO_OUTBOX_POLL_SECONDS", "5"))),
        )
