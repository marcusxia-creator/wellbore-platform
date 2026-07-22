from django.db import models


class WellStatusCategory(models.Model):
    base_uwi = models.TextField(primary_key=True)
    status_category = models.CharField(max_length=32, db_index=True)
    actual_status_text = models.TextField(blank=True, null=True, db_index=True)
    last_production_date = models.DateField(blank=True, null=True)
    last_injection_date = models.DateField(blank=True, null=True)
    refreshed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "well_status_category"
        indexes = [
            models.Index(fields=["status_category", "actual_status_text"]),
        ]

    def __str__(self):
        return f"{self.base_uwi} {self.status_category}"
