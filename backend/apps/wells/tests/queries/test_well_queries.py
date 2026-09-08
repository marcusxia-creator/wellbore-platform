"""Integration tests for the wells read layer (queries.py).

Tests run against a real PostgreSQL test database because the queries use
Postgres-specific features (DISTINCT ON, StringAgg subquery annotations).

Scope of this file: WellQueries, MetadataQueries.
Coverage is scoped to the methods that exist on this branch; ProductionQueries
tests live in the production-map PR.
"""

import pytest

from apps.wells.queries import MetadataQueries, WellQueries
from apps.wells.tests.factories import (
    WellCurrentOperatorFactory,
    WellHeaderFactory,
    WellProductionFormationFactory,
    WellStatusCategoryFactory,
    WellStatusFactory,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# WellQueries.filter_wells
# ---------------------------------------------------------------------------

class TestWellQueriesFilter:
    def test_returns_all_wells_when_no_filters_applied(self):
        WellHeaderFactory.create_batch(3)
        result = WellQueries.filter_wells(WellQueries.get_annotated_queryset())
        assert result.count() == 3

    @pytest.mark.parametrize(
        "well_type, expected_uwi",
        [
            ("OIL", "OIL-1"),
            ("GAS", "GAS-1"),
        ],
        ids=["filter-oil", "filter-gas"],
    )
    def test_filters_by_well_type(self, well_type, expected_uwi):
        WellHeaderFactory(base_uwi="OIL-1", well_type="OIL")
        WellHeaderFactory(base_uwi="GAS-1", well_type="GAS")
        result = WellQueries.filter_wells(
            WellQueries.get_annotated_queryset(), well_type=[well_type]
        )
        assert [w.base_uwi for w in result] == [expected_uwi]

    def test_well_type_filter_accepts_multiple_values(self):
        WellHeaderFactory(base_uwi="OIL-1", well_type="OIL")
        WellHeaderFactory(base_uwi="GAS-1", well_type="GAS")
        WellHeaderFactory(base_uwi="WTR-1", well_type="WATER")
        result = WellQueries.filter_wells(
            WellQueries.get_annotated_queryset(), well_type=["OIL", "GAS"]
        )
        assert {w.base_uwi for w in result} == {"OIL-1", "GAS-1"}

    @pytest.mark.parametrize(
        "search_term, expected_uwi",
        [
            ("walrus", "A-1"),
            ("beluga", "B-1"),
            ("A-1", "A-1"),
        ],
        ids=["search-name-walrus", "search-name-beluga", "search-uwi"],
    )
    def test_filters_by_search(self, search_term, expected_uwi):
        WellHeaderFactory(base_uwi="A-1", well_name="Walrus North")
        WellHeaderFactory(base_uwi="B-1", well_name="Beluga South")
        result = WellQueries.filter_wells(
            WellQueries.get_annotated_queryset(), search=search_term
        )
        assert [w.base_uwi for w in result] == [expected_uwi]

    @pytest.mark.parametrize(
        "status_filter, expected_uwi",
        [
            ("Active", "ACT-1"),
            ("ABD", "ABD-1"),
            ("Suspended", "SUSP-1"),
        ],
        ids=["status-active", "status-abd", "status-suspended"],
    )
    def test_filters_by_status_category(self, status_filter, expected_uwi):
        WellHeaderFactory(base_uwi="ACT-1")
        WellHeaderFactory(base_uwi="ABD-1")
        WellHeaderFactory(base_uwi="SUSP-1")
        WellStatusCategoryFactory(base_uwi="ACT-1", status_category="Active")
        WellStatusCategoryFactory(base_uwi="ABD-1", status_category="ABD")
        WellStatusCategoryFactory(base_uwi="SUSP-1", status_category="Suspended")
        result = WellQueries.filter_wells(
            WellQueries.get_annotated_queryset(), status=[status_filter]
        )
        assert [w.base_uwi for w in result] == [expected_uwi]

    def test_status_filter_accepts_multiple_values(self):
        WellHeaderFactory(base_uwi="ACT-1")
        WellHeaderFactory(base_uwi="ABD-1")
        WellHeaderFactory(base_uwi="SUSP-1")
        WellStatusCategoryFactory(base_uwi="ACT-1", status_category="Active")
        WellStatusCategoryFactory(base_uwi="ABD-1", status_category="ABD")
        WellStatusCategoryFactory(base_uwi="SUSP-1", status_category="Suspended")
        result = WellQueries.filter_wells(
            WellQueries.get_annotated_queryset(), status=["ABD", "Suspended"]
        )
        assert {w.base_uwi for w in result} == {"ABD-1", "SUSP-1"}

    def test_filters_by_actual_status(self):
        WellHeaderFactory(base_uwi="A-1")
        WellHeaderFactory(base_uwi="A-2")
        WellStatusCategoryFactory(base_uwi="A-1", actual_status_text="Flowing")
        WellStatusCategoryFactory(base_uwi="A-2", actual_status_text="Shut-In")
        result = WellQueries.filter_wells(
            WellQueries.get_annotated_queryset(), actual_status=["Flowing"]
        )
        assert [w.base_uwi for w in result] == ["A-1"]

    @pytest.mark.parametrize(
        "filter_formation, expected_uwis",
        [
            (["Cardium"], {"F-1"}),
            (["Viking"], {"F-2"}),
            (["Cardium", "Viking"], {"F-1", "F-2"}),
        ],
        ids=["single-cardium", "single-viking", "multi-formation"],
    )
    def test_filters_by_formation(self, filter_formation, expected_uwis):
        WellHeaderFactory(base_uwi="F-1")
        WellHeaderFactory(base_uwi="F-2")
        WellProductionFormationFactory(base_uwi="F-1", formation="Cardium")
        WellProductionFormationFactory(base_uwi="F-2", formation="Viking")
        result = WellQueries.filter_wells(
            WellQueries.get_annotated_queryset(), formations=filter_formation
        )
        assert {w.base_uwi for w in result} == expected_uwis

    def test_filters_by_operator_name_via_cache_table(self):
        WellHeaderFactory(base_uwi="OP-1")
        WellHeaderFactory(base_uwi="OP-2")
        WellCurrentOperatorFactory(base_uwi="OP-1", operator_name="Saguaro Petroleum")
        WellCurrentOperatorFactory(base_uwi="OP-2", operator_name="Other Corp")
        result = WellQueries.filter_wells(
            WellQueries.get_annotated_queryset(),
            operator_name=["Saguaro Petroleum"],
        )
        assert [w.base_uwi for w in result] == ["OP-1"]

    def test_operator_filter_accepts_multiple_values(self):
        WellHeaderFactory(base_uwi="OP-1")
        WellHeaderFactory(base_uwi="OP-2")
        WellHeaderFactory(base_uwi="OP-3")
        WellCurrentOperatorFactory(base_uwi="OP-1", operator_name="Alpha")
        WellCurrentOperatorFactory(base_uwi="OP-2", operator_name="Beta")
        WellCurrentOperatorFactory(base_uwi="OP-3", operator_name="Gamma")
        result = WellQueries.filter_wells(
            WellQueries.get_annotated_queryset(),
            operator_name=["Alpha", "Beta"],
        )
        assert {w.base_uwi for w in result} == {"OP-1", "OP-2"}

    def test_operator_filter_falls_back_to_well_status_when_cache_absent(self, mocker):
        """When well_current_operator table is absent, filter scans well_status directly."""
        mocker.patch(
            "apps.wells.queries._table_exists",
            side_effect=lambda t: False,
        )
        header = WellHeaderFactory(base_uwi="OP-FB-1")
        WellStatusFactory(base_uwi=header, cur_operator_name="Fallback Corp")
        result = WellQueries.filter_wells(
            WellQueries.get_annotated_queryset(),
            operator_name=["Fallback Corp"],
        )
        assert result.filter(base_uwi="OP-FB-1").exists()

    def test_combined_filters_are_and_combined(self):
        WellHeaderFactory(base_uwi="X-1", well_type="OIL")
        WellHeaderFactory(base_uwi="X-2", well_type="GAS")
        WellStatusCategoryFactory(base_uwi="X-1", status_category="Active")
        WellStatusCategoryFactory(base_uwi="X-2", status_category="Active")
        result = WellQueries.filter_wells(
            WellQueries.get_annotated_queryset(),
            status=["Active"],
            well_type=["GAS"],
        )
        assert [w.base_uwi for w in result] == ["X-2"]

    def test_distinct_on_returns_one_row_per_well(self):
        """Multiple related rows (e.g. two status rows) must not produce duplicates."""
        header = WellHeaderFactory(base_uwi="DUP-1")
        WellStatusFactory(base_uwi=header, suffix="00")
        WellStatusFactory(base_uwi=header, suffix="01")
        result = WellQueries.filter_wells(WellQueries.get_annotated_queryset())
        assert result.filter(base_uwi="DUP-1").count() == 1


# ---------------------------------------------------------------------------
# WellQueries.get_annotated_queryset — annotation values
# ---------------------------------------------------------------------------

class TestWellQueriesAnnotations:
    def test_annotates_status_category_value(self):
        WellHeaderFactory(base_uwi="X-1")
        WellStatusCategoryFactory(base_uwi="X-1", status_category="Suspended")
        well = WellQueries.get_annotated_queryset().get(base_uwi="X-1")
        assert well.status_category_value == "Suspended"

    def test_annotates_actual_status_text_value(self):
        WellHeaderFactory(base_uwi="X-2")
        WellStatusCategoryFactory(base_uwi="X-2", actual_status_text="Shut-In")
        well = WellQueries.get_annotated_queryset().get(base_uwi="X-2")
        assert well.actual_status_text_value == "Shut-In"

    def test_annotates_operator_value_from_well_status(self):
        header = WellHeaderFactory(base_uwi="OP-ANN-1")
        WellStatusFactory(base_uwi=header, cur_operator_name="Saguaro Petroleum")
        well = WellQueries.get_annotated_queryset().get(base_uwi="OP-ANN-1")
        assert well.operator_value == "Saguaro Petroleum"

    def test_annotates_well_type_value_from_well_status(self):
        header = WellHeaderFactory(base_uwi="WT-ANN-1")
        WellStatusFactory(base_uwi=header, well_type="GAS")
        well = WellQueries.get_annotated_queryset().get(base_uwi="WT-ANN-1")
        assert well.well_type_value == "GAS"

    def test_annotates_production_formations_value(self):
        WellHeaderFactory(base_uwi="PF-1")
        WellProductionFormationFactory(base_uwi="PF-1", formation="Cardium")
        WellProductionFormationFactory(base_uwi="PF-1", formation="Viking")
        well = WellQueries.get_annotated_queryset().get(base_uwi="PF-1")
        assert well.production_formations_value == "Cardium; Viking"

    @pytest.mark.parametrize(
        "annotation_attr",
        [
            "cumulative_oil_volume_value",
            "cumulative_gas_volume_value",
            "cumulative_fluid_volume_value",
        ],
        ids=["cum-oil", "cum-gas", "cum-fluid"],
    )
    def test_cumulative_volume_is_null_when_no_rows_exist(self, annotation_attr):
        """No production_monthly rows for this well → annotation is null."""
        WellHeaderFactory(base_uwi="CV-1")
        well = WellQueries.get_annotated_queryset().get(base_uwi="CV-1")
        assert getattr(well, annotation_attr) is None

    @pytest.mark.parametrize(
        "annotation_attr",
        [
            "cumulative_oil_volume_value",
            "cumulative_gas_volume_value",
            "cumulative_fluid_volume_value",
        ],
        ids=["cum-oil-absent", "cum-gas-absent", "cum-fluid-absent"],
    )
    def test_cumulative_volume_is_null_when_table_absent(self, annotation_attr, mocker):
        """When production_monthly table does not exist the annotation degrades to null."""
        mocker.patch(
            "apps.wells.queries._table_exists",
            side_effect=lambda t: False,
        )
        WellHeaderFactory(base_uwi="CV-2")
        well = WellQueries.get_annotated_queryset().get(base_uwi="CV-2")
        assert getattr(well, annotation_attr) is None


# ---------------------------------------------------------------------------
# MetadataQueries
# ---------------------------------------------------------------------------

class TestMetadataQueries:
    def test_get_well_types_returns_distinct_values(self):
        h1 = WellHeaderFactory(base_uwi="WT-1")
        h2 = WellHeaderFactory(base_uwi="WT-2")
        WellStatusFactory(base_uwi=h1, well_type="OIL")
        WellStatusFactory(base_uwi=h2, well_type="GAS")
        assert {"OIL", "GAS"}.issubset(set(MetadataQueries.get_well_types()))

    def test_get_well_types_excludes_blank(self):
        header = WellHeaderFactory(base_uwi="WT-BLANK")
        WellStatusFactory(base_uwi=header, well_type="")
        assert "" not in MetadataQueries.get_well_types()

    def test_get_well_types_excludes_null(self):
        header = WellHeaderFactory(base_uwi="WT-NULL")
        WellStatusFactory(base_uwi=header, well_type=None)
        assert None not in MetadataQueries.get_well_types()

    @pytest.mark.parametrize(
        "filter_category, expected_statuses",
        [
            ("Active", ["Flowing"]),
            ("ABD", ["Abandoned"]),
            (None, ["Abandoned", "Flowing"]),
        ],
        ids=["filter-active", "filter-abd", "no-filter"],
    )
    def test_get_actual_well_statuses(self, filter_category, expected_statuses):
        WellStatusCategoryFactory(
            base_uwi="AST-1", status_category="Active", actual_status_text="Flowing"
        )
        WellStatusCategoryFactory(
            base_uwi="AST-2", status_category="ABD", actual_status_text="Abandoned"
        )
        result = list(
            MetadataQueries.get_actual_well_statuses(status_category=filter_category)
        )
        assert result == expected_statuses

    def test_get_production_injection_formations_returns_distinct_values(self):
        WellProductionFormationFactory(base_uwi="PIF-1", formation="Cardium")
        WellProductionFormationFactory(base_uwi="PIF-2", formation="Viking")
        assert {"Cardium", "Viking"}.issubset(
            set(MetadataQueries.get_production_injection_formations())
        )

    def test_get_current_operators_returns_distinct_names(self):
        WellCurrentOperatorFactory(base_uwi="CO-1", operator_name="Alpha Corp")
        WellCurrentOperatorFactory(base_uwi="CO-2", operator_name="Beta Inc")
        result = set(MetadataQueries.get_current_operators())
        assert {"Alpha Corp", "Beta Inc"}.issubset(result)

    def test_get_current_operators_excludes_unknown(self):
        WellCurrentOperatorFactory(base_uwi="CO-UNK", operator_name="Unknown")
        result = list(MetadataQueries.get_current_operators())
        assert "Unknown" not in result

    def test_get_current_operators_excludes_blank(self):
        WellCurrentOperatorFactory(base_uwi="CO-BLANK", operator_name="")
        result = list(MetadataQueries.get_current_operators())
        assert "" not in result

    @pytest.mark.parametrize(
        "search_term, should_include, should_exclude",
        [
            ("alpha", "Alpha Corp", "Beta Inc"),
            ("BETA", "Beta Inc", "Alpha Corp"),
        ],
        ids=["search-alpha", "search-beta-upper"],
    )
    def test_get_current_operators_search_is_case_insensitive(
        self, search_term, should_include, should_exclude
    ):
        WellCurrentOperatorFactory(base_uwi="SRC-1", operator_name="Alpha Corp")
        WellCurrentOperatorFactory(base_uwi="SRC-2", operator_name="Beta Inc")
        result = list(MetadataQueries.get_current_operators(search=search_term))
        assert should_include in result
        assert should_exclude not in result

    def test_get_current_operators_falls_back_to_well_status_when_cache_absent(
        self, mocker
    ):
        """When well_current_operator table is absent, fall back to well_status scan."""
        mocker.patch(
            "apps.wells.queries._table_exists",
            side_effect=lambda t: False,
        )
        header = WellHeaderFactory(base_uwi="CO-FB-1")
        WellStatusFactory(base_uwi=header, cur_operator_name="Fallback Corp")
        result = list(MetadataQueries.get_current_operators())
        assert "Fallback Corp" in result
