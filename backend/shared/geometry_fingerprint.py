from __future__ import annotations

import hashlib
import json
from typing import Any


def geometry_fingerprint(geojson: dict[str, Any]) -> str:
    """Return a stable fingerprint for a farm boundary payload.

    Sorting keys and using compact separators means equivalent JSON objects
    produce the same value, while any actual boundary change invalidates the
    cached H3 cells.
    """
    canonical = json.dumps(
        geojson,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
