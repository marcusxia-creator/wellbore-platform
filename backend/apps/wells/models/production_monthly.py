from django.db import models


class ProductionMonthly(models.Model):
    """Unmanaged read model for the production_monthly table.

    This table is created and populated by the data-import pipeline
    (apps.data_imports). It does not exist on a fresh deployment; callers
    guard with `_table_exists("production_monthly")` in queries.py before
    issuing any queries against it.

    managed = False: Django will never CREATE / DROP this table; migrations
    only register the model so the ORM can reference it.
    """

    base_uwi = models.TextField(db_index=True)
    production_month = models.DateField()
    monthly_oil = models.FloatField(blank=True, null=True)
    monthly_water = models.FloatField(blank=True, null=True)
    monthly_gas = models.FloatField(blank=True, null=True)
    monthly_fluid = models.FloatField(blank=True, null=True)
    cumulative_oil = models.FloatField(blank=True, null=True)
    cumulative_water = models.FloatField(blank=True, null=True)
    cumulative_gas = models.FloatField(blank=True, null=True)
    cumulative_fluid = models.FloatField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "production_monthly"
        ordering = ["base_uwi", "-production_month"]

    def __str__(self):
        return f"{self.base_uwi} {self.production_month}"
