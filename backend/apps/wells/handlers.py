"""Orchestration layer for the wells app.

Handlers coordinate a request: they parse inputs, call the read layer
(`queries.py`), and shape the result for the views. Views stay thin and only
deal with HTTP; handlers hold the "what to call and in what order" logic.
"""

from django.db.models import QuerySet

from apps.wells.models import WellHeader
from apps.wells.queries import MetadataQueries, WellQueries
from apps.wells.services.well_status_service import STATUS_CATEGORIES


class WellHandler:
    """Coordinates well read requests."""

    @staticmethod
    def list_wells(params) -> QuerySet:
        """Build the filtered well queryset from request query params."""
        queryset = WellQueries.get_annotated_queryset()
        return WellQueries.filter_wells(
            queryset,
            status=params.get("status"),
            actual_status=params.get("actual_status"),
            well_type=params.get("well_type"),
            formations=params.getlist("prod_inject_frmtn"),
            search=params.get("search"),
        )

    @staticmethod
    def get_well_detail(base_uwi: str):
        """Return a single well with all related data, or raise 404."""
        return WellQueries.get_well_detail(base_uwi)


class MetadataHandler:
    """Coordinates filter-option reads and shapes them as {value, label} lists."""

    @staticmethod
    def well_statuses() -> list[dict]:
        return [{"value": status, "label": status} for status in STATUS_CATEGORIES]

    @staticmethod
    def actual_well_statuses(status_category: str | None = None) -> list[dict]:
        statuses = MetadataQueries.get_actual_well_statuses(status_category)
        return [{"value": status, "label": status} for status in statuses]

    @staticmethod
    def well_types() -> list[dict]:
        types = MetadataQueries.get_well_types()
        return [{"value": well_type, "label": well_type} for well_type in types]

    @staticmethod
    def production_injection_formations() -> list[dict]:
        formations = MetadataQueries.get_production_injection_formations()
        return [{"value": formation, "label": formation} for formation in formations]
