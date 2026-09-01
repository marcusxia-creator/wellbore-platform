"""Single-well WellStor model output.

One row per well per model run, holding the candidate-selection score for a well
and the nearest substation used for that scoring. Sourced from the single-well
prediction output of the WellStor selection model.

Linked to the read-only `wells.WellHeader` logically via `base_uwi` (no database
foreign key, matching the wells cache-table convention). The nearest substation
is a real foreign key because Substation is a managed table owned by this app.
"""

from django.db import models


class WellStorPrediction(models.Model):
    base_uwi = models.TextField(db_index=True)  # logical link to WellHeader.base_uwi
    nearest_substation = models.ForeignKey(
        "wellstor.Substation",
        on_delete=models.SET_NULL,
        related_name="well_predictions",
        blank=True,
        null=True,
    )

    distance_m = models.FloatField(blank=True, null=True)  # well to nearest substation
    airmass = models.FloatField(blank=True, null=True)
    good_probability = models.FloatField(blank=True, null=True)  # model score in [0, 1]
    wellstore_candidate = models.BooleanField(blank=True, null=True)  # final label

    # run metadata
    radius_m = models.FloatField(blank=True, null=True)
    model_version = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wellstor_prediction"
        indexes = [
            models.Index(fields=["base_uwi", "radius_m"]),
        ]

    def __str__(self):
        return f"{self.base_uwi} prediction"
