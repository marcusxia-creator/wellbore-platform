"""Region-level WellStor model output (per substation).

One row per substation per model run, holding the region suitability score and
the aggregate metrics of the wells around the substation at its selected radius.
Sourced from the region prediction output of the WellStor selection model.
"""

from django.db import models


class RegionPrediction(models.Model):
    substation = models.ForeignKey(
        "wellstor.Substation",
        on_delete=models.CASCADE,
        related_name="region_predictions",
    )

    substation_candidate = models.BooleanField(blank=True, null=True)  # final region label
    suitable_probability = models.FloatField(blank=True, null=True)  # model score in [0, 1]

    min_suitable_radius_m = models.FloatField(blank=True, null=True)
    suitable_radius = models.FloatField(blank=True, null=True)

    # aggregates over the wells within the selected radius
    average_distance = models.FloatField(blank=True, null=True)
    well_count = models.IntegerField(blank=True, null=True)
    good_count = models.IntegerField(blank=True, null=True)
    total_volume = models.FloatField(blank=True, null=True)
    total_airmass = models.FloatField(blank=True, null=True)
    baseline_air_mass = models.FloatField(blank=True, null=True)
    usable_air_mass = models.FloatField(blank=True, null=True)
    energy_storage_mwh = models.FloatField(blank=True, null=True)
    max_pressure = models.FloatField(blank=True, null=True)
    min_pressure = models.FloatField(blank=True, null=True)
    middle_pressure = models.FloatField(blank=True, null=True)

    model_version = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "region_prediction"

    def __str__(self):
        return f"{self.substation_id} region prediction"
