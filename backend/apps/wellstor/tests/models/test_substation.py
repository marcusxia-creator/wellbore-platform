"""Integration tests for the Substation model."""

import pytest
from django.db import IntegrityError, transaction

from apps.wellstor.models import Substation
from apps.wellstor.tests.factories import SubstationFactory

pytestmark = pytest.mark.django_db


class TestSubstation:
    def test_create_and_fetch(self):
        substation = SubstationFactory(facility_code="SUB-1")
        assert Substation.objects.get(facility_code="SUB-1").pk == substation.pk

    def test_facility_code_is_unique(self):
        SubstationFactory(facility_code="DUP-1")
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                SubstationFactory(facility_code="DUP-1")

    def test_str(self):
        substation = SubstationFactory(facility_code="SUB-9", facility_name="North Yard")
        assert str(substation) == "SUB-9 - North Yard"
