from django.db.models import OuterRef, Q, Subquery
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import WellHeader, WellProductionFormation, WellStatusCategory
from .serializers import WellSerializer
from .status_rules import STATUS_CATEGORIES


class FastPageNumberPagination(PageNumberPagination):
    page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        page_number = request.query_params.get(self.page_query_param, 1)
        try:
            page_number = max(int(page_number), 1)
        except (TypeError, ValueError):
            page_number = 1

        offset = (page_number - 1) * page_size
        self.count = queryset.count()
        rows = list(queryset[offset : offset + page_size + 1])
        self.has_next = len(rows) > page_size
        self.page_number = page_number
        return rows[:page_size]

    def get_paginated_response(self, data):
        next_page = self.page_number + 1 if self.has_next else None
        return Response(
            {
                "count": self.count,
                "next": next_page,
                "previous": self.page_number - 1 if self.page_number > 1 else None,
                "results": data,
            }
        )


class WellViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WellSerializer
    lookup_field = "base_uwi"
    pagination_class = FastPageNumberPagination

    def get_queryset(self):
        status_category = WellStatusCategory.objects.filter(base_uwi=OuterRef("base_uwi"))
        queryset = WellHeader.objects.all().prefetch_related(
            "locations",
            "statuses",
            "drilling_records",
            "casing_records",
            "production_summaries",
        ).annotate(
            status_category_value=Subquery(status_category.values("status_category")[:1]),
            actual_status_text_value=Subquery(status_category.values("actual_status_text")[:1]),
        )
        status_value = self.request.query_params.get("status")
        actual_status = self.request.query_params.get("actual_status")
        well_type = self.request.query_params.get("well_type")
        prod_inject_frmtn = self.request.query_params.getlist("prod_inject_frmtn")
        search = self.request.query_params.get("search")

        if status_value:
            queryset = queryset.filter(base_uwi__in=WellStatusCategory.objects.filter(
                status_category=status_value
            ).values("base_uwi"))
        if actual_status:
            queryset = queryset.filter(base_uwi__in=WellStatusCategory.objects.filter(
                actual_status_text=actual_status
            ).values("base_uwi"))
        if well_type:
            queryset = queryset.filter(well_type=well_type)
        if prod_inject_frmtn:
            queryset = queryset.filter(
                base_uwi__in=WellProductionFormation.objects.filter(
                    formation__in=prod_inject_frmtn
                ).values("base_uwi")
            )
        if search:
            queryset = queryset.filter(
                Q(base_uwi__icontains=search)
                | Q(user_format_well_id__icontains=search)
                | Q(well_name__icontains=search)
                | Q(cur_operator_name__icontains=search)
            )

        return queryset.order_by("base_uwi", "-suffix", "-raw_id").distinct("base_uwi")

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_value = self.kwargs.get(self.lookup_field)
        obj = get_object_or_404(queryset, base_uwi=lookup_value)
        self.check_object_permissions(self.request, obj)
        return obj


@api_view(["GET"])
def well_statuses(request):
    return Response([{"value": status, "label": status} for status in STATUS_CATEGORIES])


@api_view(["GET"])
def actual_well_statuses(request):
    queryset = WellStatusCategory.objects.exclude(actual_status_text__isnull=True).exclude(actual_status_text="")
    category = request.query_params.get("status")

    if category:
        queryset = queryset.filter(status_category=category)

    statuses = (
        queryset
        .order_by("actual_status_text")
        .values_list("actual_status_text", flat=True)
        .distinct()
    )
    return Response([{"value": status, "label": status} for status in statuses])


@api_view(["GET"])
def well_types(request):
    types = (
        WellHeader.objects.exclude(well_type__isnull=True)
        .exclude(well_type="")
        .order_by("well_type")
        .values_list("well_type", flat=True)
        .distinct()
    )
    return Response([{"value": well_type, "label": well_type} for well_type in types])


@api_view(["GET"])
def production_injection_formations(request):
    formations = (
        WellProductionFormation.objects.exclude(formation__isnull=True)
        .exclude(formation="")
        .order_by("formation")
        .values_list("formation", flat=True)
        .distinct()
    )
    return Response([{"value": formation, "label": formation} for formation in formations])
