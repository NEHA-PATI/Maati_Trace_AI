SAFE_PROFILE_FIELDS = {
    "display_name", "organisation_description", "website_url", "preferred_language",
    "profile_image_url", "services_provided",
}
WARNING_PROFILE_FIELDS = {
    "contact_person_name", "contact_person_designation", "contact_phone", "alternate_phone",
    "contact_email", "declared_area_acres", "member_count", "active_member_count",
    "main_commodities", "services_provided", "state_name", "district_name", "block_code",
    "village_code", "village_name",
}
REVERIFICATION_PROFILE_FIELDS = {
    "legal_name", "organisation_type", "registration_type", "registration_number",
    "registration_authority", "date_of_registration", "cin", "pan_masked", "state_code",
}


def classify_profile_changes(fields: list[str] | set[str]) -> str:
    names = set(fields)
    if names & REVERIFICATION_PROFILE_FIELDS:
        return "REVERIFICATION_REQUIRED"
    if names & WARNING_PROFILE_FIELDS:
        return "REVIEW_WARNING"
    return "SAFE"
