"""Write layer for the wells app.

Holds all database mutations, keeping them separate from the read layer in
`queries.py`. Callers (management commands, future tasks/handlers) invoke these
functions instead of writing SQL inline, enforcing a clear read/write split
(`queries.py` for reads, `writes.py` for writes).

Writable (Django-managed) cache tables
---------------------------------------
* well_status_category       — derived status category per well
* well_production_formation  — one row per (well, formation) from prod summary
* well_current_operator      — most-recent operator per well

Unmanaged tables written by this module
----------------------------------------
* production_monthly         — monthly aggregates rebuilt from production_daily
  (table owned by the data-import pipeline; this module only rebuilds it when
  called explicitly, e.g. after a bulk daily-data correction)

Every other table in this app is read-only from this module's perspective.

Calling convention
------------------
All public functions return a simple value (int or tuple[int, ...]) indicating
how many rows were written so that management commands can log progress.
"""

from django.db import connection
from django.utils import timezone

from apps.wells.services.well_status_service import cutoff_24_months


def refresh_well_status_categories() -> int:
    """Populate the well_status_category cache table from source tables.

    Clears the table and fills it in a single statement, using the 24-month
    activity cutoff to derive each well's status category. Returns the number
    of rows written.

    Status logic (matches well_status_service.categorize_status):
        1. status text contains 'abd'  → ABD
        2. status text contains 'susp' → Suspended
        3. last activity < 24 months ago → Inactive
        4. otherwise → Active
    """
    cutoff = cutoff_24_months()

    sql = """
    TRUNCATE TABLE well_status_category;

    INSERT INTO well_status_category (
        base_uwi,
        status_category,
        actual_status_text,
        last_production_date,
        last_injection_date,
        refreshed_at
    )
    WITH selected_header AS (
        SELECT DISTINCT ON (base_uwi)
            base_uwi,
            suffix,
            raw_id
        FROM well_header
        WHERE base_uwi IS NOT NULL
        ORDER BY base_uwi, suffix DESC NULLS LAST, raw_id DESC NULLS LAST
    ),
    latest_status AS (
        SELECT DISTINCT ON (base_uwi)
            base_uwi,
            suffix,
            well_status_text
        FROM well_status
        WHERE base_uwi IS NOT NULL
        ORDER BY base_uwi, suffix DESC NULLS LAST, raw_id DESC NULLS LAST
    ),
    production_dates AS (
        SELECT DISTINCT ON (base_uwi)
            base_uwi,
            suffix,
            GREATEST(
                CASE
                    WHEN last_prod_yyyy_mm ~ '^[0-9]{4}[/\\-][0-9]{2}[/\\-][0-9]{2}$'
                    THEN to_date(replace(last_prod_yyyy_mm, '-', '/'), 'YYYY/MM/DD')
                    ELSE NULL
                END,
                on_prod_yyyy_mm_dd
            ) AS last_production_date,
            GREATEST(
                CASE
                    WHEN last_inject_yyyy_mm ~ '^[0-9]{4}[/\\-][0-9]{2}[/\\-][0-9]{2}$'
                    THEN to_date(replace(last_inject_yyyy_mm, '-', '/'), 'YYYY/MM/DD')
                    ELSE NULL
                END,
                on_inject_yyyy_mm_dd
            ) AS last_injection_date
        FROM well_production_summary
        WHERE base_uwi IS NOT NULL
        ORDER BY base_uwi, suffix DESC NULLS LAST, raw_id DESC NULLS LAST
    )
    SELECT
        h.base_uwi,
        CASE
            WHEN LOWER(COALESCE(s.well_status_text, '')) LIKE '%%abd%%' THEN 'ABD'
            WHEN LOWER(COALESCE(s.well_status_text, '')) LIKE '%%susp%%' THEN 'Suspended'
            WHEN (
                p.last_production_date IS NOT NULL AND p.last_production_date < %s
            ) OR (
                p.last_injection_date IS NOT NULL AND p.last_injection_date < %s
            ) THEN 'Inactive'
            ELSE 'Active'
        END AS status_category,
        s.well_status_text AS actual_status_text,
        p.last_production_date,
        p.last_injection_date,
        %s AS refreshed_at
    FROM selected_header h
    LEFT JOIN latest_status s ON s.base_uwi = h.base_uwi
    LEFT JOIN production_dates p ON p.base_uwi = h.base_uwi;
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [cutoff, cutoff, timezone.now()])
        cursor.execute("SELECT COUNT(*) FROM well_status_category")
        count = cursor.fetchone()[0]

    return count


def refresh_well_production_formations() -> tuple[int, int]:
    """Populate the well_production_formation cache table from source tables.

    Clears the table and fills it by splitting each well's `prod_inject_frmtn`
    value on ';' into individual formation rows. Returns a tuple of
    (mapping row count, distinct formation count).
    """
    sql = """
    TRUNCATE TABLE well_production_formation;

    INSERT INTO well_production_formation (
        base_uwi,
        formation,
        source_value,
        suffix,
        refreshed_at
    )
    WITH selected_production AS (
        SELECT DISTINCT ON (base_uwi)
            base_uwi,
            suffix,
            raw_id,
            prod_inject_frmtn
        FROM well_production_summary
        WHERE base_uwi IS NOT NULL
          AND prod_inject_frmtn IS NOT NULL
          AND btrim(prod_inject_frmtn) <> ''
        ORDER BY base_uwi, suffix DESC NULLS LAST, raw_id DESC NULLS LAST
    ),
    sliced AS (
        SELECT
            base_uwi,
            btrim(formation_part) AS formation,
            prod_inject_frmtn AS source_value,
            suffix
        FROM selected_production,
        regexp_split_to_table(prod_inject_frmtn, ';') AS formation_part
    )
    SELECT DISTINCT ON (base_uwi, formation)
        base_uwi,
        formation,
        source_value,
        suffix,
        %s AS refreshed_at
    FROM sliced
    WHERE formation <> ''
    ORDER BY base_uwi, formation, suffix DESC NULLS LAST;
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [timezone.now()])
        cursor.execute("SELECT COUNT(*) FROM well_production_formation")
        mapping_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT formation) FROM well_production_formation")
        formation_count = cursor.fetchone()[0]

    return mapping_count, formation_count


def refresh_well_current_operators() -> int:
    """Populate the well_current_operator cache table from source tables.

    For each unique base_uwi, picks the single most-recent operator name by
    choosing the row with the highest suffix (then raw_id) from well_status.
    Falls back to well_header.cur_operator_name when well_status has no
    cur_operator_name, so the cache is always populated even on sparse data.

    Returns the number of rows written.

    Why a separate cache table?
    ---------------------------
    The operator dropdown on the dashboard/production map requires fast
    DISTINCT queries over potentially tens of thousands of wells. A cache table
    with a dedicated index is significantly faster than scanning well_status at
    request time, and keeps the query layer clean (no inline CTEs in views).
    """
    sql = """
    TRUNCATE TABLE well_current_operator;

    INSERT INTO well_current_operator (
        base_uwi,
        operator_name,
        suffix,
        raw_id,
        refreshed_at
    )
    WITH selected_header AS (
        -- Canonical well list: one row per base_uwi (latest suffix/raw_id).
        SELECT DISTINCT ON (base_uwi)
            base_uwi,
            suffix,
            raw_id,
            cur_operator_name AS header_operator_name
        FROM well_header
        WHERE base_uwi IS NOT NULL
        ORDER BY base_uwi, suffix DESC NULLS LAST, raw_id DESC NULLS LAST
    ),
    latest_status AS (
        -- Most-recent operator name from well_status per base_uwi.
        SELECT DISTINCT ON (base_uwi)
            base_uwi,
            suffix,
            raw_id,
            cur_operator_name AS status_operator_name
        FROM well_status
        WHERE base_uwi IS NOT NULL
        ORDER BY base_uwi, suffix DESC NULLS LAST, raw_id DESC NULLS LAST
    )
    SELECT
        h.base_uwi,
        -- Prefer the status table; fall back to well_header if status has none.
        COALESCE(
            NULLIF(btrim(s.status_operator_name), ''),
            NULLIF(btrim(h.header_operator_name), ''),
            'Unknown'
        ) AS operator_name,
        COALESCE(s.suffix, h.suffix)   AS suffix,
        COALESCE(s.raw_id, h.raw_id)   AS raw_id,
        %s AS refreshed_at
    FROM selected_header h
    LEFT JOIN latest_status s ON s.base_uwi = h.base_uwi;
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [timezone.now()])
        cursor.execute("SELECT COUNT(*) FROM well_current_operator")
        count = cursor.fetchone()[0]

    return count


def rebuild_production_monthly(base_uwis: list[str] | None = None) -> int:
    """Rebuild production_monthly from production_daily for the given wells.

    Aggregates daily rows into monthly buckets and computes running cumulative
    totals using SQL window functions (matching the schema written by the
    data-import pipeline). Deletes existing monthly rows for the affected wells
    before re-inserting so that corrected daily data is fully reflected.

    Parameters
    ----------
    base_uwis:
        Optional list of UWIs to rebuild. When None, rebuilds every well that
        has rows in production_daily (full refresh).

    Returns
    -------
    int
        Number of rows written to production_monthly.

    Raises
    ------
    RuntimeError
        If production_daily does not exist (table has never been created by the
        import pipeline). Callers should guard with _table_exists when
        appropriate.

    Notes
    -----
    This function intentionally does NOT truncate production_monthly globally —
    it only touches the rows for the supplied (or all) base_uwis so that a
    partial rebuild for one well does not destroy data for others.
    """
    sql_all_uwis = """
    SELECT DISTINCT base_uwi FROM production_daily
    """
    sql_delete = """
    DELETE FROM production_monthly WHERE base_uwi = ANY(%s)
    """
    sql_insert = """
    INSERT INTO production_monthly (
        base_uwi,
        production_month,
        monthly_oil,
        monthly_water,
        monthly_gas,
        monthly_fluid,
        cumulative_oil,
        cumulative_water,
        cumulative_gas,
        cumulative_fluid,
        updated_at
    )
    WITH monthly AS (
        SELECT
            base_uwi,
            date_trunc('month', production_date)::date  AS production_month,
            SUM(daily_oil)                              AS monthly_oil,
            SUM(daily_water)                            AS monthly_water,
            SUM(daily_gas)                              AS monthly_gas,
            SUM(fluid)                                  AS monthly_fluid
        FROM production_daily
        WHERE base_uwi = ANY(%s)
        GROUP BY base_uwi, date_trunc('month', production_date)::date
    )
    SELECT
        base_uwi,
        production_month,
        monthly_oil,
        monthly_water,
        monthly_gas,
        monthly_fluid,
        SUM(monthly_oil)   OVER (PARTITION BY base_uwi ORDER BY production_month)
            AS cumulative_oil,
        SUM(monthly_water) OVER (PARTITION BY base_uwi ORDER BY production_month)
            AS cumulative_water,
        SUM(monthly_gas)   OVER (PARTITION BY base_uwi ORDER BY production_month)
            AS cumulative_gas,
        SUM(monthly_fluid) OVER (PARTITION BY base_uwi ORDER BY production_month)
            AS cumulative_fluid,
        %s AS updated_at
    FROM monthly
    ORDER BY base_uwi, production_month
    """

    with connection.cursor() as cursor:
        # Resolve target UWIs when not supplied by caller.
        if base_uwis is None:
            cursor.execute(sql_all_uwis)
            base_uwis = [row[0] for row in cursor.fetchall()]

        if not base_uwis:
            return 0

        cursor.execute(sql_delete, [base_uwis])
        cursor.execute(sql_insert, [base_uwis, timezone.now()])
        cursor.execute(
            "SELECT COUNT(*) FROM production_monthly WHERE base_uwi = ANY(%s)",
            [base_uwis],
        )
        count = cursor.fetchone()[0]

    return count


def rebuild_injection_monthly(base_uwis: list[str] | None = None) -> int:
    """Rebuild injection_monthly from injection_daily for the given wells.

    Aggregates daily rows into monthly buckets and computes running cumulative
    totals using SQL window functions (water, gas, steam). Deletes existing
    monthly rows for the affected wells before re-inserting so that corrected
    daily data is fully reflected.

    Parameters
    ----------
    base_uwis:
        Optional list of UWIs to rebuild. When None, rebuilds every well that
        has rows in injection_daily (full refresh).

    Returns
    -------
    int
        Number of rows written to injection_monthly.

    Notes
    -----
    This function intentionally does NOT truncate injection_monthly globally —
    it only touches the rows for the supplied (or all) base_uwis so that a
    partial rebuild for one well does not destroy data for others.
    """
    sql_all_uwis = """
    SELECT DISTINCT base_uwi FROM injection_daily
    """
    sql_delete = """
    DELETE FROM injection_monthly WHERE base_uwi = ANY(%s)
    """
    sql_insert = """
    INSERT INTO injection_monthly (
        base_uwi,
        injection_month,
        monthly_water,
        monthly_gas,
        monthly_steam,
        cumulative_water,
        cumulative_gas,
        cumulative_steam,
        updated_at
    )
    WITH monthly AS (
        SELECT
            base_uwi,
            date_trunc('month', injection_date)::date  AS injection_month,
            SUM(daily_water)                           AS monthly_water,
            SUM(daily_gas)                             AS monthly_gas,
            SUM(daily_steam)                           AS monthly_steam
        FROM injection_daily
        WHERE base_uwi = ANY(%s)
        GROUP BY base_uwi, date_trunc('month', injection_date)::date
    )
    SELECT
        base_uwi,
        injection_month,
        monthly_water,
        monthly_gas,
        monthly_steam,
        SUM(monthly_water) OVER (PARTITION BY base_uwi ORDER BY injection_month)
            AS cumulative_water,
        SUM(monthly_gas)   OVER (PARTITION BY base_uwi ORDER BY injection_month)
            AS cumulative_gas,
        SUM(monthly_steam) OVER (PARTITION BY base_uwi ORDER BY injection_month)
            AS cumulative_steam,
        %s AS updated_at
    FROM monthly
    ORDER BY base_uwi, injection_month
    ON CONFLICT (base_uwi, injection_month) DO UPDATE SET
        monthly_water    = EXCLUDED.monthly_water,
        monthly_gas      = EXCLUDED.monthly_gas,
        monthly_steam    = EXCLUDED.monthly_steam,
        cumulative_water = EXCLUDED.cumulative_water,
        cumulative_gas   = EXCLUDED.cumulative_gas,
        cumulative_steam = EXCLUDED.cumulative_steam,
        updated_at       = EXCLUDED.updated_at
    """

    with connection.cursor() as cursor:
        # Resolve target UWIs when not supplied by caller.
        if base_uwis is None:
            cursor.execute(sql_all_uwis)
            base_uwis = [row[0] for row in cursor.fetchall()]

        if not base_uwis:
            return 0

        cursor.execute(sql_delete, [base_uwis])
        cursor.execute(sql_insert, [base_uwis, timezone.now()])
        cursor.execute(
            "SELECT COUNT(*) FROM injection_monthly WHERE base_uwi = ANY(%s)",
            [base_uwis],
        )
        count = cursor.fetchone()[0]

    return count
