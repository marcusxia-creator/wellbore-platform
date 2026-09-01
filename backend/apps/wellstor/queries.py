"""Read layer for the wellstor app.

Holds all read-only queryset builders for wellstor ML data, grouped into
classes of static methods. These never mutate data; writes live in `writes.py`.
"""

from django.db.models import QuerySet

from apps.wellstor.models import RegionPrediction, WellFeature, WellStorPrediction


class WellFeatureQueries:
    """Read-only queries for WellFeature records."""

    @staticmethod
    def get_all() -> QuerySet:
        """Return all WellFeature rows ordered by base_uwi."""
        return WellFeature.objects.order_by("base_uwi")

    @staticmethod
    def get_wellstor_candidates() -> QuerySet:
        """Return WellFeature rows flagged as WellStor candidates."""
        return WellFeature.objects.filter(wellstor_flag=True).order_by("base_uwi")

    @staticmethod
    def get_for_well(base_uwi: str) -> WellFeature | None:
        """Return the WellFeature for a given well, or None if not yet computed."""
        return WellFeature.objects.filter(base_uwi=base_uwi).first()


class WellStorPredictionQueries:
    """Read-only queries for single-well model prediction records."""

    @staticmethod
    def get_for_well(base_uwi: str) -> QuerySet:
        """Return all prediction rows for a well, newest first."""
        return (
            WellStorPrediction.objects.filter(base_uwi=base_uwi)
            .select_related("nearest_substation")
            .order_by("-created_at")
        )

    @staticmethod
    def get_candidates(model_version: str | None = None) -> QuerySet:
        """Return prediction rows where wellstore_candidate is True.

        Optionally filter to a specific model version.
        """
        queryset = WellStorPrediction.objects.filter(wellstore_candidate=True).select_related(
            "nearest_substation"
        )
        if model_version:
            queryset = queryset.filter(model_version=model_version)
        return queryset.order_by("base_uwi", "-created_at")


class RegionPredictionQueries:
    """Read-only queries for region-level model prediction records."""

    @staticmethod
    def get_all(model_version: str | None = None) -> QuerySet:
        """Return all region prediction rows with substation data prefetched.

        Optionally filter to a specific model version.
        """
        queryset = RegionPrediction.objects.select_related("substation")
        if model_version:
            queryset = queryset.filter(model_version=model_version)
        return queryset.order_by("substation__name", "-created_at")

    @staticmethod
    def get_suitable_regions(model_version: str | None = None) -> QuerySet:
        """Return region predictions where substation_candidate is True."""
        queryset = RegionPrediction.objects.filter(substation_candidate=True).select_related(
            "substation"
        )
        if model_version:
            queryset = queryset.filter(model_version=model_version)
        return queryset.order_by("-suitable_probability")

    @staticmethod
    def get_for_substation(substation_id: int) -> QuerySet:
        """Return all region predictions for a given substation, newest first."""
        return (
            RegionPrediction.objects.filter(substation_id=substation_id)
            .select_related("substation")
            .order_by("-created_at")
        )
