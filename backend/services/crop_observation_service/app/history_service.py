from __future__ import annotations

from datetime import date
from uuid import UUID

from services.crop_observation_service.app import observation_service, repository as repo
from services.crop_observation_service.app.dependencies import RequestContext
from services.crop_observation_service.app.schemas import (
    HistoryItem,
    HistoryMediaSummary,
    HistoryResponse,
)


def get_history(
    context: RequestContext,
    crop_cycle_id: UUID,
    *,
    before: date | None,
    limit: int,
) -> HistoryResponse:
    observation_service.resolve_cycle_and_authorize(context, crop_cycle_id)

    rows = repo.list_recent_daily_observations(crop_cycle_id, before=before, limit=limit)

    items = []
    for row in rows:
        practices = repo.list_practice_observations_for_daily(row["daily_observation_id"])
        media = repo.list_media_for_owner("DAILY_STAGE", row["daily_observation_id"])
        for practice in practices:
            media += repo.list_media_for_owner("PRACTICE", practice["practice_observation_id"])

        photos = sum(1 for m in media if m["media_role"] == "PHOTO" and m["upload_status"] == "READY")
        voice = any(m["media_role"] == "VOICE_NOTE" and m["upload_status"] == "READY" for m in media)

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
                media_summary=HistoryMediaSummary(photos=photos, voice=voice),
            )
        )

    next_cursor = items[-1].date.isoformat() if len(items) == limit else None
    return HistoryResponse(items=items, next_cursor=next_cursor)
