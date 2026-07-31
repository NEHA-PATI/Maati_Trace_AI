from __future__ import annotations

import pytest
from pydantic import ValidationError

from services.auth_service.app.schemas import (
    LoginRequest,
    SignupStartRequest,
    FpoAccessRequestCreate,
    InvitationAcceptRequest,
    InvitationCreateRequest,
    PasswordResetRequest,
)


def test_signup_has_no_public_role_or_profile_fields():
    with pytest.raises(ValidationError):
        SignupStartRequest(
            full_name="Neha Pati",
            email="neha@example.com",
            phone_number="9876543210",
            password="correct horse battery staple",
            consent_terms=True,
            role="fpo",
        )


def test_signup_normalises_phone_and_email():
    request = SignupStartRequest(
        full_name="  Neha   Pati  ",
        email="NEHA@EXAMPLE.COM",
        phone_number="09876543210",
        password="correct horse battery staple",
        consent_terms=True,
    )
    assert request.full_name == "Neha Pati"
    assert str(request.email) == "neha@example.com"
    assert request.phone_number == "+919876543210"


def test_login_normalises_phone_identifier():
    request = LoginRequest(identifier="9876543210", password="anything")
    assert request.resolved_identifier() == "+919876543210"


def test_fpo_access_phone_is_e164():
    payload = FpoAccessRequestCreate(
        organisation_name="Green Growers FPO",
        contact_person_name="Neha Pati",
        contact_email="NEHA@EXAMPLE.COM",
        contact_phone="09876543210",
    )
    assert payload.contact_phone == "+919876543210"
    assert str(payload.contact_email) == "neha@example.com"


def test_invitation_accept_rejects_short_password():
    with pytest.raises(ValidationError):
        InvitationAcceptRequest(
            token="x" * 60,
            full_name="Neha Pati",
            phone_number="9876543210",
            password="too-short",
        )


def test_invitation_role_is_restricted():
    with pytest.raises(ValidationError):
        InvitationCreateRequest(email="fpo@example.com", role="farmer")


def test_reset_request_rejects_short_token():
    with pytest.raises(ValidationError):
        PasswordResetRequest(token="short", new_password="long enough password")