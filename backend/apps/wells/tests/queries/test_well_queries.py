"""Integration tests for the wells read layer (queries).

These hit a real PostgreSQL test database because the queries rely on
Postgres-only features (DISTINCT ON, subquery annotations).
"""

import pytest

from apps.wells.queries import MetadataQueries, WellQueries
from apps.wells.tests.factories import (
    WellHeaderFactory,
    WellProductionFormationFactory,
    WellStatusCategoryFactory,
)

pytestmark = pytest.mark.django_db


class TestWellQueriesFilter:
    def test_returns_all_when_no_filters(self):
        WellHeaderFactory.create_batch(3)
        result = WellQueries.filter_wells(WellQueries.get_annotated_queryset())
        assert result.count() == 3

    def test_filters_by_well_type(self):
        WellHeaderFactory(base_uwi="OIL-1", well_type="OIL")
        WellHeaderFactory(base_uwi="GAS-1", well_type="GAS")
        result = WellQueries.filter_wells(WellQueries.get_annotated_queryset(), well_type="OIL")
        assert [w.base_uwi for w in result] == ["OIL-1"]

    def test_filters_by_search_on_well_name(self):
        WellHeaderFactory(base_uwi="A-1", well_name="Walrus North")
        WellHeaderFactory(base_uwi="B-1", well_name="Beluga South")
        result = WellQueries.filter_wells(WellQueries.get_annotated_queryset(), search="walrus")
        assert [w.base_uwi for w in result] == ["A-1"]

    def test_filters_by_status_category(self):
        WellHeaderFactory(base_uwi="ACT-1")
        WellHeaderFactory(base_uwi="ABD-1")
        WellStatusCategoryFactory(base_uwi="ACT-1", status_category="Active")
        WellStatusCategoryFactory(base_uwi="ABD-1", status_category="ABD")
        result = WellQueries.filter_wells(WellQueries.get_annotated_queryset(), status="Active")
        assert [w.base_uwi for w in result] == ["ACT-1"]

    def test_filters_by_formation(self):
        WellHeaderFactory(base_uwi="F-1")
        WellHeaderFactory(base_uwi="F-2")
        WellProductionFormationFactory(base_uwi="F-1", formation="Cardium")
        WellProductionFormationFactory(base_uwi="F-2", formation="Viking")
        result = WellQueries.filter_wells(
            WellQueries.get_annotated_queryset(), formations=["Cardium"]
        )
        assert [w.base_uwi for w in result] == ["F-1"]


class TestWellQueriesAnnotation:
    def test_annotates_status_category_value(self):
        WellHeaderFactory(base_uwi="X-1")
        WellStatusCategoryFactory(base_uwi="X-1", status_category="Suspended")
        well = WellQueries.get_annotated_queryset().get(base_uwi="X-1")
        assert well.status_category_value == "Suspended"


class TestMetadataQueries:
    def test_get_well_types(self):
        WellHeaderFactory(well_type="OIL")
        WellHeaderFactory(well_type="GAS")
        assert set(MetadataQueries.get_well_types()) == {"OIL", "GAS"}

    def test_get_actual_well_statuses_filtered_by_category(self):
        WellStatusCategoryFactory(base_uwi="A-1", status_category="Active", actual_status_text="Flowing")
        WellStatusCategoryFactory(base_uwi="A-2", status_category="ABD", actual_status_text="Abandoned")
        result = MetadataQueries.get_actual_well_statuses(status_category="Active")
        assert list(result) == ["Flowing"]

    def test_get_production_injection_formations(self):
        WellProductionFormationFactory(base_uwi="A-1", formation="Cardium")
        WellProductionFormationFactory(base_uwi="A-2", formation="Viking")
        assert set(MetadataQueries.get_production_injection_formations()) == {"Cardium", "Viking"}
