"""Integration tests for writes.rebuild_injection_monthly.

These tests run against a real PostgreSQL test database and exercise the full
SQL window-function aggregation path. injection_daily and injection_monthly
are managed=True so Django's test runner creates them automatically; only
injection_daily needs a manual-create guard because it still lacks Django
migration support in this branch.

All tests use transaction=True because the function executes DELETE + INSERT.
"""

import pytest
from django.db import connection

from apps.wells import writes

pytestmark = pytest.mark.django_db(transaction=True)


# ---------------------------------------------------------------------------
# Fixture — injection_daily is managed=True, table created by migrations.
# injection_monthly is also managed=True.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def injection_daily_table(db):
    """Both injection tables are managed=True and created by Django migrations.
    No-op fixture kept for explicitness.
    """
    pass


def _insert_daily(base_uwi, rows):
    """Insert rows into injection_daily.
    Each row is (date_str, daily_water, daily_gas, daily_steam).
    """
    with connection.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO injection_daily
                (base_uwi, injection_date, daily_water, daily_gas, daily_steam,
                 injection_pressure)
            VALUES (%s, %s, %s, %s, %s, 0)
            ON CONFLICT (base_uwi, injection_date) DO NOTHING
            """,
            [(base_uwi, d, w, g, s) for d, w, g, s in rows],
        )


def _monthly_rows(base_uwi):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT injection_month,
                   monthly_water, cumulative_water,
                   monthly_gas,   cumulative_gas,
                   monthly_steam, cumulative_steam
            FROM injection_monthly
            WHERE base_uwi = %s
            ORDER BY injection_month
            """,
            [base_uwi],
        )
        cols = [
            "injection_month",
            "monthly_water", "cumulative_water",
            "monthly_gas",   "cumulative_gas",
            "monthly_steam", "cumulative_steam",
        ]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Basic correctness
# ---------------------------------------------------------------------------

class TestRebuildInjectionMonthlyBasic:
    def test_returns_zero_when_no_daily_data_for_uwi(self):
        count = writes.rebuild_injection_monthly(base_uwis=["NO-INJ-DAILY"])
        assert count == 0

    def test_returns_zero_when_daily_table_empty_and_no_uwis_given(self):
        count = writes.rebuild_injection_monthly()
        assert count == 0

    def test_creates_one_monthly_row_per_month(self):
        _insert_daily("RIM-BASIC", [
            ("2024-01-05",  50.0, 5.0, 0.0),
            ("2024-01-20",  60.0, 6.0, 0.0),
            ("2024-02-10",  70.0, 7.0, 0.0),
        ])
        count = writes.rebuild_injection_monthly(base_uwis=["RIM-BASIC"])
        assert count == 2  # Jan + Feb

    def test_aggregates_daily_into_monthly_sums(self):
        _insert_daily("RIM-SUM", [
            ("2024-01-05",  40.0, 4.0, 1.0),
            ("2024-01-25",  60.0, 6.0, 2.0),
        ])
        writes.rebuild_injection_monthly(base_uwis=["RIM-SUM"])
        rows = _monthly_rows("RIM-SUM")
        assert len(rows) == 1
        jan = rows[0]
        assert jan["monthly_water"] == pytest.approx(100.0)
        assert jan["monthly_gas"]   == pytest.approx(10.0)
        assert jan["monthly_steam"] == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Cumulative running totals
# ---------------------------------------------------------------------------

class TestRebuildInjectionMonthlyCumulatives:
    def test_cumulative_water_is_running_sum_across_months(self):
        _insert_daily("RIM-CUM", [
            ("2024-01-01", 100.0, 0.0, 0.0),
            ("2024-02-01", 200.0, 0.0, 0.0),
            ("2024-03-01", 300.0, 0.0, 0.0),
        ])
        writes.rebuild_injection_monthly(base_uwis=["RIM-CUM"])
        rows = _monthly_rows("RIM-CUM")
        cumulative_water = [r["cumulative_water"] for r in rows]
        assert cumulative_water == pytest.approx([100.0, 300.0, 600.0])

    @pytest.mark.parametrize(
        "daily_rows, expected_cum_water",
        [
            (
                [("2024-01-01", 50.0, 0.0, 0.0), ("2024-02-01", 50.0, 0.0, 0.0)],
                [50.0, 100.0],
            ),
            (
                [
                    ("2024-01-01", 10.0, 0.0, 0.0),
                    ("2024-01-15", 20.0, 0.0, 0.0),
                    ("2024-02-01", 30.0, 0.0, 0.0),
                ],
                [30.0, 60.0],  # Jan=30 cumulative, Feb=60 cumulative
            ),
        ],
        ids=["two-equal-months", "partial-month-split"],
    )
    def test_cumulative_water_matches_expected(self, daily_rows, expected_cum_water):
        uwi = f"RIM-PARAM-{expected_cum_water[0]:.0f}"
        _insert_daily(uwi, daily_rows)
        writes.rebuild_injection_monthly(base_uwis=[uwi])
        rows = _monthly_rows(uwi)
        assert [r["cumulative_water"] for r in rows] == pytest.approx(expected_cum_water)

    @pytest.mark.parametrize(
        "fluid_col, daily_col_index, expected_cumulatives",
        [
            ("cumulative_gas",   1, [10.0, 20.0]),
            ("cumulative_steam", 2, [5.0,  10.0]),
        ],
        ids=["cumulative-gas", "cumulative-steam"],
    )
    def test_all_fluid_cumulatives_computed(
        self, fluid_col, daily_col_index, expected_cumulatives
    ):
        """Gas and steam cumulatives computed correctly alongside water."""
        uwi = f"RIM-FLUID-{fluid_col[:3].upper()}"
        # rows: (date, water, gas, steam)
        base_row = [0.0, 0.0, 0.0]
        rows = []
        for month, val in zip(["2024-01-01", "2024-02-01"], [10.0, 10.0]):
            r = base_row[:]
            r[daily_col_index] = val
            rows.append((month, r[0], r[1], r[2]))
        _insert_daily(uwi, rows)
        writes.rebuild_injection_monthly(base_uwis=[uwi])
        result_rows = _monthly_rows(uwi)
        assert [r[fluid_col] for r in result_rows] == pytest.approx(expected_cumulatives)


# ---------------------------------------------------------------------------
# Delete + re-insert idempotency
# ---------------------------------------------------------------------------

class TestRebuildInjectionMonthlyIdempotency:
    def test_running_twice_yields_same_row_count(self):
        _insert_daily("RIM-IDEM", [
            ("2024-01-01", 50.0, 5.0, 0.0),
            ("2024-02-01", 60.0, 6.0, 0.0),
        ])
        count_first  = writes.rebuild_injection_monthly(base_uwis=["RIM-IDEM"])
        count_second = writes.rebuild_injection_monthly(base_uwis=["RIM-IDEM"])
        assert count_first == count_second

    def test_partial_rebuild_does_not_delete_other_well_rows(self):
        """Rebuilding one well must not affect another well's monthly rows."""
        _insert_daily("RIM-KEEP",  [("2024-01-01", 10.0, 0.0, 0.0)])
        _insert_daily("RIM-TOUCH", [("2024-01-01", 20.0, 0.0, 0.0)])
        writes.rebuild_injection_monthly()  # full rebuild
        initial_keep_count = len(_monthly_rows("RIM-KEEP"))

        writes.rebuild_injection_monthly(base_uwis=["RIM-TOUCH"])
        assert len(_monthly_rows("RIM-KEEP")) == initial_keep_count

    def test_updated_daily_data_reflected_after_rebuild(self):
        """After adding new daily rows, re-running rebuild updates monthly data."""
        _insert_daily("RIM-UPDATE", [("2024-01-01", 100.0, 0.0, 0.0)])
        writes.rebuild_injection_monthly(base_uwis=["RIM-UPDATE"])
        first_water = _monthly_rows("RIM-UPDATE")[0]["cumulative_water"]

        _insert_daily("RIM-UPDATE", [("2024-02-01", 200.0, 0.0, 0.0)])
        writes.rebuild_injection_monthly(base_uwis=["RIM-UPDATE"])
        rows = _monthly_rows("RIM-UPDATE")
        assert len(rows) == 2
        assert rows[1]["cumulative_water"] == pytest.approx(first_water + 200.0)


# ---------------------------------------------------------------------------
# Full rebuild (no base_uwis supplied)
# ---------------------------------------------------------------------------

class TestRebuildInjectionMonthlyFullRefresh:
    def test_full_rebuild_covers_all_wells(self):
        _insert_daily("RIM-ALL-1", [("2024-01-01", 10.0, 0.0, 0.0)])
        _insert_daily("RIM-ALL-2", [("2024-01-01", 20.0, 0.0, 0.0)])
        count = writes.rebuild_injection_monthly()
        assert count >= 2

    def test_full_rebuild_returns_positive_count(self):
        _insert_daily("RIM-COUNT", [("2024-01-01", 10.0, 1.0, 0.5)])
        count = writes.rebuild_injection_monthly()
        assert count > 0
