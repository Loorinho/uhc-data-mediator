from django.core.management.base import BaseCommand, CommandError

from core.interoperability.services.population_transformer import transform_population


class Command(BaseCommand):
    help = "Transform imported 2021 census district populations into a canonical product release."

    def handle(self, *args, **options):
        try:
            release, created = transform_population(year=2021)
        except Exception as exc:
            raise CommandError(f"Population transformation failed: {exc}") from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"{'Created' if created else 'Reused'} release {release.id} "
                f"(v{release.version}, status={release.status}, "
                f"transformation={release.transformation_status})"
            )
        )
