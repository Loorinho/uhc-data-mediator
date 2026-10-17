from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.governance.models import DataProduct
from core.interoperability.models import CanonicalMeasure, MeasureSourceMapping

SOURCE = "STATS-SL-2021-MTPHC"
CODE = "sl-district-population"


class Command(BaseCommand):
    help = "Register population canonical measure, source mapping and governed product."

    def add_arguments(self, parser):
        parser.add_argument("--owner-username", required=True)

    @transaction.atomic
    def handle(self, *args, **opts):
        User = get_user_model()
        owner = User.objects.filter(username=opts["owner_username"]).first()
        if not owner:
            raise CommandError("Existing data owner username not found.")
        measure, made = CanonicalMeasure.objects.get_or_create(
            code="TOTAL_POPULATION",
            defaults={
                "name": "Total resident population",
                "description": "Total resident population of a census district in reference year 2021.",
                "unit": CanonicalMeasure.Unit.COUNT,
                "aggregation_method": CanonicalMeasure.Aggregation.SUM,
                "definition": {
                    "measure_kind": "stock",
                    "period_semantics": "reference_year",
                    "population_type": "resident",
                },
                "is_active": True,
            },
        )
        if not measure.is_active or measure.unit != CanonicalMeasure.Unit.COUNT:
            raise CommandError(
                "Existing TOTAL_POPULATION measure is inactive or incompatible."
            )
        mapping, _ = MeasureSourceMapping.objects.get_or_create(
            source=SOURCE,
            source_measure_id="population",
            defaults={"measure": measure},
        )
        if mapping.measure_id != measure.pk:
            raise CommandError("Conflicting census population measure mapping.")
        product, created = DataProduct.objects.get_or_create(
            code=CODE,
            defaults={
                "title": "Sierra Leone District Population",
                "purpose": "Official 2021 census district resident population for transparent comparison with reported health activity.",
                "data_owner": owner,
                "source": SOURCE,
                "schema_version": "1.0.0",
                "sensitivity_classification": DataProduct.Sensitivity.INTERNAL,
                "permitted_evidence": [
                    {
                        "type": "POPULATION_DENOMINATOR",
                        "permitted": True,
                        "condition": "Validate geographic and temporal compatibility before joining activity data",
                    },
                    {"type": "CONTEMPORARY_2025_POPULATION", "permitted": False},
                ],
                "quality_policy": {
                    "require_full_2021_census": True,
                    "expected_district_count": 16,
                    "expected_total_population": 7548702,
                    "require_valid_source_provenance": True,
                },
            },
        )
        if product.source != SOURCE:
            raise CommandError("Existing data product has an incompatible source.")
        self.stdout.write(
            self.style.SUCCESS(
                f"Product {product.code}: {'created' if created else 'existing'}; measure {measure.code}"
            )
        )
