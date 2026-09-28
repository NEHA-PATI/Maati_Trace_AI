from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection

from services.fpo_management_service.app.repository import get_fpo_access_context, require_fpo_feature


def _ctx(conn: Connection, user_id: UUID | str, feature: str) -> dict[str, Any]:
    get_fpo_access_context(conn, user_id=user_id); require_fpo_feature(conn, user_id=user_id, feature_key=feature); return dict(get_fpo_access_context(conn, user_id=user_id))


def input_plans(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c=_ctx(conn,user_id,"INPUT_REQUIREMENT_PLANNING"); return [dict(r) for r in conn.execute(text("SELECT * FROM public.fpo_input_demand_plans WHERE fpo_id=:fpo ORDER BY created_at DESC"),{"fpo":str(c["fpo_id"])}).mappings()]

def create_input_plan(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c=_ctx(conn,user_id,"INPUT_REQUIREMENT_PLANNING")
    if not conn.execute(text("SELECT 1 FROM public.fpo_season_plans WHERE season_plan_id=:season AND fpo_id=:fpo"),{"season":str(payload["season_plan_id"]),"fpo":str(c["fpo_id"])}).scalar_one_or_none(): raise ValueError("FPO_SEASON_PLAN_NOT_FOUND")
    return dict(conn.execute(text("INSERT INTO public.fpo_input_demand_plans (fpo_id,season_plan_id,name,created_by) VALUES (:fpo,:season,:name,:user) RETURNING *"),{"fpo":str(c["fpo_id"]),"season":str(payload["season_plan_id"]),"name":payload["name"].strip(),"user":str(user_id)}).mappings().one())

def calculate_input_plan(conn: Connection, user_id: UUID | str, plan_id: UUID | str) -> dict[str, Any]:
    c=_ctx(conn,user_id,"INPUT_REQUIREMENT_PLANNING"); plan=conn.execute(text("SELECT * FROM public.fpo_input_demand_plans WHERE input_plan_id=:id AND fpo_id=:fpo FOR UPDATE"),{"id":str(plan_id),"fpo":str(c["fpo_id"])}).mappings().first()
    if not plan: raise ValueError("FPO_INPUT_PLAN_NOT_FOUND")
    targets=conn.execute(text("SELECT * FROM public.fpo_season_crop_targets WHERE season_plan_id=:season"),{"season":str(plan["season_plan_id"])}).mappings().all(); conn.execute(text("DELETE FROM public.fpo_input_demand_items WHERE input_plan_id=:id"),{"id":str(plan_id)})
    for target in targets:
        area=float(target["target_area_acres"] or 0); conn.execute(text("INSERT INTO public.fpo_input_demand_items (input_plan_id,crop_code,input_category,input_code,input_name,farmer_count,area_acres,required_quantity,quantity_unit,calculation_basis,confidence) VALUES (:plan,:crop,'OTHER',:code,:name,:farmers,:area,:quantity,'acres',CAST(:basis AS jsonb),'MEDIUM')"),{"plan":str(plan_id),"crop":target["crop_code"],"code":f"AREA-{target['crop_code']}","name":f"Planned area for {target['crop_code']}","farmers":target["target_farmer_count"] or 0,"area":area,"quantity":area,"basis":json.dumps({"source":"season_target","target_area_acres":area})})
    row=conn.execute(text("UPDATE public.fpo_input_demand_plans SET status='CALCULATED',calculated_at=now(),updated_at=now(),version=version+1 WHERE input_plan_id=:id RETURNING *"),{"id":str(plan_id)}).mappings().one(); return dict(row)

def input_items(conn: Connection, user_id: UUID | str, plan_id: UUID | str) -> list[dict[str, Any]]:
    c=_ctx(conn,user_id,"INPUT_REQUIREMENT_PLANNING"); return [dict(r) for r in conn.execute(text("SELECT i.* FROM public.fpo_input_demand_items i JOIN public.fpo_input_demand_plans p ON p.input_plan_id=i.input_plan_id WHERE i.input_plan_id=:id AND p.fpo_id=:fpo ORDER BY i.crop_code,i.input_name"),{"id":str(plan_id),"fpo":str(c["fpo_id"])}).mappings()]

def forecasts(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c=_ctx(conn,user_id,"YIELD_FORECASTS_STANDARD"); return [dict(r) for r in conn.execute(text("SELECT * FROM public.fpo_yield_forecasts WHERE fpo_id=:fpo ORDER BY created_at DESC LIMIT 500"),{"fpo":str(c["fpo_id"])}).mappings()]

def run_forecast(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c=_ctx(conn,user_id,"YIELD_FORECASTS_STANDARD"); crop=payload.get("crop_code","PORTFOLIO"); through=conn.execute(text("SELECT data_through FROM public.fpo_portfolio_summary WHERE fpo_id=:fpo"),{"fpo":str(c["fpo_id"])}).scalar_one_or_none() or datetime.now(timezone.utc)
    quality="INSUFFICIENT_DATA"; explanation=["NO_VALIDATED_YIELD_OBSERVATIONS"]
    row=conn.execute(text("INSERT INTO public.fpo_yield_forecasts (fpo_id,season_plan_id,scope_type,crop_code,forecast_yield_value,forecast_yield_unit,model_key,model_version,input_data_through,quality_status,explanation_codes) VALUES (:fpo,:season,'PORTFOLIO',:crop,0,'unknown','maatitrace-yield-standard','v1',:through,:quality,:explanation) RETURNING *"),{"fpo":str(c["fpo_id"]),"season":str(payload["season_plan_id"]) if payload.get("season_plan_id") else None,"crop":crop,"through":through,"quality":quality,"explanation":explanation}).mappings().one(); return dict(row)

def report_catalogue(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    _ctx(conn,user_id,"ADVANCED_REPORTS"); return [{"report_type":k,"label":v,"formats":["CSV","XLSX","PDF"]} for k,v in {"FARMER_PORTFOLIO":"Farmer portfolio","FARM_AND_ACREAGE":"Farm and acreage","CROP_SEASON":"Crop and season portfolio","MONITORING_ALERTS":"Monitoring and alerts","ADVISORY_DELIVERY":"Advisory delivery","INPUT_REQUIREMENTS":"Input requirements","YIELD_FORECASTS":"Yield forecasts","DATA_QUALITY":"Data quality"}.items()]

def report_jobs(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c=_ctx(conn,user_id,"ADVANCED_REPORTS"); return [dict(r) for r in conn.execute(text("SELECT * FROM public.fpo_report_jobs WHERE fpo_id=:fpo ORDER BY requested_at DESC LIMIT 100"),{"fpo":str(c["fpo_id"])}).mappings()]

def create_report_job(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c=_ctx(conn,user_id,"DATA_EXPORT"); fmt=payload.get("format","CSV").upper(); report_type=payload["report_type"].upper()
    if fmt not in {"CSV","XLSX","PDF"}: raise ValueError("FPO_REPORT_FORMAT_INVALID")
    idem=payload.get("idempotency_key") or hashlib.sha256(f"{c['fpo_id']}:{report_type}:{fmt}:{json.dumps(payload.get('parameters') or {},sort_keys=True)}".encode()).hexdigest()
    return dict(conn.execute(text("INSERT INTO public.fpo_report_jobs (fpo_id,report_type,format,parameters,requested_by,idempotency_key) VALUES (:fpo,:type,:format,CAST(:parameters AS jsonb),:user,:idem) ON CONFLICT (fpo_id,idempotency_key) DO UPDATE SET requested_at=public.fpo_report_jobs.requested_at RETURNING *"),{"fpo":str(c["fpo_id"]),"type":report_type,"format":fmt,"parameters":json.dumps(payload.get("parameters") or {}),"user":str(user_id),"idem":idem}).mappings().one())
