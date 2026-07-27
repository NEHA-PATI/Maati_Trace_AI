# from __future__ import annotations

# import html
# import json
# from typing import Any

# import requests
# from sqlalchemy import text

# from shared.config.settings import settings
# from shared.db.postgres import engine


# class MailServiceError(RuntimeError):
#     pass


# def _record_email(
#     *,
#     to_email: str,
#     to_name: str | None,
#     subject: str,
#     template_key: str,
#     provider: str,
#     status: str,
#     provider_message_id: str | None = None,
#     error_message: str | None = None,
#     metadata: dict[str, Any] | None = None,
# ) -> None:
#     query = text("""
#         INSERT INTO email_outbox (
#             to_email,
#             to_name,
#             subject,
#             template_key,
#             provider,
#             provider_message_id,
#             status,
#             error_message,
#             metadata,
#             sent_at,
#             failed_at
#         )
#         VALUES (
#             :to_email,
#             :to_name,
#             :subject,
#             :template_key,
#             :provider,
#             :provider_message_id,
#             :status,
#             :error_message,
#             CAST(:metadata AS jsonb),
#             CASE WHEN :status = 'sent' THEN now() END,
#             CASE WHEN :status = 'failed' THEN now() END
#         );
#     """)

#     with engine.begin() as connection:
#         connection.execute(
#             query,
#             {
#                 "to_email": to_email,
#                 "to_name": to_name,
#                 "subject": subject,
#                 "template_key": template_key,
#                 "provider": provider,
#                 "provider_message_id": provider_message_id,
#                 "status": status,
#                 "error_message": error_message,
#                 "metadata": json.dumps(metadata or {}),
#             },
#         )


# def send_signup_otp_email(
#     to_email: str,
#     full_name: str,
#     otp: str,
# ) -> None:
#     provider = settings.mail_provider.strip().lower()
#     subject = "Your MaatiTrace verification code"

#     safe_name = html.escape(full_name)
#     safe_otp = html.escape(otp)

#     html_content = f"""
#     <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto">
#         <h2>Verify your MaatiTrace account</h2>
#         <p>Hello {safe_name},</p>
#         <p>Your verification code is:</p>

#         <div style="
#             font-size:30px;
#             font-weight:700;
#             letter-spacing:5px;
#             padding:16px;
#             background:#f2f7f2;
#             text-align:center;
#         ">
#             {safe_otp}
#         </div>

#         <p>This code expires in {settings.signup_otp_expire_minutes} minutes.</p>
#         <p>Do not share this code with anyone.</p>
#     </div>
#     """

#     if provider == "console":
#         print(f"MAATITRACE OTP for {to_email}: {otp}")

#         _record_email(
#             to_email=to_email,
#             to_name=full_name,
#             subject=subject,
#             template_key="signup_otp",
#             provider="console",
#             status="sent",
#         )
#         return

#     if provider != "brevo":
#         raise MailServiceError(
#             f"Unsupported mail provider: {provider}"
#         )

#     if not settings.brevo_api_key:
#         raise MailServiceError("BREVO_API_KEY is not configured")

#     if not settings.mail_from_email:
#         raise MailServiceError("MAIL_FROM_EMAIL is not configured")

#     try:
#         response = requests.post(
#             "https://api.brevo.com/v3/smtp/email",
#             headers={
#                 "api-key": settings.brevo_api_key,
#                 "accept": "application/json",
#                 "content-type": "application/json",
#             },
#             json={
#                 "sender": {
#                     "name": settings.mail_from_name,
#                     "email": settings.mail_from_email,
#                 },
#                 "to": [
#                     {
#                         "name": full_name,
#                         "email": to_email,
#                     }
#                 ],
#                 "subject": subject,
#                 "htmlContent": html_content,
#             },
#             timeout=settings.mail_http_timeout_seconds,
#         )

#         response.raise_for_status()
#         response_data = response.json() if response.content else {}

#     except requests.RequestException as exc:
#         _record_email(
#             to_email=to_email,
#             to_name=full_name,
#             subject=subject,
#             template_key="signup_otp",
#             provider="brevo",
#             status="failed",
#             error_message=str(exc),
#         )

#         raise MailServiceError(
#             "Verification email could not be sent"
#         ) from exc

#     _record_email(
#         to_email=to_email,
#         to_name=full_name,
#         subject=subject,
#         template_key="signup_otp",
#         provider="brevo",
#         status="sent",
#         provider_message_id=response_data.get("messageId"),
#     )















from __future__ import annotations

import html
import json
from typing import Any

import requests
from sqlalchemy import text

from shared.config.settings import settings
from shared.db.postgres import engine


class MailServiceError(RuntimeError):
    pass


def _record_email(
    *,
    to_email: str,
    to_name: str | None,
    subject: str,
    template_key: str,
    provider: str,
    status: str,
    provider_message_id: str | None = None,
    error_message: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO email_outbox (
                    to_email,
                    to_name,
                    subject,
                    template_key,
                    provider,
                    provider_message_id,
                    status,
                    error_message,
                    metadata,
                    sent_at,
                    failed_at
                )
                VALUES (
                    :to_email,
                    :to_name,
                    :subject,
                    :template_key,
                    :provider,
                    :provider_message_id,
                    :status,
                    :error_message,
                    CAST(:metadata AS jsonb),
                    CASE WHEN :status = 'sent' THEN now() END,
                    CASE WHEN :status = 'failed' THEN now() END
                );
                """
            ),
            {
                "to_email": to_email,
                "to_name": to_name,
                "subject": subject,
                "template_key": template_key,
                "provider": provider,
                "provider_message_id": provider_message_id,
                "status": status,
                "error_message": error_message,
                "metadata": json.dumps(metadata or {}),
            },
        )


def _graph_access_token() -> str:
    if not settings.microsoft_tenant_id:
        raise MailServiceError("MICROSOFT_TENANT_ID is missing")
    if not settings.microsoft_client_id:
        raise MailServiceError("MICROSOFT_CLIENT_ID is missing")
    if not settings.microsoft_client_secret:
        raise MailServiceError("MICROSOFT_CLIENT_SECRET is missing")

    token_url = (
        "https://login.microsoftonline.com/"
        f"{settings.microsoft_tenant_id}/oauth2/v2.0/token"
    )
    try:
        response = requests.post(
            token_url,
            data={
                "client_id": settings.microsoft_client_id,
                "client_secret": settings.microsoft_client_secret,
                "scope": settings.microsoft_graph_scope,
                "grant_type": "client_credentials",
            },
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MailServiceError("Could not get Microsoft Graph mail token") from exc

    data = response.json()
    access_token = data.get("access_token")
    if not access_token:
        raise MailServiceError("Microsoft Graph token response did not include access_token")
    return str(access_token)


def _send_with_microsoft_graph(
    *,
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
) -> str | None:
    if not settings.mail_from_email:
        raise MailServiceError("MAIL_FROM_EMAIL is missing")

    access_token = _graph_access_token()
    send_url = f"https://graph.microsoft.com/v1.0/users/{settings.mail_from_email}/sendMail"
    payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": html_content,
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": to_email,
                        "name": to_name,
                    }
                }
            ],
        },
        "saveToSentItems": "true",
    }

    try:
        response = requests.post(
            send_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MailServiceError("Verification email could not be sent with Microsoft Graph") from exc

    return response.headers.get("request-id") or response.headers.get("client-request-id")


def send_signup_otp_email(to_email: str, full_name: str, otp: str) -> None:
    provider = settings.mail_provider.strip().lower()
    subject = "Your MaatiTrace verification code"
    safe_name = html.escape(full_name)
    safe_otp = html.escape(otp)
    html_content = (
        "<div style='font-family:Arial,sans-serif;max-width:560px;margin:auto'>"
        "<h2>Verify your MaatiTrace account</h2>"
        f"<p>Hello {safe_name},</p>"
        "<p>Your verification code is:</p>"
        f"<div style='font-size:28px;font-weight:700;letter-spacing:4px'>{safe_otp}</div>"
        f"<p>This code expires in {settings.signup_otp_expire_minutes} minutes.</p>"
        "<p>If you did not request this, you can ignore this email.</p>"
        "</div>"
    )

    if provider == "console":
        print(f"MAATITRACE LOCAL OTP for {to_email}: {otp}")
        _record_email(
            to_email=to_email,
            to_name=full_name,
            subject=subject,
            template_key="signup_otp",
            provider="console",
            status="sent",
        )
        return

    if provider != "microsoft_graph":
        raise MailServiceError("MAIL_PROVIDER must be console or microsoft_graph")

    try:
        provider_message_id = _send_with_microsoft_graph(
            to_email=to_email,
            to_name=full_name,
            subject=subject,
            html_content=html_content,
        )
    except MailServiceError as exc:
        _record_email(
            to_email=to_email,
            to_name=full_name,
            subject=subject,
            template_key="signup_otp",
            provider="microsoft_graph",
            status="failed",
            error_message=str(exc),
        )
        raise

    _record_email(
        to_email=to_email,
        to_name=full_name,
        subject=subject,
        template_key="signup_otp",
        provider="microsoft_graph",
        status="sent",
        provider_message_id=provider_message_id,
    )