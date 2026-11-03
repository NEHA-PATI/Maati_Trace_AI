from __future__ import annotations

from contextlib import contextmanager
from uuid import uuid4

from services.profile_service.app import service as profile_service
from services.profile_service.app.schemas import FpoProvisioningProfileRequest


class FakeResult:
    def __init__(self, row=None):
        self.row = row

    def mappings(self):
        return self

    def first(self):
        return self.row


class FakeConnection:
    def __init__(self, user_id, profile_id):
        self.user_id = str(user_id)
        self.profile_id = str(profile_id)
        self.statements = []

    def execute(self, statement, _params=None):
        sql = str(statement)
        self.statements.append(sql)
        if "SELECT role, is_active, is_verified" in sql:
            return FakeResult(
                {"role": "fpo", "is_active": True, "is_verified": True},
            )
        if "SELECT state_name FROM public.states" in sql:
            return FakeResult({"state_name": "Odisha"})
        if "SELECT p.fpo_id, fu.user_id AS owner_user_id" in sql:
            return FakeResult(
                {"fpo_id": self.profile_id, "owner_user_id": self.user_id},
            )
        return FakeResult()


class FakeEngine:
    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def begin(self):
        yield self.connection


def test_internal_provisioning_matches_registration_not_first_membership(monkeypatch):
    user_id = uuid4()
    expected_profile_id = uuid4()
    connection = FakeConnection(user_id, expected_profile_id)
    monkeypatch.setattr(profile_service, "engine", FakeEngine(connection))
    payload = FpoProvisioningProfileRequest.model_validate(
        {
            "user_id": str(user_id),
            "correlation_id": str(uuid4()),
            "authorised_fpo_representative": True,
            "full_name": "FPO Representative",
            "email": "representative@example.com",
            "phone_number": "+919876543210",
            "signup_profile": {
                "organisation_name": "Growers Producer Company",
                "registration_type": "producer_company",
                "registration_number": "FPO-001",
                "state_code": 21,
            },
        }
    )

    result = profile_service.provision_fpo_profile_internal(payload)

    assert result == {"profile_fpo_id": str(expected_profile_id)}
    assert not any(
        "WHERE fu.user_id = :user_id" in sql for sql in connection.statements
    )
