"""
E&M CODE DISTRIBUTION EXTRACTOR
Extract billing code patterns from Medicare claims for billing intelligence

Focuses on:
- E&M Codes: 99213, 99214, 99215 (office visits)
- Psych Codes: 90837, 90834 (psychotherapy)
- Calculate distributions and identify gaps
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
CLAIMS_FILE = ROOT / "data/raw/physician_utilization/Medicare Physician & Other Practitioners - by Provider and Service/2023/MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv"
OUTPUT_FILE = ROOT / "data/curated/staging/stg_billing_intelligence.csv"

# Target codes
EM_CODES = ['99213', '99214', '99215', '99212', '99211']  # Office visits
PSYCH_CODES = ['90837', '90834', '90832']  # Psychotherapy
ALL_TARGET_CODES = EM_CODES + PSYCH_CODES

def extract_billing_intelligence():
    """
    Extract E&M and psych code distributions from Medicare claims.
    """
    
    print("🔍 EXTRACTING BILLING INTELLIGENCE FROM MEDICARE CLAIMS...")
    print(f"Reading: {CLAIMS_FILE}")
    
    # Read claims data in chunks (9.6M rows is large)
    print("\n📊 Processing claims data...")
    
    chunks = []
    chunk_size = 500000
    
    for chunk_num, chunk in enumerate(pd.read_csv(
        CLAIMS_FILE,
        usecols=['Rndrng_NPI', 'HCPCS_Cd', 'Tot_Srvcs', 'Tot_Benes'],
        chunksize=chunk_size,
        dtype={'Rndrng_NPI': str, 'HCPCS_Cd': str}
    )):
        # Filter to target codes only
        chunk = chunk[chunk['HCPCS_Cd'].isin(ALL_TARGET_CODES)]
        
        if len(chunk) > 0:
            chunks.append(chunk)
            print(f"  Chunk {chunk_num + 1}: Found {len(chunk):,} relevant codes")
    
    if not chunks:
        print("❌ No target codes found in claims data!")
        return
    
    # Combine all chunks
    df = pd.concat(chunks, ignore_index=True)
    print(f"\n✅ Found {len(df):,} total claims for target codes")
    print(f"   Unique NPIs: {df['Rndrng_NPI'].nunique():,}")
    
    # Pivot to get code distribution by NPI
    print("\n🔄 Building code distribution matrix...")
    
    # Create pivot table
    pivot = df.pivot_table(
        index='Rndrng_NPI',
        columns='HCPCS_Cd',
        values='Tot_Srvcs',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # Rename columns
    pivot.columns.name = None
    pivot = pivot.rename(columns={'Rndrng_NPI': 'npi'})
    
    # Add total counts
    pivot['total_em_codes'] = pivot[[c for c in EM_CODES if c in pivot.columns]].sum(axis=1)
    pivot['total_psych_codes'] = pivot[[c for c in PSYCH_CODES if c in pivot.columns]].sum(axis=1)
    
    # Calculate E&M distribution percentages
    for code in EM_CODES:
        if code in pivot.columns:
            pivot[f'{code}_pct'] = (pivot[code] / pivot['total_em_codes'] * 100).fillna(0).round(1)
    
    # Calculate psych risk ratio (90837 / 90834)
    if '90837' in pivot.columns and '90834' in pivot.columns:
        pivot['psych_risk_ratio'] = (
            pivot['90837'] / (pivot['90834'] + 1)  # +1 to avoid division by zero
        ).round(2)
    
    # Save
    pivot.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved billing intelligence to: {OUTPUT_FILE}")
    
    # Stats
    print("\n📈 BILLING INTELLIGENCE STATS:")
    print(f"   Total NPIs: {len(pivot):,}")
    print(f"   NPIs with E&M codes: {len(pivot[pivot['total_em_codes'] > 0]):,}")
    print(f"   NPIs with psych codes: {len(pivot[pivot['total_psych_codes'] > 0]):,}")
    
    # E&M distribution summary
    em_providers = pivot[pivot['total_em_codes'] > 100].copy()
    if len(em_providers) > 0:
        print(f"\n   E&M Distribution (providers with >100 E&M codes):")
        for code in ['99213', '99214', '99215']:
            if f'{code}_pct' in em_providers.columns:
                avg_pct = em_providers[f'{code}_pct'].mean()
                print(f"     {code}: {avg_pct:.1f}% average")
    
    # Psych risk summary
    psych_providers = pivot[pivot['total_psych_codes'] > 100].copy()
    if len(psych_providers) > 0 and 'psych_risk_ratio' in psych_providers.columns:
        print(f"\n   Psych Risk Ratio (providers with >100 psych codes):")
        print(f"     Average: {psych_providers['psych_risk_ratio'].mean():.2f}")
        print(f"     High risk (>1.5): {len(psych_providers[psych_providers['psych_risk_ratio'] > 1.5]):,}")
    
    # Sample
    print("\n📋 SAMPLE BILLING INTELLIGENCE:")
    sample = pivot[pivot['total_em_codes'] > 500].head(3)
    for idx, row in sample.iterrows():
        print(f"\n   NPI: {row['npi']}")
        print(f"   Total E&M: {row['total_em_codes']:.0f}")
        if '99213_pct' in row:
            print(f"   99213: {row['99213_pct']:.1f}%")
        if '99214_pct' in row:
            print(f"   99214: {row['99214_pct']:.1f}%")
        if '99215_pct' in row:
            print(f"   99215: {row['99215_pct']:.1f}%")

if __name__ == "__main__":
    extract_billing_intelligence()
