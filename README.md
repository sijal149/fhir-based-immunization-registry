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
- Pydantic
- Docker
- HTML / JavaScript (frontend)

## Endpoints
## API Endpoints

### Patient
- `POST /patient` — Register a new patient as a FHIR Patient resource
- `GET /patient/{id}` — Retrieve patient by ID
- `GET /patient/search` — Search patients by family name
- `POST /patient/validate` — Validate and register a patient

### Practitioner
- `POST /practitioner` — Register a practitioner
- `GET /practitioner/{id}` — Retrieve practitioner by ID

### Immunization
- `POST /immunization` — Record immunization with patient and practitioner references
- `GET /immunization/{id}` — Retrieve immunization record
- `POST /register-complete` — Register patient, practitioner, and immunization as a transaction Bundle

### Observations & Conditions
- `POST /observation` — Record LOINC-coded vital signs with reference ranges
- `POST /condition` — Record SNOMED CT and ICD-10 dual coded conditions

### Conversions
- `POST /convert/adt` — Convert HL7 v2 ADT message to FHIR Patient resource
- `POST /convert/ccda` — Convert CCDA document to FHIR transaction Bundle

### SMART on FHIR
- `POST /smart/token-request` — SMART on FHIR Backend Services JWT assertion flow

## How to Run

1. Start HAPI FHIR server:
```bash
docker run -d --name hapi-fhir -p 8080:8080 hapiproject/hapi:latest
```

2. Install dependencies:
```bash
pip install fastapi uvicorn requests pydantic jinja2 PyJWT cryptography httpx
```

3. Generate RSA keys for SMART on FHIR:
```bash
python generate_keys.py
```

4. Run the API:
```bash
uvicorn main:app --reload
```

5. Open Swagger UI at `http://127.0.0.1:8000/docs`