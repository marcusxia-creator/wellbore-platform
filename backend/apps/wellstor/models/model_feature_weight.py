"""Feature weight metadata for a trained WellStor model.

One row per model / version / feature, storing the learned weight so a training
run's feature importances are inspectable without loading the model artifact.
"""

from django.db import models


class ModelFeatureWeight(models.Model):
    model_name = models.TextField()  # e.g. "well_selection", "region_selection"
    model_version = models.TextField()
    feature = models.TextField()
    weight = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "model_feature_weight"
        indexes = [
            models.Index(fields=["model_name", "model_version"]),
        ]

    def __str__(self):
        return f"{self.model_name}/{self.model_version} {self.feature}={self.weight}"
