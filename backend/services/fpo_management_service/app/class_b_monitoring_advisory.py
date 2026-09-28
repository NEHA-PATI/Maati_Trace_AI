from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection

from services.fpo_management_service.app.repository import get_fpo_access_context, require_fpo_feature


def _ctx(conn: Connection, user_id: UUID | str, feature: str) -> dict[str, Any]:
    get_fpo_access_context(conn, user_id=user_id)
    require_fpo_feature(conn, user_id=user_id, feature_key=feature)
    return dict(get_fpo_access_context(conn, user_id=user_id))


def metric_registry(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    _ctx(conn, user_id, "ALERT_RULE_MANAGEMENT")
    return [dict(r) for r in conn.execute(text("SELECT * FROM public.fpo_alert_metric_registry WHERE status='ACTIVE' ORDER BY display_name")).mappings()]


def alert_rules(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "ALERT_RULE_MANAGEMENT")
    return [dict(r) for r in conn.execute(text("SELECT * FROM public.fpo_alert_rules WHERE fpo_id=:fpo AND status <> 'ARCHIVED' ORDER BY updated_at DESC"), {"fpo": str(c["fpo_id"])}).mappings()]


def create_alert_rule(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "ALERT_RULE_MANAGEMENT")
    metric = conn.execute(text("SELECT metric_key,allowed_operators,supported_scopes,status FROM public.fpo_alert_metric_registry WHERE metric_key=:metric"), {"metric": payload["feature_metric"]}).mappings().first()
    if not metric or metric["status"] != "ACTIVE": raise ValueError("FPO_ALERT_METRIC_UNAVAILABLE")
    if payload.get("scope_type", "PORTFOLIO") not in metric["supported_scopes"]: raise ValueError("FPO_ALERT_SCOPE_UNSUPPORTED")
    condition = payload.get("condition_configuration") or {}
    if condition.get("operator") not in metric["allowed_operators"]: raise ValueError("FPO_ALERT_OPERATOR_UNSUPPORTED")
    row = conn.execute(text("""
        INSERT INTO public.fpo_alert_rules (fpo_id,name,feature_metric,scope_type,scope_configuration,condition_configuration,severity,deduplication_window_minutes,cooldown_minutes,created_by)
        VALUES (:fpo,:name,:metric,:scope,CAST(:scope_config AS jsonb),CAST(:condition AS jsonb),:severity,:dedupe,:cooldown,:user)
        RETURNING *
    """), {"fpo": str(c["fpo_id"]), "name": payload["name"].strip(), "metric": payload["feature_metric"], "scope": payload.get("scope_type", "PORTFOLIO"), "scope_config": json.dumps(payload.get("scope_configuration") or {}), "condition": json.dumps(condition), "severity": payload.get("severity", "WARNING"), "dedupe": payload.get("deduplication_window_minutes", 360), "cooldown": payload.get("cooldown_minutes", 720), "user": str(user_id)}).mappings().one()
    return dict(row)


def publish_alert_rule(conn: Connection, user_id: UUID | str, rule_id: UUID | str, action: str) -> dict[str, Any]:
    c = _ctx(conn, user_id, "ALERT_RULE_MANAGEMENT")
    rule = conn.execute(text("SELECT * FROM public.fpo_alert_rules WHERE alert_rule_id=:id AND fpo_id=:fpo FOR UPDATE"), {"id": str(rule_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not rule: raise ValueError("FPO_ALERT_RULE_NOT_FOUND")
    if action == "publish" and rule["status"] not in {"DRAFT", "PAUSED"}: raise ValueError("FPO_ALERT_RULE_NOT_PUBLISHABLE")
    status = "ACTIVE" if action == "publish" else "PAUSED"
    row = conn.execute(text("UPDATE public.fpo_alert_rules SET status=:status,published_by=CASE WHEN :status='ACTIVE' THEN :user ELSE published_by END,published_at=CASE WHEN :status='ACTIVE' THEN now() ELSE published_at END,updated_at=now(),rule_version=rule_version+1 WHERE alert_rule_id=:id RETURNING *"), {"id": str(rule_id), "status": status, "user": str(user_id)}).mappings().one()
    return dict(row)


def monitoring_summary(conn: Connection, user_id: UUID | str) -> dict[str, Any]:
    c = _ctx(conn, user_id, "PORTFOLIO_MONITORING_ADVANCED")
    alerts = conn.execute(text("SELECT count(*) FILTER (WHERE a.status IN ('OPEN','ACKNOWLEDGED','IN_PROGRESS')) AS open_alerts,count(*) FILTER (WHERE a.severity='CRITICAL' AND a.status NOT IN ('RESOLVED','DISMISSED')) AS critical_alerts FROM public.fpo_operational_alerts a WHERE a.fpo_id=:fpo"), {"fpo": str(c["fpo_id"])}).mappings().one()
    rules = conn.execute(text("SELECT count(*) FILTER (WHERE r.status='ACTIVE') AS active_rules FROM public.fpo_alert_rules r WHERE r.fpo_id=:fpo"), {"fpo": str(c["fpo_id"])}).mappings().one()
    return {"fpo_id": c["fpo_id"], "open_alerts": int(alerts["open_alerts"] or 0), "critical_alerts": int(alerts["critical_alerts"] or 0), "active_rules": int(rules["active_rules"] or 0)}


def advisory_templates(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    _ctx(conn, user_id, "ADVISORY_WORKBENCH")
    return [dict(r) for r in conn.execute(text("SELECT template_id,template_code,name,advisory_type,crop_code,stage_code,language_code,title_template,body_template,required_consent_scopes,version,safety_review_status FROM public.fpo_advisory_templates WHERE status='PUBLISHED' AND safety_review_status IN ('APPROVED','NOT_REQUIRED') AND (fpo_id IS NULL OR fpo_id=(SELECT fpo_id FROM public.fpo_organizations WHERE auth_user_id=:user)) ORDER BY name,language_code"), {"user": str(user_id)}).mappings()]


def preview_advisory(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    _ctx(conn, user_id, "ADVISORY_WORKBENCH")
    template = conn.execute(text("SELECT * FROM public.fpo_advisory_templates WHERE template_id=:id AND status='PUBLISHED' AND safety_review_status IN ('APPROVED','NOT_REQUIRED')"), {"id": str(payload["template_id"])}).mappings().first()
    if not template: raise ValueError("FPO_ADVISORY_TEMPLATE_UNAVAILABLE")
    substitutions = payload.get("variables") or {}
    title, body = template["title_template"], template["body_template"]
    for key, value in substitutions.items(): title = title.replace("{{" + key + "}}", str(value)); body = body.replace("{{" + key + "}}", str(value))
    return {"template_id": template["template_id"], "language_code": template["language_code"], "title": title, "body": body, "required_consent_scopes": template["required_consent_scopes"], "safety_review_status": template["safety_review_status"]}


def campaigns(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "COMMUNICATION_BROADCAST")
    return [dict(r) for r in conn.execute(text("SELECT * FROM public.fpo_advisory_campaigns WHERE fpo_id=:fpo ORDER BY created_at DESC"), {"fpo": str(c["fpo_id"])}).mappings()]


def create_campaign(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "COMMUNICATION_BROADCAST")
    template = conn.execute(text("SELECT template_id,required_consent_scopes FROM public.fpo_advisory_templates WHERE template_id=:id AND status='PUBLISHED' AND safety_review_status IN ('APPROVED','NOT_REQUIRED')"), {"id": str(payload["template_id"])}).mappings().first()
    if not template: raise ValueError("FPO_ADVISORY_TEMPLATE_UNAVAILABLE")
    if payload.get("channel", "IN_APP") not in {"IN_APP", "SMS", "WHATSAPP", "VOICE"}: raise ValueError("FPO_CAMPAIGN_CHANNEL_INVALID")
    row = conn.execute(text("INSERT INTO public.fpo_advisory_campaigns (fpo_id,name,template_id,segment_id,recipient_filter_snapshot,channel,language_strategy,fixed_language_code,created_by) VALUES (:fpo,:name,:template,:segment,CAST(:snapshot AS jsonb),:channel,:strategy,:language,:user) RETURNING *"), {"fpo": str(c["fpo_id"]), "name": payload["name"].strip(), "template": str(payload["template_id"]), "segment": str(payload["segment_id"]) if payload.get("segment_id") else None, "snapshot": json.dumps(payload.get("recipient_filter_snapshot") or {}), "channel": payload.get("channel", "IN_APP"), "strategy": payload.get("language_strategy", "FARMER_PREFERENCE"), "language": payload.get("fixed_language_code"), "user": str(user_id)}).mappings().one()
    return dict(row)


def estimate_campaign(conn: Connection, user_id: UUID | str, campaign_id: UUID | str) -> dict[str, Any]:
    c = _ctx(conn, user_id, "COMMUNICATION_BROADCAST")
    campaign = conn.execute(text("SELECT * FROM public.fpo_advisory_campaigns WHERE campaign_id=:id AND fpo_id=:fpo FOR UPDATE"), {"id": str(campaign_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not campaign: raise ValueError("FPO_CAMPAIGN_NOT_FOUND")
    segment_join = "JOIN public.fpo_farmer_segment_members m ON m.farmer_id=r.farmer_profile_id AND m.relationship_id=r.relationship_id" if campaign["segment_id"] else ""
    scope = "AND m.segment_id=:segment" if campaign["segment_id"] else ""
    params = {"fpo": str(c["fpo_id"]), "segment": str(campaign["segment_id"])}
    # Consent is rechecked at estimate and must be checked again by the dispatcher.
    rows = conn.execute(text(f"""SELECT r.relationship_id,r.farmer_profile_id,c.consent_id FROM public.fpo_farmer_relationships r {segment_join} JOIN public.fpo_farmer_relationship_consents c ON c.relationship_id=r.relationship_id AND c.revoked_at IS NULL AND (c.expires_at IS NULL OR c.expires_at>now()) WHERE r.fpo_id=:fpo AND r.status='ACTIVE' AND 'ADVISORY_MESSAGE'=ANY(c.scopes) {scope}"""), params).mappings().all()
    conn.execute(text("UPDATE public.fpo_advisory_campaigns SET recipient_count=:count,eligible_count=:count,suppressed_count=0,updated_at=now() WHERE campaign_id=:id"), {"id": str(campaign_id), "count": len(rows)})
    return {"campaign_id": campaign_id, "recipient_count": len(rows), "eligible_count": len(rows), "suppressed_count": 0, "required_scope": "ADVISORY_MESSAGE"}


def schedule_campaign(conn: Connection, user_id: UUID | str, campaign_id: UUID | str) -> dict[str, Any]:
    estimate_campaign(conn, user_id, campaign_id)
    row = conn.execute(text("UPDATE public.fpo_advisory_campaigns SET status='SCHEDULED',scheduled_at=now(),updated_at=now(),version=version+1 WHERE campaign_id=:id AND status='DRAFT' RETURNING campaign_id,status,scheduled_at,eligible_count,suppressed_count"), {"id": str(campaign_id)}).mappings().first()
    if not row: raise ValueError("FPO_CAMPAIGN_NOT_SCHEDULABLE")
    return dict(row)
