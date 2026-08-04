"""Enumerations for WellStor machine-learning features.

Integer values mirror the encoding used by the upstream processed-data pipeline
so persisted feature values stay consistent with the source datasets.
"""

from django.db import models


class PerforationType(models.IntegerChoices):
    """Perforation / completion type of a well."""

    UNDEFINED = 0, "Undefined"
    TREAT = 1, "Treat"
    PERF = 2, "Perf"
    FRAC = 3, "Frac"
    OPENHOLE = 4, "Openhole"
    PLUG = 5, "Plug"
    LINER = 6, "Liner"


class DeepestCasingType(models.IntegerChoices):
    """Type of the deepest casing string recorded for a well."""

    UNKNOWN = 0, "Unknown"
    INTERMEDIATE = 1, "Intermediate"
    PRODUCTION = 2, "Production"
    LINER = 3, "Liner"
    SURFACE = 4, "Surface"
    CONDUCTOR = 5, "Conductor"
