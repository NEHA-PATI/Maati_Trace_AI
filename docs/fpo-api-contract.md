# FPO API contract: Classes A, B and C

Source of truth: `backend/services/fpo_management_service/app/main.py`, `service.py`,
`class_b*.py`, `class_c*.py`, and the API gateway proxy. This document describes the
implemented contract; it does not invent fields that are only present in SQL migrations.

## 1. How to call the API

The public gateway base is the configured API gateway URL. Replace the internal `/v1`
prefix below with `/api` and use the matching gateway prefix:

| Internal service path | Public gateway path |
|---|---|
| `/v1/fpo/me/...` | `/api/fpo/me/...` |
| `/v1/fpo-portal/...` | `/api/fpo-portal/...` |
| `/v1/admin/fpo/...` | `/api/admin/fpo/...` (gateway requires an admin role) |
| `/v1/farmer/...` | `/api/farmer/...` |
| `/v1/farmers/...` | `/api/farmers/...` |

All protected endpoints require `Authorization: Bearer <token>`. JSON requests use
`Content-Type: application/json`. UUID path parameters must be valid UUIDs.

## 1.1 FPO-01 signup, provisioning and organization identity

FPO signup is completed only after email OTP verification. Auth creates the verified
user and an `auth.user.created` outbox event in the same database transaction. The
Auth-owned publisher delivers FPO events to the authenticated internal ingestion route;
FPO Management persists them in its own inbox and provisions the organization. It then
calls Profile Service to create or recover the FPO profile and owner membership. FPO
Management links the profile and marks the organization `READY` only after Profile
Service confirms success:

```text
OTP verified
  -> Auth user + outbox event (same transaction)
  -> Auth FPO event publisher
  -> authenticated FPO inbox
  -> FPO organization + stable public FPO ID
  -> authenticated Profile Service provisioning
  -> profile + owner membership
  -> organization/profile link
  -> READY
```

The public FPO ID is independent from the Auth user UUID and Profile Service profile
UUID. It is generated once from the canonical numeric state code, event year, global
FPO sequence, and check character; existing IDs are not rewritten.

The authenticated user's `GET /v1/fpo-portal/bootstrap-status` response exposes
`schema_version`, `status`, `step`, `retryable`, `next_poll_after_seconds`,
`correlation_id`, `organization`, `attempt_count`, and a safe `error` object when
provisioning has failed. The UI polls this endpoint until the organization is ready or
the user is shown a recovery/support state. FPO feature and verification routes remain
blocked until provisioning is ready.

Admin recovery endpoints (admin role required):

| Method and path | Request | Response |
|---|---|---|
| `GET /v1/admin/fpo/provisioning` | Optional `status` (`RECEIVED`, `PROCESSING`, `PROCESSED`, `FAILED`, `DEAD`), `limit` 1–100, and `offset` | Provisioning cases with event, organization, attempts, correlation, and safe error details. |
| `GET /v1/admin/fpo/provisioning/{fpo_id}` | FPO organization UUID | Provisioning details and latest event. |
| `POST /v1/admin/fpo/provisioning/events/{event_id}/retry` | `{"reason":"..."}` (3–1,000 characters) | Retry queued; previous attempt count and reason are retained in the audit event. |
| `POST /v1/admin/fpo/provisioning/{fpo_id}/retry` | `{"reason":"..."}` (3–1,000 characters) | Retry queued for the organization's latest event. |
| `GET /metrics` | None | Prometheus text-format queue, delivery, retry, failure, and duration metrics. |

The event ingestion and Profile Service provisioning routes are internal service-to-
service endpoints, not browser APIs. They require `X-Internal-Service-Token`; never
expose either token to the frontend. Both shared tokens must contain at least 32 bytes.
Configure `FPO_EVENT_DELIVERY_TOKEN` identically for Auth and FPO Management, and
`PROFILE_INTERNAL_SERVICE_TOKEN` identically for FPO Management and Profile Service.
The localhost URL defaults are for single-host local development. In container or
multi-host deployments, set `FPO_EVENT_INGESTION_URL` and `PROFILE_SERVICE_URL` to the
internal service DNS names and listening ports.

Apply `backend/data_contracts/sql/fpo_sql/20261102_39_fpo_provisioning_delivery.sql`
after the existing FPO schema migrations. From `backend/`, apply the forward migration:

```powershell
psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f data_contracts/sql/fpo_sql/20261102_39_fpo_provisioning_delivery.sql
```

Run the Auth publisher as a separate worker process with
`python -m services.auth_service.app.fpo_event_worker`, and keep the existing
`python -m services.fpo_management_service.worker` running. The FPO Management
readiness endpoint remains not-ready until the migration, both tokens, Profile Service,
and a current worker heartbeat are available.
In VS Code, start both from the `MaatiTrace: FPO Provisioning Workers` task after
configuring the tokens in the Auth and FPO Management service `.env` files.

### Common errors

Authentication/authorization errors are JSON objects of this shape:

```json
{"detail":{"code":"AUTH_REQUIRED","message":"Authentication is required."}}
```

Typical statuses are `401` (missing/invalid token), `403` (wrong role, unavailable
feature, or FPO gate), `404` (unknown resource), `409` (invalid state transition or
conflict), `422` (Pydantic validation or domain validation), and `503` (document/import
storage unavailable). Validation failures generated by FastAPI have the standard
shape `{"detail":[{"loc":[...],"msg":"...","type":"..."}]}`.

Successful responses are not wrapped in a common `data` envelope. GET collection
operations return arrays; GET summary/read-model operations return objects; mutation
operations return the created or updated database row/object. Timestamps are normally
ISO-8601 strings and UUIDs are strings in JSON.

## 2. Class A — foundation, access, relationships and FPO workspace

Class A is the foundation layer. It is not exposed under a literal `/class-a` URL.
The implemented routes are the portal, verification, relationship, entitlement,
directory, dashboard, alert, and admin feature-control routes.

### A.1 Portal and verification

| Method and path | Request payload | Response |
|---|---|---|
| `GET /v1/fpo-portal/bootstrap-status` | None | Bootstrap/provisioning status object. Includes the current account/FPO readiness state and gate information. |
| `GET /v1/fpo-portal/bootstrap` or `GET /v1/fpo/me/bootstrap` | None | Portal bootstrap object: FPO context, verification/provisioning state, plan/entitlement information, and initial dashboard metadata. |
| `GET /v1/fpo-portal/verification` | None | Current verification status object. |
| `GET /v1/fpo/me/documents` | None | Array of the authenticated FPO's verification document metadata. |
| `POST /v1/fpo/me/documents/upload-intents` | `DocumentUploadIntentRequest` | `201`; upload-intent/document metadata, including document ID and storage upload information. |
| `PUT /v1/fpo/me/documents/{document_id}/content` | Raw binary body; `Content-Type` must identify the file; max 20 MiB | Upload/storage result object. |
| `POST /v1/fpo/me/documents/{document_id}/finalize` | `{"checksum": "<32-128 chars>"}` | Finalized document metadata/status. |
| `DELETE /v1/fpo/me/documents/{document_id}` | None | Deleted document/result object. |
| `POST /v1/fpo-portal/verification/submit` | None | `201`; submitted verification case/status. |
| `PATCH /v1/fpo-portal/admin/organizations/{fpo_id}/verification` | `VerificationDecision` | Updated verification case/status. Admin only. |
| `GET /v1/fpo-portal/admin/organizations/{fpo_id}/verification/documents` | None | Array of document metadata for the FPO. Admin only. |
| `GET /v1/fpo-portal/admin/verification/documents/{document_id}/content` | None | Raw file bytes with the stored MIME type and inline filename. Admin only. |
| `GET /v1/fpo-portal/admin/organizations/{fpo_id}/verification/checklist` | None | Array of checklist results. Admin only. |
| `PATCH /v1/fpo-portal/admin/verification/checklist/{result_id}` | `VerificationChecklistUpdate` | Updated checklist result. Admin only. |
| `GET /v1/fpo-portal/admin/verification-queue` or `GET /v1/admin/fpo-verification-cases` | Query `status` optional | Verification-case array. Admin only. |
| `GET /v1/admin/fpo/overview` | None | Admin FPO overview/aggregate object. Admin only. |
| `PATCH /v1/fpo-portal/admin/verification/documents/{document_id}` or `PATCH /v1/admin/fpo-verification-documents/{document_id}` | `DocumentValidationRequest` | Updated document validation status. Admin only. |

`DocumentUploadIntentRequest`:

```json
{
  "document_type": "REGISTRATION_CERTIFICATE",
  "filename": "certificate.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 245760,
  "checksum": "sha256-or-other-checksum-with-32-to-128-chars"
}
```

Fields: `document_type` string 2–80, `filename` string 1–255, `mime_type` string 3–120,
`size_bytes` integer >0 and <=20,971,520, `checksum` string 32–128. Extra fields are
rejected.

`DocumentFinalizeRequest` is exactly `{checksum: string}` with checksum length 32–128.
`VerificationDecision` requires `status` in `UNDER_REVIEW|APPROVED|CHANGES_REQUIRED|REJECTED`
and optional `note` up to 2,000 chars. `VerificationChecklistUpdate` requires
`result` in `PENDING|PASS|FAIL|NOT_APPLICABLE` and optional `note` up to 1,000 chars.
`DocumentValidationRequest` requires `validation_status` in `VALID|INVALID` and optional
`reason` up to 1,000 chars.

### A.2 FPO/farmer relationship and workspace reads

| Method and path | Request/query | Response |
|---|---|---|
| `GET /v1/fpo-portal/discover` | Farmer/admin; `query` optional, `limit` 1–100, default 25 | FPO directory array. |
| `GET /v1/farmer/fpo-consent-policy` | Farmer | Current published consent policy, version, required and optional scopes. |
| `GET /v1/farmer/fpo-relationships` | Farmer/admin | Farmer relationship array. |
| `GET /v1/farmer/farms/{farm_id}/fpo-relationships` | Farmer/admin | Relationships for one farm only. |
| `POST /v1/farmer/farm-relationships` | `RelationshipRequest` including `farm_id` | `201`; created farm-scoped relationship/request. |
| `POST /v1/farmer/fpo-relationships` | Backward-compatible alias; `RelationshipRequest` still requires `farm_id` | `201`; created farm-scoped relationship/request. |
| `GET /v1/fpo-portal/relationships` | FPO/admin | Relationship-request array. |
| `GET /v1/fpo-portal/farm-relationships` | FPO/admin; canonical farm-request inbox path | Same farm-scoped relationship-request array. |
| `PATCH /v1/fpo-portal/relationships/{relationship_id}` | `{"decision":"ACTIVE"}` or `{"decision":"REJECTED"}` | Updated relationship. |
| `PATCH /v1/fpo-portal/farm-relationships/{relationship_id}` | `{"decision":"ACTIVE|REJECTED","note":"..."}` | Updated farm-scoped relationship; note is optional. |
| `DELETE /v1/farmer/fpo-relationships/{relationship_id}` | Farmer only | Revoked relationship. |
| `DELETE /v1/farmer/farms/{farm_id}/fpo-relationships/{relationship_id}` | Farmer only | Revoked relationship for the exact farm. |
| `POST /v1/farmers/me/fpo-relationship-requests/{relationship_id}/cancel` | Farmer only | Cancelled request. |
| `POST /v1/fpo-portal/relationships/{relationship_id}/terminate` or `/v1/fpo/me/relationships/{relationship_id}/terminate` | `{"reason":"..."}` | Terminated relationship. |
| `GET /v1/fpo-portal/entitlements` or `/v1/fpo/me/entitlements` | FPO/admin | Entitlement array/object, including feature keys and enabled state. |
| `GET /v1/fpo-portal/reports/portfolio` | FPO/admin | Portfolio report read model. |
| `GET /v1/fpo-portal/dashboard` or `/v1/fpo/me/dashboard` | FPO/admin | Dashboard read model. |
| `GET /v1/fpo-portal/farmers` or `/v1/fpo/me/farmers` | `query`, `district_code`, `block_code`, `relationship_status`, `cursor`, `limit` 1–100 default 50 | Paginated farmer directory object, including farmer rows and continuation cursor when available. |
| `GET /v1/fpo/me/farmers/{farmer_id}` | FPO only | Farmer detail object. |
| `GET /v1/fpo/me/farmers/{farmer_id}/farms` | FPO only | Farmer farm array. |
| `GET /v1/fpo/me/farmers/{farmer_id}/farms/{farm_id}/intelligence` | FPO only | Farm intelligence/read-model object. |
| `GET /v1/fpo-portal/alerts` | `status` optional | Operational-alert array. |
| `PATCH /v1/fpo-portal/alerts/{alert_id}/acknowledge` | None | Acknowledged alert object. |

`RelationshipRequest` requires `fpo_id`, `farm_id` UUIDs, the published `policy_code` and
`policy_version`, and an explicit `accepted: true` after the farmer reviews the policy.
The currently published policy is obtained from `GET /v1/farmer/fpo-consent-policy`;
`selected_optional_scopes` is a string array max 20. A farm may have pending and active
relationships with multiple FPOs. Duplicate pending or active relationships for the same
FPO/farm are prevented. FPO review/portfolio access is scoped to that farm and requires
an active relationship and valid consent. Farmer contact is masked in the FPO request inbox.
`RelationshipTermination` requires
`reason` 3–1,000 chars. All models reject unknown fields.

### A.3 Admin class/feature control

| Method and path | Payload | Response |
|---|---|---|
| `GET /v1/fpo-portal/admin/features/catalogue` or `GET /v1/admin/fpo/features` | None | Feature catalogue array. Admin only. |
| `PATCH /v1/fpo-portal/admin/organizations/{fpo_id}/class` | `{"class_code":"A|B|C"}` (case-insensitive input) | Updated FPO class/plan assignment. Admin only. |
| `POST /v1/fpo-portal/admin/organizations/{fpo_id}/feature-overrides` | `FeatureOverrideRequest` | `201`; created override. Admin only. |
| `GET /v1/fpo-portal/admin/organizations/{fpo_id}/feature-overrides` | None | Override array. Admin only. |
| `POST /v1/fpo-portal/admin/reconciliation/run` | None | Reconciliation result/summary. Admin only. |

`FeatureOverrideRequest` requires `feature_key` (2–100), `enabled` boolean, and `reason`
(3–1,000); `expires_at` is optional datetime.

## 3. Class B — portfolio organization, monitoring, advisory and planning

All authenticated Class B FPO routes below require role `fpo`; otherwise the service
returns `403 FPO_ROLE_REQUIRED`. Class B also requires the relevant feature entitlement
and the FPO's published plan. Most creates return `201`.

### B.1 Shared `ClassBPayload`

The following JSON object is accepted by all Class B mutation routes unless stated
otherwise. Every field is optional at the Pydantic layer; the operation's service logic
decides which fields are required. Unknown fields are rejected.

```json
{
  "name": "North Block Farmers",
  "description": "High moisture-risk farmers",
  "color_token": "emerald",
  "criteria": {},
  "segment_type": "DYNAMIC",
  "note_type": "GENERAL",
  "title": "Field visit",
  "content": "Inspect irrigation",
  "follow_up_at": "2026-10-01T09:00:00Z",
  "season_code": "KHARIF",
  "season_year": 2026,
  "planning_start_date": "2026-06-01",
  "season_start_date": "2026-06-01",
  "season_end_date": "2026-10-31",
  "geography_filter": {},
  "notes": "...",
  "crop_code": "RICE",
  "variety_code": "IR64",
  "target_area_acres": 10.5,
  "target_farmer_count": 100,
  "target_farm_count": 120,
  "task_type": "FOLLOW_UP",
  "priority": "NORMAL",
  "farmer_id": "00000000-0000-0000-0000-000000000000",
  "due_at": "2026-10-01T09:00:00Z",
  "status": "IN_PROGRESS",
  "feature_metric": "NDVI",
  "scope_type": "FPO",
  "scope_configuration": {},
  "condition_configuration": {},
  "severity": "HIGH",
  "deduplication_window_minutes": 60,
  "cooldown_minutes": 120,
  "template_id": "00000000-0000-0000-0000-000000000000",
  "segment_id": "00000000-0000-0000-0000-000000000000",
  "channel": "SMS",
  "language_strategy": "FIXED",
  "fixed_language_code": "en",
  "variables": {},
  "season_plan_id": "00000000-0000-0000-0000-000000000000",
  "report_type": "PORTFOLIO",
  "format": "CSV",
  "idempotency_key": "client-key",
  "template_code": "WATER_STRESS",
  "advisory_type": "IRRIGATION",
  "language_code": "en",
  "title_template": "...",
  "body_template": "...",
  "decision": "APPROVE",
  "reason": "Release approved"
}
```

Validation: strings with explicit limits are `name` <=240, `description` <=2,000,
`color_token` <=40, `title` <=240, `content` <=10,000, `season_code` <=50,
`notes`/`reason` <=2,000/1,000, `crop_code`/`variety_code` <=80, `task_type` <=40,
`status`/`severity`/`channel`/`language_strategy`/`report_type`/`format`/`template_code`/
`advisory_type`/`language_code` unconstrained except where noted, `priority` is
`LOW|NORMAL|HIGH|URGENT`, `segment_type` is `DYNAMIC|STATIC`, and `note_type` is
`GENERAL|FOLLOW_UP|VISIT|DATA_QUALITY|ADVISORY`. Numeric/date/UUID fields use the
corresponding JSON number, ISO datetime/date string, or UUID representation.

### B.2 Class B endpoint catalogue

| Method and path | Payload/query | Response |
|---|---|---|
| `GET /v1/fpo/me/import-templates/{import_type}` | Path `FARMERS`, `FARMS`, or `FARMERS_AND_FARMS` | Template/schema object. |
| `POST /v1/fpo/me/imports/upload-intents` | `ImportIntentRequest` | `201`; import job/upload intent. |
| `PUT /v1/fpo/me/imports/{job_id}/content` | Raw CSV/XLSX bytes | Upload result/job status. |
| `POST /v1/fpo/me/imports/{job_id}/validate` | None | Validation result/job including row counts/errors. |
| `GET /v1/fpo/me/imports` | None | Import-job array. |
| `GET /v1/fpo/me/imports/{job_id}` | None | Import job object. |
| `GET /v1/fpo/me/imports/{job_id}/rows` | None | Import-row array with row-level validation details. |
| `POST /v1/fpo/me/imports/{job_id}/commit` | None | Committed job/result summary. |
| `POST /v1/fpo/me/imports/{job_id}/cancel` | None | Cancelled job. |
| `GET /v1/fpo/me/data-quality/summary` | None | Quality aggregate object. |
| `GET /v1/fpo/me/data-quality/issues` | None | Quality-issue array. |
| `GET /v1/fpo/me/tags` | None | Tag array. |
| `POST /v1/fpo/me/tags` | `ClassBPayload` (`name`, `description`, `color_token` used) | `201`; tag row. |
| `POST /v1/fpo/me/farmers/{farmer_id}/tags/{tag_id}` | None | Farmer-tag association row. |
| `GET /v1/fpo/me/segments` | None | Segment array. |
| `POST /v1/fpo/me/segments` | `ClassBPayload` (`name`, `segment_type`, `criteria`, `geography_filter` used) | `201`; segment row. |
| `POST /v1/fpo/me/segments/{segment_id}/evaluate` | None | Evaluation result/counts and updated segment state. |
| `GET /v1/fpo/me/segments/{segment_id}/farmers` | None | Segment-member farmer array. |
| `GET /v1/fpo/me/farmers/{farmer_id}/notes` | None | Note array. |
| `POST /v1/fpo/me/farmers/{farmer_id}/notes` | `ClassBPayload` (`note_type`, `title`, `content`, `follow_up_at` used) | `201`; note row. |
| `GET /v1/fpo/me/season-plans` | None | Season-plan array. |
| `POST /v1/fpo/me/season-plans` | `ClassBPayload` (`season_code`, `season_year`, dates, notes used) | `201`; season plan. |
| `POST /v1/fpo/me/season-plans/{plan_id}/crop-targets` | `ClassBPayload` (crop/variety/target fields used) | `201`; crop-target row. |
| `GET /v1/fpo/me/tasks` | None | Task array. |
| `POST /v1/fpo/me/tasks` | `ClassBPayload` (`task_type`, `priority`, `farmer_id`, `due_at`, `content` used) | `201`; task row. |
| `PATCH /v1/fpo/me/tasks/{task_id}` | `ClassBPayload`; only `status` and `content` are passed to service | Updated task. |
| `GET /v1/fpo/me/monitoring/summary` | None | Monitoring summary/read model. |
| `GET /v1/fpo/me/alert-rules` | None | Alert-rule array. |
| `GET /v1/fpo/me/alert-rules/metrics` | None | Metric-registry array. |
| `POST /v1/fpo/me/alert-rules` | `ClassBPayload` (metric/scope/condition/severity/dedup/cooldown used) | `201`; alert rule. |
| `POST /v1/fpo/me/alert-rules/{rule_id}/publish` | None | Published rule. |
| `POST /v1/fpo/me/alert-rules/{rule_id}/pause` | None | Paused rule. |
| `GET /v1/fpo/me/advisory-templates` | None | Published advisory-template array. |
| `POST /v1/fpo/me/advisories/preview` | `ClassBPayload` (template/segment/channel/language/variables used) | Preview object containing rendered content/recipient context. |
| `GET /v1/fpo/me/campaigns` | None | Campaign array. |
| `POST /v1/fpo/me/campaigns` | `ClassBPayload` (template/segment/channel/language fields used) | `201`; campaign. |
| `POST /v1/fpo/me/campaigns/{campaign_id}/estimate` | None | Audience/delivery estimate object. |
| `POST /v1/fpo/me/campaigns/{campaign_id}/schedule` | None | Scheduled campaign. |
| `GET /v1/fpo/me/input-demand-plans` | None | Input-demand-plan array. |
| `POST /v1/fpo/me/input-demand-plans` | `ClassBPayload` (season plan, crop, targets and notes used) | `201`; input-demand plan. |
| `POST /v1/fpo/me/input-demand-plans/{plan_id}/calculate` | None | Calculation result/updated plan. |
| `GET /v1/fpo/me/input-demand-plans/{plan_id}/items` | None | Calculated input-item array. |
| `GET /v1/fpo/me/yield-forecasts` | None | Forecast array. |
| `POST /v1/fpo/me/yield-forecasts/run` | `ClassBPayload` (season/crop/geography/idempotency fields used) | `201`; forecast/result. |
| `GET /v1/fpo/me/reports/catalogue` | None | Report-definition array. |
| `GET /v1/fpo/me/report-jobs` | None | Report-job array. |
| `POST /v1/fpo/me/report-jobs` | `ClassBPayload` (`report_type`, `format`, filters, `idempotency_key` used) | `201`; report job. |

`ImportIntentRequest` requires `import_type` in `FARMERS|FARMS|FARMERS_AND_FARMS`,
`source_format` in `CSV|XLSX` (case-insensitive), `filename` 1–255, and `checksum`
32–128 chars. The raw upload endpoints do not parse JSON; send the file bytes.

### B.3 Class B admin/release endpoints

| Method/path | Payload | Response |
|---|---|---|
| `GET /v1/admin/fpo/class-b/advisory-templates` | None | Template array. Admin only. |
| `POST /v1/admin/fpo/class-b/advisory-templates` | `ClassBPayload` (template fields) | `201`; draft template. |
| `PATCH /v1/admin/fpo/class-b/advisory-templates/{template_id}` | `ClassBPayload`; `decision` is used, default `REJECT` | Reviewed template. |
| `GET /v1/admin/fpo/class-b/release-readiness` | None | `{plan, checks, ready}` release-readiness object. |
| `POST /v1/admin/fpo/class-b/publish` | `ClassBPayload`; `reason` used, default release message | Published plan/version row. |

The readiness response is an object with the selected plan, an array of check objects
(check key/status/evidence), and boolean `ready`. Publishing returns `409` if readiness
or plan state prevents publication.

## 4. Class C — commercial execution, traceability and enterprise integrations

Class C FPO endpoints use the same FPO role/entitlement/plan gates as Class B. GETs
return arrays or read-model objects; POST/PATCH action endpoints return the affected row
or action result. The service returns database columns as JSON rather than a separate
Pydantic response envelope.

### C.1 Typed request payloads

All these models reject unknown fields.

**Counterparty (`ClassCCounterpartyPayload`)** — required: `counterparty_code` (2–40),
`counterparty_type` (`BUYER|EXPORTER|PROCESSOR|RETAILER|INSTITUTIONAL_BUYER|LOGISTICS_PROVIDER|LABORATORY|WAREHOUSE_OPERATOR|LENDER|INSURER|OTHER`), and `legal_name` (2–200).
Optional: `trade_name` <=200, `registration_number` <=80, `tax_identifier` <=120,
`country_code` default `IN` length 2, `state_code`/`district_code` <=20,
`address_line_1`/`address_line_2` <=200, `postal_code` <=20, `website_url` <=500,
`preferred_currency` default `INR` length 3, `payment_terms_code` <=40,
`risk_rating` <=20, `notes` <=4,000, `due_diligence_status`, `reason` <=1,000.

**Opportunity (`ClassCOpportunityPayload`)** — required `opportunity_code` 2–40,
`counterparty_id` UUID, `title` 2–200, `commodity_code` 2–50,
`target_quantity` >0, and `quantity_unit` 1–20. Optional `variety_code`/`quality_grade_code`
<=50, `target_price` >=0, `currency_code` default `INR` length 3,
`delivery_start_date`/`delivery_end_date`, `delivery_location_text` <=300,
`source_channel` default `DIRECT` <=30, `probability_percent` 0–100,
`owner_notes` <=4,000, `stage`, and `reason` <=1,000.

**Procurement (`ClassCProcurementPayload`)** — all optional except defaulted
`currency_code` (`INR`). Fields: `plan_code` 2–40, `name` <=180, `season_code` <=40,
`season_year` 2000–2200, `start_date`, `end_date`, `notes` <=2,000,
`commodity_code`/`variety_code`/`quality_grade_code` <=50, `district_code`/`block_code` <=20,
`target_quantity` >0, `quantity_unit` <=20, `forecast_available_quantity` >=0,
`target_min_price`/`target_max_price` >=0, `shortfall_threshold_percent` 0–100,
`status`, `reason` <=1,000.

**Lot (`ClassCLotPayload`)** — all optional. `lot_code` 2–60, `procurement_plan_id`,
`commodity_code`/`variety_code` <=50, `crop_year` 2000–2200, `season_code` <=40,
`quantity_unit` <=20, farmer/farm/crop-cycle/relationship/consent UUIDs,
`source_receipt_code` <=60, `gross_quantity` >0, `deduction_quantity` default 0 >=0,
`accepted_quantity` >=0, `rejected_quantity` default 0 >=0, `declared_harvest_date`,
`collection_point_code` <=60, `source_grade_code` <=50, `source_price` >=0,
`currency_code` <=3, and `source_snapshot` object default `{}`.

**Quality (`ClassCQualityPayload`)** — optional `lot_id`, `quality_schema_id`,
`measured_values` object default `{}`, `disposition`, `calculated_grade_code` <=50,
`reviewer_note` <=2,000.

**Warehouse (`ClassCWarehousePayload`)** — required `warehouse_code` 2–50 and `name`
2–180; optional `address_text` <=500, `capacity_quantity` >=0, `quantity_unit` <=20.

**Inventory (`ClassCInventoryPayload`)** — optional `lot_id`, `warehouse_id`,
`location_code` <=60, `grade_code` <=50, `entry_type`, `quantity` >0,
`quantity_unit` <=20, `reference_code` <=80, `reason` <=1,000.

**Quality schema (`ClassCQualitySchemaPayload`)** — required `schema_key` 2–100,
`name` 2–180, `commodity_code` 2–50; `version` default 1 >=1,
`jurisdiction_code` <=30, `grade_definitions` and `parameter_definitions` arrays of objects.

**Contract (`ClassCContractPayload`)** — required `contract_code` 2–60,
`counterparty_id` UUID, `title` 2–200, `contract_type` 2–30, `effective_date`.
Optional: `opportunity_id`, `expiry_date`, `currency_code` default `INR` length 3,
`value_amount` >=0, `incoterm_code` <=20, `payment_terms_code` <=40,
`delivery_terms` <=2,000, `source_document_artifact_id`, `source_document_checksum` <=128.

**Order (`ClassCOrderPayload`)** — required `order_code` 2–60, `counterparty_id` UUID,
and `lines` array of 1–100 objects. Optional `contract_id`, `opportunity_id`,
`buyer_purchase_order_ref` <=120, delivery dates, `delivery_address_text` <=400,
`currency_code` default `INR` length 3.

**Dispatch (`ClassCDispatchPayload`)** — required only for dispatch creation:
`dispatch_code` 2–60. Optional `order_id`, `warehouse_id`, `logistics_counterparty_id`,
`transport_document_ref` <=120, `scheduled_departure_at`, `dispatch_id`, `order_line_id`,
`inventory_lot_id`, `quantity` >0, `quantity_unit` <=20, `package_count` >=1,
`package_type_code` <=40, `traceability_code` <=80. Item creation uses the item fields.

**Compliance (`ClassCCompliancePayload`)** — required `document_type_code` 2–60;
optional `issuing_authority` <=200, issue/expiry dates, `country_code` default `IN`
length 2, `artifact_id`, `checksum` <=128.

**Export (`ClassCExportPayload`)** — required `pack_code` 2–80,
`destination_code` 2–50, `commodity_code` 2–50, and `template_key` 2–100;
optional `order_id`, `lot_id`.

**Data pack (`ClassCDataPackPayload`)** — required `schema_id` UUID,
`purpose_code` 2–80, `recipient_category` 2–40; optional `recipient_id` UUID and
`farmer_ids` UUID array max 500.

**Integration (`ClassCIntegrationPayload`)** — `client_name` optional 2–160,
`scopes` string array max 20, `rate_limit_per_minute` default 60 range 1–1000,
`expires_at`, `name` optional 2–160, `endpoint_url` <=500, and `event_types`
string array max 50. API-client creation requires `client_name` and at least one
allowed scope (`TRACEABILITY_READ`, `PROCUREMENT_READ`, `INVENTORY_READ`, `ORDER_READ`,
or `WEBHOOK_MANAGE`) in service logic. Webhook URLs must start with `https://`.

### C.2 Class C endpoint catalogue

| Method and path | Payload/query | Response |
|---|---|---|
| `GET /v1/fpo/me/class-c/counterparties` | None | Counterparty array. |
| `POST /v1/fpo/me/class-c/counterparties` | Counterparty payload | `201`; counterparty row. |
| `PATCH /v1/fpo/me/class-c/counterparties/{counterparty_id}/due-diligence` | Counterparty payload; `due_diligence_status` and `reason` used | Updated due-diligence/counterparty row. |
| `GET /v1/fpo/me/class-c/opportunities` | None | Opportunity array. |
| `POST /v1/fpo/me/class-c/opportunities` | Opportunity payload | `201`; opportunity row. |
| `PATCH /v1/fpo/me/class-c/opportunities/{opportunity_id}/stage` | Opportunity payload; `stage`, `reason` used | Updated opportunity. |
| `GET /v1/fpo/me/class-c/procurement-plans` | None | Procurement-plan array. |
| `POST /v1/fpo/me/class-c/procurement-plans` | Procurement payload | `201`; plan row. |
| `GET /v1/fpo/me/class-c/procurement-plans/{plan_id}/items` | None | Procurement-item array. |
| `POST /v1/fpo/me/class-c/procurement-plans/{plan_id}/items` | Procurement payload; item fields used | `201`; item row. |
| `PATCH /v1/fpo/me/class-c/procurement-plans/{plan_id}/status` | Procurement payload; `status`, `reason` used | Updated plan. |
| `GET /v1/fpo/me/class-c/lots` | None | Aggregation-lot array. |
| `POST /v1/fpo/me/class-c/lots` | Lot payload | `201`; lot row. |
| `GET /v1/fpo/me/class-c/lots/{lot_id}/sources` | None | Lot-source array. |
| `POST /v1/fpo/me/class-c/lots/{lot_id}/sources` | Lot payload; source fields used | `201`; lot-source row. |
| `POST /v1/fpo/me/class-c/lots/{lot_id}/seal` | None | Sealed lot row/status. |
| `GET /v1/fpo/me/class-c/quality/inspections` | None | Inspection array. |
| `POST /v1/fpo/me/class-c/quality/inspections` | Quality payload | `201`; inspection row and test-result data when generated. |
| `PATCH /v1/fpo/me/class-c/quality/inspections/{inspection_id}/review` | Quality payload; `disposition` default `HOLD`, grade/note used | Reviewed inspection. |
| `GET /v1/fpo/me/class-c/warehouses` | None | Warehouse array. |
| `POST /v1/fpo/me/class-c/warehouses` | Warehouse payload | `201`; warehouse row. |
| `GET /v1/fpo/me/class-c/inventory` | None | Inventory-lot/stock array. |
| `POST /v1/fpo/me/class-c/inventory/lots` | Inventory payload | `201`; inventory-lot row. |
| `POST /v1/fpo/me/class-c/inventory/lots/{inventory_lot_id}/ledger` | Inventory payload | `201`; inventory-ledger entry. |
| `POST /v1/fpo/me/class-c/inventory/reconcile` | None | Inventory reconciliation summary. |
| `GET /v1/fpo/me/class-c/contracts` | None | Contract array. |
| `POST /v1/fpo/me/class-c/contracts` | Contract payload | `201`; contract row. |
| `POST /v1/fpo/me/class-c/contracts/{contract_id}/activate` | None | Activated contract. |
| `GET /v1/fpo/me/class-c/orders` | None | Order array. |
| `POST /v1/fpo/me/class-c/orders` | Order payload | `201`; order and line data. |
| `POST /v1/fpo/me/class-c/orders/{order_id}/confirm` | None | Confirmed order. |
| `GET /v1/fpo/me/class-c/dispatches` | None | Dispatch array. |
| `POST /v1/fpo/me/class-c/dispatches` | Dispatch payload | `201`; dispatch row. |
| `POST /v1/fpo/me/class-c/dispatches/{dispatch_id}/items` | Dispatch payload; item fields used | `201`; dispatch-item row. |
| `POST /v1/fpo/me/class-c/dispatches/{dispatch_id}/depart` | None | Departed dispatch/status. |
| `GET /v1/fpo/me/class-c/compliance/documents` | None | Compliance-document array. |
| `POST /v1/fpo/me/class-c/compliance/documents` | Compliance payload | `201`; compliance-document row. |
| `GET /v1/fpo/me/class-c/compliance/readiness` | None | Compliance readiness object with requirement/document status. |
| `GET /v1/fpo/me/class-c/export-packs` | None | Export-pack array. |
| `POST /v1/fpo/me/class-c/export-packs` | Export payload | `201`; export-pack row. |
| `GET /v1/fpo/me/class-c/data-packs/schemas` | None | Published data-pack schema array. |
| `POST /v1/fpo/me/class-c/data-packs` | Data-pack payload | `201`; data-pack request. |
| `POST /v1/fpo/me/class-c/data-packs/{request_id}/validate-consent` | None | Consent-validation result, including eligible/excluded farmers and request status. |
| `GET /v1/fpo/me/class-c/sustainability/metrics` | None | Sustainability-metric array. |
| `GET /v1/fpo/me/class-c/integrations/api-clients` | None | API-client array; secrets are not returned. |
| `POST /v1/fpo/me/class-c/integrations/api-clients` | Integration payload | `201`; client metadata plus one-time `client_secret` and `secret_display_warning`. |
| `POST /v1/fpo/me/class-c/integrations/api-clients/{client_id}/rotate-secret` | None | Client metadata plus one-time new `client_secret` and warning. |
| `POST /v1/fpo/me/class-c/integrations/api-clients/{client_id}/revoke` | None | `{client_id,status,revoked_at}`. |
| `GET /v1/fpo/me/class-c/integrations/webhooks` | None | Webhook subscription array; signing secrets are not returned. |
| `POST /v1/fpo/me/class-c/integrations/webhooks` | Integration payload (`name`, `endpoint_url`, `event_types`) | `201`; webhook metadata plus one-time `signing_secret` and warning. |
| `POST /v1/fpo/me/class-c/integrations/webhooks/{subscription_id}/disable` | None | `{subscription_id,status,disabled_at}`. |

### C.3 Class C admin/release endpoints

| Method/path | Payload | Response |
|---|---|---|
| `GET /v1/admin/fpo/class-c/quality-schemas` | None | Quality-schema array. Admin only. |
| `POST /v1/admin/fpo/class-c/quality-schemas` | `ClassCQualitySchemaPayload` | `201`; draft quality schema. |
| `POST /v1/admin/fpo/class-c/quality-schemas/{schema_id}/publish` | None | Published quality schema. |
| `GET /v1/admin/fpo/class-c/release-readiness` | None | `{plan,checks,ready}`. Checks include feature configuration, Class B foundation, traceability, inventory, commercial, export, data-sharing, and integration contracts. |
| `POST /v1/admin/fpo/class-c/publish` | `ClassBPayload`; only `reason` is used, with default release message | Published Class C plan/version row. |

## 5. Important implementation notes

1. The gateway exposes the FPO owner prefix as `/api/fpo/...`; it forwards to the FPO
   service's `/v1/fpo/...`. Legacy `/api/fpo-portal/...` remains supported. The current
   proxy does not expose the service's `/v1/admin/...` paths through a dedicated public
   alias; those admin routes need direct service routing or a gateway change.
2. There are no explicit response Pydantic models on these routes. Exact response keys
   therefore follow the selected SQL columns/returned rows in the service functions and
   can include database timestamps/status fields in addition to the semantic fields
   described above.
3. Class B's shared payload means a syntactically valid request can still fail domain
   validation if the operation-specific fields are missing or inconsistent.
4. Class C secret values (`client_secret`, `signing_secret`) are intentionally returned
   only at create/rotate time. Store them immediately; list endpoints return metadata,
   not secrets.
5. Plan/entitlement gates can return domain codes such as
   `FPO_PROVISIONING_PENDING`, `FPO_PROFILE_INCOMPLETE`, `FPO_VERIFICATION_PENDING`,
   `FPO_CHANGES_REQUIRED`, `FPO_REJECTED`, `FPO_SUSPENDED`, or
   `FPO_PLAN_NOT_ASSIGNED`.
