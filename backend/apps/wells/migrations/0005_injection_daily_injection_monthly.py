from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wells", "0004_well_current_operator_production_monthly"),
    ]

    operations = [
        # InjectionDaily: Django-managed table. Using managed=True so that
        # `migrate` creates the table on fresh deployments. Rows are populated
        # by the data-import pipeline or direct SQL inserts.
        migrations.CreateModel(
            name="InjectionDaily",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("base_uwi", models.TextField(db_index=True)),
                ("injection_date", models.DateField()),
                ("daily_water", models.FloatField(default=0)),
                ("daily_gas", models.FloatField(default=0)),
                ("daily_steam", models.FloatField(default=0)),
                ("injection_pressure", models.FloatField(default=0)),
                ("source_file", models.TextField(blank=True, null=True)),
                ("imported_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "injection_daily",
                "ordering": ["base_uwi", "injection_date"],
                "unique_together": {("base_uwi", "injection_date")},
            },
        ),
        # InjectionMonthly: Django-managed table. Monthly rows are aggregated
        # from injection_daily by the import pipeline or writes functions.
        # Using managed=True so `migrate` creates the table automatically.
        migrations.CreateModel(
            name="InjectionMonthly",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("base_uwi", models.TextField(db_index=True)),
                ("injection_month", models.DateField()),
                ("monthly_water", models.FloatField(default=0)),
                ("monthly_gas", models.FloatField(default=0)),
                ("monthly_steam", models.FloatField(default=0)),
                ("cumulative_water", models.FloatField(default=0)),
                ("cumulative_gas", models.FloatField(default=0)),
                ("cumulative_steam", models.FloatField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "injection_monthly",
                "ordering": ["base_uwi", "-injection_month"],
                "unique_together": {("base_uwi", "injection_month")},
            },
        ),
    ]
