"""Read layer for the data_browser app.

All functions are read-only. They use Django's database connection so no
separate psycopg connection is needed — the app reuses the existing Django
DB configuration.

Design principles
-----------------
* All table/column identifiers are validated against a strict regex before
  being interpolated into SQL to prevent SQL injection.
* Column selection, search, and pagination are all handled server-side to
  avoid transferring unnecessarily large result sets.
* Functions return plain Python dicts/lists so handlers never need to know
  about DB internals.
"""

import re

from django.db import connection

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Only allow identifiers that start with a letter or underscore and contain
# only letters, digits, and underscores — matches PostgreSQL identifier rules.
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Hard cap on rows returned per page to prevent accidental full-table dumps.
MAX_PAGE_SIZE = 500

# Only tables with these prefixes may be deleted via the write layer.
DELETABLE_TABLE_PREFIXES = ("raw_excel_batch_", "unique_raw_excel_batch_")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_identifier(value: str, label: str = "identifier") -> str:
    """Raise ValueError if *value* is not a safe SQL identifier."""
    if not _SAFE_IDENTIFIER.fullmatch(value or ""):
        raise ValueError(f"Invalid {label}: {value!r}")
    return value


def _int_param(value, default: int) -> int:
    """Coerce *value* to int, returning *default* on failure."""
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# BrowserQueries
# ---------------------------------------------------------------------------

class BrowserQueries:
    """Read-only introspection and data queries for the data browser."""

    @staticmethod
    def get_table_catalog() -> list[dict]:
        """Return the full catalog of public tables in the current database.

        Each entry in the returned list has the shape::

            {
                "name": str,                  # table name
                "estimated_rows": int,        # pg_stat_user_tables estimate
                "columns": [
                    {"name": str, "type": str, "position": int},
                    ...
                ],
            }

        Tables are ordered alphabetically. Columns within each table are
        ordered by their ordinal position.
        """
        sql = """
        SELECT
            c.table_name,
            c.column_name,
            c.data_type,
            c.ordinal_position,
            COALESCE(s.n_live_tup, 0)::bigint AS estimated_rows
        FROM information_schema.columns c
        LEFT JOIN pg_stat_user_tables s
            ON s.schemaname = c.table_schema
            AND s.relname   = c.table_name
        WHERE c.table_schema = 'public'
        ORDER BY c.table_name, c.ordinal_position
        """
        tables: dict[str, dict] = {}
        with connection.cursor() as cursor:
            cursor.execute(sql)
            for table_name, column_name, data_type, position, estimated_rows in cursor.fetchall():
                entry = tables.setdefault(
                    table_name,
                    {
                        "name": table_name,
                        "estimated_rows": estimated_rows,
                        "columns": [],
                    },
                )
                entry["columns"].append(
                    {"name": column_name, "type": data_type, "position": position}
                )
        return list(tables.values())

    @staticmethod
    def get_table_columns(table_name: str) -> list[dict]:
        """Return column metadata for a single table.

        Parameters
        ----------
        table_name:
            Name of the table to inspect. Must be a valid SQL identifier.

        Returns
        -------
        list[dict]
            Each dict has keys ``name``, ``type``, ``position``.

        Raises
        ------
        ValueError
            If *table_name* is not a valid identifier or does not exist in
            the public schema.
        """
        _validate_identifier(table_name, "table name")
        catalog = BrowserQueries.get_table_catalog()
        table = next((t for t in catalog if t["name"] == table_name), None)
        if table is None:
            raise ValueError(f"Table {table_name!r} does not exist.")
        return table["columns"]

    @staticmethod
    def get_table_rows(
        table_name: str,
        *,
        columns: list[str] | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict:
        """Return paginated rows from *table_name* with optional column
        selection and full-text search.

        Parameters
        ----------
        table_name:
            Target table. Must be a valid SQL identifier.
        columns:
            Subset of column names to return. Defaults to all columns.
            Any column name not present in the table is silently ignored.
        search:
            Optional search string. When supplied, every column is cast to
            text and searched with ILIKE so the search is case-insensitive.
        page:
            1-based page number.
        page_size:
            Rows per page; capped at MAX_PAGE_SIZE (500).

        Returns
        -------
        dict with keys:
            table        – table name
            columns      – list of column metadata dicts for selected columns
            count        – total matching rows (before pagination)
            page         – current page
            page_size    – effective page size
            next         – next page number or None
            previous     – previous page number or None
            results      – list of row dicts (values cast to str)

        Raises
        ------
        ValueError
            If *table_name* is invalid or does not exist.
        """
        _validate_identifier(table_name, "table name")
        all_columns = BrowserQueries.get_table_columns(table_name)
        all_column_names = [c["name"] for c in all_columns]

        # Resolve selected columns; silently drop any not in the table.
        if columns:
            selected_names = [c for c in columns if c in all_column_names]
        else:
            selected_names = all_column_names
        if not selected_names:
            selected_names = all_column_names

        # Sanitize pagination params.
        page = max(_int_param(page, 1), 1)
        page_size = min(max(_int_param(page_size, 100), 1), MAX_PAGE_SIZE)
        offset = (page - 1) * page_size

        # Build WHERE clause for full-text search across all columns.
        # We search all columns (not just selected ones) for consistency with
        # the reference implementation.
        where_sql = ""
        where_params: list = []
        if search and search.strip():
            search = search.strip()
            conditions = " OR ".join(
                f'"{col}"::text ILIKE %s' for col in all_column_names
            )
            where_sql = f" WHERE {conditions}"
            where_params = [f"%{search}%"] * len(all_column_names)

        # SELECT clause: cast every selected column to text for uniform output.
        select_clause = ", ".join(
            f'"{col}"::text AS "{col}"' for col in selected_names
        )
        order_col = all_column_names[0]

        with connection.cursor() as cursor:
            # Total count.
            cursor.execute(
                f'SELECT COUNT(*) FROM "{table_name}"{where_sql}',
                where_params,
            )
            count = cursor.fetchone()[0]

            # Data page.
            cursor.execute(
                f'SELECT {select_clause} FROM "{table_name}"{where_sql}'
                f' ORDER BY "{order_col}"::text NULLS LAST'
                f" LIMIT %s OFFSET %s",
                [*where_params, page_size, offset],
            )
            col_names = [desc[0] for desc in cursor.description]
            results = [dict(zip(col_names, row)) for row in cursor.fetchall()]

        selected_col_meta = [c for c in all_columns if c["name"] in selected_names]

        return {
            "table": table_name,
            "columns": selected_col_meta,
            "count": count,
            "page": page,
            "page_size": page_size,
            "next": page + 1 if offset + page_size < count else None,
            "previous": page - 1 if page > 1 else None,
            "results": results,
        }

    @staticmethod
    def table_exists(table_name: str) -> bool:
        """Return True if *table_name* exists in the public schema.

        Does not validate the identifier — callers should do that themselves
        when the value originates from user input.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                )
                """,
                [table_name],
            )
            return cursor.fetchone()[0]
