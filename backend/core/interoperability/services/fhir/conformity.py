"""FHIR R4 validation runner and evidence report.

Requires official HL7 validator CLI jar and Java in the execution environment.
Never classifies a missing/failed validator invocation as conformant.

What it does
    Executes the HL7 validator, interprets its OperationOutcome,
    performs additional checks, and generates a conformity report

"""

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

FHIR_VERSION = "4.0.1"


def _read_outcomes(payload):
    if isinstance(payload, dict) and payload.get("resourceType") == "OperationOutcome":
        return [payload]
    if isinstance(payload, dict) and payload.get("resourceType") == "Bundle":
        return [
            entry["resource"]
            for entry in payload.get("entry", [])
            if isinstance(entry.get("resource"), dict)
            and entry["resource"].get("resourceType") == "OperationOutcome"
        ]
    return []


def _semantic_checks(bundle):
    issues = []
    if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
        return [
            {
                "source": "APPLICATION",
                "severity": "error",
                "code": "structure",
                "diagnostics": "Expected a FHIR Bundle",
            }
        ]
    entries = bundle.get("entry", [])
    if not isinstance(entries, list):
        return [
            {
                "source": "APPLICATION",
                "severity": "error",
                "code": "structure",
                "diagnostics": "Bundle.entry must be an array",
            }
        ]
    full_urls = [e.get("fullUrl") for e in entries if isinstance(e, dict)]
    duplicates = [u for u, n in Counter(full_urls).items() if u and n > 1]
    for url in duplicates:
        issues.append(
            {
                "source": "APPLICATION",
                "severity": "error",
                "code": "duplicate",
                "diagnostics": f"Duplicate Bundle.entry.fullUrl: {url}",
            }
        )
    locations = {
        e.get("fullUrl")
        for e in entries
        if isinstance(e, dict)
        and isinstance(e.get("resource"), dict)
        and e["resource"].get("resourceType") == "Location"
    }
    for ix, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        res = entry.get("resource") or {}
        if res.get("resourceType") != "Observation":
            continue
        if res.get("subject", {}).get("reference") not in locations:
            issues.append(
                {
                    "source": "APPLICATION",
                    "severity": "error",
                    "code": "not-found",
                    "diagnostics": f"Observation entry[{ix}]: subject Location reference not in Bundle",
                }
            )
        if res.get("code", {}).get("coding", [{}])[0].get("code") == "ANC_FIRST_VISITS":
            issues.append(
                {
                    "source": "APPLICATION",
                    "severity": "warning",
                    "code": "business-rule",
                    "diagnostics": f"Observation entry[{ix}]: ANC first visits is a reported activity count, not ANC coverage; do not infer coverage.",
                }
            )
    return issues


def validate_bundle(
    bundle_path,
    validator_jar,
    output_dir,
    java="java",
    timeout_seconds=300,
    validator_version="UNRECORDED",
    tx=None,
):
    source = Path(bundle_path).resolve()
    jar = Path(validator_jar).resolve()
    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if not source.is_file():
        raise FileNotFoundError(f"Bundle does not exist: {source}")
    sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    report_file = destination / "conformity_report.json"
    validator_result = destination / "validator_operation_outcome.json"
    log_path = destination / "validator_console.log"
    issues = []
    validator_completed = False
    failure = None
    return_code = None
    command = [
        java,
        "-jar",
        str(jar),
        str(source),
        "-version",
        FHIR_VERSION,
        "-output",
        str(validator_result),
    ]
    if tx:
        command.extend(["-tx", tx])

    try:
        bundle = json.loads(source.read_text(encoding="utf-8"))
        application_issues = _semantic_checks(bundle)
    except (ValueError, OSError) as exc:
        bundle = None
        application_issues = [
            {
                "source": "APPLICATION",
                "severity": "error",
                "code": "invalid",
                "diagnostics": str(exc),
            }
        ]

    if not jar.is_file():
        failure = f"HL7 validator JAR not found: {jar}"
    else:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            return_code = result.returncode
            log_path.write_text(
                result.stdout + "\n--- STDERR ---\n" + result.stderr, encoding="utf-8"
            )
            if validator_result.is_file():
                try:
                    parsed = json.loads(validator_result.read_text(encoding="utf-8"))
                    outcomes = _read_outcomes(parsed)
                    if outcomes:
                        validator_completed = True
                        for outcome in outcomes:
                            for issue in outcome.get("issue", []):
                                issues.append(
                                    {
                                        "source": "HL7_VALIDATOR",
                                        "severity": issue.get("severity", "error"),
                                        "code": issue.get("code", "unknown"),
                                        "diagnostics": issue.get("diagnostics")
                                        or (issue.get("details") or {}).get("text")
                                        or "",
                                        "expression": issue.get("expression", []),
                                    }
                                )
                    else:
                        failure = "Validator output did not contain an OperationOutcome; review raw output."
                except (ValueError, OSError) as exc:
                    failure = f"Cannot read validator OperationOutcome: {exc}"
            else:
                failure = "Validator did not produce an output JSON file."
            # Validator may return nonzero when actual validation errors occurred;
            # those are classed NON_CONFORMANT if a usable OperationOutcome exists.
        except (OSError, subprocess.TimeoutExpired) as exc:
            failure = f"Validator invocation failed: {exc}"

    issues.extend(application_issues)
    summary = Counter(i["severity"].lower() for i in issues)
    if not validator_completed:
        conformity = "BLOCKED"
    elif summary["fatal"] or summary["error"]:
        conformity = "NON_CONFORMANT"
    elif summary["warning"]:
        conformity = "CONFORMANT_WITH_WARNINGS"
    else:
        conformity = "CONFORMANT"

    report = {
        "fhir_version": FHIR_VERSION,
        "validation_target": "HL7 FHIR R4 base specification",
        "validator": "HL7 FHIR Validator CLI",
        "validator_version": validator_version,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "bundle_path": str(source),
        "bundle_sha256": sha256,
        "validator_completed": validator_completed,
        "validator_return_code": return_code,
        "validator_failure": failure,
        "classification": conformity,
        "counts": {s: summary[s] for s in ("fatal", "error", "warning", "information")},
        "issues": issues,
        "raw_validator_result": str(validator_result)
        if validator_result.exists()
        else None,
        "console_log": str(log_path) if log_path.exists() else None,
    }
    report_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
