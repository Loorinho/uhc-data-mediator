
# core/ingestion/models.py

import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class AcquisitionAttempt(models.Model):
    class Mode(models.TextChoices):
        LIVE = "LIVE", "Live DHIS2"
        FIXTURE = "FIXTURE", "Fixture"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        PARTIAL = "PARTIAL", "Partial"
        FAILED = "FAILED", "Failed"

    class Outcome(models.TextChoices):
        OK = "OK", "Completed"
        INCOMPLETE = "INCOMPLETE", "Incomplete data"
        ERROR = "ERROR", "Error"
        TIMEOUT = "TIMEOUT", "Timeout"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    correlation_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    mode = models.CharField(
        max_length=10,
        choices=Mode.choices,
        default=Mode.LIVE,
        db_index=True,
    )

    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    source = models.CharField(
        max_length=100,
        default="DHIS2-SL-DEMO",
        db_index=True,
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="acquisition_attempts",
    )

    requested_at = models.DateTimeField(
        default=timezone.now,
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

    # Immutable scope of this acquisition:
    # {
    #   "dx_ids": ["fbfJHSPpUQD"],
    #   "periods": ["2025"],
    #   "org_unit_ids": ["O6uvpzGd5pu", ...]
    # }
    #
    # Populate this when POST /acquisition creates
    # the attempt. It should not change afterward.
    request_config = models.JSONField(
        default=dict,
        blank=True,
    )

    # Actual upstream request details, including URL.
    request_payload = models.JSONField(
        default=dict,
        blank=True,
    )

    # Original response JSON received from DHIS2.
    response_payload = models.JSONField(
        default=dict,
        blank=True,
    )

    api_url = models.TextField(
        blank=True,
        default="",
    )

    http_status_code = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    outcome = models.CharField(
        max_length=20,
        choices=Outcome.choices,
        null=True,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
        default="",
    )

    duration_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    records_received = models.PositiveIntegerField(
        default=0,
    )

    records_saved = models.PositiveIntegerField(
        default=0,
    )

    expected_combinations = models.PositiveIntegerField(
        default=0,
    )

    received_combinations = models.PositiveIntegerField(
        default=0,
    )

    # Missing dx/period/org-unit combinations.
    missing_combinations = models.JSONField(
        default=list,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "acquisition_attempts"

        ordering = ["-requested_at"]

        indexes = [
            models.Index(
                fields=["status", "requested_at"],
                name="acq_status_requested_idx",
            ),
            models.Index(
                fields=["source", "requested_at"],
                name="acq_source_requested_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.source} | "
            f"{self.mode} | "
            f"{self.status} | "
            f"{self.correlation_id}"
        )


class District(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(
        max_length=150,
        unique=True,
    )

    # Optional administrative code from an
    # authoritative district dataset.
    code = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )

    # Nullable because some census districts
    # have no confirmed one-to-one DHIS2 mapping.
    dhis2_org_unit_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )

    dhis2_name = models.CharField(
        max_length=150,
        blank=True,
        default="",
    )

    class MappingStatus(models.TextChoices):
        VERIFIED = "VERIFIED", "Verified"
        CANDIDATE = "CANDIDATE", "Candidate"
        UNMAPPED = "UNMAPPED", "Unmapped"

    mapping_status = models.CharField(
        max_length=12,
        choices=MappingStatus.choices,
        default=MappingStatus.UNMAPPED,
        db_index=True,
    )

    mapping_notes = models.TextField(
        blank=True,
        default="",
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "districts"
        ordering = ["name"]

        constraints = [
            models.CheckConstraint(
                condition=(
                    ~Q(mapping_status="VERIFIED")
                    | (
                        Q(dhis2_org_unit_id__isnull=False)
                        & ~Q(dhis2_org_unit_id="")
                    )
                ),
                name="verified_district_has_dhis2_uid",
            ),
        ]

    def __str__(self):
        return self.name


class DistrictPopulation(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="population_records",
    )

    reference_year = models.PositiveSmallIntegerField(
        db_index=True,
    )

    population = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)],
    )

    source = models.CharField(
        max_length=255,
    )

    source_url = models.URLField(
        max_length=1000,
        blank=True,
        default="",
    )

    source_notes = models.TextField(
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "district_populations"

        ordering = ["district__name", "-reference_year"]

        constraints = [
            models.UniqueConstraint(
                fields=["district", "reference_year"],
                name="uq_population_district_year",
            ),
            models.CheckConstraint(
                condition=Q(population__gt=0),
                name="population_must_be_positive",
            ),
        ]

        indexes = [
            models.Index(
                fields=["reference_year", "district"],
                name="pop_year_district_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.district.name} | "
            f"{self.reference_year} | "
            f"{self.population}"
        )


class Observation(models.Model):
    class MeasureType(models.TextChoices):
        DATA_ELEMENT = "DATA_ELEMENT", "Data element"
        INDICATOR = "INDICATOR", "Indicator"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    source = models.CharField(
        max_length=100,
        default="DHIS2-SL-DEMO",
        db_index=True,
    )

    # Kept as indicator_id to match the existing
    # ingestion processor. It can contain either
    # a DHIS2 indicator UID or a data element UID.
    indicator_id = models.CharField(
        max_length=100,
        db_index=True,
    )

    indicator_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    measure_type = models.CharField(
        max_length=20,
        choices=MeasureType.choices,
        default=MeasureType.DATA_ELEMENT,
    )

    org_unit_id = models.CharField(
        max_length=100,
        db_index=True,
    )

    org_unit_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="observations",
        null=True,
        blank=True,
    )

    # Examples: 2025, 202507, 2026Q1
    period = models.CharField(
        max_length=30,
        db_index=True,
    )

    value = models.DecimalField(
        max_digits=24,
        decimal_places=6,
    )

    # Additional analytics dimensions other than
    # dx, pe, ou and value.
    dimensions = models.JSONField(
        default=dict,
        blank=True,
    )

    # SHA256 of canonicalized dimensions JSON.
    dimensions_hash = models.CharField(
        max_length=64,
    )

    attempt = models.ForeignKey(
        AcquisitionAttempt,
        on_delete=models.PROTECT,
        related_name="observations",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "observations"

        ordering = ["-period", "org_unit_name"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "source",
                    "indicator_id",
                    "org_unit_id",
                    "period",
                    "dimensions_hash",
                ],
                name="uq_observation_natural_key",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "district",
                    "indicator_id",
                    "period",
                ],
                # Msr for measure_type
                name="obs_district_msr_period_idx",
            ),
            models.Index(
                fields=[
                    "source",
                    "indicator_id",
                    "period",
                ],
                name="obs_source_measure_period_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.indicator_name or self.indicator_id} | "
            f"{self.org_unit_name or self.org_unit_id} | "
            f"{self.period} | {self.value}"
        )
