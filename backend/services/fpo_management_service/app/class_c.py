from __future__ import annotations

import hashlib
import json
import os
from typing import Any
from uuid import UUID

from cryptography.fernet import Fernet
from sqlalchemy import text
from sqlalchemy.engine import Connection

from services.fpo_management_service.app.repository import get_fpo_access_context, require_fpo_feature


def _key() -> bytes:
    value = os.getenv("FPO_PRIVATE_DATA_KEY") or os.getenv("DOCUMENT_ENCRYPTION_KEY")
    if not value:
        raise ValueError("FPO_PRIVATE_DATA_KEY_NOT_CONFIGURED")
    return value.encode()


def _cipher(value: str | None) -> bytes | None:
    return Fernet(_key()).encrypt(value.encode("utf-8")) if value else None


def _ctx(conn: Connection, user_id: UUID | str, feature: str) -> dict[str, Any]:
    context = get_fpo_access_context(conn, user_id=user_id)
    require_fpo_feature(conn, user_id=user_id, feature_key=feature)
    return dict(context)


def _audit(conn: Connection, fpo_id: str, user_id: UUID | str, action: str, resource_type: str, resource_id: str | None, reason: str | None = None) -> None:
    conn.execute(text("""
        INSERT INTO public.fpo_commercial_audit_events
            (fpo_id,actor_user_id,action,resource_type,resource_id,reason)
        VALUES (:fpo,:user,:action,:type,:resource,:reason)
    """), {"fpo": fpo_id, "user": str(user_id), "action": action, "type": resource_type, "resource": resource_id, "reason": reason})


def counterparties(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "BUYER_EXPORTER_CRM")
    rows = conn.execute(text("""
        SELECT counterparty_id,counterparty_code,counterparty_type,legal_name,trade_name,
               country_code,state_code,district_code,preferred_currency,risk_rating,
               due_diligence_status,status,created_at,updated_at
        FROM public.fpo_counterparties
        WHERE fpo_id=:fpo AND status <> 'ARCHIVED'
        ORDER BY updated_at DESC
    """), {"fpo": str(c["fpo_id"])}).mappings().all()
    return [dict(row) for row in rows]


def create_counterparty(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "BUYER_EXPORTER_CRM")
    row = conn.execute(text("""
        INSERT INTO public.fpo_counterparties
            (fpo_id,counterparty_code,counterparty_type,legal_name,trade_name,registration_number,
             tax_identifier_encrypted,country_code,state_code,district_code,address_line_1,address_line_2,
             postal_code,website_url,preferred_currency,payment_terms_code,risk_rating,notes_encrypted,created_by_user_id)
        VALUES (:fpo,:code,:type,:legal,:trade,:registration,:tax,:country,:state,:district,:address1,:address2,
                :postal,:website,:currency,:terms,:risk,:notes,:user)
        RETURNING counterparty_id,counterparty_code,counterparty_type,legal_name,trade_name,country_code,
                  state_code,district_code,preferred_currency,risk_rating,due_diligence_status,status,created_at
    """), {"fpo": str(c["fpo_id"]), "code": payload["counterparty_code"].strip().upper(), "type": payload["counterparty_type"].upper(), "legal": payload["legal_name"].strip(), "trade": payload.get("trade_name"), "registration": payload.get("registration_number"), "tax": _cipher(payload.get("tax_identifier")), "country": payload.get("country_code", "IN").upper(), "state": payload.get("state_code"), "district": payload.get("district_code"), "address1": payload.get("address_line_1"), "address2": payload.get("address_line_2"), "postal": payload.get("postal_code"), "website": payload.get("website_url"), "currency": payload.get("preferred_currency", "INR").upper(), "terms": payload.get("payment_terms_code"), "risk": payload.get("risk_rating"), "notes": _cipher(payload.get("notes")), "user": str(user_id)}).mappings().one()
    _audit(conn, str(c["fpo_id"]), user_id, "COUNTERPARTY_CREATED", "counterparty", str(row["counterparty_id"]))
    return dict(row)


def update_counterparty_due_diligence(conn: Connection, user_id: UUID | str, counterparty_id: UUID | str, status: str, reason: str | None = None) -> dict[str, Any]:
    c = _ctx(conn, user_id, "BUYER_EXPORTER_CRM")
    status = status.upper()
    if status not in {"PENDING", "UNDER_REVIEW", "APPROVED", "REJECTED", "EXPIRED"}:
        raise ValueError("FPO_DUE_DILIGENCE_STATUS_INVALID")
    row = conn.execute(text("""
        UPDATE public.fpo_counterparties
        SET due_diligence_status=:status,due_diligence_reviewed_at=now(),
            due_diligence_expires_at=CASE WHEN :status='APPROVED' THEN now()+interval '365 days' ELSE NULL END,
            updated_at=now(),version_no=version_no+1
        WHERE counterparty_id=:id AND fpo_id=:fpo RETURNING *
    """), {"status": status, "id": str(counterparty_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not row:
        raise ValueError("FPO_COUNTERPARTY_NOT_FOUND")
    _audit(conn, str(c["fpo_id"]), user_id, "COUNTERPARTY_DUE_DILIGENCE_UPDATED", "counterparty", str(counterparty_id), reason)
    result = dict(row)
    result.pop("tax_identifier_encrypted", None)
    result.pop("notes_encrypted", None)
    return result


def opportunities(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "MARKET_OPPORTUNITIES")
    return [dict(row) for row in conn.execute(text("""
        SELECT o.*,c.legal_name AS counterparty_name
        FROM public.fpo_market_opportunities o
        JOIN public.fpo_counterparties c ON c.counterparty_id=o.counterparty_id AND c.fpo_id=o.fpo_id
        WHERE o.fpo_id=:fpo ORDER BY o.updated_at DESC
    """), {"fpo": str(c["fpo_id"])}).mappings()]


def create_opportunity(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "MARKET_OPPORTUNITIES")
    counterparty = conn.execute(text("SELECT counterparty_id FROM public.fpo_counterparties WHERE counterparty_id=:id AND fpo_id=:fpo AND status='ACTIVE'"), {"id": str(payload["counterparty_id"]), "fpo": str(c["fpo_id"])}).scalar_one_or_none()
    if not counterparty:
        raise ValueError("FPO_COUNTERPARTY_NOT_FOUND")
    row = conn.execute(text("""
        INSERT INTO public.fpo_market_opportunities
          (fpo_id,opportunity_code,counterparty_id,title,commodity_code,variety_code,quality_grade_code,
           target_quantity,quantity_unit,target_price,currency_code,delivery_start_date,delivery_end_date,
           delivery_location_text,source_channel,probability_percent,owner_notes_encrypted,created_by_user_id)
        VALUES (:fpo,:code,:counterparty,:title,:commodity,:variety,:grade,:quantity,:unit,:price,:currency,
                :start,:end,:location,:channel,:probability,:notes,:user) RETURNING *
    """), {"fpo": str(c["fpo_id"]), "code": payload["opportunity_code"].strip().upper(), "counterparty": str(counterparty), "title": payload["title"].strip(), "commodity": payload["commodity_code"].strip().upper(), "variety": payload.get("variety_code"), "grade": payload.get("quality_grade_code"), "quantity": payload["target_quantity"], "unit": payload["quantity_unit"], "price": payload.get("target_price"), "currency": payload.get("currency_code", "INR").upper(), "start": payload.get("delivery_start_date"), "end": payload.get("delivery_end_date"), "location": payload.get("delivery_location_text"), "channel": payload.get("source_channel", "DIRECT").upper(), "probability": payload.get("probability_percent"), "notes": _cipher(payload.get("owner_notes")), "user": str(user_id)}).mappings().one()
    _audit(conn, str(c["fpo_id"]), user_id, "OPPORTUNITY_CREATED", "market_opportunity", str(row["opportunity_id"]))
    result = dict(row); result.pop("owner_notes_encrypted", None); return result


def transition_opportunity(conn: Connection, user_id: UUID | str, opportunity_id: UUID | str, stage: str, reason: str | None = None) -> dict[str, Any]:
    c = _ctx(conn, user_id, "MARKET_OPPORTUNITIES")
    stage = stage.upper()
    allowed = {"DRAFT", "QUALIFYING", "PROPOSAL", "NEGOTIATION", "WON", "LOST", "CANCELLED"}
    if stage not in allowed:
        raise ValueError("FPO_OPPORTUNITY_STAGE_INVALID")
    if stage in {"LOST", "CANCELLED"} and len((reason or "").strip()) < 3:
        raise ValueError("FPO_OPPORTUNITY_REASON_REQUIRED")
    row = conn.execute(text("""
        UPDATE public.fpo_market_opportunities SET stage=:stage,
          lost_reason_code=CASE WHEN :stage IN ('LOST','CANCELLED') THEN :reason ELSE lost_reason_code END,
          closed_at=CASE WHEN :stage IN ('WON','LOST','CANCELLED') THEN now() ELSE NULL END,
          updated_at=now(),version_no=version_no+1
        WHERE opportunity_id=:id AND fpo_id=:fpo RETURNING *
    """), {"stage": stage, "reason": reason, "id": str(opportunity_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not row:
        raise ValueError("FPO_OPPORTUNITY_NOT_FOUND")
    _audit(conn, str(c["fpo_id"]), user_id, "OPPORTUNITY_STAGE_CHANGED", "market_opportunity", str(opportunity_id), reason)
    result = dict(row); result.pop("owner_notes_encrypted", None); return result


def procurement_plans(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "PROCUREMENT_PLANNING")
    return [dict(row) for row in conn.execute(text("SELECT * FROM public.fpo_procurement_plans WHERE fpo_id=:fpo ORDER BY updated_at DESC"), {"fpo": str(c["fpo_id"]) }).mappings()]


def create_procurement_plan(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "PROCUREMENT_PLANNING")
    row = conn.execute(text("""
        INSERT INTO public.fpo_procurement_plans
          (fpo_id,plan_code,name,season_code,season_year,start_date,end_date,currency_code,notes,created_by_user_id)
        VALUES (:fpo,:code,:name,:season,:year,:start,:end,:currency,:notes,:user) RETURNING *
    """), {"fpo": str(c["fpo_id"]), "code": payload["plan_code"].strip().upper(), "name": payload["name"].strip(), "season": payload["season_code"].strip().upper(), "year": payload["season_year"], "start": payload["start_date"], "end": payload["end_date"], "currency": payload.get("currency_code", "INR").upper(), "notes": payload.get("notes"), "user": str(user_id)}).mappings().one()
    _audit(conn, str(c["fpo_id"]), user_id, "PROCUREMENT_PLAN_CREATED", "procurement_plan", str(row["procurement_plan_id"]))
    return dict(row)


def add_procurement_item(conn: Connection, user_id: UUID | str, plan_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "PROCUREMENT_PLANNING")
    plan = conn.execute(text("SELECT status FROM public.fpo_procurement_plans WHERE procurement_plan_id=:id AND fpo_id=:fpo"), {"id": str(plan_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not plan or plan["status"] not in {"DRAFT", "UNDER_REVIEW"}:
        raise ValueError("FPO_PROCUREMENT_PLAN_NOT_EDITABLE")
    row = conn.execute(text("""
        INSERT INTO public.fpo_procurement_plan_items
          (fpo_id,procurement_plan_id,commodity_code,variety_code,quality_grade_code,district_code,block_code,target_quantity,quantity_unit,forecast_available_quantity,target_min_price,target_max_price,shortfall_threshold_percent,created_by_user_id)
        VALUES (:fpo,:plan,:commodity,:variety,:grade,:district,:block,:quantity,:unit,:forecast,:min_price,:max_price,:threshold,:user) RETURNING *
    """), {"fpo": str(c["fpo_id"]), "plan": str(plan_id), "commodity": payload["commodity_code"].strip().upper(), "variety": payload.get("variety_code"), "grade": payload.get("quality_grade_code"), "district": payload.get("district_code"), "block": payload.get("block_code"), "quantity": payload["target_quantity"], "unit": payload["quantity_unit"], "forecast": payload.get("forecast_available_quantity"), "min_price": payload.get("target_min_price"), "max_price": payload.get("target_max_price"), "threshold": payload.get("shortfall_threshold_percent"), "user": str(user_id)}).mappings().one()
    conn.execute(text("UPDATE public.fpo_procurement_plans SET updated_at=now(),version_no=version_no+1 WHERE procurement_plan_id=:id"), {"id": str(plan_id)})
    return dict(row)


def procurement_items(conn: Connection, user_id: UUID | str, plan_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "PROCUREMENT_PLANNING")
    return [dict(row) for row in conn.execute(text("SELECT i.* FROM public.fpo_procurement_plan_items i WHERE i.fpo_id=:fpo AND i.procurement_plan_id=:plan ORDER BY i.commodity_code"), {"fpo": str(c["fpo_id"]), "plan": str(plan_id)}).mappings()]


def transition_procurement_plan(conn: Connection, user_id: UUID | str, plan_id: UUID | str, status: str, reason: str | None = None) -> dict[str, Any]:
    c = _ctx(conn, user_id, "PROCUREMENT_PLANNING")
    status = status.upper()
    if status not in {"UNDER_REVIEW", "APPROVED", "ACTIVE", "COMPLETED", "CANCELLED"}:
        raise ValueError("FPO_PROCUREMENT_STATUS_INVALID")
    if status == "APPROVED" and not conn.execute(text("SELECT 1 FROM public.fpo_procurement_plan_items WHERE procurement_plan_id=:id AND fpo_id=:fpo"), {"id": str(plan_id), "fpo": str(c["fpo_id"])}).scalar_one_or_none():
        raise ValueError("FPO_PROCUREMENT_ITEMS_REQUIRED")
    row = conn.execute(text("""
        UPDATE public.fpo_procurement_plans SET status=:status,
          approved_at=CASE WHEN :status='APPROVED' THEN now() ELSE approved_at END,
          approved_by_user_id=CASE WHEN :status='APPROVED' THEN :user ELSE approved_by_user_id END,
          locked_at=CASE WHEN :status IN ('APPROVED','ACTIVE') THEN now() ELSE locked_at END,
          updated_at=now(),version_no=version_no+1
        WHERE procurement_plan_id=:id AND fpo_id=:fpo RETURNING *
    """), {"status": status, "user": str(user_id), "id": str(plan_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not row: raise ValueError("FPO_PROCUREMENT_PLAN_NOT_FOUND")
    _audit(conn, str(c["fpo_id"]), user_id, "PROCUREMENT_PLAN_STATUS_CHANGED", "procurement_plan", str(plan_id), reason)
    return dict(row)


def lots(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "PRODUCE_AGGREGATION_LOTS")
    return [dict(row) for row in conn.execute(text("SELECT * FROM public.fpo_aggregation_lots WHERE fpo_id=:fpo ORDER BY updated_at DESC"), {"fpo": str(c["fpo_id"])}).mappings()]


def create_lot(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "PRODUCE_AGGREGATION_LOTS")
    row = conn.execute(text("""
        INSERT INTO public.fpo_aggregation_lots
          (fpo_id,lot_code,procurement_plan_id,commodity_code,variety_code,crop_year,season_code,quantity_unit,traceability_code,created_by_user_id)
        VALUES (:fpo,:code,:plan,:commodity,:variety,:year,:season,:unit,:traceability,:user) RETURNING *
    """), {"fpo": str(c["fpo_id"]), "code": payload["lot_code"].strip().upper(), "plan": str(payload["procurement_plan_id"]) if payload.get("procurement_plan_id") else None, "commodity": payload["commodity_code"].strip().upper(), "variety": payload.get("variety_code"), "year": payload["crop_year"], "season": payload.get("season_code"), "unit": payload["quantity_unit"], "traceability": f"MT-{str(c['fpo_id'])[:8]}-{payload['lot_code'].strip().upper()}" , "user": str(user_id)}).mappings().one()
    _audit(conn, str(c["fpo_id"]), user_id, "LOT_CREATED", "aggregation_lot", str(row["lot_id"]))
    return dict(row)


def lot_sources(conn: Connection, user_id: UUID | str, lot_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "END_TO_END_TRACEABILITY")
    return [dict(row) for row in conn.execute(text("SELECT lot_source_id,lot_id,source_sequence,farmer_id,farm_id,crop_cycle_id,relationship_id,source_receipt_code,delivered_at,gross_quantity,accepted_quantity,rejected_quantity,quantity_unit,source_grade_code,status FROM public.fpo_lot_sources WHERE lot_id=:lot AND fpo_id=:fpo ORDER BY source_sequence"), {"lot": str(lot_id), "fpo": str(c["fpo_id"])}).mappings()]


def add_lot_source(conn: Connection, user_id: UUID | str, lot_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "PRODUCE_AGGREGATION_LOTS")
    lot = conn.execute(text("SELECT * FROM public.fpo_aggregation_lots WHERE lot_id=:lot AND fpo_id=:fpo FOR UPDATE"), {"lot": str(lot_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not lot or lot["status"] in {"SEALED", "CLOSED", "RECALLED"}: raise ValueError("FPO_LOT_NOT_RECEIVING")
    relationship = conn.execute(text("SELECT relationship_id FROM public.fpo_farmer_relationships WHERE relationship_id=:rel AND fpo_id=:fpo AND farmer_id=:farmer AND status='ACTIVE'"), {"rel": str(payload["relationship_id"]), "fpo": str(c["fpo_id"]), "farmer": str(payload["farmer_id"])}).scalar_one_or_none()
    if not relationship: raise ValueError("FPO_ACTIVE_RELATIONSHIP_REQUIRED")
    consent = conn.execute(text("SELECT consent_id FROM public.fpo_farmer_relationship_consents WHERE consent_id=:consent AND relationship_id=:rel AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at>now()) AND 'COMMERCIAL_PARTICIPATION'=ANY(scopes)"), {"consent": str(payload["consent_id"]), "rel": str(relationship)}).scalar_one_or_none()
    if not consent: raise ValueError("FPO_COMMERCIAL_CONSENT_REQUIRED")
    sequence = int(conn.execute(text("SELECT COALESCE(MAX(source_sequence),0)+1 FROM public.fpo_lot_sources WHERE lot_id=:lot"), {"lot": str(lot_id)}).scalar_one())
    row = conn.execute(text("""
      INSERT INTO public.fpo_lot_sources
        (fpo_id,lot_id,source_sequence,farmer_id,farm_id,crop_cycle_id,relationship_id,consent_id,source_receipt_code,gross_quantity,deduction_quantity,accepted_quantity,rejected_quantity,quantity_unit,declared_harvest_date,collection_point_code,source_grade_code,source_price,currency_code,source_snapshot,created_by_user_id)
      VALUES (:fpo,:lot,:sequence,:farmer,:farm,:cycle,:rel,:consent,:receipt,:gross,:deduction,:accepted,:rejected,:unit,:harvest,:collection,:grade,:price,:currency,CAST(:snapshot AS jsonb),:user) RETURNING *
    """), {"fpo": str(c["fpo_id"]), "lot": str(lot_id), "sequence": sequence, "farmer": str(payload["farmer_id"]), "farm": str(payload["farm_id"]), "cycle": str(payload["crop_cycle_id"]) if payload.get("crop_cycle_id") else None, "rel": str(relationship), "consent": str(consent), "receipt": payload["source_receipt_code"].strip(), "gross": payload["gross_quantity"], "deduction": payload.get("deduction_quantity", 0), "accepted": payload["accepted_quantity"], "rejected": payload.get("rejected_quantity", 0), "unit": payload["quantity_unit"], "harvest": payload.get("declared_harvest_date"), "collection": payload.get("collection_point_code"), "grade": payload.get("source_grade_code"), "price": payload.get("source_price"), "currency": payload.get("currency_code"), "snapshot": json.dumps(payload.get("source_snapshot") or {}), "user": str(user_id)}).mappings().one()
    conn.execute(text("UPDATE public.fpo_aggregation_lots SET received_quantity=received_quantity+:gross,accepted_quantity=accepted_quantity+:accepted,rejected_quantity=rejected_quantity+:rejected,available_quantity=available_quantity+:accepted,status='RECEIVING',updated_at=now(),version_no=version_no+1 WHERE lot_id=:lot"), {"gross": payload["gross_quantity"], "accepted": payload["accepted_quantity"], "rejected": payload.get("rejected_quantity", 0), "lot": str(lot_id)})
    previous = conn.execute(text("SELECT event_hash FROM public.fpo_lot_events WHERE lot_id=:lot ORDER BY event_sequence DESC LIMIT 1"), {"lot": str(lot_id)}).scalar_one_or_none()
    sequence_hash = int(conn.execute(text("SELECT COALESCE(MAX(event_sequence),0)+1 FROM public.fpo_lot_events WHERE lot_id=:lot"), {"lot": str(lot_id)}).scalar_one())
    event_payload = {"lot_id": str(lot_id), "sequence": sequence_hash, "type": "SOURCE_ADDED", "receipt": payload["source_receipt_code"], "accepted": payload["accepted_quantity"], "previous": previous}
    event_hash = hashlib.sha256(json.dumps(event_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    conn.execute(text("INSERT INTO public.fpo_lot_events (fpo_id,lot_id,event_sequence,event_type,actor_type,actor_id,quantity_delta,unit_code,metadata,previous_event_hash,event_hash) VALUES (:fpo,:lot,:sequence,'SOURCE_ADDED','USER',:user,:quantity,:unit,CAST(:metadata AS jsonb),:previous,:hash)"), {"fpo": str(c["fpo_id"]), "lot": str(lot_id), "sequence": sequence_hash, "user": str(user_id), "quantity": payload["accepted_quantity"], "unit": payload["quantity_unit"], "metadata": json.dumps({"source_receipt_code": payload["source_receipt_code"]}), "previous": previous, "hash": event_hash})
    return dict(row)


def seal_lot(conn: Connection, user_id: UUID | str, lot_id: UUID | str) -> dict[str, Any]:
    c = _ctx(conn, user_id, "END_TO_END_TRACEABILITY")
    row = conn.execute(text("UPDATE public.fpo_aggregation_lots SET status='SEALED',sealed_at=now(),updated_at=now(),version_no=version_no+1 WHERE lot_id=:lot AND fpo_id=:fpo AND status IN ('OPEN','RECEIVING') AND accepted_quantity > 0 RETURNING *"), {"lot": str(lot_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not row: raise ValueError("FPO_LOT_NOT_SEALABLE")
    previous = conn.execute(text("SELECT event_hash FROM public.fpo_lot_events WHERE lot_id=:lot ORDER BY event_sequence DESC LIMIT 1"), {"lot": str(lot_id)}).scalar_one_or_none(); sequence = int(conn.execute(text("SELECT COALESCE(MAX(event_sequence),0)+1 FROM public.fpo_lot_events WHERE lot_id=:lot"), {"lot": str(lot_id)}).scalar_one())
    payload = {"lot_id": str(lot_id), "sequence": sequence, "type": "LOT_SEALED", "previous": previous}; event_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    conn.execute(text("INSERT INTO public.fpo_lot_events (fpo_id,lot_id,event_sequence,event_type,actor_type,actor_id,metadata,previous_event_hash,event_hash) VALUES (:fpo,:lot,:sequence,'LOT_SEALED','USER',:user,'{}'::jsonb,:previous,:hash)"), {"fpo": str(c["fpo_id"]), "lot": str(lot_id), "sequence": sequence, "user": str(user_id), "previous": previous, "hash": event_hash})
    _audit(conn, str(c["fpo_id"]), user_id, "LOT_SEALED", "aggregation_lot", str(lot_id), "Sealing is irreversible for source mutations")
    return dict(row)


def quality_inspections(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "QUALITY_GRADING")
    return [dict(row) for row in conn.execute(text("SELECT i.*,l.lot_code,l.commodity_code FROM public.fpo_quality_inspections i JOIN public.fpo_aggregation_lots l ON l.lot_id=i.lot_id WHERE i.fpo_id=:fpo ORDER BY i.created_at DESC"), {"fpo": str(c["fpo_id"])}).mappings()]


def create_quality_inspection(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "QUALITY_GRADING")
    valid = conn.execute(text("SELECT 1 FROM public.fpo_aggregation_lots WHERE lot_id=:lot AND fpo_id=:fpo AND status IN ('SEALED','QUALITY_HOLD','AVAILABLE')"), {"lot": str(payload["lot_id"]), "fpo": str(c["fpo_id"])}).scalar_one_or_none()
    if not valid: raise ValueError("FPO_LOT_NOT_READY_FOR_QUALITY")
    schema = conn.execute(text("SELECT quality_schema_id FROM public.fpo_quality_grading_schemas WHERE quality_schema_id=:schema AND status='PUBLISHED'"), {"schema": str(payload["quality_schema_id"])}).scalar_one_or_none()
    if not schema: raise ValueError("FPO_QUALITY_SCHEMA_NOT_PUBLISHED")
    inspection_code = f"INS-{str(payload['lot_id'])[:8]}-{int(conn.execute(text('SELECT COALESCE(COUNT(*),0)+1 FROM public.fpo_quality_inspections WHERE fpo_id=:fpo'), {'fpo': str(c['fpo_id'])}).scalar_one())}"
    row = conn.execute(text("INSERT INTO public.fpo_quality_inspections (fpo_id,lot_id,quality_schema_id,inspection_code,status,measured_values,inspected_by_user_id,inspected_at) VALUES (:fpo,:lot,:schema,:code,'SAMPLED',CAST(:values AS jsonb),:user,now()) RETURNING *"), {"fpo": str(c["fpo_id"]), "lot": str(payload["lot_id"]), "schema": str(schema), "code": inspection_code, "values": json.dumps(payload.get("measured_values") or {}), "user": str(user_id)}).mappings().one()
    conn.execute(text("UPDATE public.fpo_aggregation_lots SET status='QUALITY_HOLD',updated_at=now(),version_no=version_no+1 WHERE lot_id=:lot"), {"lot": str(payload["lot_id"])})
    return dict(row)


def review_quality_inspection(conn: Connection, user_id: UUID | str, inspection_id: UUID | str, disposition: str, grade: str | None, note: str | None) -> dict[str, Any]:
    c = _ctx(conn, user_id, "QUALITY_GRADING"); disposition = disposition.upper()
    if disposition not in {"PASS", "HOLD", "REJECT"}: raise ValueError("FPO_QUALITY_DISPOSITION_INVALID")
    row = conn.execute(text("UPDATE public.fpo_quality_inspections SET status='REVIEWED',disposition=:disposition,resulting_grade_code=:grade,calculated_grade_code=:grade,reviewed_by_user_id=:user,reviewed_at=now(),reviewer_note=:note,updated_at=now(),version_no=version_no+1 WHERE inspection_id=:id AND fpo_id=:fpo AND status IN ('SAMPLED','IN_PROGRESS','COMPLETED') RETURNING *"), {"disposition": disposition, "grade": grade, "user": str(user_id), "note": note, "id": str(inspection_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not row: raise ValueError("FPO_QUALITY_INSPECTION_NOT_FOUND")
    lot_status = "AVAILABLE" if disposition == "PASS" else "QUALITY_HOLD"
    conn.execute(text("UPDATE public.fpo_aggregation_lots SET status=:status,updated_at=now(),version_no=version_no+1 WHERE lot_id=:lot"), {"status": lot_status, "lot": str(row["lot_id"])})
    _audit(conn, str(c["fpo_id"]), user_id, "QUALITY_INSPECTION_REVIEWED", "quality_inspection", str(inspection_id), note)
    return dict(row)


def warehouses(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "WAREHOUSE_INVENTORY")
    return [dict(row) for row in conn.execute(text("SELECT * FROM public.fpo_warehouses WHERE fpo_id=:fpo ORDER BY name"), {"fpo": str(c["fpo_id"])}).mappings()]


def create_warehouse(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "WAREHOUSE_INVENTORY")
    row = conn.execute(text("INSERT INTO public.fpo_warehouses (fpo_id,warehouse_code,name,address_text,capacity_quantity,quantity_unit,created_by_user_id) VALUES (:fpo,:code,:name,:address,:capacity,:unit,:user) RETURNING *"), {"fpo": str(c["fpo_id"]), "code": payload["warehouse_code"].strip().upper(), "name": payload["name"].strip(), "address": payload.get("address_text"), "capacity": payload.get("capacity_quantity"), "unit": payload.get("quantity_unit"), "user": str(user_id)}).mappings().one()
    _audit(conn, str(c["fpo_id"]), user_id, "WAREHOUSE_CREATED", "warehouse", str(row["warehouse_id"]))
    return dict(row)


def inventory_lots(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "WAREHOUSE_INVENTORY")
    return [dict(row) for row in conn.execute(text("SELECT i.*,l.lot_code,w.name AS warehouse_name FROM public.fpo_inventory_lots i JOIN public.fpo_aggregation_lots l ON l.lot_id=i.lot_id JOIN public.fpo_warehouses w ON w.warehouse_id=i.warehouse_id WHERE i.fpo_id=:fpo ORDER BY i.updated_at DESC"), {"fpo": str(c["fpo_id"])}).mappings()]


def create_inventory_lot(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "WAREHOUSE_INVENTORY")
    source = conn.execute(text("SELECT lot_id,commodity_code,accepted_quantity,available_quantity,quantity_unit,status FROM public.fpo_aggregation_lots WHERE lot_id=:lot AND fpo_id=:fpo"), {"lot": str(payload["lot_id"]), "fpo": str(c["fpo_id"])}).mappings().first()
    if not source or source["status"] not in {"AVAILABLE", "SEALED"}: raise ValueError("FPO_LOT_NOT_AVAILABLE_FOR_INVENTORY")
    warehouse = conn.execute(text("SELECT warehouse_id FROM public.fpo_warehouses WHERE warehouse_id=:warehouse AND fpo_id=:fpo AND status='ACTIVE'"), {"warehouse": str(payload["warehouse_id"]), "fpo": str(c["fpo_id"])}).scalar_one_or_none()
    if not warehouse: raise ValueError("FPO_WAREHOUSE_NOT_FOUND")
    row = conn.execute(text("""
      INSERT INTO public.fpo_inventory_lots (fpo_id,lot_id,warehouse_id,location_code,grade_code,received_quantity,on_hand_quantity,quantity_unit)
      VALUES (:fpo,:lot,:warehouse,:location,:grade,:quantity,:quantity,:unit) RETURNING *
    """), {"fpo": str(c["fpo_id"]), "lot": str(payload["lot_id"]), "warehouse": str(warehouse), "location": payload.get("location_code"), "grade": payload.get("grade_code"), "quantity": source["available_quantity"], "unit": source["quantity_unit"]}).mappings().one()
    _audit(conn, str(c["fpo_id"]), user_id, "INVENTORY_LOT_CREATED", "inventory_lot", str(row["inventory_lot_id"]))
    return dict(row)


def post_inventory_entry(conn: Connection, user_id: UUID | str, inventory_lot_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "WAREHOUSE_INVENTORY"); entry_type = payload["entry_type"].upper(); quantity = float(payload["quantity"])
    if entry_type not in {"RECEIPT", "TRANSFER_IN", "TRANSFER_OUT", "DISPATCH", "ADJUSTMENT", "LOSS", "REVERSAL"} or quantity <= 0: raise ValueError("FPO_INVENTORY_ENTRY_INVALID")
    lot = conn.execute(text("SELECT * FROM public.fpo_inventory_lots WHERE inventory_lot_id=:id AND fpo_id=:fpo FOR UPDATE"), {"id": str(inventory_lot_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not lot: raise ValueError("FPO_INVENTORY_LOT_NOT_FOUND")
    delta = quantity if entry_type in {"RECEIPT", "TRANSFER_IN"} else -quantity
    if float(lot["on_hand_quantity"]) + delta < float(lot["reserved_quantity"]) + float(lot["quarantine_quantity"]): raise ValueError("FPO_INVENTORY_NEGATIVE_AVAILABLE")
    seq = int(conn.execute(text("SELECT COALESCE(MAX(entry_sequence),0)+1 FROM public.fpo_inventory_ledger WHERE inventory_lot_id=:id"), {"id": str(inventory_lot_id)}).scalar_one())
    row = conn.execute(text("INSERT INTO public.fpo_inventory_ledger (fpo_id,inventory_lot_id,entry_sequence,entry_type,quantity_delta,quantity_unit,reference_code,reason,actor_user_id) VALUES (:fpo,:lot,:sequence,:type,:delta,:unit,:reference,:reason,:user) RETURNING *"), {"fpo": str(c["fpo_id"]), "lot": str(inventory_lot_id), "sequence": seq, "type": entry_type, "delta": delta, "unit": payload.get("quantity_unit") or lot["quantity_unit"], "reference": payload["reference_code"], "reason": payload.get("reason"), "user": str(user_id)}).mappings().one()
    conn.execute(text("UPDATE public.fpo_inventory_lots SET on_hand_quantity=on_hand_quantity+:delta,status=CASE WHEN on_hand_quantity+:delta=0 THEN 'DEPLETED' ELSE status END,updated_at=now() WHERE inventory_lot_id=:id"), {"delta": delta, "id": str(inventory_lot_id)})
    _audit(conn, str(c["fpo_id"]), user_id, "INVENTORY_LEDGER_POSTED", "inventory_lot", str(inventory_lot_id), payload.get("reason"))
    return dict(row)


def reconcile_inventory(conn: Connection, user_id: UUID | str) -> dict[str, Any]:
    c = _ctx(conn, user_id, "WAREHOUSE_INVENTORY")
    rows = conn.execute(text("""
      SELECT i.inventory_lot_id,i.on_hand_quantity,COALESCE(SUM(l.quantity_delta),0) AS ledger_balance
      FROM public.fpo_inventory_lots i LEFT JOIN public.fpo_inventory_ledger l ON l.inventory_lot_id=i.inventory_lot_id
      WHERE i.fpo_id=:fpo GROUP BY i.inventory_lot_id,i.on_hand_quantity
    """), {"fpo": str(c["fpo_id"])}).mappings().all()
    differences = [{"inventory_lot_id": str(row["inventory_lot_id"]), "projection": float(row["on_hand_quantity"]), "ledger": float(row["ledger_balance"])} for row in rows if abs(float(row["on_hand_quantity"]) - float(row["ledger_balance"])) > 0.0001]
    status = "PASSED" if not differences else "FAILED"
    run = conn.execute(text("INSERT INTO public.fpo_inventory_reconciliation_runs (fpo_id,status,checked_lot_count,difference_count,details,completed_at) VALUES (:fpo,:status,:count,:differences,CAST(:details AS jsonb),now()) RETURNING *"), {"fpo": str(c["fpo_id"]), "status": status, "count": len(rows), "differences": len(differences), "details": json.dumps({"differences": differences})}).mappings().one()
    return dict(run)


def admin_quality_schemas(conn: Connection) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(text("SELECT * FROM public.fpo_quality_grading_schemas ORDER BY schema_key,version DESC" )).mappings()]


def admin_create_quality_schema(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    row = conn.execute(text("""
      INSERT INTO public.fpo_quality_grading_schemas (schema_key,version,name,commodity_code,jurisdiction_code,grade_definitions,parameter_definitions,created_by_user_id)
      VALUES (:key,:version,:name,:commodity,:jurisdiction,CAST(:grades AS jsonb),CAST(:parameters AS jsonb),:user) RETURNING *
    """), {"key": payload["schema_key"].strip().upper(), "version": payload.get("version", 1), "name": payload["name"].strip(), "commodity": payload["commodity_code"].strip().upper(), "jurisdiction": payload.get("jurisdiction_code"), "grades": json.dumps(payload.get("grade_definitions") or []), "parameters": json.dumps(payload.get("parameter_definitions") or []), "user": str(user_id)}).mappings().one()
    return dict(row)


def admin_publish_quality_schema(conn: Connection, user_id: UUID | str, schema_id: UUID | str) -> dict[str, Any]:
    row = conn.execute(text("UPDATE public.fpo_quality_grading_schemas SET status='PUBLISHED',published_by_user_id=:user,published_at=now(),updated_at=now() WHERE quality_schema_id=:id AND status='DRAFT' RETURNING *"), {"user": str(user_id), "id": str(schema_id)}).mappings().first()
    if not row: raise ValueError("FPO_QUALITY_SCHEMA_NOT_PUBLISHABLE")
    return dict(row)


def contracts(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "CONTRACT_AND_ORDER_MANAGEMENT")
    return [dict(row) for row in conn.execute(text("SELECT x.*,p.legal_name AS counterparty_name FROM public.fpo_commercial_contracts x JOIN public.fpo_counterparties p ON p.counterparty_id=x.counterparty_id WHERE x.fpo_id=:fpo ORDER BY x.updated_at DESC"), {"fpo": str(c["fpo_id"])}).mappings()]


def create_contract(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "CONTRACT_AND_ORDER_MANAGEMENT")
    counterparty = conn.execute(text("SELECT counterparty_id FROM public.fpo_counterparties WHERE counterparty_id=:id AND fpo_id=:fpo AND status='ACTIVE' AND due_diligence_status='APPROVED'"), {"id": str(payload["counterparty_id"]), "fpo": str(c["fpo_id"])}).scalar_one_or_none()
    if not counterparty: raise ValueError("FPO_COUNTERPARTY_DUE_DILIGENCE_REQUIRED")
    row = conn.execute(text("INSERT INTO public.fpo_commercial_contracts (fpo_id,contract_code,counterparty_id,opportunity_id,title,contract_type,effective_date,expiry_date,currency_code,value_amount,incoterm_code,payment_terms_code,delivery_terms,source_document_artifact_id,source_document_checksum,created_by_user_id) VALUES (:fpo,:code,:counterparty,:opportunity,:title,:type,:effective,:expiry,:currency,:value,:incoterm,:payment,:delivery,:artifact,:checksum,:user) RETURNING *"), {"fpo": str(c["fpo_id"]), "code": payload["contract_code"].strip().upper(), "counterparty": str(counterparty), "opportunity": str(payload["opportunity_id"]) if payload.get("opportunity_id") else None, "title": payload["title"].strip(), "type": payload["contract_type"].upper(), "effective": payload["effective_date"], "expiry": payload.get("expiry_date"), "currency": payload.get("currency_code", "INR").upper(), "value": payload.get("value_amount"), "incoterm": payload.get("incoterm_code"), "payment": payload.get("payment_terms_code"), "delivery": payload.get("delivery_terms"), "artifact": str(payload["source_document_artifact_id"]) if payload.get("source_document_artifact_id") else None, "checksum": payload.get("source_document_checksum"), "user": str(user_id)}).mappings().one()
    _audit(conn, str(c["fpo_id"]), user_id, "CONTRACT_CREATED", "commercial_contract", str(row["contract_id"]))
    return dict(row)


def activate_contract(conn: Connection, user_id: UUID | str, contract_id: UUID | str) -> dict[str, Any]:
    c = _ctx(conn, user_id, "CONTRACT_AND_ORDER_MANAGEMENT")
    row = conn.execute(text("""
      UPDATE public.fpo_commercial_contracts x SET status='ACTIVE',activated_at=now(),updated_at=now(),version_no=version_no+1
      WHERE x.contract_id=:id AND x.fpo_id=:fpo AND x.status IN ('DRAFT','UNDER_REVIEW')
        AND x.source_document_artifact_id IS NOT NULL AND x.source_document_checksum IS NOT NULL
        AND EXISTS (SELECT 1 FROM public.fpo_counterparties p WHERE p.counterparty_id=x.counterparty_id AND p.due_diligence_status='APPROVED') RETURNING x.*
    """), {"id": str(contract_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not row: raise ValueError("FPO_CONTRACT_NOT_ACTIVATABLE")
    _audit(conn, str(c["fpo_id"]), user_id, "CONTRACT_ACTIVATED", "commercial_contract", str(contract_id))
    return dict(row)


def orders(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "CONTRACT_AND_ORDER_MANAGEMENT")
    return [dict(row) for row in conn.execute(text("SELECT o.*,p.legal_name AS counterparty_name FROM public.fpo_orders o JOIN public.fpo_counterparties p ON p.counterparty_id=o.counterparty_id WHERE o.fpo_id=:fpo ORDER BY o.updated_at DESC"), {"fpo": str(c["fpo_id"])}).mappings()]


def create_order(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "CONTRACT_AND_ORDER_MANAGEMENT")
    valid = conn.execute(text("SELECT 1 FROM public.fpo_counterparties WHERE counterparty_id=:id AND fpo_id=:fpo AND status='ACTIVE'"), {"id": str(payload["counterparty_id"]), "fpo": str(c["fpo_id"])}).scalar_one_or_none()
    if not valid: raise ValueError("FPO_COUNTERPARTY_NOT_FOUND")
    lines = payload.get("lines") or []
    if not lines: raise ValueError("FPO_ORDER_LINES_REQUIRED")
    subtotal = sum(float(line["ordered_quantity"]) * float(line.get("unit_price", 0)) for line in lines)
    row = conn.execute(text("INSERT INTO public.fpo_orders (fpo_id,order_code,counterparty_id,contract_id,opportunity_id,buyer_purchase_order_ref,delivery_start_date,delivery_end_date,delivery_address_text,currency_code,subtotal_amount,total_amount,created_by_user_id) VALUES (:fpo,:code,:counterparty,:contract,:opportunity,:po,:start,:end,:address,:currency,:subtotal,:total,:user) RETURNING *"), {"fpo": str(c["fpo_id"]), "code": payload["order_code"].strip().upper(), "counterparty": str(payload["counterparty_id"]), "contract": str(payload["contract_id"]) if payload.get("contract_id") else None, "opportunity": str(payload["opportunity_id"]) if payload.get("opportunity_id") else None, "po": payload.get("buyer_purchase_order_ref"), "start": payload.get("delivery_start_date"), "end": payload.get("delivery_end_date"), "address": payload.get("delivery_address_text"), "currency": payload.get("currency_code", "INR").upper(), "subtotal": subtotal, "total": subtotal, "user": str(user_id)}).mappings().one()
    for index, line in enumerate(lines, 1):
        quantity = float(line["ordered_quantity"]); price = float(line.get("unit_price", 0)); conn.execute(text("INSERT INTO public.fpo_order_lines (fpo_id,order_id,line_number,commodity_code,variety_code,grade_code,ordered_quantity,quantity_unit,unit_price,line_total,status) VALUES (:fpo,:order,:number,:commodity,:variety,:grade,:quantity,:unit,:price,:total,'DRAFT')"), {"fpo": str(c["fpo_id"]), "order": str(row["order_id"]), "number": index, "commodity": line["commodity_code"].strip().upper(), "variety": line.get("variety_code"), "grade": line.get("grade_code"), "quantity": quantity, "unit": line["quantity_unit"], "price": price, "total": quantity * price})
    _audit(conn, str(c["fpo_id"]), user_id, "ORDER_CREATED", "order", str(row["order_id"]))
    return dict(row)


def confirm_order(conn: Connection, user_id: UUID | str, order_id: UUID | str) -> dict[str, Any]:
    c = _ctx(conn, user_id, "CONTRACT_AND_ORDER_MANAGEMENT")
    row = conn.execute(text("UPDATE public.fpo_orders SET status='CONFIRMED',confirmed_at=now(),updated_at=now(),version_no=version_no+1 WHERE order_id=:id AND fpo_id=:fpo AND status='DRAFT' RETURNING *"), {"id": str(order_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not row: raise ValueError("FPO_ORDER_NOT_CONFIRMABLE")
    _audit(conn, str(c["fpo_id"]), user_id, "ORDER_CONFIRMED", "order", str(order_id)); return dict(row)


def dispatches(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "LOGISTICS_COORDINATION")
    return [dict(row) for row in conn.execute(text("SELECT d.*,o.order_code,w.name AS warehouse_name FROM public.fpo_dispatches d JOIN public.fpo_orders o ON o.order_id=d.order_id JOIN public.fpo_warehouses w ON w.warehouse_id=d.warehouse_id WHERE d.fpo_id=:fpo ORDER BY d.updated_at DESC"), {"fpo": str(c["fpo_id"])}).mappings()]


def create_dispatch(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "LOGISTICS_COORDINATION")
    valid = conn.execute(text("SELECT 1 FROM public.fpo_orders WHERE order_id=:order AND fpo_id=:fpo AND status IN ('CONFIRMED','ALLOCATING','READY_TO_DISPATCH','PARTIALLY_DISPATCHED')"), {"order": str(payload["order_id"]), "fpo": str(c["fpo_id"])}).scalar_one_or_none()
    if not valid: raise ValueError("FPO_ORDER_NOT_DISPATCHABLE")
    warehouse = conn.execute(text("SELECT warehouse_id FROM public.fpo_warehouses WHERE warehouse_id=:warehouse AND fpo_id=:fpo AND status='ACTIVE'"), {"warehouse": str(payload["warehouse_id"]), "fpo": str(c["fpo_id"])}).scalar_one_or_none()
    if not warehouse: raise ValueError("FPO_WAREHOUSE_NOT_FOUND")
    row = conn.execute(text("INSERT INTO public.fpo_dispatches (fpo_id,dispatch_code,order_id,warehouse_id,logistics_counterparty_id,transport_document_ref,scheduled_departure_at,created_by_user_id) VALUES (:fpo,:code,:order,:warehouse,:logistics,:transport,:scheduled,:user) RETURNING *"), {"fpo": str(c["fpo_id"]), "code": payload["dispatch_code"].strip().upper(), "order": str(payload["order_id"]), "warehouse": str(warehouse), "logistics": str(payload["logistics_counterparty_id"]) if payload.get("logistics_counterparty_id") else None, "transport": payload.get("transport_document_ref"), "scheduled": payload.get("scheduled_departure_at"), "user": str(user_id)}).mappings().one()
    _audit(conn, str(c["fpo_id"]), user_id, "DISPATCH_CREATED", "dispatch", str(row["dispatch_id"])); return dict(row)


def add_dispatch_item(conn: Connection, user_id: UUID | str, dispatch_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "LOGISTICS_COORDINATION")
    dispatch = conn.execute(text("SELECT * FROM public.fpo_dispatches WHERE dispatch_id=:id AND fpo_id=:fpo AND status='DRAFT'"), {"id": str(dispatch_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not dispatch: raise ValueError("FPO_DISPATCH_NOT_EDITABLE")
    line = conn.execute(text("SELECT * FROM public.fpo_order_lines WHERE order_line_id=:line AND fpo_id=:fpo"), {"line": str(payload["order_line_id"]), "fpo": str(c["fpo_id"])}).mappings().first()
    lot = conn.execute(text("SELECT * FROM public.fpo_inventory_lots WHERE inventory_lot_id=:lot AND fpo_id=:fpo FOR UPDATE"), {"lot": str(payload["inventory_lot_id"]), "fpo": str(c["fpo_id"])}).mappings().first()
    if not line or not lot or float(payload["quantity"]) > float(lot["on_hand_quantity"]) - float(lot["reserved_quantity"]) - float(lot["quarantine_quantity"]): raise ValueError("FPO_DISPATCH_STOCK_INCOMPATIBLE")
    row = conn.execute(text("INSERT INTO public.fpo_dispatch_items (fpo_id,dispatch_id,order_line_id,inventory_lot_id,quantity,quantity_unit,package_count,package_type_code,traceability_code,status) VALUES (:fpo,:dispatch,:line,:lot,:quantity,:unit,:packages,:package_type,:traceability,'DRAFT') RETURNING *"), {"fpo": str(c["fpo_id"]), "dispatch": str(dispatch_id), "line": str(payload["order_line_id"]), "lot": str(payload["inventory_lot_id"]), "quantity": payload["quantity"], "unit": payload["quantity_unit"], "packages": payload.get("package_count"), "package_type": payload.get("package_type_code"), "traceability": payload["traceability_code"]}).mappings().one()
    conn.execute(text("UPDATE public.fpo_dispatches SET status='PACKING',updated_at=now(),version_no=version_no+1 WHERE dispatch_id=:id"), {"id": str(dispatch_id)}); return dict(row)


def depart_dispatch(conn: Connection, user_id: UUID | str, dispatch_id: UUID | str) -> dict[str, Any]:
    c = _ctx(conn, user_id, "LOGISTICS_COORDINATION")
    dispatch = conn.execute(text("SELECT * FROM public.fpo_dispatches WHERE dispatch_id=:id AND fpo_id=:fpo AND status IN ('PACKING','READY') FOR UPDATE"), {"id": str(dispatch_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not dispatch: raise ValueError("FPO_DISPATCH_NOT_READY")
    items = conn.execute(text("SELECT * FROM public.fpo_dispatch_items WHERE dispatch_id=:dispatch AND fpo_id=:fpo"), {"dispatch": str(dispatch_id), "fpo": str(c["fpo_id"])}).mappings().all()
    if not items: raise ValueError("FPO_DISPATCH_ITEMS_REQUIRED")
    for item in items:
        post_inventory_entry(conn, user_id, item["inventory_lot_id"], {"entry_type": "DISPATCH", "quantity": item["quantity"], "quantity_unit": item["quantity_unit"], "reference_code": f"DISPATCH-{dispatch['dispatch_code']}-{item['dispatch_item_id']}", "reason": "Dispatch departure"})
        conn.execute(text("UPDATE public.fpo_dispatch_items SET status='IN_TRANSIT' WHERE dispatch_item_id=:id"), {"id": str(item["dispatch_item_id"])})
        conn.execute(text("UPDATE public.fpo_order_lines SET dispatched_quantity=dispatched_quantity+:quantity,status='DISPATCHED' WHERE order_line_id=:line"), {"quantity": item["quantity"], "line": str(item["order_line_id"])})
    row = conn.execute(text("UPDATE public.fpo_dispatches SET status='IN_TRANSIT',departed_at=now(),updated_at=now(),version_no=version_no+1 WHERE dispatch_id=:id RETURNING *"), {"id": str(dispatch_id)}).mappings().one()
    _audit(conn, str(c["fpo_id"]), user_id, "DISPATCH_DEPARTED", "dispatch", str(dispatch_id)); return dict(row)


def compliance_documents(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "COMPLIANCE_AND_CERTIFICATIONS")
    return [dict(row) for row in conn.execute(text("SELECT * FROM public.fpo_compliance_documents WHERE fpo_id=:fpo ORDER BY expiry_date NULLS LAST,created_at DESC"), {"fpo": str(c["fpo_id"])}).mappings()]


def create_compliance_document(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "COMPLIANCE_AND_CERTIFICATIONS")
    row = conn.execute(text("INSERT INTO public.fpo_compliance_documents (fpo_id,document_type_code,issuing_authority,issued_date,expiry_date,country_code,artifact_id,checksum,created_by_user_id) VALUES (:fpo,:type,:authority,:issued,:expiry,:country,:artifact,:checksum,:user) RETURNING *"), {"fpo": str(c["fpo_id"]), "type": payload["document_type_code"].strip().upper(), "authority": payload.get("issuing_authority"), "issued": payload.get("issued_date"), "expiry": payload.get("expiry_date"), "country": payload.get("country_code", "IN").upper(), "artifact": str(payload["artifact_id"]) if payload.get("artifact_id") else None, "checksum": payload.get("checksum"), "user": str(user_id)}).mappings().one()
    _audit(conn, str(c["fpo_id"]), user_id, "COMPLIANCE_DOCUMENT_CREATED", "compliance_document", str(row["compliance_document_id"])); return dict(row)


def compliance_readiness(conn: Connection, user_id: UUID | str) -> dict[str, Any]:
    c = _ctx(conn, user_id, "COMPLIANCE_AND_CERTIFICATIONS")
    docs = conn.execute(text("SELECT document_type_code,review_status,expiry_date FROM public.fpo_compliance_documents WHERE fpo_id=:fpo AND status='ACTIVE'"), {"fpo": str(c["fpo_id"])}).mappings().all()
    return {"complete": sum(1 for d in docs if d["review_status"] == "APPROVED"), "under_review": sum(1 for d in docs if d["review_status"] == "UNDER_REVIEW"), "expired": sum(1 for d in docs if d["review_status"] == "EXPIRED"), "documents": [dict(d) for d in docs]}


def export_packs(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "EXPORT_DOCUMENT_PACKS")
    return [dict(row) for row in conn.execute(text("SELECT * FROM public.fpo_export_packs WHERE fpo_id=:fpo ORDER BY created_at DESC"), {"fpo": str(c["fpo_id"])}).mappings()]


def create_export_pack(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "EXPORT_DOCUMENT_PACKS")
    row = conn.execute(text("INSERT INTO public.fpo_export_packs (fpo_id,pack_code,destination_code,commodity_code,order_id,lot_id,template_key,requested_by_user_id) VALUES (:fpo,:code,:destination,:commodity,:order,:lot,:template,:user) RETURNING *"), {"fpo": str(c["fpo_id"]), "code": payload["pack_code"].strip().upper(), "destination": payload["destination_code"].strip().upper(), "commodity": payload["commodity_code"].strip().upper(), "order": str(payload["order_id"]) if payload.get("order_id") else None, "lot": str(payload["lot_id"]) if payload.get("lot_id") else None, "template": payload["template_key"], "user": str(user_id)}).mappings().one()
    _audit(conn, str(c["fpo_id"]), user_id, "EXPORT_PACK_REQUESTED", "export_pack", str(row["export_pack_id"])); return dict(row)


def data_pack_schemas(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    _ctx(conn, user_id, "FINANCE_INSURANCE_DATA_PACKS")
    return [dict(row) for row in conn.execute(text("SELECT * FROM public.fpo_data_pack_schemas WHERE status='PUBLISHED' ORDER BY name" )).mappings()]


def create_data_pack_request(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c = _ctx(conn, user_id, "FINANCE_INSURANCE_DATA_PACKS")
    schema = conn.execute(text("SELECT * FROM public.fpo_data_pack_schemas WHERE data_pack_schema_id=:schema AND status='PUBLISHED'"), {"schema": str(payload["schema_id"])}).mappings().first()
    if not schema: raise ValueError("FPO_DATA_PACK_SCHEMA_NOT_PUBLISHED")
    row = conn.execute(text("INSERT INTO public.fpo_data_pack_requests (fpo_id,schema_id,purpose_code,recipient_category,recipient_id,farmer_ids,requested_by_user_id) VALUES (:fpo,:schema,:purpose,:recipient,:recipient_id,CAST(:farmers AS jsonb),:user) RETURNING *"), {"fpo": str(c["fpo_id"]), "schema": str(payload["schema_id"]), "purpose": payload["purpose_code"], "recipient": payload["recipient_category"], "recipient_id": str(payload["recipient_id"]) if payload.get("recipient_id") else None, "farmers": json.dumps([str(x) for x in payload.get("farmer_ids", [])]), "user": str(user_id)}).mappings().one()
    return dict(row)


def validate_data_pack_request(conn: Connection, user_id: UUID | str, request_id: UUID | str) -> dict[str, Any]:
    c = _ctx(conn, user_id, "FINANCE_INSURANCE_DATA_PACKS")
    request = conn.execute(text("SELECT * FROM public.fpo_data_pack_requests WHERE request_id=:id AND fpo_id=:fpo FOR UPDATE"), {"id": str(request_id), "fpo": str(c["fpo_id"])}).mappings().first()
    if not request: raise ValueError("FPO_DATA_PACK_REQUEST_NOT_FOUND")
    farmer_ids = request["farmer_ids"] or []; valid = 0; invalid = []
    for farmer_id in farmer_ids:
        grant = conn.execute(text("SELECT 1 FROM public.fpo_data_sharing_grants g JOIN public.fpo_farmer_relationship_consents c ON c.consent_id=g.consent_id WHERE g.fpo_id=:fpo AND g.farmer_id=:farmer AND g.purpose_code=:purpose AND g.status='ACTIVE' AND g.revoked_at IS NULL AND (g.expires_at IS NULL OR g.expires_at>now()) AND c.revoked_at IS NULL"), {"fpo": str(c["fpo_id"]), "farmer": str(farmer_id), "purpose": request["purpose_code"]}).scalar_one_or_none()
        if grant: valid += 1
        else: invalid.append(str(farmer_id))
    result = {"eligible_count": valid, "excluded_farmer_ids": invalid, "validated_at": "now"}; status = "CONSENT_VALIDATED" if valid and not invalid else "DRAFT"
    row = conn.execute(text("UPDATE public.fpo_data_pack_requests SET status=:status,validation_result=CAST(:result AS jsonb),updated_at=now() WHERE request_id=:id RETURNING *"), {"status": status, "result": json.dumps(result), "id": str(request_id)}).mappings().one(); return dict(row)


def sustainability_metrics(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c = _ctx(conn, user_id, "SUSTAINABILITY_ANALYTICS")
    return [dict(row) for row in conn.execute(text("SELECT * FROM public.fpo_sustainability_metrics WHERE fpo_id=:fpo ORDER BY created_at DESC LIMIT 500"), {"fpo": str(c["fpo_id"])}).mappings()]
