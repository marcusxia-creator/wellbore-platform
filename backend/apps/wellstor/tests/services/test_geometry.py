"""Pure-logic tests for geometry helpers. No database."""

import math

from apps.wellstor.services.geometry import (
    air_mass_from_pressure_volume,
    cylinder_volume_m3,
    haversine_km,
    parse_numeric,
)


class TestParseNumeric:
    def test_strips_unit_suffix(self):
        assert parse_numeric("244.5mm") == 244.5

    def test_extracts_digits_from_grade(self):
        assert parse_numeric("J055") == 55.0

    def test_none_and_blank(self):
        assert parse_numeric(None) is None
        assert parse_numeric("") is None
        assert parse_numeric("   ") is None


class TestCylinderVolume:
    def test_known_cylinder(self):
        # r = 0.1 m, h = 10 m → π * 0.01 * 10
        assert cylinder_volume_m3(200, 10) == math.pi * 0.1**2 * 10

    def test_missing_input(self):
        assert cylinder_volume_m3(None, 10) is None
        assert cylinder_volume_m3(200, None) is None


class TestAirMass:
    def test_matches_ideal_gas_formula(self):
        p_psi, v_m3, t_c = 1000.0, 10.0, 25.0
        expected = (1000.0 * 6894.76 * 10.0) / (287.0 * (25.0 + 273.15))
        assert air_mass_from_pressure_volume(p_psi, v_m3, t_c) == expected

    def test_missing_input(self):
        assert air_mass_from_pressure_volume(None, 10) is None


class TestHaversine:
    def test_same_point_is_zero(self):
        assert haversine_km(55.0, -114.0, 55.0, -114.0) == 0.0

    def test_missing_coord(self):
        assert haversine_km(None, -114.0, 55.0, -114.0) is None
