import pandas as pd
import os

SEED_PATH = "data/curated/clinics_seed.csv"

def check_subsegments_by_code():
    if not os.path.exists(SEED_PATH):
        print("File not found.")
        return
        
    print("Loading Segment C...")
    df = pd.read_csv(SEED_PATH, low_memory=False, usecols=["segment_label", "taxonomy", "org_name"])
    
    # Filter to just Segment C
    seg_c = df[df["segment_label"] == "Segment C"].copy()
    print(f"Total Segment C Rows: {len(seg_c)}")
    
    # Ensure taxonomy is string
    seg_c["taxonomy"] = seg_c["taxonomy"].fillna("").astype(str)

    # 1. URGENT CARE CHECK (Code: 261QU0200X)
    urgent_care = seg_c[seg_c["taxonomy"].str.contains("261QU0200X", na=False)]
    print(f"Confirmed Urgent Care (by Code): {len(urgent_care)}")
    
    # 2. PRIMARY CARE CHECK (Codes: Family, Internal, General)
    # 207Q00000X = Family Medicine
    # 207R00000X = Internal Medicine
    # 208D00000X = General Practice
    primary_codes = "207Q00000X|207R00000X|208D00000X"
    primary = seg_c[seg_c["taxonomy"].str.contains(primary_codes, na=False)]
    print(f"Confirmed Primary Care (by Code): {len(primary)}")

    # 3. HOSPITAL CHECK (Name Search - same as before)
    hospitals = seg_c[seg_c["org_name"].str.contains("HOSPITAL|MEDICAL CENTER|HEALTH SYSTEM", case=False, na=False)]
    print(f"Potential Hospitals (Name Match): {len(hospitals)}")

if __name__ == "__main__":
    check_subsegments_by_code()
