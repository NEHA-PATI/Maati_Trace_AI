from __future__ import annotations

import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests

from shared.config.settings import settings


class DownloadError(RuntimeError):
    pass


def download_to_temp(href: str, *, requires_earthdata: bool = False) -> str:
    headers: dict[str, str] = {}
    if requires_earthdata:
        token = settings.earthdata_token.strip()
        if not token:
            raise DownloadError(
                "EARTHDATA_TOKEN is required to download this NASA Earthdata product"
            )
        headers["Authorization"] = f"Bearer {token}"

    suffix = Path(urlparse(href).path).suffix or ".bin"
    fd, path = tempfile.mkstemp(prefix="maatitrace_", suffix=suffix)
    os.close(fd)
    try:
        with requests.get(
            href,
            headers=headers,
            stream=True,
            timeout=settings.source_download_timeout_seconds,
            allow_redirects=True,
        ) as response:
            response.raise_for_status()
            with open(path, "wb") as out:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        out.write(chunk)
        return path
    except Exception as exc:
        try:
            os.remove(path)
        except OSError:
            pass
        raise DownloadError(f"Failed to download source asset: {exc}") from exc
