"""Integration tests for the RegionPrediction model."""

import pytest

from apps.wellstor.models import RegionPrediction
from apps.wellstor.tests.factories import RegionPredictionFactory, SubstationFactory

pytestmark = pytest.mark.django_db


class TestRegionPrediction:
    def test_create_and_fetch(self):
        prediction = RegionPredictionFactory()
        assert RegionPrediction.objects.get(pk=prediction.pk).pk == prediction.pk

    def test_links_to_substation(self):
        substation = SubstationFactory(facility_code="SUB-1")
        prediction = RegionPredictionFactory(substation=substation)
        assert prediction.substation == substation
        assert substation.region_predictions.count() == 1

    def test_cascade_delete_with_substation(self):
        substation = SubstationFactory()
        RegionPredictionFactory(substation=substation)
        substation.delete()
        assert RegionPrediction.objects.count() == 0

    def test_str(self):
        prediction = RegionPredictionFactory()
        assert str(prediction) == f"{prediction.substation_id} region prediction"
