"""Per-well training label for the single-well WellStor model.

One row per well per training set, holding the supervised target (whether the
well is a good storage candidate) used to train and retrain the single-well
model. Sourced from the curated training dataset.

Linked to `wells.WellHeader` logically via `base_uwi` (no database foreign key,
matching the wells cache-table convention).
"""

from django.db import models


class WellTrainingLabel(models.Model):
    base_uwi = models.TextField(db_index=True)  # logical link to WellHeader.base_uwi
    label = models.IntegerField(blank=True, null=True)  # supervised target (e.g. 0 / 1)

    source_file = models.TextField(blank=True, null=True)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "well_training_label"

    def __str__(self):
        return f"{self.base_uwi} label={self.label}"
