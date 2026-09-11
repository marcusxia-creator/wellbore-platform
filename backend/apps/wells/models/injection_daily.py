from django.db import models


class InjectionDaily(models.Model):
    """Django-managed model for the injection_daily table.

    The table is created by Django migrations (managed=True). Rows are
    populated by the data-import pipeline or direct SQL inserts in writes.py.

    Schema (created by ensure_injection_tables in data_imports/services.py):
        base_uwi          text NOT NULL
        injection_date    date NOT NULL
        daily_water       double precision NOT NULL DEFAULT 0
        daily_gas         double precision NOT NULL DEFAULT 0
        daily_steam       double precision NOT NULL DEFAULT 0
        injection_pressure double precision NOT NULL DEFAULT 0
        source_file       text
        imported_at       timestamptz NOT NULL DEFAULT now()
        UNIQUE (base_uwi, injection_date)
    """

    base_uwi = models.TextField(db_index=True)
    injection_date = models.DateField()
    daily_water = models.FloatField(default=0)
    daily_gas = models.FloatField(default=0)
    daily_steam = models.FloatField(default=0)
    injection_pressure = models.FloatField(default=0)
    source_file = models.TextField(blank=True, null=True)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "injection_daily"
        ordering = ["base_uwi", "injection_date"]
        unique_together = [("base_uwi", "injection_date")]

    def __str__(self) -> str:
        return f"{self.base_uwi} {self.injection_date}"
