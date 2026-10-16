
from django.core.management.base import BaseCommand
from django.db import transaction

from core.ingestion.models import District


DISTRICT_MAPPINGS = {
    "Bo": "O6uvpzGd5pu",
    "Bombali": "fdc6uOvgoji",
    "Bonthe": "lc3eMKXaEfw",
    "Kailahun": "jUb8gELQApl",
    "Kambia": "PMa2VCrupOd",
    "Kenema": "kJq2mPyFEHo",
    "Koinadugu": "qhqAxPSTUXp",
    "Kono": "Vth0fbpFcsO",
    "Moyamba": "jmIPBj66vD6",
    "Port Loko": "TEQlaapDQoK",
    "Pujehun": "bL4ooGhyHRQ",
    "Tonkolili": "eIQbndfxQMb",
}


class Command(BaseCommand):
    help = "Seed verified Sierra Leone DHIS2 districts"

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for name, org_unit_id in DISTRICT_MAPPINGS.items():
            district, created = District.objects.update_or_create(
                name=name,
                defaults={
                    "dhis2_org_unit_id": org_unit_id,
                    "dhis2_name": name,
                    "mapping_status": District.MappingStatus.VERIFIED,
                    "is_active": True,
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

            self.stdout.write(
                f"{'Created' if created else 'Updated'}: "
                f"{district.name} -> {district.dhis2_org_unit_id}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Completed: {created_count} created, "
                f"{updated_count} updated."
            )
        )
