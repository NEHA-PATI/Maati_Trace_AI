from __future__ import annotations

from typing import Any
from uuid import UUID
from datetime import date

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine


class HotStreamRepositoryError(RuntimeError):
    pass


def create_pipeline_job(farm_id: UUID | str, job_type: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    query = text(
        """
        INSERT INTO pipeline_jobs (farm_id, service_name, job_type, status, metadata)
        VALUES (:farm_id, :service_name, :job_type, 'pending', CAST(:metadata AS jsonb))
        RETURNING job_id, farm_id, service_name, job_type, status, current_stage, started_at, finished_at, error_code, error_message, metadata;
        """
    )

    payload = {
        "farm_id": str(farm_id),
        "service_name": "hot_stream_orchestrator_service",
        "job_type": job_type,
        "metadata": json_or_empty(metadata),
    }

    try:
        with engine.begin() as conn:
            row = conn.execute(query, payload).mappings().one()
    except SQLAlchemyError as exc:
        raise HotStreamRepositoryError(f"Failed to create pipeline job: {exc}") from exc

    return dict(row)


def update_pipeline_job_stage(job_id: UUID | str, stage: str, status: str | None = None, metadata: dict[str, Any] | None = None) -> None:
    query = text(
        """
        UPDATE pipeline_jobs
        SET current_stage = :stage,
            status = COALESCE(:status, status),
            metadata = COALESCE(CAST(:metadata AS jsonb), metadata),
            updated_at = now()
        WHERE job_id = :job_id
        RETURNING job_id;
        """
    )

    payload = {
        "job_id": str(job_id),
        "stage": stage,
        "status": status,
        "metadata": json_or_empty(metadata),
    }

    try:
        with engine.begin() as conn:
            row = conn.execute(query, payload).mappings().first()
    except SQLAlchemyError as exc:
        raise HotStreamRepositoryError(f"Failed to update pipeline job stage: {exc}") from exc

    if row is None:
        raise HotStreamRepositoryError(f"Pipeline job not found: {job_id}")


def complete_pipeline_job(job_id: UUID | str, metadata: dict[str, Any] | None = None) -> None:
    query = text(
        """
        UPDATE pipeline_jobs
        SET status = 'succeeded',
            current_stage = NULL,
            finished_at = now(),
            metadata = COALESCE(CAST(:metadata AS jsonb), metadata),
            updated_at = now()
        WHERE job_id = :job_id
        RETURNING job_id;
        """
    )

    payload = {"job_id": str(job_id), "metadata": json_or_empty(metadata)}

    try:
        with engine.begin() as conn:
            row = conn.execute(query, payload).mappings().first()
    except SQLAlchemyError as exc:
        raise HotStreamRepositoryError(f"Failed to complete pipeline job: {exc}") from exc

    if row is None:
        raise HotStreamRepositoryError(f"Pipeline job not found: {job_id}")


def fail_pipeline_job(job_id: UUID | str, error_code: str | None = None, error_message: str | None = None, metadata: dict[str, Any] | None = None) -> None:
    query = text(
        """
        UPDATE pipeline_jobs
        SET status = 'failed',
            error_code = :error_code,
            error_message = :error_message,
            finished_at = now(),
            metadata = COALESCE(CAST(:metadata AS jsonb), metadata),
            updated_at = now()
        WHERE job_id = :job_id
        RETURNING job_id;
        """
    )

    payload = {
        "job_id": str(job_id),
        "error_code": error_code,
        "error_message": error_message,
        "metadata": json_or_empty(metadata),
    }

    try:
        with engine.begin() as conn:
            row = conn.execute(query, payload).mappings().first()
    except SQLAlchemyError as exc:
        raise HotStreamRepositoryError(f"Failed to fail pipeline job: {exc}") from exc

    if row is None:
        raise HotStreamRepositoryError(f"Pipeline job not found: {job_id}")


def json_or_empty(value: dict[str, Any] | None) -> str:
    if value is None:
        return "{}"
    try:
        import json

        return json.dumps(value)
    except Exception:
        return "{}"


def get_existing_scene_analysis_summary(
    farm_id: UUID | str,
    scene_id: str,
    snapshot_date: date,
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT
            farm_id,
            snapshot_date,
            scene_id,
            MAX(scene_datetime) AS scene_datetime,
            MAX(scene_cloud_cover) AS scene_cloud_cover,
            COUNT(*) AS row_count,
            COUNT(DISTINCT h3_index) AS distinct_h3_count,
            COALESCE(SUM(pixel_count), 0) AS total_pixel_count,
            COALESCE(SUM(valid_pixel_count), 0) AS total_valid_pixel_count,
            COALESCE(SUM(cloud_pixel_count), 0) AS total_cloud_pixel_count,
            MAX(parquet_uri) AS parquet_uri
        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
          AND scene_id = :scene_id
          AND snapshot_date = :snapshot_date
        GROUP BY farm_id, snapshot_date, scene_id;
        """
    )

    try:
        with engine.connect() as conn:
            row = conn.execute(
                query,
                {
                    "farm_id": str(farm_id),
                    "scene_id": scene_id,
                    "snapshot_date": snapshot_date,
                },
            ).mappings().first()
    except SQLAlchemyError as exc:
        raise HotStreamRepositoryError(
            f"Failed to read existing scene analysis summary: {exc}"
        ) from exc

    return dict(row) if row else None