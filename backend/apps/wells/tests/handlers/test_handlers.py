"""Integration tests for the wells orchestration layer (handlers)."""

import pytest
from django.http import QueryDict

from apps.wells.handlers import MetadataHandler, WellHandler
from apps.wells.tests.factories import (
    WellHeaderFactory,
    WellProductionFormationFactory,
    WellStatusCategoryFactory,
)

pytestmark = pytest.mark.django_db


def make_params(**kwargs):
    params = QueryDict(mutable=True)
    for key, value in kwargs.items():
        if isinstance(value, list):
            params.setlist(key, value)
        else:
            params[key] = value
    return params


class TestWellHandler:
    def test_list_wells_no_filters(self):
        WellHeaderFactory.create_batch(2)
        result = WellHandler.list_wells(make_params())
        assert result.count() == 2

    def test_list_wells_applies_filters(self):
        WellHeaderFactory(base_uwi="OIL-1", well_type="OIL")
        WellHeaderFactory(base_uwi="GAS-1", well_type="GAS")
        result = WellHandler.list_wells(make_params(well_type="OIL"))
        assert [w.base_uwi for w in result] == ["OIL-1"]

    def test_list_wells_multi_formation_param(self):
        WellHeaderFactory(base_uwi="F-1")
        WellHeaderFactory(base_uwi="F-2")
        WellProductionFormationFactory(base_uwi="F-1", formation="Cardium")
        WellProductionFormationFactory(base_uwi="F-2", formation="Viking")
        result = WellHandler.list_wells(make_params(prod_inject_frmtn=["Cardium", "Viking"]))
        assert {w.base_uwi for w in result} == {"F-1", "F-2"}


class TestMetadataHandler:
    def test_well_statuses_shape(self):
        result = MetadataHandler.well_statuses()
        assert result == [
            {"value": "ABD", "label": "ABD"},
            {"value": "Suspended", "label": "Suspended"},
            {"value": "Inactive", "label": "Inactive"},
            {"value": "Active", "label": "Active"},
        ]

    def test_well_types_shape(self):
        WellHeaderFactory(well_type="OIL")
        result = MetadataHandler.well_types()
        assert {"value": "OIL", "label": "OIL"} in result

    def test_actual_well_statuses_filtered(self):
        WellStatusCategoryFactory(base_uwi="A-1", status_category="Active", actual_status_text="Flowing")
        WellStatusCategoryFactory(base_uwi="A-2", status_category="ABD", actual_status_text="Abandoned")
        result = MetadataHandler.actual_well_statuses("Active")
        assert result == [{"value": "Flowing", "label": "Flowing"}]
