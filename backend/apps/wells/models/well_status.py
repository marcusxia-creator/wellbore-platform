from django.db import models

from .well_header import WellHeader


class WellStatus(models.Model):
    raw_id = models.BigIntegerField(primary_key=True)
    base_uwi = models.ForeignKey(
        WellHeader,
        models.DO_NOTHING,
        db_column="base_uwi",
        to_field="base_uwi",
        related_name="statuses",
        db_constraint=False,
        blank=True,
        null=True,
    )
    import_timestamp = models.TextField(blank=True, null=True)
    source_file = models.TextField(blank=True, null=True)
    suffix = models.TextField(blank=True, null=True)
    user_format_well_id = models.TextField(blank=True, null=True)
    inactive_well = models.BooleanField(blank=True, null=True)
    shut_in_well = models.BooleanField(blank=True, null=True)
    well_status_abrv = models.TextField(blank=True, null=True)
    well_status_text = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "well_status"
        ordering = ["base_uwi", "-suffix", "-raw_id"]

    def __str__(self):
        return f"{self.base_uwi_id} status"
