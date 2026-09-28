from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from cryptography.fernet import Fernet
from sqlalchemy import text
from sqlalchemy.engine import Connection

from services.fpo_management_service.app.repository import get_fpo_access_context, require_fpo_feature


def _context(conn: Connection, user_id: UUID | str, feature: str) -> dict[str, Any]:
    get_fpo_access_context(conn, user_id=user_id)
    require_fpo_feature(conn, user_id=user_id, feature_key=feature)
    return dict(get_fpo_access_context(conn, user_id=user_id))


def _relationship(conn: Connection, *, fpo_id: str, farmer_id: str) -> dict[str, Any]:
    row = conn.execute(text("""
        SELECT relationship_id, farmer_profile_id, status FROM public.fpo_farmer_relationships
        WHERE fpo_id=:fpo AND farmer_profile_id=:farmer AND status='ACTIVE' LIMIT 1
    """), {"fpo": fpo_id, "farmer": farmer_id}).mappings().first()
    if not row: raise ValueError("FPO_FARMER_RELATIONSHIP_REQUIRED")
    return dict(row)


def _key() -> bytes:
    raw = os.getenv("FPO_PRIVATE_NOTE_KEY", "").strip()
    if raw: return raw.encode()
    if os.getenv("APP_ENV", "local").strip().lower() in {"prod", "production"}:
        raise RuntimeError("FPO_PRIVATE_NOTE_KEY must be configured in production")
    secret = os.getenv("JWT_SECRET", "development-private-note-key").encode()
    return base64.urlsafe_b64encode(hashlib.sha256(secret).digest())


def _cipher(value: str) -> bytes: return Fernet(_key()).encrypt(value.encode("utf-8"))
def _plain(value: bytes) -> str: return Fernet(_key()).decrypt(bytes(value)).decode("utf-8")


def list_tags(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c=_context(conn,user_id,"FARMER_SEGMENTATION")
    return [dict(r) for r in conn.execute(text("SELECT tag_id,name,description,color_token,is_active,created_at,updated_at FROM public.fpo_farmer_tags WHERE fpo_id=:fpo AND is_active ORDER BY normalized_name"),{"fpo":str(c["fpo_id"])}).mappings()]

def create_tag(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c=_context(conn,user_id,"FARMER_SEGMENTATION"); name=payload["name"].strip(); normalized=" ".join(name.lower().split())
    row=conn.execute(text("INSERT INTO public.fpo_farmer_tags (fpo_id,name,normalized_name,description,color_token,created_by) VALUES (:fpo,:name,:normalized,:description,:color,:user) RETURNING tag_id,name,description,color_token,is_active,created_at"),{"fpo":str(c["fpo_id"]),"name":name,"normalized":normalized,"description":payload.get("description"),"color":payload.get("color_token","emerald"),"user":str(user_id)}).mappings().one()
    return dict(row)

def assign_tag(conn: Connection, user_id: UUID | str, farmer_id: UUID | str, tag_id: UUID | str) -> dict[str, Any]:
    c=_context(conn,user_id,"FARMER_SEGMENTATION"); rel=_relationship(conn,fpo_id=str(c["fpo_id"]),farmer_id=str(farmer_id))
    row=conn.execute(text("INSERT INTO public.fpo_farmer_tag_assignments (fpo_id,tag_id,farmer_id,relationship_id,assigned_by) VALUES (:fpo,:tag,:farmer,:rel,:user) ON CONFLICT (tag_id,farmer_id) DO UPDATE SET removed_at=NULL,removed_by=NULL RETURNING tag_assignment_id,tag_id,farmer_id,relationship_id,assigned_at"),{"fpo":str(c["fpo_id"]),"tag":str(tag_id),"farmer":str(farmer_id),"rel":str(rel["relationship_id"]),"user":str(user_id)}).mappings().one(); return dict(row)

def create_segment(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c=_context(conn,user_id,"FARMER_SEGMENTATION"); criteria=payload.get("criteria") or {}
    allowed={"crop_code","district_code","block_code","village_name","condition_status","min_area_acres","max_area_acres"}
    if set(criteria)-allowed: raise ValueError("Unsupported segment criteria")
    row=conn.execute(text("INSERT INTO public.fpo_farmer_segments (fpo_id,name,description,segment_type,criteria,created_by) VALUES (:fpo,:name,:description,:type,CAST(:criteria AS jsonb),:user) RETURNING *"),{"fpo":str(c["fpo_id"]),"name":payload["name"].strip(),"description":payload.get("description"),"type":payload.get("segment_type","DYNAMIC"),"criteria":json.dumps(criteria),"user":str(user_id)}).mappings().one(); return dict(row)

def _segment_rows(conn: Connection, fpo_id: str, criteria: dict[str, Any]) -> list[dict[str, Any]]:
    where=["p.fpo_id=:fpo","p.relationship_status='ACTIVE'"]; params={"fpo":fpo_id}
    for key,column in [("district_code","p.district_code"),("block_code","p.block_code"),("village_name","p.village_name"),("condition_status","p.condition_status")]:
        if criteria.get(key) is not None: where.append(f"{column}=:{key}"); params[key]=criteria[key]
    if criteria.get("crop_code"): where.append(":crop = ANY(p.active_crop_codes)"); params["crop"]=criteria["crop_code"]
    if criteria.get("min_area_acres") is not None: where.append("p.area_acres >= :min_area"); params["min_area"]=criteria["min_area_acres"]
    if criteria.get("max_area_acres") is not None: where.append("p.area_acres <= :max_area"); params["max_area"]=criteria["max_area_acres"]
    return [dict(r) for r in conn.execute(text(f"SELECT p.farmer_id,p.farm_count,p.area_acres FROM public.fpo_farmer_portfolio p WHERE {' AND '.join(where)}"),params).mappings()]

def evaluate_segment(conn: Connection, user_id: UUID | str, segment_id: UUID | str) -> dict[str, Any]:
    c=_context(conn,user_id,"FARMER_SEGMENTATION"); segment=conn.execute(text("SELECT * FROM public.fpo_farmer_segments WHERE segment_id=:id AND fpo_id=:fpo AND status='ACTIVE' FOR UPDATE"),{"id":str(segment_id),"fpo":str(c["fpo_id"])}).mappings().first()
    if not segment: raise ValueError("FPO_SEGMENT_NOT_FOUND")
    members=_segment_rows(conn,str(c["fpo_id"]),segment["criteria"] or {})
    conn.execute(text("DELETE FROM public.fpo_farmer_segment_members WHERE segment_id=:id"),{"id":str(segment_id)})
    for member in members:
        rel=_relationship(conn,fpo_id=str(c["fpo_id"]),farmer_id=str(member["farmer_id"]))
        conn.execute(text("INSERT INTO public.fpo_farmer_segment_members (segment_id,farmer_id,relationship_id,membership_source) VALUES (:segment,:farmer,:rel,'RULE')"),{"segment":str(segment_id),"farmer":str(member["farmer_id"]),"rel":str(rel["relationship_id"])})
    row=conn.execute(text("UPDATE public.fpo_farmer_segments SET member_count=:count,last_evaluated_at=now(),updated_at=now(),version=version+1 WHERE segment_id=:id RETURNING segment_id,name,member_count,last_evaluated_at,version"),{"id":str(segment_id),"count":len(members)}).mappings().one(); return dict(row)

def list_segments(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c=_context(conn,user_id,"FARMER_SEGMENTATION"); return [dict(r) for r in conn.execute(text("SELECT segment_id,name,description,segment_type,criteria,status,last_evaluated_at,member_count,version,created_at,updated_at FROM public.fpo_farmer_segments WHERE fpo_id=:fpo ORDER BY updated_at DESC"),{"fpo":str(c["fpo_id"])}).mappings()]

def segment_members(conn: Connection, user_id: UUID | str, segment_id: UUID | str) -> list[dict[str, Any]]:
    c=_context(conn,user_id,"FARMER_SEGMENTATION"); return [dict(r) for r in conn.execute(text("SELECT m.farmer_id,m.relationship_id,p.farmer_name,p.phone_masked,p.district_name,p.village_name FROM public.fpo_farmer_segment_members m JOIN public.fpo_farmer_portfolio p ON p.fpo_id=:fpo AND p.farmer_id=m.farmer_id WHERE m.segment_id=:segment AND m.relationship_id IN (SELECT relationship_id FROM public.fpo_farmer_relationships WHERE fpo_id=:fpo AND status='ACTIVE') ORDER BY p.farmer_name"),{"fpo":str(c["fpo_id"]),"segment":str(segment_id)}).mappings()]

def notes(conn: Connection, user_id: UUID | str, farmer_id: UUID | str) -> list[dict[str, Any]]:
    c=_context(conn,user_id,"FARMER_NOTES_AND_FOLLOWUPS"); rel=_relationship(conn,fpo_id=str(c["fpo_id"]),farmer_id=str(farmer_id)); rows=conn.execute(text("SELECT * FROM public.fpo_farmer_notes WHERE fpo_id=:fpo AND farmer_id=:farmer ORDER BY updated_at DESC"),{"fpo":str(c["fpo_id"]),"farmer":str(farmer_id)}).mappings(); result=[]
    for r in rows:
        d=dict(r); d["content"]=_plain(d.pop("content_ciphertext")); result.append(d)
    return result

def create_note(conn: Connection, user_id: UUID | str, farmer_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c=_context(conn,user_id,"FARMER_NOTES_AND_FOLLOWUPS"); rel=_relationship(conn,fpo_id=str(c["fpo_id"]),farmer_id=str(farmer_id)); row=conn.execute(text("INSERT INTO public.fpo_farmer_notes (fpo_id,farmer_id,relationship_id,note_type,title,content_ciphertext,follow_up_at,created_by) VALUES (:fpo,:farmer,:rel,:type,:title,:content,:follow,:user) RETURNING note_id,note_type,title,follow_up_at,status,created_at"),{"fpo":str(c["fpo_id"]),"farmer":str(farmer_id),"rel":str(rel["relationship_id"]),"type":payload.get("note_type","GENERAL"),"title":payload["title"].strip(),"content":_cipher(payload["content"]),"follow":payload.get("follow_up_at"),"user":str(user_id)}).mappings().one(); return dict(row)

def season_plans(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c=_context(conn,user_id,"SEASON_PLANNING"); return [dict(r) for r in conn.execute(text("SELECT * FROM public.fpo_season_plans WHERE fpo_id=:fpo ORDER BY season_year DESC,season_start_date DESC"),{"fpo":str(c["fpo_id"])}).mappings()]

def create_season_plan(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c=_context(conn,user_id,"SEASON_PLANNING"); row=conn.execute(text("INSERT INTO public.fpo_season_plans (fpo_id,season_code,season_year,name,planning_start_date,season_start_date,season_end_date,geography_filter,notes,created_by) VALUES (:fpo,:code,:year,:name,:planning,:start,:end,CAST(:geo AS jsonb),:notes,:user) RETURNING *"),{"fpo":str(c["fpo_id"]),"code":payload["season_code"],"year":payload["season_year"],"name":payload["name"],"planning":payload["planning_start_date"],"start":payload["season_start_date"],"end":payload["season_end_date"],"geo":json.dumps(payload.get("geography_filter") or {}),"notes":payload.get("notes"),"user":str(user_id)}).mappings().one(); return dict(row)

def add_crop_target(conn: Connection, user_id: UUID | str, plan_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c=_context(conn,user_id,"SEASON_PLANNING"); exists=conn.execute(text("SELECT 1 FROM public.fpo_season_plans WHERE season_plan_id=:id AND fpo_id=:fpo AND status='DRAFT'"),{"id":str(plan_id),"fpo":str(c["fpo_id"])}).scalar_one_or_none()
    if not exists: raise ValueError("FPO_SEASON_PLAN_LOCKED")
    row=conn.execute(text("INSERT INTO public.fpo_season_crop_targets (season_plan_id,crop_code,variety_code,target_farmer_count,target_farm_count,target_area_acres,target_sowing_start,target_sowing_end,target_harvest_start,target_harvest_end,target_yield_value,target_yield_unit,input_assumptions) VALUES (:plan,:crop,:variety,:farmers,:farms,:area,:sow_start,:sow_end,:harvest_start,:harvest_end,:yield,:unit,CAST(:assumptions AS jsonb)) RETURNING *"),{"plan":str(plan_id),"crop":payload["crop_code"],"variety":payload.get("variety_code"),"farmers":payload.get("target_farmer_count"),"farms":payload.get("target_farm_count"),"area":payload.get("target_area_acres",0),"sow_start":payload.get("target_sowing_start"),"sow_end":payload.get("target_sowing_end"),"harvest_start":payload.get("target_harvest_start"),"harvest_end":payload.get("target_harvest_end"),"yield":payload.get("target_yield_value"),"unit":payload.get("target_yield_unit"),"assumptions":json.dumps(payload.get("input_assumptions") or {})}).mappings().one(); return dict(row)

def tasks(conn: Connection, user_id: UUID | str) -> list[dict[str, Any]]:
    c=_context(conn,user_id,"FIELD_ACTIVITY_PLANNING"); return [dict(r) for r in conn.execute(text("SELECT * FROM public.fpo_field_tasks WHERE fpo_id=:fpo ORDER BY CASE priority WHEN 'URGENT' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'NORMAL' THEN 3 ELSE 4 END,due_at NULLS LAST,created_at DESC"),{"fpo":str(c["fpo_id"])}).mappings()]

def create_task(conn: Connection, user_id: UUID | str, payload: dict[str, Any]) -> dict[str, Any]:
    c=_context(conn,user_id,"FIELD_ACTIVITY_PLANNING"); farmer=payload.get("farmer_id"); rel=_relationship(conn,fpo_id=str(c["fpo_id"]),farmer_id=str(farmer)) if farmer else None
    row=conn.execute(text("INSERT INTO public.fpo_field_tasks (fpo_id,task_type,title,description,priority,farmer_id,relationship_id,due_at,assigned_actor_id,created_by) VALUES (:fpo,:type,:title,:description,:priority,:farmer,:rel,:due,:user,:user) RETURNING *"),{"fpo":str(c["fpo_id"]),"type":payload.get("task_type","FOLLOW_UP"),"title":payload["title"].strip(),"description":payload.get("description"),"priority":payload.get("priority","NORMAL"),"farmer":str(farmer) if farmer else None,"rel":str(rel["relationship_id"]) if rel else None,"due":payload.get("due_at"),"user":str(user_id)}).mappings().one(); return dict(row)

def update_task(conn: Connection, user_id: UUID | str, task_id: UUID | str, status: str, note: str | None = None) -> dict[str, Any]:
    c=_context(conn,user_id,"FIELD_ACTIVITY_PLANNING"); row=conn.execute(text("SELECT * FROM public.fpo_field_tasks WHERE task_id=:id AND fpo_id=:fpo FOR UPDATE"),{"id":str(task_id),"fpo":str(c["fpo_id"])}).mappings().first()
    if not row: raise ValueError("FPO_TASK_NOT_FOUND")
    if status not in {"OPEN","IN_PROGRESS","COMPLETED","CANCELLED"}: raise ValueError("Unsupported task status")
    updated=conn.execute(text("UPDATE public.fpo_field_tasks SET status=:status,completion_note=:note,completed_at=CASE WHEN :status='COMPLETED' THEN now() ELSE completed_at END,updated_at=now(),version=version+1 WHERE task_id=:id RETURNING *"),{"id":str(task_id),"status":status,"note":note}).mappings().one()
    conn.execute(text("INSERT INTO public.fpo_field_task_events (task_id,event_type,status_from,status_to,actor_user_id,note) VALUES (:id,'STATUS_CHANGED',:old,:new,:user,:note)"),{"id":str(task_id),"old":row["status"],"new":status,"user":str(user_id),"note":note}); return dict(updated)
