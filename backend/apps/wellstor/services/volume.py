"""Available-wellbore-volume and deviation calculations."""

from __future__ import annotations

import math

from .geometry import cylinder_volume_m3, parse_numeric

VERTICAL_ANGLE_THRESHOLD = 10.0
SMALL_VOLUME_THRESHOLD_M3 = 5.0


def depth_for_available_volume(casing_depth, liner_start, top_depth_md) -> float | None:
    """Shallowest of casing shoe, liner top, and top perforation depth."""
    values = [parse_numeric(v) for v in (casing_depth, liner_start, top_depth_md)]
    present = [v for v in values if v is not None]
    return min(present) if present else None


def available_wellbore_volume_m3(diameter_mm, casing_depth, liner_start, top_depth_md) -> float | None:
    """Cylinder volume down to ``depth_for_available_volume``."""
    depth = depth_for_available_volume(casing_depth, liner_start, top_depth_md)
    if depth is None:
        return None
    return cylinder_volume_m3(diameter_mm, depth)


def normalized_available_volume(available_volume, tvd_m, available_depth) -> float | None:
    """Scale volume by ``TVD / depth_for_available_volume``, capped at 1."""
    volume = parse_numeric(available_volume)
    if volume is None:
        return None
    tvd = parse_numeric(tvd_m)
    depth = parse_numeric(available_depth)
    if tvd is None or depth is None or tvd == 0:
        return volume
    ratio = min(tvd / depth, 1.0)
    return ratio * volume


def below_volume_threshold(normalized_volume, threshold: float = SMALL_VOLUME_THRESHOLD_M3) -> bool:
    """True when normalized volume is present and below the candidate cutoff (default 5 m3)."""
    volume = parse_numeric(normalized_volume)
    return volume is not None and volume < threshold


def deviation_angle(md, tvd) -> float | None:
    """Deviation angle in degrees: ``acos(TVD / MD)``."""
    try:
        md = float(md)
        tvd = float(tvd)
    except (TypeError, ValueError):
        return None
    if md == 0 or math.isnan(md) or math.isnan(tvd):
        return None
    ratio = tvd / md
    if ratio < -1 or ratio > 1:
        return None
    return math.degrees(math.acos(ratio))


def classify_deviation(angle, vertical_threshold: float = VERTICAL_ANGLE_THRESHOLD) -> str | None:
    """Classify ``vertical`` / ``deviated`` / ``horizontal`` from a deviation angle."""
    try:
        angle = float(angle)
    except (TypeError, ValueError):
        return None
    if math.isnan(angle):
        return None
    if angle <= vertical_threshold:
        return "vertical"
    if angle >= (60 - vertical_threshold):
        return "horizontal"
    return "deviated"
