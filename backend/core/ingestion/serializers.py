from rest_framework import serializers

from core.ingestion.models import (
    AcquisitionAttempt,
    Observation,
)


class AcquisitionRequestSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=AcquisitionAttempt.Mode.choices)


class AcquisitionAttemptListSerializer(serializers.ModelSerializer):
    acquisitionId = serializers.UUIDField(
        source="id",
        read_only=True,
    )

    correlationId = serializers.UUIDField(
        source="correlation_id",
        read_only=True,
    )

    requestedAt = serializers.DateTimeField(
        source="requested_at",
        read_only=True,
    )

    startedAt = serializers.DateTimeField(
        source="started_at",
        read_only=True,
    )

    finishedAt = serializers.DateTimeField(
        source="finished_at",
        read_only=True,
    )

    durationMs = serializers.IntegerField(
        source="duration_ms",
        read_only=True,
    )

    recordsReceived = serializers.IntegerField(
        source="records_received",
        read_only=True,
    )

    recordsSaved = serializers.IntegerField(
        source="records_saved",
        read_only=True,
    )

    expectedCombinations = serializers.IntegerField(
        source="expected_combinations",
        read_only=True,
    )

    receivedCombinations = serializers.IntegerField(
        source="received_combinations",
        read_only=True,
    )

    configuration = serializers.JSONField(
        source="request_config",
        read_only=True,
    )

    class Meta:
        model = AcquisitionAttempt

        fields = [
            "acquisitionId",
            "correlationId",
            "mode",
            "status",
            "outcome",
            "source",
            "configuration",
            "requestedAt",
            "startedAt",
            "finishedAt",
            "durationMs",
            "recordsReceived",
            "recordsSaved",
            "expectedCombinations",
            "receivedCombinations",
        ]


class AcquisitionAttemptDetailSerializer(AcquisitionAttemptListSerializer):
    errorMessage = serializers.CharField(
        source="error_message",
        read_only=True,
    )

    missingCombinations = serializers.JSONField(
        source="missing_combinations",
        read_only=True,
    )

    httpStatusCode = serializers.IntegerField(
        source="http_status_code",
        read_only=True,
    )

    apiUrl = serializers.CharField(
        source="api_url",
        read_only=True,
    )

    requestPayload = serializers.JSONField(
        source="request_payload",
        read_only=True,
    )

    class Meta(AcquisitionAttemptListSerializer.Meta):
        fields = AcquisitionAttemptListSerializer.Meta.fields + [
            "errorMessage",
            "missingCombinations",
            "httpStatusCode",
            "apiUrl",
            "requestPayload",
        ]


class AcquisitionObservationSerializer(serializers.ModelSerializer):
    observationId = serializers.UUIDField(
        source="id",
        read_only=True,
    )

    measureId = serializers.CharField(
        source="indicator_id",
        read_only=True,
    )

    measureName = serializers.CharField(
        source="indicator_name",
        read_only=True,
    )

    measureType = serializers.CharField(
        source="measure_type",
        read_only=True,
    )

    orgUnitId = serializers.CharField(
        source="org_unit_id",
        read_only=True,
    )

    orgUnitName = serializers.CharField(
        source="org_unit_name",
        read_only=True,
    )

    districtId = serializers.UUIDField(
        source="district_id",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Observation

        fields = [
            "observationId",
            "measureId",
            "measureName",
            "measureType",
            "orgUnitId",
            "orgUnitName",
            "districtId",
            "period",
            "value",
            "dimensions",
        ]
