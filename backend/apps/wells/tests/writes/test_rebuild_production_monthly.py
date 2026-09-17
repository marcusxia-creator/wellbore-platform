"""Integration tests for writes.rebuild_production_monthly.

These tests run against a real PostgreSQL test database and exercise the
full SQL window-function aggregation path. The production_daily and
production_monthly tables are created explicitly in the fixture because they
are unmanaged models (owned by the data-import pipeline).

All tests use transaction=True because the function executes DELETE + INSERT
within a single cursor block.
"""

import pytest
from django.db import connection

from apps.wells import writes

pytestmark = pytest.mark.django_db(transaction=True)


# ---------------------------------------------------------------------------
# Fixture — ensure unmanaged tables exist in the test DB
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def production_tables(db):
    """production_monthly is managed=True so Django's test runner creates it
    automatically via migrations. production_daily is not yet managed by
    Django migrations, so we create it here if absent.
    """
    with connection.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS production_daily (
                id              bigserial PRIMARY KEY,
                base_uwi        text NOT NULL,
                production_date date NOT NULL,
                daily_oil       double precision,
                daily_water     double precision,
                daily_gas       double precision,
                fluid           double precision,
                imported_at     timestamptz NOT NULL DEFAULT now(),
                UNIQUE (base_uwi, production_date)
            )
        """)


def _insert_daily(base_uwi, rows):
    """Insert rows into production_daily.
    Each row is (date_str, daily_oil, daily_water, daily_gas, fluid).
    """
    with connection.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO production_daily
                (base_uwi, production_date, daily_oil, daily_water, daily_gas, fluid)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (base_uwi, production_date) DO NOTHING
            """,
            [(base_uwi, d, oil, water, gas, fluid) for d, oil, water, gas, fluid in rows],
        )


def _monthly_rows(base_uwi):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT production_month, monthly_oil, cumulative_oil,
                   monthly_gas, cumulative_gas, monthly_fluid, cumulative_fluid
            FROM production_monthly
            WHERE base_uwi = %s
            ORDER BY production_month
            """,
            [base_uwi],
        )
        cols = ["production_month", "monthly_oil", "cumulative_oil",
                "monthly_gas", "cumulative_gas", "monthly_fluid", "cumulative_fluid"]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Basic correctness
# ---------------------------------------------------------------------------

class TestRebuildProductionMonthlyBasic:
    def test_returns_zero_when_no_daily_data_exists(self):
        count = writes.rebuild_production_monthly(base_uwis=["NO-DAILY-UWI"])
        assert count == 0

    def test_returns_zero_when_daily_table_is_empty_and_no_uwis_given(self):
        # Ensure table exists but has no rows for the test.
        count = writes.rebuild_production_monthly()
        assert count == 0

    def test_creates_one_monthly_row_per_month(self):
        _insert_daily("RBM-BASIC", [
            ("2024-01-05", 10.0, 1.0, 100.0, 11.0),
            ("2024-01-15", 20.0, 2.0, 200.0, 22.0),
            ("2024-02-10", 30.0, 3.0, 300.0, 33.0),
        ])
        count = writes.rebuild_production_monthly(base_uwis=["RBM-BASIC"])
        assert count == 2  # Jan + Feb

    def test_aggregates_daily_into_monthly_sums(self):
        _insert_daily("RBM-SUM", [
            ("2024-01-05", 10.0, 1.0, 100.0, 11.0),
            ("2024-01-20", 20.0, 2.0, 200.0, 22.0),
        ])
        writes.rebuild_production_monthly(base_uwis=["RBM-SUM"])
        rows = _monthly_rows("RBM-SUM")
        assert len(rows) == 1
        jan = rows[0]
        assert jan["monthly_oil"] == pytest.approx(30.0)
        assert jan["monthly_gas"] == pytest.approx(300.0)
        assert jan["monthly_fluid"] == pytest.approx(33.0)


# ---------------------------------------------------------------------------
# Cumulative running totals
# ---------------------------------------------------------------------------

class TestRebuildProductionMonthlyCumulatives:
    def test_cumulative_oil_is_running_sum_across_months(self):
        _insert_daily("RBM-CUM", [
            ("2024-01-01", 100.0, 0.0, 0.0, 0.0),
            ("2024-02-01", 200.0, 0.0, 0.0, 0.0),
            ("2024-03-01", 300.0, 0.0, 0.0, 0.0),
        ])
        writes.rebuild_production_monthly(base_uwis=["RBM-CUM"])
        rows = _monthly_rows("RBM-CUM")
        cumulative_oils = [r["cumulative_oil"] for r in rows]
        assert cumulative_oils == pytest.approx([100.0, 300.0, 600.0])

    @pytest.mark.parametrize(
        "daily_values, expected_cumulatives",
        [
            (
                [("2024-01-01", 50, 10, 500, 60), ("2024-02-01", 50, 10, 500, 60)],
                [50.0, 100.0],
            ),
            (
                [("2024-01-01", 10, 0, 0, 10), ("2024-01-15", 20, 0, 0, 20),
                 ("2024-02-01", 30, 0, 0, 30)],
                [30.0, 60.0],  # Jan=30, Feb=60 cumulative
            ),
        ],
        ids=["two-equal-months", "partial-month-split"],
    )
    def test_cumulative_matches_expected(self, daily_values, expected_cumulatives):
        uwi = f"RBM-PARAM-{expected_cumulatives[0]:.0f}"
        _insert_daily(uwi, daily_values)
        writes.rebuild_production_monthly(base_uwis=[uwi])
        rows = _monthly_rows(uwi)
        assert [r["cumulative_oil"] for r in rows] == pytest.approx(expected_cumulatives)


# ---------------------------------------------------------------------------
# Delete + re-insert idempotency
# ---------------------------------------------------------------------------

class TestRebuildProductionMonthlyIdempotency:
    def test_running_twice_yields_same_row_count(self):
        _insert_daily("RBM-IDEM", [
            ("2024-01-01", 10.0, 1.0, 100.0, 11.0),
            ("2024-02-01", 20.0, 2.0, 200.0, 22.0),
        ])
        count_first = writes.rebuild_production_monthly(base_uwis=["RBM-IDEM"])
        count_second = writes.rebuild_production_monthly(base_uwis=["RBM-IDEM"])
        assert count_first == count_second

    def test_rebuilding_one_well_does_not_delete_other_well_rows(self):
        """Partial rebuild must only touch the specified UWIs."""
        _insert_daily("RBM-KEEP", [("2024-01-01", 10.0, 0.0, 0.0, 10.0)])
        _insert_daily("RBM-TOUCH", [("2024-01-01", 20.0, 0.0, 0.0, 20.0)])
        writes.rebuild_production_monthly()  # full rebuild
        initial_keep_count = len(_monthly_rows("RBM-KEEP"))

        # Rebuild only RBM-TOUCH — RBM-KEEP rows must be untouched.
        writes.rebuild_production_monthly(base_uwis=["RBM-TOUCH"])
        assert len(_monthly_rows("RBM-KEEP")) == initial_keep_count

    def test_updated_daily_data_reflected_after_rebuild(self):
        """After inserting new daily rows, re-running rebuild updates the monthly data."""
        _insert_daily("RBM-UPDATE", [("2024-01-01", 100.0, 0.0, 0.0, 100.0)])
        writes.rebuild_production_monthly(base_uwis=["RBM-UPDATE"])
        first_oil = _monthly_rows("RBM-UPDATE")[0]["cumulative_oil"]

        # Add a second month of daily data and rebuild.
        _insert_daily("RBM-UPDATE", [("2024-02-01", 200.0, 0.0, 0.0, 200.0)])
        writes.rebuild_production_monthly(base_uwis=["RBM-UPDATE"])
        rows = _monthly_rows("RBM-UPDATE")
        assert len(rows) == 2
        assert rows[1]["cumulative_oil"] == pytest.approx(first_oil + 200.0)


# ---------------------------------------------------------------------------
# Full rebuild (no base_uwis supplied)
# ---------------------------------------------------------------------------

class TestRebuildProductionMonthlyFullRefresh:
    def test_full_rebuild_covers_all_wells(self):
        _insert_daily("RBM-ALL-1", [("2024-01-01", 10.0, 0.0, 0.0, 10.0)])
        _insert_daily("RBM-ALL-2", [("2024-01-01", 20.0, 0.0, 0.0, 20.0)])
        count = writes.rebuild_production_monthly()
        assert count >= 2  # at least one row per well

    def test_full_rebuild_returns_positive_count(self):
        _insert_daily("RBM-COUNT", [("2024-01-01", 10.0, 0.0, 0.0, 10.0)])
        count = writes.rebuild_production_monthly()
        assert count > 0
