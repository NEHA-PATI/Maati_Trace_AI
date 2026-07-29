from __future__ import annotations

import fakeredis
import pytest

from services.auth_service.app.config_validation import reset_auth_config_cache
from services.auth_service.app.errors import AuthError
from services.auth_service.app.rate_limit import POLICIES, RateLimitPolicy, RateLimiter


def test_rate_limit_returns_retry_after(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    reset_auth_config_cache()
    client = fakeredis.FakeRedis(decode_responses=True)
    limiter = RateLimiter(client)
    monkeypatch.setitem(POLICIES, "login", RateLimitPolicy(limit=2, window_seconds=60))

    dimensions = [("ip", "127.0.0.1"), ("identifier", "neha@example.com")]
    limiter.enforce("login", dimensions)
    limiter.enforce("login", dimensions)

    with pytest.raises(AuthError) as raised:
        limiter.enforce("login", dimensions)

    assert raised.value.code == "RATE_LIMITED"
    assert raised.value.status_code == 429
    assert raised.value.retry_after and raised.value.retry_after > 0