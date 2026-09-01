"""Integration tests for the WellFeature model.

These hit a real PostgreSQL test database (the model is stored in a managed
table with a unique constraint on base_uwi).
"""

import pytest
from django.db import IntegrityError, transaction

from apps.wellstor.enums import DeepestCasingType, PerforationType
from apps.wellstor.models import WellFeature
from apps.wellstor.tests.factories import WellFeatureFactory

pytestmark = pytest.mark.django_db


class TestWellFeature:
    def test_create_and_fetch(self):
        feature = WellFeatureFactory(base_uwi="UWI-1")
        assert WellFeature.objects.get(base_uwi="UWI-1").pk == feature.pk

    def test_base_uwi_is_unique(self):
        WellFeatureFactory(base_uwi="DUP-1")
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                WellFeatureFactory(base_uwi="DUP-1")

    def test_enum_fields_store_integer_values(self):
        feature = WellFeatureFactory(
            perforation_type=PerforationType.FRAC,
            deepest_casing_type=DeepestCasingType.SURFACE,
        )
        feature.refresh_from_db()
        assert feature.perforation_type == 3
        assert feature.deepest_casing_type == 4

    def test_str(self):
        feature = WellFeatureFactory(base_uwi="UWI-X")
        assert str(feature) == "UWI-X feature"

    def test_preprocessing_fields_persist(self):
        feature = WellFeatureFactory(
            base_uwi="UWI-P",
            uwi_suffix="00",
            nts_prefix="A",
            nts_area="93",
            nts_sheet="A",
            deepest_casing_id=159.4,
            liner_start_m=1200.0,
            liner_end_m=1800.0,
            wellstor_flag=True,
        )
        stored = WellFeature.objects.get(base_uwi="UWI-P")
        assert stored.uwi_suffix == "00"
        assert stored.nts_prefix == "A"
        assert stored.nts_area == "93"
        assert stored.nts_sheet == "A"
        assert stored.deepest_casing_id == 159.4
        assert stored.liner_start_m == 1200.0
        assert stored.liner_end_m == 1800.0
        assert stored.wellstor_flag is True
