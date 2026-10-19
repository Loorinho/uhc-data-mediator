"""
Automatically process pending FHIR generation and validation jobs.

So, polls postgres,
Claims one pending job
Marks it as running
Executes the relevant service
Saves the outcome
Continues polling for new jobs.

"""

import logging
import signal
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections, transaction
from django.utils import timezone

from core.interoperability.models import (
    FHIRExport,
    FHIRValidationResult,
)
from core.interoperability.services.fhir.jobs import (
    process_fhir_export,
    process_fhir_validation,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process pending FHIR export and validation jobs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--poll-seconds",
            type=int,
            default=getattr(
                settings,
                "FHIR_WORKER_POLL_SECONDS",
                3,
            ),
        )

        parser.add_argument(
            "--once",
            action="store_true",
        )

    def handle(self, *args, **options):
        poll_seconds = options["poll_seconds"]
        run_once = options["once"]

        if poll_seconds < 1:
            raise ValueError("--poll-seconds must be at least 1")

        self.running = True

        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

        self.stdout.write(
            self.style.SUCCESS("FHIR export and validation worker started.")
        )

        while self.running:
            close_old_connections()

            try:
                job = self.claim_next_job()

                if job is None:
                    if run_once:
                        break

                    time.sleep(poll_seconds)
                    continue

                job_type, job_id = job

                self.stdout.write(f"Processing {job_type}: {job_id}")

                if job_type == "EXPORT":
                    result = process_fhir_export(job_id)
                else:
                    result = process_fhir_validation(job_id)

                self.stdout.write(f"{job_type} {job_id}: {result}")

            except Exception:
                logger.exception("Unexpected FHIR worker failure")

                if run_once:
                    break

            finally:
                close_old_connections()

            if run_once:
                break

        self.stdout.write("FHIR worker stopped.")

    def claim_next_job(self):
        """
        Claim an export first, then a validation.

        The row lock prevents duplicate processing.
        """
        with transaction.atomic():
            # uses select_for_update(skip_locked=True) to prevent multiple workers
            # from claiming the same pending record simultaneously.
            export = (
                FHIRExport.objects.select_for_update(skip_locked=True)
                .filter(
                    status=FHIRExport.Status.PENDING,
                )
                .order_by("requested_at", "id")
                .first()
            )

            if export is not None:
                export.status = FHIRExport.Status.RUNNING
                export.started_at = timezone.now()
                export.finished_at = None
                export.error_message = ""

                export.save(
                    update_fields=[
                        "status",
                        "started_at",
                        "finished_at",
                        "error_message",
                    ]
                )

                return "EXPORT", export.pk

            validation = (
                FHIRValidationResult.objects.select_for_update(skip_locked=True)
                .filter(
                    status=FHIRValidationResult.Status.PENDING,
                )
                .order_by("requested_at", "id")
                .first()
            )

            if validation is not None:
                validation.status = FHIRValidationResult.Status.RUNNING
                validation.started_at = timezone.now()
                validation.finished_at = None
                validation.error_message = ""

                validation.save(
                    update_fields=[
                        "status",
                        "started_at",
                        "finished_at",
                        "error_message",
                    ]
                )

                return "VALIDATION", validation.pk

        return None

    def stop(self, signum, frame):
        self.running = False
