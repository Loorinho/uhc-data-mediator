from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.ingestion.models import (
    AcquisitionAttempt,
    Observation,
)
from core.ingestion.pagination import (
    AcquisitionObservationPagination,
)
from core.ingestion.serializers import (
    AcquisitionAttemptDetailSerializer,
    AcquisitionObservationSerializer,
)
from core.responses import api_response


class AcquisitionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acquisition_id):
        queryset = AcquisitionAttempt.objects.all()

        if not request.user.is_staff:
            queryset = queryset.filter(requested_by=request.user)

        attempt = get_object_or_404(
            queryset,
            pk=acquisition_id,
        )

        observations = Observation.objects.filter(attempt=attempt).order_by(
            "org_unit_name",
            "indicator_id",
            "period",
            "id",
        )

        paginator = AcquisitionObservationPagination()

        page = paginator.paginate_queryset(
            observations,
            request,
            view=self,
        )

        serializer = AcquisitionAttemptDetailSerializer(attempt)

        observation_serializer = AcquisitionObservationSerializer(
            page,
            many=True,
        )

        current_page = paginator.page

        data = {
            **serializer.data,
            "observations": {
                "items": observation_serializer.data,
                "pagination": {
                    "page": current_page.number,
                    "pageSize": paginator.get_page_size(request),
                    "totalItems": (current_page.paginator.count),
                    "totalPages": (current_page.paginator.num_pages),
                    "hasNext": (current_page.has_next()),
                    "hasPrevious": (current_page.has_previous()),
                },
            },
        }

        # Raw DHIS2 responses can be large.
        # Only include them when explicitly requested.
        include_raw = (
            request.query_params.get(
                "include_raw",
                "false",
            ).lower()
            == "true"
        )

        if include_raw:
            data["responsePayload"] = attempt.response_payload

        return api_response(
            message="Acquisition details retrieved.",
            data=data,
            status_code=status.HTTP_200_OK,
        )
