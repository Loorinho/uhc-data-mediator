from rest_framework import generics, serializers
from rest_framework.exceptions import ValidationError

from core.interoperability.models import (
    CanonicalMeasure,
    CanonicalObservation,
    MeasureSourceMapping,
)
from core.shared.exploration import AuthenticatedPaginationViewMixin, visible_releases


class MeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = CanonicalMeasure
        fields = (
            "code",
            "name",
            "description",
            "unit",
            "aggregation_method",
            "definition",
            "is_active",
        )


class MeasureMappingSerializer(serializers.ModelSerializer):
    measure = MeasureSerializer(read_only=True)

    class Meta:
        model = MeasureSourceMapping
        fields = ("id", "source", "source_measure_id", "measure")


class CanonicalObservationSerializer(serializers.ModelSerializer):
    measure = MeasureSerializer(read_only=True)
    district = serializers.SerializerMethodField()
    source_type = serializers.SerializerMethodField()

    class Meta:
        model = CanonicalObservation
        fields = (
            "id",
            "measure",
            "district",
            "period",
            "period_type",
            "value",
            "dimensions",
            "schema_version",
            "release",
            "source_type",
            "source_observation",
            "source_population",
            "transformed_at",
        )

    def get_district(self, obj):
        return {"id": str(obj.district_id), "name": obj.district.name}

    def get_source_type(self, obj):
        return "DHIS2" if obj.source_observation_id else "CENSUS_POPULATION"


class MeasureListView(AuthenticatedPaginationViewMixin, generics.ListAPIView):
    serializer_class = MeasureSerializer

    def get_queryset(self):
        qs = CanonicalMeasure.objects.all().order_by("code")
        if self.request.query_params.get("active") in ("true", "false"):
            qs = qs.filter(is_active=self.request.query_params["active"] == "true")
        return qs


class MeasureDetailView(AuthenticatedPaginationViewMixin, generics.RetrieveAPIView):
    serializer_class = MeasureSerializer
    queryset = CanonicalMeasure.objects.all()
    lookup_field = "code"


class MeasureMappingListView(AuthenticatedPaginationViewMixin, generics.ListAPIView):
    serializer_class = MeasureMappingSerializer

    def get_queryset(self):
        qs = MeasureSourceMapping.objects.select_related("measure").order_by(
            "source", "source_measure_id"
        )
        if self.request.query_params.get("source"):
            qs = qs.filter(source=self.request.query_params["source"])
        return qs


class CanonicalObservationListView(
    AuthenticatedPaginationViewMixin, generics.ListAPIView
):
    serializer_class = CanonicalObservationSerializer

    def get_queryset(self):
        qs = (
            CanonicalObservation.objects.filter(
                release__in=visible_releases(self.request.user)
            )
            .select_related("district", "measure")
            .order_by("district__name", "period", "id")
        )
        params = self.request.query_params
        if params.get("release_id"):
            qs = qs.filter(release_id=params["release_id"])
        if params.get("measure"):
            qs = qs.filter(measure_id=params["measure"])
        if params.get("district_id"):
            qs = qs.filter(district_id=params["district_id"])
        if params.get("period"):
            qs = qs.filter(period=params["period"])
        return qs


class CanonicalObservationDetailView(
    AuthenticatedPaginationViewMixin, generics.RetrieveAPIView
):
    serializer_class = CanonicalObservationSerializer
    lookup_field = "id"

    def get_queryset(self):
        return CanonicalObservation.objects.filter(
            release__in=visible_releases(self.request.user)
        ).select_related("district", "measure")
