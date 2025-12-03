"""
OPERATION DATA RESCUE: ORGANIZATION-LEVEL MINING
Aggregates providers into Organizations (Entity Resolution)

Logic:
1. Group by Organization Name + Zip Code
2. Aggregate volume and provider counts
3. Determine primary specialty
4. Calculate group-wide billing patterns

Output: Organization-level billing intelligence
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
CLAIMS_FILE = ROOT / "data/raw/physician_utilization/Medicare Physician & Other Practitioners - by Provider and Service/2023/MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv"
OUTPUT_FILE = ROOT / "data/curated/staging/billing_intelligence_orgs.csv"

# Target codes
EM_CODES = ['99213', '99214', '99215', '99212', '99211']
PSYCH_CODES = ['90837', '90834', '90832', '90791']
CHIRO_CODES = ['98940', '98941', '98942', '98943']

ALL_CODES = EM_CODES + PSYCH_CODES + CHIRO_CODES

def mine_org_intelligence():
    print("🚨 OPERATION DATA RESCUE: MINING ORGANIZATIONS (TYPE 2 NPIs ONLY)")
    print(f"📂 Source: {CLAIMS_FILE}")
    print(f"🎯 Target: Verified Organization Entities\n")
    
    # Read claims data
    print("📊 Reading claims data...")
    
    chunks = []
    chunk_size = 500000
    
    for chunk_num, chunk in enumerate(pd.read_csv(
        CLAIMS_FILE,
        usecols=[
            'Rndrng_NPI', 
            'Rndrng_Prvdr_Last_Org_Name', # Organization Name for Type 2
            'Rndrng_Prvdr_First_Name',    # Should be empty for Type 2
            'Rndrng_Prvdr_St1',           # Street Address
            'Rndrng_Prvdr_Zip5',
            'Rndrng_Prvdr_State_Abrvtn',
            'Rndrng_Prvdr_Type',
            'Rndrng_Prvdr_Ent_Cd',
            'HCPCS_Cd', 
            'Tot_Srvcs'
        ],
        chunksize=chunk_size,
        dtype={
            'Rndrng_NPI': str, 
            'HCPCS_Cd': str, 
            'Rndrng_Prvdr_Zip5': str,
            'Rndrng_Prvdr_Last_Org_Name': str,
            'Rndrng_Prvdr_St1': str
        }
    )):
        # Filter to target codes
        chunk = chunk[chunk['HCPCS_Cd'].isin(ALL_CODES)]
        
        # Filter for Type 2 (Organizations) ONLY
        chunk = chunk[chunk['Rndrng_Prvdr_Ent_Cd'] == 'O']
        
        if len(chunk) > 0:
            chunks.append(chunk)
            print(f"  Chunk {chunk_num + 1}: {len(chunk):,} organization claims")
    
    if not chunks:
        print("❌ No target codes found for Organizations!")
        return
    
    # Combine
    df = pd.concat(chunks, ignore_index=True)
    print(f"\n✅ Found {len(df):,} total organization claims")
    
    # Clean Address (Basic normalization)
    df['address_key'] = df['Rndrng_Prvdr_St1'].str.upper().str.strip()
    
    # 1. Calculate Organization Metrics
    # Group by NPI (Type 2 NPI is the unique identifier)
    # We also keep Name, Address, Zip, State, Specialty as they should be constant for the NPI
    group_cols = ['Rndrng_NPI']
    
    # For non-grouping columns, we take the mode (most frequent) to handle any minor inconsistencies
    org_metrics = df.groupby(group_cols).agg({
        'Rndrng_Prvdr_Last_Org_Name': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown',
        'Rndrng_Prvdr_St1': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown',
        'Rndrng_Prvdr_Zip5': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown',
        'Rndrng_Prvdr_State_Abrvtn': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown',
        'Rndrng_Prvdr_Type': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown',
        'Tot_Srvcs': 'sum'             # Total Volume
    }).reset_index()
    
    # Rename for clarity
    org_metrics.rename(columns={
        'Rndrng_Prvdr_Last_Org_Name': 'org_name',
        'Rndrng_Prvdr_St1': 'address',
        'Rndrng_Prvdr_Zip5': 'zip_code',
        'Rndrng_Prvdr_State_Abrvtn': 'state',
        'Rndrng_Prvdr_Type': 'primary_specialty',
        'Tot_Srvcs': 'total_claims_volume'
    }, inplace=True)

    # 2. Calculate Billing Patterns (Pivot)
    print("📈 Calculating billing patterns...")
    
    pivot = df.pivot_table(
        index='Rndrng_NPI',
        columns='HCPCS_Cd',
        values='Tot_Srvcs',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # Merge metrics with billing data
    final_df = pd.merge(
        org_metrics, 
        pivot, 
        on='Rndrng_NPI'
    )
    
    # Calculate Ratios
    # E&M
    em_cols = [c for c in EM_CODES if c in final_df.columns]
    if em_cols:
        final_df['total_em'] = final_df[em_cols].sum(axis=1)
        for code in ['99213', '99214', '99215']:
            if code in final_df.columns:
                final_df[f'{code}_pct'] = (final_df[code] / final_df['total_em'] * 100).fillna(0).round(1)
    else:
        final_df['total_em'] = 0
    
    # Psych
    psych_cols = [c for c in PSYCH_CODES if c in final_df.columns]
    if psych_cols:
        final_df['total_psych'] = final_df[psych_cols].sum(axis=1)
        if '90837' in final_df.columns and '90834' in final_df.columns:
            final_df['psych_risk_ratio'] = (
                final_df['90837'] / (final_df['90834'] + final_df['90837'] + 1)
            ).round(3)
        else:
            final_df['psych_risk_ratio'] = 0
    else:
        final_df['total_psych'] = 0
        final_df['psych_risk_ratio'] = 0
        
    # Chiro
    chiro_cols = [c for c in CHIRO_CODES if c in final_df.columns]
    if chiro_cols:
        final_df['total_chiro'] = final_df[chiro_cols].sum(axis=1)
    else:
        final_df['total_chiro'] = 0

    # Determine Track based on Primary Specialty
    def get_track(specialty):
        spec = str(specialty).lower()
        if 'chiropractic' in spec:
            return 'Chiropractic'
        elif any(x in spec for x in ['psychiatry', 'psychologist', 'social worker', 'behavioral']):
            return 'Behavioral Health'
        elif any(x in spec for x in ['family', 'internal', 'general', 'nurse', 'physician assistant']):
            return 'Primary Care'
        else:
            return 'Other'

    final_df['track'] = final_df['primary_specialty'].apply(get_track)

    # Save
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved to: {OUTPUT_FILE}")
    
    # Stats
    print("\n📊 ORGANIZATION STATS:")
    print(f"   Total Organizations: {len(final_df):,}")
    print(f"   Avg Claims/Org: {final_df['total_claims_volume'].mean():.1f}")
    print(f"   Max Claims/Org: {final_df['total_claims_volume'].max()}")
    
    print(f"\n   By Track:")
    print(final_df['track'].value_counts())
    
    # Sample
    print(f"\n📋 SAMPLE ORGANIZATIONS:")
    print(final_df[['org_name', 'state', 'total_claims_volume', 'primary_specialty']].head(5))

if __name__ == "__main__":
    mine_org_intelligence()
