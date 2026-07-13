"""Read layer for the wells app.

Holds all read-only queryset builders, grouped into classes of static methods.
These never mutate data; database writes live in `writes.py`. Handlers call
these methods to fetch data.
"""

from django.db.models import OuterRef, Q, QuerySet, Subquery

from apps.wells.models import WellHeader, WellProductionFormation, WellStatusCategory


class WellQueries:
    """Read-only queries for well records."""

    @staticmethod
    def get_annotated_queryset() -> QuerySet:
        """Return the base well queryset with related data prefetched and status annotated."""
        status_category = WellStatusCategory.objects.filter(base_uwi=OuterRef("base_uwi"))
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
                status_category_value=Subquery(status_category.values("status_category")[:1]),
                actual_status_text_value=Subquery(status_category.values("actual_status_text")[:1]),
            )
        )

    @staticmethod
    def filter_wells(
        queryset: QuerySet,
        *,
        status: str | None = None,
        actual_status: str | None = None,
        well_type: str | None = None,
        formations: list[str] | None = None,
        search: str | None = None,
    ) -> QuerySet:
        """Apply the supported filters and return ordered, distinct results."""
        if status:
            queryset = queryset.filter(
                base_uwi__in=WellStatusCategory.objects.filter(
                    status_category=status
                ).values("base_uwi")
            )
        if actual_status:
            queryset = queryset.filter(
                base_uwi__in=WellStatusCategory.objects.filter(
                    actual_status_text=actual_status
                ).values("base_uwi")
            )
        if well_type:
            queryset = queryset.filter(well_type=well_type)
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
                | Q(cur_operator_name__icontains=search)
            )

        return queryset.order_by("base_uwi", "-suffix", "-raw_id").distinct("base_uwi")


class MetadataQueries:
    """Read-only queries for filter dropdown options."""

    @staticmethod
    def get_actual_well_statuses(status_category: str | None = None) -> QuerySet:
        """Return distinct actual_status_text values, optionally filtered by status_category."""
        queryset = (
            WellStatusCategory.objects.exclude(actual_status_text__isnull=True)
            .exclude(actual_status_text="")
        )
        if status_category:
            queryset = queryset.filter(status_category=status_category)
        return (
            queryset.order_by("actual_status_text")
            .values_list("actual_status_text", flat=True)
            .distinct()
        )

    @staticmethod
    def get_well_types() -> QuerySet:
        """Return distinct well_type values from WellHeader."""
        return (
            WellHeader.objects.exclude(well_type__isnull=True)
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
