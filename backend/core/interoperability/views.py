from django.db import transaction
from django.db.models import Max
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.auditing.models import AuditEvent
from core.auditing.services import record_after_commit
from core.governance.models import (
    DataProduct,
    DataProductRelease,
)
from core.ingestion.models import AcquisitionAttempt
from core.ingestion.permissions import IsDataProvider
from core.interoperability.serializers import (
    TransformationRequestSerializer,
)
from core.responses import api_response


class TriggerTransformationAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDataProvider]

    def post(self, request, acquisition_id):
        serializer = TransformationRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return api_response(
                message="A valid productCode is required.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        product_code = serializer.validated_data["productCode"]

        # 1. Verify the source acquisition exists.
        acquisition = AcquisitionAttempt.objects.filter(pk=acquisition_id).first()

        if acquisition is None:
            return api_response(
                message=(f"Acquisition with ID {acquisition_id} was not found."),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # 2. Verify the data product exists.
        product = DataProduct.objects.filter(code=product_code).first()

        if product is None:
            return api_response(
                message=(f"Data product with code '{product_code}' was not found."),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # 3. Enforce ownership.
        if product.data_owner_id != request.user.pk:
            return api_response(
                message=(
                    "You are not authorized to create releases for this data product."
                ),
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # 4. Accept completed LIVE and FIXTURE acquisitions.
        if acquisition.mode not in (
            AcquisitionAttempt.Mode.LIVE,
            AcquisitionAttempt.Mode.FIXTURE,
        ):
            return api_response(
                message="Unsupported acquisition mode.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if acquisition.status not in (
            AcquisitionAttempt.Status.SUCCEEDED,
            AcquisitionAttempt.Status.PARTIAL,
        ):
            return api_response(
                message=("The acquisition must be completed before transformation."),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if acquisition.source != product.source:
            return api_response(
                message=("Acquisition source does not match the data product source."),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if acquisition.records_saved == 0:
            return api_response(
                message="Acquisition has no saved observations.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # 5. Create a pending, versioned release.
        with transaction.atomic():
            product = DataProduct.objects.select_for_update().get(pk=product.pk)

            existing = (
                DataProductRelease.objects.filter(
                    product=product,
                    source_acquisition=acquisition,
                )
                .order_by("-version")
                .first()
            )

            # Idempotency: do not duplicate releases or
            # TRANSFORMATION_REQUESTED events on retries.
            if existing:
                return api_response(
                    message=(
                        "A release already exists for "
                        "this acquisition and data product."
                    ),
                    data={
                        "releaseId": str(existing.id),
                        "version": existing.version,
                        "status": existing.status,
                        "transformationStatus": (existing.transformation_status),
                    },
                    status_code=status.HTTP_200_OK,
                )

            latest_version = (
                DataProductRelease.objects.filter(product=product).aggregate(
                    max_version=Max("version")
                )["max_version"]
                or 0
            )

            release = DataProductRelease.objects.create(
                product=product,
                source_acquisition=acquisition,
                version=latest_version + 1,
                schema_version=product.schema_version,
                status=DataProductRelease.Status.DRAFT,
                transformation_status=(DataProductRelease.TransformationStatus.PENDING),
                quality_status=(DataProductRelease.QualityStatus.NOT_CHECKED),
            )

            # 6. Record who requested the transformation.
            # The event runs after the transaction commits.
            record_after_commit(
                action="TRANSFORMATION_REQUESTED",
                outcome=AuditEvent.Outcome.SUCCESS,
                actor=request.user,
                resource_type="DataProductRelease",
                resource_id=release.id,
                correlation_id=release.id,
                details={
                    "dataProductId": str(release.product_id),
                    "productCode": product.code,
                    "releaseVersion": release.version,
                    "acquisitionId": str(acquisition.id),
                    "acquisitionCorrelationId": str(acquisition.correlation_id),
                    "acquisitionMode": acquisition.mode,
                    "source": acquisition.source,
                    "transformationStatus": "PENDING",
                },
            )

        return api_response(
            message="Canonical transformation has been queued.",
            data={
                "releaseId": str(release.id),
                "acquisitionId": str(acquisition.id),
                "productCode": product.code,
                "version": release.version,
                "status": release.status,
                "transformationStatus": (release.transformation_status),
                "qualityStatus": release.quality_status,
            },
            status_code=status.HTTP_200_OK,
        )
