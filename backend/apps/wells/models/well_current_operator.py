from django.db import models


class WellCurrentOperator(models.Model):
    """Cache table: one row per base_uwi storing the most-recent operator name.

    Populated by `writes.refresh_well_current_operators()` (called from the
    management command of the same name). Never mutated at request time.
    """

    base_uwi = models.TextField(primary_key=True)
    operator_name = models.TextField(db_index=True)
    suffix = models.TextField(blank=True, null=True)
    raw_id = models.BigIntegerField(blank=True, null=True)
    refreshed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "well_current_operator"
        indexes = [
            models.Index(
                fields=["operator_name", "base_uwi"],
                name="wells_well__operato_9176c2_idx",
            ),
        ]

    def __str__(self):
        return f"{self.base_uwi} {self.operator_name}"
