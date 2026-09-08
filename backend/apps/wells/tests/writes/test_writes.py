"""Integration tests for the wells write layer (cache-table refresh).

These run the raw-SQL refresh functions against a real PostgreSQL test database
and assert the derived cache tables are populated correctly.

All tests use transaction=True because the refresh functions execute TRUNCATE
(which issues an implicit commit in some DB modes) followed by INSERT.
"""

import pytest

from apps.wells import writes
from apps.wells.models import WellCurrentOperator, WellProductionFormation, WellStatusCategory
from apps.wells.tests.factories import (
    WellHeaderFactory,
    WellProductionSummaryFactory,
    WellStatusFactory,
)

pytestmark = pytest.mark.django_db(transaction=True)


class TestRefreshWellStatusCategories:
    def test_categorizes_abd_well(self):
        header = WellHeaderFactory(base_uwi="ABD-1")
        WellStatusFactory(base_uwi=header, well_status_text="Well ABD")

        count = writes.refresh_well_status_categories()

        assert count >= 1
        row = WellStatusCategory.objects.get(base_uwi="ABD-1")
        assert row.status_category == "ABD"

    def test_categorizes_suspended_well(self):
        header = WellHeaderFactory(base_uwi="SUSP-1")
        WellStatusFactory(base_uwi=header, well_status_text="Suspended well")

        writes.refresh_well_status_categories()

        row = WellStatusCategory.objects.get(base_uwi="SUSP-1")
        assert row.status_category == "Suspended"

    def test_active_well_with_no_old_activity(self):
        header = WellHeaderFactory(base_uwi="ACT-1")
        WellStatusFactory(base_uwi=header, well_status_text="Flowing")

        writes.refresh_well_status_categories()

        row = WellStatusCategory.objects.get(base_uwi="ACT-1")
        assert row.status_category == "Active"


class TestRefreshWellProductionFormations:
    def test_splits_semicolon_separated_formations(self):
        header = WellHeaderFactory(base_uwi="FRM-1")
        WellProductionSummaryFactory(
            base_uwi=header, prod_inject_frmtn="Cardium;Viking"
        )

        mapping_count, formation_count = writes.refresh_well_production_formations()

        assert mapping_count == 2
        assert formation_count == 2
        formations = set(
            WellProductionFormation.objects.filter(base_uwi="FRM-1").values_list(
                "formation", flat=True
            )
        )
        assert formations == {"Cardium", "Viking"}

    def test_ignores_blank_formation(self):
        header = WellHeaderFactory(base_uwi="FRM-2")
        WellProductionSummaryFactory(base_uwi=header, prod_inject_frmtn="Cardium; ")

        mapping_count, _ = writes.refresh_well_production_formations()

        formations = set(
            WellProductionFormation.objects.filter(base_uwi="FRM-2").values_list(
                "formation", flat=True
            )
        )
        assert formations == {"Cardium"}

    @pytest.mark.parametrize(
        "raw_value, expected_formations",
        [
            ("Cardium", {"Cardium"}),
            ("Cardium;Viking", {"Cardium", "Viking"}),
            ("Cardium; Viking ; Belly River", {"Cardium", "Viking", "Belly River"}),
        ],
        ids=["single", "two-formations", "three-with-spaces"],
    )
    def test_splits_various_formation_strings(self, raw_value, expected_formations):
        uwi = f"FRM-PARAM-{raw_value[:4]}"
        header = WellHeaderFactory(base_uwi=uwi)
        WellProductionSummaryFactory(base_uwi=header, prod_inject_frmtn=raw_value)

        writes.refresh_well_production_formations()

        result = set(
            WellProductionFormation.objects.filter(base_uwi=uwi).values_list(
                "formation", flat=True
            )
        )
        assert result == expected_formations


class TestRefreshWellCurrentOperators:
    def test_creates_one_row_per_well(self):
        WellHeaderFactory(base_uwi="CO-1")
        WellHeaderFactory(base_uwi="CO-2")
        WellStatusFactory(base_uwi__base_uwi="CO-1", cur_operator_name="Alpha Corp")
        WellStatusFactory(base_uwi__base_uwi="CO-2", cur_operator_name="Beta Inc")

        count = writes.refresh_well_current_operators()

        assert count >= 2

    def test_stores_operator_name_from_well_status(self):
        header = WellHeaderFactory(base_uwi="CO-STATUS-1")
        WellStatusFactory(base_uwi=header, cur_operator_name="Saguaro Petroleum")

        writes.refresh_well_current_operators()

        row = WellCurrentOperator.objects.get(base_uwi="CO-STATUS-1")
        assert row.operator_name == "Saguaro Petroleum"

    def test_falls_back_to_well_header_operator(self):
        """When well_status has no cur_operator_name, use well_header value."""
        WellHeaderFactory(base_uwi="CO-HDR-1", cur_operator_name="Header Operator")
        # Status row exists but has no operator name
        WellStatusFactory(
            base_uwi__base_uwi="CO-HDR-1",
            cur_operator_name=None,
        )

        writes.refresh_well_current_operators()

        row = WellCurrentOperator.objects.get(base_uwi="CO-HDR-1")
        assert row.operator_name == "Header Operator"

    def test_uses_unknown_when_no_operator_available(self):
        """Falls back to 'Unknown' when neither table provides an operator name."""
        WellHeaderFactory(base_uwi="CO-UNK-1", cur_operator_name=None)
        WellStatusFactory(base_uwi__base_uwi="CO-UNK-1", cur_operator_name=None)

        writes.refresh_well_current_operators()

        row = WellCurrentOperator.objects.get(base_uwi="CO-UNK-1")
        assert row.operator_name == "Unknown"

    def test_picks_latest_suffix_when_multiple_status_rows_exist(self):
        """With suffix 00 and 01 for the same well, suffix 01 wins."""
        header = WellHeaderFactory(base_uwi="CO-MULTI-1")
        WellStatusFactory(base_uwi=header, suffix="00", cur_operator_name="Old Operator")
        WellStatusFactory(base_uwi=header, suffix="01", cur_operator_name="New Operator")

        writes.refresh_well_current_operators()

        row = WellCurrentOperator.objects.get(base_uwi="CO-MULTI-1")
        assert row.operator_name == "New Operator"

    def test_truncates_before_repopulating(self):
        """Running refresh twice must not double-count rows."""
        WellHeaderFactory(base_uwi="CO-TWICE-1")
        WellStatusFactory(base_uwi__base_uwi="CO-TWICE-1", cur_operator_name="Alpha")

        writes.refresh_well_current_operators()
        count_first = WellCurrentOperator.objects.count()

        writes.refresh_well_current_operators()
        count_second = WellCurrentOperator.objects.count()

        assert count_first == count_second

    @pytest.mark.parametrize(
        "operator_name",
        ["Saguaro Petroleum LLC", "ALPHA CORP", "beta & associates"],
        ids=["mixed-case", "all-upper", "special-chars"],
    )
    def test_preserves_operator_name_exactly(self, operator_name):
        uwi = f"CO-EXACT-{operator_name[:4].upper()}"
        header = WellHeaderFactory(base_uwi=uwi)
        WellStatusFactory(base_uwi=header, cur_operator_name=operator_name)

        writes.refresh_well_current_operators()

        row = WellCurrentOperator.objects.get(base_uwi=uwi)
        assert row.operator_name == operator_name
