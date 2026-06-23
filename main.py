from fastapi import FastAPI
from pydantic import BaseModel
import requests
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

templates = Jinja2Templates(directory="templates")

app = FastAPI()

HAPI_BASE = "http://localhost:8080/fhir"

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Define request body structure
class PatientRequest(BaseModel):
    name: str
    gender: str
    birthdate: str

class Practitioner(BaseModel):
    name: str
    organization: str

class ImmunizationStatus(BaseModel):
    patient_id: int
    vaccine_name: str
    vaccine_code: str
    date: str
    dose_number: int
    practitioner_id: int

class BundleRequest(BaseModel):
    name: str
    gender: str
    birthdate: str
    vaccine_name: str
    vaccine_code: str
    dose_number: int
    date: str
    practitioner_name: str
    organization: str

@app.post('/patient/validate')
def create_validated_patient(data: PatientRequest):
    validated_patient = {
        "resourceType" : "Patient",
        "name" : [{"family": data.name.split()[-1], "given": [data.name.split()[0]]}],
        "gender" : data.gender,
        "birthDate" : data.birthdate
    }
    response = requests.post(f"{HAPI_BASE}/Patient/$validate",
                             json = validated_patient,
                             headers={"Content-Type": "application/fhir+json"})
    validation_result = response.json()
    issues = validation_result.get("issue", [])
    has_errors = any(issue["severity"] == "error" for issue in issues)
    if has_errors:
        return validation_result
    else:
        save_response = requests.post(f"{HAPI_BASE}/Patient",
                                      json = validated_patient,
                                      headers= {"Content-Type": "application/fhir+json"})
        return save_response.json()

@app.post("/patient")
def create_patient(data: PatientRequest):
    patient = {
        "resourceType": "Patient",
        "name": [{"family": data.name.split()[-1], "given": [data.name.split()[0]]}],
        "gender": data.gender,
        "birthDate": data.birthdate
    }
    response = requests.post(
        f"{HAPI_BASE}/Patient",
        json=patient,
        headers={"Content-Type": "application/fhir+json"}
    )
    return response.json()

@app.get("/patient/search")
def search_patients(family: str):
    response = requests.get(f"{HAPI_BASE}/Patient?family={family}")
    return response.json()

@app.get("/patient/search/simple")
def search_patients_simple(family: str):
    response = requests.get(f"{HAPI_BASE}/Patient?family={family}")
    entries = response.json()["entry"] 
    return [ {
        "id": item["resource"]["id"],
        "gender": item['resource']['gender'],
        "name": item["resource"]["name"][0]["given"][0] + " " + item["resource"]["name"][0]["family"]
    }
    for item in entries
    ]

@app.get("/patient/{patient_id}")
def get_patient(patient_id: str):
    response = requests.get(f"{HAPI_BASE}/Patient/{patient_id}")
    return response.json()

@app.post("/practitioner")
def create_practitioner(data: Practitioner):
    practitioner = {
        "resourceType": "Practitioner",
        "name": [{"family": data.name.split()[-1], "given": [data.name.split()[0]]}],
        "qualification": [{"issuer": {
                "display": data.organization
            }
            }]
        }
    response = requests.post(
        f"{HAPI_BASE}/Practitioner",
        json=practitioner,
        headers={"Content-Type": "application/fhir+json"}
    )
    return response.json()

@app.get("/practitioner/{practitioner_id}")
def get_practitioner(practitioner_id: str):
    response = requests.get(f"{HAPI_BASE}/Practitioner/{practitioner_id}")
    return response.json()

@app.post("/immunization")
def create_immunization(data: ImmunizationStatus):
    immunization = {
        "resourceType": "Immunization",
        "status": "completed",
        "vaccineCode":{
            "coding": [{
                "system" : "http://hl7.org/fhir/sid/cvx",
                "code" : data.vaccine_code,
                "display" : data.vaccine_name
            }]
        },
        "patient": {
            "reference": f"Patient/{data.patient_id}"
        },
        "occurrenceDateTime": data.date,
        "performer": [{
            "actor": {
                "reference": f"Practitioner/{data.practitioner_id}"
            }
        }],
        "protocolApplied": [{
            "doseNumberPositiveInt" : data.dose_number
            }]
    }
    response = requests.post(f"{HAPI_BASE}/Immunization",
                             json = immunization,
                             headers = {"Content-Type": "application/fhir+json"})
    return response.json()

@app.get("/immunization/{immunization_id}")
def get_immunization(immunization_id : str):
    response = requests.get(f"{HAPI_BASE}/Immunization/{immunization_id}")
    return response.json() 

@app.post("/register-complete")
def complete_bundle(data: BundleRequest):
    bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            {
                "fullUrl": "urn:uuid:patient-temp-id",
                "resource": {
                    "resourceType": "Patient",
                    "name": [{"family": data.name.split()[-1], "given": [data.name.split()[0]]}],
                    "gender": data.gender,
                    "birthDate": data.birthdate
                },
                "request": {
                    "method": "POST",
                    "url": "Patient"
                }
            },
            {
                "fullUrl": "urn:uuid:practitioner-temp-id",
                "resource": {
                    "resourceType": "Practitioner",
                    "name": [{"family": data.practitioner_name.split()[-1], "given": [data.practitioner_name.split()[0]]}],
                    "qualification": [{"issuer": {"display": data.organization}}]
                },
                "request": {
                    "method": "POST",
                    "url": "Practitioner"
                }
            },
            {
                "fullUrl": "urn:uuid:immunization-temp-id",
                "resource": {
                    "resourceType": "Immunization",
                    "status": "completed",
                    "vaccineCode":{
                        "coding": [{
                            "system" : "http://hl7.org/fhir/sid/cvx",
                            "code" : data.vaccine_code,
                            "display" : data.vaccine_name
                        }]
                    },
                    "patient": {
                        "reference": "urn:uuid:patient-temp-id"
                    },
                    "occurrenceDateTime": data.date,
                    "performer": [{
                        "actor": {
                            "reference": "urn:uuid:practitioner-temp-id"
                        }
                    }],
                    "protocolApplied": [{
                        "doseNumberPositiveInt" : data.dose_number
                        }]
                },
                "request": {
                    "method": "POST",
                    "url": "Immunization"
                }
            }
        ]
    }
    response = requests.post(f"{HAPI_BASE}",
                             json = bundle,
                             headers = {"Content-Type": "application/fhir+json"})
    return response.json()



