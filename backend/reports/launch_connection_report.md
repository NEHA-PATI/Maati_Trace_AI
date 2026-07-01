**Launch Connection Report**

Route map:
- Frontend base URL: `http://localhost:5173`
- Backend gateway base URL: `http://localhost:8000`
- Frontend now calls only gateway-prefixed routes under `/api/*`

Frontend page to API mapping:
- `/login` -> `POST /api/auth/login`, `GET /api/auth/me`
- `/admin` -> `GET /api/routes`, `GET /api/fpos`
- `/fpo/me`, `/fpo/:fpoId`, `/my-fpo` -> `GET /api/fpos/me|:id`, `GET /api/fpos/:id/summary`, `GET /api/fpos/:id/farmers`, `GET /api/fpos/:id/farms`
- `/farmer/me`, `/farmers/:farmerId` -> `GET /api/farmers/me|:id`, `GET /api/farmers/:id/summary`, `GET /api/farmers/:id/farms`
- `/land/:farmId` -> `GET /api/farms/:id`, `GET /api/analytics/farms/:id/summary`, `GET /api/analytics/farms/:id/sentinel2/latest`, `GET /api/analytics/farms/:id/sentinel2/history`, `GET /api/analytics/farms/:id/trends`, `GET /api/analytics/farms/:id/grid-cells`, `GET /api/analytics/farms/:id/grid-values/latest`, `POST /api/farm-analysis/:id/materialize`, `POST /api/hot-stream/farms/:id/trends/materialize`, `POST /api/hot-stream/farms/:id/grid/materialize`
- `/farm-register` -> `GET /api/location/states`, `GET /api/location/districts`, `GET /api/location/blocks`, `POST /api/location/validate`, `POST /api/farmers`, `POST /api/farms/register`

API endpoint to service mapping:
- `/api/auth/*` -> `auth_service`
- `/api/location/*` -> `DISTRICT_BOUNDARY_SERVICE`
- `/api/h3/*` -> `boundary_index_service`
- `/api/fpos/*`, `/api/farmers/*`, `/api/farms/*` -> `farm_registry_service`
- `/api/farm-analysis/*`, `/api/hot-stream/*` -> `hot_stream_orchestrator_service`
- `/api/analytics/*` -> `analytics_query_service`

Backend service to database table mapping:
- `auth_service` -> `users`, `refresh_tokens`
- `farm_registry_service` -> `fpos`, `fpo_users`, `farmer_profiles`, `farms`
- `analytics_query_service` -> `h3_sentinel2_features`, `farm_h3_daily_trends`, `farm_grid_cells`, `farm_grid_h3_crosswalk`, `farm_grid_daily_values`
- `DISTRICT_BOUNDARY_SERVICE` -> `states`, `districts`, `blocks`

RBAC access matrix:
- Admin: `/admin`, `/fpo/:fpoId`, `/my-fpo`, `/farmers/:farmerId`, `/land/:farmId`, `/farm-register`, `/bulk-upload`, `/notifications`, `/use-cases`, `/our-method`
- FPO: `/fpo/me`, `/fpo/:fpoId` (own), `/my-fpo`, `/farmers/:farmerId` (under FPO), `/land/:farmId` (under FPO), `/farm-register`, `/bulk-upload`, `/notifications`, `/use-cases`, `/our-method`
- Farmer: `/farmer/me`, `/farmers/:farmerId` (self), `/land/:farmId` (own), `/farm-register`, `/notifications`, `/use-cases`, `/our-method`

Dataflow diagrams in text:
- Login -> gateway -> auth service -> `users` + `refresh_tokens` -> session storage -> role redirect
- Farm register -> gateway -> district validation -> farm registry -> `farmer_profiles` + `farms` -> optional materialize -> orchestrator -> raster/lakehouse -> analytics tables
- Land page -> gateway -> farm registry + analytics query -> farm metadata + H3/grid summaries -> frontend map and metric cards

Implemented endpoint list:
- Gateway route targets for `h3`, `hot-stream`, `farm-analysis`, `analytics`
- Gateway location aliases for `states`, `districts`, `blocks`, `validate`
- Farm registry: `GET /v1/fpos`, `GET /v1/fpos/me`, `GET /v1/fpos/{fpo_id}/summary`, `GET /v1/fpos/{fpo_id}/farmers`, `GET /v1/fpos/{fpo_id}/farms`, `GET /v1/farmers/me`, `GET /v1/farmers/{farmer_id}/summary`
- Analytics query: `GET /v1/analytics/farmers/{farmer_id}/summary`, `GET /v1/analytics/fpos/{fpo_id}/summary`, `GET /v1/analytics/farms/{farm_id}/trends`, `GET /v1/analytics/farms/{farm_id}/h3-cells`, `GET /v1/analytics/farms/{farm_id}/grid-cells`, `GET /v1/analytics/farms/{farm_id}/grid-values/latest`, `GET /v1/analytics/farms/{farm_id}/grid-values/history`
- Hot stream: alias `POST /v1/hot-stream/farms/{farm_id}/materialize`, wired pending endpoints for trends and grid materialization

Missing endpoint list:
- Fully implemented trend aggregation job backing `farm_h3_daily_trends`
- Fully implemented grid generation and crosswalk materialization job
- Password reset and open registration flows
- Bulk CSV upload backend endpoint contract

Pending work list:
- Add ownership-aware RBAC checks beyond top-level role checks on backend
- Replace static `FarmMapView` with fully geographic grid polygons from `farm_grid_cells`
- Materialize grid cells and grid daily values from real polygon/H3 overlap logic
- Add aggregate admin counts for farmers, farms, acres, H3 rows, grid rows

Test results:
- `python -m py_compile ...` passed for edited backend files
- `npm run build` passed after removing stale Base44 imports

Known limitations:
- Grid and trend materialize endpoints currently return pending messages rather than full jobs
- Land page shows raw JSON for history/grid payloads as a resilient launch fallback
- `/fpo/me` and `/farmers/me` depend on valid bearer token and corresponding user linkage rows

Exact commands to run backend services:
- `uvicorn services.api_gateway_service.app.main:app --reload --port 8000`
- `uvicorn services.auth_service.app.main:app --reload --port 8002`
- `uvicorn services.boundary_index_service.app.main:app --reload --port 8004`
- `uvicorn services.district_boundary_service.app.main:app --reload --port 8005`
- `uvicorn services.farm_registry_service.app.main:app --reload --port 8006`
- `uvicorn services.stac_catalog_service.app.main:app --reload --port 8007`
- `uvicorn services.raster_processor_service.app.main:app --reload --port 8008`
- `uvicorn services.lakehouse_writer_service.app.main:app --reload --port 8009`
- `uvicorn services.hot_stream_orchestrator_service.app.main:app --reload --port 8010`
- `uvicorn services.analytics_query_service.app.main:app --reload --port 8011`

Exact command to run frontend:
- `cd frontend && npm run dev`

Sample login credentials used:
- Email: `admin.test@maatitrace.in`
- Password: `Test@12345`

Final verification checklist:
- Frontend gateway base env set to `http://localhost:8000`
- Login page posts to gateway auth route
- Protected routes verify session with `/api/auth/me`
- Admin dashboard loads route inventory through gateway
- FPO and farmer pages fetch registry records through gateway
- Land page fetches farm + analytics through gateway only
- SQL contract file for RBAC/grid/trends created
