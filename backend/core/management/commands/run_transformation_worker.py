import logging
import signal
import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections, transaction

from core.auditing.models import AuditEvent
from core.auditing.services import record_audit_event
from core.governance.models import DataProductRelease
from core.interoperability.services.canonical_transformer import (
    transform_release,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process pending canonical data transformations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--poll-seconds",
            type=int,
            default=3,
        )

        parser.add_argument(
            "--once",
            action="store_true",
            help="Process at most one pending release",
        )

    def handle(self, *args, **options):
        poll_seconds = options["poll_seconds"]
        run_once = options["once"]

        if poll_seconds < 1:
            raise ValueError("poll-seconds must be at least 1")

        self.running = True

        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

        self.stdout.write(
            self.style.SUCCESS("Canonical transformation worker started.")
        )

        while self.running:
            close_old_connections()

            try:
                release_id = self.claim_next_release()

                if release_id is None:
                    if run_once:
                        break

                    time.sleep(poll_seconds)
                    continue

                self.stdout.write(f"Transforming release: {release_id}")

                try:
                    count = transform_release(release_id)

                except Exception as exc:
                    logger.exception(
                        "Transformation failed: %s",
                        release_id,
                    )

                    try:
                        self.mark_failed(
                            release_id,
                            str(exc),
                        )
                    except Exception:
                        logger.exception(
                            "CRITICAL: Could not persist transformation failure for %s",
                            release_id,
                        )

                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Release {release_id}: {count} canonical observations"
                        )
                    )

                if run_once:
                    break

            except Exception:
                logger.exception("Transformation worker encountered an error")

                if run_once:
                    break

                time.sleep(poll_seconds)

            finally:
                close_old_connections()

        self.stdout.write("Canonical transformation worker stopped.")

    def claim_next_release(self):
        """
        Claim a pending release.

        The status update and audit STARTED event
        happen in the same transaction.
        """
        with transaction.atomic():
            release = (
                DataProductRelease.objects.select_for_update(skip_locked=True)
                .filter(
                    status=DataProductRelease.Status.DRAFT,
                    transformation_status=(
                        DataProductRelease.TransformationStatus.PENDING
                    ),
                )
                .order_by("created_at")
                .first()
            )

            if release is None:
                return None

            release.transformation_status = (
                DataProductRelease.TransformationStatus.RUNNING
            )

            release.save(update_fields=["transformation_status"])

            record_audit_event(
                action="TRANSFORMATION_STARTED",
                outcome=AuditEvent.Outcome.SUCCESS,
                resource_type="DataProductRelease",
                resource_id=release.pk,
                correlation_id=release.pk,
                details={
                    "dataProductId": str(release.product_id),
                    "transformationStatus": "RUNNING",
                    "executor": "transformation-worker",
                },
            )

            return release.pk

    def audit_completed_transformation(
        self,
        release_id,
        observation_count,
    ):
        """
        Inspect the persisted release status.

        A successful function return is not sufficient
        evidence of a successful transformation.
        """
        release = DataProductRelease.objects.get(pk=release_id)

        if (
            release.transformation_status
            != DataProductRelease.TransformationStatus.SUCCEEDED
        ):
            logger.warning(
                "Transformation %s returned but its "
                "persisted status is %s. "
                "No success audit event recorded.",
                release_id,
                release.transformation_status,
            )
            return

        try:
            record_audit_event(
                action="TRANSFORMATION_SUCCEEDED",
                outcome=AuditEvent.Outcome.SUCCESS,
                resource_type="DataProductRelease",
                resource_id=release.pk,
                correlation_id=release.pk,
                details={
                    "dataProductId": str(release.product_id),
                    "transformationStatus": (release.transformation_status),
                    "canonicalObservationCount": (observation_count),
                    "executor": "transformation-worker",
                },
            )

        except Exception:
            logger.exception(
                "CRITICAL: Success audit event could not be saved for release %s",
                release_id,
            )

    def mark_failed(self, release_id, error):
        """
        Persist the failed status and FAILURE audit
        record within the same transaction.
        """
        with transaction.atomic():
            release = DataProductRelease.objects.select_for_update().get(pk=release_id)

            # Do not overwrite an already completed
            # transformation.
            if (
                release.transformation_status
                != DataProductRelease.TransformationStatus.RUNNING
            ):
                logger.warning(
                    "Release %s is already in status %s",
                    release_id,
                    release.transformation_status,
                )
                return

            release.transformation_status = (
                DataProductRelease.TransformationStatus.FAILED
            )

            release.quality_report = {
                **(release.quality_report or {}),
                "transformation_error": error,
            }

            release.save(
                update_fields=[
                    "transformation_status",
                    "quality_report",
                ]
            )

            record_audit_event(
                action="TRANSFORMATION_FAILED",
                outcome=AuditEvent.Outcome.FAILURE,
                resource_type="DataProductRelease",
                resource_id=release.pk,
                correlation_id=release.pk,
                details={
                    "dataProductId": str(release.product_id),
                    "transformationStatus": "FAILED",
                    "errorType": "TRANSFORMATION_ERROR",
                    "executor": "transformation-worker",
                },
            )

    def stop(self, signum, frame):
        self.running = False
