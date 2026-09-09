"""Integration tests for data_browser.queries (BrowserQueries).

These tests run against the real PostgreSQL test database created by Django's
test runner. They create and tear down temporary tables (raw_excel_batch_*)
within each test to avoid polluting the schema.
"""

import pytest
from django.db import connection

from apps.data_browser.queries import BrowserQueries, MAX_PAGE_SIZE

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_temp_table(name: str, columns: list[tuple[str, str]] | None = None) -> str:
    """Create a raw_excel_batch_* table with the given columns and return its name."""
    if columns is None:
        columns = [("col_a", "text"), ("col_b", "integer")]
    col_defs = ", ".join(f'"{col}" {dtype}' for col, dtype in columns)
    with connection.cursor() as cur:
        cur.execute(f'CREATE TABLE IF NOT EXISTS "{name}" (id bigserial PRIMARY KEY, {col_defs})')
    return name


def _drop_temp_table(name: str) -> None:
    with connection.cursor() as cur:
        cur.execute(f'DROP TABLE IF EXISTS "{name}" CASCADE')


def _insert_rows(table_name: str, rows: list[dict]) -> None:
    if not rows:
        return
    cols = list(rows[0].keys())
    col_list = ", ".join(f'"{c}"' for c in cols)
    placeholders = ", ".join(["%s"] * len(cols))
    with connection.cursor() as cur:
        cur.executemany(
            f'INSERT INTO "{table_name}" ({col_list}) VALUES ({placeholders})',
            [tuple(r[c] for c in cols) for r in rows],
        )


# ---------------------------------------------------------------------------
# BrowserQueries.get_table_catalog
# ---------------------------------------------------------------------------

class TestGetTableCatalog:
    def test_includes_known_django_managed_table(self):
        """well_status_category is always present after migrations run."""
        catalog = BrowserQueries.get_table_catalog()
        names = {t["name"] for t in catalog}
        assert "well_status_category" in names

    def test_each_entry_has_required_keys(self):
        catalog = BrowserQueries.get_table_catalog()
        assert catalog, "catalog must not be empty"
        for entry in catalog:
            assert "name" in entry
            assert "estimated_rows" in entry
            assert "columns" in entry
            assert isinstance(entry["columns"], list)

    def test_columns_have_required_keys(self):
        catalog = BrowserQueries.get_table_catalog()
        for entry in catalog:
            for col in entry["columns"]:
                assert "name" in col
                assert "type" in col
                assert "position" in col

    def test_temp_table_appears_in_catalog(self):
        tbl = "raw_excel_batch_catalog_test"
        _create_temp_table(tbl)
        try:
            names = {t["name"] for t in BrowserQueries.get_table_catalog()}
            assert tbl in names
        finally:
            _drop_temp_table(tbl)

    def test_temp_table_removed_from_catalog_after_drop(self):
        tbl = "raw_excel_batch_catalog_remove_test"
        _create_temp_table(tbl)
        _drop_temp_table(tbl)
        names = {t["name"] for t in BrowserQueries.get_table_catalog()}
        assert tbl not in names


# ---------------------------------------------------------------------------
# BrowserQueries.get_table_columns
# ---------------------------------------------------------------------------

class TestGetTableColumns:
    def test_returns_columns_for_existing_table(self):
        cols = BrowserQueries.get_table_columns("well_status_category")
        names = [c["name"] for c in cols]
        assert "base_uwi" in names
        assert "status_category" in names

    def test_raises_for_nonexistent_table(self):
        with pytest.raises(ValueError, match="does not exist"):
            BrowserQueries.get_table_columns("this_table_does_not_exist_xyz")

    @pytest.mark.parametrize(
        "bad_name",
        ["", "bad name", "bad-name", "123bad", "; DROP TABLE users; --"],
        ids=["empty", "space", "hyphen", "leading-digit", "injection"],
    )
    def test_raises_for_invalid_identifier(self, bad_name):
        with pytest.raises(ValueError, match="Invalid"):
            BrowserQueries.get_table_columns(bad_name)

    def test_columns_ordered_by_position(self):
        cols = BrowserQueries.get_table_columns("well_status_category")
        positions = [c["position"] for c in cols]
        assert positions == sorted(positions)


# ---------------------------------------------------------------------------
# BrowserQueries.get_table_rows — basic behavior
# ---------------------------------------------------------------------------

class TestGetTableRowsBasic:
    def setup_method(self):
        self.tbl = "raw_excel_batch_rows_test"
        _create_temp_table(self.tbl, [("well_name", "text"), ("depth_m", "integer")])
        _insert_rows(self.tbl, [
            {"well_name": "Alpha", "depth_m": 1000},
            {"well_name": "Beta",  "depth_m": 2000},
            {"well_name": "Gamma", "depth_m": 3000},
        ])

    def teardown_method(self):
        _drop_temp_table(self.tbl)

    def test_returns_all_rows_by_default(self):
        result = BrowserQueries.get_table_rows(self.tbl)
        assert result["count"] == 3
        assert len(result["results"]) == 3

    def test_result_dict_has_required_keys(self):
        result = BrowserQueries.get_table_rows(self.tbl)
        for key in ("table", "columns", "count", "page", "page_size", "next", "previous", "results"):
            assert key in result

    def test_values_are_cast_to_str(self):
        result = BrowserQueries.get_table_rows(self.tbl, columns=["depth_m"])
        for row in result["results"]:
            assert isinstance(row["depth_m"], str)

    def test_table_name_in_result(self):
        result = BrowserQueries.get_table_rows(self.tbl)
        assert result["table"] == self.tbl

    def test_raises_for_invalid_table_name(self):
        with pytest.raises(ValueError, match="Invalid"):
            BrowserQueries.get_table_rows("bad-table-name!")


# ---------------------------------------------------------------------------
# BrowserQueries.get_table_rows — column selection
# ---------------------------------------------------------------------------

class TestGetTableRowsColumnSelection:
    def setup_method(self):
        self.tbl = "raw_excel_batch_col_select_test"
        _create_temp_table(self.tbl, [("col_a", "text"), ("col_b", "text"), ("col_c", "text")])
        _insert_rows(self.tbl, [{"col_a": "x", "col_b": "y", "col_c": "z"}])

    def teardown_method(self):
        _drop_temp_table(self.tbl)

    def test_returns_only_requested_columns(self):
        result = BrowserQueries.get_table_rows(self.tbl, columns=["col_a", "col_c"])
        assert set(result["results"][0].keys()) == {"col_a", "col_c"}

    def test_ignores_nonexistent_columns(self):
        result = BrowserQueries.get_table_rows(self.tbl, columns=["col_a", "nonexistent"])
        # nonexistent is silently dropped; col_a is returned
        assert "col_a" in result["results"][0]
        assert "nonexistent" not in result["results"][0]

    def test_falls_back_to_all_columns_when_selection_empty(self):
        result = BrowserQueries.get_table_rows(self.tbl, columns=[])
        assert len(result["results"][0]) >= 3  # at least col_a, col_b, col_c

    @pytest.mark.parametrize(
        "col_subset",
        [["col_a"], ["col_b"], ["col_a", "col_b"]],
        ids=["single-a", "single-b", "two-cols"],
    )
    def test_parametrized_column_subsets(self, col_subset):
        result = BrowserQueries.get_table_rows(self.tbl, columns=col_subset)
        returned_keys = set(result["results"][0].keys())
        for col in col_subset:
            assert col in returned_keys


# ---------------------------------------------------------------------------
# BrowserQueries.get_table_rows — search
# ---------------------------------------------------------------------------

class TestGetTableRowsSearch:
    def setup_method(self):
        self.tbl = "raw_excel_batch_search_test"
        _create_temp_table(self.tbl, [("name", "text"), ("region", "text")])
        _insert_rows(self.tbl, [
            {"name": "Walrus North", "region": "Alberta"},
            {"name": "Beluga South", "region": "Alberta"},
            {"name": "Orca Deep",    "region": "BC"},
        ])

    def teardown_method(self):
        _drop_temp_table(self.tbl)

    @pytest.mark.parametrize(
        "search_term, expected_count",
        [
            ("walrus", 1),
            ("alberta", 2),
            ("bc", 1),
            ("orca", 1),
            ("WALRUS", 1),   # case-insensitive
            ("zzz_no_match", 0),
        ],
        ids=["by-name", "by-region-2", "by-region-1", "partial-name",
             "case-insensitive", "no-match"],
    )
    def test_search_filters_rows(self, search_term, expected_count):
        result = BrowserQueries.get_table_rows(self.tbl, search=search_term)
        assert result["count"] == expected_count

    def test_search_across_all_columns(self):
        """Search should match in any column, not just the first one."""
        result = BrowserQueries.get_table_rows(self.tbl, search="BC")
        assert result["count"] == 1
        assert result["results"][0]["name"] == "Orca Deep"

    def test_empty_search_returns_all_rows(self):
        result = BrowserQueries.get_table_rows(self.tbl, search="")
        assert result["count"] == 3


# ---------------------------------------------------------------------------
# BrowserQueries.get_table_rows — pagination
# ---------------------------------------------------------------------------

class TestGetTableRowsPagination:
    def setup_method(self):
        self.tbl = "raw_excel_batch_pagination_test"
        _create_temp_table(self.tbl, [("val", "integer")])
        _insert_rows(self.tbl, [{"val": i} for i in range(10)])

    def teardown_method(self):
        _drop_temp_table(self.tbl)

    @pytest.mark.parametrize(
        "page, page_size, expected_len, has_next, has_prev",
        [
            (1, 3, 3, True,  False),
            (2, 3, 3, True,  True),
            (4, 3, 1, False, True),   # last page has only 1 row (10 total)
            (1, 10, 10, False, False),  # all on one page
        ],
        ids=["page-1", "page-2", "last-page", "all-on-one"],
    )
    def test_pagination_behavior(self, page, page_size, expected_len, has_next, has_prev):
        result = BrowserQueries.get_table_rows(
            self.tbl, page=page, page_size=page_size
        )
        assert len(result["results"]) == expected_len
        assert (result["next"] is not None) == has_next
        assert (result["previous"] is not None) == has_prev

    def test_page_size_capped_at_max(self):
        result = BrowserQueries.get_table_rows(self.tbl, page_size=MAX_PAGE_SIZE + 999)
        assert result["page_size"] == MAX_PAGE_SIZE

    def test_page_defaults_to_one(self):
        result = BrowserQueries.get_table_rows(self.tbl)
        assert result["page"] == 1


# ---------------------------------------------------------------------------
# BrowserQueries.table_exists
# ---------------------------------------------------------------------------

class TestTableExists:
    def test_returns_true_for_known_managed_table(self):
        assert BrowserQueries.table_exists("well_status_category") is True

    def test_returns_false_for_nonexistent_table(self):
        assert BrowserQueries.table_exists("this_does_not_exist_xyz_abc") is False

    def test_returns_true_for_newly_created_table(self):
        tbl = "raw_excel_batch_exists_test"
        _create_temp_table(tbl)
        try:
            assert BrowserQueries.table_exists(tbl) is True
        finally:
            _drop_temp_table(tbl)

    def test_returns_false_after_table_dropped(self):
        tbl = "raw_excel_batch_exists_drop_test"
        _create_temp_table(tbl)
        _drop_temp_table(tbl)
        assert BrowserQueries.table_exists(tbl) is False
