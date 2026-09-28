from __future__ import annotations

import hashlib
import json
import secrets
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.engine import Connection

from services.fpo_management_service.app.repository import get_fpo_access_context, require_fpo_feature


def _ctx(conn: Connection, user_id: UUID | str, feature: str) -> dict[str, Any]:
    context = get_fpo_access_context(conn, user_id=user_id)
    require_fpo_feature(conn, user_id=user_id, feature_key=feature)
    return dict(context)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def api_clients(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "ENTERPRISE_API_ACCESS")
    return [dict(row) for row in conn.execute(text("SELECT client_id,client_name,client_identifier,scopes,rate_limit_per_minute,status,last_used_at,expires_at,revoked_at,created_at FROM public.fpo_api_clients WHERE fpo_id=:fpo ORDER BY created_at DESC"), {"fpo": str(c["fpo_id"])}).mappings()]


def create_api_client(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "ENTERPRISE_API_ACCESS")
    client_secret = secrets.token_urlsafe(36)
    client_identifier = f"mtc_{secrets.token_urlsafe(12)}"
    allowed = {"TRACEABILITY_READ", "PROCUREMENT_READ", "INVENTORY_READ", "ORDER_READ", "WEBHOOK_MANAGE"}
    scopes = [scope for scope in payload.get("scopes", []) if scope in allowed]
    if not scopes: raise ValueError("FPO_API_SCOPES_REQUIRED")
    row = conn.execute(text("INSERT INTO public.fpo_api_clients (fpo_id,client_name,client_identifier,secret_hash,scopes,rate_limit_per_minute,expires_at,created_by_user_id) VALUES (:fpo,:name,:identifier,:hash,CAST(:scopes AS jsonb),:rate,:expires,:user) RETURNING client_id,client_name,client_identifier,scopes,rate_limit_per_minute,status,expires_at,created_at"), {"fpo": str(c["fpo_id"]), "name": payload["client_name"].strip(), "identifier": client_identifier, "hash": _digest(client_secret), "scopes": json.dumps(scopes), "rate": min(max(int(payload.get("rate_limit_per_minute", 60)), 1), 1000), "expires": payload.get("expires_at"), "user": str(user_id)}).mappings().one()
    result = dict(row); result["client_secret"] = client_secret; result["secret_display_warning"] = "Store this secret now. It will never be displayed again."; return result


def rotate_api_client_secret(conn: Connection, user_id: UUID | str, client_id: UUID | str) -> dict[str, Any]:
    c = _ctx(conn, user_id, "ENTERPRISE_API_ACCESS"); secret = secrets.token_urlsafe(36)
    row = conn.execute(text("UPDATE public.fpo_api_clients SET secret_hash=:hash,updated_at=now(),status='ACTIVE',revoked_at=NULL WHERE client_id=:id AND fpo_id=:fpo AND status<>'REVOKED' RETURNING client_id,client_name,client_identifier,status,expires_at"), {"hash": _digest(secret), "id": str(client_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not row: raise ValueError("FPO_API_CLIENT_NOT_FOUND")
    result = dict(row); result["client_secret"] = secret; result["secret_display_warning"] = "Store this secret now. It will never be displayed again."; return result


def revoke_api_client(conn: Connection, user_id: UUID | str, client_id: UUID | str) -> dict[str, Any]:
    c = _ctx(conn, user_id, "ENTERPRISE_API_ACCESS")
    row = conn.execute(text("UPDATE public.fpo_api_clients SET status='REVOKED',revoked_at=now(),updated_at=now() WHERE client_id=:id AND fpo_id=:fpo RETURNING client_id,status,revoked_at"), {"id": str(client_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not row: raise ValueError("FPO_API_CLIENT_NOT_FOUND")
    return dict(row)


def webhooks(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "OUTBOUND_WEBHOOKS")
    return [dict(row) for row in conn.execute(text("SELECT subscription_id,name,endpoint_url,event_types,status,failure_count,last_delivered_at,disabled_at,created_at FROM public.fpo_webhook_subscriptions WHERE fpo_id=:fpo ORDER BY created_at DESC"), {"fpo": str(c["fpo_id"])}).mappings()]


def create_webhook(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "OUTBOUND_WEBHOOKS")
    if not payload["endpoint_url"].startswith("https://"): raise ValueError("FPO_WEBHOOK_HTTPS_REQUIRED")
    secret = secrets.token_urlsafe(36)
    row = conn.execute(text("INSERT INTO public.fpo_webhook_subscriptions (fpo_id,name,endpoint_url,secret_hash,event_types,created_by_user_id) VALUES (:fpo,:name,:endpoint,:hash,CAST(:events AS jsonb),:user) RETURNING subscription_id,name,endpoint_url,event_types,status,created_at"), {"fpo": str(c["fpo_id"]), "name": payload["name"].strip(), "endpoint": payload["endpoint_url"], "hash": _digest(secret), "events": json.dumps(payload.get("event_types", [])), "user": str(user_id)}).mappings().one()
    result = dict(row); result["signing_secret"] = secret; result["secret_display_warning"] = "Store this signing secret now. It will never be displayed again."; return result


def disable_webhook(conn: Connection, user_id: UUID | str, subscription_id: UUID | str) -> dict[str, Any]:
    c = _ctx(conn, user_id, "OUTBOUND_WEBHOOKS")
    row = conn.execute(text("UPDATE public.fpo_webhook_subscriptions SET status='DISABLED',disabled_at=now(),updated_at=now() WHERE subscription_id=:id AND fpo_id=:fpo RETURNING subscription_id,status,disabled_at"), {"id": str(subscription_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not row: raise ValueError("FPO_WEBHOOK_NOT_FOUND")
    return dict(row)


def class_c_release_readiness(conn: Connection, admin_user_id: UUID | str) -> dict[str, Any]:
    plan = conn.execute(text("SELECT * FROM public.fpo_plan_versions WHERE class_code='C' AND version=4")).mappings().first()
    if not plan: raise ValueError("FPO_CLASS_C_PLAN_NOT_FOUND")
    checks: list[dict[str, Any]] = []
    def add(key: str, passed: bool, evidence: dict[str, Any]) -> None:
        checks.append({"check_key": key, "status": "PASS" if passed else "FAIL", "evidence": evidence})
    feature_count = int(conn.execute(text("SELECT count(*) FROM public.fpo_class_feature_versions WHERE class_code='C' AND version=4 AND enabled" )).scalar_one())
    add("CLASS_C_FEATURE_CONFIGURATION", feature_count >= 50, {"enabled_feature_count": feature_count})
    add("CLASS_B_PLAN_FOUNDATION", bool(conn.execute(text("SELECT 1 FROM public.fpo_plan_versions WHERE class_code='B' AND status='PUBLISHED'")).scalar_one_or_none()), {})
    for table, key in [("fpo_aggregation_lots", "TRACEABILITY_CONTRACT"), ("fpo_inventory_ledger", "INVENTORY_CONTRACT"), ("fpo_commercial_contracts", "COMMERCIAL_CONTRACT"), ("fpo_export_packs", "EXPORT_PACK_CONTRACT"), ("fpo_data_sharing_grants", "DATA_SHARING_CONTRACT"), ("fpo_api_clients", "INTEGRATION_CONTRACT")]:
        add(key, bool(conn.execute(text("SELECT to_regclass(:name)"), {"name": f"public.{table}"}).scalar_one_or_none()), {})
    for item in checks:
        conn.execute(text("INSERT INTO public.fpo_class_c_release_checks (plan_version_id,check_key,status,evidence,checked_by) VALUES (:plan,:key,:status,CAST(:evidence AS jsonb),:user) ON CONFLICT (plan_version_id,check_key) DO UPDATE SET status=EXCLUDED.status,evidence=EXCLUDED.evidence,checked_by=EXCLUDED.checked_by,checked_at=now()"), {"plan": str(plan["plan_version_id"]), "key": item["check_key"], "status": item["status"], "evidence": json.dumps(item["evidence"]), "user": str(admin_user_id)})
    return {"plan": dict(plan), "checks": checks, "ready": all(item["status"] == "PASS" for item in checks)}


def publish_class_c_plan(conn: Connection, admin_user_id: UUID | str, reason: str) -> dict[str, Any]:
    readiness = class_c_release_readiness(conn, admin_user_id)
    if not readiness["ready"]: raise ValueError("FPO_CLASS_C_RELEASE_NOT_READY")
    row = conn.execute(text("UPDATE public.fpo_plan_versions SET status='PUBLISHED',release_state='PUBLISHED',effective_from=now(),published_at=now(),published_by=:user,publication_reason=:reason WHERE class_code='C' AND version=4 AND status='DRAFT' RETURNING *"), {"user": str(admin_user_id), "reason": reason.strip()}).mappings().first()
    if not row: raise ValueError("FPO_CLASS_C_PLAN_NOT_PUBLISHABLE")
    return dict(row)
