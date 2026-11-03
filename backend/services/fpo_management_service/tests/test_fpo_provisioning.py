from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import uuid4

import pytest

from services.fpo_management_service.app.repository import (
    claim_provisioning_events,
    public_fpo_id,
    record_event_inbox,
    validate_auth_user_created_event,
)


def valid_event() -> dict:
    user_id = str(uuid4())
    return {
        "event_id": str(uuid4()),
        "event_type": "auth.user.created",
        "event_version": 2,
        "occurred_at": "2026-11-02T10:00:00+00:00",
        "correlation_id": str(uuid4()),
        "subject_id": user_id,
        "payload": {
            "user_id": user_id,
            "account_type": "fpo",
            "authorised_fpo_representative": True,
            "email": "representative@example.com",
            "phone_number": "+919876543210",
            "full_name": "FPO Representative",
            "signup_profile": {
                "organisation_name": "Growers Producer Company",
                "registration_type": "PRODUCER_COMPANY",
                "registration_number": "FPO-001",
                "state_code": 21,
                "district_code": 2101,
            },
        },
    }


class FakeResult:
    def __init__(self, scalar=None, row=None):
        self.scalar = scalar
        self.row = row

    def scalar_one_or_none(self):
        return self.scalar

    def mappings(self):
        return self

    def first(self):
        return self.row

    def one(self):
        return self.row


class FakeConnection:
    def __init__(self, *, inserted_id=None, existing=None):
        self.inserted_id = inserted_id
        self.existing = existing
        self.statements = []

    def execute(self, statement, params=None):
        sql = str(statement)
        self.statements.append((sql, params or {}))
        if "INSERT INTO public.fpo_event_inbox" in sql:
            return FakeResult(scalar=self.inserted_id)
        if "SELECT inbox_id, payload_hash, status" in sql:
            return FakeResult(row=self.existing)
        return FakeResult()


def test_public_id_uses_canonical_state_and_event_year_deterministically():
    occurred_at = datetime(2026, 11, 2, tzinfo=timezone.utc)
    first = public_fpo_id(21, 100001, occurred_at)
    assert first.startswith("MTFPO-S21-26-100001-")
    assert first == public_fpo_id(21, 100001, occurred_at)


@pytest.mark.parametrize("state_code,sequence", [(0, 100001), (-1, 100001), (21, 0)])
def test_public_id_rejects_invalid_identity_inputs(state_code, sequence):
    with pytest.raises(ValueError, match="FPO_PUBLIC_ID_INPUT_INVALID"):
        public_fpo_id(state_code, sequence)


def test_event_validator_rejects_subject_mismatch_and_unexpected_sensitive_fields():
    event = valid_event()
    event["subject_id"] = str(uuid4())
    with pytest.raises(ValueError, match="FPO_EVENT_SUBJECT_MISMATCH"):
        validate_auth_user_created_event(event)

    event = valid_event()
    event["payload"]["bank_account"] = "must-not-be-accepted"
    with pytest.raises(ValueError, match="FPO_EVENT_PAYLOAD_FIELDS_INVALID"):
        validate_auth_user_created_event(event)


def test_duplicate_event_delivery_is_idempotent():
    event = valid_event()
    digest = sha256(json.dumps(event["payload"], sort_keys=True, default=str).encode()).hexdigest()
    conn = FakeConnection(
        existing={"inbox_id": str(uuid4()), "payload_hash": digest, "status": "DEAD"},
    )
    assert record_event_inbox(conn, event) == "DUPLICATE"
    assert any("delivery_count = delivery_count + 1" in sql for sql, _ in conn.statements)
    assert not any("SET status = 'PROCESSING'" in sql for sql, _ in conn.statements)


def test_payload_conflict_is_poisoned_instead_of_reprocessed():
    event = valid_event()
    conn = FakeConnection(
        existing={"inbox_id": str(uuid4()), "payload_hash": "different", "status": "PROCESSED"},
    )
    assert record_event_inbox(conn, event) == "POISON_EVENT"
    assert any("status = 'DEAD'" in sql and "POISON_EVENT" in sql for sql, _ in conn.statements)


def test_claim_worker_selects_only_its_inbox_and_keeps_stale_lock_grouped():
    class ClaimConnection:
        def execute(self, statement, _params):
            self.sql = str(statement)
            return type("Rows", (), {"mappings": lambda self: self, "all": lambda self: []})()

    conn = ClaimConnection()
    assert claim_provisioning_events(conn, batch_size=10) == []
    assert "auth_outbox_events" not in conn.sql
    assert "consumer_name = 'fpo_management_service'" in conn.sql
    assert "status IN ('RECEIVED', 'FAILED')" in conn.sql
    assert "status = 'PROCESSING' AND locked_at" in conn.sql
