from django.db import models


class WellHeader(models.Model):
    base_uwi = models.TextField(primary_key=True)
    import_timestamp = models.TextField(blank=True, null=True)
    raw_id = models.BigIntegerField(blank=True, null=True)
    source_file = models.TextField(blank=True, null=True)
    suffix = models.TextField(blank=True, null=True)
    user_format_well_id = models.TextField(blank=True, null=True)
    area = models.TextField(blank=True, null=True)
    cur_operator_code = models.TextField(blank=True, null=True)
    cur_operator_name = models.TextField(blank=True, null=True)
    lahee_class_code = models.TextField(blank=True, null=True)
    lic_subs_well_obj = models.TextField(blank=True, null=True)
    lic_wa_wid_permit = models.TextField(blank=True, null=True)
    org_operator_name = models.TextField(blank=True, null=True)
    orig_operator_code = models.TextField(blank=True, null=True)
    orig_units_m_api = models.TextField(blank=True, null=True)
    well_name = models.TextField(blank=True, null=True)
    well_pad_id = models.TextField(blank=True, null=True)
    well_type = models.TextField(blank=True, null=True)
    permit_id = models.TextField(db_column="Permit_id", blank=True, null=True)

    class Meta:
        managed = False
        db_table = "well_header"
        ordering = ["base_uwi", "-suffix", "-raw_id"]

    def __str__(self):
        return f"{self.base_uwi} - {self.well_name or self.user_format_well_id or ''}".strip()


Well = WellHeader
