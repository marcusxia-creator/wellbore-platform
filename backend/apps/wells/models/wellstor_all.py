from django.db import models


class WellstorAll(models.Model):
    raw_id = models.BigAutoField(primary_key=True)
    source_file = models.TextField(blank=True, null=True)
    import_timestamp = models.TextField(blank=True, null=True)
    user_format_well_id = models.TextField(blank=True, null=True)
    area = models.TextField(blank=True, null=True)
    well_status_text = models.TextField(blank=True, null=True)
    prod_status_text = models.TextField(blank=True, null=True)
    surf_hole_latitude_nad83 = models.TextField(blank=True, null=True)
    surf_hole_longitude_nad83 = models.TextField(blank=True, null=True)
    base_uwi = models.TextField(db_column="uwi_base", blank=True, null=True)
    uwi_suffix = models.TextField(blank=True, null=True)
    deepest_casing_depth = models.TextField(blank=True, null=True)
    deepest_casing_size = models.TextField(blank=True, null=True)
    deepest_casing_grade = models.TextField(blank=True, null=True)
    deepest_casing_weight = models.TextField(blank=True, null=True)
    max_casing_volume_m3 = models.TextField(blank=True, null=True)
    available_wellbore_volume_m3 = models.TextField(blank=True, null=True)
    normalized_wellstor_volume_m3 = models.TextField(blank=True, null=True)
    orphan = models.TextField(blank=True, null=True)
    wellstor_flag = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "wellstor_all"

    def __str__(self):
        return f"{self.base_uwi or self.user_format_well_id} WellStor"
