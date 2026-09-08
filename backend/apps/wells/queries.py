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
    ProductionMonthly,
    WellCurrentOperator,
    WellHeader,
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
