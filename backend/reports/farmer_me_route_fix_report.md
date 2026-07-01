**Farmer Me Route Fix Report**

Root cause:
- `GET /api/farmers/me` was reaching `farm_registry_service`, but the service depended on local token decoding instead of explicit auth-service lookup.
- Existing linked-profile handling was too generic and did not return the required launch-grade error codes.
- Route order was reviewed and confirmed: `/v1/farmers/me` is defined before `/v1/farmers/{farmer_id}`.

Files changed:
- [auth_client.py](/D:/Maati%20Trace/MaatiTrace%20AI/backend/services/farm_registry_service/app/auth_client.py)
- [main.py](/D:/Maati%20Trace/MaatiTrace%20AI/backend/services/farm_registry_service/app/main.py)
- [repository.py](/D:/Maati%20Trace/MaatiTrace%20AI/backend/services/farm_registry_service/app/repository.py)
- [FarmerProfile.jsx](/D:/Maati%20Trace/MaatiTrace%20AI/frontend/src/pages/FarmerProfile.jsx)

Route order confirmation:
- `/v1/farmers/me` is declared before `/v1/farmers/{farmer_id}`
- `/v1/fpos/me` is declared before `/v1/fpos/{fpo_id}`

Auth forwarding confirmation:
- `farm_registry_service` now reads the incoming `Authorization` header
- It calls `auth_service GET /v1/auth/me`
- It forwards the same bearer token unchanged
- Gateway proxy still preserves `Authorization` and only strips `host`, `content-length`, and `connection`

Exact endpoint behavior:
- `GET /v1/farmers/me`
- Missing token -> `401` with `UNAUTHORIZED`
- Non-farmer user -> `403` with:
  - `code: NOT_A_FARMER_USER`
  - `message: Current user is not a farmer user`
- Farmer user without linked profile -> `404` with:
  - `code: FARMER_PROFILE_NOT_FOUND`
  - `message: No farmer profile is linked to this user`
- Linked farmer user -> `200` with the normal `FarmerResponse`

Frontend redirect behavior:
- Admin login -> `/admin`
- FPO login -> `/fpo/me`
- Farmer login -> `/farmer/me`
- `FarmerProfile.jsx` now blocks non-farmer users from using `/farmer/me` and only loads `/api/farmers/me` for the current farmer route

Repository behavior:
- Added `get_farmer_by_user_id(user_id)`
- This looks up the active `farmer_profiles` row using the authenticated `user_id`

Manual linkage SQL if needed:
```sql
UPDATE farmer_profiles
SET user_id = '<farmer-user-id>'
WHERE farmer_id = '<farmer-id>';
```

Test commands:
- `GET http://localhost:8000/api/farmers/me` with admin token
- `GET http://localhost:8000/api/farmers/me` with farmer token
- `GET http://localhost:8000/api/farmers/{farmer_id}`
- `python -m py_compile backend/services/farm_registry_service/app/main.py`
- `python -m py_compile backend/services/farm_registry_service/app/repository.py`
- `cd frontend && npm run build`

Test results:
- Python compile passed for updated backend files
- Frontend build passed

Remaining manual linkage needed:
- If an older farmer user exists in `users` but still has no matching `farmer_profiles.user_id`, apply the safe update above or complete farmer provisioning through the app flow
