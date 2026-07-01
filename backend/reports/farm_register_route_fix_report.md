**Farm Register Route Fix Report**

Root cause:
- `FarmRegister.jsx` was rendering raw API objects directly in select controls, which caused React to throw `Objects are not valid as a React child`.
- The sidebar was using a static link list instead of filtering by the authenticated role.

Files changed:
- [frontend/src/pages/FarmRegister.jsx](/D:/Maati%20Trace/MaatiTrace%20AI/frontend/src/pages/FarmRegister.jsx)
- [frontend/src/components/layout/AppSidebar.jsx](/D:/Maati%20Trace/MaatiTrace%20AI/frontend/src/components/layout/AppSidebar.jsx)
- [frontend/src/lib/rbac/permissions.js](/D:/Maati%20Trace/MaatiTrace%20AI/frontend/src/lib/rbac/permissions.js)
- [frontend/src/lib/api/location.js](/D:/Maati%20Trace/MaatiTrace%20AI/frontend/src/lib/api/location.js)
- [frontend/src/lib/api/farm.js](/D:/Maati%20Trace/MaatiTrace%20AI/frontend/src/lib/api/farm.js)
- [frontend/src/docs/frontend_backend_connection_map.md](/D:/Maati%20Trace/MaatiTrace%20AI/frontend/src/docs/frontend_backend_connection_map.md)

Sidebar RBAC fix:
- `getSidebarItemsForRole(role)` now returns a role-specific navigation set.
- Farmer users now only see Farmer Profile, Register Land, Notifications, Use Cases, and Our Method.
- Admin and FPO users continue to see their allowed items, including My FPO and Bulk Upload where permitted.

Farm registration flow:
- Step 1 loads normalized states, districts, and blocks from the gateway.
- Step 2 links or reuses a farmer profile.
- Step 3 lets the user add polygon points on the map, clear them, undo the last point, or use a sample polygon fallback.
- Step 4 previews the location, farmer, and polygon details before submit.
- Step 5 registers the farm through `/api/farms/register`.
- Step 6 captures a local snapshot with `html2canvas` and attempts upload if a backend endpoint exists.
- Step 7 triggers farm analysis plus trend/grid materialization calls.
- Step 8 redirects to `/land/{farm_id}`.

API endpoints used:
- `GET /api/location/states`
- `GET /api/location/districts?state_name=...`
- `GET /api/location/blocks?state_name=...&district_name=...`
- `POST /api/location/validate`
- `POST /api/h3/preview`
- `POST /api/farms/register`
- `POST /api/farms/{farm_id}/snapshot` when available
- `POST /api/farm-analysis/{farm_id}/materialize`
- `POST /api/hot-stream/farms/{farm_id}/trends/materialize`
- `POST /api/hot-stream/farms/{farm_id}/grid/materialize`

Map polygon behavior:
- Users can click the map preview to add polygon points.
- Points are numbered and turned into GeoJSON Polygon coordinates.
- Undo and clear actions are available.
- A textarea fallback remains available for direct GeoJSON input.

Snapshot behavior:
- After successful registration, a PNG snapshot is captured client-side.
- If the backend snapshot upload route is missing, the snapshot remains stored locally and the flow continues.

Pipeline behavior:
- Farm registration is followed by H3 preview, analysis materialization, and trend/grid materialization attempts.
- Pending endpoints are treated as non-blocking warnings.

Pending backend endpoints:
- Farm snapshot upload endpoint is not confirmed.
- Full trend/grid materialization job implementations may still be pending.

Test checklist:
- Login as farmer and confirm the sidebar no longer shows Admin Dashboard or My FPO.
- Open Register Land and confirm no React object rendering crash.
- Select location values and verify the selected labels show plain text.
- Draw a polygon or paste GeoJSON and submit successfully.
- Confirm redirect to `/land/{farm_id}`.
- Login as admin and confirm the admin sidebar items remain available.
