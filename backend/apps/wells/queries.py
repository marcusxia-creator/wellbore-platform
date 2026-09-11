"""Read layer for the wells app.

Holds all read-only queryset builders, grouped into classes of static methods.
These never mutate data; database writes live in `writes.py`. Handlers call
these methods to fetch data.

Design principles
-----------------
* Every public method accepts only primitive Python types (str, list, bool) so
  callers never need to know about ORM internals.
* Annotations are additive: `get_annotated_queryset` returns the full base
  queryset; callers may narrow it further with `filter_wells`.
* Multi-value filter params accept a list so one API call can pass e.g.
  status=ABD&status=Suspended without extra plumbing in views.
* The `_optional_subquery` helper gracefully returns a null Value when the
  underlying table does not yet exist (e.g. `production_monthly` before the
  first import), keeping the API stable across deployment stages.
* Operator filtering goes through the `well_current_operator` cache table when
  it exists; otherwise it falls back to a direct `well_status` scan so the
  filter always works regardless of whether the cache has been populated.
"""

from django.contrib.postgres.aggregates import StringAgg
from django.db import connection
from django.db.models import FloatField, OuterRef, Q, QuerySet, Subquery, TextField, Value

from apps.wells.models import (
    InjectionMonthly,
    ProductionMonthly,
    WellCurrentOperator,
    WellHeader,
    WellLocation,
    WellProductionFormation,
    WellStatus,
    WellStatusCategory,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _table_exists(table_name: str) -> bool:
    """Return True if *table_name* exists in the current database."""
    return table_name in connection.introspection.table_names()


# ---------------------------------------------------------------------------
# WellQueries
# ---------------------------------------------------------------------------

class WellQueries:
    """Read-only queries for well records."""

    @staticmethod
    def get_annotated_queryset() -> QuerySet:
        """Return the base well queryset with related data prefetched and
        common scalar values annotated.

        Annotations
        -----------
        status_category_value       – ABD / Suspended / Inactive / Active
        actual_status_text_value    – raw status text from source
        operator_value              – cur_operator_name from latest status row
        well_type_value             – well type from latest status row
        cumulative_oil_volume_value – latest cumulative oil (m³), or null
        cumulative_gas_volume_value – latest cumulative gas (e³m³), or null
        cumulative_fluid_volume_value – latest cumulative fluid (m³), or null
        production_formations_value – semicolon-joined formation names, or null
        """
        status_cat = WellStatusCategory.objects.filter(base_uwi=OuterRef("base_uwi"))

        latest_status = (
            WellStatus.objects.filter(base_uwi=OuterRef("base_uwi"))
            .order_by("-suffix", "-raw_id")
        )

        formations = (
            WellProductionFormation.objects.filter(base_uwi=OuterRef("base_uwi"))
            .values("base_uwi")
            .annotate(
                names=StringAgg(
                    "formation",
                    delimiter="; ",
                    distinct=True,
                    ordering="formation",
                )
            )
            .values("names")
        )

        # Cumulative volumes: degrade gracefully when production_monthly does
        # not yet exist (fresh deployment before first import).
        if _table_exists("production_monthly"):
            prod_monthly = ProductionMonthly.objects.filter(
                base_uwi=OuterRef("base_uwi")
            ).order_by("-production_month")
            cum_oil   = Subquery(prod_monthly.values("cumulative_oil")[:1])
            cum_gas   = Subquery(prod_monthly.values("cumulative_gas")[:1])
            cum_fluid = Subquery(prod_monthly.values("cumulative_fluid")[:1])
        else:
            cum_oil   = Value(None, output_field=FloatField())
            cum_gas   = Value(None, output_field=FloatField())
            cum_fluid = Value(None, output_field=FloatField())

        return (
            WellHeader.objects.all()
            .prefetch_related(
                "locations",
                "statuses",
                "drilling_records",
                "casing_records",
                "production_summaries",
            )
            .annotate(
                status_category_value=Subquery(status_cat.values("status_category")[:1]),
                actual_status_text_value=Subquery(status_cat.values("actual_status_text")[:1]),
                operator_value=Subquery(latest_status.values("cur_operator_name")[:1]),
                well_type_value=Subquery(latest_status.values("well_type")[:1]),
                cumulative_oil_volume_value=cum_oil,
                cumulative_gas_volume_value=cum_gas,
                cumulative_fluid_volume_value=cum_fluid,
                production_formations_value=Subquery(formations, output_field=TextField()),
            )
        )

    @staticmethod
    def filter_wells(
        queryset: QuerySet,
        *,
        status: list[str] | None = None,
        actual_status: list[str] | None = None,
        well_type: list[str] | None = None,
        operator_name: list[str] | None = None,
        formations: list[str] | None = None,
        search: str | None = None,
    ) -> QuerySet:
        """Apply the supported filters and return ordered, distinct results.

        All filters are AND-combined; within each list filter the values are
        OR-combined (e.g. status=["ABD","Suspended"] returns both).

        Operator filter uses the well_current_operator cache when available,
        falls back to a direct well_status scan so the filter works even if
        the cache management command has not been run yet.
        """
        if status:
            queryset = queryset.filter(
                base_uwi__in=WellStatusCategory.objects.filter(
                    status_category__in=status
                ).values("base_uwi")
            )

        if actual_status:
            queryset = queryset.filter(
                base_uwi__in=WellStatusCategory.objects.filter(
                    actual_status_text__in=actual_status
                ).values("base_uwi")
            )

        if well_type:
            queryset = queryset.filter(
                base_uwi__in=WellStatus.objects.filter(
                    well_type__in=well_type
                ).values("base_uwi")
            )

        if operator_name:
            if _table_exists("well_current_operator"):
                queryset = queryset.filter(
                    base_uwi__in=WellCurrentOperator.objects.filter(
                        operator_name__in=operator_name
                    ).values("base_uwi")
                )
            else:
                # Fallback: scan well_status directly
                queryset = queryset.filter(
                    base_uwi__in=WellStatus.objects.filter(
                        cur_operator_name__in=operator_name
                    ).values("base_uwi")
                )

        if formations:
            queryset = queryset.filter(
                base_uwi__in=WellProductionFormation.objects.filter(
                    formation__in=formations
                ).values("base_uwi")
            )

        if search:
            queryset = queryset.filter(
                Q(base_uwi__icontains=search)
                | Q(user_format_well_id__icontains=search)
                | Q(well_name__icontains=search)
                | Q(
                    base_uwi__in=WellStatus.objects.filter(
                        cur_operator_name__icontains=search
                    ).values("base_uwi")
                )
            )

        return queryset.order_by("base_uwi", "-suffix", "-raw_id").distinct("base_uwi")


# ---------------------------------------------------------------------------
# MetadataQueries
# ---------------------------------------------------------------------------

class MetadataQueries:
    """Read-only queries for filter dropdown options."""

    @staticmethod
    def get_actual_well_statuses(status_category: str | None = None) -> QuerySet:
        """Return distinct actual_status_text values, optionally filtered by
        status_category.
        """
        queryset = (
            WellStatusCategory.objects.exclude(actual_status_text__isnull=True)
            .exclude(actual_status_text="")
        )
        if status_category:
            queryset = queryset.filter(status_category=status_category)
        return (
            queryset
            .order_by("actual_status_text")
            .values_list("actual_status_text", flat=True)
            .distinct()
        )

    @staticmethod
    def get_well_types() -> QuerySet:
        """Return distinct well_type values from WellStatus."""
        return (
            WellStatus.objects.exclude(well_type__isnull=True)
            .exclude(well_type="")
            .order_by("well_type")
            .values_list("well_type", flat=True)
            .distinct()
        )

    @staticmethod
    def get_production_injection_formations() -> QuerySet:
        """Return distinct formation values from WellProductionFormation."""
        return (
            WellProductionFormation.objects.exclude(formation__isnull=True)
            .exclude(formation="")
            .order_by("formation")
            .values_list("formation", flat=True)
            .distinct()
        )

    @staticmethod
    def get_current_operators(search: str | None = None) -> QuerySet:
        """Return distinct operator names.

        Uses the well_current_operator cache when available (fast, indexed).
        Falls back to a direct well_status scan so the endpoint works on fresh
        deployments before the cache command is first run.

        Accepts an optional *search* substring for server-side autocomplete.
        """
        if _table_exists("well_current_operator"):
            qs = (
                WellCurrentOperator.objects.exclude(operator_name__isnull=True)
                .exclude(operator_name="")
                .exclude(operator_name="Unknown")
            )
            if search:
                qs = qs.filter(operator_name__icontains=search)
            return qs.order_by("operator_name").values_list("operator_name", flat=True).distinct()

        # Fallback path
        qs = (
            WellStatus.objects.exclude(cur_operator_name__isnull=True)
            .exclude(cur_operator_name="")
        )
        if search:
            qs = qs.filter(cur_operator_name__icontains=search)
        return qs.order_by("cur_operator_name").values_list("cur_operator_name", flat=True).distinct()


# ---------------------------------------------------------------------------
# ProductionQueries
# ---------------------------------------------------------------------------

class ProductionQueries:
    """Read-only queries for production data (map bubbles + daily plot).

    All methods that touch production_daily / production_monthly guard against
    the tables not existing yet via _table_exists(), returning empty results
    on fresh deployments rather than raising exceptions.
    """

    @staticmethod
    def get_daily_production(base_uwi: str) -> list[dict]:
        """Return daily production rows for a single well, ordered by date.

        Each row is a plain dict with keys:
            date          – ISO date string (YYYY-MM-DD)
            daily_oil     – float (bbls)
            daily_water   – float (bbls)
            daily_gas     – float (MCF)
            fluid         – float (bbls)

        Returns an empty list when the production_daily table does not exist
        or the well has no rows.
        """
        if not _table_exists("production_daily"):
            return []

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    production_date,
                    daily_oil,
                    daily_water,
                    daily_gas,
                    fluid
                FROM production_daily
                WHERE base_uwi = %s
                ORDER BY production_date ASC
                """,
                [base_uwi],
            )
            return [
                {
                    "date": row[0].isoformat(),
                    "daily_oil": float(row[1] or 0),
                    "daily_water": float(row[2] or 0),
                    "daily_gas": float(row[3] or 0),
                    "fluid": float(row[4] or 0),
                }
                for row in cursor.fetchall()
            ]

    @staticmethod
    def get_mapped_wells_queryset(
        operator_name: list[str] | None = None,
    ) -> QuerySet:
        """Return an annotated queryset restricted to wells that have coordinates.

        Used by the production map to build the bubble layer. Starts from the
        same full annotation base as WellQueries.get_annotated_queryset() so
        the serializer can read operator, cumulative volumes, and formations
        without extra queries.

        The `operator_name` filter is the primary filter on the production map
        (default: Saguaro Petroleum LLC). Pass None to return all mapped wells.

        Only wells whose *latest* location row has a non-null latitude AND
        longitude are included — unmapped wells cannot be placed on the map.
        """
        # UWIs that have at least one location with both lat and lon.
        mapped_uwis = (
            WellLocation.objects.exclude(latitude__isnull=True)
            .exclude(longitude__isnull=True)
            .values_list("base_uwi", flat=True)
            .distinct()
        )

        queryset = (
            WellQueries.get_annotated_queryset()
            .filter(base_uwi__in=mapped_uwis)
        )

        if operator_name:
            queryset = WellQueries.filter_wells(
                queryset, operator_name=operator_name
            )

        return queryset

    @staticmethod
    def get_production_totals(base_uwi: str) -> dict:
        """Return cumulative production totals for a single well.

        Reads the latest row from production_monthly (highest production_month)
        which already carries running cumulative columns. Returns a dict with:
            cumulative_oil   – float or None
            cumulative_water – float or None
            cumulative_gas   – float or None
            cumulative_fluid – float or None

        Returns all-None dict when production_monthly is absent or the well
        has no rows.
        """
        empty = {
            "cumulative_oil": None,
            "cumulative_water": None,
            "cumulative_gas": None,
            "cumulative_fluid": None,
        }

        if not _table_exists("production_monthly"):
            return empty

        row = (
            ProductionMonthly.objects.filter(base_uwi=base_uwi)
            .order_by("-production_month")
            .values("cumulative_oil", "cumulative_water", "cumulative_gas", "cumulative_fluid")
            .first()
        )

        if row is None:
            return empty

        return {
            "cumulative_oil": row["cumulative_oil"],
            "cumulative_water": row["cumulative_water"],
            "cumulative_gas": row["cumulative_gas"],
            "cumulative_fluid": row["cumulative_fluid"],
        }


# ---------------------------------------------------------------------------
# InjectionQueries
# ---------------------------------------------------------------------------

class InjectionQueries:
    """Read-only queries for injection data (daily plot + cumulative totals).

    All methods guard against the injection tables not yet existing (they are
    created by the data-import pipeline on first injection upload), returning
    safe empty values instead of raising exceptions.
    """

    @staticmethod
    def get_daily_injection(base_uwi: str) -> list[dict]:
        """Return daily injection rows for a single well, ordered by date.

        Each row is a plain dict with keys:
            date               – ISO date string (YYYY-MM-DD)
            daily_water        – float (m³)
            daily_gas          – float (e³m³)
            daily_steam        – float (m³)
            injection_pressure – float (kPa)

        Returns an empty list when the injection_daily table does not exist
        or the well has no rows.
        """
        if not _table_exists("injection_daily"):
            return []

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    injection_date,
                    daily_water,
                    daily_gas,
                    daily_steam,
                    injection_pressure
                FROM injection_daily
                WHERE base_uwi = %s
                ORDER BY injection_date ASC
                """,
                [base_uwi],
            )
            return [
                {
                    "date": row[0].isoformat(),
                    "daily_water": float(row[1] or 0),
                    "daily_gas": float(row[2] or 0),
                    "daily_steam": float(row[3] or 0),
                    "injection_pressure": float(row[4] or 0),
                }
                for row in cursor.fetchall()
            ]

    @staticmethod
    def get_injection_totals(base_uwi: str) -> dict:
        """Return cumulative injection totals for a single well.

        Reads the latest row from injection_monthly (highest injection_month),
        which already carries running cumulative columns. Returns a dict with:
            cumulative_water  – float or None
            cumulative_gas    – float or None
            cumulative_steam  – float or None

        Returns all-None dict when injection_monthly is absent or the well
        has no rows.
        """
        empty = {
            "cumulative_water": None,
            "cumulative_gas": None,
            "cumulative_steam": None,
        }

        if not _table_exists("injection_monthly"):
            return empty

        row = (
            InjectionMonthly.objects.filter(base_uwi=base_uwi)
            .order_by("-injection_month")
            .values("cumulative_water", "cumulative_gas", "cumulative_steam")
            .first()
        )

        if row is None:
            return empty

        return {
            "cumulative_water": row["cumulative_water"],
            "cumulative_gas": row["cumulative_gas"],
            "cumulative_steam": row["cumulative_steam"],
        }

    @staticmethod
    def get_mapped_injection_wells_queryset(
        operator_name: list[str] | None = None,
    ) -> QuerySet:
        """Return an annotated queryset of wells that have injection data AND coordinates.

        Mirrors ProductionQueries.get_mapped_wells_queryset but restricts the
        result to wells that have at least one row in injection_daily. Used to
        power an injection bubble map layer.

        The `operator_name` filter works the same way as in
        WellQueries.filter_wells (cache → fallback).

        Returns an empty queryset when injection_daily does not exist.
        """
        if not _table_exists("injection_daily"):
            return WellHeader.objects.none()

        injection_uwis_sql = "SELECT DISTINCT base_uwi FROM injection_daily"
        with connection.cursor() as cursor:
            cursor.execute(injection_uwis_sql)
            injection_uwis = [row[0] for row in cursor.fetchall()]

        if not injection_uwis:
            return WellHeader.objects.none()

        mapped_uwis = (
            WellLocation.objects.exclude(latitude__isnull=True)
            .exclude(longitude__isnull=True)
            .values_list("base_uwi", flat=True)
            .distinct()
        )

        queryset = (
            WellQueries.get_annotated_queryset()
            .filter(base_uwi__in=mapped_uwis)
            .filter(base_uwi__in=injection_uwis)
        )

        if operator_name:
            queryset = WellQueries.filter_wells(queryset, operator_name=operator_name)

        return queryset
