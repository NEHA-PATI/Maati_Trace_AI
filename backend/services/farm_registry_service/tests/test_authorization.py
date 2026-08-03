import os
from uuid import UUID

import pytest

os.environ.setdefault("JWT_SECRET", "test-secret")

from services.farm_registry_service.app.errors import FarmRegistryError
from services.farm_registry_service.app.profile_client import FarmerValidation
from services.farm_registry_service.app.service import (
    ActorScope,
    _authorize_farm_read,
    _authorize_target_farmer,
)

FARMER_A = UUID("11111111-1111-1111-1111-111111111111")
FARMER_B = UUID("22222222-2222-2222-2222-222222222222")
FPO_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
FPO_B = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
USER_ID = UUID("99999999-9999-9999-9999-999999999999")


def target(
    *,
    farmer_id=FARMER_A,
    fpo_id=FPO_A,
    complete=True,
):
    return FarmerValidation(
        farmer_id=farmer_id,
        fpo_id=fpo_id,
        is_active=True,
        profile_complete=complete,
        onboarding_status="completed" if complete else "pending",
    )


def test_farmer_can_manage_own_farm():
    actor = ActorScope(role="farmer", user_id=USER_ID, farmer_id=FARMER_A)
    _authorize_target_farmer(actor, target(), write=True)


def test_farmer_cannot_manage_another_farmer():
    actor = ActorScope(role="farmer", user_id=USER_ID, farmer_id=FARMER_A)
    with pytest.raises(FarmRegistryError) as exc:
        _authorize_target_farmer(actor, target(farmer_id=FARMER_B), write=True)
    assert exc.value.status_code == 403


def test_fpo_manager_can_manage_linked_farmer():
    actor = ActorScope(
        role="fpo",
        user_id=USER_ID,
        fpo_id=FPO_A,
        fpo_role="manager",
    )
    _authorize_target_farmer(actor, target(), write=True)


def test_fpo_viewer_cannot_register_member_farm():
    actor = ActorScope(
        role="fpo",
        user_id=USER_ID,
        fpo_id=FPO_A,
        fpo_role="viewer",
    )
    with pytest.raises(FarmRegistryError) as exc:
        _authorize_target_farmer(actor, target(), write=True)
    assert exc.value.code == "FPO_ROLE_CANNOT_REGISTER_FARM"


def test_fpo_cannot_manage_unrelated_farmer():
    actor = ActorScope(
        role="fpo",
        user_id=USER_ID,
        fpo_id=FPO_A,
        fpo_role="admin",
    )
    with pytest.raises(FarmRegistryError) as exc:
        _authorize_target_farmer(actor, target(fpo_id=FPO_B), write=True)
    assert exc.value.code == "FPO_FARMER_ACCESS_FORBIDDEN"


def test_farmer_cannot_read_unrelated_farm():
    actor = ActorScope(role="farmer", user_id=USER_ID, farmer_id=FARMER_A)
    with pytest.raises(FarmRegistryError):
        _authorize_farm_read(
            actor,
            {
                "farmer_id": FARMER_B,
                "fpo_id": FPO_A,
            },
        )


def test_admin_can_read_any_farm():
    actor = ActorScope(role="admin", user_id=USER_ID)
    _authorize_farm_read(
        actor,
        {
            "farmer_id": FARMER_B,
            "fpo_id": FPO_B,
        },
    )
