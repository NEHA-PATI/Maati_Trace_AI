from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RenderedEmail:
    subject: str
    html_body: str
    text_body: str


def _escape(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _base_html(title: str, body: str) -> str:
    return (
        "<!doctype html>"
        "<html><body style='margin:0;background:#f4f7f4;font-family:Arial,sans-serif;color:#17221d'>"
        "<table role='presentation' width='100%' cellspacing='0' cellpadding='0' style='background:#f4f7f4;padding:24px'>"
        "<tr><td align='center'>"
        "<table role='presentation' width='100%' cellspacing='0' cellpadding='0' "
        "style='max-width:600px;background:#ffffff;border:1px solid #dfe8e2;border-radius:18px;overflow:hidden'>"
        "<tr><td style='padding:24px;background:#0f5132;color:#ffffff'>"
        "<div style='font-size:12px;letter-spacing:2px;text-transform:uppercase'>MaatiTrace</div>"
        f"<h1 style='margin:8px 0 0;font-size:24px'>{_escape(title)}</h1>"
        "</td></tr>"
        f"<tr><td style='padding:28px;line-height:1.6'>{body}</td></tr>"
        "<tr><td style='padding:18px 28px;background:#f7faf8;color:#66736c;font-size:12px'>"
        "This is an automated security message from MaatiTrace. Do not share verification codes or links."
        "</td></tr></table></td></tr></table></body></html>"
    )


def render_email(template_key: str, data: dict[str, Any]) -> RenderedEmail:
    if template_key == "signup_otp":
        name = _escape(data.get("full_name") or "there")
        otp = _escape(data["otp"])
        minutes = int(data.get("expires_minutes") or 10)
        subject = "Your MaatiTrace verification code"
        body = (
            f"<p>Hello {name},</p>"
            "<p>Use this six-digit code to verify your MaatiTrace account:</p>"
            f"<div style='font-size:32px;font-weight:700;letter-spacing:8px;padding:18px 0'>{otp}</div>"
            f"<p>This code expires in <strong>{minutes} minutes</strong>.</p>"
            "<p>If you did not start this signup, you can ignore this email.</p>"
        )
        text = (
            f"Hello {html.unescape(name)},\n\n"
            f"Your MaatiTrace verification code is {html.unescape(otp)}.\n"
            f"It expires in {minutes} minutes.\n\n"
            "If you did not start this signup, ignore this email."
        )
        return RenderedEmail(subject, _base_html("Verify your account", body), text)

    if template_key == "password_reset":
        name = _escape(data.get("full_name") or "there")
        reset_url = _escape(data["reset_url"])
        minutes = int(data.get("expires_minutes") or 30)
        subject = "Reset your MaatiTrace password"
        body = (
            f"<p>Hello {name},</p>"
            "<p>A password reset was requested for your MaatiTrace account.</p>"
            f"<p><a href='{reset_url}' style='display:inline-block;background:#0f5132;color:#ffffff;"
            "text-decoration:none;padding:12px 20px;border-radius:10px;font-weight:700'>Reset password</a></p>"
            f"<p>This link expires in <strong>{minutes} minutes</strong> and can be used only once.</p>"
            "<p>If you did not request this, no action is required.</p>"
        )
        text = (
            f"Hello {html.unescape(name)},\n\n"
            "A password reset was requested for your MaatiTrace account.\n"
            f"Open this one-time link: {html.unescape(reset_url)}\n"
            f"The link expires in {minutes} minutes.\n\n"
            "If you did not request this, no action is required."
        )
        return RenderedEmail(subject, _base_html("Reset your password", body), text)

    if template_key == "password_changed":
        name = _escape(data.get("full_name") or "there")
        subject = "Your MaatiTrace password was changed"
        body = (
            f"<p>Hello {name},</p>"
            "<p>Your MaatiTrace password was changed successfully.</p>"
            "<p>All existing signed-in sessions were revoked for your protection.</p>"
            "<p>If you did not make this change, contact the MaatiTrace administrator immediately.</p>"
        )
        text = (
            f"Hello {html.unescape(name)},\n\n"
            "Your MaatiTrace password was changed successfully.\n"
            "All existing signed-in sessions were revoked.\n"
            "If you did not make this change, contact the MaatiTrace administrator immediately."
        )
        return RenderedEmail(subject, _base_html("Password changed", body), text)

    if template_key == "fpo_invitation":
        invite_url = _escape(data["invite_url"])
        inviter_name = _escape(data.get("inviter_name") or "a MaatiTrace administrator")
        hours = int(data.get("expires_hours") or 72)
        role = _escape(data.get("role") or "fpo").upper()
        subject = "You are invited to MaatiTrace"
        body = (
            f"<p>{inviter_name} invited you to create a <strong>{role}</strong> account on MaatiTrace.</p>"
            f"<p><a href='{invite_url}' style='display:inline-block;background:#0f5132;color:#ffffff;"
            "text-decoration:none;padding:12px 20px;border-radius:10px;font-weight:700'>Accept invitation</a></p>"
            f"<p>This invitation expires in <strong>{hours} hours</strong> and can be used only once.</p>"
            "<p>If you were not expecting this invitation, ignore this email.</p>"
        )
        text = (
            f"{html.unescape(inviter_name)} invited you to create a {html.unescape(role)} account on MaatiTrace.\n\n"
            f"Accept the invitation: {html.unescape(invite_url)}\n"
            f"The invitation expires in {hours} hours and can be used only once."
        )
        return RenderedEmail(subject, _base_html("MaatiTrace invitation", body), text)

    if template_key == "fpo_access_acknowledgement":
        name = _escape(data.get("contact_person_name") or "there")
        organisation = _escape(data.get("organisation_name") or "your organisation")
        request_id = _escape(data.get("request_id") or "")
        subject = "We received your MaatiTrace FPO access request"
        body = (
            f"<p>Hello {name},</p>"
            f"<p>We received the access request for <strong>{organisation}</strong>.</p>"
            f"<p>Reference: <strong>{request_id}</strong></p>"
            "<p>An administrator will review the supplied organisation details. This request does not create an account.</p>"
        )
        text = (
            f"Hello {html.unescape(name)},\n\n"
            f"We received the MaatiTrace FPO access request for {html.unescape(organisation)}.\n"
            f"Reference: {html.unescape(request_id)}\n"
            "An administrator will review it. This request does not create an account."
        )
        return RenderedEmail(subject, _base_html("FPO access request received", body), text)

    raise ValueError(f"Unsupported email template: {template_key}")