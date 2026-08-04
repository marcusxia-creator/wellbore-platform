from django.contrib import admin

from apps.wellstor.models import (
    RegionPrediction,
    RegionRadiusResult,
    Substation,
    WellFeature,
    WellStorPrediction,
)


@admin.register(RegionPrediction)
class RegionPredictionAdmin(admin.ModelAdmin):
    list_display = (
        "substation",
        "substation_candidate",
        "suitable_probability",
        "suitable_radius",
        "well_count",
        "good_count",
    )
    list_filter = ("substation_candidate",)
    search_fields = ("substation__facility_code", "substation__facility_name")


@admin.register(RegionRadiusResult)
class RegionRadiusResultAdmin(admin.ModelAdmin):
    list_display = (
        "substation",
        "radius_m",
        "well_count",
        "good_count",
        "suitable_probability",
        "substation_candidate",
    )
    list_filter = ("substation_candidate", "radius_m")
    search_fields = ("substation__facility_code", "substation__facility_name")


@admin.register(WellStorPrediction)
class WellStorPredictionAdmin(admin.ModelAdmin):
    list_display = (
        "base_uwi",
        "nearest_substation",
        "distance_m",
        "good_probability",
        "wellstore_candidate",
        "radius_m",
    )
    list_filter = ("wellstore_candidate", "radius_m")
    search_fields = ("base_uwi",)


@admin.register(Substation)
class SubstationAdmin(admin.ModelAdmin):
    list_display = ("facility_code", "facility_name", "latitude", "longitude", "capacity_mw")
    search_fields = ("facility_code", "facility_name")


@admin.register(WellFeature)
class WellFeatureAdmin(admin.ModelAdmin):
    list_display = (
        "base_uwi",
        "latitude",
        "longitude",
        "wellstor_flag",
        "normalized_available_volume",
        "casing_burst_rating_psi",
        "usable_air_mass",
    )
    list_filter = ("wellstor_flag", "idle_well_flag")
    search_fields = ("base_uwi", "user_format_well_id")
    readonly_fields = [field.name for field in WellFeature._meta.fields]
