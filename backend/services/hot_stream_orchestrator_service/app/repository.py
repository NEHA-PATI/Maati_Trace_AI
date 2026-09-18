from __future__ import annotations

from typing import Any
from uuid import UUID
from datetime import date

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine


class HotStreamRepositoryError(RuntimeError):
    pass


def _step_status_from_pipeline(status: str | None) -> str:
    return status or "running"


def upsert_pipeline_job_step(
    job_id: UUID | str,
    *,
    stage: str,
    status: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Persist a queryable stage row while retaining legacy JSON metadata."""
    details = metadata or {}
    dataset_key = details.get("dataset_key") or ""
    rows_read = details.get("source_items_found")
    rows_written = details.get("postgres_rows_written")
    error_code = details.get("error_code") or details.get("reason_code")
    error_message = details.get("error_message") or details.get("message")
    step_status = _step_status_from_pipeline(status)
    query = text(
        """
        INSERT INTO pipeline_job_steps (
            job_id, farm_id, stage_key, dataset_key, status,
            started_at, finished_at, rows_read, rows_written,
            error_code, error_message, metadata, updated_at
        )
        SELECT
            p.job_id, p.farm_id, :stage, :dataset_key, :status,
            CASE WHEN :status IN ('running', 'pending') THEN COALESCE(s.started_at, now()) ELSE s.started_at END,
            CASE WHEN :status IN ('running', 'pending') THEN NULL ELSE now() END,
            :rows_read, :rows_written, :error_code, :error_message,
            CAST(:metadata AS jsonb), now()
        FROM pipeline_jobs p
        LEFT JOIN pipeline_job_steps s
          ON s.job_id = p.job_id AND s.stage_key = :stage
         AND COALESCE(s.dataset_key, '') = COALESCE(:dataset_key, '')
        WHERE p.job_id = :job_id
        ON CONFLICT (job_id, stage_key, dataset_key) DO UPDATE SET
            status = EXCLUDED.status,
            started_at = COALESCE(pipeline_job_steps.started_at, EXCLUDED.started_at),
            finished_at = EXCLUDED.finished_at,
            rows_read = COALESCE(EXCLUDED.rows_read, pipeline_job_steps.rows_read),
            rows_written = COALESCE(EXCLUDED.rows_written, pipeline_job_steps.rows_written),
            error_code = EXCLUDED.error_code,
            error_message = EXCLUDED.error_message,
            metadata = EXCLUDED.metadata,
            updated_at = now();
        """
    )
    payload = {
        "job_id": str(job_id),
        "stage": stage,
        "dataset_key": str(dataset_key),
        "status": step_status,
        "rows_read": rows_read,
        "rows_written": rows_written,
        "error_code": error_code,
        "error_message": error_message,
        "metadata": json_or_empty(details),
    }
    try:
        with engine.begin() as conn:
            conn.execute(query, payload)
    except SQLAlchemyError as exc:
        raise HotStreamRepositoryError(f"Failed to upsert pipeline step: {exc}") from exc


def upsert_farm_dataset_state(
    farm_id: UUID | str,
    dataset_key: str,
    *,
    status: str,
    spatial_level: str | None = None,
    native_resolution_m: float | None = None,
    provider: str | None = None,
    processing_version: str | None = None,
    history_start: str | None = None,
    history_end: str | None = None,
    latest_observation_at: str | None = None,
    row_count: int = 0,
    retryable: bool = False,
    error_code: str | None = None,
    error_message: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Update durable latest source readiness without failing the pipeline."""
    query = text(
        """
        INSERT INTO farm_dataset_state (
            farm_id, dataset_key, status, spatial_level, native_resolution_m,
            last_attempt_at, last_success_at, history_start, history_end,
            latest_observation_at,
            row_count, processing_version, provider, retryable, retry_count,
            next_retry_at, error_code, error_message, metadata, updated_at
        ) VALUES (
            :farm_id, :dataset_key, :status, :spatial_level, :native_resolution_m,
            now(), CASE WHEN :success THEN now() ELSE NULL END,
            CAST(:history_start AS date), CAST(:history_end AS date),
            CAST(:latest_observation_at AS timestamptz),
            :row_count, :processing_version, :provider, :retryable,
            CASE WHEN :retryable THEN 1 ELSE 0 END,
            CASE WHEN :retryable THEN now() + interval '1 hour' ELSE NULL END,
            :error_code, :error_message, CAST(:metadata AS jsonb), now()
        )
        ON CONFLICT (farm_id, dataset_key) DO UPDATE SET
            status = EXCLUDED.status,
            spatial_level = COALESCE(EXCLUDED.spatial_level, farm_dataset_state.spatial_level),
            native_resolution_m = COALESCE(EXCLUDED.native_resolution_m, farm_dataset_state.native_resolution_m),
            last_attempt_at = now(),
            last_success_at = CASE WHEN :success THEN now() ELSE farm_dataset_state.last_success_at END,
            history_start = COALESCE(EXCLUDED.history_start, farm_dataset_state.history_start),
            history_end = COALESCE(EXCLUDED.history_end, farm_dataset_state.history_end),
            latest_observation_at = COALESCE(EXCLUDED.latest_observation_at, farm_dataset_state.latest_observation_at),
            row_count = EXCLUDED.row_count,
            processing_version = COALESCE(EXCLUDED.processing_version, farm_dataset_state.processing_version),
            provider = COALESCE(EXCLUDED.provider, farm_dataset_state.provider),
            retryable = EXCLUDED.retryable,
            retry_count = CASE WHEN :success THEN 0 ELSE farm_dataset_state.retry_count + CASE WHEN :retryable THEN 1 ELSE 0 END END,
            next_retry_at = CASE WHEN :retryable THEN now() + interval '1 hour' ELSE NULL END,
            error_code = EXCLUDED.error_code,
            error_message = EXCLUDED.error_message,
            metadata = EXCLUDED.metadata,
            updated_at = now();
        """
    )
    payload = {
        "farm_id": str(farm_id),
        "dataset_key": dataset_key,
        "status": status,
        "spatial_level": spatial_level,
        "native_resolution_m": native_resolution_m,
        "success": status == "ready",
        "history_start": history_start,
        "history_end": history_end,
        "latest_observation_at": latest_observation_at,
        "row_count": int(row_count or 0),
        "processing_version": processing_version,
        "provider": provider,
        "retryable": bool(retryable),
        "error_code": error_code,
        "error_message": error_message,
        "metadata": json_or_empty(metadata),
    }
    try:
        with engine.begin() as conn:
            conn.execute(query, payload)
    except SQLAlchemyError as exc:
        raise HotStreamRepositoryError(f"Failed to update dataset state: {exc}") from exc


def get_farm_dataset_states(farm_id: UUID | str) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT * FROM farm_dataset_state
        WHERE farm_id = :farm_id
        ORDER BY dataset_key;
        """
    )
    try:
        with engine.connect() as conn:
            return [dict(row) for row in conn.execute(query, {"farm_id": str(farm_id)}).mappings().all()]
    except SQLAlchemyError as exc:
        raise HotStreamRepositoryError(f"Failed to read dataset state: {exc}") from exc


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

    try:
        upsert_pipeline_job_step(job_id, stage=stage, status=status, metadata=metadata)
    except HotStreamRepositoryError:
        # Step observability must not break older installations.
        pass


def complete_pipeline_job(
    job_id: UUID | str,
    metadata: dict[str, Any] | None = None,
    *,
    status: str = "succeeded",
) -> None:
    query = text(
        """
        UPDATE pipeline_jobs
        SET status = :status,
            current_stage = NULL,
            finished_at = now(),
            metadata = COALESCE(CAST(:metadata AS jsonb), metadata),
            updated_at = now()
        WHERE job_id = :job_id
        RETURNING job_id;
        """
    )

    payload = {
        "job_id": str(job_id),
        "status": status,
        "metadata": json_or_empty(metadata),
    }

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


def get_latest_pipeline_job(
    farm_id: UUID | str,
    *,
    job_type: str = "farm_latest_analysis",
) -> dict[str, Any] | None:
    """Return the latest canonical analysis job for a farm.

    Stage jobs are intentionally stored in the same table, so the job type is
    part of this lookup.  This prevents a feature or environment sub-job from
    being mistaken for the farmer-visible analysis run.
    """

    query = text(
        """
        SELECT job_id, farm_id, service_name, job_type, status, current_stage,
               started_at, finished_at, error_code, error_message, metadata,
               updated_at
        FROM pipeline_jobs
        WHERE farm_id = :farm_id
          AND job_type = :job_type
        ORDER BY started_at DESC NULLS LAST, updated_at DESC
        LIMIT 1;
        """
    )
    try:
        with engine.connect() as conn:
            row = conn.execute(
                query,
                {"farm_id": str(farm_id), "job_type": job_type},
            ).mappings().first()
    except SQLAlchemyError as exc:
        raise HotStreamRepositoryError(f"Failed to read latest pipeline job: {exc}") from exc
    return dict(row) if row else None


def get_active_pipeline_job(
    farm_id: UUID | str,
    *,
    job_type: str = "farm_latest_analysis",
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT job_id, farm_id, service_name, job_type, status, current_stage,
               started_at, finished_at, error_code, error_message, metadata,
               updated_at
        FROM pipeline_jobs
        WHERE farm_id = :farm_id
          AND job_type = :job_type
          AND status IN ('pending', 'running')
        ORDER BY started_at DESC NULLS LAST, updated_at DESC
        LIMIT 1;
        """
    )
    try:
        with engine.connect() as conn:
            row = conn.execute(
                query,
                {"farm_id": str(farm_id), "job_type": job_type},
            ).mappings().first()
    except SQLAlchemyError as exc:
        raise HotStreamRepositoryError(f"Failed to read active pipeline job: {exc}") from exc
    return dict(row) if row else None


def get_or_create_active_latest_analysis_job(
    farm_id: UUID | str,
    metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bool]:
    """Atomically claim the farmer-visible latest-analysis slot.

    The API can receive two clicks at the same time.  The advisory lock keeps
    those requests from creating two master workflows for the same farm while
    leaving independent farms fully concurrent.
    """

    select_query = text(
        """
        SELECT job_id, farm_id, service_name, job_type, status, current_stage,
               started_at, finished_at, error_code, error_message, metadata,
               updated_at
        FROM pipeline_jobs
        WHERE farm_id = :farm_id
          AND job_type = 'farm_latest_analysis'
          AND status IN ('pending', 'running')
        ORDER BY started_at DESC NULLS LAST, updated_at DESC
        LIMIT 1;
        """
    )
    insert_query = text(
        """
        INSERT INTO pipeline_jobs (farm_id, service_name, job_type, status, metadata)
        VALUES (:farm_id, :service_name, :job_type, 'pending', CAST(:metadata AS jsonb))
        RETURNING job_id, farm_id, service_name, job_type, status, current_stage,
                  started_at, finished_at, error_code, error_message, metadata,
                  updated_at;
        """
    )
    farm_key = str(farm_id)
    try:
        with engine.begin() as conn:
            conn.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:farm_key));"),
                {"farm_key": f"farm_latest_analysis:{farm_key}"},
            )
            existing = conn.execute(select_query, {"farm_id": farm_key}).mappings().first()
            if existing:
                return dict(existing), True
            created = conn.execute(
                insert_query,
                {
                    "farm_id": farm_key,
                    "service_name": "hot_stream_orchestrator_service",
                    "job_type": "farm_latest_analysis",
                    "metadata": json_or_empty(metadata),
                },
            ).mappings().one()
            return dict(created), False
    except SQLAlchemyError as exc:
        raise HotStreamRepositoryError(
            f"Failed to claim latest analysis job: {exc}"
        ) from exc


def json_or_empty(value: dict[str, Any] | None) -> str:
    if value is None:
        return "{}"
    try:
        import json
        from datetime import date, datetime
        from decimal import Decimal
        from uuid import UUID

        def default(item: Any):
            if isinstance(item, (date, datetime)):
                return item.isoformat()
            if isinstance(item, UUID):
                return str(item)
            if isinstance(item, Decimal):
                return float(item)
            return str(item)

        return json.dumps(value, default=default)
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


def get_sentinel2_history_summary(
    farm_id: UUID | str,
    *,
    start_date: date,
    end_date: date,
    min_valid_fraction: float = 0.0,
) -> dict[str, Any]:
    query = text(
        """
        WITH daily AS (
            SELECT
                snapshot_date,
                COUNT(DISTINCT h3_index) AS h3_count,
                AVG(COALESCE(valid_fraction, 0)) AS avg_valid_fraction,
                COUNT(*) AS row_count
            FROM h3_sentinel2_features
            WHERE farm_id = :farm_id
              AND snapshot_date BETWEEN :start_date AND :end_date
              AND COALESCE(valid_fraction, 0) >= :min_valid_fraction
            GROUP BY snapshot_date
        )
        SELECT
            COUNT(*) AS valid_observation_dates,
            COALESCE(SUM(row_count), 0) AS row_count,
            COALESCE(MAX(h3_count), 0) AS max_h3_count,
            MIN(snapshot_date) AS first_observation_date,
            MAX(snapshot_date) AS latest_observation_date,
            ARRAY_AGG(snapshot_date ORDER BY snapshot_date) AS observation_dates
        FROM daily;
        """
    )

    try:
        with engine.connect() as conn:
            row = conn.execute(
                query,
                {
                    "farm_id": str(farm_id),
                    "start_date": start_date,
                    "end_date": end_date,
                    "min_valid_fraction": min_valid_fraction,
                },
            ).mappings().one()
    except SQLAlchemyError as exc:
        raise HotStreamRepositoryError(
            f"Failed to read Sentinel-2 history summary: {exc}"
        ) from exc

    result = dict(row)
    result["valid_observation_dates"] = int(result.get("valid_observation_dates") or 0)
    result["row_count"] = int(result.get("row_count") or 0)
    result["max_h3_count"] = int(result.get("max_h3_count") or 0)
    result["observation_dates"] = [
        item.isoformat() if hasattr(item, "isoformat") else str(item)
        for item in (result.get("observation_dates") or [])
        if item is not None
    ]
    return result
