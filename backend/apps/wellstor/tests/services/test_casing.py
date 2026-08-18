"""Pure-logic tests for casing calculations. No database."""

import math

from apps.wellstor.services.casing import (
    STEEL_DENSITY_KG_M3,
    casing_burst_rating_psi,
    deepest_casing_id,
    max_casing_volume_m3,
    pressure_grade,
    select_deepest_casing,
)


class TestSelectDeepestCasing:
    def test_prefers_deeper_production_over_shallower_intermediate(self):
        selected = select_deepest_casing(
            {
                "Intermediate": {"depth": 800, "size": 244.5, "grade": "K055", "weight": 70},
                "Production": {"depth": 1500, "size": 177.8, "grade": "L080", "weight": 34},
                "Surface": {"depth": 200, "size": 339.7, "grade": "J055", "weight": 80},
            }
        )
        assert selected["deepest_casing_type"] == "Production"
        assert selected["deepest_casing_depth"] == 1500
        assert selected["deepest_casing_size"] == 177.8

    def test_falls_back_to_any_type_when_no_preferred(self):
        selected = select_deepest_casing(
            {"Surface": {"depth": 200, "size": 339.7, "grade": "J055", "weight": 80}}
        )
        assert selected["deepest_casing_type"] == "Surface"
        assert selected["deepest_casing_depth"] == 200

    def test_empty_input(self):
        selected = select_deepest_casing({})
        assert selected["deepest_casing_type"] is None
        assert selected["deepest_casing_depth"] is None


class TestDeepestCasingId:
    def test_matches_steel_wall_formula(self):
        od_mm, weight = 177.8, 34.2
        od_m = od_mm / 1000
        expected = math.sqrt(od_m**2 - (4.0 * weight) / (math.pi * STEEL_DENSITY_KG_M3)) * 1000
        assert deepest_casing_id(od_mm, weight) == expected

    def test_parses_mm_string(self):
        assert deepest_casing_id("177.8mm", 34.2) == deepest_casing_id(177.8, 34.2)

    def test_impossible_wall_returns_none(self):
        assert deepest_casing_id(177.8, 10_000) is None

    def test_missing_input(self):
        assert deepest_casing_id(None, 34.2) is None


class TestPressureGrade:
    def test_extracts_from_letter_grade(self):
        assert pressure_grade("J055") == 55.0
        assert pressure_grade("L080") == 80.0
        assert pressure_grade("P110") == 110.0

    def test_missing(self):
        assert pressure_grade(None) is None
        assert pressure_grade("") is None


class TestBurstRating:
    def test_barlow_with_design_factor(self):
        od_mm, id_mm, grade = 177.8, 159.4, 80.0
        od_in = od_mm / 25.4
        id_in = id_mm / 25.4
        wall = (od_in - id_in) / 2.0
        expected = 0.875 * (2.0 * grade * 1000.0 * wall) / od_in * 0.8
        assert casing_burst_rating_psi(od_mm, id_mm, grade) == expected

    def test_id_not_smaller_than_od(self):
        assert casing_burst_rating_psi(177.8, 177.8, 80) is None


class TestMaxCasingVolume:
    def test_uses_full_casing_depth(self):
        assert max_casing_volume_m3(200, 10) == math.pi * 0.1**2 * 10
