"""Per-radius region sweep result (per substation and radius).

One row per substation per candidate radius, holding the aggregate metrics used
to pick each substation's suitable radius. Sourced from the all-radius output of
the region model.
"""

from django.db import models


class RegionRadiusResult(models.Model):
    substation = models.ForeignKey(
        "wellstor.Substation",
        on_delete=models.CASCADE,
        related_name="region_radius_results",
    )
    radius_m = models.FloatField(blank=True, null=True)

    average_distance = models.FloatField(blank=True, null=True)
    well_count = models.IntegerField(blank=True, null=True)
    good_count = models.IntegerField(blank=True, null=True)
    total_volume = models.FloatField(blank=True, null=True)
    total_airmass = models.FloatField(blank=True, null=True)
    max_pressure = models.FloatField(blank=True, null=True)
    min_pressure = models.FloatField(blank=True, null=True)
    middle_pressure = models.FloatField(blank=True, null=True)

    suitable_probability = models.FloatField(blank=True, null=True)
    substation_candidate = models.BooleanField(blank=True, null=True)
    prediction_source = models.TextField(blank=True, null=True)
    prediction_reason = models.TextField(blank=True, null=True)

    model_version = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "region_radius_result"
        indexes = [
            models.Index(fields=["substation", "radius_m"]),
        ]

    def __str__(self):
        return f"{self.substation_id} @ {self.radius_m}m"
