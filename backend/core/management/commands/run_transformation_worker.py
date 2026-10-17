
import logging
import signal
import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections, transaction

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
            raise ValueError(
                "poll-seconds must be at least 1"
            )

        self.running = True

        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

        self.stdout.write(
            self.style.SUCCESS(
                "Canonical transformation worker started."
            )
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

                self.stdout.write(
                    f"Transforming release: {release_id}"
                )

                try:
                    count = transform_release(release_id)

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Release {release_id}: "
                            f"{count} canonical observations"
                        )
                    )

                except Exception as exc:
                    logger.exception(
                        "Transformation failed: %s",
                        release_id,
                    )
                    self.mark_failed(release_id, str(exc))

                if run_once:
                    break

            except Exception:
                logger.exception(
                    "Transformation worker encountered an error"
                )

                if run_once:
                    break

                time.sleep(poll_seconds)

            finally:
                close_old_connections()

        self.stdout.write(
            "Canonical transformation worker stopped."
        )

    def claim_next_release(self):
        with transaction.atomic():
            release = (
                DataProductRelease.objects
                .select_for_update(skip_locked=True)
                .filter(
                    status=DataProductRelease.Status.DRAFT,
                    transformation_status=(
                        DataProductRelease
                        .TransformationStatus.PENDING
                    ),
                )
                .order_by("created_at")
                .first()
            )

            if release is None:
                return None

            release.transformation_status = (
                DataProductRelease
                .TransformationStatus.RUNNING
            )

            release.save(
                update_fields=["transformation_status"]
            )

            return release.pk

    def mark_failed(self, release_id, error):
        with transaction.atomic():
            release = (
                DataProductRelease.objects
                .select_for_update()
                .get(pk=release_id)
            )

            release.transformation_status = (
                DataProductRelease
                .TransformationStatus.FAILED
            )

            # No separate error_message field exists
            # in our current release model, so record
            # the failure in the quality/diagnostic report.
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

    def stop(self, signum, frame):
        self.running = False
