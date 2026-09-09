"""Integration tests for InjectionQueries (queries.py).

These tests run against a real PostgreSQL test database. The injection_daily
and injection_monthly tables are unmanaged (owned by the import pipeline), so
the conftest must create them before these tests run. All raw INSERT statements
use django.db.connection.cursor() directly because the tables are unmanaged and
Factory Boy cannot create rows without the table existing.
"""

import pytest
from django.db import connection

from apps.wells.queries import InjectionQueries
from apps.wells.tests.factories import (
    WellCurrentOperatorFactory,
    WellHeaderFactory,
    WellLocationFactory,
    WellStatusCategoryFactory,
    WellStatusFactory,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers — raw SQL fixtures for unmanaged tables
# ---------------------------------------------------------------------------

def _create_injection_tables():
    """Ensure injection_daily and injection_monthly tables exist in the test DB."""
    with connection.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS injection_daily (
                id              bigserial PRIMARY KEY,
                base_uwi        text NOT NULL,
                injection_date  date NOT NULL,
                daily_water     double precision NOT NULL DEFAULT 0,
                daily_gas       double precision NOT NULL DEFAULT 0,
                daily_steam     double precision NOT NULL DEFAULT 0,
                injection_pressure double precision NOT NULL DEFAULT 0,
                source_file     text,
                imported_at     timestamptz NOT NULL DEFAULT now(),
                UNIQUE (base_uwi, injection_date)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS injection_monthly (
                id              bigserial PRIMARY KEY,
                base_uwi        text NOT NULL,
                injection_month date NOT NULL,
                monthly_water   double precision NOT NULL DEFAULT 0,
                monthly_gas     double precision NOT NULL DEFAULT 0,
                monthly_steam   double precision NOT NULL DEFAULT 0,
                cumulative_water double precision NOT NULL DEFAULT 0,
                cumulative_gas  double precision NOT NULL DEFAULT 0,
                cumulative_steam double precision NOT NULL DEFAULT 0,
                updated_at      timestamptz NOT NULL DEFAULT now(),
                UNIQUE (base_uwi, injection_month)
            )
        """)


def _insert_daily(base_uwi, rows):
    """Insert rows into injection_daily. Each row is (date_str, water, gas, steam, pressure)."""
    with connection.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO injection_daily
                (base_uwi, injection_date, daily_water, daily_gas, daily_steam, injection_pressure)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (base_uwi, injection_date) DO NOTHING
            """,
            [(base_uwi, d, w, g, s, p) for d, w, g, s, p in rows],
        )


def _insert_monthly(base_uwi, rows):
    """Insert rows into injection_monthly.
    Each row is (month_str, m_water, m_gas, m_steam, c_water, c_gas, c_steam).
    """
    with connection.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO injection_monthly
                (base_uwi, injection_month,
                 monthly_water, monthly_gas, monthly_steam,
                 cumulative_water, cumulative_gas, cumulative_steam)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (base_uwi, injection_month) DO NOTHING
            """,
            [(base_uwi, m, mw, mg, ms, cw, cg, cs) for m, mw, mg, ms, cw, cg, cs in rows],
        )


@pytest.fixture(autouse=True)
def injection_tables(db):
    """Create injection tables once per test session if they do not exist."""
    _create_injection_tables()


# ---------------------------------------------------------------------------
# InjectionQueries.get_daily_injection
# ---------------------------------------------------------------------------

class TestGetDailyInjection:
    def test_returns_empty_list_when_table_absent(self, mocker):
        """When injection_daily does not exist, return [] without raising."""
        mocker.patch(
            "apps.wells.queries._table_exists",
            side_effect=lambda t: False,
        )
        result = InjectionQueries.get_daily_injection("ANY-UWI")
        assert result == []

    def test_returns_empty_list_for_well_with_no_rows(self):
        result = InjectionQueries.get_daily_injection("NO-INJ-UWI")
        assert result == []

    def test_returns_correct_row_shape(self):
        _insert_daily("SHAPE-INJ", [("2024-03-15", 50.0, 10.0, 0.0, 800.0)])
        rows = InjectionQueries.get_daily_injection("SHAPE-INJ")
        assert len(rows) == 1
        row = rows[0]
        assert set(row.keys()) == {
            "date", "daily_water", "daily_gas", "daily_steam", "injection_pressure"
        }
        assert row["date"] == "2024-03-15"
        assert row["daily_water"] == 50.0
        assert row["injection_pressure"] == 800.0

    def test_rows_are_ordered_by_date_ascending(self):
        _insert_daily("ORD-INJ", [
            ("2024-03-01", 1.0, 0.0, 0.0, 100.0),
            ("2024-01-01", 3.0, 0.0, 0.0, 300.0),
            ("2024-02-01", 2.0, 0.0, 0.0, 200.0),
        ])
        result = InjectionQueries.get_daily_injection("ORD-INJ")
        dates = [r["date"] for r in result]
        assert dates == sorted(dates)

    @pytest.mark.parametrize(
        "null_col, expected_value",
        [
            ("daily_water", 0.0),
            ("daily_gas", 0.0),
            ("daily_steam", 0.0),
            ("injection_pressure", 0.0),
        ],
        ids=["null-water", "null-gas", "null-steam", "null-pressure"],
    )
    def test_null_values_coerced_to_zero(self, null_col, expected_value):
        """NULL columns in injection_daily must be returned as 0.0, not None."""
        uwi = f"NULL-INJ-{null_col[:4].upper()}"
        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO injection_daily
                    (base_uwi, injection_date,
                     daily_water, daily_gas, daily_steam, injection_pressure)
                VALUES (%s, '2024-06-01', NULL, NULL, NULL, NULL)
                ON CONFLICT (base_uwi, injection_date) DO NOTHING
                """,
                [uwi],
            )
        rows = InjectionQueries.get_daily_injection(uwi)
        assert rows[0][null_col] == expected_value

    def test_only_returns_rows_for_requested_well(self):
        _insert_daily("INJ-A", [("2024-01-01", 100.0, 0.0, 0.0, 500.0)])
        _insert_daily("INJ-B", [("2024-01-01", 200.0, 0.0, 0.0, 600.0)])
        result = InjectionQueries.get_daily_injection("INJ-A")
        assert len(result) == 1
        assert result[0]["daily_water"] == 100.0


# ---------------------------------------------------------------------------
# InjectionQueries.get_injection_totals
# ---------------------------------------------------------------------------

class TestGetInjectionTotals:
    def test_returns_all_none_when_table_absent(self, mocker):
        mocker.patch(
            "apps.wells.queries._table_exists",
            side_effect=lambda t: False,
        )
        result = InjectionQueries.get_injection_totals("ANY-UWI")
        assert result == {
            "cumulative_water": None,
            "cumulative_gas": None,
            "cumulative_steam": None,
        }

    def test_returns_all_none_for_well_with_no_rows(self):
        result = InjectionQueries.get_injection_totals("NO-INJ-MONTHLY")
        assert result == {
            "cumulative_water": None,
            "cumulative_gas": None,
            "cumulative_steam": None,
        }

    def test_returns_latest_month_cumulatives(self):
        _insert_monthly("TOT-INJ", [
            ("2024-01-01", 100.0, 10.0, 0.0, 100.0, 10.0, 0.0),
            ("2024-02-01", 200.0, 20.0, 0.0, 300.0, 30.0, 0.0),  # latest
        ])
        result = InjectionQueries.get_injection_totals("TOT-INJ")
        assert result["cumulative_water"] == 300.0
        assert result["cumulative_gas"] == 30.0
        assert result["cumulative_steam"] == 0.0

    @pytest.mark.parametrize(
        "col",
        ["cumulative_water", "cumulative_gas", "cumulative_steam"],
        ids=["water", "gas", "steam"],
    )
    def test_all_cumulative_keys_present_in_result(self, col):
        result = InjectionQueries.get_injection_totals("KEY-CHECK-INJ")
        assert col in result

    def test_ignores_other_well_rows(self):
        _insert_monthly("TOTX-1", [("2024-01-01", 50.0, 5.0, 0.0, 50.0, 5.0, 0.0)])
        _insert_monthly("TOTX-2", [("2024-01-01", 999.0, 999.0, 0.0, 999.0, 999.0, 0.0)])
        result = InjectionQueries.get_injection_totals("TOTX-1")
        assert result["cumulative_water"] == 50.0


# ---------------------------------------------------------------------------
# InjectionQueries.get_mapped_injection_wells_queryset
# ---------------------------------------------------------------------------

class TestGetMappedInjectionWellsQueryset:
    def test_returns_empty_queryset_when_table_absent(self, mocker):
        mocker.patch(
            "apps.wells.queries._table_exists",
            side_effect=lambda t: False,
        )
        result = InjectionQueries.get_mapped_injection_wells_queryset()
        assert result.count() == 0

    def test_excludes_wells_with_no_injection_data(self):
        WellHeaderFactory(base_uwi="MAP-NO-INJ")
        WellLocationFactory(base_uwi__base_uwi="MAP-NO-INJ", latitude=55.0, longitude=-114.0)
        # No injection rows for this well.
        result = InjectionQueries.get_mapped_injection_wells_queryset()
        assert result.filter(base_uwi="MAP-NO-INJ").count() == 0

    def test_excludes_wells_with_no_coordinates(self):
        WellHeaderFactory(base_uwi="MAP-NO-COORD-INJ")
        _insert_daily("MAP-NO-COORD-INJ", [("2024-01-01", 50.0, 0.0, 0.0, 500.0)])
        # No location row for this well.
        result = InjectionQueries.get_mapped_injection_wells_queryset()
        assert result.filter(base_uwi="MAP-NO-COORD-INJ").count() == 0

    def test_includes_well_with_injection_and_coordinates(self):
        WellHeaderFactory(base_uwi="MAP-INJ-OK")
        WellLocationFactory(base_uwi__base_uwi="MAP-INJ-OK", latitude=55.0, longitude=-114.0)
        _insert_daily("MAP-INJ-OK", [("2024-01-01", 50.0, 0.0, 0.0, 500.0)])
        result = InjectionQueries.get_mapped_injection_wells_queryset()
        assert result.filter(base_uwi="MAP-INJ-OK").exists()

    @pytest.mark.parametrize(
        "filter_operators, expected_uwi, excluded_uwi",
        [
            (["Alpha Corp"], "MAP-INJ-OP-1", "MAP-INJ-OP-2"),
            (["Beta Inc"], "MAP-INJ-OP-2", "MAP-INJ-OP-1"),
        ],
        ids=["filter-alpha", "filter-beta"],
    )
    def test_operator_filter(self, filter_operators, expected_uwi, excluded_uwi):
        WellHeaderFactory(base_uwi="MAP-INJ-OP-1")
        WellHeaderFactory(base_uwi="MAP-INJ-OP-2")
        WellLocationFactory(base_uwi__base_uwi="MAP-INJ-OP-1", latitude=55.0, longitude=-114.0)
        WellLocationFactory(base_uwi__base_uwi="MAP-INJ-OP-2", latitude=56.0, longitude=-115.0)
        WellCurrentOperatorFactory(base_uwi="MAP-INJ-OP-1", operator_name="Alpha Corp")
        WellCurrentOperatorFactory(base_uwi="MAP-INJ-OP-2", operator_name="Beta Inc")
        _insert_daily("MAP-INJ-OP-1", [("2024-01-01", 50.0, 0.0, 0.0, 500.0)])
        _insert_daily("MAP-INJ-OP-2", [("2024-01-01", 60.0, 0.0, 0.0, 600.0)])
        result = InjectionQueries.get_mapped_injection_wells_queryset(
            operator_name=filter_operators
        )
        uwis = {w.base_uwi for w in result}
        assert expected_uwi in uwis
        assert excluded_uwi not in uwis

    def test_returns_one_row_per_well(self):
        """Multiple injection rows for the same well must not cause duplicates."""
        header = WellHeaderFactory(base_uwi="MAP-INJ-DUP")
        WellLocationFactory(base_uwi=header, latitude=55.0, longitude=-114.0)
        _insert_daily("MAP-INJ-DUP", [
            ("2024-01-01", 10.0, 0.0, 0.0, 500.0),
            ("2024-02-01", 20.0, 0.0, 0.0, 500.0),
        ])
        result = InjectionQueries.get_mapped_injection_wells_queryset()
        assert result.filter(base_uwi="MAP-INJ-DUP").count() == 1

    def test_carries_status_annotation(self):
        """Mapped injection queryset must carry status annotation for the serializer."""
        WellHeaderFactory(base_uwi="MAP-INJ-ANN")
        WellLocationFactory(base_uwi__base_uwi="MAP-INJ-ANN", latitude=55.0, longitude=-114.0)
        WellStatusCategoryFactory(base_uwi="MAP-INJ-ANN", status_category="Active")
        _insert_daily("MAP-INJ-ANN", [("2024-01-01", 10.0, 0.0, 0.0, 500.0)])
        well = InjectionQueries.get_mapped_injection_wells_queryset().get(base_uwi="MAP-INJ-ANN")
        assert well.status_category_value == "Active"

    def test_carries_operator_annotation(self):
        header = WellHeaderFactory(base_uwi="MAP-INJ-OP-ANN")
        WellLocationFactory(base_uwi=header, latitude=55.0, longitude=-114.0)
        WellStatusFactory(base_uwi=header, cur_operator_name="Saguaro Petroleum")
        _insert_daily("MAP-INJ-OP-ANN", [("2024-01-01", 10.0, 0.0, 0.0, 500.0)])
        well = InjectionQueries.get_mapped_injection_wells_queryset().get(
            base_uwi="MAP-INJ-OP-ANN"
        )
        assert well.operator_value == "Saguaro Petroleum"
