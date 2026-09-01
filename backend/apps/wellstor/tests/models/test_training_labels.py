"""Integration tests for the training label and model metadata models."""

import pytest

from apps.wellstor.models import ModelFeatureWeight, RegionTrainingLabel, WellTrainingLabel
from apps.wellstor.tests.factories import (
    ModelFeatureWeightFactory,
    RegionTrainingLabelFactory,
    SubstationFactory,
    WellTrainingLabelFactory,
)

pytestmark = pytest.mark.django_db


class TestWellTrainingLabel:
    def test_create_and_fetch(self):
        label = WellTrainingLabelFactory(base_uwi="UWI-1", label=1)
        stored = WellTrainingLabel.objects.get(pk=label.pk)
        assert stored.base_uwi == "UWI-1"
        assert stored.label == 1

    def test_str(self):
        label = WellTrainingLabelFactory(base_uwi="UWI-X", label=0)
        assert str(label) == "UWI-X label=0"


class TestRegionTrainingLabel:
    def test_links_to_substation(self):
        substation = SubstationFactory(facility_code="SUB-1")
        label = RegionTrainingLabelFactory(substation=substation)
        assert substation.region_training_labels.count() == 1
        assert label.substation == substation

    def test_cascade_delete_with_substation(self):
        substation = SubstationFactory()
        RegionTrainingLabelFactory(substation=substation)
        substation.delete()
        assert RegionTrainingLabel.objects.count() == 0


class TestModelFeatureWeight:
    def test_create_and_fetch(self):
        weight = ModelFeatureWeightFactory(model_name="region_selection", feature="airmass", weight=1.5)
        stored = ModelFeatureWeight.objects.get(pk=weight.pk)
        assert stored.model_name == "region_selection"
        assert stored.feature == "airmass"
        assert stored.weight == 1.5
