from __future__ import annotations

import logging
import hashlib
import os
import re
import httpx
from uuid import UUID
from sqlalchemy import text

from shared.db.postgres import engine
from services.fpo_management_service.app.config import FpoManagementConfig
from services.fpo_management_service.app.storage import create_upload_url, DocumentStorageError, delete_bytes, download_bytes, scan_with_clamav, store_bytes
from services.fpo_management_service.app.repository import (
    claim_provisioning_events,
    record_event_inbox,
    mark_event_inbox_processed,
    mark_event_inbox_failed,
    set_provisioning_error,
    list_provisioning_cases,
    get_provisioning_case,
    retry_provisioning_event,
    retry_fpo_provisioning,
    fpo_provisioning_metrics,
    get_bootstrap_status,
    get_portal_bootstrap,
    provision_fpo,
    complete_fpo_provisioning,
    get_verification_for_user,
    create_document_upload_intent,
    create_document_replacement_intent,
    get_document_upload_target,
    finalize_document_upload,
    list_verification_documents,
    delete_verification_document,
    list_admin_verification_documents,
    get_admin_verification_document_target,
    list_verification_checklist,
    update_verification_checklist,
    validate_verification_document,
    claim_document_scan_batch,
    mark_document_scan_result,
    list_verification_queue,
    get_admin_overview,
    review_verification,
    submit_verification,
    create_farmer_relationship_request,
    decide_farmer_relationship,
    refresh_portfolio_read_models,
    discover_fpos,
    list_farmer_relationships,
    list_fpo_relationships,
    revoke_farmer_relationship,
    cancel_farmer_relationship_request,
    terminate_farmer_relationship,
    assign_fpo_class,
    list_feature_catalogue,
    resolve_fpo_entitlements,
    require_fpo_feature,
    create_feature_override,
    list_feature_overrides,
    reconcile_fpo_data,
    fpo_portfolio_report,
    list_fpo_alerts,
    acknowledge_fpo_alert,
    get_fpo_dashboard_read_model,
    list_fpo_farmer_portfolio,
    get_fpo_access_context,
    get_fpo_farmer_detail,
    list_fpo_farmer_farms,
    list_fpo_farm_monitoring,
    authorize_fpo_farm_intelligence,
    create_support_ticket,
    list_support_tickets,
    claim_verification_case,
    assign_verification_case,
    release_verification_case,
    escalate_verification_case,
    decide_verification_case,
)
from services.fpo_management_service.app.class_b import (
    import_template, create_import_intent, upload_import_content, validate_import,
    list_imports, get_import, import_rows, staged_import_records, farmer_staged_records, farmer_staged_record, link_staged_farm, reconcile_farmer_account, commit_import, cancel_import, process_import_jobs,
    quality_summary, quality_issues,
)
from services.fpo_management_service.app.class_b_portfolio import (
    list_tags, create_tag, assign_tag, create_segment, evaluate_segment, list_segments,
    segment_members, notes, create_note, season_plans, create_season_plan,
    add_crop_target, tasks, create_task, update_task,
)
from services.fpo_management_service.app.class_b_monitoring_advisory import (
    metric_registry, alert_rules, create_alert_rule, publish_alert_rule, monitoring_summary,
    advisory_templates, preview_advisory, campaigns, create_campaign, estimate_campaign, schedule_campaign,
)
from services.fpo_management_service.app.class_b_inputs_reports import (
    input_plans, create_input_plan, calculate_input_plan, input_items, forecasts, run_forecast,
    report_catalogue, report_jobs, create_report_job,
)
from services.fpo_management_service.app.class_b_admin import (
    admin_templates, admin_create_template, admin_review_template, release_readiness,
    publish_class_b_plan, process_report_jobs,
)
from services.fpo_management_service.app.class_c import (
    counterparties, create_counterparty, update_counterparty_due_diligence,
    opportunities, create_opportunity, transition_opportunity,
    procurement_plans, create_procurement_plan, add_procurement_item,
    procurement_items, transition_procurement_plan,
    lots, create_lot, lot_sources, add_lot_source, seal_lot,
    quality_inspections, create_quality_inspection, review_quality_inspection,
    warehouses, create_warehouse, inventory_lots,
    create_inventory_lot, post_inventory_entry, reconcile_inventory,
    admin_quality_schemas, admin_create_quality_schema, admin_publish_quality_schema,
    contracts, create_contract, activate_contract, orders, create_order, confirm_order,
    dispatches, create_dispatch, add_dispatch_item, depart_dispatch,
    compliance_documents, create_compliance_document, compliance_readiness,
    export_packs, create_export_pack, data_pack_schemas, create_data_pack_request, validate_data_pack_request, sustainability_metrics,
)
from services.fpo_management_service.app.class_c_enterprise import (
    api_clients, create_api_client, rotate_api_client_secret, revoke_api_client,
    webhooks, create_webhook, disable_webhook, class_c_release_readiness, publish_class_c_plan,
)

logger = logging.getLogger("fpo_management_service")


def _create_profile_for_provisioning(
    payload: dict,
    correlation_id: str,
    existing_profile_fpo_id: str | None,
) -> str:
    config = FpoManagementConfig.from_env()
    if len(config.profile_internal_service_token.encode("utf-8")) < 32:
        raise ValueError("PROFILE_SERVICE_AUTH_NOT_CONFIGURED")
    request_payload = {
        "user_id": payload["user_id"],
        "correlation_id": correlation_id,
        "existing_profile_fpo_id": existing_profile_fpo_id,
        "authorised_fpo_representative": payload["authorised_fpo_representative"],
        "full_name": payload["full_name"],
        "email": payload["email"],
        "phone_number": payload["phone_number"],
        "signup_profile": payload["signup_profile"],
    }
    try:
        response = httpx.post(
            f"{config.profile_service_url}/internal/v1/fpos/provision",
            json=request_payload,
            headers={
                "X-Internal-Service-Token": config.profile_internal_service_token,
                "X-Correlation-ID": correlation_id,
            },
            timeout=10,
        )
    except httpx.HTTPError as exc:
        raise RuntimeError("PROFILE_SERVICE_UNAVAILABLE") from exc
    if response.status_code == 409:
        raise ValueError("FPO_REGISTRATION_CONFLICT")
    if response.status_code == 422:
        raise ValueError("FPO_PROFILE_PROVISIONING_INVALID")
    if response.status_code != 200:
        raise RuntimeError("PROFILE_SERVICE_PROVISIONING_FAILED")
    try:
        profile_id = str(response.json()["profile_fpo_id"])
        UUID(profile_id)
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError("PROFILE_SERVICE_RESPONSE_INVALID") from exc
    return profile_id


def process_batch(batch_size: int) -> int:
    processed = 0
    with engine.begin() as conn:
        events = claim_provisioning_events(conn, batch_size=batch_size)
    for event in events:
        try:
            payload = dict(event["payload"])
            with engine.begin() as conn:
                organization = provision_fpo(
                    conn,
                    {
                        **payload,
                        "_occurred_at": event["occurred_at"].isoformat(),
                        "_correlation_id": str(event["correlation_id"]),
                    },
                )
            profile_id = _create_profile_for_provisioning(
                payload,
                str(event["correlation_id"]),
                str(organization["profile_fpo_id"]) if organization.get("profile_fpo_id") else None,
            )
            with engine.begin() as conn:
                complete_fpo_provisioning(
                    conn,
                    user_id=payload["user_id"],
                    profile_fpo_id=profile_id,
                    correlation_id=event["correlation_id"],
                )
                mark_event_inbox_processed(conn, event["event_id"])
                processed += 1
        except Exception as exc:
            error_code = str(exc) if isinstance(exc, ValueError) else "FPO_PROVISIONING_TEMPORARY_FAILURE"
            logger.exception(
                "fpo_provisioning_failed",
                extra={
                    "event_id": str(event["event_id"]),
                    "correlation_id": str(event.get("correlation_id") or ""),
                    "error_code": error_code,
                },
            )
            with engine.begin() as conn:
                mark_event_inbox_failed(conn, event["event_id"], error_code)
                set_provisioning_error(
                    conn,
                    user_id=event["subject_id"],
                    error_code=error_code,
                    error="We could not finish setting up your organization. Support can retry safely.",
                    correlation_id=event.get("correlation_id"),
                )
    return processed


def process_document_scan_batch(batch_size: int) -> int:
    with engine.begin() as conn:
        documents = claim_document_scan_batch(conn, batch_size=batch_size)
    processed = 0
    for document in documents:
        try:
            data = download_bytes(object_key=document["object_key"])
            if len(data) != int(document["size_bytes"]):
                raise DocumentStorageError("Stored document size does not match upload metadata")
            verified_checksum = hashlib.sha256(data).hexdigest()
            if verified_checksum != str(document["checksum"]).lower():
                with engine.begin() as conn:
                    mark_document_scan_result(conn, document_id=document["document_id"], scan_status="QUARANTINED", error="Stored document checksum mismatch", verified_checksum=verified_checksum)
                processed += 1
                continue
            mime = str(document["mime_type"]).lower()
            magic_matches = {
                "application/pdf": data.startswith(b"%PDF-"),
                "image/jpeg": data.startswith(b"\xff\xd8\xff"),
                "image/png": data.startswith(b"\x89PNG\r\n\x1a\n"),
            }
            if not magic_matches.get(mime, False):
                with engine.begin() as conn:
                    mark_document_scan_result(conn, document_id=document["document_id"], scan_status="QUARANTINED", error="Declared MIME type does not match stored file signature", verified_checksum=verified_checksum)
                processed += 1
                continue
            status, error = scan_with_clamav(data)
            with engine.begin() as conn:
                mark_document_scan_result(conn, document_id=document["document_id"], scan_status=status, error=error, verified_checksum=verified_checksum)
            processed += 1
        except Exception as exc:
            logger.exception("fpo_document_scan_failed", extra={"document_id": str(document["document_id"])})
            with engine.begin() as conn:
                mark_document_scan_result(conn, document_id=document["document_id"], scan_status="FAILED", error=str(exc))
    return processed


def process_storage_deletion_batch(batch_size: int) -> int:
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT deletion_id, document_id, object_key
            FROM public.fpo_verification_storage_deletions
            WHERE status IN ('PENDING','RETRY') AND next_attempt_at <= now()
            ORDER BY created_at
            FOR UPDATE SKIP LOCKED LIMIT :limit
        """), {"limit": max(1, min(batch_size, 100))}).mappings().all()
        for row in rows:
            conn.execute(text("UPDATE public.fpo_verification_storage_deletions SET status='PROCESSING', attempts=attempts+1, updated_at=now() WHERE deletion_id=:id"), {"id": str(row["deletion_id"])})
    processed = 0
    for row in rows:
        try:
            delete_bytes(object_key=row["object_key"])
            with engine.begin() as conn:
                conn.execute(text("UPDATE public.fpo_verification_storage_deletions SET status='DELETED', deleted_at=now(), updated_at=now() WHERE deletion_id=:id"), {"id": str(row["deletion_id"])})
            processed += 1
        except DocumentStorageError as exc:
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE public.fpo_verification_storage_deletions
                    SET status = CASE WHEN attempts >= 5 THEN 'DEAD' ELSE 'RETRY' END,
                        next_attempt_at = now() + make_interval(secs => CASE WHEN attempts = 1 THEN 30 WHEN attempts = 2 THEN 120 WHEN attempts = 3 THEN 600 ELSE 1800 END),
                        last_error = :error, updated_at = now()
                    WHERE deletion_id = :id
                """), {"id": str(row["deletion_id"]), "error": str(exc)[:1000]})
    return processed


def bootstrap_status(user_id):
    with engine.connect() as conn:
        return get_bootstrap_status(conn, user_id)


def ingest_auth_user_created_event(event: dict) -> str:
    with engine.begin() as conn:
        return record_event_inbox(conn, event)


def admin_provisioning_cases(*, limit: int, offset: int, status: str | None = None):
    with engine.connect() as conn:
        return list_provisioning_cases(conn, limit=limit, offset=offset, status=status)


def admin_provisioning_case(fpo_id):
    with engine.connect() as conn:
        return get_provisioning_case(conn, fpo_id)


def admin_retry_provisioning(*, event_id, actor_user_id, reason):
    with engine.begin() as conn:
        return retry_provisioning_event(
            conn,
            event_id=event_id,
            actor_user_id=actor_user_id,
            reason=reason,
        )


def admin_retry_fpo_provisioning(*, fpo_id, actor_user_id, reason):
    with engine.begin() as conn:
        return retry_fpo_provisioning(
            conn,
            fpo_id=fpo_id,
            actor_user_id=actor_user_id,
            reason=reason,
        )


def provisioning_metrics():
    with engine.connect() as conn:
        return fpo_provisioning_metrics(conn)


def portal_bootstrap(user_id):
    with engine.connect() as conn:
        return get_portal_bootstrap(conn, user_id)


def verification_status(user_id):
    with engine.connect() as conn:
        return get_verification_for_user(conn, user_id)


def verification_documents(user_id):
    with engine.connect() as conn:
        return list_verification_documents(conn, user_id=user_id)


def admin_verification_documents(fpo_id):
    with engine.connect() as conn:
        return list_admin_verification_documents(conn, fpo_id=fpo_id)


def admin_verification_document_content(document_id):
    with engine.connect() as conn:
        target = get_admin_verification_document_target(conn, document_id=document_id)
    return target, download_bytes(object_key=target["object_key"])


def admin_verification_checklist(fpo_id):
    with engine.connect() as conn:
        return list_verification_checklist(conn, fpo_id=fpo_id)


def update_admin_verification_checklist(admin_user_id, result_id, result, note):
    with engine.begin() as conn:
        return update_verification_checklist(conn, admin_user_id=admin_user_id, result_id=result_id, result=result, note=note)


def document_upload_intent(user_id, document_type, filename, mime_type, size_bytes, checksum):
    with engine.begin() as conn:
        result = create_document_upload_intent(
            conn, user_id=user_id, document_type=document_type, filename=filename,
            mime_type=mime_type, size_bytes=size_bytes, checksum=checksum,
        )
    return {**result, **create_upload_url(object_key=result["object_key"], mime_type=mime_type, document_id=str(result["document_id"]))}


def document_replacement_intent(user_id, document_id, filename, mime_type, size_bytes, checksum):
    with engine.begin() as conn:
        result = create_document_replacement_intent(conn, user_id=user_id, document_id=document_id, filename=filename, mime_type=mime_type, size_bytes=size_bytes, checksum=checksum)
    return {**result, **create_upload_url(object_key=result["object_key"], mime_type=mime_type, document_id=str(result["document_id"]))}


def upload_document_content(user_id, document_id, content_type: str, data: bytes):
    with engine.connect() as conn:
        target = get_document_upload_target(conn, user_id=user_id, document_id=document_id)
    if content_type.lower() != target["mime_type"].lower():
        raise ValueError("Uploaded content type does not match the upload intent")
    if len(data) != int(target["size_bytes"]):
        raise ValueError("Uploaded content size does not match the upload intent")
    declared = target["mime_type"].lower()
    signatures = {
        "application/pdf": data.startswith(b"%PDF-"),
        "image/jpeg": data.startswith(b"\xff\xd8\xff"),
        "image/png": data.startswith(b"\x89PNG\r\n\x1a\n"),
    }
    if not signatures.get(declared, False):
        raise ValueError("Uploaded bytes do not match the declared document type")
    store_bytes(object_key=target["object_key"], data=data)
    return {"document_id": str(document_id), "upload_status": "UPLOADED", "next_step": "FINALIZE"}


def document_upload_finalize(user_id, document_id, checksum):
    with engine.begin() as conn:
        return finalize_document_upload(conn, user_id=user_id, document_id=document_id, checksum=checksum)


def document_delete(user_id, document_id):
    with engine.begin() as conn:
        row = delete_verification_document(conn, user_id=user_id, document_id=document_id)
    return {"document_id": row["document_id"], "deleted": True, "cleanup": "QUEUED", "original_filename": row["original_filename"]}


def admin_validate_document(admin_user_id, document_id, validation_status, reason, case_id=None, expected_case_version=None):
    with engine.begin() as conn:
        return validate_verification_document(conn, admin_user_id=admin_user_id, document_id=document_id, validation_status=validation_status, reason=reason, case_id=case_id, expected_case_version=expected_case_version)


def submit_verification_request(user_id, expected_profile_version=None, confirmation=True):
    if not confirmation:
        raise ValueError("FPO_VERIFICATION_CONFIRMATION_REQUIRED")
    with engine.begin() as conn:
        return submit_verification(conn, user_id, expected_profile_version=expected_profile_version)


def admin_claim_verification_case(admin_user_id, case_id):
    with engine.begin() as conn:
        return claim_verification_case(conn, case_id=case_id, reviewer_user_id=admin_user_id)


def admin_assign_verification_case(admin_user_id, case_id, reviewer_user_id, reason):
    with engine.begin() as conn:
        return assign_verification_case(conn, case_id=case_id, reviewer_user_id=reviewer_user_id, assigned_by=admin_user_id, reason=reason)


def admin_release_verification_case(admin_user_id, case_id, reason):
    with engine.begin() as conn:
        return release_verification_case(conn, case_id=case_id, reviewer_user_id=admin_user_id, reason=reason)


def admin_escalate_verification_case(admin_user_id, case_id, reason):
    with engine.begin() as conn:
        return escalate_verification_case(conn, case_id=case_id, actor_user_id=admin_user_id, reason=reason)


def admin_decide_verification_case(admin_user_id, case_id, payload):
    with engine.begin() as conn:
        return decide_verification_case(conn, case_id=case_id, reviewer_user_id=admin_user_id, **payload)


def review_verification_request(fpo_id, reviewer_user_id, status, note):
    with engine.begin() as conn:
        return review_verification(
            conn,
            fpo_id=fpo_id,
            reviewer_user_id=reviewer_user_id,
            status=status,
            note=note,
        )


def verification_queue(status: str | None = None):
    with engine.connect() as conn:
        return list_verification_queue(conn, status=status)


def admin_overview():
    with engine.connect() as conn:
        return get_admin_overview(conn)


def discover_fpo_directory(query: str | None = None, limit: int = 25):
    with engine.connect() as conn:
        return discover_fpos(conn, query=query, limit=limit)


def fpo_relationship_consent_policy(language_code="en"):
    from services.fpo_management_service.app.repository import get_current_fpo_consent_policy
    with engine.connect() as conn:
        return get_current_fpo_consent_policy(conn, language_code=language_code)


def request_farmer_relationship(farmer_user_id, fpo_id, farm_id, policy_code, policy_version, accepted, selected_optional_scopes, language_code, correlation_id, ip_address):
    with engine.begin() as conn:
        result = create_farmer_relationship_request(
            conn, farmer_user_id=farmer_user_id, fpo_id=fpo_id, farm_id=farm_id,
            policy_code=policy_code, policy_version=policy_version, accepted=accepted,
            selected_optional_scopes=selected_optional_scopes, language_code=language_code,
            correlation_id=correlation_id, ip_address=ip_address,
        )
        refresh_portfolio_read_models(conn, fpo_id=result["fpo_id"])
        return result


def farmer_relationships(farmer_user_id, farm_id=None):
    with engine.connect() as conn:
        return list_farmer_relationships(conn, farmer_user_id=farmer_user_id, farm_id=farm_id)


def fpo_relationships(fpo_user_id):
    with engine.connect() as conn:
        get_fpo_access_context(conn, user_id=fpo_user_id)
        require_fpo_feature(conn, user_id=fpo_user_id, feature_key="FARMER_DIRECTORY")
        return list_fpo_relationships(conn, fpo_user_id=fpo_user_id)


def decide_relationship(fpo_user_id, relationship_id, decision, note=""):
    with engine.begin() as conn:
        get_fpo_access_context(conn, user_id=fpo_user_id)
        require_fpo_feature(conn, user_id=fpo_user_id, feature_key="FARMER_DIRECTORY")
        result = decide_farmer_relationship(
            conn,
            fpo_user_id=fpo_user_id,
            relationship_id=relationship_id,
            decision=decision,
            note=note,
        )
        refresh_portfolio_read_models(conn, fpo_id=result["fpo_id"])
        return result


def revoke_relationship(farmer_user_id, relationship_id, farm_id=None):
    with engine.begin() as conn:
        result = revoke_farmer_relationship(
            conn,
            farmer_user_id=farmer_user_id, farm_id=farm_id,
            relationship_id=relationship_id,
        )
        refresh_portfolio_read_models(conn, fpo_id=result["fpo_id"])
        return result


def cancel_relationship(farmer_user_id, relationship_id):
    with engine.begin() as conn:
        result = cancel_farmer_relationship_request(conn, farmer_user_id=farmer_user_id, relationship_id=relationship_id)
        refresh_portfolio_read_models(conn, fpo_id=result["fpo_id"])
        return result


def terminate_relationship(fpo_user_id, relationship_id, reason):
    with engine.begin() as conn:
        get_fpo_access_context(conn, user_id=fpo_user_id)
        require_fpo_feature(conn, user_id=fpo_user_id, feature_key="RELATIONSHIP_INBOX")
        result = terminate_farmer_relationship(conn, fpo_user_id=fpo_user_id, relationship_id=relationship_id, reason=reason)
        refresh_portfolio_read_models(conn, fpo_id=result["fpo_id"])
        return result


def fpo_entitlements(user_id):
    with engine.connect() as conn:
        return resolve_fpo_entitlements(conn, user_id=user_id)


def feature_catalogue():
    with engine.connect() as conn:
        return list_feature_catalogue(conn)


def assign_class(fpo_id, class_code, admin_user_id):
    with engine.begin() as conn:
        return assign_fpo_class(conn, fpo_id=fpo_id, class_code=class_code, admin_user_id=admin_user_id)


def create_fpo_feature_override(fpo_id, feature_key, enabled, reason, expires_at, admin_user_id):
    with engine.begin() as conn:
        return create_feature_override(
            conn,
            fpo_id=fpo_id,
            feature_key=feature_key,
            enabled=enabled,
            reason=reason,
            expires_at=expires_at,
            admin_user_id=admin_user_id,
        )


def fpo_feature_overrides(fpo_id):
    with engine.connect() as conn:
        return list_feature_overrides(conn, fpo_id=fpo_id)


def run_fpo_reconciliation(admin_user_id):
    with engine.begin() as conn:
        return reconcile_fpo_data(conn, admin_user_id=admin_user_id)


def portfolio_report(user_id):
    with engine.connect() as conn:
        get_fpo_access_context(conn, user_id=user_id)
        return fpo_portfolio_report(conn, user_id=user_id)


def operational_alerts(user_id, status=None):
    with engine.connect() as conn:
        get_fpo_access_context(conn, user_id=user_id)
        return list_fpo_alerts(conn, user_id=user_id, status=status)


def acknowledge_alert(user_id, alert_id):
    with engine.begin() as conn:
        get_fpo_access_context(conn, user_id=user_id)
        return acknowledge_fpo_alert(conn, user_id=user_id, alert_id=alert_id)


def dashboard_read_model(user_id):
    with engine.begin() as conn:
        organization = get_fpo_access_context(conn, user_id=user_id)
        refresh_portfolio_read_models(conn, fpo_id=organization["fpo_id"])
        return get_fpo_dashboard_read_model(conn, user_id=user_id)


def fpo_import_template(user_id, import_type):
    with engine.begin() as conn: return import_template(conn, user_id=user_id, import_type=import_type)

def fpo_create_import_intent(user_id, import_type, source_format, filename, checksum):
    with engine.begin() as conn: return create_import_intent(conn, user_id=user_id, import_type=import_type, source_format=source_format, filename=filename, checksum=checksum)

def fpo_upload_import_content(user_id, job_id, data):
    with engine.begin() as conn: return upload_import_content(conn, user_id=user_id, job_id=job_id, data=data)

def fpo_validate_import(user_id, job_id):
    with engine.begin() as conn: return validate_import(conn, user_id=user_id, job_id=job_id)

def fpo_list_imports(user_id):
    with engine.connect() as conn: return list_imports(conn, user_id=user_id)

def fpo_get_import(user_id, job_id):
    with engine.connect() as conn: return get_import(conn, user_id=user_id, job_id=job_id)

def fpo_import_rows(user_id, job_id):
    with engine.connect() as conn: return import_rows(conn, user_id=user_id, job_id=job_id)

def fpo_staged_import_records(user_id, job_id):
    with engine.connect() as conn: return staged_import_records(conn, user_id=user_id, job_id=job_id)

def farmer_staged_import_records(user_id):
    with engine.connect() as conn: return farmer_staged_records(conn, user_id=user_id)

def farmer_staged_import_record(user_id, staged_record_id):
    with engine.connect() as conn: return farmer_staged_record(conn, user_id=user_id, staged_record_id=staged_record_id)

def farmer_link_staged_farm(user_id, staged_record_id, farm_id):
    with engine.begin() as conn: return link_staged_farm(conn, user_id=user_id, staged_record_id=staged_record_id, farm_id=farm_id)

def fpo_commit_import(user_id, job_id):
    with engine.begin() as conn: return commit_import(conn, user_id=user_id, job_id=job_id)

def fpo_cancel_import(user_id, job_id):
    with engine.begin() as conn: return cancel_import(conn, user_id=user_id, job_id=job_id)

def fpo_quality_summary(user_id):
    with engine.connect() as conn: return quality_summary(conn, user_id=user_id)

def fpo_quality_issues(user_id):
    with engine.connect() as conn: return quality_issues(conn, user_id=user_id)


def farmer_directory(user_id, query=None, district_code=None, block_code=None, relationship_status=None, cursor=None, limit=50):
    with engine.connect() as conn:
        get_fpo_access_context(conn, user_id=user_id)
        return list_fpo_farmer_portfolio(conn, user_id=user_id, query=query, district_code=district_code, block_code=block_code, relationship_status=relationship_status, cursor=cursor, limit=limit)


def farmer_detail(user_id, farmer_id):
    with engine.begin() as conn:
        return get_fpo_farmer_detail(conn, user_id=user_id, farmer_id=farmer_id)


def farmer_farms(user_id, farmer_id):
    with engine.begin() as conn:
        return list_fpo_farmer_farms(conn, user_id=user_id, farmer_id=farmer_id)


def farm_monitoring(user_id, query=None):
    with engine.begin() as conn:
        return list_fpo_farm_monitoring(conn, user_id=user_id, query=query)


def farmer_farm_intelligence(user_id, farmer_id, farm_id):
    with engine.begin() as conn:
        farm = authorize_fpo_farm_intelligence(conn, user_id=user_id, farmer_id=farmer_id, farm_id=farm_id)
    base = FpoManagementConfig.from_env().analytics_query_service_url
    try:
        with httpx.Client(timeout=15.0) as client:
            responses = {
                "summary": client.get(f"{base}/v1/analytics/farms/{farm_id}/summary"),
                "latest": client.get(f"{base}/v1/analytics/farms/{farm_id}/sentinel2/latest"),
                "h3_cells": client.get(f"{base}/v1/analytics/farms/{farm_id}/h3-cells"),
                "grid_values": client.get(f"{base}/v1/analytics/farms/{farm_id}/grid-values/latest"),
                "grid_calculations": client.get(f"{base}/v1/analytics/farms/{farm_id}/grid-calculations/latest"),
                "calculations": client.get(f"{base}/v1/analytics/farms/{farm_id}/calculations/latest?scope=farm"),
                "calculation_history": client.get(f"{base}/v1/analytics/farms/{farm_id}/calculations/latest?scope=farm&latest_only=false"),
            }
    except httpx.HTTPError as exc:
        raise ValueError("FPO_INTELLIGENCE_UNAVAILABLE") from exc
    payload = {"farm": farm, "read_only": True, "data": {}}
    for key, response in responses.items():
        if response.status_code == 404:
            payload["data"][key] = None
        elif response.is_success:
            payload["data"][key] = response.json()
        else:
            raise ValueError("FPO_INTELLIGENCE_UNAVAILABLE")
    return payload


def create_farmer_support_ticket(user_id, farm_id, fpo_id, category, subject, description):
    with engine.begin() as conn:
        return create_support_ticket(conn, farmer_user_id=user_id, farm_id=farm_id, fpo_id=fpo_id, category=category, subject=subject, description=description)


def farmer_support_tickets(user_id):
    with engine.connect() as conn:
        return list_support_tickets(conn, farmer_user_id=user_id)


def fpo_tags(user_id):
    with engine.connect() as conn: return list_tags(conn, user_id)
def fpo_create_tag(user_id, payload):
    with engine.begin() as conn: return create_tag(conn, user_id, payload)
def fpo_assign_tag(user_id, farmer_id, tag_id):
    with engine.begin() as conn: return assign_tag(conn, user_id, farmer_id, tag_id)
def fpo_segments(user_id):
    with engine.connect() as conn: return list_segments(conn, user_id)
def fpo_create_segment(user_id, payload):
    with engine.begin() as conn: return create_segment(conn, user_id, payload)
def fpo_evaluate_segment(user_id, segment_id):
    with engine.begin() as conn: return evaluate_segment(conn, user_id, segment_id)
def fpo_segment_members(user_id, segment_id):
    with engine.connect() as conn: return segment_members(conn, user_id, segment_id)
def fpo_notes(user_id, farmer_id):
    with engine.connect() as conn: return notes(conn, user_id, farmer_id)
def fpo_create_note(user_id, farmer_id, payload):
    with engine.begin() as conn: return create_note(conn, user_id, farmer_id, payload)
def fpo_season_plans(user_id):
    with engine.connect() as conn: return season_plans(conn, user_id)
def fpo_create_season_plan(user_id, payload):
    with engine.begin() as conn: return create_season_plan(conn, user_id, payload)
def fpo_add_crop_target(user_id, plan_id, payload):
    with engine.begin() as conn: return add_crop_target(conn, user_id, plan_id, payload)
def fpo_tasks(user_id):
    with engine.connect() as conn: return tasks(conn, user_id)
def fpo_create_task(user_id, payload):
    with engine.begin() as conn: return create_task(conn, user_id, payload)
def fpo_update_task(user_id, task_id, status, note=None):
    with engine.begin() as conn: return update_task(conn, user_id, task_id, status, note)

def fpo_metric_registry(user_id):
    with engine.connect() as conn: return metric_registry(conn, user_id)
def fpo_alert_rules(user_id):
    with engine.connect() as conn: return alert_rules(conn, user_id)
def fpo_create_alert_rule(user_id, payload):
    with engine.begin() as conn: return create_alert_rule(conn, user_id, payload)
def fpo_publish_alert_rule(user_id, rule_id, action):
    with engine.begin() as conn: return publish_alert_rule(conn, user_id, rule_id, action)
def fpo_monitoring_summary(user_id):
    with engine.connect() as conn: return monitoring_summary(conn, user_id)
def fpo_advisory_templates(user_id):
    with engine.connect() as conn: return advisory_templates(conn, user_id)
def fpo_preview_advisory(user_id, payload):
    with engine.connect() as conn: return preview_advisory(conn, user_id, payload)
def fpo_campaigns(user_id):
    with engine.connect() as conn: return campaigns(conn, user_id)
def fpo_create_campaign(user_id, payload):
    with engine.begin() as conn: return create_campaign(conn, user_id, payload)
def fpo_estimate_campaign(user_id, campaign_id):
    with engine.begin() as conn: return estimate_campaign(conn, user_id, campaign_id)
def fpo_schedule_campaign(user_id, campaign_id):
    with engine.begin() as conn: return schedule_campaign(conn, user_id, campaign_id)
def fpo_input_plans(user_id):
    with engine.connect() as conn: return input_plans(conn, user_id)
def fpo_create_input_plan(user_id, payload):
    with engine.begin() as conn: return create_input_plan(conn, user_id, payload)
def fpo_calculate_input_plan(user_id, plan_id):
    with engine.begin() as conn: return calculate_input_plan(conn, user_id, plan_id)
def fpo_input_items(user_id, plan_id):
    with engine.connect() as conn: return input_items(conn, user_id, plan_id)
def fpo_forecasts(user_id):
    with engine.connect() as conn: return forecasts(conn, user_id)
def fpo_run_forecast(user_id, payload):
    with engine.begin() as conn: return run_forecast(conn, user_id, payload)
def fpo_report_catalogue(user_id):
    with engine.connect() as conn: return report_catalogue(conn, user_id)
def fpo_report_jobs(user_id):
    with engine.connect() as conn: return report_jobs(conn, user_id)
def fpo_create_report_job(user_id, payload):
    with engine.begin() as conn: return create_report_job(conn, user_id, payload)
def fpo_process_report_jobs(batch_size=5):
    with engine.begin() as conn: return process_report_jobs(conn, batch_size)
def fpo_admin_templates():
    with engine.connect() as conn: return admin_templates(conn)
def fpo_admin_create_template(admin_user_id, payload):
    with engine.begin() as conn: return admin_create_template(conn, admin_user_id, payload)
def fpo_admin_review_template(admin_user_id, template_id, decision):
    with engine.begin() as conn: return admin_review_template(conn, admin_user_id, template_id, decision)
def fpo_release_readiness(admin_user_id):
    with engine.begin() as conn: return release_readiness(conn, admin_user_id)
def fpo_publish_class_b_plan(admin_user_id, reason):
    with engine.begin() as conn: return publish_class_b_plan(conn, admin_user_id, reason)
def fpo_counterparties(user_id):
    with engine.connect() as conn: return counterparties(conn, user_id)
def fpo_create_counterparty(user_id, payload):
    with engine.begin() as conn: return create_counterparty(conn, user_id, payload)
def fpo_update_counterparty_due_diligence(user_id, counterparty_id, status, reason=None):
    with engine.begin() as conn: return update_counterparty_due_diligence(conn, user_id, counterparty_id, status, reason)
def fpo_opportunities(user_id):
    with engine.connect() as conn: return opportunities(conn, user_id)
def fpo_create_opportunity(user_id, payload):
    with engine.begin() as conn: return create_opportunity(conn, user_id, payload)
def fpo_transition_opportunity(user_id, opportunity_id, stage, reason=None):
    with engine.begin() as conn: return transition_opportunity(conn, user_id, opportunity_id, stage, reason)
def fpo_procurement_plans(user_id):
    with engine.connect() as conn: return procurement_plans(conn, user_id)
def fpo_create_procurement_plan(user_id, payload):
    with engine.begin() as conn: return create_procurement_plan(conn, user_id, payload)
def fpo_add_procurement_item(user_id, plan_id, payload):
    with engine.begin() as conn: return add_procurement_item(conn, user_id, plan_id, payload)
def fpo_procurement_items(user_id, plan_id):
    with engine.connect() as conn: return procurement_items(conn, user_id, plan_id)
def fpo_transition_procurement_plan(user_id, plan_id, status, reason=None):
    with engine.begin() as conn: return transition_procurement_plan(conn, user_id, plan_id, status, reason)
def fpo_lots(user_id):
    with engine.connect() as conn: return lots(conn, user_id)
def fpo_create_lot(user_id, payload):
    with engine.begin() as conn: return create_lot(conn, user_id, payload)
def fpo_lot_sources(user_id, lot_id):
    with engine.connect() as conn: return lot_sources(conn, user_id, lot_id)
def fpo_add_lot_source(user_id, lot_id, payload):
    with engine.begin() as conn: return add_lot_source(conn, user_id, lot_id, payload)
def fpo_seal_lot(user_id, lot_id):
    with engine.begin() as conn: return seal_lot(conn, user_id, lot_id)
def fpo_quality_inspections(user_id):
    with engine.connect() as conn: return quality_inspections(conn, user_id)
def fpo_create_quality_inspection(user_id, payload):
    with engine.begin() as conn: return create_quality_inspection(conn, user_id, payload)
def fpo_review_quality_inspection(user_id, inspection_id, disposition, grade=None, note=None):
    with engine.begin() as conn: return review_quality_inspection(conn, user_id, inspection_id, disposition, grade, note)
def fpo_warehouses(user_id):
    with engine.connect() as conn: return warehouses(conn, user_id)
def fpo_create_warehouse(user_id, payload):
    with engine.begin() as conn: return create_warehouse(conn, user_id, payload)
def fpo_inventory_lots(user_id):
    with engine.connect() as conn: return inventory_lots(conn, user_id)
def fpo_create_inventory_lot(user_id, payload):
    with engine.begin() as conn: return create_inventory_lot(conn, user_id, payload)
def fpo_post_inventory_entry(user_id, inventory_lot_id, payload):
    with engine.begin() as conn: return post_inventory_entry(conn, user_id, inventory_lot_id, payload)
def fpo_reconcile_inventory(user_id):
    with engine.begin() as conn: return reconcile_inventory(conn, user_id)
def fpo_admin_quality_schemas():
    with engine.connect() as conn: return admin_quality_schemas(conn)
def fpo_admin_create_quality_schema(user_id, payload):
    with engine.begin() as conn: return admin_create_quality_schema(conn, user_id, payload)
def fpo_admin_publish_quality_schema(user_id, schema_id):
    with engine.begin() as conn: return admin_publish_quality_schema(conn, user_id, schema_id)
def fpo_contracts(user_id):
    with engine.connect() as conn: return contracts(conn, user_id)
def fpo_create_contract(user_id, payload):
    with engine.begin() as conn: return create_contract(conn, user_id, payload)
def fpo_activate_contract(user_id, contract_id):
    with engine.begin() as conn: return activate_contract(conn, user_id, contract_id)
def fpo_orders(user_id):
    with engine.connect() as conn: return orders(conn, user_id)
def fpo_create_order(user_id, payload):
    with engine.begin() as conn: return create_order(conn, user_id, payload)
def fpo_confirm_order(user_id, order_id):
    with engine.begin() as conn: return confirm_order(conn, user_id, order_id)
def fpo_dispatches(user_id):
    with engine.connect() as conn: return dispatches(conn, user_id)
def fpo_create_dispatch(user_id, payload):
    with engine.begin() as conn: return create_dispatch(conn, user_id, payload)
def fpo_add_dispatch_item(user_id, dispatch_id, payload):
    with engine.begin() as conn: return add_dispatch_item(conn, user_id, dispatch_id, payload)
def fpo_depart_dispatch(user_id, dispatch_id):
    with engine.begin() as conn: return depart_dispatch(conn, user_id, dispatch_id)
def fpo_compliance_documents(user_id):
    with engine.connect() as conn: return compliance_documents(conn, user_id)
def fpo_create_compliance_document(user_id, payload):
    with engine.begin() as conn: return create_compliance_document(conn, user_id, payload)
def fpo_compliance_readiness(user_id):
    with engine.connect() as conn: return compliance_readiness(conn, user_id)
def fpo_export_packs(user_id):
    with engine.connect() as conn: return export_packs(conn, user_id)
def fpo_create_export_pack(user_id, payload):
    with engine.begin() as conn: return create_export_pack(conn, user_id, payload)
def fpo_data_pack_schemas(user_id):
    with engine.connect() as conn: return data_pack_schemas(conn, user_id)
def fpo_create_data_pack_request(user_id, payload):
    with engine.begin() as conn: return create_data_pack_request(conn, user_id, payload)
def fpo_validate_data_pack_request(user_id, request_id):
    with engine.begin() as conn: return validate_data_pack_request(conn, user_id, request_id)
def fpo_sustainability_metrics(user_id):
    with engine.connect() as conn: return sustainability_metrics(conn, user_id)
def fpo_api_clients(user_id):
    with engine.connect() as conn: return api_clients(conn, user_id)
def fpo_create_api_client(user_id, payload):
    with engine.begin() as conn: return create_api_client(conn, user_id, payload)
def fpo_rotate_api_client_secret(user_id, client_id):
    with engine.begin() as conn: return rotate_api_client_secret(conn, user_id, client_id)
def fpo_revoke_api_client(user_id, client_id):
    with engine.begin() as conn: return revoke_api_client(conn, user_id, client_id)
def fpo_webhooks(user_id):
    with engine.connect() as conn: return webhooks(conn, user_id)
def fpo_create_webhook(user_id, payload):
    with engine.begin() as conn: return create_webhook(conn, user_id, payload)
def fpo_disable_webhook(user_id, subscription_id):
    with engine.begin() as conn: return disable_webhook(conn, user_id, subscription_id)
def fpo_class_c_release_readiness(admin_user_id):
    with engine.begin() as conn: return class_c_release_readiness(conn, admin_user_id)
def fpo_publish_class_c_plan(admin_user_id, reason):
    with engine.begin() as conn: return publish_class_c_plan(conn, admin_user_id, reason)
