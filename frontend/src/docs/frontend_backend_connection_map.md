# Frontend Backend Connection Map

## Browser entry point
- Browser requests go to the API gateway only.
- The frontend uses `/api/...` routes through `VITE_API_GATEWAY_URL`.
- Backend services stay private and are called directly from service to service.

## Auth
- `frontend/src/lib/api/auth.js` -> gateway `/api/auth/*`
- `Login.jsx` -> `login`
- `SignupFlow.jsx` -> `startSignup`, `verifySignupOtp`, `completeSignup`
- `ProtectedRoute.jsx` -> `getMe`

## Location
- `frontend/src/lib/api/location.js` -> gateway `/api/location/states`, `/api/location/districts`, `/api/location/blocks`, `/api/location/validate`
- `FarmRegister.jsx` -> `getStates`, `getDistricts`, `getBlocks`, `validateLocation`

## Farm and analysis
- `frontend/src/lib/api/farm.js` -> gateway `/api/farms/*` and `/api/h3/preview`
- `frontend/src/lib/api/hotStream.js` -> gateway `/api/hot-stream/*` and `/api/farm-analysis/*`
- `FarmRegister.jsx` -> create farmer, H3 preview, register farm, analysis materialization
- `LandIntelligence.jsx` -> farm summary, H3 cells, grid cells, grid values, cell details

## Farmer/FPO
- `frontend/src/lib/api/farmer.js` -> gateway `/api/farmers/*`
- `frontend/src/lib/api/fpo.js` -> gateway `/api/fpos/*`
- `FarmerProfile.jsx` -> farmer profile, farms, summary
- `FpoDashboard.jsx` -> FPO profile, farmers, farms, summary
- `MyFpo.jsx` -> current FPO profile
- `Settings.jsx` -> current farmer/FPO profile update and export

## Dashboard/admin
- `AdminDashboard.jsx` -> gateway health, FPO lists, farm lists

## Notes
- The UI never talks to backend service URLs directly in production.
- `frontend/src/shared/api/apiClient.js` is the single browser network abstraction.
