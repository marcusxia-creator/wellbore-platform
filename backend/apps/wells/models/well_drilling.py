from django.db import models

from .well_header import WellHeader


class WellDrilling(models.Model):
    raw_id = models.BigIntegerField(primary_key=True)
    base_uwi = models.ForeignKey(
        WellHeader,
        models.DO_NOTHING,
        db_column="base_uwi",
        to_field="base_uwi",
        related_name="drilling_records",
        db_constraint=False,
        blank=True,
        null=True,
    )
    import_timestamp = models.TextField(blank=True, null=True)
    source_file = models.TextField(blank=True, null=True)
    suffix = models.TextField(blank=True, null=True)
    user_format_well_id = models.TextField(blank=True, null=True)
    date_drlg_completed = models.DateField(blank=True, null=True)
    date_rig_released = models.DateField(blank=True, null=True)
    date_well_spudded = models.DateField(blank=True, null=True)
    drilling_contractor = models.TextField(blank=True, null=True)
    drilling_rig_number = models.TextField(blank=True, null=True)
    md_all_wells_m = models.FloatField(blank=True, null=True)
    md_deviated_wells_m = models.FloatField(blank=True, null=True)
    tvd_m = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "well_drilling"
        ordering = ["base_uwi", "-suffix", "-raw_id"]

    def __str__(self):
        return f"{self.base_uwi_id} drilling"
