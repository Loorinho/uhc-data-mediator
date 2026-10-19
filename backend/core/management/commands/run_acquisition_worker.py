import logging
import signal
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections, transaction
from django.utils import timezone

from core.auditing.models import AuditEvent
from core.auditing.services import record_audit_event
from core.ingestion.models import AcquisitionAttempt
from core.ingestion.services.acquisition_processor import (
    process_acquisition,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process queued LIVE and FIXTURE acquisitions"

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

        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

        self.stdout.write(
            self.style.SUCCESS("DHIS2 acquisition worker started (LIVE + FIXTURE).")
        )

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

            except Exception as exc:
                logger.exception(
                    "Unexpected worker error: %s",
                    attempt_id,
                )

                # process_acquisition normally saves its own
                # terminal status. If an exception escapes
                # before that happens, prevent the attempt
                # from remaining RUNNING indefinitely.
                self.fail_unfinished_attempt(
                    attempt_id,
                    exc,
                )

            finally:
                # Reload the persisted status and audit the
                # actual result, not just the return value
                # from process_acquisition().
                try:
                    self.audit_final_outcome(attempt_id)
                except Exception:
                    logger.exception(
                        "CRITICAL: Could not audit final acquisition outcome: %s",
                        attempt_id,
                    )

                close_old_connections()

            if run_once:
                break

        self.stdout.write("DHIS2 acquisition worker stopped.")

    def claim_next_attempt(self):
        """
        Claim one pending LIVE or FIXTURE attempt.

        The transaction ensures another worker
        cannot claim the same row concurrently.
        """
        with transaction.atomic():
            attempt = (
                AcquisitionAttempt.objects.select_for_update(skip_locked=True)
                .filter(
                    status=AcquisitionAttempt.Status.PENDING,
                    mode__in=[
                        AcquisitionAttempt.Mode.LIVE,
                        AcquisitionAttempt.Mode.FIXTURE,
                    ],
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

            # Record the STARTED event in the same DB
            # transaction as the RUNNING status.
            # If this database write fails, the claim
            # rolls back and the attempt stays PENDING.
            record_audit_event(
                action="ACQUISITION_STARTED",
                outcome=AuditEvent.Outcome.SUCCESS,
                actor=attempt.requested_by,
                resource_type="AcquisitionAttempt",
                resource_id=attempt.id,
                correlation_id=attempt.correlation_id,
                details={
                    "mode": attempt.mode,
                    "source": attempt.source,
                    "executor": "uhc-worker",
                    "status": attempt.status,
                },
            )

            return attempt.pk

    def fail_unfinished_attempt(self, attempt_id, exc):
        """
        Mark an attempt FAILED only if it is still
        RUNNING after an unexpected exception.

        Avoid overwriting a terminal status already
        saved by the acquisition processor.
        """
        try:
            with transaction.atomic():
                attempt = AcquisitionAttempt.objects.select_for_update().get(
                    pk=attempt_id
                )

                if attempt.status != AcquisitionAttempt.Status.RUNNING:
                    return

                attempt.status = AcquisitionAttempt.Status.FAILED
                attempt.finished_at = timezone.now()
                attempt.error_message = (
                    f"Unexpected worker failure: {type(exc).__name__}"
                )

                attempt.save(
                    update_fields=[
                        "status",
                        "finished_at",
                        "error_message",
                        "updated_at",
                    ]
                )

        except Exception:
            logger.exception(
                "Failed to persist unexpected failure for acquisition %s",
                attempt_id,
            )

    def audit_final_outcome(self, attempt_id):
        """
        Record the persisted terminal outcome.

        Never report SUCCEEDED merely because
        process_acquisition() returned without
        raising an exception.
        """
        attempt = AcquisitionAttempt.objects.select_related("requested_by").get(
            pk=attempt_id
        )

        if attempt.status == AcquisitionAttempt.Status.SUCCEEDED:
            action = "ACQUISITION_SUCCEEDED"
            outcome = AuditEvent.Outcome.SUCCESS

        elif attempt.status == AcquisitionAttempt.Status.PARTIAL:
            action = "ACQUISITION_PARTIAL"
            outcome = AuditEvent.Outcome.FAILURE

        elif attempt.status == AcquisitionAttempt.Status.FAILED:
            action = "ACQUISITION_FAILED"
            outcome = AuditEvent.Outcome.FAILURE

        else:
            logger.warning(
                "Acquisition %s has non-terminal status %s; "
                "skipping terminal audit event",
                attempt_id,
                attempt.status,
            )
            return

        record_audit_event(
            action=action,
            outcome=outcome,
            actor=attempt.requested_by,
            resource_type="AcquisitionAttempt",
            resource_id=attempt.id,
            correlation_id=attempt.correlation_id,
            details={
                "mode": attempt.mode,
                "source": attempt.source,
                "executor": "uhc-worker",
                "finalStatus": attempt.status,
                "outcome": attempt.outcome,
            },
        )

    def stop(self, signum, frame):
        self.running = False
