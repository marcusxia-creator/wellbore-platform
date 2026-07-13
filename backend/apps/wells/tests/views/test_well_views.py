"""Integration tests for the wells API endpoints."""

import pytest
from rest_framework.test import APIClient

from apps.wells.tests.factories import (
    WellHeaderFactory,
    WellProductionFormationFactory,
    WellStatusCategoryFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


class TestWellListEndpoint:
    def test_list_returns_wells(self, client):
        WellHeaderFactory.create_batch(2)
        response = client.get("/api/wells/")
        assert response.status_code == 200
        assert response.data["count"] == 2

    def test_list_filters_by_well_type(self, client):
        WellHeaderFactory(base_uwi="OIL-1", well_type="OIL")
        WellHeaderFactory(base_uwi="GAS-1", well_type="GAS")
        response = client.get("/api/wells/", {"well_type": "OIL"})
        assert response.data["count"] == 1
        assert response.data["results"][0]["uwi"] == "OIL-1"

    def test_detail_returns_single_well(self, client):
        WellHeaderFactory(base_uwi="DET-1", well_name="Detail Well")
        response = client.get("/api/wells/DET-1/")
        assert response.status_code == 200
        assert response.data["uwi"] == "DET-1"
        assert response.data["name"] == "Detail Well"
        assert response.data["province_state"] == "Alberta"

    def test_detail_404_for_missing_well(self, client):
        response = client.get("/api/wells/NOPE/")
        assert response.status_code == 404


class TestMetadataEndpoints:
    def test_well_statuses(self, client):
        response = client.get("/api/well-statuses/")
        assert response.status_code == 200
        values = [item["value"] for item in response.data]
        assert values == ["ABD", "Suspended", "Inactive", "Active"]

    def test_well_types(self, client):
        WellHeaderFactory(well_type="OIL")
        WellHeaderFactory(well_type="GAS")
        response = client.get("/api/well-types/")
        values = {item["value"] for item in response.data}
        assert values == {"OIL", "GAS"}

    def test_actual_well_statuses(self, client):
        WellStatusCategoryFactory(base_uwi="A-1", actual_status_text="Flowing")
        WellStatusCategoryFactory(base_uwi="A-2", actual_status_text="Injecting")
        response = client.get("/api/actual-well-statuses/")
        values = {item["value"] for item in response.data}
        assert values == {"Flowing", "Injecting"}

    def test_production_injection_formations(self, client):
        WellProductionFormationFactory(base_uwi="A-1", formation="Cardium")
        WellProductionFormationFactory(base_uwi="A-2", formation="Viking")
        response = client.get("/api/production-injection-formations/")
        values = {item["value"] for item in response.data}
        assert values == {"Cardium", "Viking"}
