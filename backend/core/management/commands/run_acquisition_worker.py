import logging
import signal
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import (
    close_old_connections,
    transaction,
)
from django.utils import timezone

from core.ingestion.models import AcquisitionAttempt
from core.ingestion.services.acquisition_processor import (
    process_acquisition,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process queued LIVE DHIS2 acquisitions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--poll-seconds",
            type=int,
            default=settings.ACQUISITION_POLL_SECONDS,
        )

        parser.add_argument(
            "--once",
            action="store_true",
            help="Process one pending attempt and exit",
        )

    def handle(self, *args, **options):
        poll_seconds = options["poll_seconds"]
        run_once = options["once"]

        if poll_seconds < 1:
            raise ValueError("--poll-seconds must be >= 1")

        self.running = True

        signal.signal(
            signal.SIGTERM,
            self.stop,
        )

        signal.signal(
            signal.SIGINT,
            self.stop,
        )

        self.stdout.write(self.style.SUCCESS("DHIS2 acquisition worker started."))

        while self.running:
            close_old_connections()

            try:
                attempt_id = self.claim_next_attempt()

            except Exception:
                logger.exception("Failed to claim acquisition")

                if run_once:
                    break

                time.sleep(poll_seconds)
                continue

            if attempt_id is None:
                if run_once:
                    break

                time.sleep(poll_seconds)
                continue

            self.stdout.write(f"Processing acquisition: {attempt_id}")

            try:
                result = process_acquisition(attempt_id)

                self.stdout.write(f"Acquisition {attempt_id}: {result}")

            except Exception:
                logger.exception(
                    "Unexpected worker error: %s",
                    attempt_id,
                )

            finally:
                close_old_connections()

            if run_once:
                break

        self.stdout.write("DHIS2 acquisition worker stopped.")

    def claim_next_attempt(self):
        """
        Claim one pending LIVE attempt.

        The transaction ensures another worker
        cannot claim the same row concurrently.
        """

        with transaction.atomic():
            attempt = (
                AcquisitionAttempt.objects.select_for_update(skip_locked=True)
                .filter(
                    status=AcquisitionAttempt.Status.PENDING,
                    mode=AcquisitionAttempt.Mode.LIVE,
                )
                .order_by("requested_at")
                .first()
            )

            if attempt is None:
                return None

            attempt.status = AcquisitionAttempt.Status.RUNNING

            attempt.started_at = timezone.now()
            attempt.finished_at = None
            attempt.error_message = ""
            attempt.outcome = None

            attempt.save(
                update_fields=[
                    "status",
                    "started_at",
                    "finished_at",
                    "error_message",
                    "outcome",
                    "updated_at",
                ]
            )

            return attempt.pk

    def stop(self, signum, frame):
        self.running = False
