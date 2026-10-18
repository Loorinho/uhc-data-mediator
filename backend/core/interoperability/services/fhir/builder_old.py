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

from django.utils import timezone

from .mapping_old import FHIR_VERSION, MEASURES, period_for, quantity, stable_id


def urn(resource):
    return f"urn:uuid:{resource['id']}"


def build_anc_bundle(release, canonical_base):
    if release.product.code != "sl-district-anc-activity":
        raise ValueError("F1 supports only sl-district-anc-activity")
    if release.transformation_status != "SUCCEEDED":
        raise ValueError("Release transformation must have SUCCEEDED")
    if release.status == "REJECTED" or release.quality_status == "FAILED":
        raise ValueError("Rejected or quality-failed release cannot be exported")
    if not canonical_base.startswith("https://"):
        raise ValueError(
            "FHIR_CANONICAL_BASE_URL must be an HTTPS URL under your control"
        )
    canonical_base = canonical_base.rstrip("/")
    code_system = f"{canonical_base}/CodeSystem/uhc-measures"
    district_system = f"{canonical_base}/NamingSystem/uhc-districts"
    obs_system = f"{canonical_base}/NamingSystem/uhc-observations"
    source_system = f"{canonical_base}/NamingSystem/dhis2-orgunits"
    release_system = f"{canonical_base}/NamingSystem/data-product-releases"
    acquisition_system = f"{canonical_base}/NamingSystem/acquisitions"
    data = list(
        release.observations.select_related(
            "measure", "district", "source_observation"
        ).order_by("district__name", "measure_id", "period", "id")
    )
    if not data:
        raise ValueError("Release has no canonical observations")
    if any(x.measure.code not in MEASURES for x in data):
        raise ValueError("Release contains measures without FHIR mapping")
    entries = []

    def add(resource):
        entries.append({"fullUrl": urn(resource), "resource": resource})

    # Identifies the software responsible for
    # generating the FHIR representation
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
            {"name": "UHC Data Mediator FHIR R4 Exporter", "type": "user-friendly-name"}
        ],
        "status": "active",
    }
    add(device)

    # Represents the districts associated with the observations
    locations = {}

    # Represents the district-level ANC first-visit counts
    observations = []

    for x in data:
        district = x.district
        if district.id not in locations:
            location = {
                "resourceType": "Location",
                "id": stable_id("district", district.id),
                "status": "active",
                "name": district.name,
                "mode": "instance",
                "identifier": [{"system": district_system, "value": str(district.id)}],
            }
            if district.dhis2_org_unit_id:
                location["identifier"].append(
                    {"system": source_system, "value": district.dhis2_org_unit_id}
                )
            locations[district.id] = location
            add(location)
        definition = MEASURES[x.measure.code]
        obs = {
            "resourceType": "Observation",
            "id": stable_id("observation", x.id, release.id),
            "identifier": [{"system": obs_system, "value": str(x.id)}],
            # Governance state is distinct from FHIR Observation lifecycle.
            "status": "final" if release.status == "PUBLISHED" else "preliminary",
            "code": {
                "coding": [
                    {
                        "system": code_system,
                        "code": x.measure.code,
                        "display": definition["display"],
                    }
                ],
                "text": x.measure.name,
            },
            "subject": {
                "reference": urn(locations[district.id]),
                "display": district.name,
            },
            "effectivePeriod": period_for(x),
            "valueQuantity": quantity(x.value, definition["unit_display"]),
        }
        if x.source_observation_id is None:
            raise ValueError(f"ANC observation {x.id} has no DHIS2 source observation")
        add(obs)
        observations.append((x, obs))
    for x, obs in observations:
        source = x.source_observation

        # Records how each FHIR Observation relates to its canonical source
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
        }
        add(provenance)
    return {
        "resourceType": "Bundle",
        "id": stable_id("bundle", release.id, "mapping-v1"),
        "type": "collection",
        "timestamp": timezone.now().isoformat(),
        "identifier": {
            "system": f"{canonical_base}/NamingSystem/fhir-exports",
            "value": f"{release.id}:mapping-v1",
        },
        "entry": entries,
    }
