"""Substation (electrical facility) master record.

Anchors the region-level WellStor analysis: region models score the wells within
a radius of each substation. Sourced from the substation name/location dataset
(facility code, name, land location, coordinates, capacity).
"""

from django.db import models


class Substation(models.Model):
    facility_code = models.TextField(unique=True, db_index=True)
    facility_name = models.TextField(blank=True, null=True)
    land_location = models.TextField(blank=True, null=True)
    township = models.SmallIntegerField(blank=True, null=True)
    range = models.SmallIntegerField(blank=True, null=True)
    meridian = models.SmallIntegerField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    capacity_mw = models.FloatField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "substation"
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        return f"{self.facility_code} - {self.facility_name or ''}".strip()
