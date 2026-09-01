"""End-to-end sample-data checks against real wells_processed output.

Each parametrized case is one row extracted from the DuckDB wells_processed
table. The expected values are the numbers the upstream preprocessing pipeline
wrote, so these tests verify our service implementations reproduce the same
results to within floating-point tolerance.

No database access is needed; all inputs and expected outputs are hardcoded
from the DuckDB snapshot.
"""

import math

import pytest

from apps.wellstor.services.casing import casing_burst_rating_psi, deepest_casing_id, max_casing_volume_m3, pressure_grade
from apps.wellstor.services.features import compute_well_feature_metrics, percentage_top_depth_md_tvd, usable_air_mass
from apps.wellstor.services.volume import available_wellbore_volume_m3, depth_for_available_volume

# ---------------------------------------------------------------------------
# Real rows from wells_processed (DuckDB snapshot).
# Field names match the WellFeature model / service function parameters.
# None means the column was NULL in the source data.
# ---------------------------------------------------------------------------
SAMPLE_WELLS = [
    {
        "well_id": "100/15-12-056-21W4",
        "deepest_casing_size": 219.1,
        "deepest_casing_depth": 782.5,
        "deepest_casing_weight": 35.7,
        "deepest_casing_grade": "J055",
        "tvd_m": 664.6,
        "perforation_top_depth_md": 480.0,
        "liner_start_m": None,
        # expected pipeline outputs
        "expected_depth_for_available_volume": 480.0,
        "expected_max_casing_volume_m3": 29.502511118450503,
        "expected_available_wellbore_volume_m3": 18.097387011956855,
        "expected_normalized_available_volume": 18.097387011956855,  # tvd/depth > 1, capped
        "expected_casing_burst_rating_psi": 2373.1244206417537,
        "expected_usable_air_mass": 3435.7880854303767,
        "expected_percentage_top_depth_md_tvd": 664.6 / 480.0,
    },
    {
        "well_id": "100/15-12-076-08W6",
        "deepest_casing_size": 139.7,
        "deepest_casing_depth": 1608.0,
        "deepest_casing_weight": 23.1,
        "deepest_casing_grade": "J055",
        "tvd_m": 1608.0,
        "perforation_top_depth_md": 1483.0,
        "liner_start_m": None,
        "expected_depth_for_available_volume": 1483.0,
        "expected_max_casing_volume_m3": 24.64726519826048,
        "expected_available_wellbore_volume_m3": 22.731277542923067,
        "expected_normalized_available_volume": 22.731277542923067,
        "expected_casing_burst_rating_psi": 3853.523985498488,
        "expected_usable_air_mass": 7007.6418586141735,
        "expected_percentage_top_depth_md_tvd": 1608.0 / 1483.0,
    },
    {
        "well_id": "100/15-13-010-17W4",
        "deepest_casing_size": 139.7,
        "deepest_casing_depth": 1117.0,
        "deepest_casing_weight": 20.8,
        "deepest_casing_grade": "J055",
        "tvd_m": 1007.3,
        "perforation_top_depth_md": 1077.0,
        "liner_start_m": None,
        "expected_depth_for_available_volume": 1077.0,
        "expected_max_casing_volume_m3": 17.12126568809512,
        "expected_available_wellbore_volume_m3": 16.50814963838715,
        "expected_normalized_available_volume": 15.439794921771009,   # TVD/depth < 1, scales down
        "expected_casing_burst_rating_psi": 3450.8424092642404,
        "expected_usable_air_mass": 4262.423928511204,
        "expected_percentage_top_depth_md_tvd": 1007.3 / 1077.0,
    },
    {
        "well_id": "100/15-13-054-17W4",
        "deepest_casing_size": 114.3,
        "deepest_casing_depth": 855.2,
        "deepest_casing_weight": 14.1,
        "deepest_casing_grade": "J055",
        "tvd_m": 856.0,
        "perforation_top_depth_md": 689.9,
        "liner_start_m": None,
        "expected_depth_for_available_volume": 689.9,
        "expected_max_casing_volume_m3": 8.775058781514646,
        "expected_available_wellbore_volume_m3": 7.078944169044614,
        "expected_normalized_available_volume": 7.078944169044614,
        "expected_casing_burst_rating_psi": 3496.647144331006,
        "expected_usable_air_mass": 1980.205593085478,
        "expected_percentage_top_depth_md_tvd": 856.0 / 689.9,
    },
    {
        "well_id": "100/15-13-059-26W5",
        "deepest_casing_size": 114.3,
        "deepest_casing_depth": 3125.0,
        "deepest_casing_weight": 17.3,
        "deepest_casing_grade": "P110",
        "tvd_m": 3112.7,
        "perforation_top_depth_md": 2635.5,
        "liner_start_m": None,
        "expected_depth_for_available_volume": 2635.5,
        "expected_max_casing_volume_m3": 32.06508266163853,
        "expected_available_wellbore_volume_m3": 27.042408113519468,
        "expected_normalized_available_volume": 27.042408113519468,
        "expected_casing_burst_rating_psi": 8680.017558808655,
        "expected_usable_air_mass": 18778.286180625488,
        "expected_percentage_top_depth_md_tvd": 3112.7 / 2635.5,
    },
]

REL_TOL = 1e-6  # 0.0001 % tolerance — matches floating-point of the original pipeline


def _rel_close(actual, expected, rel_tol=REL_TOL):
    """True when actual and expected agree to rel_tol relative tolerance."""
    if actual is None and expected is None:
        return True
    if actual is None or expected is None:
        return False
    return math.isclose(actual, expected, rel_tol=rel_tol)


@pytest.mark.parametrize("well", SAMPLE_WELLS, ids=[w["well_id"] for w in SAMPLE_WELLS])
class TestSampleDataChecks:
    """Verify every computed column against the DuckDB pipeline output."""

    def test_depth_for_available_volume(self, well):
        result = depth_for_available_volume(
            well["deepest_casing_depth"],
            well["liner_start_m"],
            well["perforation_top_depth_md"],
        )
        assert _rel_close(result, well["expected_depth_for_available_volume"]), (
            f"{well['well_id']}: depth_for_available_volume {result!r} != {well['expected_depth_for_available_volume']!r}"
        )

    def test_max_casing_volume(self, well):
        result = max_casing_volume_m3(well["deepest_casing_size"], well["deepest_casing_depth"])
        assert _rel_close(result, well["expected_max_casing_volume_m3"]), (
            f"{well['well_id']}: max_casing_volume_m3 {result!r} != {well['expected_max_casing_volume_m3']!r}"
        )

    def test_available_wellbore_volume(self, well):
        result = available_wellbore_volume_m3(
            well["deepest_casing_size"],
            well["deepest_casing_depth"],
            well["liner_start_m"],
            well["perforation_top_depth_md"],
        )
        assert _rel_close(result, well["expected_available_wellbore_volume_m3"]), (
            f"{well['well_id']}: available_wellbore_volume_m3 {result!r} != {well['expected_available_wellbore_volume_m3']!r}"
        )

    def test_burst_rating(self, well):
        grade = pressure_grade(well["deepest_casing_grade"])
        casing_id = deepest_casing_id(well["deepest_casing_size"], well["deepest_casing_weight"])
        result = casing_burst_rating_psi(well["deepest_casing_size"], casing_id, grade)
        assert _rel_close(result, well["expected_casing_burst_rating_psi"]), (
            f"{well['well_id']}: casing_burst_rating_psi {result!r} != {well['expected_casing_burst_rating_psi']!r}"
        )

    def test_usable_air_mass(self, well):
        grade = pressure_grade(well["deepest_casing_grade"])
        casing_id = deepest_casing_id(well["deepest_casing_size"], well["deepest_casing_weight"])
        burst = casing_burst_rating_psi(well["deepest_casing_size"], casing_id, grade)
        from apps.wellstor.services.volume import normalized_available_volume
        avail = available_wellbore_volume_m3(
            well["deepest_casing_size"], well["deepest_casing_depth"],
            well["liner_start_m"], well["perforation_top_depth_md"],
        )
        depth = depth_for_available_volume(
            well["deepest_casing_depth"], well["liner_start_m"], well["perforation_top_depth_md"]
        )
        norm = normalized_available_volume(avail, well["tvd_m"], depth)
        result = usable_air_mass(burst, norm)
        assert _rel_close(result, well["expected_usable_air_mass"]), (
            f"{well['well_id']}: usable_air_mass {result!r} != {well['expected_usable_air_mass']!r}"
        )

    def test_percentage_top_depth_md_tvd(self, well):
        result = percentage_top_depth_md_tvd(well["tvd_m"], well["perforation_top_depth_md"])
        assert _rel_close(result, well["expected_percentage_top_depth_md_tvd"]), (
            f"{well['well_id']}: percentage_top_depth_md_tvd {result!r} != {well['expected_percentage_top_depth_md_tvd']!r}"
        )

    def test_compute_well_feature_metrics_end_to_end(self, well):
        """compute_well_feature_metrics should reproduce all computed columns in one call."""
        metrics = compute_well_feature_metrics(
            deepest_casing_size=well["deepest_casing_size"],
            deepest_casing_depth=well["deepest_casing_depth"],
            deepest_casing_weight=well["deepest_casing_weight"],
            deepest_casing_grade=well["deepest_casing_grade"],
            liner_start_m=well["liner_start_m"],
            perforation_top_depth_md=well["perforation_top_depth_md"],
            tvd_m=well["tvd_m"],
        )
        assert _rel_close(metrics["max_casing_volume_m3"], well["expected_max_casing_volume_m3"])
        assert _rel_close(metrics["available_wellbore_volume_m3"], well["expected_available_wellbore_volume_m3"])
        assert _rel_close(metrics["normalized_available_volume"], well["expected_normalized_available_volume"])
        assert _rel_close(metrics["casing_burst_rating_psi"], well["expected_casing_burst_rating_psi"])
        assert _rel_close(metrics["usable_air_mass"], well["expected_usable_air_mass"])
        assert _rel_close(metrics["percentage_top_depth_md_tvd"], well["expected_percentage_top_depth_md_tvd"])
