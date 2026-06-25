from pydantic import BaseModel
import requests
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, HTTPException,Request
from fastapi import Body
import os
import hl7 

templates = Jinja2Templates(directory="templates")

app = FastAPI()

HAPI_BASE = os.getenv("HAPI_BASE_URL", "http://localhost:8080/fhir")


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

@app.get("/valueset/nepal-vaccines")
def nepal_vaccine_set():
    return {
  "resourceType": "ValueSet",
  "id": "nepal-vaccines",
  "name": "NepalEPIVaccines",
  "status": "active",
  "compose": {
    "include": [{
      "system": "http://health.gov.np/fhir/CodeSystem/vaccines",
      "concept": [
        {
            "code":"NP-BCG",
            "display": "BCG Vaccine"
        },
        {
            "code":"NP-OPV",
            "display": "Oral Polio Vaccine"
        },
        {
            "code":"NP-PENTA",
            "display":"Pentavalent Vaccine"
        }
      ]
    }]
  }
}
    
def extract_valid_codes(valueset):
    valid_codes = set()
    codes = valueset.get("compose", {}).get("include",[])
    for item in codes:
        concepts = item.get("concept", [])
        for concept in concepts:
            code = concept.get("code")
            if code:
                valid_codes.add(code)            
    return valid_codes

valueset = nepal_vaccine_set()
allowed_codes = extract_valid_codes(valueset)

@app.post('/patient/validate')
def create_validated_patient(data: PatientRequest):
    try:
        validated_patient = {
            "resourceType" : "Patient",
            "name" : [{"family": data.name.split()[-1], "given": [data.name.split()[0]]}],
            "gender" : data.gender,
            "birthDate" : data.birthdate
        }
        response = requests.post(f"{HAPI_BASE}/Patient/$validate",
                                json = validated_patient,
                                headers={"Content-Type": "application/fhir+json"},
                                timeout = 10)
        validation_result = response.json()
        issues = validation_result.get("issue", [])
        has_errors = any(issue["severity"] == "error" for issue in issues)
        if has_errors:
            return validation_result
        else:
            save_response = requests.post(f"{HAPI_BASE}/Patient",
                                        json = validated_patient,
                                        headers= {"Content-Type": "application/fhir+json"},
                                        timeout=10)
            return save_response.json()
    except requests.exceptions.ConnectionError:
            raise HTTPException(
                status_code=503,
                detail="FHIR Server Unavailable. Is HAPI running?"
            )
    except requests.exceptions.Timeout:
            raise HTTPException(
                status_code=504,
                detail="Server too slow. Try again later."
            )

@app.post("/patient")
def create_patient(data: PatientRequest):
    try:
        patient = {
            "resourceType": "Patient",
            "name": [{"family": data.name.split()[-1], "given": [data.name.split()[0]]}],
            "gender": data.gender,
            "birthDate": data.birthdate
        }
        response = requests.post(
            f"{HAPI_BASE}/Patient",
            json=patient,
            headers={"Content-Type": "application/fhir+json"},
            timeout=10
        )
        return response.json()
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="FHIR Server Unavailable. Is HAPI running?"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Server too slow. Try again later."
        )
@app.get("/patient/search")
def search_patients(family: str):
    try:
        response = requests.get(f"{HAPI_BASE}/Patient?family={family}", timeout=10)
        return response.json()
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="FHIR Server Unavailable. Is HAPI running?"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Server too slow. Try again later."
        )
@app.get("/patient/search/simple")
def search_patients_simple(family: str):
    try:
        response = requests.get(f"{HAPI_BASE}/Patient?family={family}", timeout=10)
        entries = response.json()["entry"] 
        return [ {
            "id": item["resource"]["id"],
            "gender": item['resource']['gender'],
            "name": item["resource"]["name"][0]["given"][0] + " " + item["resource"]["name"][0]["family"]
        }
        for item in entries
        ]
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="FHIR Server Unavailable. Is HAPI running?"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Server too slow. Try again later."
        )
@app.get("/patient/{patient_id}")
def get_patient(patient_id: str):
    try:
        response = requests.get(f"{HAPI_BASE}/Patient/{patient_id}", timeout=10)
        return response.json()
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="FHIR Server Unavailable. Is HAPI running?"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Server too slow. Try again later."
        )
@app.post("/practitioner")
def create_practitioner(data: Practitioner):
    try:
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
            headers={"Content-Type": "application/fhir+json",},
            timeout=10
        )
        return response.json()
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="FHIR Server Unavailable. Is HAPI running?"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Server too slow. Try again later."
        )
@app.get("/practitioner/{practitioner_id}")
def get_practitioner(practitioner_id: str):
    try:
        response = requests.get(f"{HAPI_BASE}/Practitioner/{practitioner_id}", timeout=10)
        return response.json()
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="FHIR Server Unavailable. Is HAPI running?"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Server too slow. Try again later."
        )

@app.post("/immunization")
def create_immunization(data: ImmunizationStatus):
    try:
        if data.vaccine_code not in allowed_codes:
            raise HTTPException(
                status_code=400,
                detail="Code not valid. Bad request."
            )
        else:
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
                                    headers = {"Content-Type": "application/fhir+json"},
                                    timeout=10)
            return response.json()
    except requests.exceptions.ConnectionError:
        raise HTTPException(
                status_code=503,
                detail="FHIR Server Unavailable. Is HAPI running?"
            )
    except requests.exceptions.Timeout:
        raise HTTPException(
                status_code=504,
                detail="Server too slow. Try again later."
            )

@app.get("/immunization/{immunization_id}")
def get_immunization(immunization_id : str):
    try:
        response = requests.get(f"{HAPI_BASE}/Immunization/{immunization_id}",timeout=10)
        return response.json() 
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="FHIR Server Unavailable. Is HAPI running?"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Server too slow. Try again later."
        )

@app.post("/register-complete")
def complete_bundle(data: BundleRequest):
    try:
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
                                headers = {"Content-Type": "application/fhir+json"},
                                timeout=10)
        return response.json()
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="FHIR Server Unavailable. Is HAPI running?"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Server too slow. Try again later."
        )


@app.post("/convert/adt")
async def convert_adt(message: str = Body(..., media_type="text/plain")):
    try:
        message = message.replace('\n', '\r')
        h = hl7.parse(message)
        pid = h.segment('PID')
        family = str(pid[5][0][0])
        given = str(pid[5][0][1]) 
        birthdate_raw = str(pid[7])
        gender_raw = str(pid[8])
        def convert_gender(gender_raw):
            if gender_raw in ['m','M']:
                return 'male'
            elif gender_raw in ['f','F']:
                return 'female'
        gender = convert_gender(gender_raw)
        if len(birthdate_raw) == 8:
            birthdate = f"{birthdate_raw[0:4]}-{birthdate_raw[4:6]}-{birthdate_raw[6:8]}"
        else:
            birthdate = "unknown or wrong entry"
        patient = {
            "resourceType": "Patient",
            "id": str(pid[3][0][1]),
            "gender" : gender,
            "birthDate" : birthdate,
            "name": [
                {
                    "given":[given],
                    "family": family
                }
            ]
        }
        response = requests.post(f"{HAPI_BASE}/Patient",
                                json = patient,
                                headers={"Content-Type": "application/fhir+json"},
                                timeout = 10)
        return response.json()
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code= 503,
            detail = "FHIR Server Unavailable. Is HAPI running?"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Server too slow. Try again later."
        )
class Observation_resource(BaseModel):
    patient_id : str
    vital_sign_type : str
    value: str
    unit: str
@app.post("/observation")
def create_observation(data: Observation_resource):
    try:
        vitals_mapping = {"heart rate" : "8867-4", "body temperature": "8310-5","respiratory rate": "9279-1",
                        "blood pressure systolic" : "8480-6", "blood pressure diastolic":"8462-4", "oxygen saturation":"2708-6"} 
        loinc_code = vitals_mapping.get(data.vital_sign_type.strip().lower(), "unknown")
        reference_ranges = {
            "heart rate": {"low": 60, "high": 100},
            "body temperature": {"low": 36.1, "high": 37.2},
            "respiratory rate": {"low": 12, "high": 20},
            "oxygen saturation": {"low": 95, "high": 100},
            "blood pressure systolic": {"low": 90, "high": 120},
            "blood pressure diastolic": {"low": 60, "high": 80}
            }
        ranges = reference_ranges.get(data.vital_sign_type.strip().lower())
        value_num = float(data.value)
        if loinc_code == "unknown":
            raise HTTPException(
                status_code=400,
                detail="Bad Request"
            )
        else:
            if value_num > ranges["high"]:
                interp_code = 'H'
                interp_display = "High"
            elif value_num < ranges["low"]:
                interp_code = "L"
                interp_display = "Low"
            else:
                interp_code = "N"
                interp_display = "Normal"
            observation = {
                "resourceType": "Observation",
                "status":"final",
                "code":{
                    "coding":[{
                        "system":"http://loinc.org",
                        "code": loinc_code,
                        "display": data.vital_sign_type
                    }]
                },
                "subject":{
                    "reference":f"Patient/{data.patient_id}"
                },
                "valueQuantity" : {
                    "value": data.value,
                    "unit": data.unit
                },
                "referenceRange": [{
                "low": {"value": ranges["low"], "unit": data.unit},
                "high": {"value": ranges["high"], "unit": data.unit}
            }],
            "interpretation": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": interp_code,
                    "display": interp_display
                }]
            }]
            }
            response = requests.post(f"{HAPI_BASE}/Observation",
                                    json = observation,
                                    headers={"Content-Type":"application/fhir+json"},
                                    timeout=10)
            return response.json()
    except requests.exceptions.ConnectionError:
            raise HTTPException(
                status_code=503,
                detail="FHIR Server not available. Is HAPI running?"
            )
    except requests.exceptions.Timeout:
            raise HTTPException(
                status_code=504,
                detail="Server too slow. Try again later"
            )
    
