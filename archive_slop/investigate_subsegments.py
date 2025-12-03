import pandas as pd
import os

SEED_PATH = "data/curated/clinics_seed.csv"

def check_subsegments():
    if not os.path.exists(SEED_PATH):
        print("File not found.")
        return
        
    print("Loading Segment C...")
    df = pd.read_csv(SEED_PATH, low_memory=False)
    
    # Filter to just the "Blob"
    seg_c = df[df["segment_label"] == "Segment C"].copy()
    print(f"Total Segment C Rows: {len(seg_c)}")
    
    # 1. CHECK FOR HOSPITALS (Using naming or HCRIS proxy if available)
    # (Simple keyword check for now since HCRIS columns might be sparse in seed)
    hospitals = seg_c[seg_c["org_name"].str.contains("HOSPITAL|MEDICAL CENTER|HEALTH SYSTEM", case=False, na=False)]
    print(f"Potential Hospitals: {len(hospitals)}")

    # 2. CHECK FOR URGENT CARE (Taxonomy Keyword)
    urgent_care = seg_c[seg_c["taxonomy"].str.contains("Urgent|Emergency|Walk-In", case=False, na=False)]
    print(f"Potential Urgent Care: {len(urgent_care)}")
    
    # 3. CHECK FOR PRIMARY CARE (Taxonomy Keyword)
    primary = seg_c[seg_c["taxonomy"].str.contains("Family Medicine|Internal Medicine|General Practice", case=False, na=False)]
    print(f"Potential Primary Care: {len(primary)}")

if __name__ == "__main__":
    check_subsegments()
