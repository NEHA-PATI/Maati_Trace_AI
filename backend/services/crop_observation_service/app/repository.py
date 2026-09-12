from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from services.crop_observation_service.app.errors import CropObservationError, CropObservationRepositoryError
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


def pick_names_strict(
    translations: list[dict[str, Any]], locale: str
) -> tuple[str | None, None]:
    """Pick only the requested farmer language; never silently mix locales."""
    value = next(
        (row.get("display_name") for row in translations if row.get("locale") == locale),
        None,
    )
    if not value:
        raise CropObservationError(
            "TRANSLATION_NOT_AVAILABLE",
            "This crop content is not available in the selected language.",
            409,
        )
    return value, None


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
        SELECT DISTINCT ON (smb.target_id)
            smb.target_id AS crop_id, sma.asset_id
        FROM crop_observation.system_media_bindings smb
        JOIN crop_observation.system_media_assets sma
          ON sma.asset_id = smb.asset_id
        WHERE smb.target_type = 'CROP'
          AND smb.asset_role = 'CROP_CARD_IMAGE'
          AND smb.target_id = ANY(:crop_ids)
          AND smb.is_active = true
          AND sma.upload_status = 'READY'
        ORDER BY smb.target_id, smb.created_at DESC;
        """,
        {"crop_ids": [row["crop_id"] for row in crops]},
    )
    image_by_crop = {row["crop_id"]: row["asset_id"] for row in images}

    # Legacy fallback during the binding migration.
    missing_crop_ids = [row["crop_id"] for row in crops if row["crop_id"] not in image_by_crop]
    if missing_crop_ids:
        legacy_images = _run(
            """
            SELECT DISTINCT ON (crop_id) crop_id, asset_id
            FROM crop_observation.system_media_assets
            WHERE crop_id = ANY(:crop_ids)
              AND asset_type = 'CROP_CARD_IMAGE'
              AND is_active = true
              AND upload_status = 'READY'
            ORDER BY crop_id, created_at DESC;
            """,
            {"crop_ids": missing_crop_ids},
        )
        image_by_crop.update({row["crop_id"]: row["asset_id"] for row in legacy_images})

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
    return pick_names_strict(translations, locale)


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


def get_stage(stage_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT stage_id, config_version_id, stage_code, display_order, is_initial, is_enabled
        FROM crop_observation.crop_stages
        WHERE stage_id = :stage_id;
        """,
        {"stage_id": stage_id},
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
    return pick_names_strict(translations, locale)


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
            sp.media_config,
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

        option_media = _run(
            """
            SELECT DISTINCT ON (smb.target_id)
                smb.target_id, sma.asset_id
            FROM crop_observation.system_media_bindings smb
            JOIN crop_observation.system_media_assets sma ON sma.asset_id = smb.asset_id
            WHERE smb.target_type = 'FIELD_OPTION'
              AND smb.asset_role = 'OPTION_IMAGE'
              AND smb.target_id = ANY(:ids)
              AND smb.is_active = true
              AND sma.upload_status = 'READY'
            ORDER BY smb.target_id, smb.created_at DESC;
            """,
            {"ids": [o["field_option_id"] for o in options]},
        )
        option_media_by_id = {row["target_id"]: row["asset_id"] for row in option_media}
        for field_options in options_by_field.values():
            for option in field_options:
                asset_id = option_media_by_id.get(option["field_option_id"])
                option["image_url"] = (
                    f"/v1/crop-observations/system-media/{asset_id}/content" if asset_id else None
                )

    guides = _run(
        """
        SELECT sma.asset_id
        FROM crop_observation.system_media_bindings smb
        JOIN crop_observation.system_media_assets sma ON sma.asset_id = smb.asset_id
        WHERE smb.target_type = 'STAGE_PRACTICE'
          AND smb.target_id = ANY(:ids)
          AND smb.asset_role = 'PRACTICE_GUIDE_IMAGE'
          AND smb.is_active = true
          AND sma.upload_status = 'READY'
        ORDER BY smb.created_at DESC;
        """,
        {"ids": stage_practice_ids},
    )
    guide_by_practice = {row["target_id"]: row["asset_id"] for row in guides}
    for practice in practices:
        asset_id = guide_by_practice.get(practice["stage_practice_id"])
        practice["guide_image_url"] = (
            f"/v1/crop-observations/system-media/{asset_id}/content" if asset_id else None
        )

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


def record_cycle_stage(crop_cycle_id: UUID, stage_code: str, *, source: str, changed_by_user_id: UUID | None) -> None:
    """Move the operational stage and preserve an effective-date history."""
    with engine.begin() as conn:
        current = conn.execute(
            text("SELECT current_stage_code FROM crop_observation.crop_cycles WHERE crop_cycle_id = :id FOR UPDATE;"),
            {"id": crop_cycle_id},
        ).mappings().first()
        if current is None:
            return
        if current["current_stage_code"] == stage_code:
            history = conn.execute(
                text("SELECT 1 FROM crop_observation.crop_stage_history WHERE crop_cycle_id = :id LIMIT 1;"),
                {"id": crop_cycle_id},
            ).first()
            if history:
                return
        conn.execute(
            text("""
                UPDATE crop_observation.crop_stage_history
                SET effective_until = CURRENT_DATE
                WHERE crop_cycle_id = :id AND effective_until IS NULL;
            """),
            {"id": crop_cycle_id},
        )
        conn.execute(
            text("""
                INSERT INTO crop_observation.crop_stage_history
                    (crop_cycle_id, stage_code, effective_from, source, changed_by_user_id)
                VALUES (:id, :stage_code, CURRENT_DATE, :source, :user_id);
            """),
            {"id": crop_cycle_id, "stage_code": stage_code, "source": source, "user_id": changed_by_user_id},
        )
        conn.execute(
            text("""
                UPDATE crop_observation.crop_cycles
                SET current_stage_code = :stage_code,
                    current_stage_source = :source,
                    updated_at = now()
                WHERE crop_cycle_id = :id;
            """),
            {"id": crop_cycle_id, "stage_code": stage_code, "source": source},
        )


# ---------------------------------------------------------------------------
# Stage practice lookup (for dynamic validation)
# ---------------------------------------------------------------------------


def get_stage_practice_by_code(stage_id: UUID, practice_code: str) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT sp.stage_practice_id, sp.practice_template_id, sp.media_config, pt.practice_code
        FROM crop_observation.stage_practices sp
        JOIN crop_observation.practice_templates pt
            ON pt.practice_template_id = sp.practice_template_id
        WHERE sp.stage_id = :stage_id
          AND pt.practice_code = :practice_code
          AND sp.is_enabled = true;
        """,
        {"stage_id": stage_id, "practice_code": practice_code},
    )


def get_stage_practice(stage_practice_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT stage_practice_id, stage_id, practice_template_id, media_config, availability_scope, display_order
        FROM crop_observation.stage_practices
        WHERE stage_practice_id = :stage_practice_id;
        """,
        {"stage_practice_id": stage_practice_id},
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


def create_outbox_event(
    *,
    aggregate_type: str,
    aggregate_id: UUID,
    event_type: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    return _run_write(
        """
        INSERT INTO crop_observation.outbox_events
            (aggregate_type, aggregate_id, event_type, payload)
        VALUES (:aggregate_type, :aggregate_id, :event_type, CAST(:payload AS jsonb))
        RETURNING event_id, aggregate_type, aggregate_id, event_type, event_version,
                  payload, status, created_at, published_at;
        """,
        {
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "event_type": event_type,
            "payload": json.dumps(payload, default=str),
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


def cleanup_expired_media_requests(owner_type: str, owner_id: UUID) -> int:
    """Release slots reserved by abandoned upload tickets.

    A browser may request a presigned/local upload URL and then close before
    uploading. Those REQUESTED rows must not permanently consume one of the
    farmer's two image slots. The physical object, if any, is intentionally
    not deleted here; the maintenance script handles orphan cleanup safely.
    """
    row = _run_write(
        """
        WITH expired AS (
            SELECT ma.media_asset_id
            FROM crop_observation.media_assets ma
            JOIN crop_observation.observation_media om
              ON om.media_asset_id = ma.media_asset_id
            WHERE om.owner_type = :owner_type
              AND om.owner_id = :owner_id
              AND ma.upload_status = 'REQUESTED'
              AND COALESCE(
                    ma.upload_expires_at,
                    ma.created_at + interval '15 minutes'
                  ) <= now()
        ),
        removed AS (
            DELETE FROM crop_observation.observation_media om
            USING expired e
            WHERE om.media_asset_id = e.media_asset_id
            RETURNING om.media_asset_id
        )
        UPDATE crop_observation.media_assets ma
        SET upload_status = 'REJECTED', updated_at = now()
        FROM expired e
        WHERE ma.media_asset_id = e.media_asset_id
        RETURNING ma.media_asset_id;
        """,
        {"owner_type": owner_type, "owner_id": owner_id},
    )
    return 1 if row else 0


def count_owner_media_by_purpose(owner_type: str, owner_id: UUID, media_role: str, media_purpose: str) -> int:
    rows = _run(
        """
        SELECT COUNT(*) AS media_count
        FROM crop_observation.observation_media om
        JOIN crop_observation.media_assets ma ON ma.media_asset_id = om.media_asset_id
        WHERE om.owner_type = :owner_type
          AND om.owner_id = :owner_id
          AND om.media_role = :media_role
          AND om.media_purpose = :media_purpose
          AND (
                ma.upload_status IN ('UPLOADED', 'VERIFIED', 'READY')
                OR (
                    ma.upload_status = 'REQUESTED'
                    AND COALESCE(
                        ma.upload_expires_at,
                        ma.created_at + interval '15 minutes'
                    ) > now()
                )
              );
        """,
        {
            "owner_type": owner_type,
            "owner_id": owner_id,
            "media_role": media_role,
            "media_purpose": media_purpose,
        },
    )
    return int(rows[0]["media_count"]) if rows else 0


def next_owner_media_slot(owner_type: str, owner_id: UUID, media_role: str, media_purpose: str) -> int:
    rows = _run(
        """
        SELECT COALESCE(MAX(om.slot_number), 0) + 1 AS next_slot
        FROM crop_observation.observation_media om
        JOIN crop_observation.media_assets ma ON ma.media_asset_id = om.media_asset_id
        WHERE om.owner_type = :owner_type
          AND om.owner_id = :owner_id
          AND om.media_role = :media_role
          AND om.media_purpose = :media_purpose
          AND (
                ma.upload_status IN ('UPLOADED', 'VERIFIED', 'READY')
                OR (
                    ma.upload_status = 'REQUESTED'
                    AND COALESCE(
                        ma.upload_expires_at,
                        ma.created_at + interval '15 minutes'
                    ) > now()
                )
              );
        """,
        {
            "owner_type": owner_type,
            "owner_id": owner_id,
            "media_role": media_role,
            "media_purpose": media_purpose,
        },
    )
    return int(rows[0]["next_slot"]) if rows else 1


def create_media_asset(
    *,
    owner_user_id: UUID,
    bucket_name: str,
    object_key: str,
    media_type: str,
    mime_type: str,
    byte_size: int,
    duration_seconds: float | None,
    storage_backend: str,
    original_filename: str | None = None,
    upload_expires_at: datetime | None = None,
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.media_assets (
            owner_user_id, bucket_name, object_key, media_type, mime_type,
            byte_size, duration_seconds, upload_status, storage_backend,
            original_filename, upload_expires_at
        )
        VALUES (
            :owner_user_id, :bucket_name, :object_key, :media_type, :mime_type,
            :byte_size, :duration_seconds, 'REQUESTED', :storage_backend,
            :original_filename, :upload_expires_at
        )
        RETURNING
            media_asset_id, owner_user_id, bucket_name, object_key, media_type,
            mime_type, byte_size, duration_seconds, checksum_sha256, upload_status,
            storage_backend, original_filename, upload_expires_at, created_at, uploaded_at, verified_at;
        """,
        {
            "owner_user_id": owner_user_id,
            "bucket_name": bucket_name,
            "object_key": object_key,
            "media_type": media_type,
            "mime_type": mime_type,
            "byte_size": byte_size,
            "duration_seconds": duration_seconds,
            "storage_backend": storage_backend,
            "original_filename": original_filename,
            "upload_expires_at": upload_expires_at,
        },
    )


def get_media_asset(media_asset_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            media_asset_id, owner_user_id, bucket_name, object_key, media_type,
            mime_type, byte_size, duration_seconds, checksum_sha256,
            upload_status, storage_backend, original_filename, upload_expires_at, updated_at,
            created_at, uploaded_at, verified_at
        FROM crop_observation.media_assets
        WHERE media_asset_id = :media_asset_id;
        """,
        {"media_asset_id": media_asset_id},
    )


def update_media_object_key(media_asset_id: UUID, object_key: str) -> dict[str, Any] | None:
    return _run_write(
        """
        UPDATE crop_observation.media_assets
        SET object_key = :object_key, updated_at = now()
        WHERE media_asset_id = :media_asset_id
          AND upload_status NOT IN ('DELETED', 'READY')
        RETURNING media_asset_id, object_key;
        """,
        {"media_asset_id": media_asset_id, "object_key": object_key},
    )


def mark_media_ready(media_asset_id: UUID, checksum_sha256: str | None = None) -> dict[str, Any] | None:
    return _run_write(
        """
        UPDATE crop_observation.media_assets
        SET upload_status = 'READY', uploaded_at = now(), verified_at = now(),
            checksum_sha256 = COALESCE(:checksum_sha256, checksum_sha256)
        WHERE media_asset_id = :media_asset_id
        RETURNING
            media_asset_id, owner_user_id, bucket_name, object_key, media_type,
            mime_type, byte_size, duration_seconds, checksum_sha256,
            upload_status, storage_backend, original_filename, upload_expires_at, updated_at,
            created_at, uploaded_at, verified_at;
        """,
        {"media_asset_id": media_asset_id, "checksum_sha256": checksum_sha256},
    )


def create_observation_media(
    *,
    owner_type: str,
    owner_id: UUID,
    media_asset_id: UUID,
    media_role: str,
    media_purpose: str,
    slot_number: int | None,
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.observation_media (
            owner_type, owner_id, media_asset_id, media_role, media_purpose, slot_number
        )
        VALUES (:owner_type, :owner_id, :media_asset_id, :media_role, :media_purpose, :slot_number)
        RETURNING observation_media_id, owner_type, owner_id, media_asset_id, media_role, media_purpose, slot_number;
        """,
        {
            "owner_type": owner_type,
            "owner_id": owner_id,
            "media_asset_id": media_asset_id,
            "media_role": media_role,
            "media_purpose": media_purpose,
            "slot_number": slot_number,
        },
    )


def list_media_for_owner(owner_type: str, owner_id: UUID) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT
            om.media_role, om.owner_id, ma.media_asset_id, ma.media_type, ma.mime_type,
            ma.upload_status, ma.duration_seconds, ma.byte_size, om.media_purpose, om.slot_number
        FROM crop_observation.observation_media om
        JOIN crop_observation.media_assets ma ON ma.media_asset_id = om.media_asset_id
        WHERE om.owner_type = :owner_type
          AND om.owner_id = :owner_id
          AND ma.upload_status != 'DELETED'
        ORDER BY ma.created_at;
        """,
        {"owner_type": owner_type, "owner_id": owner_id},
    )


def delete_media_asset(media_asset_id: UUID) -> dict[str, Any] | None:
    """Soft-delete the asset and its relationship in one transaction."""
    return _run_write(
        """
        WITH detached AS (
            DELETE FROM crop_observation.observation_media
            WHERE media_asset_id = :media_asset_id
            RETURNING media_asset_id
        )
        UPDATE crop_observation.media_assets
        SET upload_status = 'DELETED', updated_at = now()
        WHERE media_asset_id = :media_asset_id
          AND upload_status != 'DELETED'
        RETURNING media_asset_id, object_key, storage_backend, owner_user_id;
        """,
        {"media_asset_id": media_asset_id},
    )


def get_media_owner(media_asset_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT COALESCE(ds.crop_cycle_id, dp.crop_cycle_id) AS crop_cycle_id,
               om.owner_type, om.owner_id
        FROM crop_observation.observation_media om
        JOIN crop_observation.media_assets ma ON ma.media_asset_id = om.media_asset_id
        LEFT JOIN crop_observation.daily_stage_observations ds
          ON om.owner_type = 'DAILY_STAGE' AND ds.daily_observation_id = om.owner_id
        LEFT JOIN crop_observation.practice_observations po
          ON om.owner_type = 'PRACTICE' AND po.practice_observation_id = om.owner_id
        LEFT JOIN crop_observation.daily_stage_observations dp
          ON po.daily_observation_id = dp.daily_observation_id
        WHERE ma.media_asset_id = :media_asset_id;
        """,
        {"media_asset_id": media_asset_id},
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
            ma.upload_status, ma.duration_seconds, om.media_purpose, om.slot_number
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


def create_system_media_asset(
    *,
    asset_type: str,
    crop_id: UUID | None,
    stage_id: UUID | None,
    bucket_name: str,
    object_key: str,
    mime_type: str,
    byte_size: int,
    locale: str | None,
    duration_seconds: float | None,
    storage_backend: str,
    original_filename: str | None,
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.system_media_assets (
            asset_type, crop_id, stage_id, bucket_name, object_key, mime_type,
            byte_size, locale, duration_seconds, storage_backend, original_filename
        )
        VALUES (
            :asset_type, :crop_id, :stage_id, :bucket_name, :object_key, :mime_type,
            :byte_size, :locale, :duration_seconds, :storage_backend, :original_filename
        )
        RETURNING asset_id, asset_type, crop_id, stage_id, object_key, mime_type, byte_size, locale, duration_seconds;
        """,
        {
            "asset_type": asset_type,
            "crop_id": crop_id,
            "stage_id": stage_id,
            "bucket_name": bucket_name,
            "object_key": object_key,
            "mime_type": mime_type,
            "byte_size": byte_size,
            "locale": locale,
            "duration_seconds": duration_seconds,
            "storage_backend": storage_backend,
            "original_filename": original_filename,
        },
    )


def deactivate_stage_instruction_audio(stage_id: UUID, locale: str) -> None:
    _run_write(
        """
        UPDATE crop_observation.system_media_assets
        SET is_active = false
        WHERE stage_id = :stage_id
          AND locale = :locale
          AND asset_type = 'STAGE_INSTRUCTION_AUDIO'
          AND is_active = true
        RETURNING asset_id;
        """,
        {"stage_id": stage_id, "locale": locale},
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


def get_tts_profile(locale: str) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            tts_profile_id, profile_code, locale, provider, model_id, voice_id,
            voice_name, output_format, generation_config, is_active
        FROM crop_observation.tts_profiles
        WHERE locale = :locale AND is_active = true
        ORDER BY created_at DESC
        LIMIT 1;
        """,
        {"locale": locale},
    )


def list_tts_profiles() -> list[dict[str, Any]]:
    return _run(
        """
        SELECT
            tts_profile_id, profile_code, locale, provider, model_id, voice_id,
            voice_name, output_format, generation_config, is_active
        FROM crop_observation.tts_profiles
        ORDER BY locale, profile_code;
        """,
        {},
    )


def upsert_tts_profile(
    *,
    profile_code: str,
    locale: str,
    provider: str,
    model_id: str,
    voice_id: str,
    voice_name: str | None,
    output_format: dict[str, Any],
    generation_config: dict[str, Any],
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.tts_profiles (
            profile_code, locale, provider, model_id, voice_id, voice_name, output_format, generation_config
        )
        VALUES (
            :profile_code, :locale, :provider, :model_id, :voice_id, :voice_name,
            CAST(:output_format AS jsonb), CAST(:generation_config AS jsonb)
        )
        ON CONFLICT (profile_code)
        DO UPDATE SET
            locale = EXCLUDED.locale,
            provider = EXCLUDED.provider,
            model_id = EXCLUDED.model_id,
            voice_id = EXCLUDED.voice_id,
            voice_name = EXCLUDED.voice_name,
            output_format = EXCLUDED.output_format,
            generation_config = EXCLUDED.generation_config,
            updated_at = now()
        RETURNING
            tts_profile_id, profile_code, locale, provider, model_id, voice_id,
            voice_name, output_format, generation_config, is_active;
        """,
        {
            "profile_code": profile_code,
            "locale": locale,
            "provider": provider,
            "model_id": model_id,
            "voice_id": voice_id,
            "voice_name": voice_name,
            "output_format": json.dumps(output_format),
            "generation_config": json.dumps(generation_config),
        },
    )


def get_tts_generation_by_cache_key(cache_key: str) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            tts_generation_id, target_type, target_id, locale, transcript,
            profile_id, cache_key, status, system_media_asset_id, error_message
        FROM crop_observation.tts_generations
        WHERE cache_key = :cache_key;
        """,
        {"cache_key": cache_key},
    )


def upsert_tts_generation(
    *,
    target_type: str,
    target_id: UUID,
    locale: str,
    transcript: str,
    profile_id: UUID,
    cache_key: str,
    status: str,
    system_media_asset_id: UUID | None,
    error_message: str | None,
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.tts_generations (
            target_type, target_id, locale, transcript, profile_id, cache_key, status,
            system_media_asset_id, error_message
        )
        VALUES (
            :target_type, :target_id, :locale, :transcript, :profile_id, :cache_key, :status,
            :system_media_asset_id, :error_message
        )
        ON CONFLICT (cache_key)
        DO UPDATE SET
            transcript = EXCLUDED.transcript,
            profile_id = EXCLUDED.profile_id,
            status = EXCLUDED.status,
            system_media_asset_id = EXCLUDED.system_media_asset_id,
            error_message = EXCLUDED.error_message,
            updated_at = now()
        RETURNING
            tts_generation_id, target_type, target_id, locale, transcript,
            profile_id, cache_key, status, system_media_asset_id, error_message;
        """,
        {
            "target_type": target_type,
            "target_id": target_id,
            "locale": locale,
            "transcript": transcript,
            "profile_id": profile_id,
            "cache_key": cache_key,
            "status": status,
            "system_media_asset_id": system_media_asset_id,
            "error_message": error_message,
        },
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
    exclude_observed_on: date | None = None,
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
          AND (:exclude_observed_on IS NULL OR dso.observed_on <> :exclude_observed_on)
        ORDER BY dso.observed_on DESC, po.created_at DESC
        LIMIT :limit;
        """,
        {
            "crop_cycle_id": crop_cycle_id,
            "stage_code": stage_code,
            "practice_code": practice_code,
            "limit": limit,
            "exclude_observed_on": exclude_observed_on,
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

# =============================================================================
# Production-final system media / review overrides.
# These binding-first helpers intentionally supersede the legacy direct
# crop_id/stage_id media lookup functions above while preserving legacy rows as
# a fallback during migration.
# =============================================================================


def get_system_media_asset(asset_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            asset_id, asset_type, crop_id, stage_id, bucket_name, object_key,
            mime_type, byte_size, locale, duration_seconds, storage_backend,
            original_filename, is_active, upload_status, checksum_sha256,
            created_by_user_id, upload_expires_at, created_at, updated_at
        FROM crop_observation.system_media_assets
        WHERE asset_id = :asset_id
          AND upload_status = 'READY';
        """,
        {"asset_id": asset_id},
    )


def create_system_media_asset(
    *,
    asset_type: str,
    crop_id: UUID | None,
    stage_id: UUID | None,
    bucket_name: str,
    object_key: str,
    mime_type: str,
    byte_size: int,
    locale: str | None,
    duration_seconds: float | None,
    storage_backend: str,
    original_filename: str | None,
    upload_status: str = "READY",
    created_by_user_id: UUID | None = None,
    is_active: bool = True,
    upload_expires_at: datetime | None = None,
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.system_media_assets (
            asset_type, crop_id, stage_id, bucket_name, object_key, mime_type,
            byte_size, locale, duration_seconds, storage_backend,
            original_filename, upload_status, created_by_user_id, is_active,
            upload_expires_at
        )
        VALUES (
            :asset_type, :crop_id, :stage_id, :bucket_name, :object_key, :mime_type,
            :byte_size, :locale, :duration_seconds, :storage_backend,
            :original_filename, :upload_status, :created_by_user_id, :is_active,
            :upload_expires_at
        )
        RETURNING
            asset_id, asset_type, crop_id, stage_id, bucket_name, object_key,
            mime_type, byte_size, locale, duration_seconds, storage_backend,
            original_filename, upload_status, created_by_user_id, is_active,
            upload_expires_at, created_at, updated_at;
        """,
        {
            "asset_type": asset_type,
            "crop_id": crop_id,
            "stage_id": stage_id,
            "bucket_name": bucket_name,
            "object_key": object_key,
            "mime_type": mime_type,
            "byte_size": byte_size,
            "locale": locale,
            "duration_seconds": duration_seconds,
            "storage_backend": storage_backend,
            "original_filename": original_filename,
            "upload_status": upload_status,
            "created_by_user_id": created_by_user_id,
            "is_active": is_active,
            "upload_expires_at": upload_expires_at,
        },
    )


def mark_system_media_ready(asset_id: UUID, checksum_sha256: str | None = None) -> dict[str, Any] | None:
    return _run_write(
        """
        UPDATE crop_observation.system_media_assets
        SET upload_status = 'READY', is_active = true,
            checksum_sha256 = COALESCE(:checksum_sha256, checksum_sha256), updated_at = now()
        WHERE asset_id = :asset_id
        RETURNING
            asset_id, asset_type, crop_id, stage_id, bucket_name, object_key,
            mime_type, byte_size, locale, duration_seconds, storage_backend,
            original_filename, upload_status, created_by_user_id, is_active,
            upload_expires_at, created_at, updated_at;
        """,
        {"asset_id": asset_id, "checksum_sha256": checksum_sha256},
    )


def get_system_media_asset_any_status(asset_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            asset_id, asset_type, crop_id, stage_id, bucket_name, object_key,
            mime_type, byte_size, locale, duration_seconds, storage_backend,
            original_filename, is_active, upload_status, checksum_sha256,
            created_by_user_id, upload_expires_at, created_at, updated_at
        FROM crop_observation.system_media_assets
        WHERE asset_id = :asset_id;
        """,
        {"asset_id": asset_id},
    )


def activate_system_media_binding(
    *,
    asset_id: UUID,
    target_type: str,
    target_id: UUID,
    asset_role: str,
    locale: str | None,
    slot_number: int | None = None,
) -> dict[str, Any]:
    """Atomically replace the active logical binding for the target/role."""
    params = {
        "asset_id": asset_id,
        "target_type": target_type,
        "target_id": target_id,
        "asset_role": asset_role,
        "locale": locale,
        "slot_number": slot_number,
    }
    # Separate the replacement from the insert. A data-modifying CTE can
    # still hit the partial unique index while replacing an active binding.
    _run_write(
        """
        UPDATE crop_observation.system_media_bindings
        SET is_active = false
        WHERE target_type = :target_type
          AND target_id = :target_id
          AND asset_role = :asset_role
          AND COALESCE(locale, '') = COALESCE(:locale, '')
          AND COALESCE(slot_number, -1) = COALESCE(:slot_number, -1)
          AND is_active = true;
        """,
        params,
    )
    return _run_write(
        """
        INSERT INTO crop_observation.system_media_bindings (
            asset_id, target_type, target_id, asset_role, locale, slot_number, is_active
        )
        VALUES (
            :asset_id, :target_type, :target_id, :asset_role, :locale, :slot_number, true
        )
        RETURNING binding_id, asset_id, target_type, target_id, asset_role,
                  locale, slot_number, is_active, created_at;
        """,
        params,
    )


def deactivate_system_media_binding(binding_id: UUID) -> dict[str, Any] | None:
    return _run_write(
        """
        UPDATE crop_observation.system_media_bindings
        SET is_active = false
        WHERE binding_id = :binding_id AND is_active = true
        RETURNING binding_id, asset_id, target_type, target_id, asset_role,
                  locale, slot_number, is_active, created_at;
        """,
        {"binding_id": binding_id},
    )


def get_system_media_binding(binding_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT binding_id, asset_id, target_type, target_id, asset_role,
               locale, slot_number, is_active
        FROM crop_observation.system_media_bindings
        WHERE binding_id = :binding_id;
        """,
        {"binding_id": binding_id},
    )


def list_system_media_bindings(
    *,
    target_type: str | None = None,
    target_id: UUID | None = None,
    asset_role: str | None = None,
    locale: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT
            smb.binding_id, smb.asset_id, smb.target_type, smb.target_id,
            smb.asset_role, smb.locale, smb.slot_number, smb.is_active,
            sma.mime_type, sma.byte_size, sma.duration_seconds,
            sma.storage_backend, sma.object_key, sma.upload_status,
            sma.original_filename, sma.created_at
        FROM crop_observation.system_media_bindings smb
        JOIN crop_observation.system_media_assets sma ON sma.asset_id = smb.asset_id
        WHERE smb.is_active = true
          AND sma.upload_status = 'READY'
          AND (:target_type IS NULL OR smb.target_type = :target_type)
          AND (:target_id IS NULL OR smb.target_id = :target_id)
          AND (:asset_role IS NULL OR smb.asset_role = :asset_role)
          AND (:locale IS NULL OR smb.locale = :locale)
        ORDER BY sma.created_at DESC
        LIMIT :limit;
        """,
        {
            "target_type": target_type,
            "target_id": target_id,
            "asset_role": asset_role,
            "locale": locale,
            "limit": limit,
        },
    )


def _get_bound_asset(
    *,
    target_type: str,
    target_id: UUID,
    asset_role: str,
    locale: str | None = None,
) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            sma.asset_id, sma.mime_type, sma.duration_seconds,
            sma.storage_backend, sma.object_key
        FROM crop_observation.system_media_bindings smb
        JOIN crop_observation.system_media_assets sma ON sma.asset_id = smb.asset_id
        WHERE smb.target_type = :target_type
          AND smb.target_id = :target_id
          AND smb.asset_role = :asset_role
          AND COALESCE(smb.locale, '') = COALESCE(:locale, '')
          AND smb.is_active = true
          AND sma.upload_status = 'READY'
        ORDER BY smb.created_at DESC
        LIMIT 1;
        """,
        {
            "target_type": target_type,
            "target_id": target_id,
            "asset_role": asset_role,
            "locale": locale,
        },
    )


def get_crop_card_image(crop_id: UUID) -> dict[str, Any] | None:
    bound = _get_bound_asset(
        target_type="CROP",
        target_id=crop_id,
        asset_role="CROP_CARD_IMAGE",
    )
    if bound:
        return bound
    return _run_one(
        """
        SELECT asset_id, mime_type, storage_backend, object_key
        FROM crop_observation.system_media_assets
        WHERE crop_id = :crop_id
          AND asset_type = 'CROP_CARD_IMAGE'
          AND is_active = true
          AND upload_status = 'READY'
        ORDER BY created_at DESC LIMIT 1;
        """,
        {"crop_id": crop_id},
    )


def get_stage_image(stage_id: UUID) -> dict[str, Any] | None:
    bound = _get_bound_asset(
        target_type="STAGE",
        target_id=stage_id,
        asset_role="STAGE_IMAGE",
    )
    if bound:
        return bound
    return _run_one(
        """
        SELECT asset_id, mime_type, storage_backend, object_key
        FROM crop_observation.system_media_assets
        WHERE stage_id = :stage_id
          AND asset_type = 'STAGE_IMAGE'
          AND is_active = true
          AND upload_status = 'READY'
        ORDER BY created_at DESC LIMIT 1;
        """,
        {"stage_id": stage_id},
    )


def get_stage_instruction_audio(stage_id: UUID, *, locale: str) -> dict[str, Any] | None:
    bound = _get_bound_asset(
        target_type="STAGE",
        target_id=stage_id,
        asset_role="INSTRUCTION_AUDIO",
        locale=locale,
    )
    if bound:
        return bound
    return _run_one(
        """
        SELECT asset_id, mime_type, duration_seconds, storage_backend, object_key
        FROM crop_observation.system_media_assets
        WHERE stage_id = :stage_id
          AND asset_type = 'STAGE_INSTRUCTION_AUDIO'
          AND locale = :locale
          AND is_active = true
          AND upload_status = 'READY'
        ORDER BY created_at DESC LIMIT 1;
        """,
        {"stage_id": stage_id, "locale": locale},
    )


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
            flag_type, priority, status
        )
        VALUES (
            :farmer_user_id, :farm_id, :crop_cycle_id, :source_type, :source_id,
            :flag_type, :priority, 'OPEN'
        )
        ON CONFLICT (source_type, source_id, flag_type) WHERE status = 'OPEN'
        DO UPDATE SET priority = EXCLUDED.priority
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


def get_practice_observation_by_daily_code(
    daily_observation_id: UUID,
    practice_code: str,
) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            practice_observation_id, daily_observation_id, stage_practice_id,
            practice_code, answers, completion_status, client_entry_id,
            created_at, updated_at
        FROM crop_observation.practice_observations
        WHERE daily_observation_id = :daily_observation_id
          AND practice_code = :practice_code;
        """,
        {"daily_observation_id": daily_observation_id, "practice_code": practice_code},
    )


def create_observation_revision(
    *,
    observation_type: str,
    observation_id: UUID,
    previous_payload: dict[str, Any] | None,
    new_payload: dict[str, Any],
    changed_by_user_id: UUID,
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.observation_revisions (
            observation_type, observation_id, revision_number,
            previous_payload, new_payload, changed_by_user_id
        )
        SELECT
            :observation_type,
            :observation_id,
            COALESCE(MAX(revision_number), 0) + 1,
            CAST(:previous_payload AS jsonb),
            CAST(:new_payload AS jsonb),
            :changed_by_user_id
        FROM crop_observation.observation_revisions
        WHERE observation_type = :observation_type
          AND observation_id = :observation_id
        RETURNING revision_id, observation_type, observation_id,
                  revision_number, previous_payload, new_payload,
                  changed_by_user_id, changed_at;
        """,
        {
            "observation_type": observation_type,
            "observation_id": observation_id,
            "previous_payload": json.dumps(previous_payload) if previous_payload is not None else None,
            "new_payload": json.dumps(new_payload),
            "changed_by_user_id": changed_by_user_id,
        },
    )


def deactivate_system_media_for_target(
    *,
    target_type: str,
    target_id: UUID,
    asset_role: str,
    locale: str | None = None,
) -> int:
    """Deactivate active logical bindings without deleting the physical asset."""
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text(
                    """
                    UPDATE crop_observation.system_media_bindings
                    SET is_active = false
                    WHERE target_type = :target_type
                      AND target_id = :target_id
                      AND asset_role = :asset_role
                      AND COALESCE(locale, '') = COALESCE(:locale, '')
                      AND is_active = true;
                    """
                ),
                {
                    "target_type": target_type,
                    "target_id": target_id,
                    "asset_role": asset_role,
                    "locale": locale,
                },
            )
            return int(result.rowcount or 0)
    except SQLAlchemyError as exc:
        raise CropObservationRepositoryError(str(exc)) from exc
