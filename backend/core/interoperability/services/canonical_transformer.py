
import hashlib
import json
import re

from django.db import transaction
from django.utils import timezone

from core.ingestion.models import (
    AcquisitionAttempt,
    Observation,
)
from core.interoperability.models import (
    CanonicalObservation,
    MeasureSourceMapping,
)
from core.governance.models import DataProductRelease


def period_type(period):
    if re.fullmatch(r"\d{4}", period):
        return CanonicalObservation.PeriodType.YEAR

    if re.fullmatch(r"\d{6}", period):
        month = int(period[4:6])
        if 1 <= month <= 12:
            return CanonicalObservation.PeriodType.MONTH

    if re.fullmatch(r"\d{4}Q[1-4]", period):
        return CanonicalObservation.PeriodType.QUARTER

    raise ValueError(f"Unsupported period: {period}")


def normalize_dimensions(dimensions):
    # Our first product is district/annual activity.
    # Do not silently transform breakdowns that
    # have not been defined in the canonical schema.
    if dimensions:
        raise ValueError(
            "Additional dimensions require an explicit "
            "canonical mapping before transformation."
        )

    return {}


def hash_dimensions(dimensions):
    canonical = json.dumps(
        dimensions,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def transform_release(release_id):
    release = (
        DataProductRelease.objects
        .select_related("source_acquisition", "product")
        .get(pk=release_id)
    )

    if release.status != DataProductRelease.Status.DRAFT:
        raise ValueError("Only DRAFT releases can be transformed")

    acquisition = release.source_acquisition

    if acquisition.status not in (
        AcquisitionAttempt.Status.SUCCEEDED,
        AcquisitionAttempt.Status.PARTIAL,
    ):
        raise ValueError(
            "Acquisition has no completed usable result"
        )

    config = acquisition.request_config or {}

    source = acquisition.source

    observations = list(
        Observation.objects
        .select_related("district")
        .filter(attempt=acquisition)
        .order_by("id")
    )

    # Because ingestion observations are upserted,
    # older attempts may no longer own their rows.
    # Do not silently publish an incomplete snapshot.
    if len(observations) != acquisition.records_saved:
        raise ValueError(
            "Source observations no longer match this "
            "acquisition. Rebuild from an immutable "
            "acquisition snapshot or use a fresh acquisition."
        )

    mappings = {
        item.source_measure_id: item.measure
        for item in MeasureSourceMapping.objects
        .select_related("measure")
        .filter(source=source)
    }

    transformed = []

    expected_periods = set(config.get("periods", []))
    expected_units = set(config.get("org_unit_ids", []))
    expected_measures = set(config.get("dx_ids", []))

    for source_row in observations:
        if source_row.indicator_id not in expected_measures:
            raise ValueError("Unexpected source measure")

        if source_row.period not in expected_periods:
            raise ValueError("Unexpected source period")

        if source_row.org_unit_id not in expected_units:
            raise ValueError("Unexpected source geography")

        if source_row.indicator_id not in mappings:
            raise ValueError(
                "No canonical measure mapping for "
                f"{source_row.indicator_id}"
            )

        if source_row.district_id is None:
            raise ValueError("Unmapped district")

        if (
            source_row.district.dhis2_org_unit_id
            != source_row.org_unit_id
        ):
            raise ValueError("District identity mismatch")

        if (
            source_row.district.mapping_status
            != "VERIFIED"
        ):
            raise ValueError(
                "District mapping is not verified"
            )

        dimensions = normalize_dimensions(
            source_row.dimensions
        )

        transformed.append(
            CanonicalObservation(
                release=release,
                measure=mappings[source_row.indicator_id],
                district=source_row.district,
                period=source_row.period,
                period_type=period_type(source_row.period),
                value=source_row.value,
                dimensions=dimensions,
                dimensions_hash=hash_dimensions(dimensions),
                schema_version=release.schema_version,
                source_observation=source_row,
            )
        )

    with transaction.atomic():
        locked_release = (
            DataProductRelease.objects
            .select_for_update()
            .get(pk=release_id)
        )

        if locked_release.status != "DRAFT":
            raise ValueError(
                "Release changed while transforming"
            )

        if locked_release.observations.exists():
            raise ValueError(
                "Release already contains observations"
            )

        CanonicalObservation.objects.bulk_create(
            transformed
        )

        locked_release.transformation_status = (
            DataProductRelease.TransformationStatus.SUCCEEDED
        )

        locked_release.refresh_date = timezone.now()

        locked_release.geographic_coverage = {
            "level": "DISTRICT",
            "requested_org_units": sorted(expected_units),
            "observed_districts": sorted({
                row.district.name for row in transformed
            }),
            "expected_count": len(expected_units),
            "observed_count": len({
                row.district_id for row in transformed
            }),
        }

        locked_release.temporal_coverage = {
            "requested_periods": sorted(expected_periods),
            "observed_periods": sorted({
                row.period for row in transformed
            }),
        }

        locked_release.lineage = {
            "source": source,
            "acquisition_id": str(acquisition.id),
            "correlation_id": str(
                acquisition.correlation_id
            ),
            "canonical_schema_version": (
                locked_release.schema_version
            ),
            "transformation": (
                "district-activity-v1"
            ),
            "source_measure_ids": sorted(expected_measures),
        }

        # Transformation completed, but quality review
        # and publication have not occurred yet.
        locked_release.status = (
            DataProductRelease.Status.VALIDATING
        )
        locked_release.quality_status = (
            DataProductRelease.QualityStatus.NOT_CHECKED
        )
        locked_release.save()

    return len(transformed)
