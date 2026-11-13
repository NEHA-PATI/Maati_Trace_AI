from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection


CHECK_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ"


def _public_fpo_id(state_code: int, sequence_number: int) -> str:
    event_time = datetime.now(timezone.utc)
    check = CHECK_ALPHABET[sequence_number % len(CHECK_ALPHABET)]
    return f"MTFPO-S{state_code:02d}-{event_time.year % 100:02d}-{sequence_number:06d}-{check}"


FARMER_SELECT = """
    fp.farmer_id,
    fp.user_id,
    fp.fpo_id,
    fp.full_name,
    u.email,
    fp.phone_number,
    fp.gender,
    fp.date_of_birth,
    fp.preferred_language,
    fp.aadhaar_last4,
    fp.kyc_status,
    fp.state_name,
    fp.district_name,
    fp.district_code,
    fp.block_name,
    fp.block_code,
    fp.village_name,
    fp.gram_panchayat,
    fp.pincode,
    fp.farmer_type,
    fp.total_landholding_acres,
    fp.cultivated_area_acres,
    fp.primary_crop,
    fp.irrigation_status,
    fp.consent_location_use,
    fp.consent_data_processing,
    fp.consent_advisory_messages,
    fp.consent_fpo_data_sharing,
    COALESCE(
        fp.profile_image_url,
        u.profile_image_url
    ) AS profile_image_url,
    fp.is_active,
    fp.created_at,
    fp.updated_at,
    fp.profile_version,
    fp.onboarding_completed_at
"""


FPO_SELECT = """
    f.fpo_id,
    org.fpo_id AS organization_id,
    org.public_fpo_id,
    org.provisioning_status,
    org.lifecycle_status,
    org.verification_status AS organization_verification_status,
    (
        SELECT assignment.class_code
        FROM public.fpo_class_assignments assignment
        WHERE assignment.fpo_id = org.fpo_id
          AND assignment.is_active = TRUE
          AND (assignment.expires_at IS NULL OR assignment.expires_at > now())
        ORDER BY assignment.assigned_at DESC
        LIMIT 1
    ) AS class_code,
    org.commercial_status,
    f.legal_name,
    f.display_name,
    f.organisation_type,
    f.cin,
    f.gstin,
    f.website_url,
    f.organisation_description,
    f.operating_since_year,
    f.registered_address_line_1,
    f.registered_address_line_2,
    f.women_member_count,
    f.small_marginal_member_count,
    f.declared_area_acres,
    f.logo_object_key,
    f.logo_mime_type,
    f.logo_size_bytes,
    f.logo_checksum,
    f.fpo_name,
    f.registration_number,
    f.registration_type,
    f.registration_authority,
    f.date_of_registration,
    f.promoted_by,
    f.promoting_institution_name,
    f.contact_person_name,
    f.contact_person_designation,
    f.contact_phone,
    f.alternate_phone,
    f.contact_email,
    f.preferred_language,
    f.state_name,
    f.district_name,
    f.district_code,
    f.block_name,
    f.block_code,
    f.village_name,
    f.gram_panchayat,
    f.pincode,
    f.postal_code,
    f.state_code,
    f.village_code,
    f.gram_panchayat_code,
    f.gram_panchayat_name,
    f.office_address,
    COALESCE((SELECT array_agg(c.commodity_code ORDER BY c.priority, c.commodity_code) FROM public.fpo_profile_commodities c WHERE c.fpo_id = f.fpo_id), f.main_commodities) AS main_commodities,
    f.member_count,
    f.active_member_count,
    f.female_member_count,
    f.year_established,
    COALESCE((SELECT array_agg(s.service_code ORDER BY s.service_code) FROM public.fpo_profile_services s WHERE s.fpo_id = f.fpo_id AND s.is_active = TRUE), f.services_provided) AS services_provided,
    f.profile_completion_percentage,
    f.verification_readiness_percentage,
    f.verification_status,
    f.profile_image_url,
    f.is_active,
    f.created_at,
    f.updated_at,
    f.profile_version,
    f.onboarding_completed_at,
    f.profile_status,
    f.verification_refresh_required
"""


def _dict(row: Any) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def get_farmer_by_user_id(
    conn: Connection,
    user_id: UUID | str,
    *,
    for_update: bool = False,
) -> dict[str, Any] | None:
    lock = " FOR UPDATE OF fp" if for_update else ""

    row = conn.execute(
        text(
            f"""
            SELECT {FARMER_SELECT}
            FROM farmer_profiles fp
            JOIN users u
              ON u.user_id = fp.user_id
            WHERE fp.user_id = :user_id
              AND fp.is_active = TRUE
            LIMIT 1
            {lock};
            """
        ),
        {"user_id": str(user_id)},
    ).mappings().first()

    return _dict(row)


def get_farmer_by_id(
    conn: Connection,
    farmer_id: UUID | str,
) -> dict[str, Any] | None:
    row = conn.execute(
        text(
            f"""
            SELECT {FARMER_SELECT}
            FROM farmer_profiles fp
            JOIN users u
              ON u.user_id = fp.user_id
            WHERE fp.farmer_id = :farmer_id
              AND fp.is_active = TRUE
            LIMIT 1;
            """
        ),
        {"farmer_id": str(farmer_id)},
    ).mappings().first()

    return _dict(row)


def ensure_farmer_profile(
    conn: Connection,
    user_id: UUID | str,
) -> dict[str, Any] | None:
    conn.execute(
        text(
            """
            INSERT INTO farmer_profiles (
                user_id,
                fpo_id,
                full_name,
                phone_number,
                gender,
                state_name,
                district_name,
                district_code,
                block_name,
                block_code,
                village_name,
                is_active,
                created_at,
                updated_at
            )
            SELECT
                u.user_id,
                NULL,
                u.full_name,
                u.phone_number,
                NULL,
                'Odisha',
                'Pending',
                NULL,
                NULL,
                NULL,
                NULL,
                TRUE,
                now(),
                now()
            FROM users u
            WHERE u.user_id = :user_id
              AND u.role = 'farmer'
            ON CONFLICT (user_id)
            DO NOTHING;
            """
        ),
        {
            "user_id": str(user_id),
        },
    )

    return get_farmer_by_user_id(
        conn,
        user_id,
        for_update=True,
    )


def update_farmer_profile(
    conn: Connection,
    *,
    user_id: UUID | str,
    values: dict[str, Any],
    profile_complete: bool,
) -> dict[str, Any] | None:
    conn.execute(
        text(
            """
            UPDATE farmer_profiles
            SET
                full_name = :full_name,
                phone_number = :phone_number,
                gender = :gender,
                date_of_birth = :date_of_birth,
                preferred_language = :preferred_language,
                aadhaar_last4 = :aadhaar_last4,

                state_name = :state_name,
                district_name = :district_name,
                district_code = :district_code,
                block_name = :block_name,
                block_code = :block_code,
                village_name = :village_name,
                gram_panchayat = :gram_panchayat,
                pincode = :pincode,

                farmer_type = :farmer_type,
                total_landholding_acres =
                    :total_landholding_acres,
                cultivated_area_acres =
                    :cultivated_area_acres,
                primary_crop = :primary_crop,
                irrigation_status = :irrigation_status,

                consent_location_use =
                    :consent_location_use,
                consent_data_processing =
                    :consent_data_processing,
                consent_advisory_messages =
                    :consent_advisory_messages,
                consent_fpo_data_sharing =
                    :consent_fpo_data_sharing,

                consent_location_use_at = CASE
                    WHEN :consent_location_use
                    THEN COALESCE(
                        consent_location_use_at,
                        now()
                    )
                    ELSE NULL
                END,

                consent_data_processing_at = CASE
                    WHEN :consent_data_processing
                    THEN COALESCE(
                        consent_data_processing_at,
                        now()
                    )
                    ELSE NULL
                END,

                consent_advisory_messages_at = CASE
                    WHEN :consent_advisory_messages
                    THEN COALESCE(
                        consent_advisory_messages_at,
                        now()
                    )
                    ELSE NULL
                END,

                consent_fpo_data_sharing_at = CASE
                    WHEN :consent_fpo_data_sharing
                    THEN COALESCE(
                        consent_fpo_data_sharing_at,
                        now()
                    )
                    ELSE NULL
                END,

                profile_image_url = :profile_image_url,

                onboarding_completed_at = CASE
                    WHEN :profile_complete
                    THEN COALESCE(
                        onboarding_completed_at,
                        now()
                    )
                    ELSE NULL
                END,

                profile_version = profile_version + 1,
                updated_at = now()

            WHERE user_id = :user_id
              AND is_active = TRUE;
            """
        ),
        {
            **values,
            "user_id": str(user_id),
            "profile_complete": profile_complete,
        },
    )

    return get_farmer_by_user_id(
        conn,
        user_id,
        for_update=True,
    )


def update_user_profile_projection(
    conn: Connection,
    *,
    user_id: UUID | str,
    full_name: str,
    phone_number: str | None = None,
    profile_image_url: str | None,
    onboarding_status: str,
    sync_phone_number: bool = True,
) -> None:
    phone_number_clause = (
        "phone_number = :phone_number,"
        if sync_phone_number
        else ""
    )
    conn.execute(
        text(
            """
            UPDATE users
            SET
                full_name = :full_name,
                {phone_number_clause}
                profile_image_url = :profile_image_url,
                onboarding_status = :onboarding_status,
                updated_at = now()
            WHERE user_id = :user_id;
            """.format(phone_number_clause=phone_number_clause)
        ),
        {
            "user_id": str(user_id),
            "full_name": full_name,
            "phone_number": phone_number,
            "profile_image_url": profile_image_url,
            "onboarding_status": onboarding_status,
        },
    )


def update_user_onboarding_status(
    conn: Connection,
    *,
    user_id: UUID | str,
    onboarding_status: str,
) -> None:
    conn.execute(
        text(
            """
            UPDATE users
            SET onboarding_status = :onboarding_status,
                updated_at = now()
            WHERE user_id = :user_id;
            """
        ),
        {
            "user_id": str(user_id),
            "onboarding_status": onboarding_status,
        },
    )


def get_fpo_memberships(
    conn: Connection,
    user_id: UUID | str,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            SELECT
                fu.fpo_user_id,
                fu.fpo_id,
                fu.user_id,
                COALESCE(
                    NULLIF(fu.fpo_role, ''),
                    NULLIF(fu.role, ''),
                    'manager'
                ) AS fpo_role,
                fu.is_active,
                fu.created_at
            FROM fpo_users fu
            WHERE fu.user_id = :user_id
              AND fu.is_active = TRUE
            ORDER BY fu.created_at DESC;
            """
        ),
        {"user_id": str(user_id)},
    ).mappings().all()

    return [dict(row) for row in rows]


def get_fpo_by_id(
    conn: Connection,
    fpo_id: UUID | str,
) -> dict[str, Any] | None:
    row = conn.execute(
        text(
            f"""
            SELECT {FPO_SELECT}
            FROM fpos f
            LEFT JOIN public.fpo_organizations org
              ON org.profile_fpo_id = f.fpo_id
            WHERE f.fpo_id = :fpo_id
              AND f.is_active = TRUE
            LIMIT 1;
            """
        ),
        {"fpo_id": str(fpo_id)},
    ).mappings().first()

    return _dict(row)


def list_fpos(
    conn: Connection,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            f"""
            SELECT {FPO_SELECT}
            FROM fpos f
            LEFT JOIN public.fpo_organizations org
              ON org.profile_fpo_id = f.fpo_id
            WHERE f.is_active = TRUE
            ORDER BY f.created_at DESC, f.fpo_id
            LIMIT :limit
            OFFSET :offset;
            """
        ),
        {"limit": limit, "offset": offset},
    ).mappings().all()

    return [dict(row) for row in rows]


def list_fpo_commodities(conn: Connection, fpo_id: UUID | str) -> list[dict[str, Any]]:
    rows = conn.execute(text("""
        SELECT commodity_code AS profile_commodity_id, fpo_id AS profile_id,
               commodity_code, variety_code, is_primary, declared_farmer_count,
               declared_area_acres, season_codes, status, created_at, updated_at
        FROM public.fpo_profile_commodities
        WHERE fpo_id = :fpo_id AND status = 'ACTIVE'
        ORDER BY is_primary DESC, commodity_code
    """), {"fpo_id": str(fpo_id)}).mappings().all()
    return [dict(row) for row in rows]


def upsert_fpo_commodity(conn: Connection, fpo_id: UUID | str, values: dict[str, Any]) -> dict[str, Any]:
    row = conn.execute(text("""
        INSERT INTO public.fpo_profile_commodities
            (fpo_id, commodity_code, variety_code, is_primary, declared_farmer_count,
             declared_area_acres, season_codes, status, created_at, updated_at)
        VALUES (:fpo_id, :commodity_code, :variety_code, :is_primary, :declared_farmer_count,
                :declared_area_acres, :season_codes, 'ACTIVE', now(), now())
        ON CONFLICT (fpo_id, commodity_code) DO UPDATE SET
            variety_code = EXCLUDED.variety_code,
            is_primary = EXCLUDED.is_primary,
            declared_farmer_count = EXCLUDED.declared_farmer_count,
            declared_area_acres = EXCLUDED.declared_area_acres,
            season_codes = EXCLUDED.season_codes,
            status = 'ACTIVE', updated_at = now()
        RETURNING commodity_code AS profile_commodity_id, fpo_id AS profile_id,
                  commodity_code, variety_code, is_primary, declared_farmer_count,
                  declared_area_acres, season_codes, status, created_at, updated_at
    """), {"fpo_id": str(fpo_id), **values}).mappings().one()
    return dict(row)


def retire_fpo_commodity(conn: Connection, fpo_id: UUID | str, commodity_code: str) -> None:
    conn.execute(text("""
        UPDATE public.fpo_profile_commodities
        SET status = 'RETIRED', is_primary = false, updated_at = now()
        WHERE fpo_id = :fpo_id AND commodity_code = :commodity_code
    """), {"fpo_id": str(fpo_id), "commodity_code": commodity_code})


def list_fpo_services(conn: Connection, fpo_id: UUID | str) -> list[dict[str, Any]]:
    rows = conn.execute(text("""
        SELECT service_code AS profile_service_id, fpo_id AS profile_id,
               service_code, details->>'display_name' AS display_name,
               details->>'description' AS description,
               NULLIF(details->>'active_from', '')::date AS active_from,
               status, created_at, updated_at
        FROM public.fpo_profile_services
        WHERE fpo_id = :fpo_id AND status = 'ACTIVE'
        ORDER BY service_code
    """), {"fpo_id": str(fpo_id)}).mappings().all()
    return [dict(row) for row in rows]


def upsert_fpo_service(conn: Connection, fpo_id: UUID | str, values: dict[str, Any]) -> dict[str, Any]:
    details = {key: values.get(key) for key in ("display_name", "description", "active_from")}
    row = conn.execute(text("""
        INSERT INTO public.fpo_profile_services
            (fpo_id, service_code, details, status, is_active, created_at, updated_at)
        VALUES (:fpo_id, :service_code, CAST(:details AS jsonb), 'ACTIVE', true, now(), now())
        ON CONFLICT (fpo_id, service_code) DO UPDATE SET
            details = EXCLUDED.details, status = 'ACTIVE', is_active = true, updated_at = now()
        RETURNING service_code AS profile_service_id, fpo_id AS profile_id,
                  service_code, details->>'display_name' AS display_name,
                  details->>'description' AS description,
                  NULLIF(details->>'active_from', '')::date AS active_from,
                  status, created_at, updated_at
    """), {"fpo_id": str(fpo_id), "details": json.dumps(details), **values}).mappings().one()
    return dict(row)


def retire_fpo_service(conn: Connection, fpo_id: UUID | str, service_code: str) -> None:
    conn.execute(text("""
        UPDATE public.fpo_profile_services
        SET status = 'RETIRED', is_active = false, updated_at = now()
        WHERE fpo_id = :fpo_id AND service_code = :service_code
    """), {"fpo_id": str(fpo_id), "service_code": service_code})


def list_fpo_service_areas(conn: Connection, fpo_id: UUID | str) -> list[dict[str, Any]]:
    rows = conn.execute(text("""
        SELECT service_area_id, area.fpo_id AS profile_id, area.geography_level,
               area.state_code, states.state_name, area.district_code,
               districts.district_name, area.block_code, blocks.block_name,
               area.village_code, area.is_primary, area.status,
               area.created_at, area.updated_at
        FROM public.fpo_profile_service_areas
        AS area
        LEFT JOIN public.states ON states.state_code = area.state_code
        LEFT JOIN public.districts ON districts.district_code = area.district_code
        LEFT JOIN public.blocks ON blocks.block_code = area.block_code
        WHERE area.fpo_id = :fpo_id AND area.status = 'ACTIVE'
        ORDER BY area.is_primary DESC, area.geography_level, area.service_area_id
    """), {"fpo_id": str(fpo_id)}).mappings().all()
    return [dict(row) for row in rows]


def create_fpo_service_area(conn: Connection, fpo_id: UUID | str, values: dict[str, Any]) -> dict[str, Any]:
    row = conn.execute(text("""
        INSERT INTO public.fpo_profile_service_areas
            (fpo_id, geography_level, state_code, district_code, block_code,
             village_code, is_primary, status, is_active, created_at, updated_at)
        VALUES (:fpo_id, :geography_level, :state_code, :district_code, :block_code,
                :village_code, :is_primary, 'ACTIVE', true, now(), now())
        RETURNING service_area_id, fpo_id AS profile_id, geography_level, state_code,
                  district_code, block_code, village_code, is_primary, status,
                  created_at, updated_at
    """), {"fpo_id": str(fpo_id), **values}).mappings().one()
    return dict(row)


def retire_fpo_service_area(conn: Connection, fpo_id: UUID | str, service_area_id: UUID) -> None:
    conn.execute(text("""
        UPDATE public.fpo_profile_service_areas
        SET status = 'RETIRED', is_active = false, updated_at = now()
        WHERE fpo_id = :fpo_id AND service_area_id = :service_area_id
    """), {"fpo_id": str(fpo_id), "service_area_id": str(service_area_id)})


def create_fpo_with_membership(
    conn: Connection,
    *,
    user_id: UUID | str,
    values: dict[str, Any],
    write_legacy_verification_status: bool = True,
) -> dict[str, Any]:
    verification_column = "verification_status," if write_legacy_verification_status else ""
    verification_value = "'pending'," if write_legacy_verification_status else ""
    row = conn.execute(
        text(
            f"""
            INSERT INTO fpos (
                legal_name,
                display_name,
                organisation_type,
                registration_authority,
                website_url,
                organisation_description,
                operating_since_year,
                fpo_name,
                registration_number,
                registration_type,
                date_of_registration,
                promoted_by,
                promoting_institution_name,

                contact_person_name,
                contact_person_designation,
                contact_phone,
                alternate_phone,
                contact_email,
                preferred_language,

                state_name,
                district_name,
                district_code,
                block_name,
                block_code,
                village_name,
                gram_panchayat,
                pincode,
                postal_code,
                state_code,
                office_address,
                village_code,
                gram_panchayat_code,
                gram_panchayat_name,

                main_commodities,
                member_count,
                active_member_count,
                female_member_count,
                year_established,
                services_provided,

                {verification_column}
                profile_image_url,
                onboarding_completed_at,
                profile_version,
                is_active
            )
            VALUES (
                :legal_name,
                :display_name,
                :organisation_type,
                :registration_authority,
                :website_url,
                :organisation_description,
                :operating_since_year,
                :fpo_name,
                :registration_number,
                :registration_type,
                :date_of_registration,
                :promoted_by,
                :promoting_institution_name,

                :contact_person_name,
                :contact_person_designation,
                :contact_phone,
                :alternate_phone,
                :contact_email,
                :preferred_language,

                :state_name,
                :district_name,
                :district_code,
                :block_name,
                :block_code,
                :village_name,
                :gram_panchayat,
                :pincode,
                :postal_code,
                :state_code,
                :office_address,
                :village_code,
                :gram_panchayat_code,
                :gram_panchayat_name,

                :main_commodities,
                :member_count,
                :active_member_count,
                :female_member_count,
                :year_established,
                :services_provided,

                {verification_value}
                :profile_image_url,
                CASE
                    WHEN :profile_complete
                    THEN now()
                    ELSE NULL
                END,
                1,
                TRUE
            )
            RETURNING fpo_id;
            """
        ),
        values,
    ).mappings().one()

    fpo_id = row["fpo_id"]

    conn.execute(text("DELETE FROM public.fpo_profile_commodities WHERE fpo_id = :fpo_id"), {"fpo_id": str(fpo_id)})
    conn.execute(text("INSERT INTO public.fpo_profile_commodities (fpo_id, commodity_code, priority) SELECT :fpo_id, value, CASE WHEN ordinality = 1 THEN 'PRIMARY' ELSE 'SECONDARY' END FROM unnest(CAST(:commodities AS text[])) WITH ORDINALITY AS values(value, ordinality) ON CONFLICT DO NOTHING"), {"fpo_id": str(fpo_id), "commodities": values.get("main_commodities") or []})
    conn.execute(text("DELETE FROM public.fpo_profile_services WHERE fpo_id = :fpo_id"), {"fpo_id": str(fpo_id)})
    conn.execute(text("INSERT INTO public.fpo_profile_services (fpo_id, service_code) SELECT :fpo_id, value FROM unnest(CAST(:services AS text[])) AS values(value) ON CONFLICT DO NOTHING"), {"fpo_id": str(fpo_id), "services": values.get("services_provided") or []})

    conn.execute(
        text(
            """
            INSERT INTO fpo_users (
                fpo_id,
                user_id,
                fpo_role,
                role,
                is_active,
                created_at,
                updated_at
            )
            VALUES (
                :fpo_id,
                :user_id,
                'owner',
                'owner',
                TRUE,
                now(),
                now()
            );
            """
        ),
        {
            "fpo_id": str(fpo_id),
            "user_id": str(user_id),
        },
    )

    conn.execute(text("DELETE FROM public.fpo_profile_commodities WHERE fpo_id = :fpo_id"), {"fpo_id": str(fpo_id)})
    conn.execute(text("INSERT INTO public.fpo_profile_commodities (fpo_id, commodity_code, priority) SELECT :fpo_id, value, CASE WHEN ordinality = 1 THEN 'PRIMARY' ELSE 'SECONDARY' END FROM unnest(CAST(:commodities AS text[])) WITH ORDINALITY AS values(value, ordinality) ON CONFLICT DO NOTHING"), {"fpo_id": str(fpo_id), "commodities": values.get("main_commodities") or []})
    conn.execute(text("DELETE FROM public.fpo_profile_services WHERE fpo_id = :fpo_id"), {"fpo_id": str(fpo_id)})
    conn.execute(text("INSERT INTO public.fpo_profile_services (fpo_id, service_code) SELECT :fpo_id, value FROM unnest(CAST(:services AS text[])) AS values(value) ON CONFLICT DO NOTHING"), {"fpo_id": str(fpo_id), "services": values.get("services_provided") or []})

    created = get_fpo_by_id(conn, fpo_id)

    if created is None:
        raise RuntimeError(
            "FPO could not be read after creation."
        )

    created["current_user_fpo_role"] = "owner"
    return created


def ensure_fpo_organization_for_profile(
    conn: Connection,
    *,
    user_id: UUID | str,
    profile_fpo_id: UUID | str,
    state_name: str | None,
) -> dict[str, Any]:
    """Link a direct FPO profile setup to its organization identity.

    Auth-event provisioning normally creates this row first. Direct signup
    setup must also be safe when that event is delayed or was not delivered.
    """
    current = conn.execute(text("""
        SELECT fpo_id, profile_fpo_id, public_fpo_id, provisioning_status,
               provisioning_step
        FROM public.fpo_organizations
        WHERE auth_user_id = :user_id
        FOR UPDATE
    """), {"user_id": str(user_id)}).mappings().first()
    if current:
        if current["profile_fpo_id"] and str(current["profile_fpo_id"]) != str(profile_fpo_id):
            raise ValueError("FPO_PROFILE_LINK_CONFLICT")
        row = conn.execute(text("""
            UPDATE public.fpo_organizations
            SET profile_fpo_id = :profile_fpo_id,
                provisioning_status = 'READY', provisioning_step = 'COMPLETED',
                provisioning_error = NULL, provisioning_error_code = NULL,
                updated_at = now(), version = version + 1
            WHERE fpo_id = :organization_id
            RETURNING fpo_id, public_fpo_id, provisioning_status, provisioning_step,
                      profile_fpo_id
        """), {"organization_id": str(current["fpo_id"]), "profile_fpo_id": str(profile_fpo_id)}).mappings().one()
        return dict(row)

    state_code = conn.execute(text("""
        SELECT state_code FROM public.states
        WHERE lower(state_name) = lower(:state_name)
        ORDER BY state_code LIMIT 1
    """), {"state_name": state_name or "Odisha"}).scalar() or 21
    sequence = int(conn.execute(text("SELECT nextval('public.fpo_public_number_seq')")).scalar_one())
    row = conn.execute(text("""
        INSERT INTO public.fpo_organizations
            (auth_user_id, public_fpo_id, lifecycle_status, provisioning_status,
             provisioning_step, verification_status, profile_fpo_id)
        VALUES (:user_id, :public_fpo_id, 'ONBOARDING', 'READY', 'COMPLETED',
                'PROFILE_INCOMPLETE', :profile_fpo_id)
        RETURNING fpo_id, public_fpo_id, provisioning_status, provisioning_step,
                  profile_fpo_id
    """), {
        "user_id": str(user_id),
        "public_fpo_id": _public_fpo_id(int(state_code), sequence),
        "profile_fpo_id": str(profile_fpo_id),
    }).mappings().one()
    return dict(row)


def update_fpo_profile(
    conn: Connection,
    *,
    fpo_id: UUID | str,
    values: dict[str, Any],
    profile_complete: bool,
    expected_profile_version: int | None = None,
    change_classification: str = "SAFE",
) -> dict[str, Any] | None:
    result = conn.execute(
        text(
            """
            UPDATE fpos
            SET
                legal_name = COALESCE(:legal_name, legal_name),
                display_name = COALESCE(:display_name, display_name),
                organisation_type = COALESCE(:organisation_type, organisation_type),
                cin = COALESCE(:cin, cin),
                gstin = COALESCE(:gstin, gstin),
                website_url = COALESCE(:website_url, website_url),
                organisation_description = COALESCE(:organisation_description, organisation_description),
                operating_since_year = COALESCE(:operating_since_year, operating_since_year),
                registered_address_line_1 = COALESCE(:registered_address_line_1, registered_address_line_1),
                registered_address_line_2 = COALESCE(:registered_address_line_2, registered_address_line_2),
                women_member_count = COALESCE(:women_member_count, women_member_count),
                small_marginal_member_count = COALESCE(:small_marginal_member_count, small_marginal_member_count),
                declared_area_acres = COALESCE(:declared_area_acres, declared_area_acres),
                fpo_name = :fpo_name,
                registration_number = :registration_number,
                registration_type = :registration_type,
                registration_authority = :registration_authority,
                date_of_registration =
                    :date_of_registration,
                promoted_by = :promoted_by,
                promoting_institution_name =
                    :promoting_institution_name,

                contact_person_name =
                    :contact_person_name,
                contact_person_designation =
                    :contact_person_designation,
                contact_phone = :contact_phone,
                alternate_phone = :alternate_phone,
                contact_email = :contact_email,
                preferred_language = :preferred_language,

                state_name = :state_name,
                district_name = :district_name,
                district_code = :district_code,
                block_name = :block_name,
                block_code = :block_code,
                village_name = :village_name,
                gram_panchayat = :gram_panchayat,
                pincode = :pincode,
                postal_code = :postal_code,
                state_code = :state_code,
                village_code = :village_code,
                gram_panchayat_code = :gram_panchayat_code,
                gram_panchayat_name = :gram_panchayat_name,
                office_address = :office_address,

                main_commodities = :main_commodities,
                member_count = :member_count,
                active_member_count =
                    :active_member_count,
                female_member_count = :female_member_count,
                year_established = :year_established,
                services_provided =
                    :services_provided,

                profile_image_url =
                    :profile_image_url,

                onboarding_completed_at = CASE
                    WHEN :profile_complete
                    THEN COALESCE(
                        onboarding_completed_at,
                        now()
                    )
                    ELSE NULL
                END,

                profile_version = profile_version + 1,
                verification_refresh_required = CASE
                    WHEN :change_classification = 'REVERIFICATION_REQUIRED' THEN TRUE
                    ELSE verification_refresh_required
                END,
                updated_at = now()

            WHERE fpo_id = :fpo_id
              AND is_active = TRUE
              AND (:expected_profile_version IS NULL OR profile_version = :expected_profile_version);
            """
        ),
        {
            **values,
            "fpo_id": str(fpo_id),
            "profile_complete": profile_complete,
            "expected_profile_version": expected_profile_version,
            "change_classification": change_classification,
        },
    )

    if result.rowcount == 0:
        return None

    return get_fpo_by_id(conn, fpo_id)


def list_fpo_farmers(
    conn: Connection,
    fpo_id: UUID | str,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            f"""
            SELECT {FARMER_SELECT}
            FROM farmer_profiles fp
            JOIN users u
              ON u.user_id = fp.user_id
            WHERE fp.fpo_id = :fpo_id
              AND fp.is_active = TRUE
            ORDER BY fp.full_name ASC;
            """
        ),
        {"fpo_id": str(fpo_id)},
    ).mappings().all()

    return [dict(row) for row in rows]


def record_profile_audit_event(
    conn: Connection,
    *,
    entity_type: str,
    entity_id: UUID | str,
    subject_user_id: UUID | str | None,
    actor_user_id: UUID | str | None,
    event_type: str,
    changed_fields: list[str],
    correlation_id: str,
    ip_address: str | None,
) -> None:
    conn.execute(
        text(
            """
            INSERT INTO profile_audit_events (
                entity_type,
                entity_id,
                subject_user_id,
                actor_user_id,
                event_type,
                changed_fields,
                correlation_id,
                ip_address,
                created_at
            )
            VALUES (
                :entity_type,
                :entity_id,
                :subject_user_id,
                :actor_user_id,
                :event_type,
                CAST(:changed_fields AS jsonb),
                :correlation_id,
                CAST(:ip_address AS inet),
                now()
            );
            """
        ),
        {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "subject_user_id": (
                str(subject_user_id)
                if subject_user_id
                else None
            ),
            "actor_user_id": (
                str(actor_user_id)
                if actor_user_id
                else None
            ),
            "event_type": event_type,
            "changed_fields": json.dumps(
                {
                    "fields": sorted(
                        set(changed_fields)
                    )
                }
            ),
            "correlation_id": correlation_id,
            "ip_address": ip_address,
        },
    )


def record_profile_change(
    conn: Connection,
    *,
    profile_id: UUID | str,
    organization_id: UUID | str | None,
    actor_user_id: UUID | str | None,
    previous_version: int,
    new_version: int,
    changed_fields: list[str],
    classification: str,
    correlation_id: str,
) -> None:
    fields_json = json.dumps(sorted(set(changed_fields)))
    conn.execute(text("""
        INSERT INTO public.fpo_profile_change_history
            (profile_id, actor_user_id, previous_profile_version, new_profile_version,
             changed_fields, change_classification, correlation_id)
        VALUES (:profile_id, :actor_user_id, :previous_version, :new_version,
                CAST(:changed_fields AS jsonb), :classification, :correlation_id)
    """), {
        "profile_id": str(profile_id),
        "actor_user_id": str(actor_user_id) if actor_user_id else None,
        "previous_version": previous_version,
        "new_version": new_version,
        "changed_fields": fields_json,
        "classification": classification,
        "correlation_id": correlation_id,
    })
    conn.execute(text("""
        INSERT INTO public.fpo_profile_events
            (event_type, profile_id, organization_id, actor_user_id, correlation_id,
             profile_version, changed_fields, payload)
        VALUES (:event_type, :profile_id, :organization_id, :actor_user_id, :correlation_id,
                :profile_version, CAST(:changed_fields AS jsonb), CAST(:payload AS jsonb))
    """), {
        "event_type": "fpo.profile.updated",
        "profile_id": str(profile_id),
        "organization_id": str(organization_id) if organization_id else None,
        "actor_user_id": str(actor_user_id) if actor_user_id else None,
        "correlation_id": correlation_id,
        "profile_version": new_version,
        "changed_fields": fields_json,
        "payload": json.dumps({
            "profile_id": str(profile_id),
            "organization_id": str(organization_id) if organization_id else None,
            "profile_version": new_version,
            "changed_fields": sorted(set(changed_fields)),
            "change_classification": classification,
        }),
    })


def list_profile_history(conn: Connection, profile_id: UUID | str, limit: int = 100) -> list[dict[str, Any]]:
    rows = conn.execute(text("""
        SELECT history_id, profile_id, actor_user_id, previous_profile_version,
               new_profile_version, changed_fields, change_classification,
               correlation_id, request_channel, created_at
        FROM public.fpo_profile_change_history
        WHERE profile_id = :profile_id
        ORDER BY created_at DESC
        LIMIT :limit
    """), {"profile_id": str(profile_id), "limit": limit}).mappings().all()
    result = []
    for row in rows:
        item = dict(row)
        item["changed_fields"] = item.get("changed_fields") or []
        result.append(item)
    return result
