# FHIR-Based Immunization Registry

**Live Demo:** https://fhir-based-immunization-registry-production.up.railway.app/docs

## What is this

Nepal's immunization data is fragmented across hundreds of health facilities
with no common standard. A child vaccinated in Kathmandu has no retrievable
record in Pokhara. This prototype demonstrates a FHIR R4 compliant
immunization registry built to solve that problem. Any system that speaks
FHIR can read, write, and exchange data with this registry.

## Tech Stack

- Python / FastAPI
- HAPI FHIR Server (R4)
- PostgreSQL
- Docker Compose (6-service orchestration)
- Mirth Connect (HL7v2 message routing)
- rapidfuzz (patient matching)

## Core Features

### Master Patient Index (MPI) — Three-Zone Matching

The core interoperability problem: linking the same patient across systems
with different local IDs.

- **Auto-link** (name score ≥ 0.95 AND exact DOB match) — high-confidence, no review needed
- **Manual review** (0.60–0.90 confidence) — logged to a `pending_review` table with full score breakdown, so a reviewer can see *why* it landed there
- **New patient** (< 0.60 confidence) — treated as a distinct person

### HL7v2 → FHIR Conversion

Live-tested via Mirth Connect: TCP Listener (MLLP) → HTTP Sender → FastAPI endpoint.

### C-CDA → FHIR Conversion

Parses C-CDA XML into a FHIR transaction Bundle.

### SMART on FHIR Backend Services

RSA-signed JWT client credentials flow.

## API Endpoints

### Patient
- `POST /patient` — Register a new patient
- `GET /patient/{id}` — Retrieve patient by ID
- `GET /patient/search` — Search patients by family name
- `POST /patient/validate` — Validate and register a patient
- `POST /patient/match` — Run three-zone MPI matching against existing patients

### Practitioner
- `POST /practitioner` — Register a practitioner
- `GET /practitioner/{id}` — Retrieve practitioner by ID

### Immunization
- `POST /immunization` — Record immunization (CVX-coded)
- `GET /immunization/{id}` — Retrieve immunization record
- `POST /register-complete` — Transaction Bundle: Patient + Practitioner + Immunization

### Observations & Conditions
- `POST /observation` — LOINC-coded vital signs with reference ranges
- `POST /condition` — SNOMED CT + ICD-10 dual-coded conditions

### Conversions
- `POST /convert/adt` — HL7v2 ADT → FHIR Patient
- `POST /convert/ccda` — C-CDA XML → FHIR Bundle

### SMART on FHIR
- `POST /smart/token-request` — JWT assertion flow

## How to Run

1. Clone the repo and start all services:
```bash
docker compose up -d
```

This starts FastAPI, HAPI FHIR, PostgreSQL (app DB + OMOP DB), and Mirth Connect.

2. Initialize the MPI database table:
```bash
docker exec -it fastapi-app python -c "from database import init_db; init_db()"
```

3. Open Swagger UI at `http://localhost:8000/docs`

4. (Optional) Access Mirth Administrator at `http://localhost:8081`

## What's Not Built Yet

- Review-resolution endpoint (approve/reject a `pending_review` record)
- Audit log for manual override decisions
- OMOP CDM ETL (`etl/fhir_to_omop.py` — in progress)