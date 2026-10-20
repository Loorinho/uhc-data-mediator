"""Replay a previously captured successful LIVE DHIS2 analytics response.

No network, seed command or local fixture JSON is required. The source is a
recorded historical response_payload in PostgreSQL, with provenance recorded
on the replay's request_payload.
"""

import hashlib
import json
import time

from core.ingestion.models import AcquisitionAttempt


def _normalized(values):
    return sorted(values)


def _matching_config(source, dx_ids, periods, org_unit_ids):
    """Require exact query dimensions, never silently substitute other data."""
    config = source.request_config or {}
    if not isinstance(config, dict):
        return False
    return all(
        isinstance(config.get(field), list)
        and _normalized(config[field]) == _normalized(wanted)
        for field, wanted in (
            ("dx_ids", dx_ids),
            ("periods", periods),
            ("org_unit_ids", org_unit_ids),
        )
    )


def fetch_fixture_analytics(*, attempt, dx_ids, periods, org_unit_ids):
    start = time.monotonic()
    # Only original LIVE SUCCEEDED responses are suitable fixture sources.
    # Failed, partial, and fixture-derived acquisitions are never replay sources.
    candidates = (
        AcquisitionAttempt.objects.filter(
            mode=AcquisitionAttempt.Mode.LIVE,
            status=AcquisitionAttempt.Status.SUCCEEDED,
        )
        .exclude(pk=attempt.pk)
        .order_by("-finished_at")
    )

    source = next(
        (
            item
            for item in candidates
            if _matching_config(item, dx_ids, periods, org_unit_ids)
            and isinstance(item.response_payload, dict)
            and isinstance(item.response_payload.get("headers"), list)
            and isinstance(item.response_payload.get("rows"), list)
            and bool(item.response_payload["rows"])
        ),
        None,
    )
    if source is None:
        raise ValueError(
            "No matching successful LIVE DHIS2 acquisition with recorded analytics "
            "headers and rows was found. FIXTURE requires a prior successful LIVE "
            "response with identical measures, periods and district IDs."
        )

    payload = source.response_payload
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    request_info = {
        "method": "FIXTURE_REPLAY",
        "url": f"fixture://acquisitions/{source.pk}",
        "dx_ids": list(dx_ids),
        "periods": list(periods),
        "org_unit_ids": list(org_unit_ids),
        "fixture_source_acquisition_id": str(source.pk),
        "fixture_payload_sha256": digest,
        "fixture_origin": "RECORDED_LIVE_DHIS2_ANALYTICS",
        "is_live_http_response": False,
    }
    # This is a synthetic success code for compatibility with the existing
    # status field, NOT an actual HTTP response from DHIS2.
    return request_info, payload, 200, int((time.monotonic() - start) * 1000)
