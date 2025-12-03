"""
DATA DIAGNOSTIC TOOL (ROBUST VERSION)
Author: Charta Health GTM Strategy

OBJECTIVE:
Audits the seed file for 'Real' data vs 'Empty' data.
Handles missing columns gracefully to reveal the true extent of data starvation.
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

def safe_check_column(df, col_name, metric_name):
    """Checks if a column exists and counts non-null/non-zero values."""
    if col_name not in df.columns:
        print(f"❌ {metric_name}: COLUMN MISSING ('{col_name}' not found in CSV)")
        return 0
    
    # Count non-null and non-zero
    # Coerce to numeric first to handle bad strings
    series = pd.to_numeric(df[col_name], errors='coerce')
    valid_count = series[series > 0].count()
    total = len(df)
    print(f"✅ {metric_name}: {valid_count:,} records ({valid_count/total:.1%})")
    return valid_count

def diagnose_data_quality():
    if not os.path.exists(SEED_DATA):
        print(f"❌ File not found: {SEED_DATA}")
        return

    print(f"🔍 Inspecting: {SEED_DATA}")
    df = pd.read_csv(SEED_DATA, low_memory=False)
    total_records = len(df)
    
    print(f"Total Clinics in Database: {total_records:,}")
    print(f"Columns Found: {list(df.columns)}")

    # --- 1. FQHC IDENTIFICATION AUDIT ---
    print_header("1. FQHC IDENTIFICATION")
    # Check multiple ways to find FQHCs
    fqhc_seg = df['segment_label'].astype(str).str.contains('Segment B|FQHC', case=False, na=False).sum()
    print(f"FQHCs by Segment Label (Seg B): {fqhc_seg:,}")
    
    if 'fqhc_flag' in df.columns:
        fqhc_flag = df[df['fqhc_flag'] == 1].shape[0]
        print(f"FQHCs by 'fqhc_flag':         {fqhc_flag:,}")
    else:
        print("❌ 'fqhc_flag' column missing.")

    # --- 2. FINANCIAL DATA AUDIT (HCRIS) ---
    print_header("2. FINANCIAL DATA (Margins & Revenue)")
    safe_check_column(df, 'net_margin', 'Real Net Margin')
    safe_check_column(df, 'allowed_amt', 'Real Medicare Revenue')
    
    # --- 3. OPERATIONAL DATA AUDIT (Utilization) ---
    print_header("3. OPERATIONAL DATA (Volume)")
    safe_check_column(df, 'services_count', 'Real Encounter Volume')

    # --- 4. PAYER MIX AUDIT (Leakage) ---
    print_header("4. PAYER MIX (Leakage Signals)")
    safe_check_column(df, 'medicaid_pct', 'Medicaid %')
    safe_check_column(df, 'medicare_pct', 'Medicare %')
    safe_check_column(df, 'em_code_pct', 'E/M Code Granularity')

    # --- 5. STRATEGIC AUDIT ---
    print_header("5. STRATEGIC DATA")
    safe_check_column(df, 'site_count', 'Location Count')
    
    if 'aco_member' in df.columns:
        aco_count = df['aco_member'].astype(str).str.lower().isin(['1', 'true', 'yes']).sum()
        print(f"ACO Members: {aco_count:,}")
    else:
        print("❌ 'aco_member' column missing.")

    print_header("DIAGNOSIS")
    print("If 'Real Net Margin' and 'Medicaid %' are 0 or Missing:")
    print("1. We have the NPI list (Identity).")
    print("2. We DO NOT have the Cost Reports (Financials) linked.")
    print("3. We DO NOT have the PUF Data (Payer Mix) linked.")
    print("Action: We must run the ingestion pipelines to merge HCRIS/PUF data into this seed file.")

if __name__ == "__main__":
    diagnose_data_quality()