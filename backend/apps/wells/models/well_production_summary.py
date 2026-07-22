from django.db import models

from .well_header import WellHeader


class WellProductionSummary(models.Model):
    raw_id = models.BigIntegerField(primary_key=True)
    base_uwi = models.ForeignKey(
        WellHeader,
        models.DO_NOTHING,
        db_column="base_uwi",
        to_field="base_uwi",
        related_name="production_summaries",
        db_constraint=False,
        blank=True,
        null=True,
    )
    import_timestamp = models.TextField(blank=True, null=True)
    source_file = models.TextField(blank=True, null=True)
    suffix = models.TextField(blank=True, null=True)
    user_format_well_id = models.TextField(blank=True, null=True)
    prod_status_abrv = models.TextField(blank=True, null=True)
    prod_status_text = models.TextField(blank=True, null=True)
    prod_inject_frmtn = models.TextField(blank=True, null=True)
    on_inject_yyyy_mm_dd = models.DateField(blank=True, null=True)
    on_prod_yyyy_mm_dd = models.DateField(blank=True, null=True)
    first_inject_yyyy_mm = models.TextField(blank=True, null=True)
    first_prod_yyyy_mm = models.TextField(blank=True, null=True)
    last_inject_yyyy_mm = models.TextField(blank=True, null=True)
    last_prod_yyyy_mm = models.TextField(blank=True, null=True)
    most_recent_12_mo_total_gas_e3m3 = models.FloatField(blank=True, null=True)
    most_recent_12_mo_total_oil_m3 = models.FloatField(blank=True, null=True)
    most_recent_12_mo_total_wtr_m3 = models.FloatField(blank=True, null=True)
    total_production_hrs = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "well_production_summary"
        ordering = ["base_uwi", "-suffix", "-raw_id"]

    def __str__(self):
        return f"{self.base_uwi_id} production summary"
