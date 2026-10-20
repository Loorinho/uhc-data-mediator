# Sierra Leone UHC Data Mediator

A Django REST Framework and TanStack Start application for acquiring, standardizing, validating, and sharing aggregate health data for Universal Health Coverage (UHC) analysis.

## 1. Problem

Health data from DHIS2 is source-specific and cannot automatically be combined or securely shared across organizations. This makes it difficult to analyze healthcare service availability alongside population data.

## 2. Solution

The platform provides a mediation layer that:

- Acquires aggregate ANC first-visit data from Sierra Leone DHIS2 using LIVE or FIXTURE mode.
- Transforms source observations into a standardized canonical model.
- Manages versioned data products and releases.
- Generates HL7 FHIR R4 resources and validates them using the official FHIR validator.
- Provides authenticated APIs and role-based interfaces for data providers, analysts, auditors, and administrators.

## 3. Architecture

**Stack:** TanStack Start (React/TypeScript), Django REST Framework, PostgreSQL, Docker Compose, and HL7 FHIR Validator CLI.

**Data flow:**

```text
DHIS2 / FIXTURE
      ↓
Acquisition Worker
      ↓
Source Observations (PostgreSQL)
      ↓
Canonical Transformation
      ↓
Data Product Release
      ↓
FHIR Generation → HL7 Validation
      ↓
Authorized Access via DRF + TanStack Start
```

Background workers handle acquisition, transformation, and FHIR processing. PostgreSQL stores observations, release metadata, processing results, and audit events.

## 4. Setup

**Prerequisites:** Git, Docker, Docker Compose, and the HL7 FHIR Validator JAR.

**1. Clone and configure the project**

```bash
git clone git@github.com:Loorinho/uhc-data-mediator.git
cd uhc-data-mediator.git
cp .env.example .env
```

Update `.env` with the required database, Django, and DHIS2 configuration. Place `validator_cli.jar` inside `fhir_validator/` in the root of the project.

**2. Start the application**

```bash
docker compose up -d --build
```

**3. Apply database migrations**

```bash
docker compose exec uhc-api python manage.py migrate
```

**4. Seed the initial data**

Run the project's database-seeding management command to initialize the required districts, population data, canonical definitions, and default administrative roles.

```bash
docker compose exec uhc-api python manage.py seed_initial_data
```

**5. Verify the services**

```bash
docker compose ps
docker compose exec uhc-api python manage.py check
```

**6. Access the application**

- Backend API: `http://127.0.0.1:8000`
- Frontend: Use the configured frontend URL or startup script.

Once the initial data is seeded, sign in using the account setup procedure and follow the functional test steps in Section 5.


## 5. Testing

**Functional test procedure:**

1. Log in as a data_provider.
2. Trigger a FIXTURE acquisition and verify `SUCCEEDED`.
3. Trigger canonical transformation and inspect the generated release.
4. Generate a FHIR Bundle and validate it.
5. Inspect conformity results and download the validation report.
6. Verify role restrictions and inspect recorded audit events.

**Backend checks:**

```bash
docker compose exec uhc-api python manage.py check
docker compose exec uhc-api python manage.py test
```

The test command requires Django tests to be configured and does not by itself demonstrate that authorization or privacy tests exist.

## 6. Known Limitations

- The public DHIS2 demo may be unavailable or reject authentication; FIXTURE mode supports reproducible testing.
- ANC activity and 2021 population data require geographic and temporal reconciliation before reliable coverage comparisons.
- Some custom FHIR terminology mappings generate validation warnings.
- Privacy controls, publication governance, and complete role-based audit coverage require final verification.
- The MVP uses local file storage and is not production-ready for a national health information exchange.

## Project Status

The core acquisition, canonical transformation, FHIR generation, and validation workflows have been demonstrated. Security, privacy, analytical integration, and audit completeness remain areas for further testing and improvement.