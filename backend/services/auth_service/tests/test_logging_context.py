from services.auth_service.app.logging_context import redact


def test_sensitive_values_are_redacted_recursively():
    result = redact(
        {
            "email": "neha@example.com",
            "password": "secret",
            "nested": {"refresh_token": "token", "status": "ok"},
        }
    )
    assert result["email"] == "neha@example.com"
    assert result["password"] == "[REDACTED]"
    assert result["nested"]["refresh_token"] == "[REDACTED]"
    assert result["nested"]["status"] == "ok"