from django.urls import path
from rest_framework.routers import DefaultRouter

from .views.metadata_view import (
    actual_well_statuses,
    production_injection_formations,
    well_statuses,
    well_types,
)
from .views.well_view import WellViewSet

router = DefaultRouter()
router.register("wells", WellViewSet, basename="well")

urlpatterns = router.urls + [
    path("well-statuses/", well_statuses, name="well-statuses"),
    path("actual-well-statuses/", actual_well_statuses, name="actual-well-statuses"),
    path("well-types/", well_types, name="well-types"),
    path(
        "production-injection-formations/",
        production_injection_formations,
        name="production-injection-formations",
    ),
]
