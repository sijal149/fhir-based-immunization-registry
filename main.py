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


