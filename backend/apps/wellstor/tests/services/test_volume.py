"""Pure-logic tests for volume and deviation calculations. No database."""

import math

from apps.wellstor.services.volume import (
    available_wellbore_volume_m3,
    below_volume_threshold,
    classify_deviation,
    depth_for_available_volume,
    deviation_angle,
    normalized_available_volume,
)


class TestDepthForAvailableVolume:
    def test_picks_the_shallowest_present_value(self):
        assert depth_for_available_volume(2000, 1200, 1500) == 1200

    def test_ignores_missing_values(self):
        assert depth_for_available_volume(2000, None, 1500) == 1500

    def test_all_missing(self):
        assert depth_for_available_volume(None, None, None) is None


class TestAvailableVolume:
    def test_uses_selected_depth(self):
        expected = math.pi * 0.1**2 * 1200
        assert available_wellbore_volume_m3(200, 2000, 1200, 1500) == expected


class TestNormalizedVolume:
    def test_scales_by_tvd_over_depth_and_caps_at_one(self):
        assert normalized_available_volume(10, 500, 1000) == 5.0
        assert normalized_available_volume(10, 2000, 1000) == 10.0

    def test_returns_raw_volume_when_tvd_missing(self):
        assert normalized_available_volume(10, None, 1000) == 10.0


class TestVolumeThreshold:
    def test_below_default_five(self):
        assert below_volume_threshold(4.9) is True
        assert below_volume_threshold(5.0) is False
        assert below_volume_threshold(None) is False


class TestDeviation:
    def test_vertical_well(self):
        angle = deviation_angle(md=1000, tvd=1000)
        assert angle == 0.0
        assert classify_deviation(angle) == "vertical"

    def test_deviated_and_horizontal(self):
        assert classify_deviation(25) == "deviated"
        assert classify_deviation(50) == "horizontal"

    def test_invalid_ratio(self):
        assert deviation_angle(md=100, tvd=200) is None
        assert classify_deviation(None) is None
