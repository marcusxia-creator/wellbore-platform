from django.db import models

from .well_header import WellHeader


class WellCasing(models.Model):
    raw_id = models.BigIntegerField(primary_key=True)
    base_uwi = models.ForeignKey(
        WellHeader,
        models.DO_NOTHING,
        db_column="base_uwi",
        to_field="base_uwi",
        related_name="casing_records",
        db_constraint=False,
        blank=True,
        null=True,
    )
    import_timestamp = models.TextField(blank=True, null=True)
    source_file = models.TextField(blank=True, null=True)
    suffix = models.TextField(blank=True, null=True)
    user_format_well_id = models.TextField(blank=True, null=True)
    casing_depth_m = models.FloatField(blank=True, null=True)
    casing_grade = models.TextField(blank=True, null=True)
    casing_latitude = models.FloatField(blank=True, null=True)
    casing_location = models.TextField(blank=True, null=True)
    casing_longitude = models.FloatField(blank=True, null=True)
    casing_remarks = models.TextField(blank=True, null=True)
    casing_size_mm = models.FloatField(blank=True, null=True)
    casing_weight_kg_m = models.FloatField(blank=True, null=True)
    casing_type = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "well_casing"
        ordering = ["base_uwi", "-suffix", "-raw_id"]

    def __str__(self):
        return f"{self.base_uwi_id} {self.casing_type or 'casing'}"
