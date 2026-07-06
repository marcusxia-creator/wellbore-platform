"""Integration tests for the wells write layer (cache-table refresh).

These run the raw-SQL refresh functions against a real PostgreSQL test database
and assert the derived cache tables are populated correctly.
"""

import pytest

from apps.wells import writes
from apps.wells.models import WellProductionFormation, WellStatusCategory
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
