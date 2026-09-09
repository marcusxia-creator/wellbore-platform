from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wells", "0004_well_current_operator_production_monthly"),
    ]

    operations = [
        # InjectionDaily: unmanaged (managed=False) — Django registers the
        # model for ORM access but never creates or drops the table.
        # The table is owned by the data-import pipeline (apps.data_imports).
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
                "managed": False,
            },
        ),
        # InjectionMonthly: unmanaged (managed=False) — same ownership rules
        # as InjectionDaily. Monthly rows are aggregated by the import pipeline
        # using SQL window functions.
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
                "managed": False,
            },
        ),
    ]
