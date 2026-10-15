from django.conf import settings
from django.db import models


class AcquisitionAttempt(models.Model):
    class Mode(models.TextChoices):
        LIVE = "LIVE", "Live DHIS2"
        FIXTURE = "FIXTURE", "Fixture"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"

    mode = models.CharField(max_length=20, choices=Mode.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT, # Prevents deleting a user referenced by a data acquisition
        related_name="acquisition_attempts",
    )

    requested_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        db_table = "acquisition_attempts"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"Acquisition {self.pk}: {self.mode} ({self.status})"