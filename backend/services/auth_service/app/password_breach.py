from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict

import requests

from services.auth_service.app.config_validation import get_auth_config
from services.auth_service.app.errors import AuthError


class PasswordBreachServiceUnavailable(RuntimeError):
    pass


class PwnedPasswordClient:
    def __init__(self, max_cache_entries: int = 512) -> None:
        self._session = requests.Session()
        self._cache: OrderedDict[str, dict[str, int]] = OrderedDict()
        self._max_cache_entries = max_cache_entries
        self._lock = threading.Lock()

    def _fetch_prefix(self, prefix: str) -> dict[str, int]:
        with self._lock:
            cached = self._cache.get(prefix)
            if cached is not None:
                self._cache.move_to_end(prefix)
                return cached

        config = get_auth_config()
        try:
            response = self._session.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                headers={
                    "Add-Padding": "true",
                    "User-Agent": "MaatiTrace-Auth/1.0",
                },
                timeout=config.pwned_passwords_timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise PasswordBreachServiceUnavailable("Password breach service is unavailable") from exc

        parsed: dict[str, int] = {}
        for line in response.text.splitlines():
            suffix, _, count = line.partition(":")
            if suffix and count.isdigit():
                parsed[suffix.strip().upper()] = int(count)

        with self._lock:
            self._cache[prefix] = parsed
            self._cache.move_to_end(prefix)
            while len(self._cache) > self._max_cache_entries:
                self._cache.popitem(last=False)
        return parsed

    def breach_count(self, password: str) -> int:
        config = get_auth_config()
        if not config.pwned_passwords_enabled:
            return 0

        digest = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()  # nosec B324: required by k-anonymity API
        prefix, suffix = digest[:5], digest[5:]
        try:
            candidates = self._fetch_prefix(prefix)
        except PasswordBreachServiceUnavailable:
            if config.pwned_passwords_fail_closed:
                raise AuthError(
                    "PASSWORD_CHECK_UNAVAILABLE",
                    "Password safety checking is temporarily unavailable. Try again shortly.",
                    503,
                )
            return 0
        return candidates.get(suffix, 0)

    def assert_not_breached(self, password: str) -> None:
        if self.breach_count(password) > 0:
            raise AuthError(
                "PASSWORD_BREACHED",
                "This password has appeared in known data breaches. Choose a different password.",
                422,
            )


_client = PwnedPasswordClient()


def assert_password_not_breached(password: str) -> None:
    _client.assert_not_breached(password)