"""Compose the computed `WellFeature` columns from raw well inputs."""

from __future__ import annotations

from .casing import casing_burst_rating_psi, deepest_casing_id, max_casing_volume_m3, pressure_grade
from .geometry import parse_numeric
from .status import idle_well_flag, wellstor_flag
from .volume import available_wellbore_volume_m3, depth_for_available_volume, normalized_available_volume

USABLE_AIR_MASS_FACTOR = 0.08


def percentage_top_depth_md_tvd(tvd_m, perforation_top_depth_md) -> float | None:
    """``tvd_m / perforation_top_depth_md``; None when the top depth is missing or zero."""
    tvd = parse_numeric(tvd_m)
    top = parse_numeric(perforation_top_depth_md)
    if tvd is None or top is None or top == 0:
        return None
    return tvd / top


def usable_air_mass(burst_rating_psi, normalized_volume) -> float | None:
    """ML processed-data approximation: ``0.08 * burst_psi * normalized_volume``."""
    burst = parse_numeric(burst_rating_psi)
    volume = parse_numeric(normalized_volume)
    if burst is None or volume is None:
        return None
    return USABLE_AIR_MASS_FACTOR * burst * volume


def compute_well_feature_metrics(
    *,
    deepest_casing_size=None,
    deepest_casing_depth=None,
    deepest_casing_weight=None,
    deepest_casing_grade=None,
    liner_start_m=None,
    perforation_top_depth_md=None,
    tvd_m=None,
    well_status_text=None,
    last_prod=None,
    last_inj=None,
    as_of=None,
) -> dict:
    """Return the calculated `WellFeature` columns for one well.

    Missing inputs yield ``None`` for the fields that depend on them. No database
    access; the caller persists the dict onto a `WellFeature` row.
    """
    casing_id = deepest_casing_id(deepest_casing_size, deepest_casing_weight)
    grade = pressure_grade(deepest_casing_grade)
    burst = casing_burst_rating_psi(deepest_casing_size, casing_id, grade)
    max_volume = max_casing_volume_m3(deepest_casing_size, deepest_casing_depth)
    available_depth = depth_for_available_volume(
        deepest_casing_depth, liner_start_m, perforation_top_depth_md
    )
    available_volume = available_wellbore_volume_m3(
        deepest_casing_size, deepest_casing_depth, liner_start_m, perforation_top_depth_md
    )
    normalized = normalized_available_volume(available_volume, tvd_m, available_depth)
    idle, months_prod, months_inj = idle_well_flag(last_prod, last_inj, as_of=as_of)

    return {
        "deepest_casing_id": casing_id,
        "pressure_grade": grade,
        "casing_burst_rating_psi": burst,
        "max_casing_volume_m3": max_volume,
        "depth_for_available_volume": available_depth,
        "available_wellbore_volume_m3": available_volume,
        "normalized_available_volume": normalized,
        "percentage_top_depth_md_tvd": percentage_top_depth_md_tvd(tvd_m, perforation_top_depth_md),
        "usable_air_mass": usable_air_mass(burst, normalized),
        "months_since_last_prod": months_prod,
        "months_since_last_inj": months_inj,
        "idle_well_flag": idle,
        "wellstor_flag": wellstor_flag(well_status_text, idle),
    }
