from __future__ import annotations

import json
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from services.crop_observation_service.app.errors import CropObservationRepositoryError
from shared.db.postgres import engine

DEFAULT_LOCALE = "en-IN"


def _run(query, params: dict[str, Any]):
    try:
        with engine.connect() as conn:
            return conn.execute(text(query), params).mappings().all()
    except SQLAlchemyError as exc:
        raise CropObservationRepositoryError(str(exc)) from exc


def _run_one(query, params: dict[str, Any]) -> dict[str, Any] | None:
    rows = _run(query, params)
    return dict(rows[0]) if rows else None


def _run_write(query, params: dict[str, Any]) -> dict[str, Any] | None:
    try:
        with engine.begin() as conn:
            rows = conn.execute(text(query), params).mappings().all()
            return dict(rows[0]) if rows else None
    except SQLAlchemyError as exc:
        raise CropObservationRepositoryError(str(exc)) from exc


def pick_names(
    translations: list[dict[str, Any]],
    locale: str,
) -> tuple[str | None, str | None]:
    """Return (primary_name, secondary_name) preferring `locale`, falling
    back to DEFAULT_LOCALE, with the other one as the secondary name."""
    by_locale = {row["locale"]: row["display_name"] for row in translations}
    primary = by_locale.get(locale) or by_locale.get(DEFAULT_LOCALE)
    secondary = None
    if locale != DEFAULT_LOCALE:
        secondary = by_locale.get(DEFAULT_LOCALE)
    if primary is None and by_locale:
        # No translation for the requested locale or the default — fall
        # back to whatever exists so the catalogue entry is never blank.
        primary = next(iter(by_locale.values()))
    return primary, secondary


# ---------------------------------------------------------------------------
# Crops
# ---------------------------------------------------------------------------


def list_active_crops(*, locale: str) -> list[dict[str, Any]]:
    crops = _run(
        """
        SELECT crop_id, crop_code, lifecycle_type, display_order
        FROM crop_observation.crops
        WHERE is_active = true
        ORDER BY display_order;
        """,
        {},
    )
    if not crops:
        return []

    translations = _run(
        """
        SELECT crop_id, locale, display_name
        FROM crop_observation.crop_translations
        WHERE crop_id = ANY(:crop_ids);
        """,
        {"crop_ids": [row["crop_id"] for row in crops]},
    )
    by_crop: dict[Any, list[dict[str, Any]]] = {}
    for row in translations:
        by_crop.setdefault(row["crop_id"], []).append(row)

    images = _run(
        """
        SELECT DISTINCT ON (crop_id) crop_id, asset_id
        FROM crop_observation.system_media_assets
        WHERE crop_id = ANY(:crop_ids) AND asset_type = 'CROP_CARD_IMAGE' AND is_active = true
        ORDER BY crop_id, created_at DESC;
        """,
        {"crop_ids": [row["crop_id"] for row in crops]},
    )
    image_by_crop = {row["crop_id"]: row["asset_id"] for row in images}

    items = []
    for crop in crops:
        primary, secondary = pick_names(by_crop.get(crop["crop_id"], []), locale)
        asset_id = image_by_crop.get(crop["crop_id"])
        items.append(
            {
                "crop_code": crop["crop_code"],
                "lifecycle_type": crop["lifecycle_type"],
                "name": primary or crop["crop_code"],
                "secondary_name": secondary,
                "image_url": (
                    f"/v1/crop-observations/system-media/{asset_id}/content" if asset_id else None
                ),
            }
        )
    return items


def get_crop_by_code(crop_code: str) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT crop_id, crop_code, lifecycle_type, default_stage_strategy, is_active
        FROM crop_observation.crops
        WHERE crop_code = :crop_code;
        """,
        {"crop_code": crop_code},
    )


def get_crop_names(crop_id: UUID, *, locale: str) -> tuple[str | None, str | None]:
    translations = _run(
        """
        SELECT locale, display_name
        FROM crop_observation.crop_translations
        WHERE crop_id = :crop_id;
        """,
        {"crop_id": crop_id},
    )
    return pick_names(translations, locale)


def get_published_config_version(crop_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT config_version_id, crop_id, version_number, status
        FROM crop_observation.crop_config_versions
        WHERE crop_id = :crop_id AND status = 'PUBLISHED'
        LIMIT 1;
        """,
        {"crop_id": crop_id},
    )


def get_config_version(config_version_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT config_version_id, crop_id, version_number, status
        FROM crop_observation.crop_config_versions
        WHERE config_version_id = :config_version_id;
        """,
        {"config_version_id": config_version_id},
    )


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------


def list_stages(config_version_id: UUID) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT stage_id, stage_code, display_order, is_initial, is_enabled
        FROM crop_observation.crop_stages
        WHERE config_version_id = :config_version_id AND is_enabled = true
        ORDER BY display_order;
        """,
        {"config_version_id": config_version_id},
    )


def get_stage_by_code(config_version_id: UUID, stage_code: str) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT stage_id, stage_code, display_order, is_initial, is_enabled
        FROM crop_observation.crop_stages
        WHERE config_version_id = :config_version_id
          AND stage_code = :stage_code
          AND is_enabled = true;
        """,
        {"config_version_id": config_version_id, "stage_code": stage_code},
    )


def get_stage_translations(stage_id: UUID) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT locale, display_name, short_description, instruction_text
        FROM crop_observation.crop_stage_translations
        WHERE stage_id = :stage_id;
        """,
        {"stage_id": stage_id},
    )


def get_stage_names(stage_id: UUID, *, locale: str) -> tuple[str | None, str | None]:
    rows = get_stage_translations(stage_id)
    translations = [{"locale": r["locale"], "display_name": r["display_name"]} for r in rows]
    return pick_names(translations, locale)


# ---------------------------------------------------------------------------
# Stage practices + fields (read-only in Phase 1)
# ---------------------------------------------------------------------------


def list_stage_practices(stage_id: UUID) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT
            sp.stage_practice_id,
            sp.practice_template_id,
            sp.display_order,
            pt.practice_code
        FROM crop_observation.stage_practices sp
        JOIN crop_observation.practice_templates pt
            ON pt.practice_template_id = sp.practice_template_id
        WHERE sp.stage_id = :stage_id AND sp.is_enabled = true
        ORDER BY sp.display_order;
        """,
        {"stage_id": stage_id},
    )


def get_stage_practices_full(stage_id: UUID) -> dict[str, Any]:
    """Everything the screen API needs to render every practice on a stage —
    practice names, fields, field labels/help text, options and option
    labels — in a fixed six queries no matter how many practices/fields/
    options the stage has, instead of the field-by-field, option-by-option
    N+1 that used to back _build_practice() (one query per translation row:
    a stage with 6 practices could mean 60+ round trips on every screen
    load, which is what made every "My Crop" click feel slow once practices
    other than Nutrient Management got real fields).

    Returns {"practices": [...], "fields_by_practice": {...},
    "options_by_field": {...}} — see service._build_practices_for_stage.
    """
    practices = [dict(p) for p in list_stage_practices(stage_id)]
    if not practices:
        return {"practices": [], "fields_by_practice": {}, "options_by_field": {}}

    stage_practice_ids = [p["stage_practice_id"] for p in practices]
    practice_template_ids = list({p["practice_template_id"] for p in practices})

    practice_translations = _run(
        """
        SELECT practice_template_id, locale, display_name
        FROM crop_observation.practice_translations
        WHERE practice_template_id = ANY(:ids);
        """,
        {"ids": practice_template_ids},
    )
    translations_by_practice: dict[Any, list[dict[str, Any]]] = {}
    for row in practice_translations:
        translations_by_practice.setdefault(row["practice_template_id"], []).append(row)
    for practice in practices:
        practice["translations"] = translations_by_practice.get(practice["practice_template_id"], [])

    fields = _run(
        """
        SELECT
            stage_practice_id, field_definition_id, field_code, field_type,
            semantic_type, display_order, is_required
        FROM crop_observation.practice_field_definitions
        WHERE stage_practice_id = ANY(:ids) AND is_enabled = true
        ORDER BY display_order;
        """,
        {"ids": stage_practice_ids},
    )
    fields_by_practice: dict[Any, list[dict[str, Any]]] = {}
    for field in fields:
        fields_by_practice.setdefault(field["stage_practice_id"], []).append(dict(field))

    if not fields:
        return {"practices": practices, "fields_by_practice": {}, "options_by_field": {}}

    field_ids = [f["field_definition_id"] for f in fields]

    field_translations = _run(
        """
        SELECT field_definition_id, locale, label, help_text
        FROM crop_observation.practice_field_translations
        WHERE field_definition_id = ANY(:ids);
        """,
        {"ids": field_ids},
    )
    field_translations_by_field: dict[Any, list[dict[str, Any]]] = {}
    for row in field_translations:
        field_translations_by_field.setdefault(row["field_definition_id"], []).append(row)
    for practice_fields in fields_by_practice.values():
        for field in practice_fields:
            field["translations"] = field_translations_by_field.get(field["field_definition_id"], [])

    options = _run(
        """
        SELECT field_definition_id, field_option_id, option_code, display_order, icon_key
        FROM crop_observation.practice_field_options
        WHERE field_definition_id = ANY(:ids) AND is_active = true
        ORDER BY display_order;
        """,
        {"ids": field_ids},
    )
    options_by_field: dict[Any, list[dict[str, Any]]] = {}
    for option in options:
        options_by_field.setdefault(option["field_definition_id"], []).append(dict(option))

    if options:
        option_ids = [o["field_option_id"] for o in options]
        option_translations = _run(
            """
            SELECT field_option_id, locale, label
            FROM crop_observation.practice_field_option_translations
            WHERE field_option_id = ANY(:ids);
            """,
            {"ids": option_ids},
        )
        option_translations_by_option: dict[Any, list[dict[str, Any]]] = {}
        for row in option_translations:
            option_translations_by_option.setdefault(row["field_option_id"], []).append(row)
        for field_options in options_by_field.values():
            for option in field_options:
                option["translations"] = option_translations_by_option.get(option["field_option_id"], [])

    return {"practices": practices, "fields_by_practice": fields_by_practice, "options_by_field": options_by_field}


def get_practice_translations(practice_template_id: UUID) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT locale, display_name
        FROM crop_observation.practice_translations
        WHERE practice_template_id = :practice_template_id;
        """,
        {"practice_template_id": practice_template_id},
    )


def list_practice_fields(stage_practice_id: UUID) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT
            field_definition_id,
            field_code,
            field_type,
            semantic_type,
            display_order,
            is_required
        FROM crop_observation.practice_field_definitions
        WHERE stage_practice_id = :stage_practice_id AND is_enabled = true
        ORDER BY display_order;
        """,
        {"stage_practice_id": stage_practice_id},
    )


def get_field_translations(field_definition_id: UUID) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT locale, label, help_text
        FROM crop_observation.practice_field_translations
        WHERE field_definition_id = :field_definition_id;
        """,
        {"field_definition_id": field_definition_id},
    )


def list_field_options(field_definition_id: UUID) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT field_option_id, option_code, display_order, icon_key
        FROM crop_observation.practice_field_options
        WHERE field_definition_id = :field_definition_id AND is_active = true
        ORDER BY display_order;
        """,
        {"field_definition_id": field_definition_id},
    )


def get_option_translations(field_option_id: UUID) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT locale, label
        FROM crop_observation.practice_field_option_translations
        WHERE field_option_id = :field_option_id;
        """,
        {"field_option_id": field_option_id},
    )


# ---------------------------------------------------------------------------
# Farm crops
# ---------------------------------------------------------------------------


def list_farm_crops(farm_id: UUID) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT
            farm_crop_id, farm_id, farmer_user_id, crop_code,
            variety_name, planted_on, status, created_at, updated_at
        FROM crop_observation.farm_crops
        WHERE farm_id = :farm_id AND status = 'ACTIVE'
        ORDER BY created_at DESC;
        """,
        {"farm_id": farm_id},
    )


def get_active_farm_crop(farm_id: UUID, crop_code: str) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            farm_crop_id, farm_id, farmer_user_id, crop_code,
            variety_name, planted_on, status, created_at, updated_at
        FROM crop_observation.farm_crops
        WHERE farm_id = :farm_id AND crop_code = :crop_code AND status = 'ACTIVE'
        LIMIT 1;
        """,
        {"farm_id": farm_id, "crop_code": crop_code},
    )


def create_farm_crop(
    *,
    farm_id: UUID,
    farmer_user_id: UUID,
    crop_code: str,
    variety_name: str | None,
    planted_on: date | None,
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.farm_crops (
            farm_id, farmer_user_id, crop_code, variety_name, planted_on, status
        )
        VALUES (
            :farm_id, :farmer_user_id, :crop_code, :variety_name, :planted_on, 'ACTIVE'
        )
        RETURNING
            farm_crop_id, farm_id, farmer_user_id, crop_code,
            variety_name, planted_on, status, created_at, updated_at;
        """,
        {
            "farm_id": farm_id,
            "farmer_user_id": farmer_user_id,
            "crop_code": crop_code,
            "variety_name": variety_name,
            "planted_on": planted_on,
        },
    )


def get_farm_crop(farm_crop_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            farm_crop_id, farm_id, farmer_user_id, crop_code,
            variety_name, planted_on, status, created_at, updated_at
        FROM crop_observation.farm_crops
        WHERE farm_crop_id = :farm_crop_id;
        """,
        {"farm_crop_id": farm_crop_id},
    )


# ---------------------------------------------------------------------------
# Crop cycles
# ---------------------------------------------------------------------------


def get_active_cycle_for_farm_crop(farm_crop_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            crop_cycle_id, farm_crop_id, config_version_id, season_year,
            season_name, cycle_started_on, cycle_ended_on,
            current_stage_code, current_stage_source, status
        FROM crop_observation.crop_cycles
        WHERE farm_crop_id = :farm_crop_id AND status = 'ACTIVE'
        ORDER BY created_at DESC
        LIMIT 1;
        """,
        {"farm_crop_id": farm_crop_id},
    )


def create_crop_cycle(
    *,
    farm_crop_id: UUID,
    config_version_id: UUID,
    season_year: int | None,
    season_name: str | None,
    current_stage_code: str | None,
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.crop_cycles (
            farm_crop_id, config_version_id, season_year, season_name,
            cycle_started_on, current_stage_code, current_stage_source, status
        )
        VALUES (
            :farm_crop_id, :config_version_id, :season_year, :season_name,
            CURRENT_DATE, :current_stage_code, 'SYSTEM', 'ACTIVE'
        )
        RETURNING
            crop_cycle_id, farm_crop_id, config_version_id, season_year,
            season_name, cycle_started_on, cycle_ended_on,
            current_stage_code, current_stage_source, status;
        """,
        {
            "farm_crop_id": farm_crop_id,
            "config_version_id": config_version_id,
            "season_year": season_year,
            "season_name": season_name,
            "current_stage_code": current_stage_code,
        },
    )


def get_crop_cycle(crop_cycle_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            crop_cycle_id, farm_crop_id, config_version_id, season_year,
            season_name, cycle_started_on, cycle_ended_on,
            current_stage_code, current_stage_source, status
        FROM crop_observation.crop_cycles
        WHERE crop_cycle_id = :crop_cycle_id;
        """,
        {"crop_cycle_id": crop_cycle_id},
    )


# ---------------------------------------------------------------------------
# Stage practice lookup (for dynamic validation)
# ---------------------------------------------------------------------------


def get_stage_practice_by_code(stage_id: UUID, practice_code: str) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT sp.stage_practice_id, sp.practice_template_id, pt.practice_code
        FROM crop_observation.stage_practices sp
        JOIN crop_observation.practice_templates pt
            ON pt.practice_template_id = sp.practice_template_id
        WHERE sp.stage_id = :stage_id
          AND pt.practice_code = :practice_code
          AND sp.is_enabled = true;
        """,
        {"stage_id": stage_id, "practice_code": practice_code},
    )


# ---------------------------------------------------------------------------
# Daily stage observations (idempotent UPSERT keyed on client_entry_id and
# on (crop_cycle_id, stage_code, observed_on) so retried Saves never
# duplicate rows and the original observed_on is never rewritten).
# ---------------------------------------------------------------------------


def upsert_daily_status(
    *,
    crop_cycle_id: UUID,
    config_version_id: UUID,
    stage_code: str,
    observed_on: date,
    crop_status: str,
    client_entry_id: UUID,
    captured_at_client,
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.daily_stage_observations (
            crop_cycle_id, config_version_id, stage_code, observed_on,
            crop_status, client_entry_id, captured_at_client
        )
        VALUES (
            :crop_cycle_id, :config_version_id, :stage_code, :observed_on,
            :crop_status, :client_entry_id, :captured_at_client
        )
        ON CONFLICT (crop_cycle_id, stage_code, observed_on)
        DO UPDATE SET
            crop_status = EXCLUDED.crop_status,
            captured_at_client = EXCLUDED.captured_at_client,
            updated_at = now()
        RETURNING
            daily_observation_id, crop_cycle_id, config_version_id, stage_code,
            observed_on, crop_status, client_entry_id, sync_source,
            captured_at_client, created_at, updated_at;
        """,
        {
            "crop_cycle_id": crop_cycle_id,
            "config_version_id": config_version_id,
            "stage_code": stage_code,
            "observed_on": observed_on,
            "crop_status": crop_status,
            "client_entry_id": client_entry_id,
            "captured_at_client": captured_at_client,
        },
    )


def get_daily_observation(daily_observation_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            daily_observation_id, crop_cycle_id, config_version_id, stage_code,
            observed_on, crop_status, client_entry_id, sync_source,
            captured_at_client, created_at, updated_at
        FROM crop_observation.daily_stage_observations
        WHERE daily_observation_id = :daily_observation_id;
        """,
        {"daily_observation_id": daily_observation_id},
    )


def get_daily_observation_by_key(
    crop_cycle_id: UUID,
    stage_code: str,
    observed_on: date,
) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            daily_observation_id, crop_cycle_id, config_version_id, stage_code,
            observed_on, crop_status, client_entry_id, sync_source,
            captured_at_client, created_at, updated_at
        FROM crop_observation.daily_stage_observations
        WHERE crop_cycle_id = :crop_cycle_id
          AND stage_code = :stage_code
          AND observed_on = :observed_on;
        """,
        {"crop_cycle_id": crop_cycle_id, "stage_code": stage_code, "observed_on": observed_on},
    )


# ---------------------------------------------------------------------------
# Practice observations
# ---------------------------------------------------------------------------


def upsert_practice_observation(
    *,
    daily_observation_id: UUID,
    stage_practice_id: UUID,
    practice_code: str,
    answers: dict[str, Any],
    client_entry_id: UUID,
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.practice_observations (
            daily_observation_id, stage_practice_id, practice_code,
            answers, client_entry_id
        )
        VALUES (
            :daily_observation_id, :stage_practice_id, :practice_code,
            CAST(:answers AS jsonb), :client_entry_id
        )
        ON CONFLICT (daily_observation_id, practice_code)
        DO UPDATE SET
            answers = EXCLUDED.answers,
            client_entry_id = EXCLUDED.client_entry_id,
            updated_at = now()
        RETURNING
            practice_observation_id, daily_observation_id, stage_practice_id,
            practice_code, answers, completion_status, client_entry_id,
            created_at, updated_at;
        """,
        {
            "daily_observation_id": daily_observation_id,
            "stage_practice_id": stage_practice_id,
            "practice_code": practice_code,
            "answers": json.dumps(answers),
            "client_entry_id": client_entry_id,
        },
    )


def get_practice_observation(practice_observation_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            practice_observation_id, daily_observation_id, stage_practice_id,
            practice_code, answers, completion_status, client_entry_id,
            created_at, updated_at
        FROM crop_observation.practice_observations
        WHERE practice_observation_id = :practice_observation_id;
        """,
        {"practice_observation_id": practice_observation_id},
    )


def list_practice_observations_for_daily(daily_observation_id: UUID) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT
            practice_observation_id, daily_observation_id, stage_practice_id,
            practice_code, answers, completion_status, client_entry_id,
            created_at, updated_at
        FROM crop_observation.practice_observations
        WHERE daily_observation_id = :daily_observation_id
        ORDER BY created_at;
        """,
        {"daily_observation_id": daily_observation_id},
    )


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


def list_recent_daily_observations(
    crop_cycle_id: UUID,
    *,
    before: date | None,
    limit: int,
) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT
            daily_observation_id, stage_code, observed_on, crop_status,
            created_at, updated_at
        FROM crop_observation.daily_stage_observations
        WHERE crop_cycle_id = :crop_cycle_id
          AND (:before IS NULL OR observed_on < :before)
        ORDER BY observed_on DESC
        LIMIT :limit;
        """,
        {"crop_cycle_id": crop_cycle_id, "before": before, "limit": limit},
    )


# ---------------------------------------------------------------------------
# Media
# ---------------------------------------------------------------------------


def count_owner_media(owner_type: str, owner_id: UUID, media_role: str) -> int:
    rows = _run(
        """
        SELECT COUNT(*) AS media_count
        FROM crop_observation.observation_media om
        JOIN crop_observation.media_assets ma ON ma.media_asset_id = om.media_asset_id
        WHERE om.owner_type = :owner_type
          AND om.owner_id = :owner_id
          AND om.media_role = :media_role
          AND ma.upload_status != 'DELETED';
        """,
        {"owner_type": owner_type, "owner_id": owner_id, "media_role": media_role},
    )
    return int(rows[0]["media_count"]) if rows else 0


def create_media_asset(
    *,
    owner_user_id: UUID,
    bucket_name: str,
    object_key: str,
    media_type: str,
    mime_type: str,
    byte_size: int,
    duration_seconds: float | None,
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.media_assets (
            owner_user_id, bucket_name, object_key, media_type, mime_type,
            byte_size, duration_seconds, upload_status
        )
        VALUES (
            :owner_user_id, :bucket_name, :object_key, :media_type, :mime_type,
            :byte_size, :duration_seconds, 'REQUESTED'
        )
        RETURNING
            media_asset_id, owner_user_id, bucket_name, object_key, media_type,
            mime_type, byte_size, duration_seconds, checksum_sha256,
            upload_status, created_at, uploaded_at, verified_at;
        """,
        {
            "owner_user_id": owner_user_id,
            "bucket_name": bucket_name,
            "object_key": object_key,
            "media_type": media_type,
            "mime_type": mime_type,
            "byte_size": byte_size,
            "duration_seconds": duration_seconds,
        },
    )


def get_media_asset(media_asset_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            media_asset_id, owner_user_id, bucket_name, object_key, media_type,
            mime_type, byte_size, duration_seconds, checksum_sha256,
            upload_status, created_at, uploaded_at, verified_at
        FROM crop_observation.media_assets
        WHERE media_asset_id = :media_asset_id;
        """,
        {"media_asset_id": media_asset_id},
    )


def mark_media_ready(media_asset_id: UUID) -> dict[str, Any] | None:
    return _run_write(
        """
        UPDATE crop_observation.media_assets
        SET upload_status = 'READY', uploaded_at = now(), verified_at = now()
        WHERE media_asset_id = :media_asset_id
        RETURNING
            media_asset_id, owner_user_id, bucket_name, object_key, media_type,
            mime_type, byte_size, duration_seconds, checksum_sha256,
            upload_status, created_at, uploaded_at, verified_at;
        """,
        {"media_asset_id": media_asset_id},
    )


def create_observation_media(
    *,
    owner_type: str,
    owner_id: UUID,
    media_asset_id: UUID,
    media_role: str,
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.observation_media (
            owner_type, owner_id, media_asset_id, media_role
        )
        VALUES (:owner_type, :owner_id, :media_asset_id, :media_role)
        RETURNING observation_media_id, owner_type, owner_id, media_asset_id, media_role;
        """,
        {
            "owner_type": owner_type,
            "owner_id": owner_id,
            "media_asset_id": media_asset_id,
            "media_role": media_role,
        },
    )


def list_media_for_owner(owner_type: str, owner_id: UUID) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT
            om.media_role, om.owner_id, ma.media_asset_id, ma.media_type, ma.mime_type,
            ma.upload_status, ma.duration_seconds
        FROM crop_observation.observation_media om
        JOIN crop_observation.media_assets ma ON ma.media_asset_id = om.media_asset_id
        WHERE om.owner_type = :owner_type
          AND om.owner_id = :owner_id
          AND ma.upload_status != 'DELETED'
        ORDER BY ma.created_at;
        """,
        {"owner_type": owner_type, "owner_id": owner_id},
    )


def list_media_for_owners(owner_type: str, owner_ids: list[UUID]) -> list[dict[str, Any]]:
    """Batched version of list_media_for_owner — one round trip for every
    row in a history page instead of one query per row (see history_service)."""
    if not owner_ids:
        return []
    return _run(
        """
        SELECT
            om.media_role, om.owner_id, ma.media_asset_id, ma.media_type, ma.mime_type,
            ma.upload_status, ma.duration_seconds
        FROM crop_observation.observation_media om
        JOIN crop_observation.media_assets ma ON ma.media_asset_id = om.media_asset_id
        WHERE om.owner_type = :owner_type
          AND om.owner_id = ANY(:owner_ids)
          AND ma.upload_status != 'DELETED'
        ORDER BY ma.created_at;
        """,
        {"owner_type": owner_type, "owner_ids": owner_ids},
    )


def list_option_labels_for_stage_practice(stage_practice_id: UUID) -> list[dict[str, Any]]:
    """field_code/option_code/locale/label for every option on every field of
    one practice, in a single query — used to build the "translate raw codes
    into the farmer's language for the history summary line" lookup without
    the field-by-field, option-by-option N+1 that used to back it."""
    return _run(
        """
        SELECT
            fd.field_code,
            fo.option_code,
            fot.locale,
            fot.label
        FROM crop_observation.practice_field_definitions fd
        JOIN crop_observation.practice_field_options fo
            ON fo.field_definition_id = fd.field_definition_id AND fo.is_active = true
        JOIN crop_observation.practice_field_option_translations fot
            ON fot.field_option_id = fo.field_option_id
        WHERE fd.stage_practice_id = :stage_practice_id AND fd.is_enabled = true;
        """,
        {"stage_practice_id": stage_practice_id},
    )


# ---------------------------------------------------------------------------
# System media — admin-curated crop card images, stage images and
# per-locale instruction audio. Populated by scripts/sync_system_media.py
# from media_manifest.json; read-only here.
# ---------------------------------------------------------------------------


def get_system_media_asset(asset_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT asset_id, asset_type, object_key, mime_type, byte_size
        FROM crop_observation.system_media_assets
        WHERE asset_id = :asset_id AND is_active = true;
        """,
        {"asset_id": asset_id},
    )


def get_crop_card_image(crop_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT asset_id, mime_type
        FROM crop_observation.system_media_assets
        WHERE crop_id = :crop_id AND asset_type = 'CROP_CARD_IMAGE' AND is_active = true
        ORDER BY created_at DESC
        LIMIT 1;
        """,
        {"crop_id": crop_id},
    )


def get_stage_image(stage_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT asset_id, mime_type
        FROM crop_observation.system_media_assets
        WHERE stage_id = :stage_id AND asset_type = 'STAGE_IMAGE' AND is_active = true
        ORDER BY created_at DESC
        LIMIT 1;
        """,
        {"stage_id": stage_id},
    )


def get_stage_instruction_audio(stage_id: UUID, *, locale: str) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT asset_id, mime_type, duration_seconds
        FROM crop_observation.system_media_assets
        WHERE stage_id = :stage_id
          AND asset_type = 'STAGE_INSTRUCTION_AUDIO'
          AND locale = :locale
          AND is_active = true
        ORDER BY created_at DESC
        LIMIT 1;
        """,
        {"stage_id": stage_id, "locale": locale},
    )


# ---------------------------------------------------------------------------
# Per-practice history — compact "previous entries" rows shown above the
# new-entry form for a single practice (see PracticeSheet.jsx).
# ---------------------------------------------------------------------------


def list_practice_history(
    *,
    crop_cycle_id: UUID,
    stage_code: str,
    practice_code: str,
    limit: int,
) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT
            po.practice_observation_id,
            po.answers,
            po.created_at,
            dso.observed_on
        FROM crop_observation.practice_observations po
        JOIN crop_observation.daily_stage_observations dso
            ON dso.daily_observation_id = po.daily_observation_id
        WHERE dso.crop_cycle_id = :crop_cycle_id
          AND dso.stage_code = :stage_code
          AND po.practice_code = :practice_code
        ORDER BY dso.observed_on DESC, po.created_at DESC
        LIMIT :limit;
        """,
        {
            "crop_cycle_id": crop_cycle_id,
            "stage_code": stage_code,
            "practice_code": practice_code,
            "limit": limit,
        },
    )


# ---------------------------------------------------------------------------
# Review flags (SERIOUS_PROBLEM auditing)
# ---------------------------------------------------------------------------


def create_review_flag(
    *,
    farmer_user_id: UUID,
    farm_id: UUID,
    crop_cycle_id: UUID,
    source_type: str,
    source_id: UUID,
    flag_type: str,
    priority: str,
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.review_flags (
            farmer_user_id, farm_id, crop_cycle_id, source_type, source_id,
            flag_type, priority
        )
        VALUES (
            :farmer_user_id, :farm_id, :crop_cycle_id, :source_type, :source_id,
            :flag_type, :priority
        )
        RETURNING review_flag_id, status;
        """,
        {
            "farmer_user_id": farmer_user_id,
            "farm_id": farm_id,
            "crop_cycle_id": crop_cycle_id,
            "source_type": source_type,
            "source_id": source_id,
            "flag_type": flag_type,
            "priority": priority,
        },
    )
