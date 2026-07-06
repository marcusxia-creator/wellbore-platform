from django.db import models


class WellProductionFormation(models.Model):
    base_uwi = models.TextField(db_index=True)
    formation = models.TextField(db_index=True)
    source_value = models.TextField(blank=True, null=True)
    suffix = models.TextField(blank=True, null=True)
    refreshed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "well_production_formation"
        unique_together = ["base_uwi", "formation"]
        indexes = [
            models.Index(fields=["formation", "base_uwi"]),
        ]

    def __str__(self):
        return f"{self.base_uwi} {self.formation}"
