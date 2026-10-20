from django.urls import path

from core.interoperability.fhir_api import (
    FHIRBundleDownloadAPIView,
    FHIRConformityReportAPIView,
    FHIRExportDetailAPIView,
    FHIRExportListAPIView,
    FHIRExportValidationsAPIView,
    FHIRValidationDetailAPIView,
    FHIRValidationIssuesAPIView,
    ReleaseFHIRExportAPIView,
)

urlpatterns = [
    path(
        "data-product-releases/<uuid:release_id>/fhir-exports/",
        ReleaseFHIRExportAPIView.as_view(),
        name="fhir-export-create",
    ),
    path(
        "fhir-exports/",
        FHIRExportListAPIView.as_view(),
        name="fhir-export-list",
    ),
    path(
        "fhir-exports/<uuid:export_id>/",
        FHIRExportDetailAPIView.as_view(),
        name="fhir-export-detail",
    ),
    path(
        "fhir-exports/<uuid:export_id>/bundle/",
        FHIRBundleDownloadAPIView.as_view(),
        name="fhir-bundle-download",
    ),
    path(
        "fhir-exports/<uuid:export_id>/validations/",
        FHIRExportValidationsAPIView.as_view(),
        name="fhir-export-validations",
    ),
    path(
        "fhir-validations/<uuid:validation_id>/",
        FHIRValidationDetailAPIView.as_view(),
        name="fhir-validation-detail",
    ),
    path(
        "fhir-validations/<uuid:validation_id>/issues/",
        FHIRValidationIssuesAPIView.as_view(),
        name="fhir-validation-issues",
    ),
    path(
        "fhir-validations/<uuid:validation_id>/report/",
        FHIRConformityReportAPIView.as_view(),
        name="fhir-validation-report",
    ),
]
