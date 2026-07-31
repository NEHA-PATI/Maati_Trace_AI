from services.auth_service.app.email_templates import render_email


def test_signup_otp_template_escapes_user_content():
    rendered = render_email(
        "signup_otp",
        {
            "full_name": "<script>alert(1)</script>",
            "otp": "123456",
            "expires_minutes": 10,
        },
    )
    assert "<script>" not in rendered.html_body
    assert "&lt;script&gt;" in rendered.html_body
    assert "123456" in rendered.text_body


def test_password_reset_template_contains_one_time_url():
    rendered = render_email(
        "password_reset",
        {
            "full_name": "Neha",
            "reset_url": "https://maatitrace.test/reset-password?token=abc",
            "expires_minutes": 30,
        },
    )
    assert "Reset password" in rendered.html_body
    assert "token=abc" in rendered.text_body


def test_all_phase2_templates_render():
    cases = {
        "password_changed": {"full_name": "Neha"},
        "fpo_invitation": {
            "invite_url": "https://maatitrace.test/accept-invitation?token=abc",
            "inviter_name": "Admin",
            "expires_hours": 72,
            "role": "fpo",
        },
        "fpo_access_acknowledgement": {
            "contact_person_name": "Neha",
            "organisation_name": "Green FPO",
            "request_id": "request-1",
        },
    }
    for key, payload in cases.items():
        rendered = render_email(key, payload)
        assert rendered.subject
        assert rendered.html_body.startswith("<!doctype html>")
        assert rendered.text_body