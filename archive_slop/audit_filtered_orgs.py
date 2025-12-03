"""
AUDIT FILTERED ORGANIZATIONS
Inspects verified organizations to identify potential "whales" that might have been filtered out.
Focuses on: Public Health Agencies, Clinics/Centers, and Multi-Specialty groups.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
INPUT_FILE = ROOT / "data/curated/verified_organizations.csv"

def audit_filtered_orgs():
    print("🚨 AUDIT: INSPECTING POTENTIAL MISSING WHALES")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    # Load Data
    print("📊 Loading verified organizations...")
    df = pd.read_csv(INPUT_FILE)
    print(f"   Loaded {len(df):,} rows")
    
    # Define targets to inspect
    # We use partial matching to be safe, but report exact matches if found
    targets = [
        "Public Health or Welfare Agency",
        "Clinic/Center",
        "Multi-Specialty",
        "Clinic or Group Practice" # Added based on known data
    ]
    
    print("\n🔍 INSPECTION RESULTS:")
    
    for target in targets:
        # Filter
        # Case insensitive match
        subset = df[df['specialty'].str.contains(target, case=False, na=False)]
        
        count = len(subset)
        avg_vol = subset['total_claims_volume'].mean() if count > 0 else 0
        
        print(f"\n👉 Target: '{target}'")
        print(f"   Found: {count:,} organizations")
        print(f"   Avg Volume: {avg_vol:,.1f}")
        
        if count > 0:
            print("   Sample Names:")
            # Get top 5 by volume
            top_5 = subset.sort_values('total_claims_volume', ascending=False).head(5)
            for _, row in top_5.iterrows():
                print(f"     - {row['organization_name']} (Vol: {row['total_claims_volume']:,.0f})")
                
    # Also check for "Planned Parenthood" specifically as requested
    print("\n👉 Specific Check: 'Planned Parenthood'")
    pp = df[df['organization_name'].str.contains("Planned Parenthood", case=False, na=False)]
    print(f"   Found: {len(pp):,} organizations")
    if len(pp) > 0:
        print("   Sample:")
        for _, row in pp.head(3).iterrows():
            print(f"     - {row['organization_name']} ({row['specialty']}, Vol: {row['total_claims_volume']:,.0f})")

if __name__ == "__main__":
    audit_filtered_orgs()
