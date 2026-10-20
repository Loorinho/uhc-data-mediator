import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class AuditEvent(models.Model):
    class Outcome(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILURE = "FAILURE", "Failure"
        DENIED = "DENIED", "Denied"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )

    actor_identifier = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    actor_role = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    organization = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    action = models.CharField(
        max_length=100,
        db_index=True,
    )

    resource_type = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    resource_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    outcome = models.CharField(
        max_length=10,
        choices=Outcome.choices,
        db_index=True,
    )

    http_method = models.CharField(
        max_length=10,
        blank=True,
        default="",
    )

    http_path = models.CharField(
        max_length=1000,
        blank=True,
        default="",
    )

    http_status = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    correlation_id = models.UUIDField(
        db_index=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    details = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        db_table = "audit_events"
        ordering = ["-created_at", "-id"]

        indexes = [
            models.Index(
                fields=["actor", "-created_at"],
                name="audit_actor_date_idx",
            ),
            models.Index(
                fields=["resource_type", "resource_id"],
                name="audit_resource_idx",
            ),
            models.Index(
                fields=["action", "outcome"],
                name="audit_action_outcome_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.action} | {self.outcome} | {self.resource_type}:{self.resource_id}"
        )
