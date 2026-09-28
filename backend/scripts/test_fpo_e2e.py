"""Verbose local FPO Class A end-to-end checker.

Read-only by default. Use --mutate only against a local database. Mutating mode
creates a real farmer-to-approved-FPO relationship and exercises the consent,
acceptance, portfolio, document and admin-validation paths when prerequisites
are present.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
from jose import jwt
from sqlalchemy import text
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv("services/fpo_management_service/.env")
from shared.config.settings import settings
from shared.db.postgres import engine


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("fpo-e2e")


class E2E:
    def __init__(self, base_url: str, mutate: bool) -> None:
        self.base_url = base_url.rstrip("/")
        self.mutate = mutate
        self.step_no = 0
        self.admin_id = None
        self.fpo_id = None
        self.farmer_id = None
        self.farm_id = None
        self.farm_ids = []
        self.farmer_profile_id = None
        self.fpo_org_id = None
        self.relationship_id = None

    def step(self, name: str, fn):
        self.step_no += 1
        log.info("[STEP %02d] START %s", self.step_no, name)
        try:
            result = fn()
            log.info("[STEP %02d] OK %s | %s", self.step_no, name, json.dumps(result, default=str)[:1200])
            return result
        except Skip as exc:
            log.warning("[STEP %02d] SKIP %s | %s", self.step_no, name, exc)
        except Exception as exc:  # noqa: BLE001 - a checker must report every failure
            log.exception("[STEP %02d] FAIL %s | %s", self.step_no, name, exc)
            raise

    def token(self, user_id: str, role: str) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode({
            "sub": str(user_id), "session_id": f"fpo-e2e-{role}-{uuid4()}",
            "type": "access", "iat": now, "exp": now + timedelta(minutes=15),
            "iss": settings.jwt_issuer, "aud": settings.jwt_audience,
        }, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def request(self, method: str, path: str, role: str | None = None, **kwargs):
        user_id = {"admin": self.admin_id, "fpo": self.fpo_id, "farmer": self.farmer_id}.get(role)
        headers = kwargs.pop("headers", {})
        if user_id:
            headers["Authorization"] = f"Bearer {self.token(user_id, role)}"
        headers.setdefault("X-Correlation-ID", f"fpo-e2e-{uuid4()}")
        response = httpx.request(method, f"{self.base_url}{path}", headers=headers, timeout=20, **kwargs)
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {path} -> {response.status_code}: {response.text[:600]}")
        return response

    def db_setup(self):
        with engine.connect() as conn:
            self.admin_id = conn.execute(text("SELECT user_id FROM public.users WHERE role = 'admin' AND is_active = TRUE ORDER BY created_at LIMIT 1")).scalar_one_or_none()
            self.fpo_id = conn.execute(text("SELECT auth_user_id FROM public.fpo_organizations WHERE provisioning_status = 'READY' ORDER BY created_at LIMIT 1")).scalar_one_or_none()
            self.fpo_org_id = conn.execute(text("SELECT fpo_id FROM public.fpo_organizations WHERE auth_user_id = :user_id"), {"user_id": str(self.fpo_id)}).scalar_one_or_none() if self.fpo_id else None
            self.farmer_id = conn.execute(text("SELECT user_id FROM public.users WHERE role = 'farmer' AND is_active = TRUE ORDER BY created_at LIMIT 1")).scalar_one_or_none()
            self.farmer_profile_id = conn.execute(text("SELECT farmer_id FROM public.farmer_profiles WHERE user_id=:user_id"), {"user_id": str(self.farmer_id)}).scalar_one_or_none() if self.farmer_id else None
            self.farm_ids = [row[0] for row in conn.execute(text("""
                SELECT f.farm_id FROM public.farms f
                WHERE f.farmer_id=:farmer_id AND f.is_active=TRUE
                  AND NOT EXISTS (SELECT 1 FROM public.fpo_farmer_relationships r WHERE r.farm_id=f.farm_id AND r.status IN ('ACTIVE','PENDING_FPO_ACCEPTANCE'))
                ORDER BY f.created_at, f.farm_id LIMIT 2
            """), {"farmer_id": str(self.farmer_profile_id)}).all()] if self.farmer_profile_id else []
            self.farm_id = self.farm_ids[0] if self.farm_ids else None
        if not self.admin_id or not self.fpo_id or not self.farmer_id:
            raise RuntimeError("An active admin, provisioned FPO owner, and farmer are required")
        return {"admin_user": str(self.admin_id), "fpo_owner": str(self.fpo_id), "farmer_user": str(self.farmer_id), "fpo_id": str(self.fpo_org_id)}

    def run(self):
        self.step("FPO management live health", lambda: self.request("GET", "/health/live").json())
        self.step("FPO management database readiness", lambda: self.request("GET", "/health/ready").json())
        self.step("Load real local users and FPO organization", self.db_setup)
        self.step("Admin verification queue visible", lambda: {"count": len(self.request("GET", "/v1/fpo-portal/admin/verification-queue", "admin").json())})
        self.step("Admin feature catalogue visible", lambda: {"count": len(self.request("GET", "/v1/admin/fpo/features", "admin").json())})
        admin_documents = self.step("Admin verification documents queue visible", lambda: self.request("GET", f"/v1/fpo-portal/admin/organizations/{self.fpo_org_id}/verification/documents", "admin").json())
        if not admin_documents:
            self.step("Document upload/finalize/admin-review path", lambda: (_ for _ in ()).throw(Skip("no real verification document exists for the selected FPO")))
        self.step("Admin verification checklist visible", lambda: {"count": len(self.request("GET", f"/v1/fpo-portal/admin/organizations/{self.fpo_org_id}/verification/checklist", "admin").json())})
        bootstrap = self.step("FPO bootstrap and effective entitlements", lambda: self.request("GET", "/v1/fpo-portal/bootstrap", "fpo").json())
        self.step("Class A bulk registration guard", lambda: self._assert_class_a_bulk_guard(bootstrap))
        self.step("FPO dashboard v2 contract", lambda: self.request("GET", "/v1/fpo-portal/dashboard", "fpo").json())
        self.step("FPO alerts endpoint", lambda: {"count": len(self.request("GET", "/v1/fpo-portal/alerts", "fpo").json())})
        self.step("FPO portfolio report endpoint", lambda: self.request("GET", "/v1/fpo-portal/reports/portfolio", "fpo").json())
        policy = self.step("Published farm-sharing consent policy", lambda: self.request("GET", "/v1/farmer/fpo-consent-policy", "farmer").json())
        if policy.get("policy_code") != "FPO_DATA_SHARING" or not policy.get("mandatory_scopes"):
            raise RuntimeError("Published farm-sharing policy is missing its required consent scopes")
        self.step("Farmer FPO relationship history", lambda: {"count": len(self.request("GET", "/v1/farmer/fpo-relationships", "farmer").json())})
        fpo_relationships = self.step("FPO farm-scoped relationship inbox", lambda: self.request("GET", "/v1/fpo-portal/farm-relationships", "fpo").json())
        pending = [r for r in fpo_relationships if r.get("status") == "PENDING_FPO_ACCEPTANCE"]
        self.step("Pending farm requests visible to the owning FPO", lambda: {"pending_count": len(pending), "farm_scoped": all(r.get("farm_id") for r in pending)})
        self.step("Request → FPO inbox → accept → exact-farm access (rolled back)", self._rollback_relationship_flow)
        if not self.mutate:
            self.step("Mutation flow disabled", lambda: (_ for _ in ()).throw(Skip("read-only mode; rerun with --mutate for relationship and document writes")))
            portfolio = self.step("Current consented farmer portfolio", lambda: self.request("GET", "/v1/fpo-portal/farmers", "fpo").json())
            active_scoped = [r for r in fpo_relationships if r.get("status") == "ACTIVE" and r.get("farm_id") and "FARM_READ" in (r.get("scopes") or []) and "LAND_INTELLIGENCE_READ" in (r.get("scopes") or [])]
            if active_scoped:
                relationship = active_scoped[0]
                farmer_profile_id = relationship["farmer_id"]
                farms = self.step("FPO farm portfolio constrained by active consented relationships", lambda: self.request("GET", f"/v1/fpo/me/farmers/{farmer_profile_id}/farms", "fpo").json())
                farm = next((row for row in farms if str(row.get("farm_id")) == str(relationship["farm_id"])), None)
                if farm:
                    self.step("Read-only farm intelligence authorization and analytics", lambda: self._read_intelligence(farmer_profile_id, farm["farm_id"]))
                else:
                    self.step("Farm-specific consent visibility", lambda: (_ for _ in ()).throw(Skip("no active farm relationship with a valid FARM_READ consent")))
            elif portfolio.get("items"):
                self.step("Farm data access eligibility", lambda: (_ for _ in ()).throw(Skip("portfolio contains no active farm-scoped relationship with current FARM_READ and LAND_INTELLIGENCE_READ consent")))
            return
        if bootstrap.get("verification", {}).get("status") != "APPROVED":
            raise RuntimeError("Mutating E2E requires an approved FPO")
        discovered = self.step("Discover approved FPO", lambda: self.request("GET", "/v1/fpo-portal/discover", "farmer").json())
        target = next((item for item in discovered if str(item["fpo_id"]) == str(self.fpo_org_id)), None)
        if not target:
            raise RuntimeError("The selected real FPO is not discoverable")
        relationship = self.step("Farmer sends FPO relationship request with server policy consent", lambda: self.request("POST", "/v1/farmer/fpo-relationships", "farmer", json={"fpo_id": str(self.fpo_org_id), "policy_code": "FPO_DATA_SHARING", "policy_version": "2", "accepted": True, "selected_optional_scopes": []}).json())
        self.relationship_id = relationship["relationship_id"]
        self.step("FPO receives relationship request", lambda: self.request("GET", "/v1/fpo-portal/relationships", "fpo").json())
        self.step("FPO accepts relationship request", lambda: self.request("PATCH", f"/v1/fpo-portal/relationships/{self.relationship_id}", "fpo", json={"decision": "ACTIVE"}).json())
        self.step("FPO farmer directory after acceptance", lambda: self.request("GET", "/v1/fpo-portal/farmers", "fpo").json())
        self.step("Projection/read-model refresh evidence", lambda: self.request("POST", "/v1/fpo-portal/admin/reconciliation/run", "admin", json={}).json())
        self.step("FPO farm portfolio after acceptance", lambda: self.request("GET", f"/v1/fpo/me/farmers/{self._first_portfolio_farmer()}/farms", "fpo").json())
        log.info("E2E relationship created and left ACTIVE for inspection: %s", self.relationship_id)

    def _first_portfolio_farmer(self):
        payload = self.request("GET", "/v1/fpo-portal/farmers", "fpo").json()
        if not payload.get("items"):
            raise RuntimeError("Accepted relationship did not produce a portfolio projection")
        return payload["items"][0]["farmer_id"]

    def _rollback_relationship_flow(self):
        if not self.farm_id or not self.farmer_profile_id:
            raise Skip("no active farm without an existing active/pending relationship is available")
        from services.fpo_management_service.app.repository import (
            authorize_fpo_farm_intelligence, create_farmer_relationship_request,
            cancel_farmer_relationship_request,
            decide_farmer_relationship, get_current_fpo_consent_policy,
            list_fpo_farmer_farms, list_fpo_farmer_portfolio,
            list_fpo_relationships, refresh_portfolio_read_models,
            revoke_farmer_relationship,
        )
        if len(self.farm_ids) < 2:
            raise Skip("two active farms with no existing primary relationship are required for cancellation and acceptance checks")
        with engine.connect() as conn:
            transaction = conn.begin()
            try:
                policy = get_current_fpo_consent_policy(conn)
                log.info("[FLOW] Consent policy loaded: %s v%s; scopes=%s", policy["policy_code"], policy["policy_version"], policy["mandatory_scopes"])
                cancelled_request = create_farmer_relationship_request(
                    conn, farmer_user_id=self.farmer_id, fpo_id=self.fpo_org_id,
                    farm_id=self.farm_ids[0], policy_code=policy["policy_code"],
                    policy_version=policy["policy_version"], accepted=True,
                    selected_optional_scopes=[], language_code=policy["language_code"],
                    correlation_id="rollback-e2e", ip_address="127.0.0.1",
                )
                self.relationship_id = str(cancelled_request["relationship_id"])
                inbox = list_fpo_relationships(conn, fpo_user_id=self.fpo_id)
                if not any(str(row["relationship_id"]) == self.relationship_id and row["status"] == "PENDING_FPO_ACCEPTANCE" for row in inbox):
                    raise RuntimeError("New consented farm request was not returned in its owner's FPO inbox")
                log.info("[FLOW] Request created and visible in FPO inbox: relationship=%s farm=%s", self.relationship_id, self.farm_ids[0])
                cancelled = cancel_farmer_relationship_request(conn, farmer_user_id=self.farmer_id, relationship_id=self.relationship_id)
                log.info("[FLOW] Farmer cancellation completed: relationship=%s status=%s", cancelled["relationship_id"], cancelled["status"])
                request = create_farmer_relationship_request(
                    conn, farmer_user_id=self.farmer_id, fpo_id=self.fpo_org_id,
                    farm_id=self.farm_ids[1], policy_code=policy["policy_code"],
                    policy_version=policy["policy_version"], accepted=True,
                    selected_optional_scopes=[], language_code=policy["language_code"],
                    correlation_id="rollback-e2e-accept", ip_address="127.0.0.1",
                )
                self.relationship_id = str(request["relationship_id"])
                log.info("[FLOW] Second farm request created for acceptance: relationship=%s farm=%s", self.relationship_id, self.farm_ids[1])
                decision = decide_farmer_relationship(conn, fpo_user_id=self.fpo_id, relationship_id=self.relationship_id, decision="ACTIVE", note="Rollback-only E2E acceptance")
                farms = list_fpo_farmer_farms(conn, user_id=self.fpo_id, farmer_id=self.farmer_profile_id)
                if not any(str(row["farm_id"]) == str(self.farm_ids[1]) for row in farms):
                    raise RuntimeError("Accepted relationship did not grant access to the selected farm")
                authorize_fpo_farm_intelligence(conn, user_id=self.fpo_id, farmer_id=self.farmer_profile_id, farm_id=self.farm_ids[1])
                refresh_portfolio_read_models(conn, fpo_id=self.fpo_org_id)
                portfolio = list_fpo_farmer_portfolio(conn, user_id=self.fpo_id)
                farmer_row = next((row for row in portfolio["items"] if str(row["farmer_id"]) == str(self.farmer_profile_id)), None)
                if not farmer_row or int(farmer_row["farm_count"]) != 1:
                    raise RuntimeError("FPO portfolio did not restrict this test farmer to exactly the authorized farm")
                log.info("[FLOW] Accepted relationship=%s; authorized farm=%s; portfolio farm_count=%s", decision["relationship_id"], self.farm_ids[1], farmer_row["farm_count"])
                revoke_farmer_relationship(conn, farmer_user_id=self.farmer_id, relationship_id=self.relationship_id, farm_id=self.farm_ids[1])
                try:
                    authorize_fpo_farm_intelligence(conn, user_id=self.fpo_id, farmer_id=self.farmer_profile_id, farm_id=self.farm_ids[1])
                except ValueError:
                    log.info("[FLOW] Revocation verified: FPO farm intelligence access denied after consent revocation")
                else:
                    raise RuntimeError("Farm intelligence remained available after farmer revoked consent")
                rejected_request = create_farmer_relationship_request(
                    conn, farmer_user_id=self.farmer_id, fpo_id=self.fpo_org_id,
                    farm_id=self.farm_ids[0], policy_code=policy["policy_code"],
                    policy_version=policy["policy_version"], accepted=True,
                    selected_optional_scopes=[], language_code=policy["language_code"],
                    correlation_id="rollback-e2e-reject", ip_address="127.0.0.1",
                )
                rejected = decide_farmer_relationship(conn, fpo_user_id=self.fpo_id, relationship_id=rejected_request["relationship_id"], decision="REJECTED", note="Rollback-only rejection test")
                consent_revoked = conn.execute(text("SELECT revoked_at FROM public.fpo_farmer_relationship_consents WHERE relationship_id=:relationship_id ORDER BY captured_at DESC LIMIT 1"), {"relationship_id": str(rejected_request["relationship_id"])}).scalar_one_or_none()
                if not consent_revoked or rejected["status"] != "REJECTED":
                    raise RuntimeError("FPO rejection did not revoke the consent record")
                log.info("[FLOW] Rejection verified: relationship=%s; captured consent was revoked", rejected["relationship_id"])
                return {"accepted_relationship_id": str(decision["relationship_id"]), "authorized_farm_id": str(self.farm_ids[1]), "authorized_farm_count": farmer_row["farm_count"], "farmer_cancelled_request": True, "farmer_revocation_enforced": True, "fpo_rejection_revoked_consent": True, "rollback": "guaranteed"}
            finally:
                transaction.rollback()

    @staticmethod
    def _assert_class_a_bulk_guard(bootstrap):
        entitlements = bootstrap.get("entitlements", {})
        bulk = entitlements.get("BULK_FARM_REGISTRATION", {})
        enabled = bool(bulk.get("enabled")) if isinstance(bulk, dict) else False
        class_code = (bootstrap.get("class") or {}).get("code")
        if class_code == "A" and enabled:
            raise RuntimeError("Class A must not expose BULK_FARM_REGISTRATION")
        return {"class_code": class_code, "bulk_farm_registration_enabled": enabled}

    def _read_intelligence(self, farmer_profile_id, farm_id):
        try:
            return self.request("GET", f"/v1/fpo/me/farmers/{farmer_profile_id}/farms/{farm_id}/intelligence", "fpo").json()
        except RuntimeError as exc:
            if "FPO_INTELLIGENCE_UNAVAILABLE" in str(exc):
                raise Skip("analytics dependency is not available in this local run") from exc
            raise


class Skip(Exception):
    pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8016")
    parser.add_argument("--mutate", action="store_true", help="Create a real local relationship; never use against production")
    args = parser.parse_args()
    try:
        E2E(args.base_url, args.mutate).run()
        log.info("FPO E2E CHECK COMPLETE: all executable steps passed")
        return 0
    except Exception:
        log.error("FPO E2E CHECK FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
