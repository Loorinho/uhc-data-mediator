"""
FHIR R4 mapping policy.
Codes are LOCAL, not claimed LOINC/SNOMED.

What it does
    Defines how canonical data fields are translated into
    FHIR-compatible values,identifiers, periods and codes.
"""

from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid5

FHIR_VERSION = "4.0.1"
NAMESPACE = UUID("761a826c-9c67-429d-9d5f-d72a10bbbd62")
MEASURES = {
    "ANC_FIRST_VISITS": {
        "display": "Reported antenatal care first visits",
        "unit_display": "visits",
    },
}


def stable_id(kind, *parts):
    return str(uuid5(NAMESPACE, "|".join([kind, *map(str, parts)])))


def period_for(observation):
    raw = observation.period
    kind = observation.period_type
    if kind == "YEAR" and len(raw) == 4 and raw.isdigit():
        year = int(raw)
        return {"start": f"{year:04d}-01-01", "end": f"{year + 1:04d}-01-01"}
    if kind == "MONTH" and len(raw) == 6 and raw.isdigit():
        # Something like 202501. First 4 digits are the year, last 2 are the month.
        year, month = int(raw[:4]), int(raw[4:])
        if not 1 <= month <= 12:
            raise ValueError(f"Invalid month {raw}")
        end_year, end_month = (year + 1, 1) if month == 12 else (year, month + 1)
        return {
            "start": f"{year:04d}-{month:02d}-01",
            "end": f"{end_year:04d}-{end_month:02d}-01",
        }
    if (
        kind == "QUARTER"
        and len(raw) == 6
        and raw[:4].isdigit()
        and raw[4] == "Q"
        and raw[5] in "1234"
    ):
        # Something like 2023Q1. First 4 digits are the year, last 2 indicate the quarter.
        year, quarter = int(raw[:4]), int(raw[5])
        month = (quarter - 1) * 3 + 1
        end_year, end_month = (year + 1, 1) if quarter == 4 else (year, month + 3)
        return {
            "start": f"{year:04d}-{month:02d}-01",
            "end": f"{end_year:04d}-{end_month:02d}-01",
        }
    raise ValueError(f"Unsupported period {raw!r}/{kind!r}")


def quantity(value, unit_display):
    number = Decimal(str(value))
    if not number.is_finite() or number < 0:
        raise ValueError("Negative/non-finite reported count cannot be exported")
    return {
        "value": int(number) if number == number.to_integral_value() else float(number),
        "unit": unit_display,
        "system": "http://unitsofmeasure.org",
        "code": "1",
    }
