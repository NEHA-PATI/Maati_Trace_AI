from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from services.crop_observation_service.app import repository as repo
from services.crop_observation_service.app.clients import farm_registry as farm_registry_client
from services.crop_observation_service.app.dependencies import RequestContext
from services.crop_observation_service.app.errors import CropObservationError
from services.crop_observation_service.app.schemas import (
    CROP_STATUS_OPTIONS,
    CropCycleCreateRequest,
    CropCycleResponse,
    CropListResponse,
    CropSummary,
    FarmCropCreateRequest,
    FarmCropResponse,
    RecentHistoryItem,
    ScreenCropOut,
    ScreenCropStatusOptionOut,
    ScreenCycleOut,
    ScreenFarmOut,
    ScreenPracticeFieldOut,
    ScreenPracticeOut,
    ScreenResponse,
    ScreenStageOut,
    ScreenStageTabOut,
    ScreenTodayOut,
)

IST = ZoneInfo("Asia/Kolkata")


def today_ist():
    return datetime.now(IST).date()


def _to_uuid(value: Any) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


# ---------------------------------------------------------------------------
# Crop catalogue
# ---------------------------------------------------------------------------


def list_crops(*, locale: str) -> CropListResponse:
    items = repo.list_active_crops(locale=locale)
    return CropListResponse(
        items=[
            CropSummary(
                crop_code=item["crop_code"],
                lifecycle_type=item["lifecycle_type"],
                name=item["name"],
                secondary_name=item["secondary_name"],
                image_url=item["image_url"],
            )
            for item in items
        ]
    )


# ---------------------------------------------------------------------------
# Farm crops — every access is authorized by asking farm_registry_service
# whether this caller may see the farm; we never re-implement that logic here.
# ---------------------------------------------------------------------------


def _authorize_farm(context: RequestContext, farm_id: UUID) -> dict[str, Any]:
    return farm_registry_client.get_authorized_farm(
        farm_id,
        authorization=context.authorization,
        correlation_id=context.correlation_id,
    )


def list_farm_crops_for_farm(context: RequestContext, farm_id: UUID) -> list[FarmCropResponse]:
    _authorize_farm(context, farm_id)
    rows = repo.list_farm_crops(farm_id)
    return [
        FarmCropResponse(
            farm_crop_id=row["farm_crop_id"],
            farm_id=row["farm_id"],
            farmer_user_id=row["farmer_user_id"],
            crop_code=row["crop_code"],
            variety_name=row["variety_name"],
            planted_on=row["planted_on"],
            status=row["status"],
            created_at=row["created_at"].isoformat(),
            updated_at=row["updated_at"].isoformat(),
        )
        for row in rows
    ]


def attach_crop_to_farm(
    context: RequestContext,
    farm_id: UUID,
    payload: FarmCropCreateRequest,
) -> FarmCropResponse:
    _authorize_farm(context, farm_id)

    crop = repo.get_crop_by_code(payload.crop_code)
    if crop is None or not crop["is_active"]:
        raise CropObservationError(
            "CROP_NOT_FOUND",
            "This crop is not available yet.",
            404,
        )

    existing = repo.get_active_farm_crop(farm_id, payload.crop_code)
    row = existing or repo.create_farm_crop(
        farm_id=farm_id,
        farmer_user_id=context.principal.user_id,
        crop_code=payload.crop_code,
        variety_name=payload.variety_name,
        planted_on=payload.planted_on,
    )
    return FarmCropResponse(
        farm_crop_id=row["farm_crop_id"],
        farm_id=row["farm_id"],
        farmer_user_id=row["farmer_user_id"],
        crop_code=row["crop_code"],
        variety_name=row["variety_name"],
        planted_on=row["planted_on"],
        status=row["status"],
        created_at=row["created_at"].isoformat(),
        updated_at=row["updated_at"].isoformat(),
    )


# ---------------------------------------------------------------------------
# Crop cycles
# ---------------------------------------------------------------------------


def _resolve_initial_stage_code(config_version_id: UUID) -> str | None:
    stages = repo.list_stages(config_version_id)
    if not stages:
        return None
    for stage in stages:
        if stage["is_initial"]:
            return stage["stage_code"]
    return stages[0]["stage_code"]


def start_crop_cycle(
    context: RequestContext,
    farm_crop_id: UUID,
    payload: CropCycleCreateRequest,
) -> CropCycleResponse:
    farm_crop = repo.get_farm_crop(farm_crop_id)
    if farm_crop is None:
        raise CropObservationError("FARM_CROP_NOT_FOUND", "Farm crop was not found.", 404)

    _authorize_farm(context, farm_crop["farm_id"])

    existing_cycle = repo.get_active_cycle_for_farm_crop(farm_crop_id)
    if existing_cycle is not None:
        return CropCycleResponse(**existing_cycle)

    crop = repo.get_crop_by_code(farm_crop["crop_code"])
    if crop is None:
        raise CropObservationError("CROP_NOT_FOUND", "This crop is not available yet.", 404)

    config_version = repo.get_published_config_version(crop["crop_id"])
    if config_version is None:
        raise CropObservationError(
            "CROP_CONFIGURATION_MISSING",
            "This crop does not have a published configuration yet.",
            409,
        )

    current_stage_code = _resolve_initial_stage_code(config_version["config_version_id"])

    row = repo.create_crop_cycle(
        farm_crop_id=farm_crop_id,
        config_version_id=config_version["config_version_id"],
        season_year=payload.season_year,
        season_name=payload.season_name,
        current_stage_code=current_stage_code,
    )
    return CropCycleResponse(**row)


# ---------------------------------------------------------------------------
# Screen API
# ---------------------------------------------------------------------------


def _build_practices_for_stage(stage_id: UUID, *, locale: str) -> list[ScreenPracticeOut]:
    """Renders every practice on a stage from ONE batched fetch
    (repo.get_stage_practices_full) instead of the old per-practice,
    per-field, per-option round trips — see that function's docstring for
    why this mattered."""
    data = repo.get_stage_practices_full(stage_id)

    result = []
    for stage_practice in data["practices"]:
        practice_translations = [
            {"locale": t["locale"], "display_name": t["display_name"]}
            for t in stage_practice["translations"]
        ]
        name, _ = repo.pick_names(practice_translations, locale)

        fields = []
        for field in data["fields_by_practice"].get(stage_practice["stage_practice_id"], []):
            field_translations = field["translations"]
            labels = [{"locale": t["locale"], "display_name": t["label"]} for t in field_translations]
            label, _ = repo.pick_names(labels, locale)
            help_text = next(
                (t["help_text"] for t in field_translations if t["locale"] == locale and t["help_text"]),
                None,
            )

            options = []
            for option in data["options_by_field"].get(field["field_definition_id"], []):
                option_labels = [
                    {"locale": t["locale"], "display_name": t["label"]}
                    for t in option.get("translations", [])
                ]
                option_label, _ = repo.pick_names(option_labels, locale)
                options.append(
                    {
                        "option_code": option["option_code"],
                        "label": option_label or option["option_code"],
                        "icon_key": option["icon_key"],
                        "image_url": option.get("image_url"),
                    }
                )

            fields.append(
                ScreenPracticeFieldOut(
                    field_code=field["field_code"],
                    field_type=field["field_type"],
                    label=label or field["field_code"],
                    help_text=help_text,
                    is_required=field["is_required"],
                    display_order=field["display_order"],
                    options=options,
                )
            )

        result.append(
            ScreenPracticeOut(
                practice_code=stage_practice["practice_code"],
                name=name or stage_practice["practice_code"],
                display_order=stage_practice["display_order"],
                media_config=stage_practice.get("media_config") or {},
                guide_image_url=stage_practice.get("guide_image_url"),
                fields=fields,
            )
        )
    return result


def _media_summary(media_rows: list[dict[str, Any]]) -> dict[str, Any]:
    def _photos(purpose: str) -> dict[str, Any]:
        rows = [
            row
            for row in media_rows
            if row["media_role"] == "PHOTO"
            and row["media_purpose"] == purpose
            and row["upload_status"] == "READY"
        ]
        return {"count": len(rows), "media_ids": [row["media_asset_id"] for row in rows]}

    voice = next(
        (
            row
            for row in media_rows
            if row["media_role"] == "VOICE_NOTE"
            and row["upload_status"] == "READY"
        ),
        None,
    )
    return {
        "crop_condition": _photos("CROP_CONDITION"),
        "issue_evidence": _photos("ISSUE_EVIDENCE"),
        "practice_evidence": _photos("PRACTICE_EVIDENCE"),
        "voice_note": {
            "count": 1 if voice else 0,
            "media_id": voice["media_asset_id"] if voice else None,
            "duration_seconds": voice["duration_seconds"] if voice else None,
        },
    }


def get_stage_screen(
    context: RequestContext,
    crop_cycle_id: UUID,
    stage_code: str,
    *,
    locale: str,
) -> ScreenResponse:
    cycle = repo.get_crop_cycle(crop_cycle_id)
    if cycle is None:
        raise CropObservationError("CROP_CYCLE_NOT_FOUND", "Crop cycle was not found.", 404)

    farm_crop = repo.get_farm_crop(cycle["farm_crop_id"])
    if farm_crop is None:
        raise CropObservationError("FARM_CROP_NOT_FOUND", "Farm crop was not found.", 404)

    farm = _authorize_farm(context, farm_crop["farm_id"])

    crop = repo.get_crop_by_code(farm_crop["crop_code"])
    if crop is None:
        raise CropObservationError("CROP_NOT_FOUND", "This crop is not available yet.", 404)
    crop_name, crop_secondary = repo.get_crop_names(crop["crop_id"], locale=locale)
    crop_card_image = repo.get_crop_card_image(crop["crop_id"])
    crop_image_url = (
        f"/v1/crop-observations/system-media/{crop_card_image['asset_id']}/content"
        if crop_card_image
        else None
    )

    stage = repo.get_stage_by_code(cycle["config_version_id"], stage_code)
    if stage is None:
        raise CropObservationError("CROP_STAGE_NOT_FOUND", "This crop stage was not found.", 404)
    stage_name, stage_secondary = repo.get_stage_names(stage["stage_id"], locale=locale)
    stage_description = next(
        (
            row["short_description"]
            for row in repo.get_stage_translations(stage["stage_id"])
            if row["locale"] == locale and row["short_description"]
        ),
        None,
    )

    stage_image = repo.get_stage_image(stage["stage_id"])
    stage_image_url = (
        f"/v1/crop-observations/system-media/{stage_image['asset_id']}/content" if stage_image else None
    )
    instruction_audio = repo.get_stage_instruction_audio(stage["stage_id"], locale=locale)
    instruction_audio_url = (
        f"/v1/crop-observations/system-media/{instruction_audio['asset_id']}/content"
        if instruction_audio
        else None
    )
    instruction_audio_duration = instruction_audio["duration_seconds"] if instruction_audio else None

    all_stages = repo.list_stages(cycle["config_version_id"])
    stage_tabs = [
        ScreenStageTabOut(
            stage_code=s["stage_code"],
            name=(repo.get_stage_names(s["stage_id"], locale=locale)[0] or s["stage_code"]),
            display_order=s["display_order"],
            is_current=s["stage_code"] == stage_code,
        )
        for s in all_stages
    ]

    practices = _build_practices_for_stage(stage["stage_id"], locale=locale)

    today = today_ist()
    today_daily = repo.get_daily_observation_by_key(cycle["crop_cycle_id"], stage_code, today)
    today_observation = None
    if today_daily is not None:
        today_practices = repo.list_practice_observations_for_daily(today_daily["daily_observation_id"])
            today_observation = {
            "daily_observation_id": today_daily["daily_observation_id"],
            "crop_status": today_daily["crop_status"],
            "practices": [
                {
                    "practice_observation_id": p["practice_observation_id"],
                    "practice_code": p["practice_code"],
                    "answers": p["answers"],
                }
                for p in today_practices
            ],
        }

    recent_rows = repo.list_recent_daily_observations(cycle["crop_cycle_id"], before=None, limit=4)
    recent_media_rows = repo.list_media_for_owners(
        "DAILY_STAGE",
        [row["daily_observation_id"] for row in recent_rows],
    )
    recent_media_by_owner: dict[UUID, list[dict[str, Any]]] = {}
    for media_row in recent_media_rows:
        recent_media_by_owner.setdefault(media_row["owner_id"], []).append(media_row)
    recent_media = {
        owner_id: _media_summary(rows) for owner_id, rows in recent_media_by_owner.items()
    }

    return ScreenResponse(
        crop=ScreenCropOut(
            crop_code=crop["crop_code"],
            name=crop_name or crop["crop_code"],
            secondary_name=crop_secondary,
            image_url=crop_image_url,
        ),
        farm=ScreenFarmOut(farm_id=_to_uuid(farm["farm_id"]), farm_name=farm.get("farm_name")),
        cycle=ScreenCycleOut(crop_cycle_id=cycle["crop_cycle_id"], current_stage_code=cycle["current_stage_code"]),
        stage=ScreenStageOut(
            stage_code=stage["stage_code"],
            name=stage_name or stage["stage_code"],
            secondary_name=stage_secondary,
            short_description=stage_description,
            image_url=stage_image_url,
            instruction_audio_url=instruction_audio_url,
            instruction_audio_duration_seconds=(
                float(instruction_audio_duration) if instruction_audio_duration is not None else None
            ),
        ),
        stage_tabs=stage_tabs,
        today=ScreenTodayOut(date=today, observation=today_observation),
        crop_status_options=[ScreenCropStatusOptionOut(code=code) for code in CROP_STATUS_OPTIONS],
        practices=practices,
        recent_history=[
            RecentHistoryItem(
                daily_observation_id=row["daily_observation_id"],
                date=row["observed_on"],
                crop_status=row["crop_status"],
                stage_code=row["stage_code"],
                media_summary=recent_media.get(row["daily_observation_id"], _media_summary([])),
            )
            for row in recent_rows
            if row["observed_on"] != today
        ],
    )
