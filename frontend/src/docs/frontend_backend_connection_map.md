**Frontend Backend Connection Map**

Frontend rule:
- All data calls go only to `http://localhost:8000`
- No direct frontend calls to backend service ports

Shared auth/session layer:
- `src/lib/api/client.js` injects the bearer token and clears session on 401
- `src/lib/auth/session.js` stores access token, refresh token, and user
- `src/lib/rbac/permissions.js` filters routes and sidebar items by role
- `src/components/ProtectedRoute.jsx` verifies `/api/auth/me` before rendering protected pages

Page to gateway mapping:
- `Login.jsx` -> `/api/auth/login`, `/api/auth/me`
- `AdminDashboard.jsx` -> `/api/routes`, `/api/fpos`, `/api/farms`
- `FpoDashboard.jsx` -> `/api/fpos/me`, `/api/fpos/:fpoId`, `/api/fpos/:fpoId/summary`, `/api/fpos/:fpoId/farmers`, `/api/fpos/:fpoId/farms`
- `MyFpo.jsx` -> `/api/fpos/me`, `/api/fpos/:fpoId/farmers`, `/api/fpos/:fpoId/farms`
- `FarmerProfile.jsx` -> `/api/farmers/me`, `/api/farmers/:farmerId`, `/api/farmers/:farmerId/summary`, `/api/farmers/:farmerId/farms`
- `LandIntelligence.jsx` -> `/api/farms/:farmId`, `/api/analytics/farms/:farmId/summary`, `/api/analytics/farms/:farmId/sentinel2/latest`, `/api/analytics/farms/:farmId/sentinel2/history`, `/api/analytics/farms/:farmId/trends`, `/api/analytics/farms/:farmId/h3-cells`, `/api/analytics/farms/:farmId/grid-cells`, `/api/analytics/farms/:farmId/grid-values/latest`, `/api/analytics/farms/:farmId/grid-cells/:gridCellId/details`
- `FarmRegister.jsx` -> `/api/location/states`, `/api/location/districts`, `/api/location/blocks`, `/api/location/validate`, `/api/h3/preview`, `/api/farmers`, `/api/farms/register`, `/api/farm-analysis/:farmId/materialize`, `/api/hot-stream/farms/:farmId/trends/materialize`, `/api/hot-stream/farms/:farmId/grid/materialize`

Reusable map components:
- `FarmPointerMap.jsx` shows many farm pointers and routes to land intelligence
- `LandGridMap.jsx` shows the satellite basemap, farm boundary, square grid, and optional H3 layer

Backend mapping:
- `/api/auth/*` -> `auth_service`
- `/api/location/*` -> `DISTRICT_BOUNDARY_SERVICE`
- `/api/h3/*` -> `boundary_index_service`
- `/api/fpos/*`, `/api/farmers/*`, `/api/farms/*` -> `farm_registry_service`
- `/api/farm-analysis/*`, `/api/hot-stream/*` -> `hot_stream_orchestrator_service`
- `/api/analytics/*` -> `analytics_query_service`

Analytics/model notes:
- `total_farm_h3_cells` = farm metadata H3 count
- `processed_h3_cells` = distinct H3 rows in latest processed Sentinel data
- `grid_cells_with_values` = grid cells with values available
- Grid values use H3-overlap weighting when crosswalk rows and H3 rows exist

Known gaps:
- If the raster processor writes identical per-H3 values upstream, grid variation will still appear flat until that pipeline is fixed
- Full read/write persistence for grid materialization still depends on the upstream hot-stream job path
- `POST /api/hot-stream/farms/:farmId/repair` now backfills missing farm metadata before analysis, so DB-inserted farms can be repaired before `Run Latest Analysis`
