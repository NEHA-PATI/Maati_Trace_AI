from __future__ import annotations

from collections import defaultdict
from typing import Any

from services.analytics_query_service.app.feature_engine.component_catalog import (
    ComponentResult,
    compute_component,
)
from services.analytics_query_service.app.feature_engine.math_utils import (
    clip01,
    finite_number,
    safe_weighted_mean,
    weighted_score,
)


class FormulaEngineError(RuntimeError):
    pass


def status_label(score: float | None, direction: str, thresholds: dict[str, Any]) -> str:
    if score is None:
        return "Insufficient data"
    value = float(score)
    if direction == "risk":
        normal = float(thresholds.get("normal", 20))
        watch = float(thresholds.get("watch", 40))
        attention = float(thresholds.get("attention", 60))
        high = float(thresholds.get("high", 80))
        if value < normal:
            return "Normal"
        if value < watch:
            return "Watch"
        if value < attention:
            return "Attention"
        if value < high:
            return "High"
        return "Critical"

    critical = float(thresholds.get("critical", 20))
    poor = float(thresholds.get("poor", 40))
    attention = float(thresholds.get("attention", 60))
    fair = float(thresholds.get("fair", 80))
    if value >= fair:
        return "Good"
    if value >= attention:
        return "Fair"
    if value >= poor:
        return "Needs attention"
    if value >= critical:
        return "Poor"
    return "Critical"


def _prediction_component(
    component_key: str,
    calculated: dict[str, dict[str, Any]],
) -> ComponentResult | None:
    inverse = component_key.startswith("prediction_inverse:")
    if inverse:
        prediction_key = component_key.split(":", 1)[1]
    elif component_key.startswith("prediction:"):
        prediction_key = component_key.split(":", 1)[1]
    else:
        return None

    result = calculated.get(prediction_key)
    if not result:
        return ComponentResult(None, 0.0, {"reason": f"Prediction {prediction_key} not available"})
    raw = finite_number(result.get("score"))
    if raw is None:
        return ComponentResult(None, 0.0, {"reason": f"Prediction {prediction_key} has no score"})
    value = clip01(raw / 100.0)
    if inverse:
        value = 1.0 - value
    return ComponentResult(value, clip01(float(result.get("confidence") or 0.0)), {
        "source_prediction": prediction_key,
        "source_score": raw,
        "inverse": inverse,
    })


def _component_payload(result: ComponentResult, weight: float) -> dict[str, Any]:
    contribution = None
    if result.value is not None:
        contribution = float(weight) * float(result.quality) * float(result.value)
    return {
        "value": result.value,
        "quality": result.quality,
        "weight": float(weight),
        "effective_weight": float(weight) * float(result.quality),
        "weighted_contribution": contribution,
        "details": result.details,
    }


def _evidence(components: dict[str, dict[str, Any]], direction: str) -> list[dict[str, Any]]:
    ranked = []
    for key, item in components.items():
        value = finite_number(item.get("value"))
        quality = finite_number(item.get("quality"))
        weight = finite_number(item.get("weight"))
        if value is None or quality is None or weight is None:
            continue
        # For a condition score, low values are the concern; for risk, high values are the concern.
        concern = value if direction == "risk" else 1.0 - value
        ranked.append((weight * quality * concern, key, item))
    ranked.sort(reverse=True, key=lambda row: row[0])
    evidence = []
    for contribution, key, item in ranked[:4]:
        evidence.append({
            "component": key,
            "component_value": item.get("value"),
            "quality": item.get("quality"),
            "configured_weight": item.get("weight"),
            "concern_contribution": round(float(contribution), 6),
            "details": item.get("details") or {},
        })
    return evidence


def calculate_h3_predictions(
    *,
    feature_rows: list[dict[str, Any]],
    formulas: list[dict[str, Any]],
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    formulas = sorted(formulas, key=lambda f: (int(f.get("execution_order") or 100), f.get("prediction_key") or ""))

    for feature_row in feature_rows:
        features = feature_row.get("features") or {}
        quality = feature_row.get("quality") or {}
        calculated: dict[str, dict[str, Any]] = {}

        for formula in formulas:
            weights = formula.get("component_weights") or {}
            if not weights:
                continue

            component_results: dict[str, ComponentResult] = {}
            for component_key in weights:
                prediction_component = _prediction_component(component_key, calculated)
                if prediction_component is not None:
                    component_results[component_key] = prediction_component
                    continue
                try:
                    component_results[component_key] = compute_component(
                        component_key,
                        features=features,
                        quality=quality,
                        profile=profile,
                        formula_parameters=formula.get("parameters") or {},
                    )
                except KeyError as exc:
                    raise FormulaEngineError(str(exc)) from exc

            weighted_components = {
                key: {"value": result.value, "quality": result.quality}
                for key, result in component_results.items()
            }
            normalized, confidence = weighted_score(weighted_components, weights)
            score = None if normalized is None else round(100.0 * normalized, 2)
            label = status_label(score, str(formula.get("score_direction") or "risk"), formula.get("thresholds") or {})
            component_payload = {
                key: _component_payload(result, float(weights.get(key) or 0.0))
                for key, result in component_results.items()
            }

            metadata: dict[str, Any] = {
                "calculation_type": "deterministic_formula",
                "validation_status": (formula.get("metadata") or {}).get("validation_status", "engineering_default"),
                "not_ml": True,
            }
            if formula.get("prediction_key") == "nutrient_stress_risk":
                water_score = finite_number((calculated.get("water_stress") or {}).get("score")) or 0.0
                heat_score = finite_number((calculated.get("heat_stress") or {}).get("score")) or 0.0
                specificity = clip01(1.0 - max(water_score, heat_score) / 100.0)
                metadata["diagnostic_specificity"] = round(specificity, 4)
                metadata["interpretation_note"] = (
                    "This is nutrient-stress risk evidence, not a diagnosis of N/P/K deficiency or a fertilizer-dose recommendation."
                )
            if formula.get("prediction_key") == "erosion_risk":
                metadata["interpretation_note"] = "Relative erosion susceptibility proxy; not a full RUSLE soil-loss estimate."

            row = {
                "farm_id": str(feature_row["farm_id"]),
                "farmer_id": str(feature_row["farmer_id"]),
                "fpo_id": str(feature_row["fpo_id"]) if feature_row.get("fpo_id") else None,
                "h3_index": int(feature_row["h3_index"]),
                "h3_resolution": int(feature_row["h3_resolution"]),
                "result_scope": "h3",
                "result_date": feature_row["feature_date"],
                "crop_code": feature_row["crop_code"],
                "prediction_key": formula["prediction_key"],
                "display_name": formula["display_name"],
                "score": score,
                "score_direction": formula["score_direction"],
                "status_label": label,
                "confidence": round(float(confidence), 4),
                "affected_area_percent": None,
                "formula_version": formula["formula_version"],
                "crop_profile_version": feature_row["crop_profile_version"],
                "feature_version": feature_row["feature_version"],
                "components": component_payload,
                "evidence": _evidence(component_payload, formula["score_direction"]),
                "quality": {
                    "feature_confidence": feature_row.get("confidence"),
                    "source_quality": quality.get("source_quality") or {},
                    "formula_confidence": round(float(confidence), 4),
                },
                "metadata": metadata,
                "observed_area_m2": feature_row.get("observed_area_m2"),
            }
            results.append(row)
            calculated[formula["prediction_key"]] = row

    return results


def aggregate_farm_predictions(
    *,
    h3_rows: list[dict[str, Any]],
    formulas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    formula_map = {formula["prediction_key"]: formula for formula in formulas}
    grouped: dict[tuple[Any, str], list[dict[str, Any]]] = defaultdict(list)
    for row in h3_rows:
        grouped[(row["result_date"], row["prediction_key"])].append(row)

    farm_rows: list[dict[str, Any]] = []
    for (result_date, prediction_key), rows in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        formula = formula_map.get(prediction_key)
        if not formula:
            continue
        weighted_pairs = []
        total_area = 0.0
        affected_area = 0.0
        component_aggregate: dict[str, list[tuple[float | None, float | None]]] = defaultdict(list)

        affected_threshold = float((formula.get("thresholds") or {}).get(
            "affected_threshold", 60 if formula.get("score_direction") == "risk" else 40
        ))
        for row in rows:
            score = finite_number(row.get("score"))
            confidence = clip01(float(row.get("confidence") or 0.0))
            area = finite_number(row.get("observed_area_m2"))
            if area is None or area <= 0:
                area = 1.0
            effective_area = area * confidence
            weighted_pairs.append((score, effective_area))
            total_area += area
            if score is not None:
                is_affected = score >= affected_threshold if formula.get("score_direction") == "risk" else score <= affected_threshold
                if is_affected:
                    affected_area += area
            for key, component in (row.get("components") or {}).items():
                component_aggregate[key].append((component.get("value"), effective_area))

        score = safe_weighted_mean(weighted_pairs)
        farm_confidence = safe_weighted_mean([
            (row.get("confidence"), finite_number(row.get("observed_area_m2")) or 1.0) for row in rows
        ]) or 0.0
        components = {}
        for key, pairs in component_aggregate.items():
            components[key] = {"value": safe_weighted_mean(pairs)}
        affected = (100.0 * affected_area / total_area) if total_area > 0 else None
        first = rows[0]
        farm_rows.append({
            "farm_id": first["farm_id"],
            "farmer_id": first["farmer_id"],
            "fpo_id": first.get("fpo_id"),
            "h3_index": None,
            "h3_resolution": None,
            "result_scope": "farm",
            "result_date": result_date,
            "crop_code": first["crop_code"],
            "prediction_key": prediction_key,
            "display_name": first["display_name"],
            "score": None if score is None else round(float(score), 2),
            "score_direction": formula["score_direction"],
            "status_label": status_label(score, formula["score_direction"], formula.get("thresholds") or {}),
            "confidence": round(float(farm_confidence), 4),
            "affected_area_percent": None if affected is None else round(affected, 2),
            "formula_version": formula["formula_version"],
            "crop_profile_version": first["crop_profile_version"],
            "feature_version": first["feature_version"],
            "components": components,
            "evidence": _evidence(first.get("components") or {}, formula["score_direction"]),
            "quality": {
                "aggregation": "area_x_h3_formula_confidence",
                "h3_count": len(rows),
                "farm_confidence": round(float(farm_confidence), 4),
            },
            "metadata": {
                "calculation_type": "deterministic_formula_farm_aggregate",
                "grid_semantics": "Farm score is aggregated from H3 formula results. The 10 m frontend grid is a display projection, not independent 10 m measurement.",
            },
        })
    return farm_rows


def project_h3_predictions_to_grid(
    *,
    h3_rows: list[dict[str, Any]],
    crosswalk: list[dict[str, Any]],
    formulas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    formula_map = {formula["prediction_key"]: formula for formula in formulas}
    by_h3: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for cross in crosswalk:
        by_h3[int(cross["h3_index"])].append(cross)

    grouped: dict[tuple[str, Any, str, str], list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for result in h3_rows:
        for cross in by_h3.get(int(result["h3_index"]), []):
            key = (
                str(cross["grid_cell_id"]),
                result["result_date"],
                result["prediction_key"],
                result["formula_version"],
            )
            grouped[key].append((result, cross))

    output = []
    for (grid_cell_id, result_date, prediction_key, formula_version), contributions in grouped.items():
        formula = formula_map.get(prediction_key)
        if not formula:
            continue
        pairs = []
        confidence_pairs = []
        dominant = None
        max_overlap = -1.0
        component_pairs: dict[str, list[tuple[float | None, float | None]]] = defaultdict(list)
        for result, cross in contributions:
            overlap = max(0.0, float(cross.get("overlap_ratio") or 0.0))
            confidence = clip01(float(result.get("confidence") or 0.0))
            effective = overlap * max(confidence, 0.01)
            pairs.append((result.get("score"), effective))
            confidence_pairs.append((confidence, overlap))
            if overlap > max_overlap:
                max_overlap = overlap
                dominant = result.get("h3_index")
            for component_key, component in (result.get("components") or {}).items():
                component_pairs[component_key].append((component.get("value"), effective))

        score = safe_weighted_mean(pairs)
        confidence = safe_weighted_mean(confidence_pairs) or 0.0
        components = {key: {"value": safe_weighted_mean(values)} for key, values in component_pairs.items()}
        first = contributions[0][0]
        evidence = _evidence(first.get("components") or {}, formula["score_direction"])
        output.append({
            "farm_id": first["farm_id"],
            "grid_cell_id": grid_cell_id,
            "result_date": result_date,
            "crop_code": first["crop_code"],
            "prediction_key": prediction_key,
            "display_name": first["display_name"],
            "score": None if score is None else round(float(score), 2),
            "score_direction": formula["score_direction"],
            "status_label": status_label(score, formula["score_direction"], formula.get("thresholds") or {}),
            "confidence": round(float(confidence), 4),
            "formula_version": formula_version,
            "crop_profile_version": first["crop_profile_version"],
            "feature_version": first["feature_version"],
            "value_source": "h3_formula_grid_overlap_weighted",
            "contributing_h3_count": len(contributions),
            "dominant_h3_index": dominant,
            "max_h3_overlap_ratio": max_overlap if max_overlap >= 0 else None,
            "components": components,
            "evidence": evidence,
        })
    return output
