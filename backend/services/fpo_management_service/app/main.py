from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.concurrency import run_in_threadpool
from sqlalchemy import text
from shared.db.postgres import engine

from services.fpo_management_service.app.config import FpoManagementConfig
from services.fpo_management_service.app.storage import DocumentStorageError
from services.fpo_management_service.app.service import (
    bootstrap_status,
    portal_bootstrap,
    review_verification_request,
    submit_verification_request,
    verification_queue,
    admin_overview,
    verification_status,
    verification_documents,
    admin_verification_documents,
    admin_verification_document_content,
    admin_verification_checklist,
    update_admin_verification_checklist,
    document_upload_intent,
    upload_document_content,
    document_upload_finalize,
    document_delete,
    admin_validate_document,
    decide_relationship,
    discover_fpo_directory,
    fpo_relationship_consent_policy,
    farmer_relationships,
    fpo_relationships,
    request_farmer_relationship,
    revoke_relationship,
    cancel_relationship,
    terminate_relationship,
    assign_class,
    feature_catalogue,
    fpo_entitlements,
    create_fpo_feature_override,
    fpo_feature_overrides,
    run_fpo_reconciliation,
    portfolio_report,
    operational_alerts,
    acknowledge_alert,
    dashboard_read_model,
    farmer_directory,
    farmer_detail,
    farmer_farms,
    farm_monitoring,
    farmer_farm_intelligence,
    create_farmer_support_ticket,
    farmer_support_tickets,
    fpo_import_template, fpo_create_import_intent, fpo_upload_import_content,
    fpo_validate_import, fpo_list_imports, fpo_get_import, fpo_import_rows, fpo_staged_import_records, farmer_staged_import_records, farmer_staged_import_record, farmer_link_staged_farm,
    fpo_commit_import, fpo_cancel_import, fpo_quality_summary, fpo_quality_issues,
    fpo_tags, fpo_create_tag, fpo_assign_tag, fpo_segments, fpo_create_segment,
    fpo_evaluate_segment, fpo_segment_members, fpo_notes, fpo_create_note,
    fpo_season_plans, fpo_create_season_plan, fpo_add_crop_target,
    fpo_tasks, fpo_create_task, fpo_update_task,
    fpo_metric_registry, fpo_alert_rules, fpo_create_alert_rule, fpo_publish_alert_rule,
    fpo_monitoring_summary, fpo_advisory_templates, fpo_preview_advisory,
    fpo_campaigns, fpo_create_campaign, fpo_estimate_campaign,
    fpo_schedule_campaign,
    fpo_input_plans, fpo_create_input_plan, fpo_calculate_input_plan, fpo_input_items,
    fpo_forecasts, fpo_run_forecast, fpo_report_catalogue, fpo_report_jobs, fpo_create_report_job,
    fpo_admin_templates, fpo_admin_create_template, fpo_admin_review_template,
    fpo_release_readiness, fpo_publish_class_b_plan,
    fpo_counterparties, fpo_create_counterparty, fpo_update_counterparty_due_diligence,
    fpo_opportunities, fpo_create_opportunity, fpo_transition_opportunity,
    fpo_procurement_plans, fpo_create_procurement_plan, fpo_add_procurement_item,
    fpo_procurement_items, fpo_transition_procurement_plan,
    fpo_lots, fpo_create_lot, fpo_lot_sources, fpo_add_lot_source, fpo_seal_lot,
    fpo_quality_inspections, fpo_create_quality_inspection, fpo_review_quality_inspection,
    fpo_warehouses, fpo_create_warehouse, fpo_inventory_lots,
    fpo_create_inventory_lot, fpo_post_inventory_entry, fpo_reconcile_inventory,
    fpo_admin_quality_schemas, fpo_admin_create_quality_schema, fpo_admin_publish_quality_schema,
    fpo_contracts, fpo_create_contract, fpo_activate_contract, fpo_orders, fpo_create_order, fpo_confirm_order,
    fpo_dispatches, fpo_create_dispatch, fpo_add_dispatch_item, fpo_depart_dispatch,
    fpo_compliance_documents, fpo_create_compliance_document, fpo_compliance_readiness,
    fpo_export_packs, fpo_create_export_pack, fpo_data_pack_schemas, fpo_create_data_pack_request, fpo_validate_data_pack_request, fpo_sustainability_metrics,
    fpo_api_clients, fpo_create_api_client, fpo_rotate_api_client_secret, fpo_revoke_api_client, fpo_webhooks, fpo_create_webhook, fpo_disable_webhook, fpo_class_c_release_readiness, fpo_publish_class_c_plan,
)
from shared.security.local_auth import (
    CurrentUserUnavailableError,
    InvalidAccessTokenError,
    MissingAuthorizationError,
    load_current_user,
)

config = FpoManagementConfig.from_env()
app = FastAPI(title="MaatiTrace FPO Management Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(config.cors_allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(config.trusted_hosts))


def fpo_domain_error(exc: ValueError, fallback: str, *, status_code: int = 403) -> HTTPException:
    code = str(exc) if str(exc).startswith("FPO_") else fallback
    messages = {
        "FPO_PROVISIONING_PENDING": "FPO provisioning is not ready.",
        "FPO_PROFILE_INCOMPLETE": "Complete the FPO profile before using the portal.",
        "FPO_VERIFICATION_PENDING": "FPO verification is still under review.",
        "FPO_CHANGES_REQUIRED": "FPO verification changes are required.",
        "FPO_REJECTED": "FPO verification was rejected.",
        "FPO_SUSPENDED": "FPO access is suspended.",
        "FPO_PLAN_NOT_ASSIGNED": "No published FPO plan is assigned.",
    }
    return HTTPException(status_code=status_code, detail={"code": code, "message": messages.get(code, str(exc))})


def current_user(authorization: str | None = Header(default=None, alias="Authorization")):
    try:
        user = load_current_user(authorization)
    except (CurrentUserUnavailableError, InvalidAccessTokenError, MissingAuthorizationError) as exc:
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED", "message": "Authentication is required."}) from exc
    if user.get("role") not in {"fpo", "farmer", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_OR_FARMER_ROLE_REQUIRED", "message": "This endpoint is not available for the current account role."})
    return user


class RelationshipRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fpo_id: UUID
    farm_id: UUID
    policy_code: str = Field(default="FPO_DATA_SHARING", min_length=2, max_length=80)
    policy_version: str = Field(default="2", min_length=1, max_length=40)
    accepted: bool
    selected_optional_scopes: list[str] = Field(default_factory=list, max_length=20)


class StagedFarmLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    farm_id: UUID


class RelationshipDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: str = Field(pattern="^(ACTIVE|REJECTED)$")
    note: str = Field(default="", max_length=1000)


class RelationshipTermination(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=3, max_length=1000)


class SupportTicketRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    farm_id: UUID | None = None
    fpo_id: UUID | None = None
    category: str = Field(default="ACCESS", pattern="^(ACCESS|CONSENT|DOCUMENTS|FARM_DATA|OTHER)$")
    subject: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=10, max_length=4000)


class ClassAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    class_code: str = Field(pattern="^(A|B|C|a|b|c)$")


class FeatureOverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    feature_key: str = Field(min_length=2, max_length=100)
    enabled: bool
    reason: str = Field(min_length=3, max_length=1000)
    expires_at: datetime | None = None


class VerificationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str = Field(pattern="^(UNDER_REVIEW|APPROVED|CHANGES_REQUIRED|REJECTED)$")
    note: str | None = Field(default=None, max_length=2000)


class DocumentUploadIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_type: str = Field(min_length=2, max_length=80)
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=3, max_length=120)
    size_bytes: int = Field(gt=0, le=20 * 1024 * 1024)
    checksum: str = Field(min_length=32, max_length=128)


class DocumentFinalizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    checksum: str = Field(min_length=32, max_length=128)


class DocumentValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    validation_status: str = Field(pattern="^(VALID|INVALID)$")
    reason: str | None = Field(default=None, max_length=1000)


class VerificationChecklistUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    result: str = Field(pattern="^(PENDING|PASS|FAIL|NOT_APPLICABLE)$")
    note: str | None = Field(default=None, max_length=1000)


class ImportIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    import_type: str = Field(pattern="^(FARMERS|FARMS|FARMERS_AND_FARMS)$")
    source_format: str = Field(pattern="^(CSV|XLSX|csv|xlsx)$")
    filename: str = Field(min_length=1, max_length=255)
    checksum: str = Field(min_length=32, max_length=128)


class ClassBPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, max_length=240)
    description: str | None = Field(default=None, max_length=2000)
    color_token: str | None = Field(default="emerald", max_length=40)
    criteria: dict = Field(default_factory=dict)
    segment_type: str = Field(default="DYNAMIC", pattern="^(DYNAMIC|STATIC)$")
    note_type: str = Field(default="GENERAL", pattern="^(GENERAL|FOLLOW_UP|VISIT|DATA_QUALITY|ADVISORY)$")
    title: str | None = Field(default=None, max_length=240)
    content: str | None = Field(default=None, max_length=10000)
    follow_up_at: datetime | None = None
    season_code: str | None = Field(default=None, max_length=50)
    season_year: int | None = None
    planning_start_date: str | None = None
    season_start_date: str | None = None
    season_end_date: str | None = None
    geography_filter: dict = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=2000)
    crop_code: str | None = Field(default=None, max_length=80)
    variety_code: str | None = Field(default=None, max_length=80)
    target_area_acres: float | None = None
    target_farmer_count: int | None = None
    target_farm_count: int | None = None
    task_type: str = Field(default="FOLLOW_UP", max_length=40)
    priority: str = Field(default="NORMAL", pattern="^(LOW|NORMAL|HIGH|URGENT)$")
    farmer_id: UUID | None = None
    due_at: datetime | None = None
    status: str | None = Field(default=None, max_length=30)
    feature_metric: str | None = None
    scope_type: str | None = None
    scope_configuration: dict = Field(default_factory=dict)
    condition_configuration: dict = Field(default_factory=dict)
    severity: str | None = None
    deduplication_window_minutes: int | None = None
    cooldown_minutes: int | None = None
    template_id: UUID | None = None
    segment_id: UUID | None = None
    channel: str | None = None
    language_strategy: str | None = None
    fixed_language_code: str | None = None
    variables: dict = Field(default_factory=dict)
    season_plan_id: UUID | None = None
    report_type: str | None = None
    format: str | None = None
    idempotency_key: str | None = None
    template_code: str | None = None
    advisory_type: str | None = None
    language_code: str | None = None
    title_template: str | None = None
    body_template: str | None = None
    decision: str | None = None
    reason: str | None = Field(default=None, max_length=1000)


class ClassCCounterpartyPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    counterparty_code: str = Field(min_length=2, max_length=40)
    counterparty_type: str = Field(pattern="^(BUYER|EXPORTER|PROCESSOR|RETAILER|INSTITUTIONAL_BUYER|LOGISTICS_PROVIDER|LABORATORY|WAREHOUSE_OPERATOR|LENDER|INSURER|OTHER)$")
    legal_name: str = Field(min_length=2, max_length=200)
    trade_name: str | None = Field(default=None, max_length=200)
    registration_number: str | None = Field(default=None, max_length=80)
    tax_identifier: str | None = Field(default=None, max_length=120)
    country_code: str = Field(default="IN", min_length=2, max_length=2)
    state_code: str | None = Field(default=None, max_length=20)
    district_code: str | None = Field(default=None, max_length=20)
    address_line_1: str | None = Field(default=None, max_length=200)
    address_line_2: str | None = Field(default=None, max_length=200)
    postal_code: str | None = Field(default=None, max_length=20)
    website_url: str | None = Field(default=None, max_length=500)
    preferred_currency: str = Field(default="INR", min_length=3, max_length=3)
    payment_terms_code: str | None = Field(default=None, max_length=40)
    risk_rating: str | None = Field(default=None, max_length=20)
    notes: str | None = Field(default=None, max_length=4000)
    due_diligence_status: str | None = None
    reason: str | None = Field(default=None, max_length=1000)


class ClassCOpportunityPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    opportunity_code: str = Field(min_length=2, max_length=40)
    counterparty_id: UUID
    title: str = Field(min_length=2, max_length=200)
    commodity_code: str = Field(min_length=2, max_length=50)
    variety_code: str | None = Field(default=None, max_length=50)
    quality_grade_code: str | None = Field(default=None, max_length=50)
    target_quantity: float = Field(gt=0)
    quantity_unit: str = Field(min_length=1, max_length=20)
    target_price: float | None = Field(default=None, ge=0)
    currency_code: str = Field(default="INR", min_length=3, max_length=3)
    delivery_start_date: str | None = None
    delivery_end_date: str | None = None
    delivery_location_text: str | None = Field(default=None, max_length=300)
    source_channel: str = Field(default="DIRECT", max_length=30)
    probability_percent: float | None = Field(default=None, ge=0, le=100)
    owner_notes: str | None = Field(default=None, max_length=4000)
    stage: str | None = None
    reason: str | None = Field(default=None, max_length=1000)


class ClassCProcurementPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_code: str | None = Field(default=None, min_length=2, max_length=40)
    name: str | None = Field(default=None, max_length=180)
    season_code: str | None = Field(default=None, max_length=40)
    season_year: int | None = Field(default=None, ge=2000, le=2200)
    start_date: str | None = None
    end_date: str | None = None
    currency_code: str = Field(default="INR", min_length=3, max_length=3)
    notes: str | None = Field(default=None, max_length=2000)
    commodity_code: str | None = Field(default=None, max_length=50)
    variety_code: str | None = Field(default=None, max_length=50)
    quality_grade_code: str | None = Field(default=None, max_length=50)
    district_code: str | None = Field(default=None, max_length=20)
    block_code: str | None = Field(default=None, max_length=20)
    target_quantity: float | None = Field(default=None, gt=0)
    quantity_unit: str | None = Field(default=None, max_length=20)
    forecast_available_quantity: float | None = Field(default=None, ge=0)
    target_min_price: float | None = Field(default=None, ge=0)
    target_max_price: float | None = Field(default=None, ge=0)
    shortfall_threshold_percent: float | None = Field(default=None, ge=0, le=100)
    status: str | None = None
    reason: str | None = Field(default=None, max_length=1000)


class ClassCLotPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lot_code: str | None = Field(default=None, min_length=2, max_length=60)
    procurement_plan_id: UUID | None = None
    commodity_code: str | None = Field(default=None, max_length=50)
    variety_code: str | None = Field(default=None, max_length=50)
    crop_year: int | None = Field(default=None, ge=2000, le=2200)
    season_code: str | None = Field(default=None, max_length=40)
    quantity_unit: str | None = Field(default=None, max_length=20)
    farmer_id: UUID | None = None
    farm_id: UUID | None = None
    crop_cycle_id: UUID | None = None
    relationship_id: UUID | None = None
    consent_id: UUID | None = None
    source_receipt_code: str | None = Field(default=None, max_length=60)
    gross_quantity: float | None = Field(default=None, gt=0)
    deduction_quantity: float = Field(default=0, ge=0)
    accepted_quantity: float | None = Field(default=None, ge=0)
    rejected_quantity: float = Field(default=0, ge=0)
    declared_harvest_date: str | None = None
    collection_point_code: str | None = Field(default=None, max_length=60)
    source_grade_code: str | None = Field(default=None, max_length=50)
    source_price: float | None = Field(default=None, ge=0)
    currency_code: str | None = Field(default=None, max_length=3)
    source_snapshot: dict = Field(default_factory=dict)


class ClassCQualityPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lot_id: UUID | None = None
    quality_schema_id: UUID | None = None
    measured_values: dict = Field(default_factory=dict)
    disposition: str | None = None
    calculated_grade_code: str | None = Field(default=None, max_length=50)
    reviewer_note: str | None = Field(default=None, max_length=2000)


class ClassCWarehousePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    warehouse_code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=180)
    address_text: str | None = Field(default=None, max_length=500)
    capacity_quantity: float | None = Field(default=None, ge=0)
    quantity_unit: str | None = Field(default=None, max_length=20)


class ClassCInventoryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lot_id: UUID | None = None
    warehouse_id: UUID | None = None
    location_code: str | None = Field(default=None, max_length=60)
    grade_code: str | None = Field(default=None, max_length=50)
    entry_type: str | None = None
    quantity: float | None = Field(default=None, gt=0)
    quantity_unit: str | None = Field(default=None, max_length=20)
    reference_code: str | None = Field(default=None, max_length=80)
    reason: str | None = Field(default=None, max_length=1000)


class ClassCQualitySchemaPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_key: str = Field(min_length=2, max_length=100)
    version: int = Field(default=1, ge=1)
    name: str = Field(min_length=2, max_length=180)
    commodity_code: str = Field(min_length=2, max_length=50)
    jurisdiction_code: str | None = Field(default=None, max_length=30)
    grade_definitions: list[dict] = Field(default_factory=list)
    parameter_definitions: list[dict] = Field(default_factory=list)


class ClassCContractPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contract_code: str = Field(min_length=2, max_length=60)
    counterparty_id: UUID
    opportunity_id: UUID | None = None
    title: str = Field(min_length=2, max_length=200)
    contract_type: str = Field(min_length=2, max_length=30)
    effective_date: str
    expiry_date: str | None = None
    currency_code: str = Field(default="INR", min_length=3, max_length=3)
    value_amount: float | None = Field(default=None, ge=0)
    incoterm_code: str | None = Field(default=None, max_length=20)
    payment_terms_code: str | None = Field(default=None, max_length=40)
    delivery_terms: str | None = Field(default=None, max_length=2000)
    source_document_artifact_id: UUID | None = None
    source_document_checksum: str | None = Field(default=None, max_length=128)


class ClassCOrderPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_code: str = Field(min_length=2, max_length=60)
    counterparty_id: UUID
    contract_id: UUID | None = None
    opportunity_id: UUID | None = None
    buyer_purchase_order_ref: str | None = Field(default=None, max_length=120)
    delivery_start_date: str | None = None
    delivery_end_date: str | None = None
    delivery_address_text: str | None = Field(default=None, max_length=400)
    currency_code: str = Field(default="INR", min_length=3, max_length=3)
    lines: list[dict] = Field(min_length=1, max_length=100)


class ClassCDispatchPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dispatch_code: str = Field(min_length=2, max_length=60)
    order_id: UUID | None = None
    warehouse_id: UUID | None = None
    logistics_counterparty_id: UUID | None = None
    transport_document_ref: str | None = Field(default=None, max_length=120)
    scheduled_departure_at: datetime | None = None
    dispatch_id: UUID | None = None
    order_line_id: UUID | None = None
    inventory_lot_id: UUID | None = None
    quantity: float | None = Field(default=None, gt=0)
    quantity_unit: str | None = Field(default=None, max_length=20)
    package_count: int | None = Field(default=None, ge=1)
    package_type_code: str | None = Field(default=None, max_length=40)
    traceability_code: str | None = Field(default=None, max_length=80)


class ClassCCompliancePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_type_code: str = Field(min_length=2, max_length=60)
    issuing_authority: str | None = Field(default=None, max_length=200)
    issued_date: str | None = None
    expiry_date: str | None = None
    country_code: str = Field(default="IN", min_length=2, max_length=2)
    artifact_id: UUID | None = None
    checksum: str | None = Field(default=None, max_length=128)


class ClassCExportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pack_code: str = Field(min_length=2, max_length=80)
    destination_code: str = Field(min_length=2, max_length=50)
    commodity_code: str = Field(min_length=2, max_length=50)
    order_id: UUID | None = None
    lot_id: UUID | None = None
    template_key: str = Field(min_length=2, max_length=100)


class ClassCDataPackPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_id: UUID
    purpose_code: str = Field(min_length=2, max_length=80)
    recipient_category: str = Field(min_length=2, max_length=40)
    recipient_id: UUID | None = None
    farmer_ids: list[UUID] = Field(default_factory=list, max_length=500)


class ClassCIntegrationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_name: str | None = Field(default=None, min_length=2, max_length=160)
    scopes: list[str] = Field(default_factory=list, max_length=20)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000)
    expires_at: datetime | None = None
    name: str | None = Field(default=None, min_length=2, max_length=160)
    endpoint_url: str | None = Field(default=None, max_length=500)
    event_types: list[str] = Field(default_factory=list, max_length=50)


@app.get("/health/live")
def live():
    return {"service": "fpo_management_service", "status": "live", "environment": config.app_env}


@app.get("/health/ready")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"service": "fpo_management_service", "status": "ready"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"service": "fpo_management_service", "status": "not_ready", "message": str(exc)[:200]}) from exc


@app.get("/v1/fpo-portal/bootstrap-status")
async def read_bootstrap_status(user=Depends(current_user)):
    return await run_in_threadpool(bootstrap_status, user["user_id"])


@app.get("/v1/fpo-portal/bootstrap")
@app.get("/v1/fpo/me/bootstrap")
async def read_portal_bootstrap(user=Depends(current_user)):
    return await run_in_threadpool(portal_bootstrap, user["user_id"])


def _fpo_only(user):
    if user.get("role") != "fpo":
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can use Class B operations."})


def _farmer_only(user):
    if user.get("role") != "farmer":
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmer accounts can use this onboarding view."})


@app.get("/v1/fpo/me/import-templates/{import_type}")
async def get_import_template(import_type: str, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_import_template, user["user_id"], import_type)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_IMPORT_TEMPLATE_INVALID") from exc


@app.post("/v1/fpo/me/imports/upload-intents", status_code=201)
async def create_import_upload_intent(payload: ImportIntentRequest, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_import_intent, user["user_id"], payload.import_type, payload.source_format, payload.filename, payload.checksum)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_IMPORT_INTENT_INVALID", status_code=422) from exc


@app.put("/v1/fpo/me/imports/{job_id}/content")
async def upload_import_file(job_id: UUID, request: Request, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_upload_import_content, user["user_id"], job_id, await request.body())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_IMPORT_UPLOAD_INVALID", status_code=422) from exc
    except DocumentStorageError as exc: raise HTTPException(status_code=503, detail={"code":"FPO_IMPORT_STORAGE_UNAVAILABLE","message":str(exc)}) from exc


@app.post("/v1/fpo/me/imports/{job_id}/validate")
async def validate_import_job(job_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_validate_import, user["user_id"], job_id)
    except (ValueError, DocumentStorageError) as exc: raise fpo_domain_error(exc, "FPO_IMPORT_VALIDATION_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/imports")
async def get_import_jobs(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_list_imports, user["user_id"])


@app.get("/v1/fpo/me/imports/{job_id}")
async def get_import_job(job_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_get_import, user["user_id"], job_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_IMPORT_NOT_FOUND", status_code=404) from exc


@app.get("/v1/fpo/me/imports/{job_id}/rows")
async def get_import_job_rows(job_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_import_rows, user["user_id"], job_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_IMPORT_NOT_FOUND", status_code=404) from exc


@app.get("/v1/fpo/me/imports/{job_id}/staged-records")
async def get_staged_import_records(job_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_staged_import_records, user["user_id"], job_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_IMPORT_NOT_FOUND", status_code=404) from exc


@app.get("/v1/farmer/me/imported-onboarding")
async def get_farmer_imported_onboarding(user=Depends(current_user)):
    _farmer_only(user)
    return await run_in_threadpool(farmer_staged_import_records, user["user_id"])


@app.get("/v1/farmer/me/imported-onboarding/{staged_record_id}")
async def get_farmer_imported_onboarding_record(staged_record_id: UUID, user=Depends(current_user)):
    _farmer_only(user)
    try: return await run_in_threadpool(farmer_staged_import_record, user["user_id"], staged_record_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FARMER_ONBOARDING_NOT_FOUND", status_code=404) from exc


@app.post("/v1/farmer/me/imported-onboarding/{staged_record_id}/link-farm")
async def link_farmer_imported_farm(staged_record_id: UUID, payload: StagedFarmLinkRequest, user=Depends(current_user)):
    _farmer_only(user)
    try: return await run_in_threadpool(farmer_link_staged_farm, user["user_id"], staged_record_id, payload.farm_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FARMER_ONBOARDING_LINK_FAILED", status_code=409) from exc


@app.post("/v1/fpo/me/imports/{job_id}/commit")
async def commit_import_job(job_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_commit_import, user["user_id"], job_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_IMPORT_COMMIT_FAILED", status_code=409) from exc


@app.post("/v1/fpo/me/imports/{job_id}/cancel")
async def cancel_import_job(job_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_cancel_import, user["user_id"], job_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_IMPORT_CANCEL_FAILED", status_code=409) from exc


@app.get("/v1/fpo/me/data-quality/summary")
async def get_quality_summary(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_quality_summary, user["user_id"])


@app.get("/v1/fpo/me/data-quality/issues")
async def get_quality_issues(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_quality_issues, user["user_id"])


@app.get("/v1/fpo/me/tags")
async def get_tags(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_tags, user["user_id"])

@app.post("/v1/fpo/me/tags", status_code=201)
async def post_tag(payload: ClassBPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_tag, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_TAG_CREATE_FAILED", status_code=422) from exc

@app.post("/v1/fpo/me/farmers/{farmer_id}/tags/{tag_id}", status_code=201)
async def post_farmer_tag(farmer_id: UUID, tag_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_assign_tag, user["user_id"], farmer_id, tag_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_TAG_ASSIGN_FAILED") from exc

@app.get("/v1/fpo/me/segments")
async def get_segments(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_segments, user["user_id"])

@app.post("/v1/fpo/me/segments", status_code=201)
async def post_segment(payload: ClassBPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_segment, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_SEGMENT_CREATE_FAILED", status_code=422) from exc

@app.post("/v1/fpo/me/segments/{segment_id}/evaluate")
async def post_segment_evaluation(segment_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_evaluate_segment, user["user_id"], segment_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_SEGMENT_EVALUATION_FAILED") from exc

@app.get("/v1/fpo/me/segments/{segment_id}/farmers")
async def get_segment_members(segment_id: UUID, user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_segment_members, user["user_id"], segment_id)

@app.get("/v1/fpo/me/farmers/{farmer_id}/notes")
async def get_farmer_notes(farmer_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_notes, user["user_id"], farmer_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_NOTES_ACCESS_DENIED") from exc

@app.post("/v1/fpo/me/farmers/{farmer_id}/notes", status_code=201)
async def post_farmer_note(farmer_id: UUID, payload: ClassBPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_note, user["user_id"], farmer_id, payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_NOTE_CREATE_FAILED", status_code=422) from exc

@app.get("/v1/fpo/me/season-plans")
async def get_season_plans(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_season_plans, user["user_id"])

@app.post("/v1/fpo/me/season-plans", status_code=201)
async def post_season_plan(payload: ClassBPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_season_plan, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_SEASON_PLAN_CREATE_FAILED", status_code=422) from exc

@app.post("/v1/fpo/me/season-plans/{plan_id}/crop-targets", status_code=201)
async def post_crop_target(plan_id: UUID, payload: ClassBPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_add_crop_target, user["user_id"], plan_id, payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_CROP_TARGET_CREATE_FAILED", status_code=422) from exc

@app.get("/v1/fpo/me/tasks")
async def get_tasks(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_tasks, user["user_id"])

@app.post("/v1/fpo/me/tasks", status_code=201)
async def post_task(payload: ClassBPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_task, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_TASK_CREATE_FAILED", status_code=422) from exc

@app.patch("/v1/fpo/me/tasks/{task_id}")
async def patch_task(task_id: UUID, payload: ClassBPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_update_task, user["user_id"], task_id, payload.status or "IN_PROGRESS", payload.content)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_TASK_UPDATE_FAILED") from exc


@app.get("/v1/fpo/me/monitoring/summary")
async def get_monitoring_summary(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_monitoring_summary, user["user_id"])

@app.get("/v1/fpo/me/alert-rules")
async def get_alert_rules(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_alert_rules, user["user_id"])

@app.get("/v1/fpo/me/alert-rules/metrics")
async def get_alert_metrics(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_metric_registry, user["user_id"])

@app.post("/v1/fpo/me/alert-rules", status_code=201)
async def post_alert_rule(payload: ClassBPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_alert_rule, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_ALERT_RULE_CREATE_FAILED", status_code=422) from exc

@app.post("/v1/fpo/me/alert-rules/{rule_id}/publish")
async def post_alert_rule_publish(rule_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_publish_alert_rule, user["user_id"], rule_id, "publish")
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_ALERT_RULE_PUBLISH_FAILED") from exc

@app.post("/v1/fpo/me/alert-rules/{rule_id}/pause")
async def post_alert_rule_pause(rule_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_publish_alert_rule, user["user_id"], rule_id, "pause")
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_ALERT_RULE_PAUSE_FAILED") from exc

@app.get("/v1/fpo/me/advisory-templates")
async def get_advisory_templates(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_advisory_templates, user["user_id"])

@app.post("/v1/fpo/me/advisories/preview")
async def post_advisory_preview(payload: ClassBPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_preview_advisory, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_ADVISORY_PREVIEW_FAILED", status_code=422) from exc

@app.get("/v1/fpo/me/campaigns")
async def get_campaigns(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_campaigns, user["user_id"])

@app.post("/v1/fpo/me/campaigns", status_code=201)
async def post_campaign(payload: ClassBPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_campaign, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_CAMPAIGN_CREATE_FAILED", status_code=422) from exc

@app.post("/v1/fpo/me/campaigns/{campaign_id}/estimate")
async def post_campaign_estimate(campaign_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_estimate_campaign, user["user_id"], campaign_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_CAMPAIGN_ESTIMATE_FAILED") from exc

@app.post("/v1/fpo/me/campaigns/{campaign_id}/schedule")
async def post_campaign_schedule(campaign_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_schedule_campaign, user["user_id"], campaign_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_CAMPAIGN_SCHEDULE_FAILED") from exc

@app.get("/v1/fpo/me/input-demand-plans")
async def get_input_plans(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_input_plans, user["user_id"])

@app.post("/v1/fpo/me/input-demand-plans", status_code=201)
async def post_input_plan(payload: ClassBPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_input_plan, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_INPUT_PLAN_CREATE_FAILED", status_code=422) from exc

@app.post("/v1/fpo/me/input-demand-plans/{plan_id}/calculate")
async def calculate_input_plan_endpoint(plan_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_calculate_input_plan, user["user_id"], plan_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_INPUT_PLAN_CALCULATION_FAILED") from exc

@app.get("/v1/fpo/me/input-demand-plans/{plan_id}/items")
async def get_input_plan_items(plan_id: UUID, user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_input_items, user["user_id"], plan_id)

@app.get("/v1/fpo/me/yield-forecasts")
async def get_yield_forecasts(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_forecasts, user["user_id"])

@app.post("/v1/fpo/me/yield-forecasts/run", status_code=201)
async def post_yield_forecast(payload: ClassBPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_run_forecast, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_FORECAST_FAILED", status_code=422) from exc

@app.get("/v1/fpo/me/reports/catalogue")
async def get_report_catalogue(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_report_catalogue, user["user_id"])

@app.get("/v1/fpo/me/report-jobs")
async def get_report_jobs(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_report_jobs, user["user_id"])

@app.post("/v1/fpo/me/report-jobs", status_code=201)
async def post_report_job(payload: ClassBPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_report_job, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_REPORT_JOB_FAILED", status_code=422) from exc

@app.get("/v1/admin/fpo/class-b/advisory-templates")
async def admin_get_advisory_templates(user=Depends(current_user)):
    if user.get("role") != "admin": raise HTTPException(status_code=403, detail={"code":"ADMIN_REQUIRED","message":"Administrator access is required."})
    return await run_in_threadpool(fpo_admin_templates)

@app.post("/v1/admin/fpo/class-b/advisory-templates", status_code=201)
async def admin_post_advisory_template(payload: ClassBPayload, user=Depends(current_user)):
    if user.get("role") != "admin": raise HTTPException(status_code=403, detail={"code":"ADMIN_REQUIRED","message":"Administrator access is required."})
    try: return await run_in_threadpool(fpo_admin_create_template, user["user_id"], payload.model_dump())
    except ValueError as exc: raise HTTPException(status_code=422, detail={"code":"FPO_TEMPLATE_CREATE_FAILED","message":str(exc)}) from exc

@app.patch("/v1/admin/fpo/class-b/advisory-templates/{template_id}")
async def admin_patch_advisory_template(template_id: UUID, payload: ClassBPayload, user=Depends(current_user)):
    if user.get("role") != "admin": raise HTTPException(status_code=403, detail={"code":"ADMIN_REQUIRED","message":"Administrator access is required."})
    try: return await run_in_threadpool(fpo_admin_review_template, user["user_id"], template_id, payload.decision or "REJECT")
    except ValueError as exc: raise HTTPException(status_code=409, detail={"code":"FPO_TEMPLATE_REVIEW_FAILED","message":str(exc)}) from exc

@app.get("/v1/admin/fpo/class-b/release-readiness")
async def admin_release_readiness(user=Depends(current_user)):
    if user.get("role") != "admin": raise HTTPException(status_code=403, detail={"code":"ADMIN_REQUIRED","message":"Administrator access is required."})
    return await run_in_threadpool(fpo_release_readiness, user["user_id"])

@app.post("/v1/admin/fpo/class-b/publish")
async def admin_publish_class_b(payload: ClassBPayload, user=Depends(current_user)):
    if user.get("role") != "admin": raise HTTPException(status_code=403, detail={"code":"ADMIN_REQUIRED","message":"Administrator access is required."})
    try: return await run_in_threadpool(fpo_publish_class_b_plan, user["user_id"], payload.reason or "Class B release approved")
    except ValueError as exc: raise HTTPException(status_code=409, detail={"code":"FPO_CLASS_B_PUBLISH_FAILED","message":str(exc)}) from exc


@app.get("/v1/admin/fpo/class-c/quality-schemas")
async def admin_get_class_c_quality_schemas(user=Depends(current_user)):
    if user.get("role") != "admin": raise HTTPException(status_code=403, detail={"code":"ADMIN_REQUIRED","message":"Administrator access is required."})
    return await run_in_threadpool(fpo_admin_quality_schemas)


@app.post("/v1/admin/fpo/class-c/quality-schemas", status_code=201)
async def admin_post_class_c_quality_schema(payload: ClassCQualitySchemaPayload, user=Depends(current_user)):
    if user.get("role") != "admin": raise HTTPException(status_code=403, detail={"code":"ADMIN_REQUIRED","message":"Administrator access is required."})
    try: return await run_in_threadpool(fpo_admin_create_quality_schema, user["user_id"], payload.model_dump())
    except ValueError as exc: raise HTTPException(status_code=422, detail={"code":"FPO_QUALITY_SCHEMA_CREATE_FAILED","message":str(exc)}) from exc


@app.post("/v1/admin/fpo/class-c/quality-schemas/{schema_id}/publish")
async def admin_publish_class_c_quality_schema(schema_id: UUID, user=Depends(current_user)):
    if user.get("role") != "admin": raise HTTPException(status_code=403, detail={"code":"ADMIN_REQUIRED","message":"Administrator access is required."})
    try: return await run_in_threadpool(fpo_admin_publish_quality_schema, user["user_id"], schema_id)
    except ValueError as exc: raise HTTPException(status_code=409, detail={"code":"FPO_QUALITY_SCHEMA_PUBLISH_FAILED","message":str(exc)}) from exc


@app.get("/v1/fpo/me/class-c/counterparties")
async def get_class_c_counterparties(user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_counterparties, user["user_id"])
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_COUNTERPARTY_ACCESS_DENIED") from exc


@app.post("/v1/fpo/me/class-c/counterparties", status_code=201)
async def post_class_c_counterparty(payload: ClassCCounterpartyPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_counterparty, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_COUNTERPARTY_CREATE_FAILED", status_code=422) from exc


@app.patch("/v1/fpo/me/class-c/counterparties/{counterparty_id}/due-diligence")
async def patch_class_c_counterparty_due_diligence(counterparty_id: UUID, payload: ClassCCounterpartyPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_update_counterparty_due_diligence, user["user_id"], counterparty_id, payload.due_diligence_status or "PENDING", payload.reason)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_COUNTERPARTY_REVIEW_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/opportunities")
async def get_class_c_opportunities(user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_opportunities, user["user_id"])
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_OPPORTUNITY_ACCESS_DENIED") from exc


@app.post("/v1/fpo/me/class-c/opportunities", status_code=201)
async def post_class_c_opportunity(payload: ClassCOpportunityPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_opportunity, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_OPPORTUNITY_CREATE_FAILED", status_code=422) from exc


@app.patch("/v1/fpo/me/class-c/opportunities/{opportunity_id}/stage")
async def patch_class_c_opportunity_stage(opportunity_id: UUID, payload: ClassCOpportunityPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_transition_opportunity, user["user_id"], opportunity_id, payload.stage or "DRAFT", payload.reason)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_OPPORTUNITY_TRANSITION_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/procurement-plans")
async def get_class_c_procurement_plans(user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_procurement_plans, user["user_id"])
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_PROCUREMENT_ACCESS_DENIED") from exc


@app.post("/v1/fpo/me/class-c/procurement-plans", status_code=201)
async def post_class_c_procurement_plan(payload: ClassCProcurementPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_procurement_plan, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_PROCUREMENT_CREATE_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/procurement-plans/{plan_id}/items")
async def get_class_c_procurement_items(plan_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_procurement_items, user["user_id"], plan_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_PROCUREMENT_ACCESS_DENIED") from exc


@app.post("/v1/fpo/me/class-c/procurement-plans/{plan_id}/items", status_code=201)
async def post_class_c_procurement_item(plan_id: UUID, payload: ClassCProcurementPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_add_procurement_item, user["user_id"], plan_id, payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_PROCUREMENT_ITEM_FAILED", status_code=422) from exc


@app.patch("/v1/fpo/me/class-c/procurement-plans/{plan_id}/status")
async def patch_class_c_procurement_status(plan_id: UUID, payload: ClassCProcurementPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_transition_procurement_plan, user["user_id"], plan_id, payload.status or "UNDER_REVIEW", payload.reason)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_PROCUREMENT_TRANSITION_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/lots")
async def get_class_c_lots(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_lots, user["user_id"])


@app.post("/v1/fpo/me/class-c/lots", status_code=201)
async def post_class_c_lot(payload: ClassCLotPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_lot, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_LOT_CREATE_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/lots/{lot_id}/sources")
async def get_class_c_lot_sources(lot_id: UUID, user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_lot_sources, user["user_id"], lot_id)


@app.post("/v1/fpo/me/class-c/lots/{lot_id}/sources", status_code=201)
async def post_class_c_lot_source(lot_id: UUID, payload: ClassCLotPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_add_lot_source, user["user_id"], lot_id, payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_LOT_SOURCE_FAILED", status_code=422) from exc


@app.post("/v1/fpo/me/class-c/lots/{lot_id}/seal")
async def post_class_c_lot_seal(lot_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_seal_lot, user["user_id"], lot_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_LOT_SEAL_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/quality/inspections")
async def get_class_c_quality_inspections(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_quality_inspections, user["user_id"])


@app.post("/v1/fpo/me/class-c/quality/inspections", status_code=201)
async def post_class_c_quality_inspection(payload: ClassCQualityPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_quality_inspection, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_QUALITY_INSPECTION_FAILED", status_code=422) from exc


@app.patch("/v1/fpo/me/class-c/quality/inspections/{inspection_id}/review")
async def patch_class_c_quality_review(inspection_id: UUID, payload: ClassCQualityPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_review_quality_inspection, user["user_id"], inspection_id, payload.disposition or "HOLD", payload.calculated_grade_code, payload.reviewer_note)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_QUALITY_REVIEW_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/warehouses")
async def get_class_c_warehouses(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_warehouses, user["user_id"])


@app.post("/v1/fpo/me/class-c/warehouses", status_code=201)
async def post_class_c_warehouse(payload: ClassCWarehousePayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_warehouse, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_WAREHOUSE_CREATE_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/inventory")
async def get_class_c_inventory(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_inventory_lots, user["user_id"])


@app.post("/v1/fpo/me/class-c/inventory/lots", status_code=201)
async def post_class_c_inventory_lot(payload: ClassCInventoryPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_inventory_lot, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_INVENTORY_LOT_FAILED", status_code=422) from exc


@app.post("/v1/fpo/me/class-c/inventory/lots/{inventory_lot_id}/ledger", status_code=201)
async def post_class_c_inventory_ledger(inventory_lot_id: UUID, payload: ClassCInventoryPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_post_inventory_entry, user["user_id"], inventory_lot_id, payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_INVENTORY_POST_FAILED", status_code=422) from exc


@app.post("/v1/fpo/me/class-c/inventory/reconcile")
async def post_class_c_inventory_reconciliation(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_reconcile_inventory, user["user_id"])


@app.get("/v1/fpo/me/class-c/contracts")
async def get_class_c_contracts(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_contracts, user["user_id"])


@app.post("/v1/fpo/me/class-c/contracts", status_code=201)
async def post_class_c_contract(payload: ClassCContractPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_contract, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_CONTRACT_CREATE_FAILED", status_code=422) from exc


@app.post("/v1/fpo/me/class-c/contracts/{contract_id}/activate")
async def post_class_c_contract_activate(contract_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_activate_contract, user["user_id"], contract_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_CONTRACT_ACTIVATION_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/orders")
async def get_class_c_orders(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_orders, user["user_id"])


@app.post("/v1/fpo/me/class-c/orders", status_code=201)
async def post_class_c_order(payload: ClassCOrderPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_order, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_ORDER_CREATE_FAILED", status_code=422) from exc


@app.post("/v1/fpo/me/class-c/orders/{order_id}/confirm")
async def post_class_c_order_confirm(order_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_confirm_order, user["user_id"], order_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_ORDER_CONFIRM_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/dispatches")
async def get_class_c_dispatches(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_dispatches, user["user_id"])


@app.post("/v1/fpo/me/class-c/dispatches", status_code=201)
async def post_class_c_dispatch(payload: ClassCDispatchPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_dispatch, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_DISPATCH_CREATE_FAILED", status_code=422) from exc


@app.post("/v1/fpo/me/class-c/dispatches/{dispatch_id}/items", status_code=201)
async def post_class_c_dispatch_item(dispatch_id: UUID, payload: ClassCDispatchPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_add_dispatch_item, user["user_id"], dispatch_id, payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_DISPATCH_ITEM_FAILED", status_code=422) from exc


@app.post("/v1/fpo/me/class-c/dispatches/{dispatch_id}/depart")
async def post_class_c_dispatch_depart(dispatch_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_depart_dispatch, user["user_id"], dispatch_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_DISPATCH_DEPARTURE_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/compliance/documents")
async def get_class_c_compliance_documents(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_compliance_documents, user["user_id"])


@app.post("/v1/fpo/me/class-c/compliance/documents", status_code=201)
async def post_class_c_compliance_document(payload: ClassCCompliancePayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_compliance_document, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_COMPLIANCE_DOCUMENT_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/compliance/readiness")
async def get_class_c_compliance_readiness(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_compliance_readiness, user["user_id"])


@app.get("/v1/fpo/me/class-c/export-packs")
async def get_class_c_export_packs(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_export_packs, user["user_id"])


@app.post("/v1/fpo/me/class-c/export-packs", status_code=201)
async def post_class_c_export_pack(payload: ClassCExportPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_export_pack, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_EXPORT_PACK_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/data-packs/schemas")
async def get_class_c_data_pack_schemas(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_data_pack_schemas, user["user_id"])


@app.post("/v1/fpo/me/class-c/data-packs", status_code=201)
async def post_class_c_data_pack(payload: ClassCDataPackPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_data_pack_request, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_DATA_PACK_FAILED", status_code=422) from exc


@app.post("/v1/fpo/me/class-c/data-packs/{request_id}/validate-consent")
async def post_class_c_data_pack_consent_validation(request_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_validate_data_pack_request, user["user_id"], request_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_DATA_PACK_CONSENT_VALIDATION_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/sustainability/metrics")
async def get_class_c_sustainability_metrics(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_sustainability_metrics, user["user_id"])


@app.get("/v1/fpo/me/class-c/integrations/api-clients")
async def get_class_c_api_clients(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_api_clients, user["user_id"])


@app.post("/v1/fpo/me/class-c/integrations/api-clients", status_code=201)
async def post_class_c_api_client(payload: ClassCIntegrationPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_api_client, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_API_CLIENT_CREATE_FAILED", status_code=422) from exc


@app.post("/v1/fpo/me/class-c/integrations/api-clients/{client_id}/rotate-secret")
async def post_class_c_api_client_rotation(client_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_rotate_api_client_secret, user["user_id"], client_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_API_CLIENT_ROTATION_FAILED", status_code=422) from exc


@app.post("/v1/fpo/me/class-c/integrations/api-clients/{client_id}/revoke")
async def post_class_c_api_client_revoke(client_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_revoke_api_client, user["user_id"], client_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_API_CLIENT_REVOKE_FAILED", status_code=422) from exc


@app.get("/v1/fpo/me/class-c/integrations/webhooks")
async def get_class_c_webhooks(user=Depends(current_user)):
    _fpo_only(user); return await run_in_threadpool(fpo_webhooks, user["user_id"])


@app.post("/v1/fpo/me/class-c/integrations/webhooks", status_code=201)
async def post_class_c_webhook(payload: ClassCIntegrationPayload, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_create_webhook, user["user_id"], payload.model_dump())
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_WEBHOOK_CREATE_FAILED", status_code=422) from exc


@app.post("/v1/fpo/me/class-c/integrations/webhooks/{subscription_id}/disable")
async def post_class_c_webhook_disable(subscription_id: UUID, user=Depends(current_user)):
    _fpo_only(user)
    try: return await run_in_threadpool(fpo_disable_webhook, user["user_id"], subscription_id)
    except ValueError as exc: raise fpo_domain_error(exc, "FPO_WEBHOOK_DISABLE_FAILED", status_code=422) from exc


@app.get("/v1/admin/fpo/class-c/release-readiness")
async def admin_class_c_release_readiness(user=Depends(current_user)):
    if user.get("role") != "admin": raise HTTPException(status_code=403, detail={"code":"ADMIN_REQUIRED","message":"Administrator access is required."})
    try: return await run_in_threadpool(fpo_class_c_release_readiness, user["user_id"])
    except ValueError as exc: raise HTTPException(status_code=409, detail={"code":"FPO_CLASS_C_READINESS_FAILED","message":str(exc)}) from exc


@app.post("/v1/admin/fpo/class-c/publish")
async def admin_publish_class_c(payload: ClassBPayload, user=Depends(current_user)):
    if user.get("role") != "admin": raise HTTPException(status_code=403, detail={"code":"ADMIN_REQUIRED","message":"Administrator access is required."})
    try: return await run_in_threadpool(fpo_publish_class_c_plan, user["user_id"], payload.reason or "Class C release approved")
    except ValueError as exc: raise HTTPException(status_code=409, detail={"code":"FPO_CLASS_C_PUBLISH_FAILED","message":str(exc)}) from exc


@app.get("/v1/fpo-portal/verification")
async def read_verification(user=Depends(current_user)):
    return await run_in_threadpool(verification_status, user["user_id"])


@app.get("/v1/fpo/me/documents")
async def read_verification_documents(user=Depends(current_user)):
    if user.get("role") != "fpo":
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read verification documents."})
    return await run_in_threadpool(verification_documents, user["user_id"])


@app.post("/v1/fpo/me/documents/upload-intents", status_code=201)
async def create_verification_document_intent(payload: DocumentUploadIntentRequest, user=Depends(current_user)):
    if user.get("role") != "fpo":
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can upload verification documents."})
    try:
        return await run_in_threadpool(document_upload_intent, user["user_id"], payload.document_type, payload.filename, payload.mime_type, payload.size_bytes, payload.checksum)
    except DocumentStorageError as exc:
        raise HTTPException(status_code=503, detail={"code": "FPO_DOCUMENT_STORAGE_UNAVAILABLE", "message": str(exc)}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "FPO_DOCUMENT_INTENT_INVALID", "message": str(exc)}) from exc


@app.post("/v1/fpo/me/documents/{document_id}/finalize")
async def finalize_verification_document(document_id: UUID, payload: DocumentFinalizeRequest, user=Depends(current_user)):
    if user.get("role") != "fpo":
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can finalize verification documents."})
    try:
        return await run_in_threadpool(document_upload_finalize, user["user_id"], document_id, payload.checksum)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_DOCUMENT_FINALIZE_FAILED", "message": str(exc)}) from exc


@app.delete("/v1/fpo/me/documents/{document_id}")
async def delete_verification_document_endpoint(document_id: UUID, user=Depends(current_user)):
    if user.get("role") != "fpo":
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can remove verification documents."})
    try:
        return await run_in_threadpool(document_delete, user["user_id"], document_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_DOCUMENT_DELETE_FAILED", "message": str(exc)}) from exc


@app.put("/v1/fpo/me/documents/{document_id}/content")
async def upload_verification_document_content(document_id: UUID, request: Request, user=Depends(current_user)):
    if user.get("role") != "fpo":
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can upload verification documents."})
    try:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 20 * 1024 * 1024:
            raise ValueError("Document must not exceed 20 MB")
        data = await request.body()
        return await run_in_threadpool(upload_document_content, user["user_id"], document_id, request.headers.get("content-type", ""), data)
    except DocumentStorageError as exc:
        raise HTTPException(status_code=503, detail={"code": "FPO_DOCUMENT_STORAGE_UNAVAILABLE", "message": str(exc)}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "FPO_DOCUMENT_UPLOAD_INVALID", "message": str(exc)}) from exc


@app.post("/v1/fpo-portal/verification/submit", status_code=201)
async def submit_verification(user=Depends(current_user)):
    try:
        return await run_in_threadpool(submit_verification_request, user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_VERIFICATION_NOT_READY", "message": str(exc)}) from exc


@app.patch("/v1/fpo-portal/admin/organizations/{fpo_id}/verification")
async def decide_verification(fpo_id: str, payload: VerificationDecision, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    try:
        return await run_in_threadpool(
            review_verification_request,
            fpo_id,
            user["user_id"],
            payload.status,
            payload.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_VERIFICATION_REVIEW_FAILED", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/admin/organizations/{fpo_id}/verification/documents")
async def read_admin_verification_documents(fpo_id: UUID, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    return await run_in_threadpool(admin_verification_documents, fpo_id)


@app.get("/v1/fpo-portal/admin/verification/documents/{document_id}/content")
async def read_admin_verification_document_content(document_id: UUID, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    try:
        target, content = await run_in_threadpool(admin_verification_document_content, document_id)
        return Response(content=content, media_type=target["mime_type"], headers={"Content-Disposition": f'inline; filename="{target["original_filename"]}"'})
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"code": "FPO_DOCUMENT_NOT_FOUND", "message": str(exc)}) from exc
    except DocumentStorageError as exc:
        raise HTTPException(status_code=503, detail={"code": "FPO_DOCUMENT_STORAGE_UNAVAILABLE", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/admin/organizations/{fpo_id}/verification/checklist")
async def read_admin_verification_checklist(fpo_id: UUID, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    return await run_in_threadpool(admin_verification_checklist, fpo_id)


@app.patch("/v1/fpo-portal/admin/verification/checklist/{result_id}")
async def update_admin_checklist(result_id: UUID, payload: VerificationChecklistUpdate, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    try:
        return await run_in_threadpool(update_admin_verification_checklist, user["user_id"], result_id, payload.result, payload.note)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_CHECKLIST_UPDATE_FAILED", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/admin/verification-queue")
@app.get("/v1/admin/fpo-verification-cases")
async def read_verification_queue(status: str | None = None, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    return await run_in_threadpool(verification_queue, status)


@app.get("/v1/admin/fpo/overview")
async def read_admin_fpo_overview(user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    return await run_in_threadpool(admin_overview)


@app.patch("/v1/fpo-portal/admin/verification/documents/{document_id}")
@app.patch("/v1/admin/fpo-verification-documents/{document_id}")
async def update_verification_document(document_id: UUID, payload: DocumentValidationRequest, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    try:
        return await run_in_threadpool(admin_validate_document, user["user_id"], document_id, payload.validation_status, payload.reason)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_DOCUMENT_VALIDATION_FAILED", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/discover")
async def discover_fpo(query: str | None = None, limit: int = Query(default=25, ge=1, le=100), user=Depends(current_user)):
    if user.get("role") not in {"farmer", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmers can discover an FPO."})
    return await run_in_threadpool(discover_fpo_directory, query, limit)


@app.get("/v1/farmer/fpo-consent-policy")
async def read_fpo_consent_policy(request: Request, user=Depends(current_user)):
    if user.get("role") != "farmer":
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmers can read the FPO sharing policy."})
    try:
        language = request.headers.get("accept-language", "en").split(",")[0]
        return await run_in_threadpool(fpo_relationship_consent_policy, language)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail={"code": "FPO_CONSENT_POLICY_UNAVAILABLE", "message": str(exc)}) from exc


@app.get("/v1/farmer/fpo-relationships")
async def read_farmer_relationships(user=Depends(current_user)):
    if user.get("role") not in {"farmer", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmers can read their FPO relationships."})
    return await run_in_threadpool(farmer_relationships, user["user_id"])


@app.get("/v1/farmer/farms/{farm_id}/fpo-relationships")
async def read_farmer_farm_relationships(farm_id: UUID, user=Depends(current_user)):
    if user.get("role") not in {"farmer", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmers can read farm FPO relationships."})
    return await run_in_threadpool(farmer_relationships, user["user_id"], farm_id)


@app.post("/v1/farmer/fpo-relationships", status_code=201)
@app.post("/v1/farmer/farm-relationships", status_code=201)
async def create_farmer_relationship(payload: RelationshipRequest, request: Request, user=Depends(current_user)):
    if user.get("role") != "farmer":
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmer accounts can request an FPO relationship."})
    try:
        return await run_in_threadpool(
            request_farmer_relationship,
            user["user_id"],
            payload.fpo_id, payload.farm_id,
            payload.policy_code, payload.policy_version, payload.accepted,
            payload.selected_optional_scopes, request.headers.get("accept-language", "en").split(",")[0],
            request.headers.get("x-correlation-id"), request.client.host if request.client else None,
        )
    except ValueError as exc:
        message = str(exc)
        if "consent policy" in message.lower() or "published" in message.lower():
            code = "FPO_CONSENT_POLICY_STALE"
        elif "already connected to this fpo" in message.lower():
            code = "FPO_ALREADY_CONNECTED"
        elif "not available for farmer association" in message.lower():
            code = "FPO_NOT_AVAILABLE"
        elif "unsupported scope" in message.lower():
            code = "FPO_CONSENT_SCOPE_INVALID"
        else:
            code = "FPO_RELATIONSHIP_REQUEST_FAILED"
        raise HTTPException(status_code=409, detail={"code": code, "message": message}) from exc


@app.get("/v1/fpo-portal/relationships")
@app.get("/v1/fpo-portal/farm-relationships")
async def read_fpo_relationships(user=Depends(current_user)):
    if user.get("role") not in {"fpo", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read relationship requests."})
    try:
        return await run_in_threadpool(fpo_relationships, user["user_id"])
    except ValueError as exc:
        raise fpo_domain_error(exc, "FPO_FEATURE_DISABLED") from exc


@app.patch("/v1/fpo-portal/relationships/{relationship_id}")
@app.patch("/v1/fpo-portal/farm-relationships/{relationship_id}")
async def update_fpo_relationship(relationship_id: UUID, payload: RelationshipDecision, user=Depends(current_user)):
    if user.get("role") != "fpo":
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can decide relationship requests."})
    try:
        return await run_in_threadpool(decide_relationship, user["user_id"], relationship_id, payload.decision, payload.note)
    except ValueError as exc:
        code = "FPO_FEATURE_DISABLED" if "Feature" in str(exc) else "FPO_RELATIONSHIP_DECISION_FAILED"
        if str(exc).startswith("FPO_"):
            raise fpo_domain_error(exc, code) from exc
        raise HTTPException(status_code=403 if code == "FPO_FEATURE_DISABLED" else 409, detail={"code": code, "message": str(exc)}) from exc


@app.delete("/v1/farmer/fpo-relationships/{relationship_id}")
async def revoke_fpo_relationship(relationship_id: UUID, user=Depends(current_user)):
    if user.get("role") != "farmer":
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmers can revoke their relationship."})
    try:
        return await run_in_threadpool(revoke_relationship, user["user_id"], relationship_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_RELATIONSHIP_REVOKE_FAILED", "message": str(exc)}) from exc


@app.delete("/v1/farmer/farms/{farm_id}/fpo-relationships/{relationship_id}")
async def revoke_farm_fpo_relationship(farm_id: UUID, relationship_id: UUID, user=Depends(current_user)):
    if user.get("role") != "farmer":
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmers can revoke farm access."})
    try:
        return await run_in_threadpool(revoke_relationship, user["user_id"], relationship_id, farm_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_FARM_RELATIONSHIP_REVOKE_FAILED", "message": str(exc)}) from exc


@app.get("/v1/farmer/fpo-support-tickets")
async def read_farmer_support_tickets(user=Depends(current_user)):
    if user.get("role") != "farmer":
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmers can read their support tickets."})
    return await run_in_threadpool(farmer_support_tickets, user["user_id"])


@app.post("/v1/farmer/fpo-support-tickets", status_code=201)
async def create_farmer_support_ticket_route(payload: SupportTicketRequest, user=Depends(current_user)):
    if user.get("role") != "farmer":
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmers can create support tickets."})
    try:
        return await run_in_threadpool(create_farmer_support_ticket, user["user_id"], payload.farm_id, payload.fpo_id, payload.category, payload.subject, payload.description)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_SUPPORT_TICKET_FAILED", "message": str(exc)}) from exc


@app.post("/v1/farmers/me/fpo-relationship-requests/{relationship_id}/cancel")
async def cancel_farmer_fpo_relationship_request(relationship_id: UUID, user=Depends(current_user)):
    if user.get("role") != "farmer":
        raise HTTPException(status_code=403, detail={"code": "FARMER_ROLE_REQUIRED", "message": "Only farmer accounts can cancel a relationship request."})
    try:
        return await run_in_threadpool(cancel_relationship, user["user_id"], relationship_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_RELATIONSHIP_CANCEL_FAILED", "message": str(exc)}) from exc


@app.post("/v1/fpo-portal/relationships/{relationship_id}/terminate")
@app.post("/v1/fpo/me/relationships/{relationship_id}/terminate")
async def terminate_fpo_relationship(relationship_id: UUID, payload: RelationshipTermination, user=Depends(current_user)):
    if user.get("role") != "fpo":
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can terminate relationships."})
    try:
        return await run_in_threadpool(terminate_relationship, user["user_id"], relationship_id, payload.reason)
    except ValueError as exc:
        if str(exc).startswith("FPO_"):
            raise fpo_domain_error(exc, "FPO_RELATIONSHIP_TERMINATION_FAILED") from exc
        raise HTTPException(status_code=409, detail={"code": "FPO_RELATIONSHIP_TERMINATION_FAILED", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/entitlements")
@app.get("/v1/fpo/me/entitlements")
async def read_fpo_entitlements(user=Depends(current_user)):
    if user.get("role") not in {"fpo", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read entitlements."})
    return await run_in_threadpool(fpo_entitlements, user["user_id"])


@app.get("/v1/fpo-portal/reports/portfolio")
async def read_portfolio_report(user=Depends(current_user)):
    if user.get("role") not in {"fpo", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read portfolio reports."})
    try:
        return await run_in_threadpool(portfolio_report, user["user_id"])
    except ValueError as exc:
        raise fpo_domain_error(exc, "FPO_FEATURE_DISABLED") from exc


@app.get("/v1/fpo-portal/dashboard")
@app.get("/v1/fpo/me/dashboard")
async def read_dashboard(user=Depends(current_user)):
    if user.get("role") not in {"fpo", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read the dashboard."})
    try:
        return await run_in_threadpool(dashboard_read_model, user["user_id"])
    except ValueError as exc:
        raise fpo_domain_error(exc, "FPO_FEATURE_DISABLED") from exc


@app.get("/v1/fpo-portal/farmers")
@app.get("/v1/fpo/me/farmers")
async def read_farmer_directory(
    query: str | None = None,
    district_code: int | None = None,
    block_code: int | None = None,
    relationship_status: str | None = None,
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    user=Depends(current_user),
):
    if user.get("role") not in {"fpo", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read the farmer directory."})
    try:
        return await run_in_threadpool(farmer_directory, user["user_id"], query, district_code, block_code, relationship_status, cursor, limit)
    except ValueError as exc:
        raise fpo_domain_error(exc, "FPO_FEATURE_DISABLED") from exc


@app.get("/v1/fpo/me/farmers/{farmer_id}")
async def read_fpo_farmer_detail(farmer_id: UUID, user=Depends(current_user)):
    if user.get("role") != "fpo":
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read farmer details."})
    try:
        return await run_in_threadpool(farmer_detail, user["user_id"], farmer_id)
    except ValueError as exc:
        raise fpo_domain_error(exc, "FPO_FARMER_ACCESS_DENIED") from exc


@app.get("/v1/fpo/me/farmers/{farmer_id}/farms")
async def read_fpo_farmer_farms(farmer_id: UUID, user=Depends(current_user)):
    if user.get("role") != "fpo":
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read farmer farms."})
    try:
        return await run_in_threadpool(farmer_farms, user["user_id"], farmer_id)
    except ValueError as exc:
        raise fpo_domain_error(exc, "FPO_FARM_ACCESS_DENIED") from exc


@app.get("/v1/fpo-portal/farms/monitoring")
@app.get("/v1/fpo/me/farms/monitoring")
async def read_fpo_farm_monitoring(query: str | None = None, user=Depends(current_user)):
    if user.get("role") not in {"fpo", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read farm monitoring."})
    try:
        return {"items": await run_in_threadpool(farm_monitoring, user["user_id"], query)}
    except ValueError as exc:
        raise fpo_domain_error(exc, "FPO_FARM_ACCESS_DENIED") from exc


@app.get("/v1/fpo/me/farmers/{farmer_id}/farms/{farm_id}/intelligence")
async def read_fpo_farm_intelligence(farmer_id: UUID, farm_id: UUID, user=Depends(current_user)):
    if user.get("role") != "fpo":
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read farm intelligence."})
    try:
        return await run_in_threadpool(farmer_farm_intelligence, user["user_id"], farmer_id, farm_id)
    except ValueError as exc:
        if str(exc).startswith("FPO_"):
            raise fpo_domain_error(exc, "FPO_FARM_SCOPE_FORBIDDEN") from exc
        raise HTTPException(status_code=403, detail={"code": "FPO_FARM_SCOPE_FORBIDDEN", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/alerts")
async def read_operational_alerts(status: str | None = Query(default=None), user=Depends(current_user)):
    if user.get("role") not in {"fpo", "admin"}:
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can read alerts."})
    try:
        return await run_in_threadpool(operational_alerts, user["user_id"], status)
    except ValueError as exc:
        raise fpo_domain_error(exc, "FPO_FEATURE_DISABLED") from exc


@app.patch("/v1/fpo-portal/alerts/{alert_id}/acknowledge")
async def mark_alert_acknowledged(alert_id: UUID, user=Depends(current_user)):
    if user.get("role") != "fpo":
        raise HTTPException(status_code=403, detail={"code": "FPO_ROLE_REQUIRED", "message": "Only FPO accounts can acknowledge alerts."})
    try:
        return await run_in_threadpool(acknowledge_alert, user["user_id"], alert_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_ALERT_ACKNOWLEDGE_FAILED", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/admin/features/catalogue")
@app.get("/v1/admin/fpo/features")
async def read_feature_catalogue(user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    return await run_in_threadpool(feature_catalogue)


@app.patch("/v1/fpo-portal/admin/organizations/{fpo_id}/class")
async def update_fpo_class(fpo_id: UUID, payload: ClassAssignment, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    try:
        return await run_in_threadpool(assign_class, fpo_id, payload.class_code, user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_CLASS_ASSIGNMENT_FAILED", "message": str(exc)}) from exc


@app.post("/v1/fpo-portal/admin/organizations/{fpo_id}/feature-overrides", status_code=201)
async def create_override(fpo_id: UUID, payload: FeatureOverrideRequest, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    try:
        return await run_in_threadpool(
            create_fpo_feature_override,
            fpo_id,
            payload.feature_key,
            payload.enabled,
            payload.reason,
            payload.expires_at,
            user["user_id"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "FPO_FEATURE_OVERRIDE_FAILED", "message": str(exc)}) from exc


@app.get("/v1/fpo-portal/admin/organizations/{fpo_id}/feature-overrides")
async def read_overrides(fpo_id: UUID, user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    return await run_in_threadpool(fpo_feature_overrides, fpo_id)


@app.post("/v1/fpo-portal/admin/reconciliation/run")
async def run_reconciliation(user=Depends(current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    return await run_in_threadpool(run_fpo_reconciliation, user["user_id"])
