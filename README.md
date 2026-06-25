# FHIR-Based Immunization Registry

**Live Demo:** https://fhir-based-immunization-registry-production.up.railway.app/docs

## What is this
Nepal's immunization data is fragmented across hundreds of health facilities 
with no common standard — a child vaccinated in Kathmandu has no retrievable 
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
- `POST /patient` — Register a new patient as a FHIR Patient resource
- `GET /patient/{id}` — Retrieve patient by ID
- `GET /patient/search?family=` — Search patients by family name
- `POST /practitioner` — Register a practitioner
- `GET /practitioner/{id}` — Retrieve practitioner by ID
- `POST /immunization` — Record immunization with patient and practitioner references
- `GET /immunization/{id}` — Retrieve immunization record
-- `POST /convert/adt` — converts HL7 v2 ADT message to FHIR Patient resource

## How to Run

1. Start HAPI FHIR server:
```bash
docker run -d --name hapi-fhir -p 8080:8080 hapiproject/hapi:latest
```

2. Install dependencies:
```bash
pip install fastapi uvicorn requests pydantic jinja2
```

3. Run the API:
```bash
uvicorn main:app --reload
```

4. Open browser at `http://127.0.0.1:8000`