from django.db import models

from .well_header import WellHeader


class WellLocation(models.Model):
    raw_id = models.BigIntegerField(primary_key=True)
    base_uwi = models.ForeignKey(
        WellHeader,
        models.DO_NOTHING,
        db_column="base_uwi",
        to_field="base_uwi",
        related_name="locations",
        db_constraint=False,
        blank=True,
        null=True,
    )
    import_timestamp = models.TextField(blank=True, null=True)
    source_file = models.TextField(blank=True, null=True)
    suffix = models.TextField(blank=True, null=True)
    user_format_well_id = models.TextField(blank=True, null=True)
    bot_hole_latitude_nad83 = models.TextField(blank=True, null=True)
    bot_hole_longitude_nad83 = models.TextField(blank=True, null=True)
    govt_surf_loc = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    surf_hole_latitude_nad83 = models.TextField(blank=True, null=True)
    surf_hole_longitude_nad83 = models.TextField(blank=True, null=True)
    surf_loc = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "well_location"
        ordering = ["base_uwi", "-suffix", "-raw_id"]

    def __str__(self):
        return f"{self.base_uwi_id} location"
