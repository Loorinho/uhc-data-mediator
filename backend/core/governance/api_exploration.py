from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.governance.models import DataProduct, DataProductRelease
from core.interoperability.api_exploration import CanonicalObservationSerializer
from core.interoperability.models import CanonicalObservation
from core.interoperability.services.population_transformer import transform_population
from core.shared.exploration import (
    AuthenticatedPaginationViewMixin,
    respond,
    visible_products,
    visible_releases,
)


class DataProductSerializer(serializers.ModelSerializer):
    data_owner_id = serializers.ReadOnlyField()

    class Meta:
        model = DataProduct
        fields = (
            "id",
            "code",
            "title",
            "purpose",
            "source",
            "schema_version",
            "sensitivity_classification",
            "permitted_evidence",
            "quality_policy",
            "data_owner_id",
            "created_at",
            "updated_at",
        )


class ReleaseSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    observation_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DataProductRelease
        fields = (
            "id",
            "product",
            "product_code",
            "version",
            "source_acquisition",
            "schema_version",
            "status",
            "transformation_status",
            "quality_status",
            "geographic_coverage",
            "temporal_coverage",
            "refresh_date",
            "quality_report",
            "lineage",
            "created_at",
            "published_at",
            "published_by",
            "observation_count",
        )


def release_queryset(user):
    return visible_releases(user).annotate(observation_count=Count("observations"))


class ProductListView(AuthenticatedPaginationViewMixin, generics.ListAPIView):
    serializer_class = DataProductSerializer

    def get_queryset(self):
        return visible_products(self.request.user).order_by("code")


class ProductDetailView(AuthenticatedPaginationViewMixin, generics.RetrieveAPIView):
    serializer_class = DataProductSerializer
    lookup_field = "code"

    def get_queryset(self):
        return visible_products(self.request.user)


class ProductReleasesView(AuthenticatedPaginationViewMixin, generics.ListAPIView):
    serializer_class = ReleaseSerializer

    def get_queryset(self):
        product = get_object_or_404(
            visible_products(self.request.user), code=self.kwargs["code"]
        )
        return (
            release_queryset(self.request.user)
            .filter(product=product)
            .order_by("-version")
        )


class ReleaseListView(AuthenticatedPaginationViewMixin, generics.ListAPIView):
    serializer_class = ReleaseSerializer

    def get_queryset(self):
        qs = release_queryset(self.request.user).order_by("-created_at", "-version")
        if self.request.query_params.get("product_code"):
            qs = qs.filter(product__code=self.request.query_params["product_code"])
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        return qs


class ReleaseDetailView(AuthenticatedPaginationViewMixin, generics.RetrieveAPIView):
    serializer_class = ReleaseSerializer
    lookup_field = "id"

    def get_queryset(self):
        return release_queryset(self.request.user)


class ReleaseObservationsView(AuthenticatedPaginationViewMixin, generics.ListAPIView):
    serializer_class = CanonicalObservationSerializer

    def get_queryset(self):
        release = get_object_or_404(
            visible_releases(self.request.user), pk=self.kwargs["release_id"]
        )
        return (
            CanonicalObservation.objects.filter(release=release)
            .select_related("district", "measure")
            .order_by("district__name", "id")
        )


class ReleaseLineageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, release_id):
        release = get_object_or_404(visible_releases(request.user), pk=release_id)
        return respond(
            "Release lineage retrieved successfully.",
            {
                "releaseId": str(release.id),
                "productCode": release.product.code,
                "version": release.version,
                "sourceAcquisitionId": str(release.source_acquisition_id)
                if release.source_acquisition_id
                else None,
                "lineage": release.lineage,
                "geographicCoverage": release.geographic_coverage,
                "temporalCoverage": release.temporal_coverage,
            },
        )


class TriggerPopulationTransformationView(APIView):
    """Synchronous, idempotent 16-row MVP transformation; returns HTTP 200.

    A later async variant can enqueue this same service without exposing a command.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, code):
        product = get_object_or_404(visible_products(request.user), code=code)
        if code != "sl-district-population":
            return respond(
                "Population transformation is only available for sl-district-population.",
                None,
                400,
            )
        if request.data not in ({}, None):
            return respond("This operation does not accept a request body.", None, 400)
        try:
            release, created = transform_population(year=2021)
        except (ValueError, DataProduct.DoesNotExist) as exc:
            return respond(str(exc), None, 400)
        # Unexpected database errors should be logged by Django and return 500.
        return respond(
            "Population canonical transformation completed."
            if created
            else "Matching population release already exists.",
            {
                "releaseId": str(release.id),
                "version": release.version,
                "status": release.status,
                "transformationStatus": release.transformation_status,
                "created": created,
            },
            status.HTTP_200_OK,
        )
