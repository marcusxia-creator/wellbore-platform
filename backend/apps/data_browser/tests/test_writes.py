"""Integration tests for data_browser.writes (BrowserWrites).

Tests use raw_excel_batch_* tables so they never touch core schema tables.
Each test creates and cleans up its own temporary table.
"""

import pytest
from django.db import connection

from apps.data_browser.queries import DELETABLE_TABLE_PREFIXES, BrowserQueries
from apps.data_browser.writes import BrowserWrites

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_temp_table(name: str) -> str:
    with connection.cursor() as cur:
        cur.execute(
            f'CREATE TABLE IF NOT EXISTS "{name}" '
            '(id bigserial PRIMARY KEY, note text)'
        )
    return name


def _drop_temp_table(name: str) -> None:
    with connection.cursor() as cur:
        cur.execute(f'DROP TABLE IF EXISTS "{name}" CASCADE')


# ---------------------------------------------------------------------------
# BrowserWrites.drop_table — success cases
# ---------------------------------------------------------------------------

class TestDropTableSuccess:
    @pytest.mark.parametrize(
        "prefix",
        list(DELETABLE_TABLE_PREFIXES),
        ids=[p.rstrip("_") for p in DELETABLE_TABLE_PREFIXES],
    )
    def test_drops_table_with_allowed_prefix(self, prefix):
        tbl = f"{prefix}drop_success_test"
        _create_temp_table(tbl)
        result = BrowserWrites.drop_table(tbl)
        assert result == {"table": tbl, "deleted": True}
        # Verify the table is actually gone.
        assert BrowserQueries.table_exists(tbl) is False

    def test_returned_dict_structure(self):
        tbl = "raw_excel_batch_return_struct_test"
        _create_temp_table(tbl)
        result = BrowserWrites.drop_table(tbl)
        assert set(result.keys()) == {"table", "deleted"}
        assert result["deleted"] is True
        assert result["table"] == tbl

    def test_drop_is_idempotent_for_separate_tables(self):
        """Dropping one table does not affect another."""
        tbl_a = "raw_excel_batch_idem_a"
        tbl_b = "raw_excel_batch_idem_b"
        _create_temp_table(tbl_a)
        _create_temp_table(tbl_b)
        BrowserWrites.drop_table(tbl_a)
        assert BrowserQueries.table_exists(tbl_a) is False
        assert BrowserQueries.table_exists(tbl_b) is True
        _drop_temp_table(tbl_b)


# ---------------------------------------------------------------------------
# BrowserWrites.drop_table — error cases
# ---------------------------------------------------------------------------

class TestDropTableErrors:
    @pytest.mark.parametrize(
        "table_name",
        [
            "well_header",
            "production_daily",
            "injection_daily",
            "well_status_category",
        ],
        ids=["well-header", "production-daily", "injection-daily", "well-status-cat"],
    )
    def test_refuses_to_drop_core_tables(self, table_name):
        """Core schema tables must never be deletable via the data browser."""
        with pytest.raises(ValueError, match="import staging"):
            BrowserWrites.drop_table(table_name)

    @pytest.mark.parametrize(
        "bad_name",
        ["", "bad name", "bad-name", "123bad", "'; DROP TABLE foo; --"],
        ids=["empty", "space", "hyphen", "leading-digit", "injection"],
    )
    def test_refuses_invalid_identifiers(self, bad_name):
        with pytest.raises(ValueError, match="Invalid"):
            BrowserWrites.drop_table(bad_name)

    def test_raises_when_table_does_not_exist(self):
        tbl = "raw_excel_batch_nonexistent_xyz"
        # Ensure it really does not exist.
        _drop_temp_table(tbl)
        with pytest.raises(ValueError, match="does not exist"):
            BrowserWrites.drop_table(tbl)

    def test_refuses_arbitrary_prefix(self):
        """A table that looks like an import table but has wrong prefix."""
        with pytest.raises(ValueError, match="import staging"):
            BrowserWrites.drop_table("excel_import_data")

    def test_refuses_partial_prefix_match(self):
        """Prefix must start at position 0, not be a substring."""
        with pytest.raises(ValueError, match="import staging"):
            BrowserWrites.drop_table("prefix_raw_excel_batch_foo")
