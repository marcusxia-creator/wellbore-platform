"""Pure-logic tests for idle / WellStor / orphan flags. No database."""

from datetime import date

from apps.wellstor.services.status import (
    idle_well_flag,
    is_orphan_reclaimed,
    is_surface_abandoned,
    months_between,
    wellstor_flag,
)


class TestMonthsBetween:
    def test_year_month_difference(self):
        assert months_between(date(2023, 1, 15), date(2025, 1, 1)) == 24

    def test_parses_year_month_string(self):
        assert months_between("2023/01", date(2025, 1, 1)) == 24

    def test_missing(self):
        assert months_between(None, date(2025, 1, 1)) is None


class TestIdleWellFlag:
    def test_idle_when_both_dates_old(self):
        idle, months_prod, months_inj = idle_well_flag(
            last_prod=date(2023, 1, 1),
            last_inj=date(2023, 1, 1),
            as_of=date(2025, 1, 1),
        )
        assert idle is True
        assert months_prod == 24
        assert months_inj == 24

    def test_missing_injection_counts_as_old(self):
        idle, _, months_inj = idle_well_flag(
            last_prod=date(2023, 1, 1),
            last_inj=None,
            as_of=date(2025, 1, 1),
        )
        assert idle is True
        assert months_inj is None

    def test_missing_production_is_not_idle(self):
        idle, months_prod, _ = idle_well_flag(
            last_prod=None,
            last_inj=None,
            as_of=date(2025, 1, 1),
        )
        assert idle is False
        assert months_prod is None

    def test_recent_production_is_not_idle(self):
        idle, _, _ = idle_well_flag(
            last_prod=date(2024, 6, 1),
            last_inj=None,
            as_of=date(2025, 1, 1),
        )
        assert idle is False


class TestWellstorFlag:
    def test_status_keywords(self):
        assert wellstor_flag("Suspended", idle=False) is True
        assert wellstor_flag("ABD ZONE", idle=False) is True

    def test_idle_alone(self):
        assert wellstor_flag("PRODUCING", idle=True) is True

    def test_neither(self):
        assert wellstor_flag("PRODUCING", idle=False) is False


class TestOrphanAndSurface:
    def test_surface_abandoned_when_date_present(self):
        assert is_surface_abandoned("2020-01-01") is True
        assert is_surface_abandoned(None) is False

    def test_orphan_rules(self):
        assert is_orphan_reclaimed("Y", None, None) is True
        assert is_orphan_reclaimed(None, "completed", None) is True
        assert is_orphan_reclaimed(None, None, "Completed") is True
        assert is_orphan_reclaimed("N", "pending", None) is False
