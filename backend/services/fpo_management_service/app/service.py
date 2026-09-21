from __future__ import annotations

import logging

from shared.db.postgres import engine
from services.fpo_management_service.app.config import FpoManagementConfig
from services.fpo_management_service.app.repository import (
    claim_events,
    get_bootstrap_status,
    get_portal_bootstrap,
    mark_failed,
    mark_published,
    provision_fpo,
    get_verification_for_user,
    list_verification_queue,
    review_verification,
    submit_verification,
    create_farmer_relationship_request,
    decide_farmer_relationship,
    discover_fpos,
    list_farmer_relationships,
    list_fpo_relationships,
    revoke_farmer_relationship,
    assign_fpo_class,
    list_feature_catalogue,
    resolve_fpo_entitlements,
    require_fpo_feature,
    create_feature_override,
    list_feature_overrides,
    reconcile_fpo_data,
    fpo_portfolio_report,
    list_fpo_alerts,
    acknowledge_fpo_alert,
    get_fpo_dashboard_read_model,
    list_fpo_farmer_portfolio,
)

logger = logging.getLogger("fpo_management_service")


def process_batch(batch_size: int) -> int:
    processed = 0
    with engine.begin() as conn:
        events = claim_events(conn, batch_size=batch_size)
    for event in events:
        try:
            with engine.begin() as conn:
                if event["event_type"] == "auth.user.created":
                    payload = event["payload"] if isinstance(event["payload"], dict) else {}
                    if payload.get("account_type") == "fpo":
                        provision_fpo(conn, payload)
                mark_published(conn, event["event_id"])
                processed += 1
        except Exception as exc:
            logger.exception("fpo_provisioning_failed", extra={"event_id": str(event["event_id"])})
            with engine.begin() as conn:
                mark_failed(conn, event["event_id"], str(exc))
    return processed


def bootstrap_status(user_id):
    with engine.connect() as conn:
        return get_bootstrap_status(conn, user_id)


def portal_bootstrap(user_id):
    with engine.connect() as conn:
        return get_portal_bootstrap(conn, user_id)


def verification_status(user_id):
    with engine.connect() as conn:
        return get_verification_for_user(conn, user_id)


def submit_verification_request(user_id):
    with engine.begin() as conn:
        return submit_verification(conn, user_id)


def review_verification_request(fpo_id, reviewer_user_id, status, note):
    with engine.begin() as conn:
        return review_verification(
            conn,
            fpo_id=fpo_id,
            reviewer_user_id=reviewer_user_id,
            status=status,
            note=note,
        )


def verification_queue(status: str | None = None):
    with engine.connect() as conn:
        return list_verification_queue(conn, status=status)


def discover_fpo_directory(query: str | None = None, limit: int = 25):
    with engine.connect() as conn:
        return discover_fpos(conn, query=query, limit=limit)


def request_farmer_relationship(farmer_user_id, fpo_id):
    with engine.begin() as conn:
        return create_farmer_relationship_request(conn, farmer_user_id=farmer_user_id, fpo_id=fpo_id)


def farmer_relationships(farmer_user_id):
    with engine.connect() as conn:
        return list_farmer_relationships(conn, farmer_user_id=farmer_user_id)


def fpo_relationships(fpo_user_id):
    with engine.connect() as conn:
        require_fpo_feature(conn, user_id=fpo_user_id, feature_key="FARMER_DIRECTORY")
        return list_fpo_relationships(conn, fpo_user_id=fpo_user_id)


def decide_relationship(fpo_user_id, relationship_id, decision):
    with engine.begin() as conn:
        require_fpo_feature(conn, user_id=fpo_user_id, feature_key="FARMER_DIRECTORY")
        return decide_farmer_relationship(
            conn,
            fpo_user_id=fpo_user_id,
            relationship_id=relationship_id,
            decision=decision,
        )


def revoke_relationship(farmer_user_id, relationship_id):
    with engine.begin() as conn:
        return revoke_farmer_relationship(
            conn,
            farmer_user_id=farmer_user_id,
            relationship_id=relationship_id,
        )


def fpo_entitlements(user_id):
    with engine.connect() as conn:
        return resolve_fpo_entitlements(conn, user_id=user_id)


def feature_catalogue():
    with engine.connect() as conn:
        return list_feature_catalogue(conn)


def assign_class(fpo_id, class_code, admin_user_id):
    with engine.begin() as conn:
        return assign_fpo_class(conn, fpo_id=fpo_id, class_code=class_code, admin_user_id=admin_user_id)


def create_fpo_feature_override(fpo_id, feature_key, enabled, reason, expires_at, admin_user_id):
    with engine.begin() as conn:
        return create_feature_override(
            conn,
            fpo_id=fpo_id,
            feature_key=feature_key,
            enabled=enabled,
            reason=reason,
            expires_at=expires_at,
            admin_user_id=admin_user_id,
        )


def fpo_feature_overrides(fpo_id):
    with engine.connect() as conn:
        return list_feature_overrides(conn, fpo_id=fpo_id)


def run_fpo_reconciliation(admin_user_id):
    with engine.begin() as conn:
        return reconcile_fpo_data(conn, admin_user_id=admin_user_id)


def portfolio_report(user_id):
    with engine.connect() as conn:
        return fpo_portfolio_report(conn, user_id=user_id)


def operational_alerts(user_id, status=None):
    with engine.connect() as conn:
        return list_fpo_alerts(conn, user_id=user_id, status=status)


def acknowledge_alert(user_id, alert_id):
    with engine.begin() as conn:
        return acknowledge_fpo_alert(conn, user_id=user_id, alert_id=alert_id)


def dashboard_read_model(user_id):
    with engine.connect() as conn:
        return get_fpo_dashboard_read_model(conn, user_id=user_id)


def farmer_directory(user_id, query=None, district_code=None, block_code=None, relationship_status=None, cursor=None, limit=50):
    with engine.connect() as conn:
        return list_fpo_farmer_portfolio(conn, user_id=user_id, query=query, district_code=district_code, block_code=block_code, relationship_status=relationship_status, cursor=cursor, limit=limit)
