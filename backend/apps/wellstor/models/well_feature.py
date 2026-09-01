"""Per-well machine-learning feature record.

One row per well, holding the processed feature columns that feed the WellStor
candidate-selection models. Values are produced by the upstream processed-data
pipeline; this table is the persisted, queryable home for them.

Linked to the read-only `wells.WellHeader` logically via `base_uwi` (the
upstream `well_id`). No database foreign key is used: WellHeader maps an
externally-owned, unmanaged table, so this table follows the same convention as
the wells cache tables and joins on the `base_uwi` text value instead.
"""

from django.db import models

from apps.wellstor.enums import DeepestCasingType, PerforationType


class WellFeature(models.Model):
    base_uwi = models.TextField(unique=True, db_index=True)  # logical link to WellHeader.base_uwi

    # identity / land location
    user_format_well_id = models.TextField(blank=True, null=True)
    uwi_suffix = models.TextField(blank=True, null=True)  # event suffix; may be empty
    loc_exc_code = models.SmallIntegerField(blank=True, null=True)
    legal_subdivisions = models.SmallIntegerField(blank=True, null=True)
    section = models.SmallIntegerField(blank=True, null=True)
    township = models.SmallIntegerField(blank=True, null=True)
    range = models.SmallIntegerField(blank=True, null=True)
    meridian = models.SmallIntegerField(blank=True, null=True)
    # BC NTS location parts (ATS wells leave these null)
    nts_prefix = models.TextField(blank=True, null=True)
    nts_quarter = models.TextField(blank=True, null=True)
    nts_unit = models.TextField(blank=True, null=True)
    nts_block = models.TextField(blank=True, null=True)
    nts_series = models.TextField(blank=True, null=True)
    nts_area = models.TextField(blank=True, null=True)
    nts_sheet = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    well_status_text = models.TextField(blank=True, null=True)

    # perforation
    perforation_top_depth_md = models.FloatField(blank=True, null=True)
    perforation_date = models.IntegerField(blank=True, null=True)  # yyyymmdd
    perforation_type = models.IntegerField(choices=PerforationType.choices, blank=True, null=True)
    govt_reported_type = models.TextField(blank=True, null=True)

    # deepest casing
    deepest_casing_type = models.IntegerField(choices=DeepestCasingType.choices, blank=True, null=True)
    deepest_casing_depth = models.FloatField(blank=True, null=True)
    deepest_casing_size = models.FloatField(blank=True, null=True)
    deepest_casing_weight = models.FloatField(blank=True, null=True)
    deepest_casing_grade = models.TextField(blank=True, null=True)
    deepest_casing_id = models.FloatField(blank=True, null=True)  # inner diameter, mm
    liner_start_m = models.FloatField(blank=True, null=True)
    liner_end_m = models.FloatField(blank=True, null=True)

    # geometry
    md_all_wells = models.FloatField(blank=True, null=True)
    tvd_m = models.FloatField(blank=True, null=True)
    lateral_length_m = models.FloatField(blank=True, null=True)

    # activity
    months_since_last_prod = models.IntegerField(blank=True, null=True)
    months_since_last_inj = models.IntegerField(blank=True, null=True)
    idle_well_flag = models.BooleanField(blank=True, null=True)
    wellstor_flag = models.BooleanField(blank=True, null=True)  # susp/abd status or idle

    # volume / pressure (core model features)
    depth_for_available_volume = models.FloatField(blank=True, null=True)
    max_casing_volume_m3 = models.FloatField(blank=True, null=True)
    available_wellbore_volume_m3 = models.FloatField(blank=True, null=True)
    normalized_available_volume = models.FloatField(blank=True, null=True)
    pressure_grade = models.FloatField(blank=True, null=True)
    casing_burst_rating_psi = models.FloatField(blank=True, null=True)

    # computed columns derived by the processed-data pipeline
    percentage_top_depth_md_tvd = models.FloatField(blank=True, null=True)
    usable_air_mass = models.FloatField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "well_feature"
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        return f"{self.base_uwi} feature"
