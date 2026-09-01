"""Casing-derived calculations: deepest string, inner diameter, burst rating, max volume."""

from __future__ import annotations

import math
import re

from .geometry import cylinder_volume_m3, is_missing, parse_numeric

STEEL_DENSITY_KG_M3 = 7925.0

_EMPTY_DEEPEST = {
    "deepest_casing_type": None,
    "deepest_casing_depth": None,
    "deepest_casing_size": None,
    "deepest_casing_grade": None,
    "deepest_casing_weight": None,
}


def select_deepest_casing(data: dict | None) -> dict:
    """Pick the deepest Intermediate/Production string, else the deepest of any type."""
    if not isinstance(data, dict) or not data:
        return dict(_EMPTY_DEEPEST)

    preferred = ("Intermediate", "Production")

    def valid_depth(entry):
        if not isinstance(entry, dict):
            return None
        try:
            depth = float(entry.get("depth"))
        except (TypeError, ValueError):
            return None
        return None if math.isnan(depth) else depth

    pool = {}
    for key in preferred:
        depth = valid_depth(data.get(key))
        if depth is not None:
            pool[key] = (data[key], depth)

    if not pool:
        for key, entry in data.items():
            depth = valid_depth(entry)
            if depth is not None:
                pool[key] = (entry, depth)

    if not pool:
        return dict(_EMPTY_DEEPEST)

    deepest_key = max(pool, key=lambda key: pool[key][1])
    selected, depth_val = pool[deepest_key]
    return {
        "deepest_casing_type": deepest_key,
        "deepest_casing_depth": depth_val,
        "deepest_casing_size": selected.get("size"),
        "deepest_casing_grade": selected.get("grade"),
        "deepest_casing_weight": selected.get("weight"),
    }


def _diameter_to_m(value) -> float | None:
    """Treat values marked mm, or numeric values > 10, as millimetres."""
    if is_missing(value):
        return None
    parsed = parse_numeric(value)
    if parsed is None:
        return None
    as_mm = "mm" in str(value).lower() or parsed > 10
    return parsed / 1000 if as_mm else parsed


def _od_to_inches(value) -> float | None:
    """Treat values marked mm, or numeric values > 20, as millimetres."""
    if is_missing(value):
        return None
    parsed = parse_numeric(value)
    if parsed is None:
        return None
    as_mm = "mm" in str(value).lower() or parsed > 20
    return parsed / 25.4 if as_mm else parsed


def deepest_casing_id(outer_diameter, weight_kg_per_m) -> float | None:
    """Inner diameter (mm) from OD + linear weight, assuming steel casing."""
    od_m = _diameter_to_m(outer_diameter)
    weight = parse_numeric(weight_kg_per_m)
    if od_m is None or weight is None:
        return None
    id_sq = od_m**2 - (4.0 * weight) / (math.pi * STEEL_DENSITY_KG_M3)
    if id_sq <= 0:
        return None
    return math.sqrt(id_sq) * 1000


def pressure_grade(grade) -> float | None:
    """Numeric ksi extracted from a casing-grade string such as ``J055`` or ``L080``."""
    if is_missing(grade):
        return None
    match = re.search(r"(\d+\.?\d*)", str(grade))
    if not match:
        return None
    try:
        return float(match.group(1))
    except (TypeError, ValueError):
        return None


def casing_burst_rating_psi(
    outer_diameter,
    inner_diameter,
    grade_ksi,
    design_factor: float = 0.8,
) -> float | None:
    """Simplified Barlow burst-pressure rating (psi), de-rated by ``design_factor``."""
    od_in = _od_to_inches(outer_diameter)
    id_in = _od_to_inches(inner_diameter)
    grade = parse_numeric(grade_ksi)
    if od_in is None or id_in is None or grade is None:
        return None
    if od_in <= 0 or id_in <= 0 or id_in >= od_in:
        return None
    wall_in = (od_in - id_in) / 2.0
    yield_psi = grade * 1000.0
    rating = 0.875 * (2.0 * yield_psi * wall_in) / od_in
    return rating * design_factor


def max_casing_volume_m3(outer_diameter, casing_depth) -> float | None:
    """Cylinder volume of the deepest casing string using full casing depth."""
    return cylinder_volume_m3(outer_diameter, casing_depth)
