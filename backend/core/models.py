import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Custom user model for the UHC data mediator.

    Inherits Django's username/password handling; `username` is unique
    by default. Roles are assigned through Django groups (e.g. 'data_provider').
    """

    class Meta:
        db_table = "users"


def generate_refresh_token() -> str:
    """Cryptographically random, URL-safe refresh token."""
    return secrets.token_urlsafe(64)


class RefreshToken(models.Model):
    """Server-side refresh token, verified on every token refresh.

    Tokens are rotated: each successful refresh invalidates the old token
    and issues a new one. Reusing an invalidated token is rejected.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="refresh_tokens"
    )
    token = models.CharField(max_length=255, unique=True, default=generate_refresh_token)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_valid = models.BooleanField(default=True)

    class Meta:
        db_table = "refresh_tokens"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=1)
        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def invalidate(self) -> None:
        self.is_valid = False
        self.save(update_fields=["is_valid"])

    def __str__(self) -> str:
        return f"RefreshToken(user={self.user.username}, valid={self.is_valid})"


# Register models that live in feature submodules (e.g. ingestion).
from .ingestion.models import AcquisitionAttempt  # noqa: E402,F401
from .governance.models import DataProduct, DataProductRelease  # noqa: E402,F401
from .interoperability.models import (  # noqa: E402,F401
    CanonicalMeasure,
    CanonicalObservation,
    MeasureSourceMapping,
)

