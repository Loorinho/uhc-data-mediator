import uuid

from django.conf import settings
from django.db import models

from core.ingestion.models import (
    District,
    DistrictPopulation,
    Observation,
)


# Defines what a canonical model means
class CanonicalMeasure(models.Model):
    class Unit(models.TextChoices):
        VISITS = "VISITS", "Visits"
        CASES = "CASES", "Cases"
        PERCENT = "PERCENT", "Percent"
        COUNT = "COUNT", "Count"

    class Aggregation(models.TextChoices):
        SUM = "SUM", "Sum"
        NONE = "NONE", "Not additive"

    code = models.CharField(
        max_length=80,
        primary_key=True,
    )

    name = models.CharField(max_length=255)

    description = models.TextField()

    unit = models.CharField(
        max_length=20,
        choices=Unit.choices,
    )

    aggregation_method = models.CharField(
        max_length=10,
        choices=Aggregation.choices,
    )

    # Additional semantic information; for example,
    # whether a denominator is required.
    definition = models.JSONField(default=dict)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "canonical_measures"

    def __str__(self):
        return self.code


# second stores the normalized dataset records.
class MeasureSourceMapping(models.Model):
    """
    Maps a source-specific identifier to a
    canonical measure. Kept out of Analytics.
    """

    source = models.CharField(max_length=100)

    source_measure_id = models.CharField(max_length=100)

    measure = models.ForeignKey(
        CanonicalMeasure,
        on_delete=models.PROTECT,
        related_name="source_mappings",
    )

    class Meta:
        db_table = "measure_source_mappings"

        constraints = [
            models.UniqueConstraint(
                fields=["source", "source_measure_id"],
                name="uq_canonical_source_measure",
            ),
        ]


class CanonicalObservation(models.Model):
    class PeriodType(models.TextChoices):
        YEAR = "YEAR", "Year"
        MONTH = "MONTH", "Month"
        QUARTER = "QUARTER", "Quarter"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    measure = models.ForeignKey(
        CanonicalMeasure,
        on_delete=models.PROTECT,
        related_name="canonical_observations",
    )

    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="canonical_observations",
    )

    period = models.CharField(max_length=30)

    period_type = models.CharField(
        max_length=10,
        choices=PeriodType.choices,
    )

    value = models.DecimalField(
        max_digits=24,
        decimal_places=6,
    )

    dimensions = models.JSONField(default=dict)

    dimensions_hash = models.CharField(max_length=64)

    schema_version = models.CharField(
        max_length=20,
        default="1.0.0",
    )

    # Reference to the original acquired observation.
    source_observation = models.ForeignKey(
        Observation,
        on_delete=models.PROTECT,
        related_name="canonical_versions",
        null=True,
        blank=True,
    )

    # Reference to the original acquired population record.
    source_population = models.ForeignKey(
        DistrictPopulation,
        on_delete=models.PROTECT,
        related_name="canonical_versions",
        null=True,
        blank=True,
    )

    # Each canonical record belongs to an explicit
    # data product release.
    release = models.ForeignKey(
        "core.DataProductRelease",
        on_delete=models.PROTECT,
        related_name="observations",
    )

    transformed_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "canonical_observations"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "release",
                    "measure",
                    "district",
                    "period",
                    "dimensions_hash",
                ],
                name="uq_canonical_release_observation",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        source_observation__isnull=False, source_population__isnull=True
                    )
                    | models.Q(
                        source_observation__isnull=True, source_population__isnull=False
                    )
                ),
                name="canonical_exactly_one_source",
            ),
        ]


# GeographicCrosswalk


class GeographicCrosswalk(models.Model):
    class SourceSystem(models.TextChoices):
        DHIS2 = "DHIS2-SL-DEMO", "DHIS2 Sierra Leone"
        CENSUS = "STATS-SL-2021-MTPHC", "Statistics Sierra Leone"

    class MappingType(models.TextChoices):
        EXACT = "EXACT", "Exact geographic match"
        PARTIAL = "PARTIAL", "Partial overlap"
        AGGREGATED = "AGGREGATED", "Multiple areas combined"
        UNKNOWN = "UNKNOWN", "Unknown relationship"

    class VerificationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending review"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    source_system = models.CharField(
        max_length=100,
        choices=SourceSystem.choices,
    )

    source_area_id = models.CharField(
        max_length=100,
    )

    source_area_name = models.CharField(
        max_length=150,
    )

    # Reference year of the source's geographic definition.
    # Nullable when not yet established.
    source_geography_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    # Internal district identity used for reconciliation.
    target_district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="geographic_crosswalks",
    )

    # Census geography against which compatibility is assessed.
    target_geography_year = models.PositiveSmallIntegerField(
        default=2021,
    )

    mapping_type = models.CharField(
        max_length=20,
        choices=MappingType.choices,
        default=MappingType.UNKNOWN,
    )

    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
    )

    evidence_url = models.URLField(
        max_length=1000,
        blank=True,
        default="",
    )

    mapping_notes = models.TextField(
        blank=True,
        default="",
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewed_geographic_mappings",
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "geographic_crosswalks"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "source_system",
                    "source_area_id",
                    "source_geography_year",
                    "target_district",
                    "target_geography_year",
                ],
                name="uq_geo_crosswalk_mapping",
                nulls_distinct=False,
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(verification_status="PENDING")
                    | models.Q(verification_status="REJECTED")
                    | (
                        models.Q(
                            verification_status="VERIFIED",
                            mapping_type="EXACT",
                            reviewed_by__isnull=False,
                            reviewed_at__isnull=False,
                        )
                        & ~models.Q(evidence_url="")
                    )
                ),
                name="geo_verified_requires_evidence",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "source_system",
                    "source_area_id",
                ],
                name="geo_source_lookup_idx",
            ),
            models.Index(
                fields=[
                    "verification_status",
                    "mapping_type",
                ],
                name="geo_mapping_status_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.source_system}: "
            f"{self.source_area_name} -> "
            f"{self.target_district.name} "
            f"({self.verification_status})"
        )
