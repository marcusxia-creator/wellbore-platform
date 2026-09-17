from django.db import models


class InjectionMonthly(models.Model):
    """Django-managed model for the injection_monthly table.

    The table is created by Django migrations (managed=True). Monthly rows
    are aggregated from injection_daily by the data-import pipeline or
    writes functions. The cumulative_* columns are running totals computed
    with SQL window functions (SUM OVER PARTITION BY base_uwi ORDER BY
    injection_month).

    Schema (created by ensure_injection_tables in data_imports/services.py):
        base_uwi          text NOT NULL
        injection_month   date NOT NULL
        monthly_water     double precision NOT NULL DEFAULT 0
        monthly_gas       double precision NOT NULL DEFAULT 0
        monthly_steam     double precision NOT NULL DEFAULT 0
        cumulative_water  double precision NOT NULL DEFAULT 0
        cumulative_gas    double precision NOT NULL DEFAULT 0
        cumulative_steam  double precision NOT NULL DEFAULT 0
        updated_at        timestamptz NOT NULL DEFAULT now()
        UNIQUE (base_uwi, injection_month)
    """

    base_uwi = models.TextField(db_index=True)
    injection_month = models.DateField()
    monthly_water = models.FloatField(default=0)
    monthly_gas = models.FloatField(default=0)
    monthly_steam = models.FloatField(default=0)
    cumulative_water = models.FloatField(default=0)
    cumulative_gas = models.FloatField(default=0)
    cumulative_steam = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "injection_monthly"
        ordering = ["base_uwi", "-injection_month"]
        unique_together = [("base_uwi", "injection_month")]

    def __str__(self) -> str:
        return f"{self.base_uwi} {self.injection_month}"
