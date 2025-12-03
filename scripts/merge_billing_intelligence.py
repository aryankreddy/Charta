"""
MERGE BILLING INTELLIGENCE INTO MAIN DATASET
Integrate E&M code distribution and psych metrics into clinics_scored_final.csv
"""

import pandas as pd
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Input files
MAIN_FILE = os.path.join(ROOT, "data", "curated", "clinics_scored_final.csv")
BILLING_FILE = os.path.join(ROOT, "data", "curated", "staging", "stg_billing_intelligence.csv")
PSYCH_FILE = os.path.join(ROOT, "data", "curated", "staging", "stg_psych_metrics.csv")

# Output
OUTPUT_FILE = os.path.join(ROOT, "data", "curated", "clinics_final_enriched.csv")

def merge_billing_intelligence():
    """
    Merge billing intelligence and psych metrics into main dataset.
    """
    
    print("🔄 MERGING BILLING INTELLIGENCE INTO MAIN DATASET...")
    
    # Load main dataset
    print(f"\n📂 Loading main dataset...")
    df = pd.read_csv(MAIN_FILE, low_memory=False)
    print(f"   Loaded {len(df):,} clinics")
    
    # Load billing intelligence
    print(f"\n📂 Loading billing intelligence...")
    billing = pd.read_csv(BILLING_FILE)
    billing['npi'] = billing['npi'].astype(str)
    print(f"   Loaded {len(billing):,} NPIs with billing data")
    
    # Load psych metrics
    if os.path.exists(PSYCH_FILE):
        print(f"\n📂 Loading psych metrics...")
        psych = pd.read_csv(PSYCH_FILE)
        psych['npi'] = psych['npi'].astype(str)
        print(f"   Loaded {len(psych):,} NPIs with psych data")
    else:
        print(f"\n⚠️  Psych metrics file not found: {PSYCH_FILE}")
        psych = None
    
    # Convert main dataset NPI to string
    df['npi'] = df['npi'].astype(str)
    
    # Merge billing intelligence
    print(f"\n🔗 Merging billing intelligence...")
    df = df.merge(billing, on='npi', how='left', suffixes=('', '_billing'))
    
    # Merge psych metrics if available
    if psych is not None:
        print(f"🔗 Merging psych metrics...")
        df = df.merge(psych, on='npi', how='left', suffixes=('', '_psych'))
    
    # Save
    print(f"\n💾 Saving enriched dataset...")
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"   Saved to: {OUTPUT_FILE}")
    
    # Stats
    print(f"\n📊 ENRICHMENT STATS:")
    print(f"   Total clinics: {len(df):,}")
    print(f"   With E&M data: {df['total_em_codes'].notna().sum():,}")
    print(f"   With psych data: {df['total_psych_codes'].notna().sum():,}")
    
    # Sample
    print(f"\n📋 SAMPLE ENRICHED DATA:")
    sample = df[df['total_em_codes'] > 100].head(3)
    for idx, row in sample.iterrows():
        print(f"\n   {row['org_name']}")
        print(f"   NPI: {row['npi']}")
        print(f"   Total E&M: {row['total_em_codes']:.0f}")
        if '99213_pct' in row and pd.notna(row['99213_pct']):
            print(f"   99213: {row['99213_pct']:.1f}%")
        if '99214_pct' in row and pd.notna(row['99214_pct']):
            print(f"   99214: {row['99214_pct']:.1f}%")
        if '99215_pct' in row and pd.notna(row['99215_pct']):
            print(f"   99215: {row['99215_pct']:.1f}%")

if __name__ == "__main__":
    merge_billing_intelligence()
