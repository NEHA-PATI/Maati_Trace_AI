import pytest

from services.auth_service.app.dependencies import RequestContext, require_roles
from services.auth_service.app.errors import AuthError


def test_admin_dependency_rejects_farmer_and_records_audit(monkeypatch):
    recorded = {}

    def fake_record(**kwargs):
        recorded.update(kwargs)

    monkeypatch.setattr(
        "services.auth_service.app.dependencies.record_audit_event",
        fake_record,
    )
    dependency = require_roles("admin")
    with pytest.raises(AuthError) as exc_info:
        dependency(
            principal={
                "user_id": "11111111-1111-1111-1111-111111111111",
                "role": "farmer",
                "session_id": "22222222-2222-2222-2222-222222222222",
            },
            context=RequestContext(
                ip_address="127.0.0.1",
                device_id_hash="device",
                user_agent_hash="agent",
            ),
        )
    assert exc_info.value.status_code == 403
    assert recorded["event_type"] == "authorization_denied"