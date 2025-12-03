import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

def ingest_npi():
    df = pd.read_csv("data/raw/npi_registry/npi_registry.csv")  # adjust file path
    df = df.rename(columns={
        "NPI": "npi",
        "Provider Name": "name",
        "Organization Name": "organization_name",
        "Address": "address",
        "City": "city",
        "State": "state",
        "ZIP": "zip_code",
        "Phone": "phone",
        "Taxonomy Description": "taxonomy",
        "Last Updated": "last_updated"
    })
    for _, row in df.iterrows():
        supabase.table("npi_registry").insert(row.dropna().to_dict()).execute()

def ingest_pecos():
    df = pd.read_csv("data/raw/pecos/pecos_enrollment.csv")
    df = df.rename(columns={
        "NPI": "npi",
        "Legal Business Name": "legal_business_name",
        "Provider Type": "provider_type",
        "Enrollment Status": "enrollment_status",
        "Enrollment Date": "enrollment_date",
        "State": "state"
    })
    for _, row in df.iterrows():
        supabase.table("pecos_enrollment").insert(row.dropna().to_dict()).execute()

def ingest_aco():
    df = pd.read_csv("data/raw/aco/aco_participants.csv")
    df = df.rename(columns={
        "ACO ID": "aco_id",
        "ACO Name": "aco_name",
        "NPI": "npi",
        "Participant Name": "participant_name",
        "Start Date": "start_date",
        "End Date": "end_date"
    })
    for _, row in df.iterrows():
        supabase.table("aco_participants").insert(row.dropna().to_dict()).execute()

def ingest_hrsa():
    df = pd.read_csv("data/raw/hrsa/Health_Center_Sites.csv")
    df = df.rename(columns={
        "Site ID": "site_id",
        "Site Name": "site_name",
        "Site Address": "address",
        "Site City": "city",
        "Site State Abbreviation": "state",
        "Site Postal Code": "zip_code",
        "Health Center Number": "hrsa_id",
        "FQHC Site NPI Number": "npi"
    })
    df["fqhc_flag"] = True
    for _, row in df.iterrows():
        supabase.table("hrsa_sites").insert(row.dropna().to_dict()).execute()

if __name__ == "__main__":
    ingest_npi()
    ingest_pecos()
    ingest_aco()
    ingest_hrsa()
    print("✅ All public data ingested.")
