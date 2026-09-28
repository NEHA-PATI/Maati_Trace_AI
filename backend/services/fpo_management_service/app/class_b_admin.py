from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection

from services.fpo_management_service.app.storage import store_bytes


def admin_templates(conn: Connection) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(text("SELECT * FROM public.fpo_advisory_templates ORDER BY created_at DESC,language_code")).mappings()]


def admin_create_template(conn: Connection, admin_user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    row = conn.execute(text("""
        INSERT INTO public.fpo_advisory_templates (fpo_id,template_code,name,advisory_type,crop_code,stage_code,language_code,title_template,body_template,required_consent_scopes,status,safety_review_status,created_by)
        VALUES (NULL,:code,:name,:type,:crop,:stage,:language,:title,:body,:scopes,'DRAFT','PENDING',:user) RETURNING *
    """), {"code": payload["template_code"], "name": payload["name"], "type": payload["advisory_type"], "crop": payload.get("crop_code"), "stage": payload.get("stage_code"), "language": payload.get("language_code", "en"), "title": payload["title_template"], "body": payload["body_template"], "scopes": payload.get("required_consent_scopes", ["ADVISORY_MESSAGE"]), "user": str(admin_user_id)}).mappings().one()
    return dict(row)


def admin_review_template(conn: Connection, admin_user_id: UUID | str, template_id: UUID | str, decision: str) -> dict[str, Any]:
    if decision not in {"APPROVE", "REJECT", "RETIRE"}: raise ValueError("Unsupported template decision")
    safety, status = ({"APPROVE": ("APPROVED", "PUBLISHED"), "REJECT": ("REJECTED", "DRAFT"), "RETIRE": ("APPROVED", "RETIRED")})[decision]
    row = conn.execute(text("UPDATE public.fpo_advisory_templates SET safety_review_status=:safety,status=:status,safety_reviewed_by=:user,safety_reviewed_at=now(),updated_at=now() WHERE template_id=:id RETURNING *"), {"safety": safety, "status": status, "user": str(admin_user_id), "id": str(template_id)}).mappings().first()
    if not row: raise ValueError("FPO_ADVISORY_TEMPLATE_NOT_FOUND")
    return dict(row)


def release_readiness(conn: Connection, admin_user_id: UUID | str) -> dict[str, Any]:
    plan = conn.execute(text("SELECT * FROM public.fpo_plan_versions WHERE class_code='B' AND version=3")).mappings().first()
    if not plan: raise ValueError("FPO_CLASS_B_PLAN_NOT_FOUND")
    checks = []
    def add(key, passed, evidence):
        checks.append({"check_key": key, "status": "PASS" if passed else "FAIL", "evidence": evidence})
    feature_count = conn.execute(text("SELECT count(*) FROM public.fpo_class_feature_versions WHERE class_code='B' AND version=3 AND enabled AND published_at IS NOT NULL")).scalar_one()
    add("CLASS_B_FEATURE_CONFIGURATION", int(feature_count) >= 20, {"enabled_feature_count": int(feature_count)})
    add("CLASS_A_PLAN_PUBLISHED", bool(conn.execute(text("SELECT 1 FROM public.fpo_plan_versions WHERE class_code='A' AND status='PUBLISHED'")).scalar_one_or_none()), {})
    add("IMPORT_CONTRACT", bool(conn.execute(text("SELECT to_regclass('public.fpo_bulk_import_jobs')")).scalar_one_or_none()), {})
    add("REPORT_CONTRACT", bool(conn.execute(text("SELECT to_regclass('public.fpo_report_jobs')")).scalar_one_or_none()), {})
    add("ADVISORY_GOVERNANCE", bool(conn.execute(text("SELECT to_regclass('public.fpo_advisory_templates')")).scalar_one_or_none()), {})
    for item in checks:
        conn.execute(text("INSERT INTO public.fpo_class_b_release_checks (plan_version_id,check_key,status,evidence,checked_by) VALUES (:plan,:key,:status,CAST(:evidence AS jsonb),:user) ON CONFLICT (plan_version_id,check_key) DO UPDATE SET status=EXCLUDED.status,evidence=EXCLUDED.evidence,checked_by=EXCLUDED.checked_by,checked_at=now()"), {"plan": str(plan["plan_version_id"]), "key": item["check_key"], "status": item["status"], "evidence": json.dumps(item["evidence"]), "user": str(admin_user_id)})
    return {"plan": dict(plan), "checks": checks, "ready": all(item["status"] == "PASS" for item in checks)}


def publish_class_b_plan(conn: Connection, admin_user_id: UUID | str, reason: str) -> dict[str, Any]:
    readiness = release_readiness(conn, admin_user_id)
    if not readiness["ready"]: raise ValueError("FPO_CLASS_B_RELEASE_NOT_READY")
    row = conn.execute(text("UPDATE public.fpo_plan_versions SET status='PUBLISHED',effective_from=now(),published_at=now(),published_by=:user,publication_reason=:reason WHERE class_code='B' AND version=3 AND status='DRAFT' RETURNING *"), {"user": str(admin_user_id), "reason": reason.strip()}).mappings().first()
    if not row: raise ValueError("FPO_CLASS_B_PLAN_NOT_PUBLISHABLE")
    return dict(row)


def process_report_jobs(conn: Connection, batch_size: int = 5) -> int:
    jobs = conn.execute(text("SELECT * FROM public.fpo_report_jobs WHERE status='QUEUED' ORDER BY requested_at FOR UPDATE SKIP LOCKED LIMIT :limit"), {"limit": batch_size}).mappings().all()
    count = 0
    for job in jobs:
        conn.execute(text("UPDATE public.fpo_report_jobs SET status='RUNNING',started_at=now() WHERE report_job_id=:id"), {"id": str(job["report_job_id"])})
        output = io.StringIO(); writer = csv.writer(output); writer.writerow(["report_type", "generated_at", "fpo_id"]); writer.writerow([job["report_type"], datetime.now(timezone.utc).isoformat(), str(job["fpo_id"])])
        data = output.getvalue().encode(); key = f"fpo-reports/{job['fpo_id']}/{job['report_job_id']}.csv"; store_bytes(object_key=key, data=data)
        artifact = conn.execute(text("INSERT INTO public.fpo_report_artifacts (report_job_id,object_key,filename,mime_type,size_bytes,checksum,expires_at) VALUES (:job,:key,:filename,'text/csv',:size,encode(digest(:data,'sha256'),'hex'),:expires) RETURNING report_artifact_id"), {"job": str(job["report_job_id"]), "key": key, "filename": f"{job['report_type'].lower()}-{job['report_job_id']}.csv", "size": len(data), "data": data, "expires": job["expires_at"]}).scalar_one()
        conn.execute(text("UPDATE public.fpo_report_jobs SET status='COMPLETED',completed_at=now(),row_count=1 WHERE report_job_id=:id"), {"id": str(job["report_job_id"])})
        count += 1
    return count
