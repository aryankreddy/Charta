import os
import sys

import pandas as pd
import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CURATED = os.path.join(ROOT, "data", "curated")
STAGING = os.path.join(CURATED, "staging")

REQUIRED_FILES = [
    os.path.join(STAGING, "stg_npi_orgs.parquet"),
    os.path.join(STAGING, "stg_hrsa_sites.parquet"),
    os.path.join(STAGING, "stg_pecos_orgs.parquet"),
    os.path.join(CURATED, "clinics_seed.csv"),
    os.path.join(CURATED, "clinics_scored.csv"),
]

for path in REQUIRED_FILES:
    if not os.path.exists(path):
        print(f"Missing expected artifact: {path}")
        sys.exit(1)

clinics = pd.read_csv(os.path.join(CURATED, "clinics_scored.csv"))
if clinics.shape[0] < 1000:
    print("Expected at least 1000 clinics in clinics_scored.csv")
    sys.exit(1)

try:
    resp = requests.get("http://localhost:8000/clinics", params={"limit": 50})
    resp.raise_for_status()
    rows = resp.json().get("rows", [])
    if len(rows) == 0:
        print("API /clinics returned zero rows")
        sys.exit(1)
except requests.RequestException as exc:
    print(f"/clinics request failed: {exc}")
    sys.exit(1)

sample = rows[0]["clinic_id"]
try:
    detail = requests.get(f"http://localhost:8000/clinic/{sample}")
    detail.raise_for_status()
    body = detail.json()
    if body.get("clinic") is None:
        print("/clinic detail missing clinic payload")
        sys.exit(1)
except requests.RequestException as exc:
    print(f"/clinic request failed: {exc}")
    sys.exit(1)

print("Smoke test passed.")
