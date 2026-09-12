from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from services.crop_observation_service.app import observation_service
from services.crop_observation_service.app import repository as repo
from services.crop_observation_service.app.dependencies import RequestContext
from services.crop_observation_service.app.errors import CropObservationError
from services.crop_observation_service.app.schemas import (
    HistoryItem,
    HistoryMediaSummary,
    HistoryResponse,
    PracticeHistoryItem,
    PracticeHistoryResponse,
)


def _summary_from_media(media: list[dict[str, Any]]) -> HistoryMediaSummary:
    def _photos(purpose: str) -> dict[str, Any]:
        items = [
            m
            for m in media
            if m["media_role"] == "PHOTO"
            and m["media_purpose"] == purpose
            and m["upload_status"] == "READY"
        ]
        return {
            "count": len(items),
            "media_ids": [m["media_asset_id"] for m in items],
        }

    voice = next(
        (
            m
            for m in media
            if m["media_role"] == "VOICE_NOTE"
            and m["upload_status"] == "READY"
        ),
        None,
    )
    return HistoryMediaSummary(
        crop_condition=_photos("CROP_CONDITION"),
        issue_evidence=_photos("ISSUE_EVIDENCE"),
        practice_evidence=_photos("PRACTICE_EVIDENCE"),
        voice_note={
            "count": 1 if voice else 0,
            "media_id": voice["media_asset_id"] if voice else None,
            "duration_seconds": voice["duration_seconds"] if voice else None,
        },
    )


def _media_summary(owner_type: str, owner_id: UUID) -> HistoryMediaSummary:
    return _summary_from_media(repo.list_media_for_owner(owner_type, owner_id))


def _media_summaries_by_owner(owner_type: str, owner_ids: list[UUID]) -> dict[UUID, HistoryMediaSummary]:
    """One query for every row on the page, instead of one query per row."""
    media_by_owner: dict[UUID, list[dict[str, Any]]] = {owner_id: [] for owner_id in owner_ids}
    for row in repo.list_media_for_owners(owner_type, owner_ids):
        media_by_owner.setdefault(row["owner_id"], []).append(row)
    return {owner_id: _summary_from_media(media) for owner_id, media in media_by_owner.items()}


def get_history(
    context: RequestContext,
    crop_cycle_id: UUID,
    *,
    before: date | None,
    limit: int,
) -> HistoryResponse:
    observation_service.resolve_cycle_and_authorize(context, crop_cycle_id)

    rows = repo.list_recent_daily_observations(crop_cycle_id, before=before, limit=limit)
    summaries = _media_summaries_by_owner("DAILY_STAGE", [row["daily_observation_id"] for row in rows])

    items = []
    for row in rows:
        practices = repo.list_practice_observations_for_daily(row["daily_observation_id"])

        items.append(
            HistoryItem(
                daily_observation_id=row["daily_observation_id"],
                date=row["observed_on"],
                crop_status=row["crop_status"],
                stage_code=row["stage_code"],
                practices=[
                    {"practice_code": p["practice_code"], "answers": p["answers"]}
                    for p in practices
                ],
                media_summary=summaries[row["daily_observation_id"]],
            )
        )

    next_cursor = items[-1].date.isoformat() if len(items) == limit else None
    return HistoryResponse(items=items, next_cursor=next_cursor)


# ---------------------------------------------------------------------------
# Per-practice history — "Previous entries" rows shown above the new-entry
# form inside a single practice's bottom sheet.
# ---------------------------------------------------------------------------

def _option_label_lookup(stage_practice_id: UUID, *, locale: str) -> dict[str, dict[str, str]]:
    """field_code -> {option_code: label} for every option-backed field on
    this practice, so raw stored codes (e.g. "UREA", "WHOLE_FARM") never
    reach the farmer-visible summary line untranslated.

    One query for the whole practice (see
    repository.list_option_labels_for_stage_practice) instead of the
    previous field-by-field, option-by-option round trips — that N+1 was
    the main reason opening a practice sheet felt slow."""
    rows = repo.list_option_labels_for_stage_practice(stage_practice_id)
    by_field_and_option: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        by_field_and_option.setdefault((row["field_code"], row["option_code"]), []).append(row)

    lookup: dict[str, dict[str, str]] = {}
    for (field_code, option_code), translations in by_field_and_option.items():
        pairs = [{"locale": t["locale"], "display_name": t["label"]} for t in translations]
        label, _ = repo.pick_names_strict(pairs, locale)
        lookup.setdefault(field_code, {})[option_code] = label or option_code
    return lookup


def _summarize_answers(answers: dict[str, Any], option_labels: dict[str, dict[str, str]]) -> list[str]:
    values: list[str] = []
    for field_code, value in answers.items():
        if value in (None, "", [], {}):
            continue
        # QUANTITY_UNIT: {"value": 20, "unit": "KG"}
        if isinstance(value, dict) and "value" in value and "unit" in value:
            values.append(f"{value['value']} {str(value['unit']).lower()}")
            continue
        # APPLICATION_AREA: {"scope": "WHOLE_FARM" | "SELECTED_AREA", ...}
        if isinstance(value, dict) and "scope" in value:
            labels = option_labels.get(field_code, {})
            values.append(labels.get(value["scope"], value["scope"]))
            continue
        if isinstance(value, str) and field_code in option_labels:
            values.append(option_labels[field_code].get(value, value))
            continue
        if isinstance(value, str):
            values.append(value)
    return values[:4]


def get_practice_history(
    context: RequestContext,
    crop_cycle_id: UUID,
    stage_code: str,
    practice_code: str,
    *,
    locale: str,
    limit: int,
) -> PracticeHistoryResponse:
    cycle = observation_service.resolve_cycle_and_authorize(context, crop_cycle_id)

    stage = repo.get_stage_by_code(cycle["config_version_id"], stage_code)
    if stage is None:
        raise CropObservationError("CROP_STAGE_NOT_FOUND", "This crop stage was not found.", 404)

    option_labels: dict[str, dict[str, str]] = {}
    for stage_practice in repo.list_stage_practices(stage["stage_id"]):
        if stage_practice["practice_code"] == practice_code:
            option_labels = _option_label_lookup(stage_practice["stage_practice_id"], locale=locale)
            break

    rows = repo.list_practice_history(
        crop_cycle_id=crop_cycle_id,
        stage_code=stage_code,
        practice_code=practice_code,
        limit=limit,
        exclude_observed_on=observation_service.today_ist(),
    )
    summaries = _media_summaries_by_owner("PRACTICE", [row["practice_observation_id"] for row in rows])

    items = [
        PracticeHistoryItem(
            practice_observation_id=row["practice_observation_id"],
            observed_on=row["observed_on"],
            answers=row["answers"],
            summary_values=_summarize_answers(row["answers"], option_labels),
            media=summaries[row["practice_observation_id"]],
        )
        for row in rows
    ]
    return PracticeHistoryResponse(items=items)
