from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlparse


class ProfileConfigurationError(RuntimeError):
    pass


def _csv_env(name: str, default: str) -> tuple[str, ...]:
    return tuple(
        item.strip()
        for item in os.getenv(name, default).split(",")
        if item.strip()
    )


@dataclass(frozen=True, slots=True)
class ProfileConfig:
    app_env: str
    auth_service_url: str
    district_boundary_service_url: str
    cors_allowed_origins: tuple[str, ...]
    trusted_hosts: tuple[str, ...]
    request_timeout_seconds: float
    internal_service_token: str

    @classmethod
    def from_env(cls) -> "ProfileConfig":
        return cls(
            app_env=os.getenv("APP_ENV", "development").strip().lower(),
            auth_service_url=os.getenv(
                "AUTH_SERVICE_URL",
                "http://localhost:8002",
            ).strip().rstrip("/"),
            district_boundary_service_url=os.getenv(
                "DISTRICT_BOUNDARY_SERVICE_URL",
                "http://localhost:8005",
            ).strip().rstrip("/"),
            cors_allowed_origins=_csv_env(
                "PROFILE_CORS_ALLOWED_ORIGINS",
                "http://localhost:5173",
            ),
            trusted_hosts=_csv_env(
                "PROFILE_TRUSTED_HOSTS",
                "localhost,127.0.0.1,testserver",
            ),
            request_timeout_seconds=float(
                os.getenv(
                    "PROFILE_REQUEST_TIMEOUT_SECONDS",
                    "15",
                )
            ),
            internal_service_token=os.getenv(
                "PROFILE_INTERNAL_SERVICE_TOKEN",
                "",
            ).strip(),
        )


def _valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_profile_config(config: ProfileConfig) -> None:
    errors: list[str] = []

    if not _valid_http_url(config.auth_service_url):
        errors.append("AUTH_SERVICE_URL must be a valid http/https URL")

    if not _valid_http_url(config.district_boundary_service_url):
        errors.append(
            "DISTRICT_BOUNDARY_SERVICE_URL must be a valid http/https URL"
        )

    if config.request_timeout_seconds < 1:
        errors.append(
            "PROFILE_REQUEST_TIMEOUT_SECONDS must be at least 1"
        )

    if len(config.internal_service_token.encode("utf-8")) < 32:
        errors.append(
            "PROFILE_INTERNAL_SERVICE_TOKEN must contain at least 32 bytes"
        )

    if not config.cors_allowed_origins:
        errors.append(
            "PROFILE_CORS_ALLOWED_ORIGINS must contain at least one origin"
        )

    if not config.trusted_hosts:
        errors.append(
            "PROFILE_TRUSTED_HOSTS must contain at least one host"
        )

    if errors:
        raise ProfileConfigurationError(
            "Profile configuration is invalid:\n- "
            + "\n- ".join(errors)
        )


@lru_cache(maxsize=1)
def get_profile_config() -> ProfileConfig:
    config = ProfileConfig.from_env()
    validate_profile_config(config)
    return config