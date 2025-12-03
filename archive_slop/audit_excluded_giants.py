"""
AUDIT EXCLUDED GIANTS (RAW DATA)
Inspects the RAW Medicare file to find large organizations that might have been missed.
Focuses on specific specialties: Public Health, Clinic/Center, Multi-Specialty, FQHC, Internal Medicine.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
# RAW FILE PATH
CLAIMS_FILE = ROOT / "data/raw/physician_utilization/Medicare Physician & Other Practitioners - by Provider and Service/2023/MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv"

def audit_excluded_giants():
    print("🚨 AUDIT: FINDING MISSING GIANTS (RAW DATA)")
    print(f"📂 Source: {CLAIMS_FILE}")
    
    if not os.path.exists(CLAIMS_FILE):
        print(f"❌ Source file not found: {CLAIMS_FILE}")
        return

    # Columns to load
    usecols = [
        'Rndrng_NPI',
        'Rndrng_Prvdr_Last_Org_Name',
        'Rndrng_Prvdr_Ent_Cd',
        'Rndrng_Prvdr_Type',
        'Tot_Srvcs'
    ]
    
    print("📊 Reading raw data (Organizations only)...")
    
    chunks = []
    chunk_size = 500000
    
    for chunk_num, chunk in enumerate(pd.read_csv(
        CLAIMS_FILE,
        usecols=usecols,
        chunksize=chunk_size,
        dtype={
            'Rndrng_NPI': str,
            'Tot_Srvcs': float
        }
    )):
        # FILTER: Keep rows ONLY where Rndrng_Prvdr_Ent_Cd == 'O'
        org_chunk = chunk[chunk['Rndrng_Prvdr_Ent_Cd'] == 'O'].copy()
        
        if len(org_chunk) > 0:
            chunks.append(org_chunk)
            print(f"  Chunk {chunk_num + 1}: Found {len(org_chunk):,} organization rows")
            
    if not chunks:
        print("❌ No organization rows found!")
        return
        
    # Combine
    df = pd.concat(chunks, ignore_index=True)
    print(f"\n✅ Total organization rows loaded: {len(df):,}")
    
    # AGGREGATE by NPI first to get Org-level stats (since rows are per HCPCS code)
    # We want to sum volume per Org, and keep their Specialty and Name
    print("🔄 Aggregating by Organization...")
    
    org_agg = df.groupby('Rndrng_NPI').agg({
        'Rndrng_Prvdr_Last_Org_Name': 'first',
        'Rndrng_Prvdr_Type': 'first',
        'Tot_Srvcs': 'sum'
    }).reset_index()
    
    print(f"   Found {len(org_agg):,} Unique Organizations")
    
    # SUSPECT CATEGORIES
    suspects = [
        "Public Health or Welfare Agency",
        "Clinic/Center",
        "Multi-Specialty",
        "Federally Qualified Health Center", # Checking for partial match "Federally Qualified"
        "Internal Medicine"
    ]
    
    print("\n🔍 DEEP DIVE INTO SUSPECT CATEGORIES:")
    
    for target in suspects:
        print(f"\n👉 Target Category: '{target}'")
        
        # Filter (Case insensitive partial match)
        subset = org_agg[org_agg['Rndrng_Prvdr_Type'].str.contains(target, case=False, na=False)]
        
        count = len(subset)
        total_vol = subset['Tot_Srvcs'].sum()
        avg_vol = total_vol / count if count > 0 else 0
        
        print(f"   Found: {count:,} organizations")
        print(f"   Total Volume: {total_vol:,.0f}")
        print(f"   Avg Volume: {avg_vol:,.1f}")
        
        if count > 0:
            print("   Top 5 by Volume:")
            top_5 = subset.sort_values('Tot_Srvcs', ascending=False).head(5)
            for _, row in top_5.iterrows():
                print(f"     - {row['Rndrng_Prvdr_Last_Org_Name']} (Vol: {row['Tot_Srvcs']:,.0f})")
                
    # Also check for specific names requested
    print("\n🔎 CHECKING FOR SPECIFIC GIANTS:")
    giant_names = ["Planned Parenthood", "Kaiser", "Community Health Center", "Austin Regional Clinic"]
    
    for name in giant_names:
        print(f"\n👉 Name Check: '{name}'")
        subset = org_agg[org_agg['Rndrng_Prvdr_Last_Org_Name'].str.contains(name, case=False, na=False)]
        
        if len(subset) > 0:
            print(f"   Found {len(subset):,} matches:")
            top_3 = subset.sort_values('Tot_Srvcs', ascending=False).head(3)
            for _, row in top_3.iterrows():
                print(f"     - {row['Rndrng_Prvdr_Last_Org_Name']} (Specialty: {row['Rndrng_Prvdr_Type']}, Vol: {row['Tot_Srvcs']:,.0f})")
        else:
            print("   ❌ No matches found.")

if __name__ == "__main__":
    audit_excluded_giants()
