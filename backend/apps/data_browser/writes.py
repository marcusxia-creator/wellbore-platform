"""Write layer for the data_browser app.

The only mutation supported here is dropping temporary import tables.
All other data in the system is managed by the wells app writes layer
or by the data-import pipeline.

Safety rules
------------
* Only tables whose names start with a DELETABLE_TABLE_PREFIXES prefix may
  be dropped. Any attempt to delete a core schema table raises ValueError.
* The table name is validated as a safe SQL identifier before being used in
  a DROP TABLE statement to prevent SQL injection.
* The table must exist; attempting to delete a non-existent table raises
  ValueError rather than silently succeeding.
"""

from django.db import connection

from apps.data_browser.queries import DELETABLE_TABLE_PREFIXES, _validate_identifier


class BrowserWrites:
    """Mutation operations for the data browser."""

    @staticmethod
    def drop_table(table_name: str) -> dict:
        """Drop a temporary import table from the database.

        Parameters
        ----------
        table_name:
            Name of the table to drop. Must be a valid SQL identifier and
            must start with one of the DELETABLE_TABLE_PREFIXES.

        Returns
        -------
        dict
            ``{"table": table_name, "deleted": True}`` on success.

        Raises
        ------
        ValueError
            If *table_name* is not a valid identifier, does not start with
            a deletable prefix, or does not exist in the public schema.
        """
        _validate_identifier(table_name, "table name")

        if not table_name.startswith(DELETABLE_TABLE_PREFIXES):
            prefixes = ", ".join(f"{p}*" for p in DELETABLE_TABLE_PREFIXES)
            raise ValueError(
                f"Only import staging tables may be deleted here "
                f"(allowed prefixes: {prefixes})."
            )

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
            if not cursor.fetchone()[0]:
                raise ValueError(f"Table {table_name!r} does not exist.")

            # Use a quoted identifier to handle any edge cases in table names.
            cursor.execute(f'DROP TABLE "{table_name}" CASCADE')

        return {"table": table_name, "deleted": True}
