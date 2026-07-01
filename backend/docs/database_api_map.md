# Database and API Map

Generated from code inspection of `services/`, `shared/`, `scripts/`, and `data_contracts/sql/`. This document reflects repository state only. It does not inspect the live database contents, so any table existence not backed by checked-in SQL is marked where relevant.

## Service overview

| Service | Port | Functional status from code | DB usage | Outbound service calls |
| --- | --- | --- | --- | --- |
| `boundary_index_service` | 8004 | Active functional service | None | None |
| `DISTRICT_BOUNDARY_SERVICE` | 8005 | Active functional service | Reads `states`, `districts`, `blocks` | None |
| `farm_registry_service` | 8006 | Active functional service | Reads/writes `fpos`, `farmer_profiles`, `farms`; reads `users` | Calls `DISTRICT_BOUNDARY_SERVICE`, `boundary_index_service` |
| `stac_catalog_service` | 8007 | Active functional service | None | External STAC providers only |
| `raster_processor_service` | 8008 | Active functional service | None | Calls `stac_catalog_service`; reads remote raster assets |
| `api_gateway_service` | not specified | Health-only scaffold | None | None |
| `auth_service` | not specified | Health-only scaffold | None in current code | None |
| `analytics_query_service` | not specified | Health-only scaffold | None | None |
| `alert_service` | not specified | Health-only scaffold | None | None |
| `cold_batch_orchestrator_service` | not specified | Health-only scaffold | None | None |
| `dashboard_bff_service` | not specified | Health-only scaffold | None | None |
| `hot_stream_orchestrator_service` | not specified | Health-only scaffold | None | None |
| `lakehouse_writer_service` | not specified | Health-only scaffold | None | None |
| `ml_inference_service` | not specified | Health-only scaffold | None | None |
| `ml_training_service` | not specified | Health-only scaffold | None | None |
| `observability_service` | not specified | Health-only scaffold | None | None |

## Endpoint inventory table

| Endpoint | Method | Owning service | Handler path | Reads tables | Writes tables | Service calls | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/health/live` | GET | all services above | each `app/main.py` | none | none | none | Health-only endpoint |
| `/health/ready` | GET | all services above | each `app/main.py` | none | none | none | Health-only endpoint |
| `/v1/location/stats` | GET | `DISTRICT_BOUNDARY_SERVICE` | `services/district_boundary_service/app/main.py` | `states`, `districts`, `blocks` | none | none | Count query only |
| `/v1/states` | GET | `DISTRICT_BOUNDARY_SERVICE` | same | `states` | none | none | Lists state master |
| `/v1/districts` | GET | `DISTRICT_BOUNDARY_SERVICE` | same | `districts` | none | none | Filtered by `state_name` |
| `/v1/blocks` | GET | `DISTRICT_BOUNDARY_SERVICE` | same | `blocks` | none | none | Filtered by district and state |
| `/v1/location/validate` | POST | `DISTRICT_BOUNDARY_SERVICE` | same | `districts`, `blocks` | none | none | Current active validation endpoint; no change recommended |
| `/v1/fpos` | POST | `farm_registry_service` | `services/farm_registry_service/app/main.py` | `districts`, `blocks`, `fpos` | `fpos` | POST to `/v1/location/validate` | Upsert-like behavior by `registration_number` |
| `/v1/fpos/{fpo_id}` | GET | `farm_registry_service` | same | `fpos` | none | none | Reads only active FPO |
| `/v1/farmers` | POST | `farm_registry_service` | same | `districts`, `blocks`, `users`, `fpos` | `farmer_profiles` | POST to `/v1/location/validate` | `users` and `fpos` existence checks |
| `/v1/farmers/{farmer_id}` | GET | `farm_registry_service` | same | `farmer_profiles` | none | none | Reads only active farmer |
| `/v1/farms/register` | POST | `farm_registry_service` | same | `farmer_profiles`, `fpos`, `districts`, `blocks` | `farms` | POST to `/v1/location/validate`; POST to `/v1/h3/preview` | Also computes area locally |
| `/v1/farms/{farm_id}` | GET | `farm_registry_service` | same | `farms` | none | none | Reads only active farm |
| `/v1/farmers/{farmer_id}/farms` | GET | `farm_registry_service` | same | `farmer_profiles`, `farms` | none | none | Verifies farmer first |
| `/v1/h3/preview` | POST | `boundary_index_service` | `services/boundary_index_service/app/main.py` | none | none | none | Pure geometry/H3 compute |
| `/v1/stac/providers` | GET | `stac_catalog_service` | `services/stac_catalog_service/app/main.py` | none | none | external STAC config only | Returns provider registry |
| `/v1/stac/datasets` | GET | `stac_catalog_service` | same | none | none | none | Static in-code dataset registry |
| `/v1/stac/providers/{provider}/collections` | GET | `stac_catalog_service` | same | none | none | external STAC provider | No local DB |
| `/v1/stac/datasets/availability` | POST | `stac_catalog_service` | same | none | none | external STAC provider | Compares provider collections with in-code registry |
| `/v1/stac/providers/{provider}/collections/{collection_id}/assets` | GET | `stac_catalog_service` | same | none | none | external STAC provider | No local DB |
| `/v1/stac/search` | POST | `stac_catalog_service` | same | none | none | external STAC provider | Returns normalized STAC items |
| `/v1/stac/latest` | POST | `stac_catalog_service` | same | none | none | external STAC provider | Wrapper around search with limit 10 then first item |
| `/v1/raster/sentinel2/indices/preview` | POST | `raster_processor_service` | `services/raster_processor_service/app/main.py` | none | none | remote raster asset reads via scene assets | No local DB |
| `/v1/raster/sentinel2/indices/preview-from-search` | POST | `raster_processor_service` | same | none | none | POST to `stac_catalog_service /v1/stac/search`, then remote raster asset reads | No local DB |

## Endpoint-to-table read/write matrix

| Endpoint | Read tables | Write tables |
| --- | --- | --- |
| `GET /v1/location/stats` | `states`, `districts`, `blocks` | none |
| `GET /v1/states` | `states` | none |
| `GET /v1/districts` | `districts` | none |
| `GET /v1/blocks` | `blocks` | none |
| `POST /v1/location/validate` | `districts`, `blocks` | none |
| `POST /v1/fpos` | `districts`, `blocks`, `fpos` | `fpos` |
| `GET /v1/fpos/{fpo_id}` | `fpos` | none |
| `POST /v1/farmers` | `districts`, `blocks`, `users`, `fpos` | `farmer_profiles` |
| `GET /v1/farmers/{farmer_id}` | `farmer_profiles` | none |
| `POST /v1/farms/register` | `districts`, `blocks`, `farmer_profiles`, `fpos` | `farms` |
| `GET /v1/farms/{farm_id}` | `farms` | none |
| `GET /v1/farmers/{farmer_id}/farms` | `farmer_profiles`, `farms` | none |
| all health, STAC, raster, and H3 endpoints | none | none |

## Service-to-service dependency graph

- `farm_registry_service -> DISTRICT_BOUNDARY_SERVICE`
  Uses `POST /v1/location/validate` before creating FPOs, farmers, and farms.
- `farm_registry_service -> boundary_index_service`
  Uses `POST /v1/h3/preview` during farm registration.
- `raster_processor_service -> stac_catalog_service`
  Uses `POST /v1/stac/search` in `/v1/raster/sentinel2/indices/preview-from-search`.
- `scripts/bulk_pipeline_ingest.py`
  Calls `farm_registry_service`, `raster_processor_service`, and health endpoints.
- `scripts/test_pipeline_cross_district.py`
  Calls `DISTRICT_BOUNDARY_SERVICE`, `farm_registry_service`, `stac_catalog_service`, `raster_processor_service`, and service health endpoints.

## Database table purpose table

| Table | Source of truth in repo | Purpose | Current status | Notes |
| --- | --- | --- | --- | --- |
| `states` | `002_location_master_schema.sql`, `ingest_location_master.py` | state master | active | Used by `DISTRICT_BOUNDARY_SERVICE` and import script |
| `districts` | `002_location_master_schema.sql`, `ingest_location_master.py` | district master | active | Used by validation and lists |
| `blocks` | `002_location_master_schema.sql`, `ingest_location_master.py` | block master | active | Used by validation and lists |
| `users` | `001_operational_schema.sql`, `farm_registry_service` | user identity lookup | active but lightly used | Only validated by `create_farmer`; no create/read user endpoint yet |
| `fpos` | code only in `farm_registry_service` | FPO master | active in code, schema missing in repo | needs_manual_review |
| `fpo_users` | no usage found | FPO-user linking | future / not implemented | Not referenced anywhere in scanned code or SQL |
| `farmer_profiles` | code only in `farm_registry_service` | farmer master/profile | active in code, schema missing in repo | needs_manual_review |
| `farms` | code only in `farm_registry_service` | canonical farm registry in active code | active in code, schema missing in repo | needs_manual_review |
| `pipeline_jobs` | `001_operational_schema.sql` only | orchestration job tracking | future | No current service writes or reads it |
| `farm_alerts` | `001_operational_schema.sql` only | alert history | future | `alert_service` is still health-only |
| `district_boundaries` | not found in code or SQL | polygon boundary store | future / not implemented | User expectation noted, but no checked-in implementation |
| `farmers` | not found in code or SQL | old farmer table name | redundant / dead naming target | Replaced in code by `farmer_profiles` |
| `registered_farms` | `001_operational_schema.sql` only | older farm registry model | redundant / legacy | Conflicts with active `farms` model |

## Redundancy analysis

- `registered_farms` is redundant against active `farms`.
  The live API writes to `farms`, not `registered_farms`. `farm_alerts` still references `registered_farms`, which makes the checked-in operational schema inconsistent with running service logic.
- `farmers` appears to be a legacy conceptual name.
  The live code uses `farmer_profiles` everywhere; no route, SQL, or script uses a table literally named `farmers`.
- `fpo_users` is currently unnecessary in the checked-in code.
  There is no query or endpoint that needs a many-to-many relation between FPOs and users yet.
- `district_boundaries` is not implemented.
  The repo currently uses location master tables plus H3 preview, not stored district polygons.

## Recommended current canonical schema

For the current backend stage, the canonical relational model should be:

- `states`
- `districts`
- `blocks`
- `users`
- `fpos`
- `farmer_profiles`
- `farms`

Recommended relationships:

- `districts.state_code -> states.state_code`
- `blocks.district_code -> districts.district_code`
- `fpos.block_code -> blocks.block_code` nullable
- `farmer_profiles.user_id -> users.user_id` nullable if onboarding allows farmer-first creation
- `farmer_profiles.fpo_id -> fpos.fpo_id` nullable
- `farms.farmer_id -> farmer_profiles.farmer_id`
- `farms.fpo_id -> fpos.fpo_id` nullable

Recommended shape choices for current stage:

- Keep `farmer_profiles` as the canonical farmer table name, since it already carries profile/location data and is what the live service uses.
- Keep `farms` as the canonical farm table name, not `registered_farms`.
- Store farm geometry as JSONB if you want to match current code exactly, or add a generated PostGIS geometry column later for spatial indexing.
- Treat `district_code`, `block_code`, and normalized names on `fpos`, `farmer_profiles`, and `farms` as denormalized convenience fields sourced from `DISTRICT_BOUNDARY_SERVICE`.

## Tables to keep now

- `states`
- `districts`
- `blocks`
- `users`
- `fpos`
- `farmer_profiles`
- `farms`

## Tables to keep for later

- `pipeline_jobs`
- `farm_alerts`
- `district_boundaries`
- `fpo_users`

## Tables to delete/ignore

- `registered_farms`
- `farmers`

## CSV/import file mapping

| File | Maps to table(s) | How |
| --- | --- | --- |
| `data_contracts/csv/states.csv` | `states` | `scripts/ingest_location_master.py` inserts/upserts `state_code`, `state_name` |
| `data_contracts/csv/districts.csv` | `districts` | same script resolves `state_code` via `states` then upserts districts |
| `data_contracts/csv/blocks.csv` | `blocks` | same script resolves `district_code` via `districts` then upserts blocks |
| `data_contracts/csv/maatitrace_bulk_pipeline_template.csv` | indirect: `fpos`, `farmer_profiles`, `farms` | `scripts/bulk_pipeline_ingest.py` reads rows and calls APIs rather than direct SQL |

## Naming mismatch, endpoint mismatch, duplicated table, or dead table

- Schema mismatch: `farm_registry_service` needs `fpos`, `farmer_profiles`, and `farms`, but no checked-in SQL file creates them.
- Schema mismatch: `farm_alerts.farm_id` currently references `registered_farms(farm_id)`, while live code produces `farms.farm_id`.
- Naming mismatch: conceptual `farmers` vs actual implementation `farmer_profiles`.
- Model mismatch: older `registered_farms` PostGIS model vs current `farms` JSONB-plus-H3 model.
- Service naming note: keep `DISTRICT_BOUNDARY_SERVICE` name and `/v1/location/validate` endpoint as-is; both are already consumed by `farm_registry_service` and pipeline scripts.
- Quality note: `raster_processor_service` has an internal comment indicating its H3 aggregation is currently bbox-center based rather than true per-pixel EPSG:4326 H3 mapping. This is not a DB issue, but it is a current behavior risk.

## Recommended cleanup SQL

Do not execute automatically. Review against the live database first.

```sql
-- 1. Preserve core location masters
-- keep: states, districts, blocks

-- 2. Preserve users
-- keep: users

-- 3. Introduce or standardize active farm-registry tables if missing
-- needs_manual_review: exact column/index definitions should be aligned with live DB

-- 4. Decouple future alerts from legacy registered_farms
ALTER TABLE farm_alerts
    DROP CONSTRAINT IF EXISTS farm_alerts_farm_id_fkey;

ALTER TABLE farm_alerts
    ADD CONSTRAINT farm_alerts_farm_id_fkey
    FOREIGN KEY (farm_id) REFERENCES farms(farm_id);

-- 5. Retire legacy registered_farms only after confirming no live dependency
-- DROP TABLE IF EXISTS registered_farms;

-- 6. If a legacy farmers table exists in the live DB and is unused
-- DROP TABLE IF EXISTS farmers;

-- 7. Keep future tables but mark as unused until services are implemented
-- keep: pipeline_jobs, farm_alerts
```

Suggested migration order:

1. Create or verify `fpos`, `farmer_profiles`, and `farms`.
2. Backfill any data from `registered_farms` into `farms` if needed.
3. Repoint `farm_alerts` foreign key from `registered_farms` to `farms`.
4. Only then archive/drop `registered_farms`.

## Risks before frontend development

- The repo schema is not self-consistent.
  A fresh setup from checked-in SQL will not satisfy the active `farm_registry_service`.
- Frontend contract risk exists around canonical entity names.
  UI should bind to `farmer_profiles` and `farms` behavior exposed by API, not to `farmers` or `registered_farms`.
- User onboarding is incomplete.
  `users` is read for validation, but there is no active user creation/read API in the scanned backend.
- Alert and job features are not production-ready.
  Their tables exist in SQL, but the corresponding services are still health-only.
- `district_boundaries` is not implemented.
  Any frontend expecting polygon boundary retrieval from DB will need a separate backend feature.
- Some table existence is `needs_manual_review`.
  The code assumes `fpos`, `farmer_profiles`, and `farms` already exist in the live database, but the repo does not define them.
