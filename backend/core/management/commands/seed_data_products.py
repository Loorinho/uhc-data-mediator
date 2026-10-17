from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from core.governance.models import DataProduct


class Command(BaseCommand):
    help = "Seed the Sierra Leone ANC data product"

    def add_arguments(self, parser):
        parser.add_argument(
            "--owner-username",
            required=True,
            help="Username of the user who will own the data product",
        )

    def handle(self, *args, **options):
        User = get_user_model()

        owner = User.objects.filter(username=options["owner_username"]).first()

        if owner is None:
            raise CommandError(
                "Data product owner was not found. Provide an existing user's username."
            )

        product, created = DataProduct.objects.update_or_create(
            code="sl-district-anc-activity",
            defaults={
                "title": ("Sierra Leone District ANC Service Activity"),
                "purpose": (
                    "Provide standardized district-level "
                    "antenatal care activity data for "
                    "health service monitoring and "
                    "exploratory UHC analysis."
                ),
                "data_owner": owner,
                "source": "DHIS2-SL-DEMO",
                "schema_version": "1.0.0",
                "sensitivity_classification": (DataProduct.Sensitivity.INTERNAL),
                "permitted_evidence": [
                    {
                        "type": "REPORTED_ACTIVITY",
                        "permitted": True,
                        "condition": (
                            "Successful canonical transformation and quality review."
                        ),
                    },
                    {
                        "type": "DISTRICT_COMPARISON",
                        "permitted": True,
                        "condition": (
                            "Disclose geographic coverage and reporting limitations."
                        ),
                    },
                    {
                        "type": "POPULATION_ADJUSTED_ANALYSIS",
                        "permitted": True,
                        "condition": (
                            "Use an appropriate denominator "
                            "and disclose its reference year."
                        ),
                    },
                    {
                        "type": "PROOF_OF_UNDERSERVED_STATUS",
                        "permitted": False,
                    },
                ],
                "quality_policy": {
                    "require_measure_mapping": True,
                    "require_verified_districts": True,
                    "require_valid_values": True,
                    "require_unique_observations": True,
                    "require_lineage": True,
                },
            },
        )

        action = "Created" if created else "Updated"

        self.stdout.write(self.style.SUCCESS(f"{action} data product: {product.code}"))

        self.stdout.write(f"Product ID: {product.id}")

        self.stdout.write(f"Owner: {owner.email}")
