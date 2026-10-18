"""
Command that triggers FHIR generation
for a specified ANC data product release.
"""

import hashlib
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.governance.models import DataProductRelease
from core.interoperability.services.fhir.builder import build_anc_bundle


class Command(BaseCommand):
    help = "Generate a FHIR R4 collection bundle from a canonical ANC release (not validated)."

    def add_arguments(self, parser):
        parser.add_argument("release_id", help="UUID of the ANC data product release")
        parser.add_argument("--output", required=True, help="Output JSON path")

    def handle(self, *args, **options):
        try:
            release = DataProductRelease.objects.select_related("product").get(
                pk=options["release_id"]
            )
        except (DataProductRelease.DoesNotExist, ValueError) as exc:
            raise CommandError("Release not found") from exc
        base = getattr(settings, "FHIR_CANONICAL_BASE_URL", "")
        if not base:
            raise CommandError(
                "Set FHIR_CANONICAL_BASE_URL to an HTTPS URL controlled by your project"
            )
        try:
            bundle = build_anc_bundle(release, base)
            payload = json.dumps(bundle, indent=2, ensure_ascii=False) + "\n"
            target = Path(options["output"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(payload, encoding="utf-8")
        except (ValueError, OSError) as exc:
            raise CommandError(f"FHIR export blocked: {exc}") from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Generated {len(bundle['entry'])} FHIR resources -> {target}"
            )
        )
        self.stdout.write(
            f"SHA-256: {hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
        )
        self.stdout.write(
            "Conformity: NOT VALIDATED. Run the HL7 validator before claiming compliance."
        )
