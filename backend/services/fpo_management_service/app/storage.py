from __future__ import annotations

import os
import socket
import struct
from pathlib import Path
from functools import lru_cache

import boto3
from botocore.exceptions import BotoCoreError, ClientError


class DocumentStorageError(RuntimeError):
    pass


def _bucket() -> str:
    value = os.getenv("FPO_DOCUMENT_S3_BUCKET", "").strip()
    if not value:
        raise DocumentStorageError("FPO document storage is not configured")
    return value


def _mode() -> str:
    mode = os.getenv("FPO_DOCUMENT_STORAGE_MODE", "local").strip().lower()
    if mode not in {"local", "s3"}:
        raise DocumentStorageError("FPO_DOCUMENT_STORAGE_MODE must be local or s3")
    app_env = os.getenv("APP_ENV", "local").strip().lower()
    if app_env in {"prod", "production"} and mode != "s3":
        raise DocumentStorageError("Production requires FPO_DOCUMENT_STORAGE_MODE=s3")
    if mode == "s3" and not _bucket():
        raise DocumentStorageError("FPO document S3 storage is not configured")
    return mode


def _local_root() -> Path:
    root = Path(os.getenv("FPO_LOCAL_DOCUMENT_ROOT", ".data/fpo-documents"))
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _local_path(object_key: str) -> Path:
    root = _local_root()
    target = (root / object_key).resolve()
    if root != target and root not in target.parents:
        raise DocumentStorageError("Invalid document object key")
    return target


def _ttl() -> int:
    return max(60, min(int(os.getenv("FPO_DOCUMENT_UPLOAD_TTL_SECONDS", "300")), 3600))


@lru_cache
def _client():
    return boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-south-1"))


def create_upload_url(*, object_key: str, mime_type: str, document_id: str) -> dict[str, object]:
    if _mode() == "local":
        return {
            "upload_url": f"/v1/fpo/me/documents/{document_id}/content",
            "method": "PUT",
            "headers": {"Content-Type": mime_type},
            "expires_in_seconds": 3600,
            "storage_mode": "local",
        }
    ttl = _ttl()
    try:
        url = _client().generate_presigned_url(
            "put_object",
            Params={"Bucket": _bucket(), "Key": object_key, "ContentType": mime_type},
            ExpiresIn=ttl,
        )
    except (BotoCoreError, ClientError) as exc:
        raise DocumentStorageError("FPO document storage is temporarily unavailable") from exc
    return {"upload_url": url, "method": "PUT", "headers": {"Content-Type": mime_type}, "expires_in_seconds": ttl, "storage_mode": "s3"}


def store_bytes(*, object_key: str, data: bytes) -> None:
    if _mode() == "s3":
        try:
            _client().put_object(Bucket=_bucket(), Key=object_key, Body=data)
        except (BotoCoreError, ClientError) as exc:
            raise DocumentStorageError("FPO document could not be written to storage") from exc
        return
    target = _local_path(object_key)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(f"{target.suffix}.uploading")
    temporary.write_bytes(data)
    temporary.replace(target)


def download_bytes(*, object_key: str) -> bytes:
    if _mode() == "local":
        try:
            return _local_path(object_key).read_bytes()
        except OSError as exc:
            raise DocumentStorageError("FPO local document could not be read") from exc
    try:
        response = _client().get_object(Bucket=_bucket(), Key=object_key)
        return response["Body"].read()
    except (BotoCoreError, ClientError) as exc:
        raise DocumentStorageError("FPO document could not be read from storage") from exc


def delete_bytes(*, object_key: str) -> None:
    if _mode() == "local":
        try:
            _local_path(object_key).unlink(missing_ok=True)
        except OSError as exc:
            raise DocumentStorageError("FPO local document could not be removed") from exc
        return
    try:
        _client().delete_object(Bucket=_bucket(), Key=object_key)
    except (BotoCoreError, ClientError) as exc:
        raise DocumentStorageError("FPO document could not be removed from storage") from exc


def scan_with_clamav(data: bytes) -> tuple[str, str | None]:
    host = os.getenv("FPO_CLAMAV_HOST", "").strip()
    if not host:
        app_env = os.getenv("APP_ENV", "local").strip().lower()
        mode = os.getenv("FPO_CLAMAV_MODE", "required" if app_env in {"prod", "production"} else "optional").strip().lower()
        if mode == "optional" and app_env not in {"prod", "production"}:
            return "CLEAN", None
        raise DocumentStorageError("FPO malware scanner is not configured")
    port = int(os.getenv("FPO_CLAMAV_PORT", "3310"))
    timeout = max(1, min(int(os.getenv("FPO_CLAMAV_TIMEOUT_SECONDS", "60")), 300))
    try:
        with socket.create_connection((host, port), timeout=timeout) as client:
            client.sendall(b"zINSTREAM\0")
            for start in range(0, len(data), 1024 * 1024):
                chunk = data[start : start + 1024 * 1024]
                client.sendall(struct.pack(">I", len(chunk)))
                client.sendall(chunk)
            client.sendall(struct.pack(">I", 0))
            response = client.recv(4096).decode("utf-8", errors="replace").strip()
    except (OSError, ValueError) as exc:
        raise DocumentStorageError("FPO malware scanner is temporarily unavailable") from exc
    if response.endswith("OK"):
        return "CLEAN", None
    if "FOUND" in response:
        return "INFECTED", response[:500]
    raise DocumentStorageError(f"Unexpected malware scanner response: {response[:300]}")
