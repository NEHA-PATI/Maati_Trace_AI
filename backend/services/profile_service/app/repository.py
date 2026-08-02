from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection


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
    f.fpo_name,
    f.registration_number,
    f.registration_type,
    f.date_of_registration,
    f.promoted_by,
    f.promoting_institution_name,
    f.contact_person_name,
    f.contact_person_designation,
    f.contact_phone,
    f.alternate_phone,
    f.contact_email,
    f.state_name,
    f.district_name,
    f.district_code,
    f.block_name,
    f.block_code,
    f.village_name,
    f.gram_panchayat,
    f.pincode,
    f.office_address,
    f.main_commodities,
    f.member_count,
    f.active_member_count,
    f.services_provided,
    f.verification_status,
    f.profile_image_url,
    f.is_active,
    f.created_at,
    f.updated_at,
    f.profile_version,
    f.onboarding_completed_at
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
    phone_number: str | None,
    profile_image_url: str | None,
    onboarding_status: str,
) -> None:
    conn.execute(
        text(
            """
            UPDATE users
            SET
                full_name = :full_name,
                phone_number = :phone_number,
                profile_image_url = :profile_image_url,
                onboarding_status = :onboarding_status,
                updated_at = now()
            WHERE user_id = :user_id;
            """
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
            WHERE f.fpo_id = :fpo_id
              AND f.is_active = TRUE
            LIMIT 1;
            """
        ),
        {"fpo_id": str(fpo_id)},
    ).mappings().first()

    return _dict(row)


def create_fpo_with_membership(
    conn: Connection,
    *,
    user_id: UUID | str,
    values: dict[str, Any],
) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            INSERT INTO fpos (
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

                state_name,
                district_name,
                district_code,
                block_name,
                block_code,
                village_name,
                gram_panchayat,
                pincode,
                office_address,

                main_commodities,
                member_count,
                active_member_count,
                services_provided,

                verification_status,
                profile_image_url,
                onboarding_completed_at,
                profile_version,
                is_active
            )
            VALUES (
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

                :state_name,
                :district_name,
                :district_code,
                :block_name,
                :block_code,
                :village_name,
                :gram_panchayat,
                :pincode,
                :office_address,

                :main_commodities,
                :member_count,
                :active_member_count,
                :services_provided,

                'pending',
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

    created = get_fpo_by_id(conn, fpo_id)

    if created is None:
        raise RuntimeError(
            "FPO could not be read after creation."
        )

    created["current_user_fpo_role"] = "owner"
    return created


def update_fpo_profile(
    conn: Connection,
    *,
    fpo_id: UUID | str,
    values: dict[str, Any],
    profile_complete: bool,
) -> dict[str, Any] | None:
    conn.execute(
        text(
            """
            UPDATE fpos
            SET
                fpo_name = :fpo_name,
                registration_number = :registration_number,
                registration_type = :registration_type,
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

                state_name = :state_name,
                district_name = :district_name,
                district_code = :district_code,
                block_name = :block_name,
                block_code = :block_code,
                village_name = :village_name,
                gram_panchayat = :gram_panchayat,
                pincode = :pincode,
                office_address = :office_address,

                main_commodities = :main_commodities,
                member_count = :member_count,
                active_member_count =
                    :active_member_count,
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
                updated_at = now()

            WHERE fpo_id = :fpo_id
              AND is_active = TRUE;
            """
        ),
        {
            **values,
            "fpo_id": str(fpo_id),
            "profile_complete": profile_complete,
        },
    )

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
