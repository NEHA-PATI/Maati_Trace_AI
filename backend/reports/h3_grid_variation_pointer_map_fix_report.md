**H3 Grid Variation + Pointer Map Fix Report**

What changed:
- Added a reusable farm-pointer satellite map for admin/FPO/farmer views.
- Wired Admin Dashboard, FPO Dashboard, My FPO, and Farmer Profile to render real farm pointers.
- Added a gateway-backed `GET /v1/farms` endpoint so dashboards can list accessible farms.
- Fixed analytics summary labels so farm H3 count and processed H3 count are separated.
- Updated grid fallback logic to keep cells only when farm coverage is greater than 1%.
- Updated grid-value calculation to use H3-overlap-weighted values when crosswalk + H3 rows exist.

Files changed:
- `frontend/src/components/ui-custom/FarmPointerMap.jsx`
- `frontend/src/pages/AdminDashboard.jsx`
- `frontend/src/pages/FpoDashboard.jsx`
- `frontend/src/pages/MyFpo.jsx`
- `frontend/src/pages/FarmerProfile.jsx`
- `frontend/src/pages/LandIntelligence.jsx`
- `frontend/src/lib/api/farm.js`
- `backend/services/farm_registry_service/app/main.py`
- `backend/services/farm_registry_service/app/repository.py`
- `backend/services/analytics_query_service/app/main.py`
- `backend/services/analytics_query_service/app/repository.py`
- `backend/services/analytics_query_service/app/service.py`
- `backend/services/analytics_query_service/app/schemas.py`

Farm-pointer behavior:
- Each farm marker is placed from `polygon_geojson` centroid when available, otherwise from `bbox`.
- Pointer hover shows farm name, village/block/district, area, and NDVI when available.
- Pointer click routes to `/land/{farm_id}`.
- Admin can see all farms returned by `GET /api/farms`.
- FPO and farmer dashboards use their respective farm lists.

H3 count fix:
- `total_farm_h3_cells` now represents the farm metadata H3 count.
- `processed_h3_cells` now represents distinct H3 cells found in the latest Sentinel/H3 rows.
- `latest_processed_h3_cells` is exposed separately for clarity.
- The frontend top KPI uses farm H3 count instead of the processed H3 count.

Grid inclusion threshold:
- Fallback grid generation now keeps cells with `coverage_ratio > 0.01`.
- Edge cells are no longer dropped just because they are partial overlaps.

Weighted grid logic:
- `farm_grid_daily_values` now prefers H3-overlap-weighted values when crosswalk rows and latest H3 rows exist.
- `grid-cell details` endpoint now returns contribution rows with H3 values from the latest feature set.
- If H3 values are identical upstream, the frontend will still reflect that truth instead of hiding it.

Validation:
- `python -m py_compile backend/services/farm_registry_service/app/main.py backend/services/farm_registry_service/app/repository.py backend/services/analytics_query_service/app/main.py backend/services/analytics_query_service/app/repository.py backend/services/analytics_query_service/app/service.py backend/services/analytics_query_service/app/schemas.py`
- `cd frontend && npm run build`

Known limitations:
- If the raster processor writes identical values per H3 cell, grid variation will still look flat until that upstream extraction is fixed.
- The new farm-pointer map depends on farm polygons or bbox data being available in the returned farm list.
- Full background job persistence for grid materialization still needs a dedicated write-through job if you want the endpoint to populate missing rows automatically instead of computing them on read.

Next step if we want true variation everywhere:
- Audit `raster_processor_service` to confirm it computes per-H3 zonal or centroid-sampled values instead of a farm-level average.
- Persist the per-H3 rows into `h3_sentinel2_features` and let grid weighting consume those rows.
