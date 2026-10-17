"""Synchronously create a canonical release from validated census DistrictPopulation rows.

A release is an immutable census snapshot. Existing releases are never overwritten.
"""

import hashlib
import json
import re
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core.governance.models import DataProduct, DataProductRelease
from core.ingestion.models import DistrictPopulation
from core.interoperability.models import (
    CanonicalMeasure,
    CanonicalObservation,
    MeasureSourceMapping,
)

SOURCE = "STATS-SL-2021-MTPHC"
PRODUCT_CODE = "sl-district-population"
EXPECTED_DISTRICTS = 16
EXPECTED_POPULATION = 7548702


def _fingerprint(rows):
    payload = [
        {
            "district_id": str(r.district_id),
            "name": r.district.name,
            "year": r.reference_year,
            "population": r.population,
            "source": r.source,
            "source_url": r.source_url,
        }
        for r in rows
    ]
    content = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(content.encode()).hexdigest()


@transaction.atomic
def transform_population(*, year=2021):
    # Product lock serializes competing release/version creation attempts.
    product = DataProduct.objects.select_for_update().get(code=PRODUCT_CODE)
    if product.source != SOURCE:
        raise ValueError(
            "Population product source differs from expected census source."
        )
    mapping = MeasureSourceMapping.objects.select_related("measure").get(
        source=SOURCE, source_measure_id="population"
    )
    measure = mapping.measure
    if measure.pk != "TOTAL_POPULATION" or not measure.is_active:
        raise ValueError("TOTAL_POPULATION source mapping missing/inactive.")

    rows = list(
        DistrictPopulation.objects.select_related("district")
        .filter(reference_year=year)
        .order_by("district__name", "id")
    )
    if len(rows) != EXPECTED_DISTRICTS:
        raise ValueError(
            f"Expected {EXPECTED_DISTRICTS} population records, found {len(rows)}"
        )
    if sum(r.population for r in rows) != EXPECTED_POPULATION:
        raise ValueError("National census population checksum failed.")
    if len({r.district_id for r in rows}) != EXPECTED_DISTRICTS:
        raise ValueError("Duplicate districts in population input.")
    if not all(r.source and r.source_url for r in rows):
        raise ValueError("Some population records have missing provenance.")
    if year != 2021:
        raise ValueError(
            "Only the verified 2021 census is supported by this transformation."
        )

    fingerprint = _fingerprint(rows)
    for existing in DataProductRelease.objects.filter(product=product).order_by(
        "-version"
    ):
        if existing.lineage.get("source_fingerprint") == fingerprint:
            return existing, False

    last = (
        DataProductRelease.objects.filter(product=product)
        .order_by("-version")
        .values_list("version", flat=True)
        .first()
        or 0
    )
    release = DataProductRelease.objects.create(
        product=product,
        version=last + 1,
        source_acquisition=None,
        schema_version=product.schema_version,
        status=DataProductRelease.Status.DRAFT,
        transformation_status=DataProductRelease.TransformationStatus.RUNNING,
        quality_status=DataProductRelease.QualityStatus.NOT_CHECKED,
        geographic_coverage={
            "source": SOURCE,
            "district_count": len(rows),
            "district_names": [r.district.name for r in rows],
            "boundary_compatibility_with_dhis2": "NOT_ASSESSED",
        },
        temporal_coverage={"reference_year": year, "period_type": "YEAR"},
        refresh_date=timezone.now(),
        lineage={
            "source": SOURCE,
            "source_record_type": "DistrictPopulation",
            "source_fingerprint": fingerprint,
            "source_record_ids": [str(r.pk) for r in rows],
            "source_urls": sorted({r.source_url for r in rows}),
            "transformation": "population_transformer_v1",
        },
    )
    canonical = []
    dimensions = {}
    dimension_hash = hashlib.sha256(b"{}").hexdigest()
    for row in rows:
        canonical.append(
            CanonicalObservation(
                release=release,
                measure=measure,
                district=row.district,
                period=str(year),
                period_type=CanonicalObservation.PeriodType.YEAR,
                value=Decimal(row.population),
                dimensions=dimensions.copy(),
                dimensions_hash=dimension_hash,
                schema_version=release.schema_version,
                source_observation=None,
                source_population=row,
            )
        )
    CanonicalObservation.objects.bulk_create(canonical)
    release.transformation_status = DataProductRelease.TransformationStatus.SUCCEEDED
    release.status = DataProductRelease.Status.VALIDATING
    release.quality_report = {
        "transformation_checks": {
            "district_count": len(rows),
            "national_population": EXPECTED_POPULATION,
            "source_present": True,
        },
        "governance_quality_evaluation": "NOT_RUN",
        "warnings": [
            "Census reference year is 2021; 2025 activity comparisons require temporal disclosure",
            "DHIS2 versus census district boundary compatibility has not been verified",
        ],
    }
    release.save(update_fields=["transformation_status", "status", "quality_report"])
    return release, True
