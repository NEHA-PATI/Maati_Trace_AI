from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import text
from shared.db.postgres import engine
from services.hot_stream_orchestrator_service.app.service import ensure_farm_analysis_ready
from services.hot_stream_orchestrator_service.app.main import full_refresh_farm_endpoint

REPORT_PATH = BACKEND_ROOT / "reports" / "full_refresh_all_farms_result.json"


def list_active_farms() -> list[dict[str, Any]]:
    query = text(
        """
        SELECT farm_id
        FROM farms
        WHERE is_active = TRUE
        ORDER BY farm_id
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()
    return [dict(r) for r in rows]


def run_all() -> None:
    farms = list_active_farms()
    results = []
    for f in farms:
        farm_id = f["farm_id"]
        try:
            # call internal endpoint function to reuse orchestration
            res = full_refresh_farm_endpoint(farm_id)
            results.append({"farm_id": str(farm_id), "result": res})
            print(json.dumps({"farm_id": str(farm_id), "status": res.get("status"), "stages": res.get("stages")}, default=str))
        except Exception as exc:
            results.append({"farm_id": str(farm_id), "error": str(exc)})
            print(json.dumps({"farm_id": str(farm_id), "status": "failed", "error": str(exc)}, default=str))

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(results, default=str, indent=2))
    print(f"Wrote report: {REPORT_PATH}")


if __name__ == "__main__":
    run_all()
