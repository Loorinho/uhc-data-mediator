from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.exceptions import ValidationError

from core.ingestion.models import (
    AcquisitionAttempt,
    District,
    DistrictPopulation,
    Observation,
)
from core.shared.exploration import (
    AuthenticatedPaginationViewMixin,
    respond,
    visible_products,
)


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = (
            "id",
            "name",
            "code",
            "dhis2_org_unit_id",
            "dhis2_name",
            "mapping_status",
            "mapping_notes",
            "is_active",
        )


class PopulationSerializer(serializers.ModelSerializer):
    district = DistrictSerializer(read_only=True)

    class Meta:
        model = DistrictPopulation
        fields = (
            "id",
            "district",
            "reference_year",
            "population",
            "source",
            "source_url",
            "source_notes",
            "created_at",
        )


class SourceObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Observation
        fields = (
            "id",
            "indicator_id",
            "indicator_name",
            "measure_type",
            "org_unit_id",
            "org_unit_name",
            "district",
            "period",
            "value",
            "dimensions",
            "attempt",
            "source",
            "created_at",
        )


class DistrictListView(AuthenticatedPaginationViewMixin, generics.ListAPIView):
    serializer_class = DistrictSerializer

    def get_queryset(self):
        qs = District.objects.all().order_by("name")
        if self.request.query_params.get("mapping_status"):
            qs = qs.filter(mapping_status=self.request.query_params["mapping_status"])
        if self.request.query_params.get("search"):
            qs = qs.filter(name__icontains=self.request.query_params["search"])
        return qs


class DistrictDetailView(AuthenticatedPaginationViewMixin, generics.RetrieveAPIView):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    lookup_field = "id"


class PopulationListView(AuthenticatedPaginationViewMixin, generics.ListAPIView):
    serializer_class = PopulationSerializer

    def get_queryset(self):
        # Population source rows are visible only to population product owners/staff.
        if not (
            self.request.user.is_staff
            or visible_products(self.request.user)
            .filter(code="sl-district-population")
            .exists()
        ):
            return DistrictPopulation.objects.none()
        qs = DistrictPopulation.objects.select_related("district").order_by(
            "district__name"
        )
        if self.request.query_params.get("year"):
            try:
                year = int(self.request.query_params["year"])
            except ValueError:
                raise ValidationError({"year": "Must be an integer."})
            qs = qs.filter(reference_year=year)
        if self.request.query_params.get("district_id"):
            qs = qs.filter(district_id=self.request.query_params["district_id"])
        return qs


class PopulationDetailView(AuthenticatedPaginationViewMixin, generics.RetrieveAPIView):
    serializer_class = PopulationSerializer
    lookup_field = "id"

    def get_queryset(self):
        if (
            self.request.user.is_staff
            or visible_products(self.request.user)
            .filter(code="sl-district-population")
            .exists()
        ):
            return DistrictPopulation.objects.select_related("district")
        return DistrictPopulation.objects.none()


class AcquisitionObservationsView(
    AuthenticatedPaginationViewMixin, generics.ListAPIView
):
    serializer_class = SourceObservationSerializer

    def get_queryset(self):
        attempts = AcquisitionAttempt.objects.all()
        if not self.request.user.is_staff:
            attempts = attempts.filter(requested_by=self.request.user)
        attempt = get_object_or_404(attempts, pk=self.kwargs["acquisition_id"])
        return Observation.objects.filter(attempt=attempt).order_by(
            "org_unit_name", "indicator_id", "period"
        )
