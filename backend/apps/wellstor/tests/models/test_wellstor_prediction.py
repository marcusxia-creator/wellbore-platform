"""Integration tests for the WellStorPrediction model."""

import pytest

from apps.wellstor.models import WellStorPrediction
from apps.wellstor.tests.factories import SubstationFactory, WellStorPredictionFactory

pytestmark = pytest.mark.django_db


class TestWellStorPrediction:
    def test_create_and_fetch(self):
        prediction = WellStorPredictionFactory(base_uwi="UWI-1")
        assert WellStorPrediction.objects.get(pk=prediction.pk).base_uwi == "UWI-1"

    def test_links_to_nearest_substation(self):
        substation = SubstationFactory(facility_code="SUB-1")
        prediction = WellStorPredictionFactory(nearest_substation=substation)
        assert prediction.nearest_substation == substation
        assert substation.well_predictions.count() == 1

    def test_allows_multiple_predictions_per_well(self):
        WellStorPredictionFactory(base_uwi="UWI-2", radius_m=5000.0)
        WellStorPredictionFactory(base_uwi="UWI-2", radius_m=10000.0)
        assert WellStorPrediction.objects.filter(base_uwi="UWI-2").count() == 2

    def test_str(self):
        prediction = WellStorPredictionFactory(base_uwi="UWI-X")
        assert str(prediction) == "UWI-X prediction"
