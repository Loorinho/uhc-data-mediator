"""
Provide the endpoints my UI will consume.
"""

import json
from pathlib import Path

from django.db import transaction
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.auditing.models import AuditEvent
from core.auditing.services import record_after_commit
from core.governance.models import DataProductRelease
from core.interoperability.fhir_permissions import (
    can_view_release,
    require_manage_release,
    require_view_release,
)
from core.interoperability.models import (
    FHIRExport,
    FHIRValidationIssue,
    FHIRValidationResult,
)
from core.interoperability.services.fhir.jobs import (
    bundle_file,
    file_sha256,
    validation_directory,
)
from core.responses import api_response


def export_data(export):
    return {
        "id": str(export.id),
        "releaseId": str(export.release_id),
        "status": export.status,
        "fhirVersion": export.fhir_version,
        "mappingVersion": export.mapping_version,
        "resourceCount": export.resource_count,
        "resourceSummary": export.resource_summary,
        "bundleSha256": export.bundle_sha256,
        "requestedAt": export.requested_at,
        "startedAt": export.started_at,
        "finishedAt": export.finished_at,
        "errorMessage": export.error_message,
    }


def validation_data(validation):
    return {
        "id": str(validation.id),
        "fhirExportId": str(validation.fhir_export_id),
        "status": validation.status,
        "classification": validation.classification,
        "validatorName": validation.validator_name,
        "validatorVersion": validation.validator_version,
        "fhirVersion": validation.fhir_version,
        "bundleSha256": validation.bundle_sha256,
        "validatorReturnCode": (validation.validator_return_code),
        "counts": {
            "fatal": validation.fatal_count,
            "error": validation.error_count,
            "warning": validation.warning_count,
            "information": validation.information_count,
        },
        "requestedAt": validation.requested_at,
        "startedAt": validation.started_at,
        "finishedAt": validation.finished_at,
        "errorMessage": validation.error_message,
    }


def issue_data(issue):
    return {
        "id": str(issue.id),
        "source": issue.source,
        "severity": issue.severity,
        "code": issue.code,
        "diagnostics": issue.diagnostics,
        "expression": issue.expression,
        "resourceType": issue.resource_type,
        "resourceId": issue.resource_id,
    }


def paginate(queryset, request, serializer):
    """
    Simple database-backed pagination.

    Query parameters:
      page=1
      page_size=20
    """
    try:
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
    except (TypeError, ValueError):
        return None

    if page < 1 or not 1 <= page_size <= 100:
        return None

    total = queryset.count()
    total_pages = max(
        1,
        (total + page_size - 1) // page_size,
    )

    offset = (page - 1) * page_size

    items = queryset[offset : offset + page_size]

    return {
        "items": [serializer(item) for item in items],
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "totalItems": total,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrevious": page > 1,
        },
    }


def paginated_response(queryset, request, serializer):
    data = paginate(queryset, request, serializer)

    if data is None:
        return api_response(
            message="Invalid pagination parameters.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return api_response(
        message="Records retrieved successfully.",
        data=data,
        status_code=status.HTTP_200_OK,
    )


def get_export_or_404(export_id):
    return get_object_or_404(
        FHIRExport.objects.select_related("release__product"),
        pk=export_id,
    )


def get_validation_or_404(validation_id):
    return get_object_or_404(
        FHIRValidationResult.objects.select_related("fhir_export__release__product"),
        pk=validation_id,
    )


def downloadable_file(path, filename):
    """
    Never read an arbitrary path supplied by the
    client. Only call this with internally derived
    export/validation storage paths.
    """
    if not path.is_file():
        return api_response(
            message="The requested file is unavailable.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return FileResponse(
        open(path, "rb"),
        as_attachment=True,
        filename=filename,
        content_type="application/json",
    )


def authorized_exports(user):
    queryset = FHIRExport.objects.select_related("release__product")

    # Evaluate per release using the centralized
    # authorization function.
    allowed_release_ids = [
        release.id
        for release in (DataProductRelease.objects.select_related("product"))
        if can_view_release(user, release)
    ]

    return queryset.filter(release_id__in=allowed_release_ids)


class ReleaseFHIRExportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, release_id):
        release = get_object_or_404(
            DataProductRelease.objects.select_related("product"),
            pk=release_id,
        )

        require_manage_release(request.user, release)

        if release.product.code != "sl-district-anc-activity":
            return api_response(
                message=(
                    "FHIR generation currently supports "
                    "only the ANC activity data product."
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if release.transformation_status != "SUCCEEDED":
            return api_response(
                message=(
                    "Release transformation must be successful before FHIR generation."
                ),
                status_code=status.HTTP_409_CONFLICT,
            )

        if release.status == "REJECTED" or release.quality_status == "FAILED":
            return api_response(
                message=("Rejected or quality-failed releases cannot be exported."),
                status_code=status.HTTP_409_CONFLICT,
            )

        with transaction.atomic():
            # Serialize generation requests for this
            # release to prevent duplicate pending jobs.
            release = DataProductRelease.objects.select_for_update().get(pk=release_id)

            existing = FHIRExport.objects.filter(
                release=release,
                status__in=["PENDING", "RUNNING"],
            ).first()

            if existing:
                return api_response(
                    message="FHIR generation is already in progress.",
                    data=export_data(existing),
                    status_code=status.HTTP_409_CONFLICT,
                )

            export = FHIRExport.objects.create(
                release=release,
                requested_by=request.user,
                status=FHIRExport.Status.PENDING,
                fhir_version="4.0.1",
                mapping_version="mapping-v2",
            )

            record_after_commit(
                action="FHIR_EXPORT_REQUESTED",
                outcome=AuditEvent.Outcome.SUCCESS,
                actor=request.user,
                resource_type="FHIRExport",
                resource_id=export.id,
                correlation_id=export.id,
                details={
                    "releaseId": str(export.release_id),
                },
            )

        return api_response(
            message="FHIR generation has been queued.",
            data=export_data(export),
            status_code=status.HTTP_200_OK,
        )


class FHIRExportListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = authorized_exports(request.user).order_by("-requested_at", "-id")

        release_id = request.query_params.get("release_id")

        if release_id:
            try:
                from uuid import UUID

                UUID(release_id)
            except (ValueError, AttributeError, TypeError):
                return api_response(
                    message="Invalid release_id.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            queryset = queryset.filter(release_id=release_id)

        return paginated_response(
            queryset,
            request,
            export_data,
        )


class FHIRExportDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, export_id):
        export = get_export_or_404(export_id)

        require_view_release(
            request.user,
            export.release,
        )

        return api_response(
            message="FHIR export retrieved.",
            data=export_data(export),
        )


class FHIRBundleDownloadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, export_id):
        export = get_export_or_404(export_id)

        require_view_release(
            request.user,
            export.release,
        )

        if export.status != FHIRExport.Status.SUCCEEDED:
            return api_response(
                message="The FHIR Bundle is not ready.",
                status_code=status.HTTP_409_CONFLICT,
            )

        path = bundle_file(export.id)

        if not path.is_file() or file_sha256(path) != export.bundle_sha256:
            return api_response(
                message=("FHIR Bundle is missing or its integrity check failed."),
                status_code=status.HTTP_409_CONFLICT,
            )

        return downloadable_file(
            path,
            f"fhir_bundle_{export.id}.json",
        )


class FHIRExportValidationsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, export_id):
        export = get_export_or_404(export_id)

        require_view_release(
            request.user,
            export.release,
        )

        queryset = export.validations.order_by("-requested_at", "-id")

        return paginated_response(
            queryset,
            request,
            validation_data,
        )

    def post(self, request, export_id):
        export = get_export_or_404(export_id)

        require_manage_release(
            request.user,
            export.release,
        )

        if export.status != FHIRExport.Status.SUCCEEDED:
            return api_response(
                message=("FHIR generation must succeed before validation."),
                status_code=status.HTTP_409_CONFLICT,
            )

        with transaction.atomic():
            export = FHIRExport.objects.select_for_update().get(pk=export_id)

            existing = FHIRValidationResult.objects.filter(
                fhir_export=export,
                status__in=["PENDING", "RUNNING"],
            ).first()

            if existing:
                return api_response(
                    message="Validation is already in progress.",
                    data=validation_data(existing),
                    status_code=status.HTTP_409_CONFLICT,
                )

            validation = FHIRValidationResult.objects.create(
                fhir_export=export,
                requested_by=request.user,
                status=FHIRValidationResult.Status.PENDING,
                fhir_version=export.fhir_version,
                bundle_sha256=export.bundle_sha256,
            )

            record_after_commit(
                action="FHIR_VALIDATION_REQUESTED",
                outcome=AuditEvent.Outcome.SUCCESS,
                actor=request.user,
                resource_type="FHIRValidationResult",
                resource_id=validation.id,
                correlation_id=validation.id,
                details={
                    "fhirExportId": str(validation.fhir_export_id),
                },
            )

        return api_response(
            message="FHIR validation has been queued.",
            data=validation_data(validation),
            status_code=status.HTTP_200_OK,
        )


class FHIRValidationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, validation_id):
        validation = get_validation_or_404(validation_id)

        require_view_release(
            request.user,
            validation.fhir_export.release,
        )

        return api_response(
            message="FHIR validation retrieved.",
            data=validation_data(validation),
        )


class FHIRValidationIssuesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, validation_id):
        validation = get_validation_or_404(validation_id)

        require_view_release(
            request.user,
            validation.fhir_export.release,
        )

        queryset = validation.issues.all()

        severity = request.query_params.get("severity")
        source = request.query_params.get("source")

        if severity:
            valid = {choice.value for choice in FHIRValidationIssue.Severity}

            if severity not in valid:
                return api_response(
                    message="Invalid issue severity.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            queryset = queryset.filter(severity=severity)

        if source:
            valid = {choice.value for choice in FHIRValidationIssue.Source}

            if source not in valid:
                return api_response(
                    message="Invalid issue source.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            queryset = queryset.filter(source=source)

        return paginated_response(
            queryset.order_by("id"),
            request,
            issue_data,
        )


class FHIRConformityReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, validation_id):
        validation = get_validation_or_404(validation_id)

        require_view_release(
            request.user,
            validation.fhir_export.release,
        )

        if validation.status not in [
            FHIRValidationResult.Status.COMPLETED,
            FHIRValidationResult.Status.FAILED,
        ]:
            return api_response(
                message="Validation report is not ready.",
                status_code=status.HTTP_409_CONFLICT,
            )

        # Build this path internally rather than
        # trusting a path from a URL or request body.
        path = validation_directory(validation) / "conformity_report.json"

        return downloadable_file(
            path,
            f"conformity_report_{validation.id}.json",
        )
