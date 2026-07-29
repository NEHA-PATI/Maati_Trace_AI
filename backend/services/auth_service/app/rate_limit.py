from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

import redis

from services.auth_service.app.config_validation import get_auth_config
from services.auth_service.app.errors import AuthError
from services.auth_service.app.security import hash_rate_limit_value


@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    limit: int
    window_seconds: int


POLICIES: dict[str, RateLimitPolicy] = {
    "signup_start": RateLimitPolicy(5, 3600),
    "signup_resend": RateLimitPolicy(4, 3600),
    "signup_verify": RateLimitPolicy(12, 900),
    "login": RateLimitPolicy(10, 900),
    "google_login": RateLimitPolicy(15, 900),
    "refresh": RateLimitPolicy(30, 300),
    "password_forgot": RateLimitPolicy(5, 3600),
    "password_reset": RateLimitPolicy(8, 3600),
    "fpo_access": RateLimitPolicy(4, 86400),
    "invitation_validate": RateLimitPolicy(20, 900),
    "invitation_accept": RateLimitPolicy(8, 3600),
}

_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""


class RateLimiter:
    def __init__(self, client: redis.Redis) -> None:
        self.client = client

    def enforce(self, scope: str, dimensions: Iterable[tuple[str, str | None]]) -> None:
        config = get_auth_config()
        if not config.rate_limit_enabled:
            return

        policy = POLICIES[scope]
        most_restrictive_retry = 0
        exceeded = False

        for dimension_name, raw_value in dimensions:
            if not raw_value:
                continue
            digest = hash_rate_limit_value(str(raw_value))
            key = f"maatitrace:auth:rl:{scope}:{dimension_name}:{digest}"
            current, ttl = self.client.eval(
                _SCRIPT,
                1,
                key,
                policy.window_seconds,
            )
            current = int(current)
            ttl = max(int(ttl), 1)
            if current > policy.limit:
                exceeded = True
                most_restrictive_retry = max(most_restrictive_retry, ttl)

        if exceeded:
            raise AuthError(
                "RATE_LIMITED",
                "Too many attempts. Try again later.",
                429,
                retry_after=most_restrictive_retry,
            )


_test_rate_limiter: RateLimiter | None = None


@lru_cache(maxsize=1)
def get_rate_limiter() -> RateLimiter:
    if _test_rate_limiter is not None:
        return _test_rate_limiter
    config = get_auth_config()
    if not config.redis_url:
        raise RuntimeError("REDIS_URL is not configured")
    client = redis.Redis.from_url(config.redis_url, decode_responses=True, protocol=2)
    return RateLimiter(client)


def set_rate_limiter_for_tests(limiter: RateLimiter | None) -> None:
    global _test_rate_limiter
    _test_rate_limiter = limiter
    get_rate_limiter.cache_clear()