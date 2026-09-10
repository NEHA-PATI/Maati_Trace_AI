from __future__ import annotations

import math
import statistics
from datetime import date, datetime
from typing import Iterable, Sequence

EPSILON = 1e-9


def finite_number(value) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


def clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def clip01(value: float) -> float:
    return clip(value, 0.0, 1.0)


def safe_ratio(numerator, denominator) -> float | None:
    n = finite_number(numerator)
    d = finite_number(denominator)
    if n is None or d is None or abs(d) <= EPSILON:
        return None
    return n / d


def safe_mean(values: Iterable[float | None]) -> float | None:
    cleaned = [v for raw in values if (v := finite_number(raw)) is not None]
    if not cleaned:
        return None
    return sum(cleaned) / len(cleaned)


def safe_weighted_mean(pairs: Iterable[tuple[float | None, float | None]]) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for raw_value, raw_weight in pairs:
        value = finite_number(raw_value)
        weight = finite_number(raw_weight)
        if value is None or weight is None or weight <= 0:
            continue
        numerator += value * weight
        denominator += weight
    if denominator <= EPSILON:
        return None
    return numerator / denominator


def median(values: Iterable[float | None]) -> float | None:
    cleaned = [v for raw in values if (v := finite_number(raw)) is not None]
    if not cleaned:
        return None
    return float(statistics.median(cleaned))


def mad(values: Iterable[float | None]) -> float | None:
    cleaned = [v for raw in values if (v := finite_number(raw)) is not None]
    if not cleaned:
        return None
    center = statistics.median(cleaned)
    return float(statistics.median(abs(value - center) for value in cleaned))


def robust_z(current, historical: Sequence[float | None], *, min_samples: int = 3) -> float | None:
    value = finite_number(current)
    history = [v for raw in historical if (v := finite_number(raw)) is not None]
    if value is None or len(history) < min_samples:
        return None
    center = float(statistics.median(history))
    deviation = float(statistics.median(abs(item - center) for item in history))
    if deviation <= EPSILON:
        # A perfectly stable baseline should not manufacture huge z-scores.
        spread = statistics.pstdev(history) if len(history) >= 2 else 0.0
        if spread <= EPSILON:
            return 0.0 if abs(value - center) <= EPSILON else (3.0 if value > center else -3.0)
        return (value - center) / spread
    return (value - center) / (1.4826 * deviation)


def standard_z(current, historical: Sequence[float | None], *, min_samples: int = 3) -> float | None:
    value = finite_number(current)
    history = [v for raw in historical if (v := finite_number(raw)) is not None]
    if value is None or len(history) < min_samples:
        return None
    mean = statistics.fmean(history)
    std = statistics.pstdev(history)
    if std <= EPSILON:
        return 0.0 if abs(value - mean) <= EPSILON else (3.0 if value > mean else -3.0)
    return (value - mean) / std


def as_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def linear_slope(points: Sequence[tuple[date | datetime | str, float | None]], *, min_samples: int = 3) -> float | None:
    cleaned: list[tuple[date, float]] = []
    for raw_date, raw_value in points:
        dt = as_date(raw_date)
        value = finite_number(raw_value)
        if dt is not None and value is not None:
            cleaned.append((dt, value))
    if len(cleaned) < min_samples:
        return None
    cleaned.sort(key=lambda item: item[0])
    origin = cleaned[0][0]
    xs = [(item[0] - origin).days for item in cleaned]
    ys = [item[1] for item in cleaned]
    xbar = statistics.fmean(xs)
    ybar = statistics.fmean(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    if denom <= EPSILON:
        return None
    return sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom


def freshness_score(age_days: int | float | None, half_life_days: float) -> float:
    if age_days is None:
        return 0.0
    age = max(0.0, float(age_days))
    half_life = max(1.0, float(half_life_days))
    return clip01(2.0 ** (-age / half_life))


def normalize_high(value, low, high) -> float | None:
    """Return 0 below low, 1 above high, linear between; higher is worse/bigger."""
    x = finite_number(value)
    lo = finite_number(low)
    hi = finite_number(high)
    if x is None or lo is None or hi is None or hi <= lo:
        return None
    return clip01((x - lo) / (hi - lo))


def normalize_low(value, low, high) -> float | None:
    """Return 1 below low, 0 above high, linear between; lower is worse."""
    high_score = normalize_high(value, low, high)
    return None if high_score is None else 1.0 - high_score


def low_z_stress(z_value, critical: float = 3.0) -> float | None:
    z = finite_number(z_value)
    if z is None:
        return None
    return clip01(-z / max(EPSILON, float(critical)))


def high_z_stress(z_value, critical: float = 3.0) -> float | None:
    z = finite_number(z_value)
    if z is None:
        return None
    return clip01(z / max(EPSILON, float(critical)))


def absolute_z_anomaly(z_value, critical: float = 3.0) -> float | None:
    z = finite_number(z_value)
    if z is None:
        return None
    return clip01(abs(z) / max(EPSILON, float(critical)))


def trapezoid_suitability(value, bounds: Sequence[float]) -> float | None:
    """0 outside [a,d], 1 inside [b,c], linearly transitions in between."""
    x = finite_number(value)
    if x is None or not isinstance(bounds, (list, tuple)) or len(bounds) != 4:
        return None
    a, b, c, d = [float(v) for v in bounds]
    if not (a <= b <= c <= d):
        return None
    if x <= a or x >= d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if a < x < b:
        return clip01((x - a) / max(EPSILON, b - a))
    return clip01((d - x) / max(EPSILON, d - c))


def weighted_score(components: dict[str, dict], weights: dict[str, float]) -> tuple[float | None, float]:
    """
    Quality-aware score over 0..1 component values.

    Score renormalizes around available quality-weighted components.
    Confidence is the proportion of configured component weight that is backed by usable data.
    """
    numerator = 0.0
    effective_denominator = 0.0
    configured_total = 0.0
    for key, raw_weight in weights.items():
        weight = max(0.0, float(raw_weight or 0.0))
        configured_total += weight
        component = components.get(key) or {}
        value = finite_number(component.get("value"))
        quality = finite_number(component.get("quality"))
        if value is None or quality is None or quality <= 0 or weight <= 0:
            continue
        quality = clip01(quality)
        effective = weight * quality
        numerator += clip01(value) * effective
        effective_denominator += effective
    if effective_denominator <= EPSILON:
        return None, 0.0
    score = numerator / effective_denominator
    confidence = effective_denominator / configured_total if configured_total > EPSILON else 0.0
    return clip01(score), clip01(confidence)
