

"""
Discover DHIS2 indicators, data elements and organisation units.

Outputs:
  output/indicators.json
  output/data_elements.json
  output/organisation_units.json
  output/activity_candidates.json
  output/sierra_leone_district_candidates.json
"""

import json
import os
import sys
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

BASE_URL = os.getenv(
    "DHIS2_BASE_URL",
    "https://play.im.dhis2.org/stable-2-43-2",
).rstrip("/")

USERNAME = os.getenv("DHIS2_USERNAME", "admin")
PASSWORD = os.getenv("DHIS2_PASSWORD", "district")

OUTPUT_DIR = Path("output")
PAGE_SIZE = 100

# Broad terms to help identify possible service-activity measures.
ACTIVITY_TERMS = (
    "outpatient",
    "out patient",
    "attendance",
    "consultation",
    "patient visit",
    "health service",
    "service delivery",
    "inpatient",
    "facility visit",
    "maternal",
    "antenatal",
    "delivery",
    "immunization",
    "immunisation",
    "vaccination",
    "malaria",
    "health facility",
)

# Common Sierra Leone district names. These are search hints,
# not assumptions about the DHIS2 hierarchy or its exact naming.
DISTRICT_NAMES = {
    "bo",
    "bombali",
    "bonthe",
    "falaba",
    "kailahun",
    "kambia",
    "karene",
    "kenema",
    "koinadugu",
    "kono",
    "moyamba",
    "port loko",
    "pujehun",
    "tonkolili",
    "western area rural",
    "western area urban",
    "west rural",
    "west urban",
}

session = requests.Session()
session.auth = HTTPBasicAuth(USERNAME, PASSWORD)
session.headers.update({"Accept": "application/json"})


def save_json(filename, data):
    path = OUTPUT_DIR / filename
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved {path} ({len(data)} records)")


def get_json(path, params=None):
    url = f"{BASE_URL}/api/{path.lstrip('/')}"
    response = session.get(url, params=params, timeout=(10, 60))

    if response.status_code in (401, 403):
        raise RuntimeError(
            f"Access denied ({response.status_code}) at {response.url}. "
            "Check the instance URL and credentials, and whether the "
            "account has permission to read metadata."
        )

    response.raise_for_status()
    return response.json()


def get_all(resource, collection, fields):
    """Retrieve all pages for a DHIS2 metadata collection."""
    results = []
    page = 1

    while True:
        payload = get_json(
            f"{resource}.json",
            params={
                "fields": fields,
                "paging": "true",
                "page": page,
                "pageSize": PAGE_SIZE,
                "order": "name:asc",
            },
        )

        items = payload.get(collection, [])
        results.extend(items)

        pager = payload.get("pager", {})
        page_count = pager.get("pageCount")

        print(
            f"\rFetching {resource}: page {page}"
            + (f"/{page_count}" if page_count else ""),
            end="",
            flush=True,
        )

        if not items:
            break

        if page_count is not None:
            if page >= page_count:
                break
        elif len(items) < PAGE_SIZE:
            break

        page += 1

    print()
    return results


def text_of(record):
    """Build searchable text from an object's name and descriptions."""
    return " ".join(
        str(record.get(key) or "")
        for key in (
            "name",
            "displayName",
            "shortName",
            "description",
            "numeratorDescription",
            "denominatorDescription",
        )
    ).lower()


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"DHIS2 instance: {BASE_URL}")
    print("Checking API connectivity...")

    info = get_json("system/info")
    print("Connected to DHIS2.")
    print("Version:", info.get("version", "not reported"))
    print()

    indicators = get_all(
        "indicators",
        "indicators",
        "id,name,displayName,shortName,description,"
        "numerator,denominator,numeratorDescription,"
        "denominatorDescription,indicatorType[id,name],"
        "lastUpdated",
    )

    data_elements = get_all(
        "dataElements",
        "dataElements",
        "id,name,displayName,shortName,description,"
        "aggregationType,domainType,valueType,"
        "categoryCombo[id,name],lastUpdated",
    )

    organisation_units = get_all(
        "organisationUnits",
        "organisationUnits",
        "id,name,displayName,shortName,code,level,"
        "path,parent[id,name],ancestors[id,name,level],"
        "openingDate,closedDate",
    )

    save_json("indicators.json", indicators)
    save_json("data_elements.json", data_elements)
    save_json("organisation_units.json", organisation_units)

    # Search indicator and data-element names separately.
    activity_candidates = {
        "indicators": [
            item for item in indicators
            if any(term in text_of(item) for term in ACTIVITY_TERMS)
        ],
        "data_elements": [
            item for item in data_elements
            if any(term in text_of(item) for term in ACTIVITY_TERMS)
        ],
    }

    save_json("activity_candidates.json", activity_candidates)

    # Keep full hierarchy details so we can identify district-level units.
    district_candidates = []

    for unit in organisation_units:
        name = (unit.get("name") or unit.get("displayName") or "").strip()
        normalized = " ".join(name.lower().split())

        # Match district names exactly, or names with a clear suffix.
        matched = (
            normalized in DISTRICT_NAMES
            or any(
                normalized == f"{district} district"
                for district in DISTRICT_NAMES
            )
        )

        if matched:
            district_candidates.append(unit)

    # Also retain possible country/root entries for hierarchy inspection.
    root_candidates = [
        unit for unit in organisation_units
        if "sierra leone" in (
            (unit.get("name") or "") + " " +
            (unit.get("displayName") or "")
        ).lower()
    ]

    save_json(
        "sierra_leone_district_candidates.json",
        {
            "possible_country_units": root_candidates,
            "district_name_matches": district_candidates,
        },
    )

    print("\n--- POSSIBLE ACTIVITY INDICATORS ---")
    for item in activity_candidates["indicators"]:
        print(
            f'{item.get("id", "")} | '
            f'{item.get("name", item.get("displayName", ""))}'
        )

    print("\n--- POSSIBLE ACTIVITY DATA ELEMENTS ---")
    for item in activity_candidates["data_elements"]:
        print(
            f'{item.get("id", "")} | '
            f'{item.get("name", item.get("displayName", ""))}'
        )

    print("\n--- POSSIBLE DISTRICT ORGANISATION UNITS ---")
    for unit in district_candidates:
        parent = unit.get("parent") or {}
        print(
            f'ID={unit.get("id")} | '
            f'Name={unit.get("name")} | '
            f'Level={unit.get("level")} | '
            f'Parent={parent.get("name", "")}'
        )

    print("\nDiscovery completed.")
    print(f"Inspect the JSON files in: {OUTPUT_DIR.resolve()}")
    print(
        "Important: candidates are based on names. "
        "We must verify their meaning and hierarchy before using them."
    )


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        print(f"\nNetwork/API error: {exc}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, RuntimeError, KeyError) as exc:
        print(f"\nDiscovery failed: {exc}", file=sys.stderr)
        sys.exit(1)
