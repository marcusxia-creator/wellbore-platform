"""Numeric helpers shared by the casing, volume, and feature services."""

from __future__ import annotations

import math
import re


def is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def parse_numeric(value) -> float | None:
    """Extract the first signed float from a value such as ``'244.5mm'`` or ``'J055'``."""
    if is_missing(value):
        return None
    match = re.search(r"-?\d+\.?\d*", str(value))
    return float(match.group()) if match else None


def cylinder_volume_m3(diameter_mm, depth_m) -> float | None:
    """Volume (m3) of a cylinder. Diameter is in mm, length/depth is in m."""
    diameter_mm = parse_numeric(diameter_mm)
    depth_m = parse_numeric(depth_m)
    if diameter_mm is None or depth_m is None:
        return None
    radius_m = (diameter_mm / 1000) / 2
    return math.pi * radius_m**2 * depth_m


def air_mass_from_pressure_volume(p_psi, v_m3, t_c: float = 25) -> float | None:
    """Ideal-gas air mass (kg) at ``p_psi`` in volume ``v_m3`` at temperature ``t_c``."""
    p_psi = parse_numeric(p_psi)
    v_m3 = parse_numeric(v_m3)
    if p_psi is None or v_m3 is None:
        return None
    r = 287.0  # J/(kg*K), dry air
    p_pa = p_psi * 6894.76
    t_k = t_c + 273.15
    return (p_pa * v_m3) / (r * t_k)


def haversine_km(lat1, lon1, lat2, lon2) -> float | None:
    """Great-circle distance in kilometres between two WGS84 points."""
    try:
        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)
    except (TypeError, ValueError):
        return None
    if any(math.isnan(v) for v in (lat1, lon1, lat2, lon2)):
        return None

    r = 6371.0
    lat1_r = math.radians(lat1)
    lon1_r = math.radians(lon1)
    lat2_r = math.radians(lat2)
    lon2_r = math.radians(lon2)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
