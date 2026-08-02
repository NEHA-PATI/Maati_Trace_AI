import pytest

from services.profile_service.app.normalization import (
    normalize_indian_mobile,
    normalize_pincode,
    normalize_text_list,
)

from services.profile_service.app.normalization import (
    is_pending_location_value,
    public_location_value,
)

def test_normalize_indian_mobile():
    assert (
        normalize_indian_mobile(
            "8208504361"
        )
        == "+918208504361"
    )

    assert (
        normalize_indian_mobile(
            "+91 82085 04361"
        )
        == "+918208504361"
    )


def test_invalid_mobile_is_rejected():
    with pytest.raises(ValueError):
        normalize_indian_mobile(
            "1234567890"
        )


def test_normalize_pincode():
    assert normalize_pincode(
        "752054"
    ) == "752054"


def test_invalid_pincode_is_rejected():
    with pytest.raises(ValueError):
        normalize_pincode(
            "012345"
        )


def test_text_lists_are_cleaned_and_deduplicated():
    assert normalize_text_list(
        [
            " Paddy ",
            "paddy",
            "Vegetables",
            "",
        ]
    ) == [
        "Paddy",
        "Vegetables",
    ]

def test_pending_location_is_logically_missing():
    assert is_pending_location_value(
        "Pending"
    ) is True

    assert is_pending_location_value(
        "Unassigned"
    ) is True

    assert is_pending_location_value(
        None
    ) is True


def test_pending_location_is_hidden_from_api():
    assert public_location_value(
        "Pending"
    ) is None

    assert public_location_value(
        " Puri "
    ) == "Puri"