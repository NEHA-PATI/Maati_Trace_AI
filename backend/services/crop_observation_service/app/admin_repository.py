from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine
from services.crop_observation_service.app.errors import CropObservationRepositoryError

VALID_FIELD_TYPES = (
    "BOOLEAN",
    "YES_NO_UNKNOWN",
    "SINGLE_CHOICE",
    "MULTI_CHOICE",
    "PICTURE_CHOICE",
    "SEVERITY",
    "QUANTITY_UNIT",
    "NUMBER",
    "SHORT_TEXT",
    "PRODUCT",
    "PEST",
    "DISEASE",
    "APPLICATION_AREA",
)


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


def _exec_write(query, params: dict[str, Any]) -> None:
    try:
        with engine.begin() as conn:
            conn.execute(text(query), params)
    except SQLAlchemyError as exc:
        raise CropObservationRepositoryError(str(exc)) from exc


# ---------------------------------------------------------------------------
# Crops
# ---------------------------------------------------------------------------


def list_all_crops() -> list[dict[str, Any]]:
    rows = [dict(row) for row in _run(
        """
        SELECT crop_id, crop_code, lifecycle_type, default_stage_strategy,
               is_active, display_order
        FROM crop_observation.crops
        ORDER BY display_order;
        """,
        {},
    )]
    if rows:
        translations = _run(
            "SELECT crop_id, locale, display_name, short_description FROM crop_observation.crop_translations WHERE crop_id = ANY(:ids);",
            {"ids": [row["crop_id"] for row in rows]},
        )
        by_id = {}
        for item in translations:
            by_id.setdefault(item["crop_id"], []).append(dict(item))
        for row in rows:
            row["translations"] = by_id.get(row["crop_id"], [])
    return rows


def create_crop(
    *, crop_code: str, lifecycle_type: str, default_stage_strategy: str, display_order: int
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.crops
            (crop_code, lifecycle_type, default_stage_strategy, display_order)
        VALUES (:crop_code, :lifecycle_type, :default_stage_strategy, :display_order)
        RETURNING crop_id, crop_code, lifecycle_type, default_stage_strategy,
                  is_active, display_order;
        """,
        {
            "crop_code": crop_code,
            "lifecycle_type": lifecycle_type,
            "default_stage_strategy": default_stage_strategy,
            "display_order": display_order,
        },
    )


def update_crop(crop_code: str, fields: dict[str, Any]) -> dict[str, Any] | None:
    if not fields:
        return _run_one(
            "SELECT crop_id, crop_code, lifecycle_type, default_stage_strategy, "
            "is_active, display_order FROM crop_observation.crops WHERE crop_code = :crop_code;",
            {"crop_code": crop_code},
        )
    assignments = ", ".join(f"{key} = :{key}" for key in fields)
    return _run_write(
        f"""
        UPDATE crop_observation.crops
        SET {assignments}, updated_at = now()
        WHERE crop_code = :crop_code
        RETURNING crop_id, crop_code, lifecycle_type, default_stage_strategy,
                  is_active, display_order;
        """,
        {**fields, "crop_code": crop_code},
    )


def upsert_crop_translation(crop_id: UUID, locale: str, display_name: str, short_description: str | None) -> None:
    _exec_write(
        """
        INSERT INTO crop_observation.crop_translations (crop_id, locale, display_name, short_description)
        VALUES (:crop_id, :locale, :display_name, :short_description)
        ON CONFLICT (crop_id, locale)
        DO UPDATE SET display_name = EXCLUDED.display_name, short_description = EXCLUDED.short_description;
        """,
        {
            "crop_id": crop_id,
            "locale": locale,
            "display_name": display_name,
            "short_description": short_description,
        },
    )


# ---------------------------------------------------------------------------
# Configuration versions
# ---------------------------------------------------------------------------


def list_configurations(crop_id: UUID) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT config_version_id, crop_id, version_number, status, created_at, published_at
        FROM crop_observation.crop_config_versions
        WHERE crop_id = :crop_id
        ORDER BY version_number DESC;
        """,
        {"crop_id": crop_id},
    )


def get_configuration(config_version_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT config_version_id, crop_id, version_number, status, created_at, published_at
        FROM crop_observation.crop_config_versions
        WHERE config_version_id = :config_version_id;
        """,
        {"config_version_id": config_version_id},
    )


def next_version_number(crop_id: UUID) -> int:
    rows = _run(
        """
        SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
        FROM crop_observation.crop_config_versions
        WHERE crop_id = :crop_id;
        """,
        {"crop_id": crop_id},
    )
    return int(rows[0]["next_version"])


def create_draft_configuration(*, crop_id: UUID, version_number: int, created_by_user_id: UUID) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.crop_config_versions
            (crop_id, version_number, status, created_by_user_id)
        VALUES (:crop_id, :version_number, 'DRAFT', :created_by_user_id)
        RETURNING config_version_id, crop_id, version_number, status, created_at, published_at;
        """,
        {"crop_id": crop_id, "version_number": version_number, "created_by_user_id": created_by_user_id},
    )


def clone_configuration(
    *, source_config_version_id: UUID, crop_id: UUID, version_number: int, created_by_user_id: UUID
) -> dict[str, Any]:
    """Creates a new DRAFT config version and deep-copies stages ->
    stage_practices -> field_definitions -> options (and every translation
    table alongside them) from the source version — the version row and the
    whole copy happen in one transaction, so a failed copy never leaves an
    orphan empty draft behind."""
    try:
        with engine.begin() as conn:
            new_version = conn.execute(
                text(
                    """
                    INSERT INTO crop_observation.crop_config_versions
                        (crop_id, version_number, status, created_by_user_id)
                    VALUES (:crop_id, :version_number, 'DRAFT', :created_by_user_id)
                    RETURNING config_version_id, crop_id, version_number, status, created_at, published_at;
                    """
                ),
                {"crop_id": crop_id, "version_number": version_number, "created_by_user_id": created_by_user_id},
            ).mappings().first()
            target_config_version_id = new_version["config_version_id"]

            stage_id_map: dict[str, str] = {}
            stages = conn.execute(
                text(
                    """
                    SELECT stage_id, stage_code, display_order, is_initial, is_enabled,
                           expected_start_day, expected_end_day
                    FROM crop_observation.crop_stages
                    WHERE config_version_id = :src;
                    """
                ),
                {"src": source_config_version_id},
            ).mappings().all()

            for stage in stages:
                new_stage = conn.execute(
                    text(
                        """
                        INSERT INTO crop_observation.crop_stages
                            (config_version_id, stage_code, display_order, is_initial,
                             is_enabled, expected_start_day, expected_end_day)
                        VALUES (:cv, :stage_code, :display_order, :is_initial,
                                :is_enabled, :start_day, :end_day)
                        RETURNING stage_id;
                        """
                    ),
                    {
                        "cv": target_config_version_id,
                        "stage_code": stage["stage_code"],
                        "display_order": stage["display_order"],
                        "is_initial": stage["is_initial"],
                        "is_enabled": stage["is_enabled"],
                        "start_day": stage["expected_start_day"],
                        "end_day": stage["expected_end_day"],
                    },
                ).mappings().first()
                stage_id_map[str(stage["stage_id"])] = str(new_stage["stage_id"])

                translations = conn.execute(
                    text(
                        "SELECT locale, display_name, short_description, instruction_text "
                        "FROM crop_observation.crop_stage_translations WHERE stage_id = :sid;"
                    ),
                    {"sid": stage["stage_id"]},
                ).mappings().all()
                for tr in translations:
                    conn.execute(
                        text(
                            """
                            INSERT INTO crop_observation.crop_stage_translations
                                (stage_id, locale, display_name, short_description, instruction_text)
                            VALUES (:sid, :locale, :name, :short_desc, :instruction)
                            """
                        ),
                        {
                            "sid": new_stage["stage_id"],
                            "locale": tr["locale"],
                            "name": tr["display_name"],
                            "short_desc": tr["short_description"],
                            "instruction": tr["instruction_text"],
                        },
                    )

                # System media is immutable/reusable. Clone only the logical
                # bindings to the new stage; do not duplicate S3/local files.
                conn.execute(
                    text(
                        """
                        INSERT INTO crop_observation.system_media_bindings
                            (asset_id, target_type, target_id, asset_role, locale, slot_number, is_active)
                        SELECT asset_id, 'STAGE', :new_stage_id, asset_role, locale, slot_number, true
                        FROM crop_observation.system_media_bindings
                        WHERE target_type = 'STAGE'
                          AND target_id = :source_stage_id
                          AND is_active = true
                        ON CONFLICT DO NOTHING;
                        """
                    ),
                    {"new_stage_id": new_stage["stage_id"], "source_stage_id": stage["stage_id"]},
                )

                stage_practices = conn.execute(
                    text(
                        """
                    SELECT stage_practice_id, practice_template_id, availability_scope,
                               display_order, is_enabled, media_config
                    FROM crop_observation.stage_practices
                    WHERE stage_id = :sid;
                        """
                    ),
                    {"sid": stage["stage_id"]},
                ).mappings().all()

                for sp in stage_practices:
                    new_sp = conn.execute(
                        text(
                            """
                            INSERT INTO crop_observation.stage_practices
                                (stage_id, practice_template_id, availability_scope,
                                 display_order, is_enabled, media_config)
                            VALUES (
                                :stage_id,
                                :practice_template_id,
                                :scope,
                                :order,
                                :enabled,
                                CAST(:media_config AS jsonb)
                            )
                            RETURNING stage_practice_id;
                            """
                        ),
                        {
                            "stage_id": new_stage["stage_id"],
                            "practice_template_id": sp["practice_template_id"],
                            "scope": sp["availability_scope"],
                            "order": sp["display_order"],
                            "enabled": sp["is_enabled"],
                            "media_config": json.dumps(sp["media_config"] or {}),
                        },
                    ).mappings().first()

                    conn.execute(
                        text(
                            """
                            INSERT INTO crop_observation.system_media_bindings
                                (asset_id, target_type, target_id, asset_role, locale, slot_number, is_active)
                            SELECT asset_id, 'STAGE_PRACTICE', :new_target, asset_role, locale, slot_number, true
                            FROM crop_observation.system_media_bindings
                            WHERE target_type = 'STAGE_PRACTICE'
                              AND target_id = :source_target
                              AND is_active = true
                            ON CONFLICT DO NOTHING;
                            """
                        ),
                        {"new_target": new_sp["stage_practice_id"], "source_target": sp["stage_practice_id"]},
                    )

                    fields = conn.execute(
                        text(
                            """
                            SELECT field_definition_id, field_code, field_type, semantic_type,
                                   display_order, is_required, is_enabled, validation_config, ui_config
                            FROM crop_observation.practice_field_definitions
                            WHERE stage_practice_id = :spid;
                            """
                        ),
                        {"spid": sp["stage_practice_id"]},
                    ).mappings().all()

                    for field in fields:
                        new_field = conn.execute(
                            text(
                                """
                                INSERT INTO crop_observation.practice_field_definitions
                                    (stage_practice_id, field_code, field_type, semantic_type,
                                     display_order, is_required, is_enabled, validation_config, ui_config)
                                VALUES (:spid, :code, :type, :semantic, :order, :required, :enabled,
                                        :validation_config, :ui_config)
                                RETURNING field_definition_id;
                                """
                            ),
                            {
                                "spid": new_sp["stage_practice_id"],
                                "code": field["field_code"],
                                "type": field["field_type"],
                                "semantic": field["semantic_type"],
                                "order": field["display_order"],
                                "required": field["is_required"],
                                "enabled": field["is_enabled"],
                                "validation_config": json.dumps(field["validation_config"]),
                                "ui_config": json.dumps(field["ui_config"]),
                            },
                        ).mappings().first()

                        field_translations = conn.execute(
                            text(
                                "SELECT locale, label, help_text FROM "
                                "crop_observation.practice_field_translations WHERE field_definition_id = :fid;"
                            ),
                            {"fid": field["field_definition_id"]},
                        ).mappings().all()
                        for tr in field_translations:
                            conn.execute(
                                text(
                                    """
                                    INSERT INTO crop_observation.practice_field_translations
                                        (field_definition_id, locale, label, help_text)
                                    VALUES (:fid, :locale, :label, :help_text)
                                    """
                                ),
                                {
                                    "fid": new_field["field_definition_id"],
                                    "locale": tr["locale"],
                                    "label": tr["label"],
                                    "help_text": tr["help_text"],
                                },
                            )

                        options = conn.execute(
                            text(
                                "SELECT field_option_id, option_code, display_order, icon_key, is_active, metadata "
                                "FROM crop_observation.practice_field_options WHERE field_definition_id = :fid;"
                            ),
                            {"fid": field["field_definition_id"]},
                        ).mappings().all()
                        for option in options:
                            new_option = conn.execute(
                                text(
                                    """
                                    INSERT INTO crop_observation.practice_field_options
                                        (field_definition_id, option_code, display_order, icon_key, is_active, metadata)
                                    VALUES (:fid, :code, :order, :icon, :active, :metadata)
                                    RETURNING field_option_id;
                                    """
                                ),
                                {
                                    "fid": new_field["field_definition_id"],
                                    "code": option["option_code"],
                                    "order": option["display_order"],
                                    "icon": option["icon_key"],
                                    "active": option["is_active"],
                                    "metadata": json.dumps(option["metadata"]),
                                },
                            ).mappings().first()

                            conn.execute(
                                text(
                                    """
                                    INSERT INTO crop_observation.system_media_bindings
                                        (asset_id, target_type, target_id, asset_role, locale, slot_number, is_active)
                                    SELECT asset_id, 'FIELD_OPTION', :new_target, asset_role, locale, slot_number, true
                                    FROM crop_observation.system_media_bindings
                                    WHERE target_type = 'FIELD_OPTION'
                                      AND target_id = :source_target
                                      AND is_active = true
                                    ON CONFLICT DO NOTHING;
                                    """
                                ),
                                {"new_target": new_option["field_option_id"], "source_target": option["field_option_id"]},
                            )

                            option_translations = conn.execute(
                                text(
                                    "SELECT locale, label FROM crop_observation.practice_field_option_translations "
                                    "WHERE field_option_id = :oid;"
                                ),
                                {"oid": option["field_option_id"]},
                            ).mappings().all()
                            for tr in option_translations:
                                conn.execute(
                                    text(
                                        """
                                        INSERT INTO crop_observation.practice_field_option_translations
                                            (field_option_id, locale, label)
                                        VALUES (:oid, :locale, :label)
                                        """
                                    ),
                                    {
                                        "oid": new_option["field_option_id"],
                                        "locale": tr["locale"],
                                        "label": tr["label"],
                                    },
                                )

            return dict(new_version)
    except SQLAlchemyError as exc:
        raise CropObservationRepositoryError(str(exc)) from exc


def supersede_published_configuration(crop_id: UUID) -> None:
    _exec_write(
        """
        UPDATE crop_observation.crop_config_versions
        SET status = 'SUPERSEDED'
        WHERE crop_id = :crop_id AND status = 'PUBLISHED';
        """,
        {"crop_id": crop_id},
    )


def publish_configuration(config_version_id: UUID, *, published_by_user_id: UUID) -> dict[str, Any] | None:
    return _run_write(
        """
        UPDATE crop_observation.crop_config_versions
        SET status = 'PUBLISHED', published_at = now(), published_by_user_id = :published_by
        WHERE config_version_id = :id
        RETURNING config_version_id, crop_id, version_number, status, created_at, published_at;
        """,
        {"id": config_version_id, "published_by": published_by_user_id},
    )


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------


def list_stages_for_config(config_version_id: UUID) -> list[dict[str, Any]]:
    rows = [dict(row) for row in _run(
        """
        SELECT stage_id, config_version_id, stage_code, display_order,
               is_initial, is_enabled, expected_start_day, expected_end_day
        FROM crop_observation.crop_stages
        WHERE config_version_id = :cv
        ORDER BY display_order;
        """,
        {"cv": config_version_id},
    )]
    translations = _run(
        "SELECT stage_id, locale, display_name, short_description, instruction_text FROM crop_observation.crop_stage_translations WHERE stage_id = ANY(:ids);",
        {"ids": [row["stage_id"] for row in rows]},
    ) if rows else []
    by_id = {}
    for item in translations:
        by_id.setdefault(item["stage_id"], []).append(dict(item))
    for row in rows:
        row["translations"] = by_id.get(row["stage_id"], [])
    return rows


def get_stage(stage_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT stage_id, config_version_id, stage_code, display_order,
               is_initial, is_enabled, expected_start_day, expected_end_day
        FROM crop_observation.crop_stages
        WHERE stage_id = :stage_id;
        """,
        {"stage_id": stage_id},
    )


def create_stage(
    *, config_version_id: UUID, stage_code: str, display_order: int, is_initial: bool
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.crop_stages
            (config_version_id, stage_code, display_order, is_initial)
        VALUES (:cv, :stage_code, :display_order, :is_initial)
        RETURNING stage_id, config_version_id, stage_code, display_order,
                  is_initial, is_enabled, expected_start_day, expected_end_day;
        """,
        {
            "cv": config_version_id,
            "stage_code": stage_code,
            "display_order": display_order,
            "is_initial": is_initial,
        },
    )


def update_stage(stage_id: UUID, fields: dict[str, Any]) -> dict[str, Any] | None:
    if not fields:
        return get_stage(stage_id)
    assignments = ", ".join(f"{key} = :{key}" for key in fields)
    return _run_write(
        f"""
        UPDATE crop_observation.crop_stages
        SET {assignments}, updated_at = now()
        WHERE stage_id = :stage_id
        RETURNING stage_id, config_version_id, stage_code, display_order,
                  is_initial, is_enabled, expected_start_day, expected_end_day;
        """,
        {**fields, "stage_id": stage_id},
    )


def delete_stage(stage_id: UUID) -> None:
    _exec_write("DELETE FROM crop_observation.crop_stages WHERE stage_id = :stage_id;", {"stage_id": stage_id})


def reorder_stages(order: list[UUID]) -> None:
    try:
        with engine.begin() as conn:
            for index, stage_id in enumerate(order):
                conn.execute(
                    text(
                        "UPDATE crop_observation.crop_stages SET display_order = :order "
                        "WHERE stage_id = :stage_id;"
                    ),
                    {"order": index, "stage_id": stage_id},
                )
    except SQLAlchemyError as exc:
        raise CropObservationRepositoryError(str(exc)) from exc


def upsert_stage_translation(stage_id: UUID, locale: str, fields: dict[str, Any]) -> None:
    columns = ", ".join(fields.keys())
    placeholders = ", ".join(f":{key}" for key in fields.keys())
    updates = ", ".join(f"{key} = EXCLUDED.{key}" for key in fields.keys())
    _exec_write(
        f"""
        INSERT INTO crop_observation.crop_stage_translations (stage_id, locale, {columns})
        VALUES (:stage_id, :locale, {placeholders})
        ON CONFLICT (stage_id, locale) DO UPDATE SET {updates};
        """,
        {**fields, "stage_id": stage_id, "locale": locale},
    )


# ---------------------------------------------------------------------------
# Stage practices
# ---------------------------------------------------------------------------


def list_practice_templates() -> list[dict[str, Any]]:
    rows = [dict(row) for row in _run(
        """
        SELECT practice_template_id, practice_code, system_type, is_active
        FROM crop_observation.practice_templates
        WHERE is_active = true
        ORDER BY practice_code;
        """,
        {},
    )]
    translations = _run(
        "SELECT practice_template_id, locale, display_name, help_text FROM crop_observation.practice_translations WHERE practice_template_id = ANY(:ids);",
        {"ids": [row["practice_template_id"] for row in rows]},
    ) if rows else []
    by_id = {}
    for item in translations:
        by_id.setdefault(item["practice_template_id"], []).append(dict(item))
    for row in rows:
        row["translations"] = by_id.get(row["practice_template_id"], [])
    return rows


def get_practice_template_by_code(practice_code: str) -> dict[str, Any] | None:
    return _run_one(
        "SELECT practice_template_id, practice_code, system_type, is_active "
        "FROM crop_observation.practice_templates WHERE practice_code = :code;",
        {"code": practice_code},
    )


def list_stage_practices_for_stage(stage_id: UUID) -> list[dict[str, Any]]:
    rows = [dict(row) for row in _run(
        """
        SELECT sp.stage_practice_id, sp.stage_id, sp.practice_template_id, pt.practice_code,
               sp.availability_scope, sp.display_order, sp.is_enabled, sp.media_config
        FROM crop_observation.stage_practices sp
        JOIN crop_observation.practice_templates pt ON pt.practice_template_id = sp.practice_template_id
        WHERE sp.stage_id = :stage_id
        ORDER BY sp.display_order;
        """,
        {"stage_id": stage_id},
    )]
    translations = _run(
        """
        SELECT practice_template_id, locale, display_name, help_text
        FROM crop_observation.practice_translations
        WHERE practice_template_id = ANY(:ids);
        """,
        {"ids": [row["practice_template_id"] for row in rows]},
    ) if rows else []
    by_id = {}
    for item in translations:
        by_id.setdefault(item["practice_template_id"], []).append(dict(item))
    for row in rows:
        row["translations"] = by_id.get(row["practice_template_id"], [])
    return rows


def get_stage_practice(stage_practice_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT sp.stage_practice_id, sp.stage_id, sp.practice_template_id, pt.practice_code,
               sp.availability_scope, sp.display_order, sp.is_enabled, sp.media_config
        FROM crop_observation.stage_practices sp
        JOIN crop_observation.practice_templates pt ON pt.practice_template_id = sp.practice_template_id
        WHERE sp.stage_practice_id = :id;
        """,
        {"id": stage_practice_id},
    )


def create_stage_practice(
    *, stage_id: UUID, practice_template_id: UUID, availability_scope: str, display_order: int, media_config: dict[str, Any]
) -> dict[str, Any]:
    row = _run_write(
        """
        INSERT INTO crop_observation.stage_practices
            (stage_id, practice_template_id, availability_scope, display_order, media_config)
        VALUES (:stage_id, :practice_template_id, :scope, :order, CAST(:media_config AS jsonb))
        RETURNING stage_practice_id;
        """,
        {
            "stage_id": stage_id,
            "practice_template_id": practice_template_id,
            "scope": availability_scope,
            "order": display_order,
            "media_config": json.dumps(media_config or {}),
        },
    )
    return get_stage_practice(row["stage_practice_id"])


def update_stage_practice(stage_practice_id: UUID, fields: dict[str, Any]) -> dict[str, Any] | None:
    if fields:
        assignments_parts = []
        params = {"id": stage_practice_id}
        for key, value in fields.items():
            if key == "media_config":
                assignments_parts.append("media_config = CAST(:media_config AS jsonb)")
                params["media_config"] = json.dumps(value)
            else:
                assignments_parts.append(f"{key} = :{key}")
                params[key] = value
        _exec_write(
            f"UPDATE crop_observation.stage_practices SET {', '.join(assignments_parts)} WHERE stage_practice_id = :id;",
            params,
        )
    return get_stage_practice(stage_practice_id)


def delete_stage_practice(stage_practice_id: UUID) -> None:
    _exec_write(
        "DELETE FROM crop_observation.stage_practices WHERE stage_practice_id = :id;",
        {"id": stage_practice_id},
    )


def upsert_practice_translation(practice_template_id: UUID, locale: str, fields: dict[str, Any]) -> None:
    columns = ", ".join(fields.keys())
    placeholders = ", ".join(f":{key}" for key in fields.keys())
    updates = ", ".join(f"{key} = EXCLUDED.{key}" for key in fields.keys())
    _exec_write(
        f"""
        INSERT INTO crop_observation.practice_translations (practice_template_id, locale, {columns})
        VALUES (:practice_template_id, :locale, {placeholders})
        ON CONFLICT (practice_template_id, locale) DO UPDATE SET {updates};
        """,
        {**fields, "practice_template_id": practice_template_id, "locale": locale},
    )


# ---------------------------------------------------------------------------
# Fields
# ---------------------------------------------------------------------------


def list_fields_for_stage_practice(stage_practice_id: UUID) -> list[dict[str, Any]]:
    rows = [dict(row) for row in _run(
        """
        SELECT field_definition_id, stage_practice_id, field_code, field_type, semantic_type,
               display_order, is_required, is_enabled, validation_config, ui_config
        FROM crop_observation.practice_field_definitions
        WHERE stage_practice_id = :id
        ORDER BY display_order;
        """,
        {"id": stage_practice_id},
    )]
    translations = _run(
        "SELECT field_definition_id, locale, label, help_text FROM crop_observation.practice_field_translations WHERE field_definition_id = ANY(:ids);",
        {"ids": [row["field_definition_id"] for row in rows]},
    ) if rows else []
    by_id = {}
    for item in translations:
        by_id.setdefault(item["field_definition_id"], []).append(dict(item))
    for row in rows:
        row["translations"] = by_id.get(row["field_definition_id"], [])
    return rows


def get_field(field_definition_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT field_definition_id, stage_practice_id, field_code, field_type, semantic_type,
               display_order, is_required, is_enabled, validation_config, ui_config
        FROM crop_observation.practice_field_definitions
        WHERE field_definition_id = :id;
        """,
        {"id": field_definition_id},
    )


def create_field(
    *,
    stage_practice_id: UUID,
    field_code: str,
    field_type: str,
    semantic_type: str | None,
    display_order: int,
    is_required: bool,
) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.practice_field_definitions
            (stage_practice_id, field_code, field_type, semantic_type, display_order, is_required)
        VALUES (:spid, :code, :type, :semantic, :order, :required)
        RETURNING field_definition_id, stage_practice_id, field_code, field_type, semantic_type,
                  display_order, is_required, is_enabled, validation_config, ui_config;
        """,
        {
            "spid": stage_practice_id,
            "code": field_code,
            "type": field_type,
            "semantic": semantic_type,
            "order": display_order,
            "required": is_required,
        },
    )


def update_field(field_definition_id: UUID, fields: dict[str, Any]) -> dict[str, Any] | None:
    if not fields:
        return get_field(field_definition_id)
    assignments = ", ".join(f"{key} = :{key}" for key in fields)
    return _run_write(
        f"""
        UPDATE crop_observation.practice_field_definitions
        SET {assignments}
        WHERE field_definition_id = :id
        RETURNING field_definition_id, stage_practice_id, field_code, field_type, semantic_type,
                  display_order, is_required, is_enabled, validation_config, ui_config;
        """,
        {**fields, "id": field_definition_id},
    )


def delete_field(field_definition_id: UUID) -> None:
    _exec_write(
        "DELETE FROM crop_observation.practice_field_definitions WHERE field_definition_id = :id;",
        {"id": field_definition_id},
    )


def reorder_fields(stage_practice_id: UUID, order: list[UUID]) -> None:
    try:
        with engine.begin() as conn:
            for index, field_id in enumerate(order):
                conn.execute(
                    text(
                        "UPDATE crop_observation.practice_field_definitions SET display_order = :order "
                        "WHERE field_definition_id = :id AND stage_practice_id = :spid;"
                    ),
                    {"order": index, "id": field_id, "spid": stage_practice_id},
                )
    except SQLAlchemyError as exc:
        raise CropObservationRepositoryError(str(exc)) from exc


def upsert_field_translation(field_definition_id: UUID, locale: str, fields: dict[str, Any]) -> None:
    columns = ", ".join(fields.keys())
    placeholders = ", ".join(f":{key}" for key in fields.keys())
    updates = ", ".join(f"{key} = EXCLUDED.{key}" for key in fields.keys())
    _exec_write(
        f"""
        INSERT INTO crop_observation.practice_field_translations (field_definition_id, locale, {columns})
        VALUES (:field_definition_id, :locale, {placeholders})
        ON CONFLICT (field_definition_id, locale) DO UPDATE SET {updates};
        """,
        {**fields, "field_definition_id": field_definition_id, "locale": locale},
    )


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


def list_options_for_field(field_definition_id: UUID) -> list[dict[str, Any]]:
    rows = [dict(row) for row in _run(
        """
        SELECT field_option_id, field_definition_id, option_code, display_order,
               icon_key, is_active, metadata
        FROM crop_observation.practice_field_options
        WHERE field_definition_id = :id
        ORDER BY display_order;
        """,
        {"id": field_definition_id},
    )]
    translations = _run(
        "SELECT field_option_id, locale, label FROM crop_observation.practice_field_option_translations WHERE field_option_id = ANY(:ids);",
        {"ids": [row["field_option_id"] for row in rows]},
    ) if rows else []
    by_id = {}
    for item in translations:
        by_id.setdefault(item["field_option_id"], []).append(dict(item))
    for row in rows:
        row["translations"] = by_id.get(row["field_option_id"], [])
    return rows


def get_option(field_option_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT field_option_id, field_definition_id, option_code, display_order,
               icon_key, is_active, metadata
        FROM crop_observation.practice_field_options
        WHERE field_option_id = :id;
        """,
        {"id": field_option_id},
    )


def create_option(*, field_definition_id: UUID, option_code: str, display_order: int) -> dict[str, Any]:
    return _run_write(
        """
        INSERT INTO crop_observation.practice_field_options
            (field_definition_id, option_code, display_order)
        VALUES (:field_definition_id, :option_code, :display_order)
        RETURNING field_option_id, field_definition_id, option_code, display_order,
                  icon_key, is_active, metadata;
        """,
        {"field_definition_id": field_definition_id, "option_code": option_code, "display_order": display_order},
    )


def update_option(field_option_id: UUID, fields: dict[str, Any]) -> dict[str, Any] | None:
    if not fields:
        return get_option(field_option_id)
    assignments = ", ".join(f"{key} = :{key}" for key in fields)
    return _run_write(
        f"""
        UPDATE crop_observation.practice_field_options
        SET {assignments}
        WHERE field_option_id = :id
        RETURNING field_option_id, field_definition_id, option_code, display_order,
                  icon_key, is_active, metadata;
        """,
        {**fields, "id": field_option_id},
    )


def delete_option(field_option_id: UUID) -> None:
    _exec_write(
        "DELETE FROM crop_observation.practice_field_options WHERE field_option_id = :id;",
        {"id": field_option_id},
    )


def upsert_option_translation(field_option_id: UUID, locale: str, label: str) -> None:
    _exec_write(
        """
        INSERT INTO crop_observation.practice_field_option_translations (field_option_id, locale, label)
        VALUES (:field_option_id, :locale, :label)
        ON CONFLICT (field_option_id, locale) DO UPDATE SET label = EXCLUDED.label;
        """,
        {"field_option_id": field_option_id, "locale": locale, "label": label},
    )


# ---------------------------------------------------------------------------
# Validation support — everything needed to check a draft before publish
# ---------------------------------------------------------------------------


def get_full_configuration_tree(config_version_id: UUID) -> list[dict[str, Any]]:
    """Flat listing of stage -> stage_practice -> field for validation."""
    return _run(
        """
        SELECT
            s.stage_id, s.stage_code,
            sp.stage_practice_id, pt.practice_code,
            fd.field_definition_id, fd.field_code, fd.field_type, fd.is_required
        FROM crop_observation.crop_stages s
        LEFT JOIN crop_observation.stage_practices sp ON sp.stage_id = s.stage_id AND sp.is_enabled = true
        LEFT JOIN crop_observation.practice_templates pt ON pt.practice_template_id = sp.practice_template_id
        LEFT JOIN crop_observation.practice_field_definitions fd
            ON fd.stage_practice_id = sp.stage_practice_id AND fd.is_enabled = true
        WHERE s.config_version_id = :cv AND s.is_enabled = true
        ORDER BY s.display_order;
        """,
        {"cv": config_version_id},
    )


def count_locales_for_stage(stage_id: UUID) -> list[str]:
    rows = _run(
        "SELECT locale FROM crop_observation.crop_stage_translations WHERE stage_id = :id;",
        {"id": stage_id},
    )
    return [r["locale"] for r in rows]


def count_locales_for_field(field_definition_id: UUID) -> list[str]:
    rows = _run(
        "SELECT locale FROM crop_observation.practice_field_translations WHERE field_definition_id = :id;",
        {"id": field_definition_id},
    )
    return [r["locale"] for r in rows]


def count_locales_for_crop(crop_id: UUID) -> list[str]:
    rows = _run(
        "SELECT locale FROM crop_observation.crop_translations WHERE crop_id = :id;",
        {"id": crop_id},
    )
    return [r["locale"] for r in rows]


def count_locales_for_option(field_option_id: UUID) -> list[str]:
    rows = _run(
        "SELECT locale FROM crop_observation.practice_field_option_translations WHERE field_option_id = :id;",
        {"id": field_option_id},
    )
    return [r["locale"] for r in rows]


# ---------------------------------------------------------------------------
# Observation monitor
# ---------------------------------------------------------------------------


def observations_summary() -> dict[str, Any]:
    row = _run_one(
        """
        SELECT
            COUNT(*) AS total_observations,
            COUNT(*) FILTER (WHERE crop_status = 'SERIOUS_PROBLEM') AS serious_count,
            COUNT(*) FILTER (WHERE observed_on = CURRENT_DATE) AS today_count
        FROM crop_observation.daily_stage_observations;
        """,
        {},
    )
    open_flags = _run_one(
        "SELECT COUNT(*) AS open_review_flags FROM crop_observation.review_flags WHERE status = 'OPEN';",
        {},
    )
    return {**(row or {}), **(open_flags or {})}


def list_observations(
    *,
    crop_code: str | None,
    status: str | None,
    from_date,
    to_date,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    return _run(
        """
        SELECT
            d.daily_observation_id, d.crop_cycle_id, d.stage_code, d.observed_on,
            d.crop_status, d.created_at,
            fc.farm_id, fc.farmer_user_id, fc.crop_code
        FROM crop_observation.daily_stage_observations d
        JOIN crop_observation.crop_cycles cc ON cc.crop_cycle_id = d.crop_cycle_id
        JOIN crop_observation.farm_crops fc ON fc.farm_crop_id = cc.farm_crop_id
        WHERE (:crop_code IS NULL OR fc.crop_code = :crop_code)
          AND (:status IS NULL OR d.crop_status = :status)
          AND (:from_date IS NULL OR d.observed_on >= :from_date)
          AND (:to_date IS NULL OR d.observed_on <= :to_date)
        ORDER BY d.observed_on DESC, d.created_at DESC
        LIMIT :limit OFFSET :offset;
        """,
        {
            "crop_code": crop_code,
            "status": status,
            "from_date": from_date,
            "to_date": to_date,
            "limit": limit,
            "offset": offset,
        },
    )


def get_observation_detail(daily_observation_id: UUID) -> dict[str, Any] | None:
    return _run_one(
        """
        SELECT
            d.daily_observation_id, d.crop_cycle_id, d.stage_code, d.observed_on,
            d.crop_status, d.created_at, d.updated_at,
            fc.farm_id, fc.farmer_user_id, fc.crop_code
        FROM crop_observation.daily_stage_observations d
        JOIN crop_observation.crop_cycles cc ON cc.crop_cycle_id = d.crop_cycle_id
        JOIN crop_observation.farm_crops fc ON fc.farm_crop_id = cc.farm_crop_id
        WHERE d.daily_observation_id = :id;
        """,
        {"id": daily_observation_id},
    )
