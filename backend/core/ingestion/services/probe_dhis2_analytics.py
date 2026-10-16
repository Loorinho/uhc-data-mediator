#Data probe 3


import os
import requests

BASE_URL = os.getenv(
    "DHIS2_BASE_URL",
    "https://play.im.dhis2.org/stable-2-43-2",
).rstrip("/")

session = requests.Session()
session.auth = (
    os.getenv("DHIS2_USERNAME", "admin"),
    os.getenv("DHIS2_PASSWORD", "district"),
)
session.headers["Accept"] = "application/json"

DATA_ELEMENT = "fbfJHSPpUQD"  # ANC 1st visit

tests = [
    # ("Facility, July 2025", "GvFqTavdpGE", "202507"),
    # ("Facility, full year 2025", "GvFqTavdpGE", "2025"),
    # ("Bo district, July 2025", "O6uvpzGd5pu", "202507"),
    # ("Bo district, full year 2025", "O6uvpzGd5pu", "2025"),
    ("Facility, July 2026", "GvFqTavdpGE", "202607"),
]

for label, org_unit, period in tests:
    params = [
        ("dimension", f"dx:{DATA_ELEMENT}"),
        ("dimension", f"pe:{period}"),
        ("dimension", f"ou:{org_unit}"),
        ("skipMeta", "false"),
    ]

    try:
        response = session.get(
            f"{BASE_URL}/api/analytics.json",
            params=params,
            timeout=(5, 60),
        )

        print(f"\n--- {label} ---")
        print("HTTP:", response.status_code)
        print("URL:", response.url)

        if not response.ok:
            print("Error:", response.text[:1000])
            continue

        payload = response.json()
        print("Headers:", [
            h.get("name") for h in payload.get("headers", [])
        ])
        print("Rows:", len(payload.get("rows", [])))
        print("Sample:", payload.get("rows", [])[:3])

    except requests.RequestException as exc:
        print("Request error:", exc)
    except ValueError as exc:
        print("Invalid JSON:", exc)





# Data probe 2
# Here, DHIS2 demo contains raw health-service observations for 2025 and 2026, but not for earlier years.
# import os
# import requests

# BASE_URL = os.getenv(
#     "DHIS2_BASE_URL",
#     "https://play.im.dhis2.org/stable-2-43-2",
# ).rstrip("/")

# session = requests.Session()
# session.auth = (
#     os.getenv("DHIS2_USERNAME", "admin"),
#     os.getenv("DHIS2_PASSWORD", "district"),
# )
# session.headers["Accept"] = "application/json"

# DATA_ELEMENT = "fbfJHSPpUQD"  # ANC 1st visit
# FACILITY = "GvFqTavdpGE"      # Agape CHP, Bo

# for year in ["2014", "2015", "2016", "2017", "2021", "2026","2025", "2024",]:
#     params = {
#         "dataElement": DATA_ELEMENT,  # REQUIRED
#         "orgUnit": FACILITY,
#         "startDate": f"{year}-01-01",
#         "endDate": f"{year}-12-31",
#     }

#     try:
#         response = session.get(
#             f"{BASE_URL}/api/dataValueSets.json",
#             params=params,
#             timeout=(5, 60),
#         )

#         print(f"\nYear: {year}")
#         print("HTTP:", response.status_code)

#         if not response.ok:
#             print("Error:", response.text[:500])
#             continue

#         payload = response.json()
#         values = payload.get("dataValues", [])

#         print("Records:", len(values))

#         for value in values[:3]:
#             print(
#                 "Period:", value.get("period"),
#                 "| Value:", value.get("value"),
#                 "| Org unit:", value.get("orgUnit"),
#             )

#     except requests.RequestException as exc:
#         print("Request failed:", exc)
#     except ValueError as exc:
#         print("Invalid JSON:", exc)


# Dry run 1

# Here analytics data return nothing from 2021 backwards. It only returned for 2025 and 2026
# import os
# import requests

# BASE_URL = os.getenv(
#     "DHIS2_BASE_URL",
#     "https://play.im.dhis2.org/stable-2-43-2",
# ).rstrip("/")

# USERNAME = os.getenv("DHIS2_USERNAME", "admin")
# PASSWORD = os.getenv("DHIS2_PASSWORD", "district")

# MEASURES = {
#     "Inpatient cases (data element)": "WHBtsCMZVAE",
#     "ANC 1st visit (data element)": "fbfJHSPpUQD",
#     "ANC visits total (indicator)": "dy1a1mseGR7",
# }

# PERIODS = ["2026","2025", "2024", "2023", "2022","2021", "2020", "2019", "2018", "2017", "2016"]

# # Start at country level to rule out individual district IDs.
# COUNTRY_UID = "ImspTQPwCqd"

# session = requests.Session()
# session.auth = (USERNAME, PASSWORD)
# session.headers["Accept"] = "application/json"

# for name, uid in MEASURES.items():
#     print(f"\n{name}: {uid}")

#     for period in PERIODS:
#         params = [
#             ("dimension", f"dx:{uid}"),
#             ("dimension", f"pe:{period}"),
#             ("dimension", f"ou:{COUNTRY_UID}"),
#             ("skipMeta", "true"),
#         ]

#         try:
#             response = session.get(
#                 f"{BASE_URL}/api/analytics.json",
#                 params=params,
#                 timeout=(5, 30),
#             )
#             response.raise_for_status()
#             data = response.json()

#             rows = data.get("rows", [])
#             print(
#                 f"  {period}: {len(rows)} rows"
#                 + (f" | example: {rows[0]}" if rows else "")
#             )

#         except (requests.RequestException, ValueError) as error:
#             print(f"  {period}: ERROR: {error}")
#             if "response" in locals() and response is not None:
#                 print(f"  Response: {response.text[:300]}")
