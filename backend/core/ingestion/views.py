from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.responses import api_response

from .models import AcquisitionAttempt
from .permissions import IsDataProvider
from .serializers import AcquisitionRequestSerializer


class AcquisitionView(APIView):
    """POST -> trigger a DHIS2 data acquisition.

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

        # Record the attempt; a worker will process it later.
        attempt = AcquisitionAttempt.objects.create(
            mode=serializer.validated_data["mode"],
            requested_by=request.user,
            status=AcquisitionAttempt.Status.PENDING,
        )

        return api_response(
            message="DHIS2 data acquisition has been queued.",
            data={
                "acquisitionId": attempt.id,
                "mode": attempt.mode,
                "status": attempt.status,
                "requestedAt": attempt.requested_at,
            },
            status_code=status.HTTP_202_ACCEPTED,
        )