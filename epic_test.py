import httpx, json

response = httpx.get(
    "https://hapi.fhir.org/baseR4/Patient?family=Smith",
    headers={"Accept": "application/fhir+json"}
)
response_json = response.json()
entries = response_json["entry"]
for entry in entries:
    given_name = entry["resource"]["name"][0]["given"][0]
    family_name = entry["resource"]["name"][0]["family"]
    birthdate = entry["resource"]["birthDate"]
    print (f"Name:{given_name} {family_name}, Birthdate: {birthdate}")


# print(parsed)
# print(response.status_code)
# print(json.dumps(response.json(), indent=2))

