import hashlib
import json
import logging
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from core.ingestion.models import (
    AcquisitionAttempt,
    District,
    Observation,
)
from core.ingestion.services.dhis2 import (
    DHIS2RequestError,
    DHIS2Service,
)
from core.ingestion.services.fixture_replay import fetch_fixture_analytics

logger = logging.getLogger(__name__)

SOURCE = "DHIS2-SL-DEMO"


MEASURES = {
    "fbfJHSPpUQD": {
        "name": "ANC 1st visit",
        "type": Observation.MeasureType.DATA_ELEMENT,
    },
    "WHBtsCMZVAE": {
        "name": "Inpatient cases",
        "type": Observation.MeasureType.DATA_ELEMENT,
    },
    "p4K11MFEWtw": {
        "name": "Inpatient malaria cases",
        "type": Observation.MeasureType.DATA_ELEMENT,
    },
    "dy1a1mseGR7": {
        "name": "ANC visits total",
        "type": Observation.MeasureType.INDICATOR,
    },
    "Uvn6LCg7dVU": {
        "name": "ANC 1 Coverage",
        "type": Observation.MeasureType.INDICATOR,
    },
}


def dimensions_hash(dimensions):
    """
    Generate a deterministic SHA256 hash.

    This ensures repeated imports of the same
    observation update the existing record.
    """
    canonical = json.dumps(
        dimensions,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def parse_analytics_rows(payload):
    """
    Normalize DHIS2 analytics rows.

    Example headers:
        dx, pe, ou, value

    Example row:
        fbfJHSPpUQD, 2025, O6uvpzGd5pu, 33765
    """

    headers = [item.get("name") for item in payload.get("headers", [])]

    required = {"dx", "pe", "ou", "value"}

    missing_headers = required - set(headers)

    if missing_headers:
        raise ValueError(
            f"DHIS2 response is missing headers: {sorted(missing_headers)}"
        )

    if len(headers) != len(set(headers)):
        raise ValueError("DHIS2 response contains duplicate headers")

    records = []

    for index, values in enumerate(payload.get("rows", [])):
        if len(values) != len(headers):
            raise ValueError(f"Invalid column count in row {index}")

        row = dict(zip(headers, values))

        try:
            value = Decimal(str(row["value"]))
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            raise ValueError(f"Invalid numeric value in row {index}")

        if not value.is_finite():
            raise ValueError(f"Non-finite value in row {index}")

        dimensions = {
            key: val
            for key, val in row.items()
            if key not in {"dx", "pe", "ou", "value"}
        }

        records.append(
            {
                "indicator_id": row["dx"],
                "period": row["pe"],
                "org_unit_id": row["ou"],
                "value": value,
                "dimensions": dimensions,
                "dimensions_hash": dimensions_hash(dimensions),
            }
        )

    return records


def get_acquisition_config(attempt):
    config = attempt.request_config

    if not isinstance(config, dict) or not config:
        raise ValueError(
            f"Acquisition {attempt.id} has no request_config. "
            "Ensure the POST acquisition handler saves "
            "dx_ids, periods and org_unit_ids when queuing."
        )

    validated = {}

    for name in ("dx_ids", "periods", "org_unit_ids"):
        values = config.get(name)

        if not isinstance(values, list) or not values:
            raise ValueError(
                f"Invalid acquisition configuration: {name}. "
                f"Expected a non-empty list, received "
                f"{type(values).__name__}."
            )

        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError(
                f"Invalid acquisition configuration: {name}. "
                "All items must be non-empty strings."
            )

        normalized = [value.strip() for value in values]

        if len(normalized) != len(set(normalized)):
            raise ValueError(
                f"Invalid acquisition configuration: {name}. "
                "Duplicate values are not allowed."
            )

        validated[name] = normalized

    return (
        validated["dx_ids"],
        validated["periods"],
        validated["org_unit_ids"],
    )


def save_failed_attempt(attempt_id, error):
    """
    Mark a failed acquisition while preserving
    any previously saved DHIS2 request/response.
    """

    with transaction.atomic():
        attempt = AcquisitionAttempt.objects.select_for_update().get(pk=attempt_id)

        attempt.status = AcquisitionAttempt.Status.FAILED
        attempt.outcome = AcquisitionAttempt.Outcome.ERROR
        attempt.finished_at = timezone.now()
        attempt.error_message = str(error)

        if isinstance(error, DHIS2RequestError):
            if error.request_info:
                attempt.request_payload = error.request_info
                attempt.api_url = error.request_info.get("url", "")

            if error.response_body is not None:
                attempt.response_payload = error.response_body

            if error.status_code is not None:
                attempt.http_status_code = error.status_code

        attempt.save()


def process_acquisition(attempt_id):
    """
    Process one claimed LIVE or FIXTURE acquisition.

    The background worker must have set its
    status to RUNNING before calling this.
    """

    attempt = AcquisitionAttempt.objects.get(pk=attempt_id)

    if attempt.status != AcquisitionAttempt.Status.RUNNING:
        raise ValueError("Acquisition must be RUNNING before processing")

    if attempt.mode not in (
        AcquisitionAttempt.Mode.LIVE,
        AcquisitionAttempt.Mode.FIXTURE,
    ):
        raise ValueError(f"Unsupported acquisition mode: {attempt.mode}")

    try:
        dx_ids, periods, org_unit_ids = get_acquisition_config(attempt)

        # Validate requested measures before calling DHIS2.
        unknown_measures = set(dx_ids) - set(MEASURES)

        if unknown_measures:
            raise ValueError(f"Unknown measure metadata: {sorted(unknown_measures)}")

        # Resolve local district mappings.
        districts = {
            district.dhis2_org_unit_id: district
            for district in District.objects.filter(
                dhis2_org_unit_id__in=org_unit_ids,
                mapping_status=(District.MappingStatus.VERIFIED),
                is_active=True,
            )
        }

        unmapped = set(org_unit_ids) - set(districts)

        if unmapped:
            raise ValueError(
                "Some requested organisation units do "
                "not have active, verified district "
                f"mappings: {sorted(unmapped)}"
            )

        # All combinations that should have data.
        expected = {
            (dx, period, org_unit)
            for dx in dx_ids
            for period in periods
            for org_unit in org_unit_ids
        }

        # The worker selects the source, but parsing and persistence remain shared.
        if attempt.mode == AcquisitionAttempt.Mode.FIXTURE:
            request_info, payload, http_status, duration_ms = fetch_fixture_analytics(
                attempt=attempt,
                dx_ids=dx_ids,
                periods=periods,
                org_unit_ids=org_unit_ids,
            )
        else:
            service = DHIS2Service()
            request_info, payload, http_status, duration_ms = service.fetch_analytics(
                dx_ids=dx_ids,
                periods=periods,
                org_unit_ids=org_unit_ids,
            )

        # FIXTURE metadata identifies the original captured LIVE acquisition.
        # Existing Observation upsert semantics are unchanged (see README caveat).
        # Preserve raw DHIS2 response independently
        # from the observation upsert transaction.
        attempt.api_url = request_info["url"]
        attempt.request_payload = request_info
        attempt.response_payload = payload
        attempt.http_status_code = http_status
        attempt.duration_ms = duration_ms

        attempt.save(
            update_fields=[
                "api_url",
                "request_payload",
                "response_payload",
                "http_status_code",
                "duration_ms",
                "updated_at",
            ]
        )

        records = parse_analytics_rows(payload)

        if not records:
            # Capture completeness information even
            # for an empty, valid HTTP 200 response.
            attempt.records_received = 0
            attempt.records_saved = 0
            attempt.expected_combinations = len(expected)
            attempt.received_combinations = 0
            attempt.missing_combinations = [
                {
                    "measure_id": dx,
                    "period": period,
                    "org_unit_id": org_unit,
                }
                for dx, period, org_unit in sorted(expected)
            ]

            attempt.save(
                update_fields=[
                    "records_received",
                    "records_saved",
                    "expected_combinations",
                    "received_combinations",
                    "missing_combinations",
                    "updated_at",
                ]
            )

            raise ValueError(
                "DHIS2 returned zero analytics rows. Missing data is not zero activity."
            )

        # Verify that DHIS2 returned only
        # requested measures, periods and districts.
        received = {
            (
                row["indicator_id"],
                row["period"],
                row["org_unit_id"],
            )
            for row in records
        }

        unexpected = received - expected

        if unexpected:
            raise ValueError(
                f"DHIS2 returned unexpected combinations: {sorted(unexpected)[:10]}"
            )

        # Check duplicate observation identities.
        unique_rows = set()

        for row in records:
            key = (
                row["indicator_id"],
                row["period"],
                row["org_unit_id"],
                row["dimensions_hash"],
            )

            if key in unique_rows:
                raise ValueError(f"Duplicate DHIS2 observation: {key}")

            unique_rows.add(key)

        missing = sorted(expected - received)

        missing_combinations = [
            {
                "measure_id": dx,
                "period": period,
                "org_unit_id": org_unit,
            }
            for dx, period, org_unit in missing
        ]

        # Atomic persistence:
        # either all observations and the final
        # attempt status are saved, or none are.
        with transaction.atomic():
            saved_count = 0

            for row in records:
                district = districts[row["org_unit_id"]]

                metadata = MEASURES[row["indicator_id"]]

                Observation.objects.update_or_create(
                    source=SOURCE,
                    indicator_id=(row["indicator_id"]),
                    org_unit_id=(row["org_unit_id"]),
                    period=row["period"],
                    dimensions_hash=(row["dimensions_hash"]),
                    defaults={
                        "indicator_name": (metadata["name"]),
                        "measure_type": (metadata["type"]),
                        "org_unit_name": (district.name),
                        "district": district,
                        "value": row["value"],
                        "dimensions": (row["dimensions"]),
                        "attempt": attempt,
                    },
                )

                saved_count += 1

            # Acquisition completeness.
            attempt.records_received = len(records)
            attempt.records_saved = saved_count
            attempt.expected_combinations = len(expected)
            attempt.received_combinations = len(received)
            attempt.missing_combinations = missing_combinations

            if missing:
                attempt.status = AcquisitionAttempt.Status.PARTIAL
                attempt.outcome = AcquisitionAttempt.Outcome.INCOMPLETE

                attempt.error_message = (
                    f"Received {len(received)} of "
                    f"{len(expected)} expected "
                    "measure/period/district combinations. "
                    f"{len(missing)} are missing."
                )
            else:
                attempt.status = AcquisitionAttempt.Status.SUCCEEDED
                attempt.outcome = AcquisitionAttempt.Outcome.OK
                attempt.error_message = ""

            attempt.finished_at = timezone.now()

            attempt.save()

        logger.info(
            "Acquisition completed: id=%s, "
            "status=%s, received=%s, saved=%s, "
            "missing=%s",
            attempt_id,
            attempt.status,
            len(records),
            saved_count,
            len(missing),
        )

        return attempt.status

    except Exception as exc:
        logger.exception(
            "Acquisition %s failed",
            attempt_id,
        )

        save_failed_attempt(
            attempt_id=attempt_id,
            error=exc,
        )

        return AcquisitionAttempt.Status.FAILED
