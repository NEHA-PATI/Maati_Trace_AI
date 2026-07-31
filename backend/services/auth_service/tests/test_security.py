from __future__ import annotations

from uuid import uuid4

from passlib.context import CryptContext

from services.auth_service.app.security import (
    create_access_token,
    decode_access_token,
    hash_otp,
    hash_password,
    normalize_indian_mobile,
    verify_otp_hash,
    verify_password_detailed,
)


def test_indian_phone_is_stored_as_e164():
    assert normalize_indian_mobile("9876543210") == "+919876543210"
    assert normalize_indian_mobile("09876543210") == "+919876543210"
    assert normalize_indian_mobile("+919876543210") == "+919876543210"


def test_argon2_password_round_trip():
    encoded = hash_password("correct horse battery staple")
    result = verify_password_detailed("correct horse battery staple", encoded)
    assert result.valid is True
    assert encoded.startswith("$argon2id$")


def test_existing_bcrypt_password_requires_upgrade():
    bcrypt = CryptContext(schemes=["bcrypt"])
    encoded = bcrypt.hash("legacy-password")
    result = verify_password_detailed("legacy-password", encoded)
    assert result.valid is True
    assert result.needs_rehash is True


def test_access_token_contains_session_claim():
    user_id = uuid4()
    session_id = uuid4()
    token = create_access_token(
        {"user_id": user_id, "role": "farmer"},
        session_id,
    )
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["session_id"] == str(session_id)
    assert payload["type"] == "access"


def test_otp_hash_is_session_bound():
    first_session = uuid4()
    second_session = uuid4()
    digest = hash_otp(first_session, "123456")
    assert verify_otp_hash(first_session, "123456", digest) is True
    assert verify_otp_hash(second_session, "123456", digest) is False
    assert verify_otp_hash(first_session, "654321", digest) is False