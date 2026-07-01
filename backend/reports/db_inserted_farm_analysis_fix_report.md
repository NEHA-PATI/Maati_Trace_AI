# DB Inserted Farm Analysis Fix Report

## Root cause
- Manually inserted farm rows could appear on the map, but analysis assumed derived fields were already populated.
- Missing or stale fields included `bbox`, `area_acres`, `h3_cells`, `h3_cell_count`, and location codes.
- As a result, the repair-free path could reach raster/materialization with incomplete context and return blank summary values or zero processed H3 cells.

## Fix
- Added a repair/preflight step in `hot_stream_orchestrator_service`.
- `ensure_farm_analysis_ready(farm_id)` now:
  - validates the farm exists
  - validates and normalizes the polygon
  - computes `bbox` from geometry when missing
  - computes `area_acres` when missing
  - backfills `h3_resolution` if missing
  - calls the H3 preview service to compute `h3_cells_bigint` and `h3_cell_count`
  - backfills location codes using the location validation service when possible
- `POST /v1/farm-analysis/{farm_id}/materialize` now calls the repair step before raster search and lakehouse write.
- Added `POST /v1/hot-stream/farms/{farm_id}/repair` so the frontend can explicitly repair a farm before analysis.

## Files changed
- `backend/services/hot_stream_orchestrator_service/app/service.py`
- `backend/services/hot_stream_orchestrator_service/app/main.py`
- `backend/services/farm_registry_service/app/repository.py`
- `backend/scripts/repair_existing_farms_for_analysis.py`
- `frontend/src/pages/LandIntelligence.jsx`
- `frontend/src/lib/api/hotStream.js`
- `frontend/src/components/ui-custom/PipelineGlassLoader.jsx`

## Endpoint behavior
- `POST /api/hot-stream/farms/{farm_id}/repair`
  - returns repaired fields, `bbox`, `area_acres`, and `h3_cell_count`
  - returns `422` with `FARM_POLYGON_INVALID` if the polygon is malformed
- `POST /api/farm-analysis/{farm_id}/materialize`
  - now runs repair first
  - continues into raster/lakehouse processing only after the farm is analysis-ready
- `POST /api/hot-stream/farms/{farm_id}/grid/materialize`
  - now returns `no_h3_features` when there are no H3 rows yet instead of silently pretending grid values were computed

## Diagnostic checks
Suggested queries for verification:
```sql
SELECT farm_id, farm_name, farmer_id, fpo_id, state_name, district_name, district_code, block_name, block_code, village_name, h3_resolution, h3_cell_count, bbox, area_acres, polygon_geojson IS NOT NULL AS has_polygon
FROM farms
WHERE farm_id = :farm_id;

SELECT COUNT(*) FROM h3_sentinel2_features WHERE farm_id = :farm_id;
SELECT COUNT(*) FROM farm_grid_cells WHERE farm_id = :farm_id;
SELECT COUNT(*) FROM farm_grid_h3_crosswalk WHERE farm_id = :farm_id;
SELECT COUNT(*) FROM farm_grid_daily_values WHERE farm_id = :farm_id;
```

## Manual test farm IDs
- `c36f136a-d01b-40cd-bd2e-2c41b368fb8c`

## Test calls
1. `GET /api/farms/{farm_id}`
2. `POST /api/hot-stream/farms/{farm_id}/repair`
3. `POST /api/farm-analysis/{farm_id}/materialize`
4. `POST /api/hot-stream/farms/{farm_id}/trends/materialize`
5. `POST /api/hot-stream/farms/{farm_id}/grid/materialize`
6. `GET /api/analytics/farms/{farm_id}/summary`
7. `GET /api/analytics/farms/{farm_id}/grid-values/latest`

## Known limitations
- If a farm has no linked farmer profile, analysis still fails with `FARM_OWNER_MISSING`.
- If raster extraction returns no per-H3 rows, processed H3 counts remain zero until satellite input is available.
- Grid materialization is explicit and still depends on H3 rows being present.
