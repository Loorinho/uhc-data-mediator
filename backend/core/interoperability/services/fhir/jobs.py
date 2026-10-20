import hashlib
import json
import logging
import os
import tempfile
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.auditing.models import AuditEvent
from core.auditing.services import record_audit_event
from core.interoperability.models import (
    FHIRExport,
    FHIRValidationIssue,
    FHIRValidationResult,
)
from core.interoperability.services.fhir.builder import (
    build_anc_bundle,
)
from core.interoperability.services.fhir.conformity import (
    validate_bundle,
)

logger = logging.getLogger(__name__)


def export_root():
    return Path(settings.FHIR_EXPORT_ROOT).resolve()


def export_directory(export_id):
    return export_root() / str(export_id)


def bundle_file(export_id):
    return export_directory(export_id) / "bundle.json"


def validation_directory(validation):
    return (
        export_directory(validation.fhir_export_id) / "validations" / str(validation.id)
    )


def file_sha256(path):
    digest = hashlib.sha256()

    with open(path, "rb") as stream:
        for chunk in iter(
            lambda: stream.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def write_json_atomically(path, payload):
    """
    Prevent readers from observing a partially
    written JSON file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temporary_name = tempfile.mkstemp(
        prefix=".fhir-",
        suffix=".json",
        dir=path.parent,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(
                payload,
                stream,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            stream.write("\n")

        os.replace(temporary_name, path)

    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def process_fhir_export(export_id):
    """
    Called only after the worker claims the export
    and changes its status to RUNNING.
    """
    export = FHIRExport.objects.select_related("release__product").get(pk=export_id)

    if export.status != FHIRExport.Status.RUNNING:
        raise ValueError("FHIR export must be RUNNING")

    try:
        bundle = build_anc_bundle(
            export.release,
            settings.FHIR_CANONICAL_BASE_URL,
        )

        path = bundle_file(export.id)
        write_json_atomically(path, bundle)

        digest = file_sha256(path)

        resources = [entry.get("resource", {}) for entry in bundle.get("entry", [])]

        resource_summary = dict(
            Counter(resource.get("resourceType", "Unknown") for resource in resources)
        )

        with transaction.atomic():
            export = FHIRExport.objects.select_for_update().get(pk=export_id)

            export.bundle_path = str(path)
            export.bundle_sha256 = digest
            export.resource_count = len(resources)
            export.resource_summary = resource_summary

            export.status = FHIRExport.Status.SUCCEEDED
            export.finished_at = timezone.now()
            export.error_message = ""

            export.save()

            export = FHIRExport.objects.get(pk=export_id)

            record_audit_event(
                action=(
                    "FHIR_EXPORT_SUCCEEDED"
                    if export.status == FHIRExport.Status.SUCCEEDED
                    else "FHIR_EXPORT_FAILED"
                ),
                outcome=(
                    AuditEvent.Outcome.SUCCESS
                    if export.status == FHIRExport.Status.SUCCEEDED
                    else AuditEvent.Outcome.FAILURE
                ),
                actor=export.requested_by,
                resource_type="FHIRExport",
                resource_id=export.id,
                correlation_id=export.id,
                details={
                    "releaseId": str(export.release_id),
                    "resourceCount": export.resource_count,
                    "finalStatus": export.status,
                },
            )

        logger.info(
            "FHIR export %s succeeded: %s resources",
            export_id,
            len(resources),
        )

        return export.status

    except Exception as exc:
        logger.exception(
            "FHIR export %s failed",
            export_id,
        )

        with transaction.atomic():
            export = FHIRExport.objects.select_for_update().get(pk=export_id)
            export.status = FHIRExport.Status.FAILED
            export.finished_at = timezone.now()
            export.error_message = (f"{type(exc).__name__}: {exc}")[:2000]
            export.save()

        return FHIRExport.Status.FAILED


def persist_validation_issues(validation, issues):
    objects = []

    for issue in issues:
        source = issue.get("source", "APPLICATION")
        severity = issue.get("severity", "information")

        expression = issue.get("expression") or []

        if isinstance(expression, str):
            expression = [expression]

        objects.append(
            FHIRValidationIssue(
                validation=validation,
                source=source,
                severity=severity,
                code=issue.get("code", ""),
                diagnostics=issue.get("diagnostics", ""),
                expression=expression,
                # Resource attribution can be improved
                # later by resolving Bundle.entry paths.
                resource_type="",
                resource_id="",
            )
        )

    FHIRValidationIssue.objects.bulk_create(
        objects,
        batch_size=500,
    )


def process_fhir_validation(validation_id):
    """
    Executes the official HL7 validator on an
    existing, unmodified FHIR Bundle.
    """
    validation = FHIRValidationResult.objects.select_related("fhir_export").get(
        pk=validation_id
    )

    if validation.status != FHIRValidationResult.Status.RUNNING:
        raise ValueError("FHIR validation must be RUNNING")

    try:
        export = validation.fhir_export

        if export.status != FHIRExport.Status.SUCCEEDED:
            raise ValueError("FHIR export has not completed successfully.")

        path = bundle_file(export.id)

        if not path.is_file():
            raise FileNotFoundError("The generated FHIR Bundle could not be found.")

        actual_sha256 = file_sha256(path)

        if actual_sha256 != export.bundle_sha256:
            raise ValueError(
                "FHIR Bundle checksum mismatch. Validation has been blocked."
            )

        output_dir = validation_directory(validation)

        report = validate_bundle(
            bundle_path=str(path),
            validator_jar=settings.FHIR_VALIDATOR_JAR,
            output_dir=str(output_dir),
            java=settings.FHIR_JAVA_COMMAND,
            timeout_seconds=settings.FHIR_VALIDATOR_TIMEOUT,
            validator_version=settings.FHIR_VALIDATOR_VERSION,
            tx=getattr(
                settings,
                "FHIR_TERMINOLOGY_SERVER",
                None,
            ),
        )

        counts = report.get("counts", {})
        classification = report.get(
            "classification",
            "BLOCKED",
        )

        # A real validator failure remains BLOCKED.
        # Never classify it as conformant.
        with transaction.atomic():
            validation = FHIRValidationResult.objects.select_for_update().get(
                pk=validation_id
            )

            validation.issues.all().delete()

            persist_validation_issues(
                validation,
                report.get("issues", []),
            )

            validation.validator_name = report.get(
                "validator",
                "HL7 FHIR Validator CLI",
            )
            validation.validator_version = report.get(
                "validator_version",
                "",
            )
            validation.fhir_version = report.get(
                "fhir_version",
                "4.0.1",
            )
            validation.bundle_sha256 = actual_sha256

            validation.validator_return_code = report.get("validator_return_code")

            validation.fatal_count = counts.get("fatal", 0)
            validation.error_count = counts.get("error", 0)
            validation.warning_count = counts.get("warning", 0)
            validation.information_count = counts.get("information", 0)

            validation.classification = classification

            validation.report_path = str(output_dir / "conformity_report.json")

            validation.operation_outcome_path = report.get("raw_validator_result") or ""

            validation.console_log_path = report.get("console_log") or ""

            validation.status = (
                FHIRValidationResult.Status.COMPLETED
                if report.get("validator_completed")
                else FHIRValidationResult.Status.FAILED
            )

            validation.finished_at = timezone.now()

            validation.error_message = report.get("validator_failure") or ""

            validation.save()

            validation = FHIRValidationResult.objects.get(pk=validation_id)

            record_audit_event(
                action=(
                    "FHIR_VALIDATION_COMPLETED"
                    if validation.status == FHIRValidationResult.Status.COMPLETED
                    else "FHIR_VALIDATION_FAILED"
                ),
                outcome=(
                    AuditEvent.Outcome.SUCCESS
                    if validation.status == FHIRValidationResult.Status.COMPLETED
                    else AuditEvent.Outcome.FAILURE
                ),
                actor=validation.requested_by,
                resource_type="FHIRValidationResult",
                resource_id=validation.id,
                correlation_id=validation.id,
                details={
                    "fhirExportId": str(validation.fhir_export_id),
                    "classification": validation.classification,
                    "errorCount": validation.error_count,
                    "warningCount": validation.warning_count,
                },
            )

        logger.info(
            "FHIR validation %s: %s",
            validation_id,
            classification,
        )

        return validation.status

    except Exception as exc:
        logger.exception(
            "FHIR validation %s failed",
            validation_id,
        )

        with transaction.atomic():
            validation = FHIRValidationResult.objects.select_for_update().get(
                pk=validation_id
            )

            validation.status = FHIRValidationResult.Status.FAILED
            validation.classification = FHIRValidationResult.Classification.BLOCKED

            validation.finished_at = timezone.now()
            validation.error_message = (f"{type(exc).__name__}: {exc}")[:2000]

            validation.save()

        return FHIRValidationResult.Status.FAILED
