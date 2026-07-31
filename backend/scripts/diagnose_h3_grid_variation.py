from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from sqlalchemy import text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from shared.db.postgres import engine


def _numeric_stats(values: list[float | None]) -> tuple[Any, Any]:
    clean = [float(value) for value in values if value is not None]
    if not clean:
        return None, None
    return min(clean), max(clean)


def _identical(values: list[float | None]) -> bool:
    clean = [float(value) for value in values if value is not None]
    return len(clean) > 1 and min(clean) == max(clean)


def _print_stats(label: str, values: list[float | None]) -> None:
    min_value, max_value = _numeric_stats(values)
    print(f"  {label}: min={min_value} max={max_value}")


def main() -> None:
    farm_query = text(
        """
        WITH latest_features AS (
            SELECT DISTINCT ON (farm_id)
                farm_id,
                snapshot_date,
                scene_id
            FROM h3_sentinel2_features
            ORDER BY farm_id, snapshot_date DESC, created_at DESC
        )
        SELECT
            f.farm_id,
            f.farm_name,
            f.h3_cell_count,
            f.h3_cells,
            lf.snapshot_date,
            COUNT(DISTINCT sf.h3_index) AS processed_h3_count,
            MIN(sf.ndvi) AS min_ndvi,
            MAX(sf.ndvi) AS max_ndvi,
            MIN(sf.ndmi) AS min_ndmi,
            MAX(sf.ndmi) AS max_ndmi,
            MIN(sf.bsi) AS min_bsi,
            MAX(sf.bsi) AS max_bsi
        FROM farms f
        LEFT JOIN latest_features lf ON lf.farm_id = f.farm_id
        LEFT JOIN h3_sentinel2_features sf
          ON sf.farm_id = f.farm_id
         AND sf.snapshot_date = lf.snapshot_date
        WHERE EXISTS (
            SELECT 1
            FROM h3_sentinel2_features x
            WHERE x.farm_id = f.farm_id
        )
        GROUP BY f.farm_id, f.farm_name, f.h3_cell_count, f.h3_cells, lf.snapshot_date
        ORDER BY f.farm_id;
        """
    )

    grid_query = text(
        """
        SELECT
            gc.farm_id,
            COUNT(DISTINCT gc.grid_cell_id) AS grid_count,
            COUNT(DISTINCT gv.grid_cell_id) AS grid_values_count,
            MIN(gv.ndvi) AS min_grid_ndvi,
            MAX(gv.ndvi) AS max_grid_ndvi,
            MIN(gv.ndmi) AS min_grid_ndmi,
            MAX(gv.ndmi) AS max_grid_ndmi,
            MIN(gv.bsi) AS min_grid_bsi,
            MAX(gv.bsi) AS max_grid_bsi
        FROM farm_grid_cells gc
        LEFT JOIN farm_grid_daily_values gv
          ON gv.grid_cell_id = gc.grid_cell_id
        GROUP BY gc.farm_id
        ORDER BY gc.farm_id;
        """
    )

    crosswalk_query = text(
        """
        SELECT
            farm_id,
            COUNT(*) AS crosswalk_rows
        FROM farm_grid_h3_crosswalk
        GROUP BY farm_id;
        """
    )

    grid_values_source_query = text(
        """
        SELECT farm_id, value_source, COUNT(*) AS cnt
        FROM farm_grid_daily_values
        GROUP BY farm_id, value_source;
        """
    )

    with engine.connect() as conn:
        farm_rows = conn.execute(farm_query).mappings().all()
        grid_rows = conn.execute(grid_query).mappings().all()
        crosswalk_rows = conn.execute(crosswalk_query).mappings().all()
        grid_values_source_rows = conn.execute(grid_values_source_query).mappings().all()

    grid_by_farm = {str(row["farm_id"]): dict(row) for row in grid_rows}
    crosswalk_by_farm = {str(row["farm_id"]): dict(row) for row in crosswalk_rows}

    print("MaatiTrace H3/Grid Variation Diagnostic")
    print("=" * 44)

    farms_checked = 0
    partial_h3: list[str] = []
    missing_grid: list[str] = []
    farms_missing_grid = 0
    farms_identical_h3_values = 0
    farms_identical_grid_values = 0
    farms_full_success = 0

    grid_values_source_by_farm: dict[str, dict[str, int]] = {}
    for r in grid_values_source_rows:
        fid = str(r["farm_id"])
        grid_values_source_by_farm.setdefault(fid, {})[str(r["value_source"]) or "unknown"] = int(r["cnt"] or 0)
    for row in farm_rows:
        farm_id = str(row["farm_id"])
        h3_cells = row.get("h3_cells") or []
        if isinstance(h3_cells, str):
            h3_cells = [h3_cells]
        if not isinstance(h3_cells, list):
            h3_cells = list(h3_cells) if h3_cells is not None else []

        processed_h3_count = int(row.get("processed_h3_count") or 0)
        h3_cell_count = int(row.get("h3_cell_count") or 0)
        h3_cell_list_count = len(h3_cells)
        grid = grid_by_farm.get(farm_id, {})
        grid_count = int(grid.get("grid_count") or 0)
        grid_values_count = int(grid.get("grid_values_count") or 0)

        h3_ndvi = [row.get("min_ndvi"), row.get("max_ndvi")]
        h3_ndmi = [row.get("min_ndmi"), row.get("max_ndmi")]
        h3_bsi = [row.get("min_bsi"), row.get("max_bsi")]

        print(f"farm_id: {farm_id}")
        print(f"farm_name: {row.get('farm_name') or '—'}")
        print(f"farm.h3_cell_count: {h3_cell_count}")
        print(f"farm.h3_cells length: {h3_cell_list_count}")
        print(f"distinct processed h3_index: {processed_h3_count}")
        print(f"latest snapshot_date: {row.get('snapshot_date')}")
        ratio = round((processed_h3_count / max(1, h3_cell_count)) * 100.0, 2) if h3_cell_count else None
        print(f"processed_h3_ratio: {ratio}%")
        _print_stats("H3 NDVI", h3_ndvi)
        _print_stats("H3 NDMI", h3_ndmi)
        _print_stats("H3 BSI", h3_bsi)
        print(f"grid cell count: {grid_count}")
        print(f"grid values count: {grid_values_count}")
        value_source_breakdown = grid_values_source_by_farm.get(farm_id, {})
        if value_source_breakdown:
            print(f"grid value sources: {value_source_breakdown}")
        _print_stats("Grid NDVI", [grid.get("min_grid_ndvi"), grid.get("max_grid_ndvi")])
        _print_stats("Grid NDMI", [grid.get("min_grid_ndmi"), grid.get("max_grid_ndmi")])
        _print_stats("Grid BSI", [grid.get("min_grid_bsi"), grid.get("max_grid_bsi")])

        if _identical([row.get("min_ndvi"), row.get("max_ndvi")]):
            print("WARNING: H3 NDVI values appear identical.")
        if _identical([row.get("min_ndmi"), row.get("max_ndmi")]):
            print("WARNING: H3 NDMI values appear identical.")
        if _identical([row.get("min_bsi"), row.get("max_bsi")]):
            print("WARNING: H3 BSI values appear identical.")
        if _identical([grid.get("min_grid_ndvi"), grid.get("max_grid_ndvi")]):
            print("WARNING: Grid NDVI values appear identical.")
        if _identical([grid.get("min_grid_ndmi"), grid.get("max_grid_ndmi")]):
            print("WARNING: Grid NDMI values appear identical.")
        if _identical([grid.get("min_grid_bsi"), grid.get("max_grid_bsi")]):
            print("WARNING: Grid BSI values appear identical.")
        if h3_cell_count and processed_h3_count and h3_cell_count != processed_h3_count:
            print("WARNING: farm H3 count != processed H3 count.")
            partial_h3.append(farm_id)
        if grid_count and grid_values_count and grid_count != grid_values_count:
            print("WARNING: grid cell count != grid values count.")
        crosswalk_rows = crosswalk_by_farm.get(farm_id, {}).get("crosswalk_rows", 0)
        print(f"crosswalk rows: {crosswalk_rows}")
        if grid_count == 0 or crosswalk_rows == 0 or grid_values_count == 0:
            farms_missing_grid += 1
            missing_grid.append(farm_id)
        print("-" * 44)

        farms_checked += 1
        if _identical([row.get("min_ndvi"), row.get("max_ndvi")]):
            farms_identical_h3_values += 1
        if _identical([grid.get("min_grid_ndvi"), grid.get("max_grid_ndvi")]):
            farms_identical_grid_values += 1
        if processed_h3_count >= h3_cell_count and grid_count > 0 and crosswalk_rows > 0 and grid_values_count > 0:
            farms_full_success += 1


    print("SUMMARY")
    print("------")
    print(f"farms_checked: {farms_checked}")
    print(f"farms_full_success: {farms_full_success}")
    print(f"farms_partial_h3: {len(partial_h3)}")
    print(f"farms_missing_grid: {farms_missing_grid}")
    print(f"farms_identical_h3_values: {farms_identical_h3_values}")
    print(f"farms_identical_grid_values: {farms_identical_grid_values}")


if __name__ == "__main__":
    main()
