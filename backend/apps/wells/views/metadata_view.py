from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.wells.handlers import MetadataHandler


@api_view(["GET"])
def well_statuses(request):
    return Response(MetadataHandler.well_statuses())


@api_view(["GET"])
def actual_well_statuses(request):
    category = request.query_params.get("status")
    return Response(MetadataHandler.actual_well_statuses(category))


@api_view(["GET"])
def well_types(request):
    return Response(MetadataHandler.well_types())


@api_view(["GET"])
def production_injection_formations(request):
    return Response(MetadataHandler.production_injection_formations())
