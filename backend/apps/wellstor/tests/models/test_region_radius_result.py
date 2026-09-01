"""Integration tests for the RegionRadiusResult model."""

import pytest

from apps.wellstor.models import RegionRadiusResult
from apps.wellstor.tests.factories import RegionRadiusResultFactory, SubstationFactory

pytestmark = pytest.mark.django_db


class TestRegionRadiusResult:
    def test_create_and_fetch(self):
        result = RegionRadiusResultFactory()
        assert RegionRadiusResult.objects.get(pk=result.pk).pk == result.pk

    def test_multiple_radii_per_substation(self):
        substation = SubstationFactory()
        RegionRadiusResultFactory(substation=substation, radius_m=5000.0)
        RegionRadiusResultFactory(substation=substation, radius_m=10000.0)
        assert substation.region_radius_results.count() == 2

    def test_str(self):
        result = RegionRadiusResultFactory(radius_m=7500.0)
        assert str(result) == f"{result.substation_id} @ 7500.0m"
