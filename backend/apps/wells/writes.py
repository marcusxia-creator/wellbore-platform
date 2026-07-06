"""Write layer for the wells app.

Holds all database mutations, keeping them separate from the read layer in
`queries.py`. Callers (management commands, future tasks/handlers) invoke these
functions instead of writing SQL inline, enforcing a clear read/write split
(`queries.py` for reads, `writes.py` for writes).

The only writable tables in this app are the derived cache tables
`well_status_category` and `well_production_formation`; every other table is an
unmanaged read-only legacy table.
"""

from django.db import connection
from django.utils import timezone

from apps.wells.services.well_status_service import cutoff_24_months


def refresh_well_status_categories() -> int:
    """Populate the well_status_category cache table from source tables.

    Clears the table and fills it in a single statement, using the 24-month
    activity cutoff to derive each well's status category. Returns the number of
    rows written.
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
    value on `;` into individual formation rows. Returns a tuple of
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
