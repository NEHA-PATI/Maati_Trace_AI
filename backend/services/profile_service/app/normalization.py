from __future__ import annotations

import re
from typing import Iterable


INDIAN_MOBILE_PATTERN = re.compile(
    r"^[6-9][0-9]{9}$"
)

PINCODE_PATTERN = re.compile(
    r"^[1-9][0-9]{5}$"
)

LOCATION_PENDING_VALUES = frozenset({
    "",
    "pending",
    "unassigned",
    "not assigned",
    "not selected",
})


def normalize_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    cleaned = " ".join(
        str(value).strip().split()
    )

    return cleaned or None


def normalize_email(
    value: str | None,
) -> str | None:
    cleaned = normalize_text(value)
    return cleaned.lower() if cleaned else None


def normalize_indian_mobile(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    compact = re.sub(
        r"[\s()\-]",
        "",
        str(value),
    )

    if compact.startswith("+91"):
        national = compact[3:]
    elif (
        compact.startswith("91")
        and len(compact) == 12
    ):
        national = compact[2:]
    elif (
        compact.startswith("0")
        and len(compact) == 11
    ):
        national = compact[1:]
    else:
        national = compact

    if not INDIAN_MOBILE_PATTERN.fullmatch(
        national
    ):
        raise ValueError(
            "Enter a valid Indian mobile number."
        )

    return f"+91{national}"


def normalize_pincode(
    value: str | None,
) -> str | None:
    cleaned = normalize_text(value)

    if cleaned is None:
        return None

    if not PINCODE_PATTERN.fullmatch(
        cleaned
    ):
        raise ValueError(
            "Pincode must contain six digits "
            "and cannot start with zero."
        )

    return cleaned


def normalize_text_list(
    values: Iterable[str] | None,
) -> list[str]:
    if values is None:
        return []

    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        cleaned = normalize_text(value)

        if not cleaned:
            continue

        key = cleaned.casefold()

        if key in seen:
            continue

        seen.add(key)
        result.append(cleaned)

    return result


def is_pending_location_value(
    value: str | None,
) -> bool:
    if value is None:
        return True

    cleaned = normalize_text(value)

    if cleaned is None:
        return True

    return (
        cleaned.casefold()
        in LOCATION_PENDING_VALUES
    )


def public_location_value(
    value: str | None,
) -> str | None:
    """
    Converts the database compatibility placeholder
    to an API-safe missing value.

    Database:
        district_name = "Pending"

    API:
        district_name = null
    """

    if is_pending_location_value(value):
        return None

    return normalize_text(value)