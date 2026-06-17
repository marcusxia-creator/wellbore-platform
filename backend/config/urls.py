from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.wells.views import (
    WellViewSet,
    actual_well_statuses,
    production_injection_formations,
    well_statuses,
    well_types,
)

router = DefaultRouter()
router.register("wells", WellViewSet, basename="well")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/well-statuses/", well_statuses, name="well-statuses"),
    path("api/actual-well-statuses/", actual_well_statuses, name="actual-well-statuses"),
    path("api/well-types/", well_types, name="well-types"),
    path("api/production-injection-formations/", production_injection_formations, name="production-injection-formations"),
]
