"""
What it does
    Constructs the actual FHIR resources from an ANC Release and combines
    them into a Bundle.

What it doesnt do
    Validate conformance. Validation must run through the official validator.

How it works
    Iterates over the canonical observations in the release,
    constructs FHIR resources for each relevant entity
    (Device, Location, Observation), and aggregates them into a FHIR Bundle.

"""

from html import escape

from django.utils import timezone

from .mapping import MEASURES, period_for, quantity, stable_id


def urn(resource):
    return f"urn:uuid:{resource['id']}"


def narrative(message):
    """FHIR Narrative, with XML-escaped dynamic content."""
    return {
        "status": "generated",
        "div": f'<div xmlns="http://www.w3.org/1999/xhtml"><p>{escape(str(message))}</p></div>',
    }


def build_anc_bundle(release, canonical_base):
    if release.product.code != "sl-district-anc-activity":
        raise ValueError("ANC FHIR exporter supports only sl-district-anc-activity")
    if release.transformation_status != "SUCCEEDED":
        raise ValueError("Release transformation must have SUCCEEDED")
    if release.status == "REJECTED" or release.quality_status == "FAILED":
        raise ValueError("Rejected or quality-failed release cannot be exported")
    if not canonical_base.startswith("https://"):
        raise ValueError("FHIR_CANONICAL_BASE_URL must be a controlled HTTPS namespace")
    canonical_base = canonical_base.rstrip("/")

    code_system_url = f"{canonical_base}/CodeSystem/uhc-measures"
    district_system = f"{canonical_base}/NamingSystem/uhc-districts"
    observation_system = f"{canonical_base}/NamingSystem/uhc-observations"
    source_system = f"{canonical_base}/NamingSystem/dhis2-orgunits"
    release_system = f"{canonical_base}/NamingSystem/data-product-releases"
    acquisition_system = f"{canonical_base}/NamingSystem/acquisitions"

    records = list(
        release.observations.select_related(
            "measure", "district", "source_observation"
        ).order_by("district__name", "measure_id", "period", "id")
    )
    if not records:
        raise ValueError("Release has no canonical observations")
    if any(record.measure.code not in MEASURES for record in records):
        raise ValueError("Release contains measures without an FHIR mapping")

    entries = []

    def add(resource):
        entries.append({"fullUrl": urn(resource), "resource": resource})

    # Local terminology definition. For complete terminology validation,
    # load this CodeSystem separately into the validator / terminology service.
    codesystem = {
        "resourceType": "CodeSystem",
        "id": stable_id("codesystem", code_system_url),
        "url": code_system_url,
        "version": "1.0.0",
        "name": "UHCMeasures",
        "title": "UHC Data Mediator Measures",
        "status": "active",
        "experimental": True,
        "description": "Local measure codes used by the UHC Data Mediator.",
        "caseSensitive": True,
        "content": "complete",
        "concept": [
            {"code": code, "display": definition["display"]}
            for code, definition in sorted(MEASURES.items())
        ],
        "text": narrative("Local terminology for canonical UHC measures"),
    }
    add(codesystem)

    device = {
        "resourceType": "Device",
        "id": stable_id("generator", "uhc-data-mediator"),
        "identifier": [
            {
                "system": f"{canonical_base}/NamingSystem/transformers",
                "value": "uhc-data-mediator",
            }
        ],
        "deviceName": [
            {
                "name": "UHC Data Mediator FHIR R4 Exporter",
                "type": "user-friendly-name",
            }
        ],
        "status": "active",
        "text": narrative("Software: UHC Data Mediator FHIR R4 Exporter"),
    }
    add(device)

    locations = {}
    observations = []

    for record in records:
        district = record.district
        if district.id not in locations:
            location = {
                "resourceType": "Location",
                "id": stable_id("district", district.id),
                "status": "active",
                "name": district.name,
                "mode": "instance",
                "identifier": [
                    {
                        "system": district_system,
                        "value": str(district.id),
                    }
                ],
                # Location.type intentionally omitted: 'JURIS' is not a valid
                # code in the previously selected v3-RoleCode system.
                "text": narrative(f"Reporting geography: {district.name} District"),
            }
            if district.dhis2_org_unit_id:
                location["identifier"].append(
                    {
                        "system": source_system,
                        "value": district.dhis2_org_unit_id,
                    }
                )
            locations[district.id] = location
            add(location)

        if record.source_observation_id is None:
            raise ValueError(
                f"ANC canonical observation {record.id} has no DHIS2 source"
            )
        definition = MEASURES[record.measure.code]
        obs = {
            "resourceType": "Observation",
            "id": stable_id("observation", record.id, release.id),
            "identifier": [
                {
                    "system": observation_system,
                    "value": str(record.id),
                }
            ],
            "status": "final" if release.status == "PUBLISHED" else "preliminary",
            "code": {
                "coding": [
                    {
                        "system": code_system_url,
                        "code": record.measure.code,
                        "display": definition["display"],
                    }
                ],
                "text": record.measure.name,
            },
            "subject": {
                "reference": urn(locations[district.id]),
                "display": district.name,
            },
            "effectivePeriod": period_for(record),
            "valueQuantity": quantity(record.value, definition["unit_display"]),
            "text": narrative(
                f"{definition['display']}: {record.value} {definition['unit_display']} "
                f"for {district.name}; reporting period {record.period}. "
                "This is reported service activity, not ANC coverage."
            ),
        }
        add(obs)
        observations.append((record, obs))

    for record, obs in observations:
        source = record.source_observation
        provenance = {
            "resourceType": "Provenance",
            "id": stable_id("provenance", obs["id"]),
            "target": [{"reference": urn(obs)}],
            "recorded": timezone.now().isoformat(),
            "agent": [{"who": {"reference": urn(device)}}],
            "entity": [
                {
                    "role": "source",
                    "what": {
                        "identifier": {
                            "system": acquisition_system,
                            "value": str(source.attempt_id),
                        },
                        "display": "DHIS2 acquisition supplying the source observation",
                    },
                },
                {
                    "role": "derivation",
                    "what": {
                        "identifier": {
                            "system": release_system,
                            "value": str(release.id),
                        },
                        "display": "Canonical data product release",
                    },
                },
            ],
            "text": narrative(
                f"UHC Data Mediator generated Observation {obs['id']} "
                f"from DHIS2 acquisition {source.attempt_id} "
                f"and canonical release {release.id}."
            ),
        }
        add(provenance)

    return {
        "resourceType": "Bundle",
        "id": stable_id("bundle", release.id, "mapping-v2"),
        "type": "collection",
        "timestamp": timezone.now().isoformat(),
        "identifier": {
            "system": f"{canonical_base}/NamingSystem/fhir-exports",
            "value": f"{release.id}:mapping-v2",
        },
        "entry": entries,
    }
