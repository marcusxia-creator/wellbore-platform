"""Integration tests for the wells read layer (queries.py).

Tests run against a real PostgreSQL test database because the queries use
Postgres-specific features (DISTINCT ON, StringAgg subquery annotations).

Parameterized cases use pytest.mark.parametrize to avoid repetitive test
methods; each parameter tuple is documented inline with an id string so that
test output is self-describing.
"""

import pytest

from apps.wells.queries import MetadataQueries, ProductionQueries, WellQueries
from apps.wells.tests.factories import (
    WellCurrentOperatorFactory,
    WellHeaderFactory,
    WellLocationFactory,
    WellProductionFormationFactory,
    WellStatusCategoryFactory,
    WellStatusFactory,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# WellQueries.filter_wells — basic filter coverage
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
            ("walrus", "A-1"),   # matches well_name (case-insensitive)
            ("beluga", "B-1"),
            ("A-1", "A-1"),      # matches base_uwi directly
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
            (["Cardium"], ["F-1"]),
            (["Viking"], ["F-2"]),
            (["Cardium", "Viking"], ["F-1", "F-2"]),
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
        assert {w.base_uwi for w in result} == set(expected_uwis)

    def test_filters_by_operator_name_via_cache_table(self):
        """Operator filter uses WellCurrentOperator cache when present."""
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
        """Applying two filters simultaneously returns only the intersection."""
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
        """Multiple related rows (e.g. two status rows) must not cause duplicates."""
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
        # StringAgg returns alphabetically ordered, semicolon-separated string.
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
        header1 = WellHeaderFactory(base_uwi="WT-1")
        header2 = WellHeaderFactory(base_uwi="WT-2")
        WellStatusFactory(base_uwi=header1, well_type="OIL")
        WellStatusFactory(base_uwi=header2, well_type="GAS")
        assert set(MetadataQueries.get_well_types()) >= {"OIL", "GAS"}

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
            (None, ["Abandoned", "Flowing"]),   # no filter → all categories
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
        assert set(MetadataQueries.get_production_injection_formations()) >= {
            "Cardium",
            "Viking",
        }

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
            ("BETA", "Beta Inc", "Alpha Corp"),   # case-insensitive
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


# ---------------------------------------------------------------------------
# ProductionQueries.get_mapped_wells_queryset
# ---------------------------------------------------------------------------

class TestProductionQueriesMappedWells:
    def test_excludes_wells_without_coordinates(self):
        WellHeaderFactory(base_uwi="MAP-1")
        WellHeaderFactory(base_uwi="MAP-2")
        WellLocationFactory(base_uwi__base_uwi="MAP-1", latitude=55.0, longitude=-114.0)
        # MAP-2 has no location row → should be excluded
        result = ProductionQueries.get_mapped_wells_queryset()
        uwis = {w.base_uwi for w in result}
        assert "MAP-1" in uwis
        assert "MAP-2" not in uwis

    def test_excludes_wells_with_null_latitude(self):
        header = WellHeaderFactory(base_uwi="MAP-NULL-LAT")
        WellLocationFactory(base_uwi=header, latitude=None, longitude=-114.0)
        result = ProductionQueries.get_mapped_wells_queryset()
        assert result.filter(base_uwi="MAP-NULL-LAT").count() == 0

    def test_excludes_wells_with_null_longitude(self):
        header = WellHeaderFactory(base_uwi="MAP-NULL-LON")
        WellLocationFactory(base_uwi=header, latitude=55.0, longitude=None)
        result = ProductionQueries.get_mapped_wells_queryset()
        assert result.filter(base_uwi="MAP-NULL-LON").count() == 0

    @pytest.mark.parametrize(
        "filter_operators, expected_uwi, excluded_uwi",
        [
            (["Saguaro Petroleum"], "MAP-OP-1", "MAP-OP-2"),
            (["Other Corp"], "MAP-OP-2", "MAP-OP-1"),
        ],
        ids=["filter-saguaro", "filter-other"],
    )
    def test_operator_filter_on_mapped_queryset(
        self, filter_operators, expected_uwi, excluded_uwi
    ):
        h1 = WellHeaderFactory(base_uwi="MAP-OP-1")
        h2 = WellHeaderFactory(base_uwi="MAP-OP-2")
        WellLocationFactory(base_uwi=h1, latitude=55.0, longitude=-114.0)
        WellLocationFactory(base_uwi=h2, latitude=56.0, longitude=-115.0)
        WellCurrentOperatorFactory(base_uwi="MAP-OP-1", operator_name="Saguaro Petroleum")
        WellCurrentOperatorFactory(base_uwi="MAP-OP-2", operator_name="Other Corp")
        result = ProductionQueries.get_mapped_wells_queryset(
            operator_name=filter_operators
        )
        uwis = {w.base_uwi for w in result}
        assert expected_uwi in uwis
        assert excluded_uwi not in uwis

    def test_returns_one_row_per_well(self):
        """Duplicate location rows must not cause duplicate well rows."""
        header = WellHeaderFactory(base_uwi="MAP-DUP")
        WellLocationFactory(base_uwi=header, latitude=55.0, longitude=-114.0, suffix="00")
        WellLocationFactory(base_uwi=header, latitude=55.1, longitude=-114.1, suffix="01")
        result = ProductionQueries.get_mapped_wells_queryset()
        assert result.filter(base_uwi="MAP-DUP").count() == 1

    def test_carries_full_annotations(self):
        """Mapped queryset must carry status and operator annotations for the serializer."""
        header = WellHeaderFactory(base_uwi="MAP-ANN-1")
        WellLocationFactory(base_uwi=header, latitude=55.0, longitude=-114.0)
        WellStatusCategoryFactory(base_uwi="MAP-ANN-1", status_category="Active")
        WellStatusFactory(base_uwi=header, cur_operator_name="Saguaro Petroleum")
        well = ProductionQueries.get_mapped_wells_queryset().get(base_uwi="MAP-ANN-1")
        assert well.status_category_value == "Active"
        assert well.operator_value == "Saguaro Petroleum"


# ---------------------------------------------------------------------------
# ProductionQueries.get_daily_production
# ---------------------------------------------------------------------------

class TestProductionQueriesDailyProduction:
    def test_returns_empty_list_when_table_absent(self, mocker):
        """When production_daily does not exist, return [] without raising."""
        mocker.patch(
            "apps.wells.queries._table_exists",
            side_effect=lambda t: False,
        )
        result = ProductionQueries.get_daily_production("ANY-UWI")
        assert result == []

    def test_returns_empty_list_for_well_with_no_rows(self):
        """Well exists but has no production_daily rows → empty list."""
        result = ProductionQueries.get_daily_production("NO-PROD-UWI")
        assert result == []

    def test_returns_correct_row_shape(self, db):
        """Each returned dict must have the expected keys."""
        from django.db import connection

        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO production_daily
                    (base_uwi, production_date, daily_oil, daily_water, daily_gas, fluid)
                VALUES (%s, '2024-01-15', 10.5, 2.0, 500.0, 12.5)
                """,
                ["SHAPE-UWI"],
            )
        rows = ProductionQueries.get_daily_production("SHAPE-UWI")
        assert len(rows) == 1
        row = rows[0]
        assert set(row.keys()) == {"date", "daily_oil", "daily_water", "daily_gas", "fluid"}
        assert row["date"] == "2024-01-15"
        assert row["daily_oil"] == 10.5

    def test_rows_are_ordered_by_date_ascending(self, db):
        from django.db import connection

        rows_to_insert = [
            ("ORD-UWI", "2024-03-01", 1.0, 0.0, 100.0, 1.0),
            ("ORD-UWI", "2024-01-01", 3.0, 0.0, 300.0, 3.0),
            ("ORD-UWI", "2024-02-01", 2.0, 0.0, 200.0, 2.0),
        ]
        with connection.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO production_daily
                    (base_uwi, production_date, daily_oil, daily_water, daily_gas, fluid)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                rows_to_insert,
            )
        result = ProductionQueries.get_daily_production("ORD-UWI")
        dates = [r["date"] for r in result]
        assert dates == sorted(dates)

    @pytest.mark.parametrize(
        "null_col, expected_value",
        [
            ("daily_oil", 0.0),
            ("daily_water", 0.0),
            ("daily_gas", 0.0),
            ("fluid", 0.0),
        ],
        ids=["null-oil", "null-water", "null-gas", "null-fluid"],
    )
    def test_null_values_coerced_to_zero(self, null_col, expected_value, db):
        """NULL columns in production_daily must be returned as 0.0, not None."""
        from django.db import connection

        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO production_daily
                    (base_uwi, production_date, daily_oil, daily_water, daily_gas, fluid)
                VALUES (%s, '2024-06-01', NULL, NULL, NULL, NULL)
                """,
                [f"NULL-{null_col}"],
            )
        rows = ProductionQueries.get_daily_production(f"NULL-{null_col}")
        assert rows[0][null_col] == expected_value


# ---------------------------------------------------------------------------
# ProductionQueries.get_production_totals
# ---------------------------------------------------------------------------

class TestProductionQueriesTotals:
    def test_returns_all_none_when_table_absent(self, mocker):
        mocker.patch(
            "apps.wells.queries._table_exists",
            side_effect=lambda t: False,
        )
        result = ProductionQueries.get_production_totals("ANY-UWI")
        assert result == {
            "cumulative_oil": None,
            "cumulative_water": None,
            "cumulative_gas": None,
            "cumulative_fluid": None,
        }

    def test_returns_all_none_for_well_with_no_rows(self):
        result = ProductionQueries.get_production_totals("NO-MONTHLY-UWI")
        assert result == {
            "cumulative_oil": None,
            "cumulative_water": None,
            "cumulative_gas": None,
            "cumulative_fluid": None,
        }

    def test_returns_latest_month_totals(self, db):
        from django.db import connection

        rows = [
            ("TOT-UWI", "2024-01-01", 100.0, 10.0, 500.0, 110.0),
            ("TOT-UWI", "2024-02-01", 200.0, 20.0, 1000.0, 220.0),  # latest
        ]
        with connection.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO production_monthly
                    (base_uwi, production_month,
                     cumulative_oil, cumulative_water, cumulative_gas, cumulative_fluid)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                rows,
            )
        result = ProductionQueries.get_production_totals("TOT-UWI")
        assert result["cumulative_oil"] == 200.0
        assert result["cumulative_gas"] == 1000.0

    @pytest.mark.parametrize(
        "col",
        ["cumulative_oil", "cumulative_water", "cumulative_gas", "cumulative_fluid"],
        ids=["oil", "water", "gas", "fluid"],
    )
    def test_all_cumulative_keys_present_in_result(self, col):
        result = ProductionQueries.get_production_totals("KEY-CHECK-UWI")
        assert col in result
