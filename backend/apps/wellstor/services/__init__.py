"""Pure calculation services for WellStor feature columns.

Formulas match the upstream preprocessing library. These functions do not read
or write the database; later ingest/write layers call them and persist the
returned values on `WellFeature`.
"""

from .casing import (
    STEEL_DENSITY_KG_M3,
    casing_burst_rating_psi,
    deepest_casing_id,
    max_casing_volume_m3,
    pressure_grade,
    select_deepest_casing,
)
from .features import compute_well_feature_metrics, percentage_top_depth_md_tvd, usable_air_mass
from .geometry import air_mass_from_pressure_volume, cylinder_volume_m3, haversine_km, parse_numeric
from .status import idle_well_flag, is_orphan_reclaimed, is_surface_abandoned, months_between, wellstor_flag
from .volume import (
    available_wellbore_volume_m3,
    below_volume_threshold,
    classify_deviation,
    depth_for_available_volume,
    deviation_angle,
    normalized_available_volume,
)

__all__ = [
    "STEEL_DENSITY_KG_M3",
    "air_mass_from_pressure_volume",
    "available_wellbore_volume_m3",
    "below_volume_threshold",
    "casing_burst_rating_psi",
    "classify_deviation",
    "compute_well_feature_metrics",
    "cylinder_volume_m3",
    "deepest_casing_id",
    "depth_for_available_volume",
    "deviation_angle",
    "haversine_km",
    "idle_well_flag",
    "is_orphan_reclaimed",
    "is_surface_abandoned",
    "max_casing_volume_m3",
    "months_between",
    "normalized_available_volume",
    "parse_numeric",
    "percentage_top_depth_md_tvd",
    "pressure_grade",
    "select_deepest_casing",
    "usable_air_mass",
    "wellstor_flag",
]
