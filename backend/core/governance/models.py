
import uuid

from django.conf import settings
from django.db import models


class DataProduct(models.Model):
    class Sensitivity(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        INTERNAL = "INTERNAL", "Internal"
        RESTRICTED = "RESTRICTED", "Restricted"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    code = models.SlugField(
        max_length=120,
        unique=True,
    )

    title = models.CharField(max_length=255)

    purpose = models.TextField()

    # Assign an actual accountable user.
    # Do not automatically assume the DHIS2 demo
    # administrator is the data owner.
    data_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_data_products",
    )

    source = models.CharField(max_length=150)

    schema_version = models.CharField(
        max_length=20,
        default="1.0.0",
    )

    sensitivity_classification = models.CharField(
        max_length=20,
        choices=Sensitivity.choices,
        default=Sensitivity.INTERNAL,
    )

    # Structured declarations, not free-text labels.
    permitted_evidence = models.JSONField(
        default=list,
    )

    # Metadata indicating what checks are required
    # before a release can be published.
    quality_policy = models.JSONField(
        default=dict,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "data_products"

    def __str__(self):
        return self.title


class DataProductRelease(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        VALIDATING = "VALIDATING", "Validating"
        READY = "READY", "Ready for review"
        PUBLISHED = "PUBLISHED", "Published"
        REJECTED = "REJECTED", "Rejected"

    class QualityStatus(models.TextChoices):
        NOT_CHECKED = "NOT_CHECKED", "Not checked"
        PASSED = "PASSED", "Passed"
        WARNING = "WARNING", "Warning"
        FAILED = "FAILED", "Failed"

    class TransformationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    product = models.ForeignKey(
        DataProduct,
        on_delete=models.PROTECT,
        related_name="releases",
    )

    version = models.PositiveIntegerField()

    source_acquisition = models.ForeignKey(
        "core.AcquisitionAttempt",
        on_delete=models.PROTECT,
        related_name="data_product_releases",
    )

    schema_version = models.CharField(max_length=20)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    transformation_status = models.CharField(
        max_length=20,
        choices=TransformationStatus.choices,
        default=TransformationStatus.PENDING,
    )

    quality_status = models.CharField(
        max_length=20,
        choices=QualityStatus.choices,
        default=QualityStatus.NOT_CHECKED,
    )

    # Geographic and temporal scope as used by
    # this exact release.
    geographic_coverage = models.JSONField(
        default=dict,
    )

    temporal_coverage = models.JSONField(
        default=dict,
    )

    refresh_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    quality_report = models.JSONField(default=dict)

    # Captures the transformation and mapping versions
    # as well as the upstream provenance.
    lineage = models.JSONField(default=dict)

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="published_data_product_releases",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "data_product_releases"

        constraints = [
            models.UniqueConstraint(
                fields=["product", "version"],
                name="uq_data_product_release_version",
            ),
        ]
