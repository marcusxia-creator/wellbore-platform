from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.wells.handlers import WellHandler
from apps.wells.serializers import WellSerializer


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
        return WellHandler.list_wells(self.request.query_params)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_value = self.kwargs.get(self.lookup_field)
        obj = get_object_or_404(queryset, base_uwi=lookup_value)
        self.check_object_permissions(self.request, obj)
        return obj
