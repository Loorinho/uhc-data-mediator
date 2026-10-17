from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.ingestion.services.population_importer import (
    PopulationImportConflict,
    import_population_csv,
)


class Command(BaseCommand):
    help = "Import validated Sierra Leone 2021 district population from CSV"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path", help="Path to census CSV inside the API container"
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        try:
            summary = import_population_csv(
                options["csv_path"], dry_run=options["dry_run"]
            )
        except (ValueError, OSError, PopulationImportConflict) as exc:
            raise CommandError(str(exc)) from exc
        prefix = "DRY RUN (no changes): " if options["dry_run"] else "Imported: "
        self.stdout.write(self.style.SUCCESS(prefix + str(summary)))
