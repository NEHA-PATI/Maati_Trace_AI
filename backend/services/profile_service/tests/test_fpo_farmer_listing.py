from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from services.profile_service.app import service
from services.profile_service.app.errors import ProfileError
from services.profile_service.tests.test_response_contracts import (
    farmer_repository_row,
)


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeEngine:
    def connect(self):
        return FakeConnection()


def context(role: str, user_id=None):
    return SimpleNamespace(
        principal=SimpleNamespace(
            role=role,
            user_id=user_id or uuid4(),
        )
    )


def patch_listing(
    monkeypatch,
    *,
    fpo_id,
    memberships=None,
    fpo_exists=True,
):
    monkeypatch.setattr(
        service,
        "engine",
        FakeEngine(),
    )
    monkeypatch.setattr(
        service,
        "get_fpo_by_id",
        lambda _conn, _fpo_id: (
            {"fpo_id": fpo_id}
            if fpo_exists
            else None
        ),
    )
    monkeypatch.setattr(
        service,
        "get_fpo_memberships",
        lambda _conn, _user_id: memberships or [],
    )
    monkeypatch.setattr(
        service,
        "list_fpo_farmers",
        lambda _conn, _fpo_id: [
            farmer_repository_row()
        ],
    )


def test_admin_can_list_fpo_farmers(monkeypatch):
    fpo_id = uuid4()
    patch_listing(
        monkeypatch,
        fpo_id=fpo_id,
    )

    result = (
        service.get_fpo_farmers_for_requester(
            context("admin"),
            fpo_id,
        )
    )

    assert len(result) == 1
    assert result[0]["full_name"] == "NEHA PATI"


def test_fpo_member_can_list_own_fpo_farmers(monkeypatch):
    fpo_id = uuid4()
    patch_listing(
        monkeypatch,
        fpo_id=fpo_id,
        memberships=[
            {
                "fpo_id": fpo_id,
            }
        ],
    )

    result = (
        service.get_fpo_farmers_for_requester(
            context("fpo"),
            fpo_id,
        )
    )

    assert len(result) == 1


def test_unrelated_fpo_member_receives_403(monkeypatch):
    fpo_id = uuid4()
    patch_listing(
        monkeypatch,
        fpo_id=fpo_id,
        memberships=[
            {
                "fpo_id": uuid4(),
            }
        ],
    )

    with pytest.raises(ProfileError) as exc:
        service.get_fpo_farmers_for_requester(
            context("fpo"),
            fpo_id,
        )

    assert exc.value.status_code == 403


def test_farmer_receives_403(monkeypatch):
    fpo_id = uuid4()
    patch_listing(
        monkeypatch,
        fpo_id=fpo_id,
    )

    with pytest.raises(ProfileError) as exc:
        service.get_fpo_farmers_for_requester(
            context("farmer"),
            fpo_id,
        )

    assert exc.value.status_code == 403


def test_unknown_fpo_receives_404(monkeypatch):
    fpo_id = uuid4()
    patch_listing(
        monkeypatch,
        fpo_id=fpo_id,
        fpo_exists=False,
    )

    with pytest.raises(ProfileError) as exc:
        service.get_fpo_farmers_for_requester(
            context("admin"),
            fpo_id,
        )

    assert exc.value.status_code == 404
