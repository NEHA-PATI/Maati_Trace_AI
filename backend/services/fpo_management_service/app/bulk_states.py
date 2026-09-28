def staged_status_for_farmer_match(record_type: str) -> str:
    return "AWAITING_FARM_CONFIRMATION" if record_type == "FARM" else "AWAITING_CONSENT"
