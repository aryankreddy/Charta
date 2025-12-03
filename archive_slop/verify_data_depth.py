"""
DATA DIAGNOSTIC TOOL
Author: Charta Health GTM Strategy

OBJECTIVE:
"Stop the Bullshit." Verify exactly how much REAL data (Margins, Actual Volume, Payer Mix)
is currently present in the seed file versus how much is missing.

This does NOT score. It audits the input quality.
"""

import pandas as pd
import os

# Setup paths
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEED_DATA = os.path.join(ROOT, "data", "curated", "clinics_seed.csv")

def print_header(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def diagnose_data_quality():
    if not os.path.exists(SEED_DATA):
        print(f"❌ File not found: {SEED_DATA}")
        return

    print(f"🔍 Inspecting: {SEED_DATA}")
    df = pd.read_csv(SEED_DATA, low_memory=False)
    total_records = len(df)
    
    print(f"Total Clinics in Database: {total_records:,}")

    # --- 1. HCRIS (Financial) Audit ---
    # Specifically checking FQHCs (Segment B) for real margins
    print_header("1. HCRIS / FINANCIAL DATA DEPTH")
    
    # Filter for FQHCs/Segment B
    fqhcs = df[df['segment_label'].astype(str).str.contains('Segment B|FQHC', case=False, na=False)]
    fqhc_count = len(fqhcs)
    
    if fqhc_count > 0:
        real_margin = fqhcs['net_margin'].notnull().sum()
        print(f"FQHCs identified: {fqhc_count:,}")
        print(f"FQHCs with REAL Margin Data:  {real_margin:,} ({real_margin/fqhc_count:.1%})")
        if real_margin == 0:
            print("⚠️  CRITICAL: No FQHC Cost Report data found. Scoring is relying 100% on estimates.")
    else:
        print("No FQHCs found in segment_label.")

    # --- 2. PHYSICIAN UTILIZATION (Volume) Audit ---
    print_header("2. PHYSICIAN UTILIZATION DATA DEPTH")
    
    # Check for real service counts
    has_vol = df['services_count'].notnull() & (df['services_count'] > 0)
    vol_count = has_vol.sum()
    
    print(f"Clinics with REAL Volume Data:  {vol_count:,} ({vol_count/total_records:.1%})")
    print(f"Clinics relying on Estimates:   {total_records - vol_count:,}")
    
    # --- 3. PAYER MIX / LEAKAGE Audit ---
    print_header("3. PAYER MIX & LEAKAGE SIGNALS")
    
    has_medicaid = df['medicaid_pct'].notnull() & (df['medicaid_pct'] > 0)
    med_count = has_medicaid.sum()
    
    print(f"Clinics with REAL Medicaid %:   {med_count:,} ({med_count/total_records:.1%})")
    
    # Check for granularity (CPT codes) if columns exist
    if 'em_code_pct' in df.columns:
        em_count = df['em_code_pct'].notnull().sum()
        print(f"Clinics with E/M Code Detail:   {em_count:,} (Critical for 'Undercoding' detection)")
    else:
        print("❌ 'em_code_pct' column missing entirely. No CPT-level data available.")

    # --- 4. SEGMENT BREAKDOWN ---
    print_header("4. DATA HEALTH BY SEGMENT")
    
    if 'segment_label' in df.columns:
        # Calculate fill rate of 'net_margin' by segment
        stats = df.groupby('segment_label')[['net_margin', 'services_count']].apply(lambda x: x.notnull().mean())
        print(f"{'Segment':<20} | {'Margin Fill %':<15} | {'Volume Fill %':<15}")
        print("-" * 56)
        for seg, row in stats.iterrows():
            print(f"{seg:<20} | {row['net_margin']:.1%}          | {row['services_count']:.1%}")

    print_header("CONCLUSION")
    if vol_count / total_records < 0.10:
        print("🚨 RESULT: DATA STARVATION")
        print("The scoring engine is functionally a 'calculator' running on empty inputs.")
        print("We need to run the HCRIS and PUF extractors and JOIN them to the seed file.")
    else:
        print("✅ Data depth looks acceptable.")

if __name__ == "__main__":
    diagnose_data_quality()