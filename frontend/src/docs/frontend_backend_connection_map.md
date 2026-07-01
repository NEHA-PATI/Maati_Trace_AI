**Frontend Backend Connection Map**

Frontend rule:
- All data calls go only to `http://localhost:8000`
- No direct frontend calls to service ports

Shared auth/session layer:
- `src/lib/api/client.js` injects bearer token and handles 401 session clearing
- `src/lib/auth/session.js` stores access token, refresh token, and user
- `src/lib/rbac/permissions.js` defines top-level role access
- `src/components/ProtectedRoute.jsx` verifies `/api/auth/me` before rendering protected pages

Page to gateway mapping:
- `Login.jsx` -> `/api/auth/login`, `/api/auth/me`
- `AdminDashboard.jsx` -> `/api/routes`, `/api/fpos`
- `FpoDashboard.jsx` -> `/api/fpos/me`, `/api/fpos/:fpoId`, `/api/fpos/:fpoId/summary`, `/api/fpos/:fpoId/farmers`, `/api/fpos/:fpoId/farms`
- `FarmerProfile.jsx` -> `/api/farmers/me`, `/api/farmers/:farmerId`, `/api/farmers/:farmerId/summary`, `/api/farmers/:farmerId/farms`
- `LandIntelligence.jsx` -> `/api/farms/:farmId`, `/api/analytics/farms/:farmId/*`, `/api/farm-analysis/:farmId/materialize`, `/api/hot-stream/farms/:farmId/*`
- `FarmRegister.jsx` -> `/api/location/*`, `/api/farmers`, `/api/farms/register`

Backend mapping:
- Gateway `/api/auth/*` -> `auth_service`
- Gateway `/api/location/*` -> `DISTRICT_BOUNDARY_SERVICE`
- Gateway `/api/fpos/*`, `/api/farmers/*`, `/api/farms/*` -> `farm_registry_service`
- Gateway `/api/farm-analysis/*`, `/api/hot-stream/*` -> `hot_stream_orchestrator_service`
- Gateway `/api/analytics/*` -> `analytics_query_service`

Visual map note:
- Current launch page keeps the red-boundary grid visual through `FarmMapView`
- Technical H3 access is reserved for admin/FPO roles
- Grid/H3 data is surfaced safely even when materialized grid rows are not yet present

Known gaps:
- Grid cells are not yet rendered from live polygon coordinates
- Trend and grid materialize endpoints are wired but still need full background job logic
- Bulk upload screen still needs backend endpoint completion for real CSV processing
