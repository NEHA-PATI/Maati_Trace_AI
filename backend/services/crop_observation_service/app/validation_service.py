from __future__ import annotations

from typing import Any
from uuid import UUID

from services.crop_observation_service.app import repository as repo
from services.crop_observation_service.app.errors import CropObservationError

APPLICATION_AREA_SCOPES = ("WHOLE_FARM", "SELECTED_AREA")
APPLICATION_AREA_RELATIVE_EXTENTS = ("SMALL_PART", "ABOUT_HALF", "MOST_OF_FARM")
YES_NO_UNKNOWN_VALUES = ("YES", "NO", "UNKNOWN")
SEVERITY_VALUES = ("LOW", "MEDIUM", "HIGH")


def _field_error(field_code: str, message: str) -> dict[str, str]:
    return {"field": field_code, "message": message}


def _validate_application_area(field_code: str, value: Any, errors: list[dict[str, str]]) -> None:
    if not isinstance(value, dict):
        errors.append(_field_error(field_code, "Application area must be an object."))
        return
    scope = value.get("scope")
    if scope not in APPLICATION_AREA_SCOPES:
        errors.append(
            _field_error(field_code, f"scope must be one of {APPLICATION_AREA_SCOPES}.")
        )
        return
    relative_extent = value.get("relative_extent")
    if scope == "SELECTED_AREA" and relative_extent is not None:
        if relative_extent not in APPLICATION_AREA_RELATIVE_EXTENTS:
            errors.append(
                _field_error(
                    field_code,
                    f"relative_extent must be one of {APPLICATION_AREA_RELATIVE_EXTENTS}.",
                )
            )
    if scope == "WHOLE_FARM" and relative_extent is not None:
        errors.append(
            _field_error(field_code, "relative_extent is only valid when scope is SELECTED_AREA.")
        )
    extra_keys = set(value.keys()) - {"scope", "relative_extent"}
    if extra_keys:
        errors.append(_field_error(field_code, f"Unexpected keys: {sorted(extra_keys)}."))


def _validate_quantity_unit(field_code: str, value: Any, errors: list[dict[str, str]]) -> None:
    if not isinstance(value, dict):
        errors.append(_field_error(field_code, "Quantity must be an object with value/unit."))
        return
    amount = value.get("value")
    unit = value.get("unit")
    if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:
        errors.append(_field_error(field_code, "value must be a positive number."))
    if not isinstance(unit, str) or not unit.strip():
        errors.append(_field_error(field_code, "unit must be a non-empty string."))
    extra_keys = set(value.keys()) - {"value", "unit"}
    if extra_keys:
        errors.append(_field_error(field_code, f"Unexpected keys: {sorted(extra_keys)}."))


def _validate_choice(
    field_code: str,
    value: Any,
    *,
    field_definition_id: UUID,
    multi: bool,
    errors: list[dict[str, str]],
) -> None:
    options = repo.list_field_options(field_definition_id)
    allowed = {o["option_code"] for o in options}
    if multi:
        if not isinstance(value, list) or not value:
            errors.append(_field_error(field_code, "Expected a non-empty list of option codes."))
            return
        invalid = [v for v in value if v not in allowed]
        if invalid:
            errors.append(_field_error(field_code, f"Invalid option(s): {invalid}."))
    else:
        if allowed and value not in allowed:
            errors.append(_field_error(field_code, f"Invalid option: {value!r}."))
        elif not allowed and (not isinstance(value, str) or not value.strip()):
            errors.append(_field_error(field_code, "Expected a non-empty option code."))


def validate_practice_answers(
    *,
    stage_practice_id: UUID,
    answers: dict[str, Any],
) -> dict[str, Any]:
    """Validate a practice's answers against its published field
    definitions. Never trusts the shape the frontend sent — every field is
    resolved from the DB, unknown keys are rejected, required fields are
    enforced, and each field_type has its own value-shape rule.
    Returns the answers unchanged (already-validated) on success.
    """
    field_defs = repo.list_practice_fields(stage_practice_id)
    if not field_defs:
        raise CropObservationError(
            "PRACTICE_NOT_CONFIGURED",
            "This practice has no configured fields yet.",
            409,
        )

    by_code = {f["field_code"]: f for f in field_defs}
    errors: list[dict[str, str]] = []

    unknown_keys = set(answers.keys()) - set(by_code.keys())
    if unknown_keys:
        raise CropObservationError(
            "UNKNOWN_FIELD",
            f"Unknown field(s) submitted: {sorted(unknown_keys)}.",
            422,
            fields=[_field_error(key, "Unknown field.") for key in sorted(unknown_keys)],
        )

    for field in field_defs:
        code = field["field_code"]
        if code not in answers:
            if field["is_required"]:
                errors.append(_field_error(code, "This field is required."))
            continue

        value = answers[code]
        field_type = field["field_type"]

        if field_type == "APPLICATION_AREA":
            _validate_application_area(code, value, errors)
        elif field_type == "QUANTITY_UNIT":
            _validate_quantity_unit(code, value, errors)
        elif field_type in ("SINGLE_CHOICE", "PICTURE_CHOICE", "PRODUCT", "PEST", "DISEASE"):
            _validate_choice(
                code, value, field_definition_id=field["field_definition_id"], multi=False, errors=errors
            )
        elif field_type == "MULTI_CHOICE":
            _validate_choice(
                code, value, field_definition_id=field["field_definition_id"], multi=True, errors=errors
            )
        elif field_type == "YES_NO_UNKNOWN":
            if value not in YES_NO_UNKNOWN_VALUES:
                errors.append(_field_error(code, f"Must be one of {YES_NO_UNKNOWN_VALUES}."))
        elif field_type == "SEVERITY":
            if value not in SEVERITY_VALUES:
                errors.append(_field_error(code, f"Must be one of {SEVERITY_VALUES}."))
        elif field_type == "BOOLEAN":
            if not isinstance(value, bool):
                errors.append(_field_error(code, "Must be true or false."))
        elif field_type == "NUMBER":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(_field_error(code, "Must be a number."))
        elif field_type == "SHORT_TEXT":
            if not isinstance(value, str) or len(value) > 500:
                errors.append(_field_error(code, "Must be text up to 500 characters."))
        else:
            errors.append(_field_error(code, f"Unsupported field_type: {field_type}."))

    if errors:
        raise CropObservationError(
            "VALIDATION_ERROR",
            "Check the submitted answers.",
            422,
            fields=errors,
        )

    return answers
