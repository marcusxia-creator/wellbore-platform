from django.contrib import admin

from apps.wellstor.models import Substation, WellFeature


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
