"""Shared pagination, permissions and API envelopes for exploration APIs."""

from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


def respond(message, data=None, status_code=200):
    # Same JSON envelope as the application's existing api_response helper.
    return Response(
        {"statusCode": status_code, "message": message, "data": data},
        status=status_code,
    )


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return respond(
            "Records retrieved successfully.",
            {
                "items": data,
                "pagination": {
                    "count": self.page.paginator.count,
                    "page": self.page.number,
                    "pageSize": self.get_page_size(self.request),
                    "totalPages": self.page.paginator.num_pages,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
            },
        )


class AuthenticatedPaginationViewMixin:
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def retrieve(self, request, *args, **kwargs):
        # DRF's default retrieve returns a bare serializer object, unlike our
        # paginated lists. Keep all exploration details in the same envelope.
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return respond("Record retrieved successfully.", serializer.data)


def visible_products(user):
    """MVP: only a product's owner or staff can view governed data."""
    from core.governance.models import DataProduct

    qs = DataProduct.objects.all()
    return qs if user.is_staff else qs.filter(data_owner=user)


def visible_releases(user):
    from core.governance.models import DataProductRelease

    qs = DataProductRelease.objects.select_related("product", "product__data_owner")
    return qs if user.is_staff else qs.filter(product__data_owner=user)
