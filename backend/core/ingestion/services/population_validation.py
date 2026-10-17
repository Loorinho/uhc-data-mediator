import csv
from pathlib import Path

EXPECTED_YEAR = 2021
EXPECTED_DISTRICTS = 16
EXPECTED_TOTAL = 7_548_702
REQUIRED_COLUMNS = {
    "district_name",
    "region",
    "reference_year",
    "male_population",
    "female_population",
    "population",
    "source",
    "source_url",
}


def _parse_nonnegative_int(value, field, district):
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{district}: invalid {field}: {value!r}") from exc
    if number < 0:
        raise ValueError(f"{district}: {field} cannot be negative")
    return number


def validate_population_csv(path):
    rows = []
    district_keys = set()
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not REQUIRED_COLUMNS.issubset(set(reader.fieldnames or [])):
            missing = sorted(REQUIRED_COLUMNS - set(reader.fieldnames or []))
            raise ValueError(f"CSV missing columns: {', '.join(missing)}")
        for line_no, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Line {line_no}: malformed CSV row")
            name = row["district_name"].strip()
            if not name:
                raise ValueError(f"Line {line_no}: district name is empty")
            key = name.casefold()
            if key in district_keys:
                raise ValueError(f"Line {line_no}: duplicate district {name}")
            district_keys.add(key)
            year = _parse_nonnegative_int(row["reference_year"], "reference_year", name)
            male = _parse_nonnegative_int(
                row["male_population"], "male_population", name
            )
            female = _parse_nonnegative_int(
                row["female_population"], "female_population", name
            )
            total = _parse_nonnegative_int(row["population"], "population", name)
            if year != EXPECTED_YEAR or total <= 0 or male + female != total:
                raise ValueError(
                    f"{name}: invalid year, total, or male/female subtotal"
                )
            source = row["source"].strip()
            source_url = row["source_url"].strip()
            if not source or not source_url.startswith("https://"):
                raise ValueError(f"{name}: missing source or HTTPS provenance URL")
            rows.append(
                {
                    "district_name": name,
                    "region": row["region"].strip(),
                    "reference_year": year,
                    "male_population": male,
                    "female_population": female,
                    "population": total,
                    "source": source,
                    "source_url": source_url,
                }
            )
    if len(rows) != EXPECTED_DISTRICTS:
        raise ValueError(f"Expected {EXPECTED_DISTRICTS} districts; found {len(rows)}")
    total = sum(r["population"] for r in rows)
    if total != EXPECTED_TOTAL:
        raise ValueError(f"Expected national total {EXPECTED_TOTAL}; found {total}")
    return rows
