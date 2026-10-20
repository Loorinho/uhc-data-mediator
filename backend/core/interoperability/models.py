import uuid

from django.conf import settings
from django.db import models

from core.governance.models import DataProductRelease
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


# FHIR


# stores information about generated FHIR Bundles
# from a canonical data product release.
class FHIRExport(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    release = models.ForeignKey(
        DataProductRelease,
        on_delete=models.PROTECT,
        related_name="fhir_exports",
    )

    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    fhir_version = models.CharField(
        max_length=20,
        default="4.0.1",
    )

    mapping_version = models.CharField(
        max_length=40,
        default="mapping-v2",
    )

    bundle_path = models.CharField(
        max_length=1024,
        blank=True,
        default="",
    )

    bundle_sha256 = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )

    resource_count = models.PositiveIntegerField(default=0)

    resource_summary = models.JSONField(
        default=dict,
        blank=True,
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_fhir_exports",
    )

    requested_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    finished_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
        default="",
    )

    class Meta:
        db_table = "fhir_exports"
        ordering = ["-requested_at", "-id"]

        indexes = [
            models.Index(
                fields=["release", "-requested_at"],
                name="fhir_exp_release_date_idx",
            ),
            models.Index(
                fields=["status", "requested_at"],
                name="fhir_exp_queue_idx",
            ),
        ]

    def __str__(self):
        return f"FHIR export {self.id} ({self.status})"


# stores conformity validation results.
# i,e Records every conformity validation
# performed on a generated FHIR Bundle.


class FHIRValidationResult(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    class Classification(models.TextChoices):
        CONFORMANT = (
            "CONFORMANT",
            "Conformant",
        )
        CONFORMANT_WITH_WARNINGS = (
            "CONFORMANT_WITH_WARNINGS",
            "Conformant with warnings",
        )
        NON_CONFORMANT = (
            "NON_CONFORMANT",
            "Non-conformant",
        )
        BLOCKED = (
            "BLOCKED",
            "Blocked",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    fhir_export = models.ForeignKey(
        FHIRExport,
        on_delete=models.PROTECT,
        related_name="validations",
    )

    # tells us whether the validation job ran successfully
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # tells us whether the FHIR Bundle conformed to the standard.
    classification = models.CharField(
        max_length=30,
        choices=Classification.choices,
        null=True,
        blank=True,
    )

    validator_name = models.CharField(
        max_length=120,
        default="HL7 FHIR Validator CLI",
    )

    validator_version = models.CharField(
        max_length=40,
        blank=True,
        default="",
    )

    fhir_version = models.CharField(
        max_length=20,
        default="4.0.1",
    )

    bundle_sha256 = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )

    validator_return_code = models.IntegerField(
        null=True,
        blank=True,
    )

    fatal_count = models.PositiveIntegerField(default=0)

    error_count = models.PositiveIntegerField(default=0)

    warning_count = models.PositiveIntegerField(default=0)

    information_count = models.PositiveIntegerField(default=0)

    report_path = models.CharField(
        max_length=1024,
        blank=True,
        default="",
    )

    operation_outcome_path = models.CharField(
        max_length=1024,
        blank=True,
        default="",
    )

    console_log_path = models.CharField(
        max_length=1024,
        blank=True,
        default="",
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_fhir_validations",
    )

    requested_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    finished_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
        default="",
    )

    class Meta:
        db_table = "fhir_validation_results"
        ordering = ["-requested_at", "-id"]

        indexes = [
            models.Index(
                fields=["fhir_export", "-requested_at"],
                name="fhir_val_export_date_idx",
            ),
            models.Index(
                fields=["status", "requested_at"],
                name="fhir_val_queue_idx",
            ),
            models.Index(
                fields=["classification"],
                name="fhir_val_class_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(classification__isnull=True)
                    | models.Q(status__in=["COMPLETED", "FAILED"])
                ),
                name="fhir_val_class_after_run",
            ),
        ]

    def __str__(self):
        return f"FHIR validation {self.id} ({self.status})"


# Stores each individual issue discovered during validation.
# It will allow the ui to display a searchable list of conformity findings.
class FHIRValidationIssue(models.Model):
    class Source(models.TextChoices):
        HL7_VALIDATOR = "HL7_VALIDATOR", "HL7 Validator"
        APPLICATION = "APPLICATION", "Application"

    class Severity(models.TextChoices):
        FATAL = "fatal", "Fatal"
        ERROR = "error", "Error"
        WARNING = "warning", "Warning"
        INFORMATION = "information", "Information"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    validation = models.ForeignKey(
        FHIRValidationResult,
        on_delete=models.CASCADE,
        related_name="issues",
    )

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
    )

    severity = models.CharField(
        max_length=12,
        choices=Severity.choices,
        db_index=True,
    )

    code = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    diagnostics = models.TextField()

    expression = models.JSONField(
        default=list,
        blank=True,
    )

    resource_type = models.CharField(
        max_length=80,
        blank=True,
        default="",
    )

    resource_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "fhir_validation_issues"
        ordering = ["id"]

        indexes = [
            models.Index(
                fields=["validation", "severity"],
                name="fhir_issue_val_sev_idx",
            ),
            models.Index(
                fields=["validation", "source"],
                name="fhir_issue_val_src_idx",
            ),
        ]

    def __str__(self):
        return f"{self.severity}: {self.code}"
