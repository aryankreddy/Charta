"""
VERIFIED ORGANIZATION MINER
Exclusively extracts verified Type 2 NPIs (Organizations) from Medicare data.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
import json

ROOT = Path(__file__).parent.parent
CLAIMS_FILE = ROOT / "data/raw/physician_utilization/Medicare Physician & Other Practitioners - by Provider and Service/2023/MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv"
OUTPUT_FILE = ROOT / "data/curated/verified_organizations.csv"

def mine_verified_organizations():
    print("🚨 MINING VERIFIED ORGANIZATIONS (TYPE 2 NPIs)")
    print(f"📂 Source: {CLAIMS_FILE}")
    
    if not os.path.exists(CLAIMS_FILE):
        print(f"❌ Source file not found: {CLAIMS_FILE}")
        return

    # Columns to load
    # Mapping based on file header verification:
    # organization_name -> Rndrng_Prvdr_Last_Org_Name
    # npi -> Rndrng_NPI
    # city -> Rndrng_Prvdr_City
    # state -> Rndrng_Prvdr_State_Abrvtn
    # zip -> Rndrng_Prvdr_Zip5
    # specialty -> Rndrng_Prvdr_Type
    # total_claims -> Tot_Srvcs
    # hcpcs_code -> HCPCS_Cd
    
    usecols = [
        'Rndrng_NPI',
        'Rndrng_Prvdr_Last_Org_Name',
        'Rndrng_Prvdr_Ent_Cd',
        'Rndrng_Prvdr_City',
        'Rndrng_Prvdr_State_Abrvtn',
        'Rndrng_Prvdr_Zip5',
        'Rndrng_Prvdr_Type',
        'HCPCS_Cd',
        'Tot_Srvcs'
    ]
    
    print("📊 Reading and filtering data...")
    
    chunks = []
    chunk_size = 500000
    total_org_rows = 0
    
    for chunk_num, chunk in enumerate(pd.read_csv(
        CLAIMS_FILE,
        usecols=usecols,
        chunksize=chunk_size,
        dtype={
            'Rndrng_NPI': str,
            'Rndrng_Prvdr_Zip5': str,
            'HCPCS_Cd': str
        }
    )):
        # FILTER: Keep rows ONLY where Rndrng_Prvdr_Ent_Cd == 'O'
        org_chunk = chunk[chunk['Rndrng_Prvdr_Ent_Cd'] == 'O'].copy()
        
        if len(org_chunk) > 0:
            chunks.append(org_chunk)
            total_org_rows += len(org_chunk)
            print(f"  Chunk {chunk_num + 1}: Found {len(org_chunk):,} organization rows")
            
    if not chunks:
        print("❌ No organization rows found!")
        return
        
    print(f"\n✅ Total organization rows extracted: {total_org_rows:,}")
    
    # Combine
    df = pd.concat(chunks, ignore_index=True)
    
    # AGGREGATE
    print("🔄 Aggregating by Organization NPI...")
    
    # We need to aggregate billing codes into a dictionary: {code: volume}
    # First, group by NPI and Code to sum volume per code (in case of duplicates, though usually unique per NPI-Code-PlaceOfService)
    # Actually, the file has Place_Of_Srvc, so (NPI, Code) might appear twice (O and F). We sum them.
    
    code_agg = df.groupby(['Rndrng_NPI', 'HCPCS_Cd'])['Tot_Srvcs'].sum().reset_index()
    
    # Create dictionary per NPI
    # This is a bit heavy for pandas apply, so let's try a faster way or just iterate if NPI count is manageable.
    # Or we can group by NPI and apply a lambda to create dict.
    
    def create_billing_dict(x):
        return json.dumps(dict(zip(x['HCPCS_Cd'], x['Tot_Srvcs'])))
        
    billing_dicts = code_agg.groupby('Rndrng_NPI').apply(create_billing_dict).reset_index(name='billing_codes')
    
    # Aggregate main fields
    # Take first value for static fields, sum for total volume
    main_agg = df.groupby('Rndrng_NPI').agg({
        'Rndrng_Prvdr_Last_Org_Name': 'first',
        'Rndrng_Prvdr_City': 'first',
        'Rndrng_Prvdr_State_Abrvtn': 'first',
        'Rndrng_Prvdr_Zip5': 'first',
        'Rndrng_Prvdr_Type': 'first',
        'Tot_Srvcs': 'sum'
    }).reset_index()
    
    # Merge
    final_df = pd.merge(main_agg, billing_dicts, on='Rndrng_NPI')
    
    # Rename columns to match requirements
    final_df.rename(columns={
        'Rndrng_NPI': 'npi',
        'Rndrng_Prvdr_Last_Org_Name': 'organization_name',
        'Rndrng_Prvdr_City': 'city',
        'Rndrng_Prvdr_State_Abrvtn': 'state',
        'Rndrng_Prvdr_Zip5': 'zip',
        'Rndrng_Prvdr_Type': 'specialty',
        'Tot_Srvcs': 'total_claims_volume'
    }, inplace=True)
    
    # Reorder
    cols = ['organization_name', 'npi', 'city', 'state', 'zip', 'specialty', 'total_claims_volume', 'billing_codes']
    final_df = final_df[cols]
    
    # EXPORT
    os.makedirs(OUTPUT_FILE.parent, exist_ok=True)
    final_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n💾 Saved to: {OUTPUT_FILE}")
    print(f"✅ Found {len(final_df):,} Verified Organizations.")
    
    # Sample
    print("\n📋 SAMPLE:")
    print(final_df.head())

if __name__ == "__main__":
    mine_verified_organizations()
