"""Pure-logic tests for well_status_service.

These tests exercise only in-memory functions and never touch the database, so
they run without PostgreSQL, a dump, or the unmanaged legacy tables. Production
summary inputs are stubbed with SimpleNamespace instead of real ORM instances.
"""

from datetime import date
from types import SimpleNamespace

from apps.wells.services.well_status_service import (
    STATUS_ABD,
    STATUS_ACTIVE,
    STATUS_INACTIVE,
    STATUS_SUSPENDED,
    activity_dates,
    categorize_status,
    cutoff_24_months,
    latest_activity_date,
    parse_year_month,
)


def make_production_summary(
    on_prod=None,
    on_inject=None,
    last_prod=None,
    last_inject=None,
):
    """Build a stub production summary with only the fields the service reads."""
    return SimpleNamespace(
        on_prod_yyyy_mm_dd=on_prod,
        on_inject_yyyy_mm_dd=on_inject,
        last_prod_yyyy_mm=last_prod,
        last_inject_yyyy_mm=last_inject,
    )


class TestCutoff24Months:
    def test_returns_date_two_years_earlier(self):
        assert cutoff_24_months(date(2026, 7, 6)) == date(2024, 7, 6)

    def test_clamps_day_to_28(self):
        # Day 31 is clamped to 28 to stay valid in every month.
        assert cutoff_24_months(date(2026, 1, 31)) == date(2024, 1, 28)

    def test_leap_day_input_is_clamped(self):
        assert cutoff_24_months(date(2024, 2, 29)) == date(2022, 2, 28)


class TestParseYearMonth:
    def test_parses_slash_format(self):
        assert parse_year_month("2020/05/15") == date(2020, 5, 15)

    def test_parses_dash_format_without_day(self):
        assert parse_year_month("2020-05") == date(2020, 5, 1)

    def test_parses_underscore_format(self):
        assert parse_year_month("2020_05_15") == date(2020, 5, 15)

    def test_parses_compact_six_digit_format(self):
        assert parse_year_month("202005") == date(2020, 5, 1)

    def test_returns_none_for_empty(self):
        assert parse_year_month("") is None
        assert parse_year_month(None) is None

    def test_returns_none_for_garbage(self):
        assert parse_year_month("not-a-date") is None


class TestActivityDates:
    def test_returns_empty_when_no_summary(self):
        assert activity_dates(None) == []

    def test_collects_and_filters_out_missing_values(self):
        summary = make_production_summary(
            on_prod=date(2021, 3, 1),
            on_inject=None,
            last_prod="2022/06/30",
            last_inject=None,
        )
        assert set(activity_dates(summary)) == {date(2021, 3, 1), date(2022, 6, 30)}


class TestLatestActivityDate:
    def test_returns_none_when_no_dates(self):
        assert latest_activity_date(make_production_summary()) is None

    def test_returns_max_date(self):
        summary = make_production_summary(
            on_prod=date(2019, 1, 1),
            last_prod="2023/12/31",
        )
        assert latest_activity_date(summary) == date(2023, 12, 31)


class TestCategorizeStatus:
    def test_abd_takes_priority(self):
        assert categorize_status("ABD OIL") == STATUS_ABD

    def test_suspended_is_detected(self):
        assert categorize_status("Suspended Well") == STATUS_SUSPENDED

    def test_inactive_when_activity_before_cutoff(self):
        today = date(2026, 7, 6)
        summary = make_production_summary(on_prod=date(2020, 1, 1))
        assert categorize_status("Flowing", summary, today=today) == STATUS_INACTIVE

    def test_active_when_activity_after_cutoff(self):
        today = date(2026, 7, 6)
        summary = make_production_summary(on_prod=date(2026, 1, 1))
        assert categorize_status("Flowing", summary, today=today) == STATUS_ACTIVE

    def test_active_when_no_activity_dates(self):
        assert categorize_status(None) == STATUS_ACTIVE

    def test_abd_wins_even_with_recent_activity(self):
        today = date(2026, 7, 6)
        summary = make_production_summary(on_prod=date(2026, 6, 1))
        assert categorize_status("well is ABD", summary, today=today) == STATUS_ABD
