import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command, get_commands
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Initialize all required UHC Data Mediator "
        "reference data, users, and product definitions."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--owner-username",
            default=None,
            help=(
                "Username of the data product owner. Defaults to SEED_ADMIN_USERNAME."
            ),
        )

        parser.add_argument(
            "--population-csv",
            default=str(
                Path(settings.BASE_DIR)
                / "core"
                / "ingestion"
                / "data"
                / "sierra_leone_district_population_2021.csv"
            ),
            help="Path to the 2021 census CSV.",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "\n===================================="
                "\n  UHC DATA MEDIATOR INITIALIZATION"
                "\n===================================="
            )
        )

        admin_username = os.environ.get("SEED_ADMIN_USERNAME", "").strip()

        admin_password = os.environ.get("SEED_ADMIN_PASSWORD", "")

        owner_username = options["owner_username"] or admin_username

        population_csv = Path(options["population_csv"]).resolve()

        # ----------------------------------
        # 1. Validate configuration
        # ----------------------------------

        if not admin_username:
            raise CommandError("SEED_ADMIN_USERNAME is not configured.")

        if not admin_password:
            raise CommandError("SEED_ADMIN_PASSWORD is not configured.")

        if not owner_username:
            raise CommandError("A data product owner username is required.")

        if not population_csv.is_file():
            raise CommandError(f"Population CSV does not exist: {population_csv}")

        # ----------------------------------
        # 2. Define initialization steps
        # ----------------------------------

        steps = [
            {
                "name": "Initialize administrator",
                "command": "seed",
                "args": [],
                "kwargs": {},
            },
            {
                "name": "Seed DHIS2 districts",
                "command": "seed_districts",
                "args": [],
                "kwargs": {},
            },
            {
                "name": "Import 2021 census population",
                "command": "import_population",
                "args": [str(population_csv)],
                "kwargs": {},
            },
            {
                "name": "Seed canonical measure mappings",
                "command": "seed_canonical_measure_mapping",
                "args": [],
                "kwargs": {},
            },
            {
                "name": "Seed ANC data product definition",
                "command": "seed_data_products",
                "args": [],
                "kwargs": {
                    "owner_username": owner_username,
                },
            },
            {
                "name": "Seed population data product",
                "command": "seed_population_product",
                "args": [],
                "kwargs": {
                    "owner_username": owner_username,
                },
            },
            {
                "name": "Seed geographic crosswalks",
                "command": "seed_geographic_crosswalks",
                "args": [],
                "kwargs": {},
            },
        ]

        # ----------------------------------
        # 3. Check management commands
        # ----------------------------------

        registered_commands = get_commands()

        missing_commands = [
            step["command"]
            for step in steps
            if step["command"] not in registered_commands
        ]

        if missing_commands:
            raise CommandError(
                "Missing management commands: " + ", ".join(missing_commands)
            )

        # ----------------------------------
        # 4. Run initialization
        # ----------------------------------

        total_steps = len(steps)
        completed_steps = []

        User = get_user_model()

        for index, step in enumerate(steps, start=1):
            command_name = step["command"]
            description = step["name"]

            self.stdout.write(f"\n[{index}/{total_steps}] {description}")

            try:
                call_command(
                    command_name,
                    *step["args"],
                    **step["kwargs"],
                    stdout=self.stdout,
                    stderr=self.stderr,
                )

                # Check the owner immediately after
                # the administrator has been seeded.
                if command_name == "seed":
                    owner_exists = User.objects.filter(username=owner_username).exists()

                    if not owner_exists:
                        raise CommandError(
                            "Data product owner "
                            f"'{owner_username}' does not exist. "
                            "Create the user before continuing "
                            "or supply a valid --owner-username."
                        )

                completed_steps.append(description)

                self.stdout.write(self.style.SUCCESS(f"SUCCESS: {description}"))

            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"\nFAILED: {description}"))

                self.stderr.write(f"Completed: {len(completed_steps)}/{total_steps}")

                raise CommandError(
                    f"Initialization stopped at '{command_name}': {exc}"
                ) from exc

        # ----------------------------------
        # 5. Completion summary
        # ----------------------------------

        self.stdout.write(
            self.style.SUCCESS(
                "\n===================================="
                "\n  INITIALIZATION COMPLETED"
                "\n===================================="
            )
        )

        self.stdout.write(f"Completed steps: {len(completed_steps)}/{total_steps}")

        self.stdout.write(f"Administrator: {admin_username}")

        self.stdout.write(f"Data product owner: {owner_username}")

        self.stdout.write(f"Population dataset: {population_csv}")
