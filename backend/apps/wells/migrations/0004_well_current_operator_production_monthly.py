from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wells", "0003_well_production_formation"),
    ]

    operations = [
        # WellCurrentOperator: Django-managed cache table (written by
        # writes.refresh_well_current_operators).
        migrations.CreateModel(
            name="WellCurrentOperator",
            fields=[
                ("base_uwi", models.TextField(primary_key=True, serialize=False)),
                ("operator_name", models.TextField(db_index=True)),
                ("suffix", models.TextField(blank=True, null=True)),
                ("raw_id", models.BigIntegerField(blank=True, null=True)),
                ("refreshed_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "well_current_operator",
                "indexes": [
                    models.Index(
                        fields=["operator_name", "base_uwi"],
                        name="wells_well__operato_9176c2_idx",
                    ),
                ],
            },
        ),
        # ProductionMonthly: unmanaged (managed=False) — Django registers the
        # model for ORM access but never creates or drops the table itself.
        # The table is owned by the data-import pipeline (apps.data_imports).
        migrations.CreateModel(
            name="ProductionMonthly",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("base_uwi", models.TextField(db_index=True)),
                ("production_month", models.DateField()),
                ("monthly_oil", models.FloatField(blank=True, null=True)),
                ("monthly_water", models.FloatField(blank=True, null=True)),
                ("monthly_gas", models.FloatField(blank=True, null=True)),
                ("monthly_fluid", models.FloatField(blank=True, null=True)),
                ("cumulative_oil", models.FloatField(blank=True, null=True)),
                ("cumulative_water", models.FloatField(blank=True, null=True)),
                ("cumulative_gas", models.FloatField(blank=True, null=True)),
                ("cumulative_fluid", models.FloatField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "production_monthly",
                "ordering": ["base_uwi", "-production_month"],
                "managed": False,
            },
        ),
    ]
