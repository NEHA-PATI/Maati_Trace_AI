# Frontend Backend Connection Map

## Auth
- `frontend/src/lib/api/auth.js` -> `auth_service` direct `/v1/auth/*`
- `Login.jsx` -> `login`
- `SignupFlow.jsx` -> `startSignup`, `verifySignupOtp`, `completeSignup`
- `ProtectedRoute.jsx` -> `getMe`

## Location
- `frontend/src/lib/api/location.js` -> `district_boundary_service` direct `/v1/states`, `/v1/districts`, `/v1/blocks`, `/v1/location/validate`
- `FarmRegister.jsx` -> `getStates`, `getDistricts`, `getBlocks`, `validateLocation`

## Farm and analysis
- `frontend/src/lib/api/farm.js` -> `farm_registry_service` direct `/v1/farms/*` and `boundary_index_service` direct `/v1/h3/preview`
- `frontend/src/lib/api/hotStream.js` -> `hot_stream_orchestrator_service` direct `/v1/hot-stream/*` and `/v1/farm-analysis/*`
- `FarmRegister.jsx` -> create farmer, H3 preview, register farm, analysis materialization
- `LandIntelligence.jsx` -> farm summary, H3 cells, grid cells, grid values, cell details

## Farmer/FPO
- `frontend/src/lib/api/farmer.js` -> `farm_registry_service` direct `/v1/farmers/*`
- `frontend/src/lib/api/fpo.js` -> `farm_registry_service` direct `/v1/fpos/*`
- `FarmerProfile.jsx` -> farmer profile, farms, summary
- `FpoDashboard.jsx` -> FPO profile, farmers, farms, summary
- `MyFpo.jsx` -> current FPO profile
- `Settings.jsx` -> current farmer/FPO profile update and export

## Dashboard/admin
- `AdminDashboard.jsx` -> direct service health, FPO lists, farm lists

## Notes
- No frontend code should call the API gateway in direct mode.
- `frontend/src/lib/api/client.js` is the service client factory and the only network abstraction the UI should use.
