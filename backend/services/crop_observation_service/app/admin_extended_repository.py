from __future__ import annotations

import json
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine
from services.crop_observation_service.app.errors import CropObservationRepositoryError


def _all(sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        with engine.connect() as conn:
            return [dict(row) for row in conn.execute(text(sql), params).mappings().all()]
    except SQLAlchemyError as exc:
        raise CropObservationRepositoryError(str(exc)) from exc


def _one(sql: str, params: dict[str, Any]) -> dict[str, Any] | None:
    rows = _all(sql, params)
    return rows[0] if rows else None


def _write(sql: str, params: dict[str, Any]) -> dict[str, Any] | None:
    try:
        with engine.begin() as conn:
            row = conn.execute(text(sql), params).mappings().first()
            return dict(row) if row else None
    except SQLAlchemyError as exc:
        raise CropObservationRepositoryError(str(exc)) from exc


def target_exists(target_type: str, target_id: UUID) -> bool:
    table_and_id = {
        "CROP": ("crop_observation.crops", "crop_id"),
        "STAGE": ("crop_observation.crop_stages", "stage_id"),
        "STAGE_PRACTICE": ("crop_observation.stage_practices", "stage_practice_id"),
        "FIELD_OPTION": ("crop_observation.practice_field_options", "field_option_id"),
    }.get(target_type)
    if not table_and_id:
        return False
    table, column = table_and_id
    # Both table/column values are internal constants above, never user input.
    row = _one(f"SELECT 1 AS ok FROM {table} WHERE {column} = :target_id;", {"target_id": target_id})
    return bool(row)


def configuration_for_target(target_type: str, target_id: UUID) -> dict[str, Any] | None:
    """Return the version owning a versioned system-media target.

    Crop card media is intentionally global. Stage, practice-guide and option
    media are content belonging to a specific configuration version and must
    never mutate a published version indirectly.
    """
    queries = {
        "STAGE": """
            SELECT cv.config_version_id, cv.status
            FROM crop_observation.crop_stages s
            JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
            WHERE s.stage_id = :target_id
        """,
        "STAGE_PRACTICE": """
            SELECT cv.config_version_id, cv.status
            FROM crop_observation.stage_practices sp
            JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
            JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
            WHERE sp.stage_practice_id = :target_id
        """,
        "FIELD_OPTION": """
            SELECT cv.config_version_id, cv.status
            FROM crop_observation.practice_field_options fo
            JOIN crop_observation.practice_field_definitions fd ON fd.field_definition_id = fo.field_definition_id
            JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
            JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
            JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
            WHERE fo.field_option_id = :target_id
        """,
    }
    query = queries.get(target_type)
    return _one(query, {"target_id": target_id}) if query else None


def get_overview(*, from_date: date | None, to_date: date | None) -> dict[str, Any]:
    return _one(
        """
        WITH d AS (
            SELECT *
            FROM crop_observation.daily_stage_observations
            WHERE (:from_date IS NULL OR observed_on >= :from_date)
              AND (:to_date IS NULL OR observed_on <= :to_date)
        ),
        records AS (
            SELECT v.*
            FROM crop_observation.v_practice_records v
            WHERE (:from_date IS NULL OR v.observed_on >= :from_date)
              AND (:to_date IS NULL OR v.observed_on <= :to_date)
        ),
        media AS (
            SELECT
                count(*) FILTER (
                    WHERE om.media_role = 'PHOTO'
                      AND om.media_purpose = 'ISSUE_EVIDENCE'
                      AND ma.upload_status = 'READY'
                ) AS issue_images,
                count(*) FILTER (
                    WHERE om.media_role = 'PHOTO'
                      AND om.media_purpose = 'PRACTICE_EVIDENCE'
                      AND ma.upload_status = 'READY'
                ) AS practice_images,
                count(*) FILTER (
                    WHERE om.media_role = 'PHOTO'
                      AND om.media_purpose = 'CROP_CONDITION'
                      AND ma.upload_status = 'READY'
                ) AS crop_condition_images,
                count(*) FILTER (
                    WHERE om.media_role = 'VOICE_NOTE'
                      AND ma.upload_status = 'READY'
                ) AS voice_notes
            FROM crop_observation.observation_media om
            JOIN crop_observation.media_assets ma ON ma.media_asset_id = om.media_asset_id
            LEFT JOIN crop_observation.daily_stage_observations ds
              ON om.owner_type = 'DAILY_STAGE' AND ds.daily_observation_id = om.owner_id
            LEFT JOIN crop_observation.practice_observations po
              ON om.owner_type = 'PRACTICE' AND po.practice_observation_id = om.owner_id
            LEFT JOIN crop_observation.daily_stage_observations dp
              ON po.daily_observation_id = dp.daily_observation_id
            WHERE (:from_date IS NULL OR COALESCE(ds.observed_on, dp.observed_on) >= :from_date)
              AND (:to_date IS NULL OR COALESCE(ds.observed_on, dp.observed_on) <= :to_date)
        )
        SELECT
            (SELECT count(*) FROM records) AS records,
            (SELECT count(DISTINCT farmer_user_id) FROM records) AS farmers,
            (SELECT count(DISTINCT farm_id) FROM records) AS farms,
            (SELECT count(*) FROM d WHERE crop_status = 'SERIOUS_PROBLEM') AS serious_stage_updates,
            (SELECT count(*) FROM d WHERE crop_status = 'SOME_PROBLEM') AS some_problem_stage_updates,
            (SELECT count(*) FROM d WHERE crop_status = 'GOOD') AS good_stage_updates,
            (SELECT count(*) FROM records WHERE review_status IN ('NEW','IN_REVIEW','NEEDS_FOLLOW_UP')) AS open_reviews,
            (SELECT count(*) FROM records WHERE severity = 'HIGH') AS high_severity_records,
            (SELECT count(*) FROM crop_observation.review_flags WHERE status = 'OPEN') AS open_flags,
            COALESCE((SELECT issue_images FROM media), 0) AS issue_images,
            COALESCE((SELECT practice_images FROM media), 0) AS practice_images,
            COALESCE((SELECT crop_condition_images FROM media), 0) AS crop_condition_images,
            COALESCE((SELECT voice_notes FROM media), 0) AS voice_notes;
        """,
        {"from_date": from_date, "to_date": to_date},
    ) or {}


def overview_by_crop(*, from_date: date | None, to_date: date | None) -> list[dict[str, Any]]:
    return _all(
        """
        SELECT crop_code, count(*)::int AS records
        FROM crop_observation.v_practice_records
        WHERE (:from_date IS NULL OR observed_on >= :from_date)
          AND (:to_date IS NULL OR observed_on <= :to_date)
        GROUP BY crop_code
        ORDER BY records DESC, crop_code;
        """,
        {"from_date": from_date, "to_date": to_date},
    )


def overview_by_practice(*, from_date: date | None, to_date: date | None) -> list[dict[str, Any]]:
    return _all(
        """
        SELECT practice_code, count(*)::int AS records
        FROM crop_observation.v_practice_records
        WHERE (:from_date IS NULL OR observed_on >= :from_date)
          AND (:to_date IS NULL OR observed_on <= :to_date)
        GROUP BY practice_code
        ORDER BY records DESC, practice_code;
        """,
        {"from_date": from_date, "to_date": to_date},
    )


def overview_trend(*, from_date: date | None, to_date: date | None) -> list[dict[str, Any]]:
    return _all(
        """
        SELECT observed_on AS day, count(*)::int AS records
        FROM crop_observation.v_practice_records
        WHERE (:from_date IS NULL OR observed_on >= :from_date)
          AND (:to_date IS NULL OR observed_on <= :to_date)
        GROUP BY observed_on
        ORDER BY observed_on;
        """,
        {"from_date": from_date, "to_date": to_date},
    )


def list_records(
    *,
    crop_code: str | None,
    stage_code: str | None,
    practice_code: str | None,
    crop_status: str | None,
    review_status: str | None,
    severity: str | None,
    farmer_user_id: UUID | None,
    farm_id: UUID | None,
    from_date: date | None,
    to_date: date | None,
    has_issue_image: bool | None,
    has_practice_image: bool | None,
    has_voice: bool | None,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    clauses = ["1=1"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    filters = {
        "crop_code": crop_code,
        "stage_code": stage_code,
        "practice_code": practice_code,
        "crop_status": crop_status,
        "review_status": review_status,
        "severity": severity,
        "farmer_user_id": farmer_user_id,
        "farm_id": farm_id,
    }
    for key, value in filters.items():
        if value is not None:
            clauses.append(f"{key} = :{key}")
            params[key] = value
    if from_date is not None:
        clauses.append("observed_on >= :from_date")
        params["from_date"] = from_date
    if to_date is not None:
        clauses.append("observed_on <= :to_date")
        params["to_date"] = to_date
    if has_issue_image is not None:
        clauses.append("issue_image_count > 0" if has_issue_image else "issue_image_count = 0")
    if has_practice_image is not None:
        clauses.append("practice_image_count > 0" if has_practice_image else "practice_image_count = 0")
    if has_voice is not None:
        clauses.append("voice_count > 0" if has_voice else "voice_count = 0")

    return _all(
        f"""
        SELECT *
        FROM crop_observation.v_practice_records
        WHERE {' AND '.join(clauses)}
        ORDER BY observed_on DESC, updated_at DESC, record_id DESC
        LIMIT :limit OFFSET :offset;
        """,
        params,
    )


def get_record(record_id: UUID) -> dict[str, Any] | None:
    return _one(
        """
        SELECT *
        FROM crop_observation.v_practice_records
        WHERE record_id = :record_id;
        """,
        {"record_id": record_id},
    )


def get_record_media(record_id: UUID) -> list[dict[str, Any]]:
    return _all(
        """
        SELECT
            ma.media_asset_id,
            ma.media_type,
            ma.mime_type,
            ma.byte_size,
            ma.duration_seconds,
            ma.upload_status,
            om.media_role,
            om.media_purpose,
            om.slot_number,
            ma.created_at
        FROM crop_observation.observation_media om
        JOIN crop_observation.media_assets ma ON ma.media_asset_id = om.media_asset_id
        WHERE om.owner_type = 'PRACTICE'
          AND om.owner_id = :record_id
          AND ma.upload_status = 'READY'
        ORDER BY om.media_purpose, om.slot_number NULLS LAST, ma.created_at;
        """,
        {"record_id": record_id},
    )


def get_record_revisions(record_id: UUID) -> list[dict[str, Any]]:
    return _all(
        """
        SELECT revision_id, revision_number, previous_payload, new_payload,
               changed_by_user_id, changed_at
        FROM crop_observation.observation_revisions
        WHERE observation_type = 'PRACTICE'
          AND observation_id = :record_id
        ORDER BY revision_number DESC;
        """,
        {"record_id": record_id},
    )


def upsert_record_review(
    *,
    record_id: UUID,
    review_status: str,
    admin_note: str | None,
    reviewed_by_user_id: UUID,
) -> dict[str, Any]:
    return _write(
        """
        INSERT INTO crop_observation.record_reviews (
            record_type, record_id, review_status, admin_note, reviewed_by_user_id
        )
        VALUES ('PRACTICE', :record_id, :review_status, :admin_note, :reviewed_by_user_id)
        ON CONFLICT (record_type, record_id)
        DO UPDATE SET
            review_status = EXCLUDED.review_status,
            admin_note = EXCLUDED.admin_note,
            reviewed_by_user_id = EXCLUDED.reviewed_by_user_id,
            updated_at = now()
        RETURNING review_id, record_type, record_id, review_status, admin_note,
                  reviewed_by_user_id, created_at, updated_at;
        """,
        {
            "record_id": record_id,
            "review_status": review_status,
            "admin_note": admin_note,
            "reviewed_by_user_id": reviewed_by_user_id,
        },
    )


def list_issues(*, limit: int, offset: int) -> list[dict[str, Any]]:
    return _all(
        """
        SELECT *
        FROM crop_observation.v_practice_records
        WHERE crop_status = 'SERIOUS_PROBLEM'
           OR severity = 'HIGH'
           OR issue_code = 'NOT_SURE'
           OR review_status IN ('NEW', 'IN_REVIEW', 'NEEDS_FOLLOW_UP')
        ORDER BY
            CASE WHEN crop_status = 'SERIOUS_PROBLEM' THEN 0 ELSE 1 END,
            CASE WHEN severity = 'HIGH' THEN 0 ELSE 1 END,
            observed_on DESC,
            updated_at DESC
        LIMIT :limit OFFSET :offset;
        """,
        {"limit": limit, "offset": offset},
    )


def upsert_audit(
    *,
    actor_user_id: UUID,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
    before_state: dict[str, Any] | None,
    after_state: dict[str, Any] | None,
    correlation_id: str | None,
) -> None:
    _write(
        """
        INSERT INTO crop_observation.admin_audit_events (
            actor_user_id, action, entity_type, entity_id,
            before_state, after_state, correlation_id
        )
        VALUES (
            :actor_user_id, :action, :entity_type, :entity_id,
            CAST(:before_state AS jsonb), CAST(:after_state AS jsonb), :correlation_id
        )
        RETURNING audit_event_id;
        """,
        {
            "actor_user_id": actor_user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "before_state": json.dumps(before_state) if before_state is not None else None,
            "after_state": json.dumps(after_state) if after_state is not None else None,
            "correlation_id": correlation_id,
        },
    )


def system_counts() -> dict[str, Any]:
    return _one(
        """
        SELECT
            (SELECT count(*) FROM crop_observation.system_media_assets WHERE upload_status = 'READY') AS system_assets_ready,
            (SELECT count(*) FROM crop_observation.system_media_assets WHERE upload_status = 'REQUESTED' AND COALESCE(upload_expires_at, created_at + interval '15 minutes') > now()) AS system_assets_requested,
            (SELECT count(*) FROM crop_observation.tts_generations WHERE status = 'READY') AS tts_ready,
            (SELECT count(*) FROM crop_observation.tts_generations WHERE status = 'FAILED') AS tts_failed,
            (SELECT count(*) FROM crop_observation.outbox_events WHERE status = 'PENDING') AS outbox_pending,
            (SELECT count(*) FROM crop_observation.review_flags WHERE status = 'OPEN') AS open_flags;
        """,
        {},
    ) or {}


def list_stage_ids_for_config(config_version_id: UUID) -> list[UUID]:
    rows = _all(
        """
        SELECT stage_id
        FROM crop_observation.crop_stages
        WHERE config_version_id = :config_version_id
          AND is_enabled = true
        ORDER BY display_order;
        """,
        {"config_version_id": config_version_id},
    )
    return [row["stage_id"] for row in rows]
