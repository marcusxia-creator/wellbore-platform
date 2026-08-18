from django.contrib import admin

from apps.wellstor.models import WellFeature


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
