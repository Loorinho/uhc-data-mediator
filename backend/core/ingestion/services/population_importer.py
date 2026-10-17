from django.db import transaction

from core.ingestion.models import District, DistrictPopulation
from core.ingestion.services.population_validation import validate_population_csv


class PopulationImportConflict(ValueError):
    pass


def import_population_csv(path, *, dry_run=False):
    rows = validate_population_csv(path)
    counts = {"districts_created": 0, "populations_created": 0, "unchanged": 0}
    # Entire operation rolled back for any conflict; dry run also uses rollback.
    with transaction.atomic():
        for row in rows:
            name = row["district_name"]
            matching = list(
                District.objects.select_for_update().filter(name__iexact=name)[:2]
            )
            if len(matching) > 1:
                raise PopulationImportConflict(f"Multiple district matches for {name}")
            if matching:
                district = matching[0]
            else:
                district = District.objects.create(
                    name=name,
                    mapping_status=District.MappingStatus.UNMAPPED,
                    is_active=True,
                )
                counts["districts_created"] += 1
            existing = (
                DistrictPopulation.objects.select_for_update()
                .filter(district=district, reference_year=row["reference_year"])
                .first()
            )
            notes = (
                f"Region: {row['region']}; male: {row['male_population']}; "
                f"female: {row['female_population']}. "
                "Imported from supplied census CSV; geographic boundaries not yet reconciled."
            )
            if existing:
                if (
                    existing.population != row["population"]
                    or existing.source != row["source"]
                    or existing.source_url != row["source_url"]
                ):
                    raise PopulationImportConflict(
                        f"Conflict for {name} ({row['reference_year']}): existing "
                        "population/provenance differs. No rows were changed."
                    )
                counts["unchanged"] += 1
            else:
                DistrictPopulation.objects.create(
                    district=district,
                    reference_year=row["reference_year"],
                    population=row["population"],
                    source=row["source"],
                    source_url=row["source_url"],
                    source_notes=notes,
                )
                counts["populations_created"] += 1
        if dry_run:
            transaction.set_rollback(True)
    return counts
