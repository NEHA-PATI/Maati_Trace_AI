from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from urllib.parse import urlencode
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from shared.db.postgres import engine
from services.auth_service.app.audit import record_audit_event
from services.auth_service.app.config_validation import get_auth_config
from services.auth_service.app.dependencies import RequestContext
from services.auth_service.app.errors import AuthError
from services.auth_service.app.google_oauth import verify_google_id_token
from services.auth_service.app.logging_context import get_correlation_id, get_logger, log_event
from services.auth_service.app.mail import queue_email
from services.auth_service.app.password_breach import assert_password_not_breached
from services.auth_service.app.repository import (
    count_fpo_access_requests,
    create_account_invitation,
    create_fpo_access_request,
    create_password_reset_session,
    create_refresh_token,
    create_signup_session,
    create_user,
    create_farmer_profile_stub,
    get_account_invitation_by_hash,
    get_auth_identity,
    get_fpo_access_request_for_update,
    get_password_reset_session_for_update,
    get_refresh_token_for_update,
    get_signup_session,
    get_user_by_email,
    get_user_by_id,
    get_user_by_phone,
    invalidate_active_invitations,
    invalidate_active_password_reset_sessions,
    invalidate_active_signup_sessions,
    invalidate_signup_session,
    list_fpo_access_requests,
    link_auth_identity,
    mark_account_invitation_accepted,
    mark_password_reset_used,
    mark_refresh_reused_and_revoke_family,
    mark_signup_completed,
    mark_signup_verified,
    mark_user_login,
    register_invalid_otp_attempt,
    review_fpo_access_request,
    revoke_all_refresh_tokens_for_user,
    revoke_refresh_family,
    revoke_refresh_session,
    rotate_refresh_token,
    update_password_hash,
    update_signup_otp_for_resend,
)
from services.auth_service.app.schemas import (
    FpoAccessRequestCreate,
    FpoAccessReviewRequest,
    InvitationAcceptRequest,
    InvitationCreateRequest,
    LoginRequest,
    PasswordForgotRequest,
    PasswordResetRequest,
    SignupStartRequest,
)
logger = get_logger(__name__)


def _database_error_details(exc: Exception) -> dict[str, Any]:
    details: dict[str, Any] = {
        "exception_type": type(exc).__name__,
        "message": str(exc),
    }
    orig = getattr(exc, "orig", None)
    if orig is None:
        return details

    details["orig_type"] = type(orig).__name__
    details["orig_message"] = str(orig)

    for attr in ("pgcode", "sqlstate"):
        value = getattr(orig, attr, None)
        if value:
            details[attr] = value

    diag = getattr(orig, "diag", None)
    if diag is None:
        return details

    for attr in (
        "constraint_name",
        "table_name",
        "column_name",
        "schema_name",
        "message_primary",
        "message_detail",
        "message_hint",
    ):
        value = getattr(diag, attr, None)
        if value:
            details[attr] = value

    return details


def _database_error_summary(exc: Exception) -> str:
    details = _database_error_details(exc)
    parts = [
        details.get("exception_type"),
        details.get("pgcode") or details.get("sqlstate"),
        details.get("table_name"),
        details.get("column_name"),
        details.get("constraint_name"),
        details.get("message_primary"),
    ]
    return " | ".join(str(part) for part in parts if part)


def _signup_integrity_error(stage: str, exc: IntegrityError) -> AuthError:
    details = _database_error_details(exc)
    log_event(
        logger,
        logging.ERROR,
        "signup_complete_db_error",
        stage=stage,
        database_error=details,
    )

    pgcode = details.get("pgcode") or details.get("sqlstate")
    if stage == "create_user" and pgcode == "23505":
        return AuthError(
            "SIGNUP_UNAVAILABLE",
            "An account cannot be created with these details. Try signing in or resetting the password.",
            409,
            internal_message=_database_error_summary(exc),
        )

    return AuthError(
        "SIGNUP_COMPLETE_FAILED",
        "Signup could not be completed. Try again.",
        500,
        internal_message=_database_error_summary(exc),
    )


from services.auth_service.app.security import (
    assert_password_policy,
    create_access_token,
    create_csrf_token,
    create_opaque_token,
    create_refresh_token_plain,
    create_six_digit_otp,
    hash_invitation_token,
    hash_otp,
    hash_password,
    hash_password_reset_token,
    hash_refresh_token,
    invitation_expiry,
    normalize_email,
    password_reset_expiry,
    refresh_token_expiry,
    utc_now,
    verify_otp_hash,
    verify_password_detailed,
)


@dataclass(frozen=True, slots=True)
class IssuedSession:
    access_token: str
    refresh_token: str
    csrf_token: str
    user: dict[str, Any]
    session_id: str


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_id": user["user_id"],
        "full_name": user.get("full_name") or user.get("email") or "MaatiTrace User",
        "email": user.get("email"),
        "phone_number": user.get("phone_number"),
        "role": user["role"],
        "is_active": bool(user.get("is_active")),
        "is_verified": bool(user.get("is_verified")),
        "onboarding_status": user.get("onboarding_status"),
        "profile_image_url": user.get("profile_image_url"),
    }


def _mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        masked_local = local[:1] + "*"
    else:
        masked_local = local[:2] + "*" * max(2, len(local) - 2)
    return f"{masked_local}@{domain}"


def _issue_session(conn, user: dict[str, Any], context: RequestContext) -> IssuedSession:
    session_id = uuid4()
    token_family_id = uuid4()
    refresh_plain = create_refresh_token_plain()
    refresh_hash = hash_refresh_token(refresh_plain)
    create_refresh_token(
        conn,
        user_id=user["user_id"],
        token_hash=refresh_hash,
        expires_at=refresh_token_expiry(),
        token_family_id=token_family_id,
        session_id=session_id,
        parent_refresh_token_id=None,
        device_id_hash=context.device_id_hash,
        issued_ip=context.ip_address,
        user_agent_hash=context.user_agent_hash,
    )
    return IssuedSession(
        access_token=create_access_token(user, session_id),
        refresh_token=refresh_plain,
        csrf_token=create_csrf_token(),
        user=_public_user(user),
        session_id=str(session_id),
    )


def start_signup(payload: SignupStartRequest, context: RequestContext) -> dict[str, Any]:
    config = get_auth_config()
    if not config.mail_enabled:
        raise AuthError("MAIL_NOT_CONFIGURED", "Email verification is temporarily unavailable.", 503)

    assert_password_policy(payload.password)
    assert_password_not_breached(payload.password)
    email = normalize_email(str(payload.email))
    signup_session_id = uuid4()
    otp = create_six_digit_otp()
    otp_hash = hash_otp(signup_session_id, otp)
    expires_at = utc_now() + timedelta(minutes=config.signup_otp_expire_minutes)
    password_hash = hash_password(payload.password)

    with engine.connect() as conn:
        account_exists = (
            get_user_by_email(conn, email) is not None
            or get_user_by_phone(conn, payload.phone_number) is not None
        )
    if account_exists:
        record_audit_event(
            event_type="signup_started",
            outcome="rejected_existing_account",
            identifier=email,
            ip_address=context.ip_address,
            device_id_hash=context.device_id_hash,
            user_agent_hash=context.user_agent_hash,
        )
        raise AuthError(
            "SIGNUP_UNAVAILABLE",
            "An account cannot be created with these details. Try signing in or resetting the password.",
            409,
        )

    try:
        with engine.begin() as conn:
            invalidated = invalidate_active_signup_sessions(
                conn,
                email=email,
                phone_number=payload.phone_number,
                reason="superseded_by_new_signup",
                superseded_by_session_id=signup_session_id,
            )
            session = create_signup_session(
                conn,
                signup_session_id=signup_session_id,
                full_name=payload.full_name,
                email=email,
                phone_number=payload.phone_number,
                password_hash=password_hash,
                otp_hash=otp_hash,
                otp_expires_at=expires_at,
                created_ip=context.ip_address,
                device_id_hash=context.device_id_hash,
                correlation_id=get_correlation_id(),
            )
            queue_email(
                conn,
                to_email=email,
                to_name=payload.full_name,
                template_key="signup_otp",
                template_data={
                    "full_name": payload.full_name,
                    "otp": otp,
                    "expires_minutes": config.signup_otp_expire_minutes,
                },
                public_metadata={"signup_session_id": str(signup_session_id)},
            )
            if invalidated:
                record_audit_event(
                    event_type="signup_session_invalidated",
                    outcome="success",
                    signup_session_id=signup_session_id,
                    identifier=email,
                    metadata={"count": invalidated, "reason": "superseded_by_new_signup"},
                    conn=conn,
                )
            record_audit_event(
                event_type="otp_requested",
                outcome="success",
                signup_session_id=signup_session_id,
                identifier=email,
                ip_address=context.ip_address,
                device_id_hash=context.device_id_hash,
                user_agent_hash=context.user_agent_hash,
                conn=conn,
            )
    except AuthError:
        raise
    except IntegrityError as exc:
        raise AuthError(
            "SIGNUP_UNAVAILABLE",
            "An account cannot be created with these details. Try signing in or resetting the password.",
            409,
            internal_message=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        raise AuthError(
            "SIGNUP_START_FAILED",
            "Signup could not be started. Try again.",
            500,
            internal_message=str(exc),
        ) from exc

    return {
        "signup_session_id": session["signup_session_id"],
        "expires_in_seconds": config.signup_otp_expire_minutes * 60,
        "resend_available_in_seconds": config.signup_otp_resend_cooldown_seconds,
        "masked_email": _mask_email(email),
    }


def resend_signup_otp(signup_session_id: UUID | str, context: RequestContext) -> dict[str, Any]:
    config = get_auth_config()
    now = utc_now()
    otp = create_six_digit_otp()
    expires_at = now + timedelta(minutes=config.signup_otp_expire_minutes)

    with engine.begin() as conn:
        session = get_signup_session(conn, signup_session_id, for_update=True)
        if session is None or session.get("invalidated_at") or session.get("completed_at"):
            raise AuthError("INVALID_SIGNUP_SESSION", "This signup session is no longer valid.", 400)
        if session.get("verified_at"):
            raise AuthError("OTP_ALREADY_VERIFIED", "This email has already been verified.", 409)

        resend_count = int(session.get("resend_count") or 0)
        if resend_count >= config.signup_otp_max_resends:
            raise AuthError("OTP_RESEND_LIMIT", "The resend limit has been reached. Start signup again.", 429)

        last_sent_at = session.get("last_sent_at")
        if last_sent_at:
            elapsed = int((now - last_sent_at).total_seconds())
            remaining = config.signup_otp_resend_cooldown_seconds - elapsed
            if remaining > 0:
                raise AuthError(
                    "OTP_RESEND_COOLDOWN",
                    "Wait before requesting another code.",
                    429,
                    retry_after=remaining,
                )

        new_hash = hash_otp(signup_session_id, otp)
        update_signup_otp_for_resend(
            conn,
            signup_session_id=signup_session_id,
            otp_hash=new_hash,
            otp_expires_at=expires_at,
        )
        queue_email(
            conn,
            to_email=session["email"],
            to_name=session["full_name"],
            template_key="signup_otp",
            template_data={
                "full_name": session["full_name"],
                "otp": otp,
                "expires_minutes": config.signup_otp_expire_minutes,
            },
            public_metadata={"signup_session_id": str(signup_session_id), "resend": resend_count + 1},
        )
        record_audit_event(
            event_type="otp_resent",
            outcome="success",
            signup_session_id=signup_session_id,
            identifier=session["email"],
            ip_address=context.ip_address,
            device_id_hash=context.device_id_hash,
            user_agent_hash=context.user_agent_hash,
            metadata={"resend_count": resend_count + 1},
            conn=conn,
        )

    return {
        "signup_session_id": signup_session_id,
        "expires_in_seconds": config.signup_otp_expire_minutes * 60,
        "resend_available_in_seconds": config.signup_otp_resend_cooldown_seconds,
        "resends_remaining": config.signup_otp_max_resends - (resend_count + 1),
    }


def verify_signup_otp(signup_session_id: UUID | str, otp: str, context: RequestContext) -> dict[str, Any]:
    config = get_auth_config()
    now = utc_now()
    failure: AuthError | None = None
    already_verified = False

    with engine.begin() as conn:
        session = get_signup_session(conn, signup_session_id, for_update=True)
        if session is None or session.get("invalidated_at") or session.get("completed_at"):
            failure = AuthError("INVALID_SIGNUP_SESSION", "This signup session is no longer valid.", 400)
        elif session.get("locked_at"):
            failure = AuthError("OTP_LOCKED", "Too many incorrect codes. Start signup again.", 423)
        elif session.get("verified_at"):
            already_verified = True
        elif session["otp_expires_at"] <= now:
            failure = AuthError("OTP_EXPIRED", "The verification code has expired.", 400)
        elif not verify_otp_hash(signup_session_id, otp, session["otp_hash"]):
            attempts = int(session.get("attempts") or 0) + 1
            should_lock = attempts >= config.signup_otp_max_attempts
            register_invalid_otp_attempt(
                conn,
                signup_session_id=signup_session_id,
                lock=should_lock,
            )
            record_audit_event(
                event_type="otp_locked" if should_lock else "otp_verification_failed",
                outcome="failure",
                signup_session_id=signup_session_id,
                identifier=session["email"],
                ip_address=context.ip_address,
                device_id_hash=context.device_id_hash,
                user_agent_hash=context.user_agent_hash,
                metadata={"attempt": attempts},
                conn=conn,
            )
            failure = AuthError(
                "OTP_LOCKED" if should_lock else "INVALID_OTP",
                "Too many incorrect codes. Start signup again." if should_lock else "The verification code is incorrect.",
                423 if should_lock else 400,
            )
        else:
            mark_signup_verified(conn, signup_session_id)
            record_audit_event(
                event_type="otp_verified",
                outcome="success",
                signup_session_id=signup_session_id,
                identifier=session["email"],
                ip_address=context.ip_address,
                device_id_hash=context.device_id_hash,
                user_agent_hash=context.user_agent_hash,
                conn=conn,
            )

    if failure:
        raise failure
    return {"signup_session_id": signup_session_id, "verified": True}


def cancel_signup(signup_session_id: UUID | str, reason: str, context: RequestContext) -> dict[str, bool]:
    with engine.begin() as conn:
        session = get_signup_session(conn, signup_session_id, for_update=True)
        if session and not session.get("completed_at"):
            invalidate_signup_session(conn, signup_session_id, reason)
            record_audit_event(
                event_type="signup_session_invalidated",
                outcome="success",
                signup_session_id=signup_session_id,
                identifier=session.get("email"),
                ip_address=context.ip_address,
                device_id_hash=context.device_id_hash,
                user_agent_hash=context.user_agent_hash,
                metadata={"reason": reason},
                conn=conn,
            )
    return {"cancelled": True}


def complete_signup(signup_session_id: UUID | str, context: RequestContext) -> IssuedSession:
    now = utc_now()
    try:
        with engine.begin() as conn:
            session = get_signup_session(conn, signup_session_id, for_update=True)
            if session is None or session.get("invalidated_at"):
                raise AuthError("INVALID_SIGNUP_SESSION", "This signup session is no longer valid.", 400)
            if session.get("completed_at"):
                raise AuthError("SIGNUP_ALREADY_COMPLETED", "This signup has already been completed.", 409)
            if session.get("locked_at"):
                raise AuthError("OTP_LOCKED", "Too many incorrect codes. Start signup again.", 423)
            if not session.get("verified_at"):
                raise AuthError("OTP_REQUIRED", "Verify your email before completing signup.", 400)
            if session["otp_expires_at"] <= now:
                raise AuthError("OTP_EXPIRED", "The verification code has expired.", 400)

            try:
                user = create_user(
                    conn,
                    full_name=session["full_name"],
                    email=session["email"],
                    phone_number=session["phone_number"],
                    password_hash=session["password_hash"],
                    role="farmer",
                    is_verified=True,
                )
            except IntegrityError as exc:
                raise _signup_integrity_error("create_user", exc) from exc

            try:
                create_farmer_profile_stub(
                    conn,
                    user_id=user["user_id"],
                    full_name=user["full_name"],
                    phone_number=user.get("phone_number"),
                )
            except IntegrityError as exc:
                raise _signup_integrity_error("create_farmer_profile_stub", exc) from exc
            mark_signup_completed(conn, signup_session_id)
            mark_user_login(conn, user["user_id"])
            issued = _issue_session(conn, user, context)
            record_audit_event(
                event_type="signup_completed",
                outcome="success",
                user_id=user["user_id"],
                signup_session_id=signup_session_id,
                auth_session_id=issued.session_id,
                identifier=session["email"],
                ip_address=context.ip_address,
                device_id_hash=context.device_id_hash,
                user_agent_hash=context.user_agent_hash,
                conn=conn,
            )
            return issued
    except AuthError:
        raise
    except IntegrityError as exc:
        raise _signup_integrity_error("signup_complete", exc) from exc
    except SQLAlchemyError as exc:
        log_event(
            logger,
            logging.ERROR,
            "signup_complete_db_error",
            stage="signup_complete",
            database_error=_database_error_details(exc),
        )
        raise AuthError(
            "SIGNUP_COMPLETE_FAILED",
            "Signup could not be completed. Try again.",
            500,
            internal_message=_database_error_summary(exc),
        ) from exc


def _record_login_failure(identifier: str, context: RequestContext, outcome: str) -> None:
    try:
        record_audit_event(
            event_type="login_failed",
            outcome=outcome,
            identifier=identifier,
            ip_address=context.ip_address,
            device_id_hash=context.device_id_hash,
            user_agent_hash=context.user_agent_hash,
        )
    except Exception:
        logger.exception("Failed to record login failure audit event")


def login(payload: LoginRequest, context: RequestContext) -> IssuedSession:
    identifier = payload.resolved_identifier()
    with engine.connect() as conn:
        user = get_user_by_email(conn, identifier) if "@" in identifier else get_user_by_phone(conn, identifier)

    if user is None or not user.get("is_active"):
        _record_login_failure(identifier, context, "invalid_credentials")
        raise AuthError("INVALID_CREDENTIALS", "Invalid email/phone or password.", 401)

    verification = verify_password_detailed(payload.password, user.get("password_hash"))
    if not verification.valid:
        _record_login_failure(identifier, context, "invalid_credentials")
        raise AuthError("INVALID_CREDENTIALS", "Invalid email/phone or password.", 401)

    with engine.begin() as conn:
        locked_user = get_user_by_id(conn, user["user_id"], for_update=True)
        if locked_user is None or not locked_user.get("is_active"):
            raise AuthError("INVALID_CREDENTIALS", "Invalid email/phone or password.", 401)
        if verification.needs_rehash:
            update_password_hash(
                conn,
                locked_user["user_id"],
                hash_password(payload.password, enforce_policy=False),
            )
        mark_user_login(conn, locked_user["user_id"])
        issued = _issue_session(conn, locked_user, context)
        record_audit_event(
            event_type="login_succeeded",
            outcome="success",
            user_id=locked_user["user_id"],
            auth_session_id=issued.session_id,
            identifier=identifier,
            ip_address=context.ip_address,
            device_id_hash=context.device_id_hash,
            user_agent_hash=context.user_agent_hash,
            conn=conn,
        )
        return issued


def login_with_google(id_token_value: str, context: RequestContext) -> IssuedSession:
    claims = verify_google_id_token(id_token_value)
    provider_subject = str(claims["sub"])
    email = normalize_email(str(claims["email"]))

    try:
        with engine.begin() as conn:
            identity = get_auth_identity(
                conn,
                provider="google",
                provider_subject=provider_subject,
                for_update=True,
            )
            linked_new_identity = False
            if identity is not None:
                user = identity
            else:
                user = get_user_by_email(conn, email, for_update=True)
                if user is not None and not get_auth_config().google_auto_link_verified_email:
                    raise AuthError(
                        "ACCOUNT_LINK_REQUIRED",
                        "Sign in with your password before linking Google.",
                        409,
                    )
                if user is None:
                    user = create_user(
                        conn,
                        full_name=claims.get("name") or email,
                        email=email,
                        phone_number=None,
                        password_hash=None,
                        role="farmer",
                        is_verified=True,
                        profile_image_url=claims.get("picture"),
                    )

                if user["role"] == "farmer":
                    create_farmer_profile_stub(
                        conn,
                        user_id=user["user_id"],
                        full_name=user["full_name"],
                        phone_number=None,
                    )
                link_auth_identity(
                    conn,
                    user_id=user["user_id"],
                    provider="google",
                    provider_subject=provider_subject,
                    email=email,
                    email_verified=True,
                    raw_profile=claims,
                )
                linked_new_identity = True

            if not user.get("is_active"):
                raise AuthError("ACCOUNT_INACTIVE", "This account is inactive.", 403)
            mark_user_login(conn, user["user_id"])
            issued = _issue_session(conn, user, context)
            if linked_new_identity:
                record_audit_event(
                    event_type="google_identity_linked",
                    outcome="success",
                    user_id=user["user_id"],
                    identifier=email,
                    conn=conn,
                )
            record_audit_event(
                event_type="google_login_succeeded",
                outcome="success",
                user_id=user["user_id"],
                auth_session_id=issued.session_id,
                identifier=email,
                ip_address=context.ip_address,
                device_id_hash=context.device_id_hash,
                user_agent_hash=context.user_agent_hash,
                conn=conn,
            )
            return issued
    except AuthError:
        raise
    except SQLAlchemyError as exc:
        raise AuthError("GOOGLE_LOGIN_FAILED", "Google sign-in could not be completed.", 500, str(exc)) from exc


def refresh_session(refresh_token_plain: str, context: RequestContext) -> IssuedSession:
    old_hash = hash_refresh_token(refresh_token_plain)
    failure: AuthError | None = None
    issued: IssuedSession | None = None

    with engine.begin() as conn:
        row = get_refresh_token_for_update(conn, old_hash)
        if row is None:
            record_audit_event(
                event_type="refresh_failed",
                outcome="token_not_found",
                ip_address=context.ip_address,
                device_id_hash=context.device_id_hash,
                user_agent_hash=context.user_agent_hash,
                conn=conn,
            )
            failure = AuthError("INVALID_REFRESH_TOKEN", "Your session is invalid or expired.", 401)
        elif row.get("revoked_at") or row.get("replaced_by_refresh_token_id"):
            mark_refresh_reused_and_revoke_family(
                conn,
                refresh_token_id=row["refresh_token_id"],
                token_family_id=row["token_family_id"],
            )
            record_audit_event(
                event_type="refresh_token_reused",
                outcome="family_revoked",
                user_id=row["user_id"],
                auth_session_id=row["session_id"],
                ip_address=context.ip_address,
                device_id_hash=context.device_id_hash,
                user_agent_hash=context.user_agent_hash,
                conn=conn,
            )
            failure = AuthError("REFRESH_REUSE_DETECTED", "Your session was revoked for security.", 401)
        elif row["expires_at"] <= utc_now():
            revoke_refresh_family(conn, token_family_id=row["token_family_id"], reason="expired")
            record_audit_event(
                event_type="refresh_failed",
                outcome="expired",
                user_id=row["user_id"],
                auth_session_id=row["session_id"],
                conn=conn,
            )
            failure = AuthError("REFRESH_EXPIRED", "Your session has expired. Sign in again.", 401)
        else:
            user = get_user_by_id(conn, row["user_id"], for_update=True)
            if user is None or not user.get("is_active"):
                revoke_refresh_family(conn, token_family_id=row["token_family_id"], reason="user_inactive")
                failure = AuthError("ACCOUNT_INACTIVE", "This account is inactive.", 401)
            else:
                new_plain = create_refresh_token_plain()
                new_hash = hash_refresh_token(new_plain)
                replacement = create_refresh_token(
                    conn,
                    user_id=user["user_id"],
                    token_hash=new_hash,
                    expires_at=refresh_token_expiry(),
                    token_family_id=row["token_family_id"],
                    session_id=row["session_id"],
                    parent_refresh_token_id=row["refresh_token_id"],
                    device_id_hash=context.device_id_hash or row.get("device_id_hash"),
                    issued_ip=context.ip_address,
                    user_agent_hash=context.user_agent_hash,
                )
                rotate_refresh_token(
                    conn,
                    old_refresh_token_id=row["refresh_token_id"],
                    replacement_refresh_token_id=replacement["refresh_token_id"],
                    replacement_token_hash=new_hash,
                    last_used_ip=context.ip_address,
                )
                issued = IssuedSession(
                    access_token=create_access_token(user, row["session_id"]),
                    refresh_token=new_plain,
                    csrf_token=create_csrf_token(),
                    user=_public_user(user),
                    session_id=str(row["session_id"]),
                )
                record_audit_event(
                    event_type="refresh_succeeded",
                    outcome="success",
                    user_id=user["user_id"],
                    auth_session_id=row["session_id"],
                    ip_address=context.ip_address,
                    device_id_hash=context.device_id_hash,
                    user_agent_hash=context.user_agent_hash,
                    conn=conn,
                )

    if failure:
        raise failure
    assert issued is not None
    return issued


def logout(refresh_token_plain: str, context: RequestContext) -> dict[str, bool]:
    token_hash = hash_refresh_token(refresh_token_plain)
    with engine.begin() as conn:
        row = get_refresh_token_for_update(conn, token_hash)
        if row is not None:
            revoke_refresh_session(conn, session_id=row["session_id"], reason="logout")
            record_audit_event(
                event_type="logout",
                outcome="success",
                user_id=row["user_id"],
                auth_session_id=row["session_id"],
                ip_address=context.ip_address,
                device_id_hash=context.device_id_hash,
                user_agent_hash=context.user_agent_hash,
                conn=conn,
            )
    return {"logged_out": True}


def logout_all(user_id: str, session_id: str, context: RequestContext) -> dict[str, bool]:
    with engine.begin() as conn:
        revoke_all_refresh_tokens_for_user(conn, user_id=user_id, reason="logout_all")
        record_audit_event(
            event_type="all_sessions_revoked",
            outcome="success",
            user_id=user_id,
            auth_session_id=session_id,
            ip_address=context.ip_address,
            device_id_hash=context.device_id_hash,
            user_agent_hash=context.user_agent_hash,
            conn=conn,
        )
    return {"logged_out": True}


def get_current_user(user_id: str) -> dict[str, Any]:
    with engine.connect() as conn:
        user = get_user_by_id(conn, user_id)
    if user is None or not user.get("is_active"):
        raise AuthError("USER_NOT_AVAILABLE", "The current user is not available.", 401)
    return _public_user(user)

# ============================================================================
# Phase 2: password recovery, FPO access requests, and admin invitations
# ============================================================================


def _frontend_token_url(path: str, token: str) -> str:
    config = get_auth_config()
    return f"{config.frontend_public_url.rstrip('/')}{path}?{urlencode({'token': token})}"


def forgot_password(payload: PasswordForgotRequest, context: RequestContext) -> dict[str, str]:
    config = get_auth_config()
    if not config.mail_enabled:
        raise AuthError(
            "MAIL_NOT_CONFIGURED",
            "Password recovery is temporarily unavailable.",
            503,
        )

    email = normalize_email(str(payload.email))
    public_message = "If an eligible account exists, a password reset email will be sent shortly."

    try:
        with engine.begin() as conn:
            user = get_user_by_email(conn, email, for_update=True)
            if user is not None and user.get("password_hash"):
                plain_token = create_opaque_token()
                token_hash = hash_password_reset_token(plain_token)
                invalidate_active_password_reset_sessions(conn, user_id=user["user_id"])
                reset_row = create_password_reset_session(
                    conn,
                    user_id=user["user_id"],
                    token_hash=token_hash,
                    expires_at=password_reset_expiry(),
                    requested_ip=context.ip_address,
                    device_id_hash=context.device_id_hash,
                    correlation_id=get_correlation_id(),
                )
                queue_email(
                    conn,
                    to_email=email,
                    to_name=user.get("full_name"),
                    template_key="password_reset",
                    template_data={
                        "full_name": user.get("full_name") or "there",
                        "reset_url": _frontend_token_url(config.frontend_password_reset_path, plain_token),
                        "expires_minutes": config.password_reset_expire_minutes,
                    },
                    public_metadata={
                        "password_reset_session_id": str(reset_row["password_reset_session_id"]),
                    },
                )
                record_audit_event(
                    event_type="password_reset_requested",
                    outcome="queued",
                    user_id=user["user_id"],
                    identifier=email,
                    ip_address=context.ip_address,
                    device_id_hash=context.device_id_hash,
                    user_agent_hash=context.user_agent_hash,
                    conn=conn,
                )
            else:
                record_audit_event(
                    event_type="password_reset_requested",
                    outcome="accepted_without_eligible_password_account",
                    identifier=email,
                    ip_address=context.ip_address,
                    device_id_hash=context.device_id_hash,
                    user_agent_hash=context.user_agent_hash,
                    conn=conn,
                )
    except AuthError:
        raise
    except SQLAlchemyError as exc:
        raise AuthError(
            "PASSWORD_RESET_REQUEST_FAILED",
            "Password recovery could not be started. Try again.",
            500,
            internal_message=str(exc),
        ) from exc

    return {"message": public_message, "correlation_id": get_correlation_id()}


def reset_password(payload: PasswordResetRequest, context: RequestContext) -> dict[str, str]:
    assert_password_policy(payload.new_password)
    assert_password_not_breached(payload.new_password)
    token_hash = hash_password_reset_token(payload.token)
    password_hash = hash_password(payload.new_password)
    now = utc_now()

    failure: AuthError | None = None
    with engine.begin() as conn:
        reset_row = get_password_reset_session_for_update(conn, token_hash=token_hash)
        if reset_row is None:
            failure = AuthError("INVALID_RESET_TOKEN", "This password reset link is invalid or expired.", 400)
        elif reset_row.get("used_at") or reset_row.get("invalidated_at"):
            failure = AuthError("RESET_TOKEN_USED", "This password reset link is no longer valid.", 400)
        elif reset_row["expires_at"] <= now:
            failure = AuthError("RESET_TOKEN_EXPIRED", "This password reset link has expired.", 400)
        else:
            user = get_user_by_id(conn, reset_row["user_id"], for_update=True)
            if user is None or not user.get("is_active"):
                failure = AuthError("INVALID_RESET_TOKEN", "This password reset link is invalid or expired.", 400)
            else:
                update_password_hash(conn, user["user_id"], password_hash)
                mark_password_reset_used(
                    conn,
                    password_reset_session_id=reset_row["password_reset_session_id"],
                    completed_ip=context.ip_address,
                )
                revoke_all_refresh_tokens_for_user(
                    conn,
                    user_id=user["user_id"],
                    reason="password_reset",
                )
                queue_email(
                    conn,
                    to_email=user["email"],
                    to_name=user.get("full_name"),
                    template_key="password_changed",
                    template_data={"full_name": user.get("full_name") or "there"},
                    public_metadata={"user_id": str(user["user_id"])},
                )
                record_audit_event(
                    event_type="password_reset_completed",
                    outcome="success",
                    user_id=user["user_id"],
                    identifier=user.get("email"),
                    ip_address=context.ip_address,
                    device_id_hash=context.device_id_hash,
                    user_agent_hash=context.user_agent_hash,
                    conn=conn,
                )
                record_audit_event(
                    event_type="password_changed",
                    outcome="all_sessions_revoked",
                    user_id=user["user_id"],
                    conn=conn,
                )

    if failure:
        record_audit_event(
            event_type="password_reset_completed",
            outcome="failure",
            ip_address=context.ip_address,
            device_id_hash=context.device_id_hash,
            user_agent_hash=context.user_agent_hash,
            metadata={"code": failure.code},
        )
        raise failure

    return {
        "message": "Your password was changed. Existing signed-in sessions were revoked.",
        "correlation_id": get_correlation_id(),
    }


def submit_fpo_access_request(
    payload: FpoAccessRequestCreate,
    context: RequestContext,
) -> dict[str, Any]:
    try:
        with engine.begin() as conn:
            request_row = create_fpo_access_request(
                conn,
                organisation_name=payload.organisation_name,
                registration_number=payload.registration_number,
                contact_person_name=payload.contact_person_name,
                contact_email=normalize_email(str(payload.contact_email)),
                contact_phone=payload.contact_phone,
                state_name=payload.state_name,
                district_name=payload.district_name,
                message=payload.message,
                created_ip=context.ip_address,
                device_id_hash=context.device_id_hash,
                correlation_id=get_correlation_id(),
            )
            queue_email(
                conn,
                to_email=request_row["contact_email"],
                to_name=request_row["contact_person_name"],
                template_key="fpo_access_acknowledgement",
                template_data={
                    "contact_person_name": request_row["contact_person_name"],
                    "organisation_name": request_row["organisation_name"],
                    "request_id": str(request_row["request_id"]),
                },
                public_metadata={"fpo_access_request_id": str(request_row["request_id"])},
            )
            record_audit_event(
                event_type="fpo_access_requested",
                outcome="success",
                identifier=request_row["contact_email"],
                ip_address=context.ip_address,
                device_id_hash=context.device_id_hash,
                user_agent_hash=context.user_agent_hash,
                metadata={"request_id": str(request_row["request_id"])},
                conn=conn,
            )
    except SQLAlchemyError as exc:
        raise AuthError(
            "FPO_ACCESS_REQUEST_FAILED",
            "The FPO access request could not be submitted. Try again.",
            500,
            internal_message=str(exc),
        ) from exc

    return {
        "request_id": request_row["request_id"],
        "status": "pending",
        "message": "Your FPO access request was received for administrator review.",
        "correlation_id": get_correlation_id(),
    }


def get_fpo_access_requests_for_admin(
    *,
    status_filter: str | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    with engine.connect() as conn:
        items = list_fpo_access_requests(
            conn,
            status_filter=status_filter,
            limit=limit,
            offset=offset,
        )
        total = count_fpo_access_requests(conn, status_filter=status_filter)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


def review_fpo_access_request_for_admin(
    *,
    request_id: UUID | str,
    payload: FpoAccessReviewRequest,
    admin_user_id: str,
    context: RequestContext,
) -> dict[str, Any]:
    with engine.begin() as conn:
        existing = get_fpo_access_request_for_update(conn, request_id=request_id)
        if existing is None:
            raise AuthError("FPO_ACCESS_REQUEST_NOT_FOUND", "The FPO access request was not found.", 404)
        updated = review_fpo_access_request(
            conn,
            request_id=request_id,
            status=payload.status,
            review_note=payload.review_note,
            reviewed_by=admin_user_id,
        )
        record_audit_event(
            event_type="fpo_access_reviewed",
            outcome=payload.status,
            actor_user_id=admin_user_id,
            identifier=updated["contact_email"],
            ip_address=context.ip_address,
            device_id_hash=context.device_id_hash,
            user_agent_hash=context.user_agent_hash,
            metadata={"request_id": str(request_id)},
            conn=conn,
        )
    return updated


def create_invitation_for_admin(
    payload: InvitationCreateRequest,
    *,
    admin_user_id: str,
    context: RequestContext,
) -> dict[str, Any]:
    config = get_auth_config()
    if not config.mail_enabled:
        raise AuthError("MAIL_NOT_CONFIGURED", "Invitation email is temporarily unavailable.", 503)

    email = normalize_email(str(payload.email))
    plain_token = create_opaque_token()
    token_hash = hash_invitation_token(plain_token)
    expires_at = invitation_expiry()

    try:
        with engine.begin() as conn:
            if get_user_by_email(conn, email, for_update=True) is not None:
                raise AuthError(
                    "INVITATION_UNAVAILABLE",
                    "An invitation cannot be created for this email address.",
                    409,
                )
            inviter = get_user_by_id(conn, admin_user_id)
            invalidate_active_invitations(conn, email=email, role=payload.role)
            invitation = create_account_invitation(
                conn,
                email=email,
                role=payload.role,
                token_hash=token_hash,
                invited_by=admin_user_id,
                expires_at=expires_at,
                metadata=payload.metadata,
                created_ip=context.ip_address,
                device_id_hash=context.device_id_hash,
                correlation_id=get_correlation_id(),
            )
            queue_email(
                conn,
                to_email=email,
                to_name=payload.metadata.get("contact_person_name"),
                template_key="fpo_invitation",
                template_data={
                    "invite_url": _frontend_token_url(config.frontend_invitation_accept_path, plain_token),
                    "inviter_name": (inviter or {}).get("full_name") or "a MaatiTrace administrator",
                    "expires_hours": config.invitation_expire_hours,
                    "role": payload.role,
                },
                public_metadata={"invitation_id": str(invitation["invitation_id"])},
            )
            record_audit_event(
                event_type="invitation_created",
                outcome="success",
                actor_user_id=admin_user_id,
                identifier=email,
                ip_address=context.ip_address,
                device_id_hash=context.device_id_hash,
                user_agent_hash=context.user_agent_hash,
                metadata={
                    "invitation_id": str(invitation["invitation_id"]),
                    "role": payload.role,
                },
                conn=conn,
            )
    except AuthError:
        raise
    except (IntegrityError, SQLAlchemyError) as exc:
        raise AuthError(
            "INVITATION_CREATE_FAILED",
            "The invitation could not be created.",
            500,
            internal_message=str(exc),
        ) from exc

    return {
        "invitation_id": invitation["invitation_id"],
        "email": invitation["email"],
        "role": invitation["role"],
        "expires_at": invitation["expires_at"],
        "message": "The invitation was queued for email delivery.",
    }


def validate_invitation(token: str) -> dict[str, Any]:
    token_hash = hash_invitation_token(token)
    with engine.connect() as conn:
        invitation = get_account_invitation_by_hash(conn, token_hash=token_hash)
    valid = bool(
        invitation
        and not invitation.get("accepted_at")
        and not invitation.get("revoked_at")
        and invitation["expires_at"] > utc_now()
    )
    if not valid:
        return {"valid": False, "masked_email": None, "role": None, "expires_at": None}
    return {
        "valid": True,
        "masked_email": _mask_email(invitation["email"]),
        "role": invitation["role"],
        "expires_at": invitation["expires_at"],
    }


def accept_invitation(payload: InvitationAcceptRequest, context: RequestContext) -> IssuedSession:
    assert_password_policy(payload.password)
    assert_password_not_breached(payload.password)
    token_hash = hash_invitation_token(payload.token)
    now = utc_now()

    try:
        with engine.begin() as conn:
            invitation = get_account_invitation_by_hash(
                conn,
                token_hash=token_hash,
                for_update=True,
            )
            if invitation is None:
                raise AuthError("INVALID_INVITATION", "This invitation is invalid or expired.", 400)
            if invitation.get("accepted_at") or invitation.get("revoked_at"):
                raise AuthError("INVITATION_USED", "This invitation is no longer valid.", 400)
            if invitation["expires_at"] <= now:
                raise AuthError("INVITATION_EXPIRED", "This invitation has expired.", 400)
            if get_user_by_email(conn, invitation["email"], for_update=True) is not None:
                raise AuthError("INVITATION_UNAVAILABLE", "This invitation cannot be accepted.", 409)
            if get_user_by_phone(conn, payload.phone_number, for_update=True) is not None:
                raise AuthError("INVITATION_UNAVAILABLE", "This invitation cannot be accepted.", 409)

            user = create_user(
                conn,
                full_name=payload.full_name,
                email=invitation["email"],
                phone_number=payload.phone_number,
                password_hash=hash_password(payload.password),
                role=invitation["role"],
                is_verified=True,
            )
            mark_account_invitation_accepted(
                conn,
                invitation_id=invitation["invitation_id"],
                accepted_by_user_id=user["user_id"],
                accepted_ip=context.ip_address,
            )
            mark_user_login(conn, user["user_id"])
            issued = _issue_session(conn, user, context)
            record_audit_event(
                event_type="invitation_accepted",
                outcome="success",
                user_id=user["user_id"],
                actor_user_id=invitation["invited_by"],
                auth_session_id=issued.session_id,
                identifier=user["email"],
                ip_address=context.ip_address,
                device_id_hash=context.device_id_hash,
                user_agent_hash=context.user_agent_hash,
                metadata={
                    "invitation_id": str(invitation["invitation_id"]),
                    "role": invitation["role"],
                },
                conn=conn,
            )
            return issued
    except AuthError:
        raise
    except (IntegrityError, SQLAlchemyError) as exc:
        raise AuthError(
            "INVITATION_ACCEPT_FAILED",
            "The invitation could not be accepted.",
            500,
            internal_message=str(exc),
        ) from exc
