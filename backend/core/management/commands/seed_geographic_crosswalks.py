from django.core.management.base import BaseCommand

from core.ingestion.models import District
from core.interoperability.models import GeographicCrosswalk


class Command(BaseCommand):
    help = "Create initial DHIS2 geographic mapping candidates"

    def handle(self, *args, **options):
        created_count = 0

        districts = District.objects.exclude(dhis2_org_unit_id__isnull=True).exclude(
            dhis2_org_unit_id=""
        )

        for district in districts:
            _, created = GeographicCrosswalk.objects.get_or_create(
                source_system=GeographicCrosswalk.SourceSystem.DHIS2,
                source_area_id=district.dhis2_org_unit_id,
                source_geography_year=None,
                target_district=district,
                target_geography_year=2021,
                defaults={
                    "source_area_name": (district.dhis2_name or district.name),
                    "mapping_type": (GeographicCrosswalk.MappingType.UNKNOWN),
                    "verification_status": (
                        GeographicCrosswalk.VerificationStatus.PENDING
                    ),
                    "mapping_notes": (
                        "Initial identifier mapping. "
                        "Administrative boundary compatibility "
                        "with 2021 census geography "
                        "has not been verified."
                    ),
                },
            )

            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_count} pending geographic mappings.")
        )
