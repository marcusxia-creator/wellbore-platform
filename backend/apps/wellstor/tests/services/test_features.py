"""Pure-logic tests for composed WellFeature calculations. No database."""

from datetime import date

from apps.wellstor.services.features import (
    compute_well_feature_metrics,
    percentage_top_depth_md_tvd,
    usable_air_mass,
)


class TestPercentageTopDepth:
    def test_ratio(self):
        assert percentage_top_depth_md_tvd(800, 1000) == 0.8

    def test_zero_or_missing_top(self):
        assert percentage_top_depth_md_tvd(800, 0) is None
        assert percentage_top_depth_md_tvd(800, None) is None


class TestUsableAirMass:
    def test_factor_is_point_zero_eight(self):
        assert usable_air_mass(3000, 100) == 24000.0

    def test_missing(self):
        assert usable_air_mass(None, 100) is None


class TestComputeWellFeatureMetrics:
    def test_wires_volume_pressure_and_flags(self):
        result = compute_well_feature_metrics(
            deepest_casing_size=177.8,
            deepest_casing_depth=2000,
            deepest_casing_weight=34.2,
            deepest_casing_grade="L080",
            liner_start_m=1200,
            perforation_top_depth_md=1500,
            tvd_m=1000,
            well_status_text="SUSPENDED",
            last_prod=date(2023, 1, 1),
            last_inj=None,
            as_of=date(2025, 1, 1),
        )

        assert result["depth_for_available_volume"] == 1200
        assert result["pressure_grade"] == 80.0
        assert result["deepest_casing_id"] is not None
        assert result["casing_burst_rating_psi"] is not None
        assert result["available_wellbore_volume_m3"] is not None
        assert result["normalized_available_volume"] is not None
        assert result["percentage_top_depth_md_tvd"] == 1000 / 1500
        assert result["usable_air_mass"] == 0.08 * result["casing_burst_rating_psi"] * result[
            "normalized_available_volume"
        ]
        assert result["idle_well_flag"] is True
        assert result["wellstor_flag"] is True
        assert result["months_since_last_prod"] == 24
        assert result["months_since_last_inj"] is None

    def test_missing_inputs_leave_dependent_fields_none(self):
        result = compute_well_feature_metrics()
        assert result["deepest_casing_id"] is None
        assert result["available_wellbore_volume_m3"] is None
        assert result["usable_air_mass"] is None
        assert result["idle_well_flag"] is False
        assert result["wellstor_flag"] is False
