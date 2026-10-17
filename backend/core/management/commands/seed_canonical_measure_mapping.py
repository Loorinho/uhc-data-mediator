from django.core.management.base import BaseCommand
from django.db import transaction

from core.interoperability.models import (
    CanonicalMeasure,
    MeasureSourceMapping,
)

class Command(BaseCommand):
    help = "Seed the ANC first visits canonical measure and DHIS2 source mapping."

    @transaction.atomic
    def handle(self, *args, **options):
        measure, measure_created = CanonicalMeasure.objects.update_or_create(
            code="ANC_FIRST_VISITS",
            defaults={
                "name": "ANC first visits",
                "description": (
                    "Reported first antenatal care visits "
                    "during the specified reporting period."
                ),
                "unit": CanonicalMeasure.Unit.VISITS,
                "aggregation_method": CanonicalMeasure.Aggregation.SUM,
                "definition": {
                    "category": "maternal_health",
                    "geographic_grain": "district",
                    "period_grain": "year_or_month",
                    "is_coverage_percentage": False,
                    "population_denominator": None,
                },
                "is_active": True,
            },
        )

        mapping, mapping_created = MeasureSourceMapping.objects.update_or_create(
            source="DHIS2-SL-DEMO",
            source_measure_id="fbfJHSPpUQD",
            defaults={"measure": measure},
        )

        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if measure_created else 'Updated'} canonical measure: {measure.code}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if mapping_created else 'Updated'} mapping: "
            f"{mapping.source}/{mapping.source_measure_id} -> {measure.code}"
        ))