from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.auditing.models import AuditEvent
from core.auditing.services import record_after_commit
from core.ingestion.models import AcquisitionAttempt
from core.ingestion.pagination import AcquisitionPagination
from core.ingestion.permissions import IsDataProvider
from core.ingestion.serializers import (
    AcquisitionAttemptListSerializer,
    AcquisitionRequestSerializer,
)
from core.responses import api_response


class AcquisitionView(APIView):
    """POST -> queue a LIVE or FIXTURE DHIS2 acquisition.

    Requires authentication plus the 'data_provider' role. For now the
    endpoint only records the acquisition attempt; a worker will pick it
    up later.
    """

    permission_classes = [IsAuthenticated, IsDataProvider]

    def post(self, request):
        serializer = AcquisitionRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return api_response(
                message="A valid acquisition mode is required.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        mode = serializer.validated_data["mode"]

        if mode not in (AcquisitionAttempt.Mode.LIVE, AcquisitionAttempt.Mode.FIXTURE):
            return api_response(
                message="Acquisition mode must be LIVE or FIXTURE.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        dx_ids = list(settings.DHIS2_DX_IDS)
        periods = list(settings.DHIS2_PERIODS)
        org_unit_ids = list(settings.DHIS2_ORG_UNIT_IDS)

        if not dx_ids or not periods or not org_unit_ids:
            return api_response(
                message="DHIS2 acquisition configuration is incomplete.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        request_config = {
            "dx_ids": dx_ids,
            "periods": periods,
            "org_unit_ids": org_unit_ids,
        }

        attempt = AcquisitionAttempt.objects.create(
            mode=mode,
            requested_by=request.user,
            status=AcquisitionAttempt.Status.PENDING,
            source="DHIS2-SL-DEMO",
            request_config=request_config,
        )

        record_after_commit(
            action="ACQUISITION_REQUESTED",
            outcome=AuditEvent.Outcome.SUCCESS,
            actor=request.user,
            resource_type="AcquisitionAttempt",
            resource_id=attempt.id,
            correlation_id=attempt.correlation_id,
            details={
                "mode": attempt.mode,
                "source": attempt.source,
            },
            http_status=200,
        )
        return api_response(
            message=(
                "DHIS2 LIVE acquisition has been queued."
                if mode == AcquisitionAttempt.Mode.LIVE
                else "DHIS2 FIXTURE replay has been queued."
            ),
            data={
                "acquisitionId": str(attempt.id),
                "correlationId": str(attempt.correlation_id),
                "mode": attempt.mode,
                "isLiveRequest": mode == AcquisitionAttempt.Mode.LIVE,
                "status": attempt.status,
                "requestedAt": attempt.requested_at,
                "configuration": request_config,
            },
        )

    def get(self, request):
        queryset = AcquisitionAttempt.objects.all()

        # Staff can view all acquisitions; other users only their own.
        if not request.user.is_staff:
            queryset = queryset.filter(requested_by=request.user)

        # Metadata describes the full authorized scope, not the filtered page.
        # Clear default ordering so DISTINCT does not also select requested_at.
        statuses = sorted(
            queryset.order_by().values_list("status", flat=True).distinct()
        )
        modes = sorted(queryset.order_by().values_list("mode", flat=True).distinct())

        acquisition_status = request.query_params.get("status")
        if acquisition_status:
            acquisition_status = acquisition_status.upper()
            valid_statuses = {choice.value for choice in AcquisitionAttempt.Status}
            if acquisition_status not in valid_statuses:
                return api_response(
                    message="Invalid acquisition status.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(status=acquisition_status)

        mode = request.query_params.get("mode")
        if mode:
            mode = mode.upper()
            valid_modes = {choice.value for choice in AcquisitionAttempt.Mode}
            if mode not in valid_modes:
                return api_response(
                    message="Invalid acquisition mode.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(mode=mode)

        queryset = queryset.order_by("-requested_at", "-id")
        paginator = AcquisitionPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)

        if page is None:
            return api_response(
                message="Acquisition attempts retrieved.",
                data={
                    "items": [],
                    "pagination": {
                        "page": 1,
                        "pageSize": 0,
                        "totalItems": 0,
                        "totalPages": 0,
                        "hasNext": False,
                        "hasPrevious": False,
                    },
                    "statuses": statuses,
                    "modes": modes,
                },
                status_code=status.HTTP_200_OK,
            )

        serializer = AcquisitionAttemptListSerializer(page, many=True)
        current_page = paginator.page

        return api_response(
            message="Acquisition attempts retrieved.",
            data={
                "items": serializer.data,
                "pagination": {
                    "page": current_page.number,
                    "pageSize": paginator.get_page_size(request),
                    "totalItems": current_page.paginator.count,
                    "totalPages": current_page.paginator.num_pages,
                    "hasNext": current_page.has_next(),
                    "hasPrevious": current_page.has_previous(),
                },
                "statuses": statuses,
                "modes": modes,
            },
            status_code=status.HTTP_200_OK,
        )
