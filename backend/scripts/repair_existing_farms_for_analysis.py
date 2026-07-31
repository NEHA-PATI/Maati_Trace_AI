from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.farm_registry_service.app.repository import list_farms
from services.hot_stream_orchestrator_service.app.service import ensure_farm_analysis_ready, HotStreamOrchestratorError


def main() -> int:
    farms = list_farms()
    repaired = 0
    failed = 0

    print(f"Found {len(farms)} active farms to inspect.")

    for farm in farms:
        farm_id = farm["farm_id"]
        try:
            result = ensure_farm_analysis_ready(farm_id)
            repaired += 1
            print(
                json.dumps(
                    {
                        "farm_id": str(farm_id),
                        "status": "ready",
                        "repaired_fields": result["repaired_fields"],
                        "h3_cell_count": result["h3_cell_count"],
                        "bbox": result["bbox"],
                        "area_acres": result["area_acres"],
                    },
                    default=str,
                )
            )
        except HotStreamOrchestratorError as exc:
            failed += 1
            print(
                json.dumps(
                    {
                        "farm_id": str(farm_id),
                        "status": "failed",
                        "code": exc.code,
                        "message": str(exc),
                    },
                    default=str,
                )
            )
        except Exception as exc:
            failed += 1
            print(
                json.dumps(
                    {
                        "farm_id": str(farm_id),
                        "status": "failed",
                        "code": "UNEXPECTED_ERROR",
                        "message": str(exc),
                    },
                    default=str,
                )
            )

    print(json.dumps({
        "processed": len(farms),
        "repaired": repaired,
        "failed": failed,
    }))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
