import json

from django.core.management.base import BaseCommand, CommandError

from core.interoperability.services.fhir.conformity import validate_bundle

"""
    Command that triggers validation for an exported Bundle
"""


class Command(BaseCommand):
    help = "Validate an exported FHIR R4 bundle using official HL7 CLI and save conformity evidence."

    def add_arguments(self, parser):
        parser.add_argument("bundle_path")
        parser.add_argument("--validator-jar", required=True)
        parser.add_argument("--output-dir", required=True)
        parser.add_argument("--validator-version", default="UNRECORDED")
        parser.add_argument(
            "--tx", default=None, help="Optional terminology server URL"
        )

    def handle(self, *args, **opts):
        report = validate_bundle(
            bundle_path=opts["bundle_path"],
            validator_jar=opts["validator_jar"],
            output_dir=opts["output_dir"],
            validator_version=opts["validator_version"],
            tx=opts["tx"],
        )
        self.stdout.write(
            json.dumps(
                {
                    "classification": report["classification"],
                    "validator_completed": report["validator_completed"],
                    "counts": report["counts"],
                    "failure": report["validator_failure"],
                },
                indent=2,
            )
        )
        if report["classification"] in ("NON_CONFORMANT", "BLOCKED"):
            raise CommandError(
                f"FHIR conformity status: {report['classification']}. See conformity_report.json"
            )
