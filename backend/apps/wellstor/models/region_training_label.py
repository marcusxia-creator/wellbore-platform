"""Per-region training label for the region WellStor model.

One row per substation per candidate radius, holding the supervised target
(whether the region is suitable) plus the aggregate features used to train and
retrain the region model. Sourced from the curated region training dataset.
"""

from django.db import models


class RegionTrainingLabel(models.Model):
    substation = models.ForeignKey(
        "wellstor.Substation",
        on_delete=models.CASCADE,
        related_name="region_training_labels",
    )
    radius_m = models.FloatField(blank=True, null=True)

    well_counts = models.IntegerField(blank=True, null=True)
    good_count = models.IntegerField(blank=True, null=True)
    total_volume = models.FloatField(blank=True, null=True)
    total_airmass = models.FloatField(blank=True, null=True)
    average_distance = models.FloatField(blank=True, null=True)
    max_pressure = models.FloatField(blank=True, null=True)
    min_pressure = models.FloatField(blank=True, null=True)
    middle_pressure = models.FloatField(blank=True, null=True)

    region_label = models.IntegerField(blank=True, null=True)  # supervised target
    suitable_radius_m = models.FloatField(blank=True, null=True)

    source_file = models.TextField(blank=True, null=True)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "region_training_label"
        indexes = [
            models.Index(fields=["substation", "radius_m"]),
        ]

    def __str__(self):
        return f"{self.substation_id} @ {self.radius_m}m label={self.region_label}"
