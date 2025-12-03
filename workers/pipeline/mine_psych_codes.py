"""
BEHAVIORAL HEALTH SIGNAL MINER
Author: Charta Health GTM Strategy

Purpose: Extract psychotherapy billing patterns to identify audit risk.

Target Codes (Comprehensive Behavioral Health Set):
- 90791: Psychiatric diagnostic evaluation
- 90792: Psychiatric diagnostic evaluation with medical services
- 90832: Psychotherapy, 30 min
- 90833: Psychotherapy, 30 min with E/MIK
- 90834: Psychotherapy, 45 min
- 90836: Psychotherapy, 45 min with E/M
- 90837: Psychotherapy, 60 min (High Scrutiny)
- 90838: Psychotherapy, 60 min with E/M (High Scrutiny)

Formula: Psych_Risk_Ratio = (Count(90837) + Count(90838)) / Total Psych Codes
Interpretation: Ratio > 0.80 = High Audit Risk (overuse of 60-min codes)
"""

import pandas as pd
import numpy as np
import os
import sys

# Configuration - Go up 2 levels from workers/pipeline/ to project root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_RAW = os.path.join(ROOT, "data", "raw")
DATA_CURATED = os.path.join(ROOT, "data", "curated")
DATA_STAGING = os.path.join(DATA_CURATED, "staging")

# Input Files
UTIL_FILE = os.path.join(DATA_RAW, "physician_utilization", "Medicare Physician & Other Practitioners - by Provider and Service", "2023", "MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv")
PECOS_DIR = os.path.join(DATA_RAW, "pecos", "Medicare Fee-For-Service  Public Provider Enrollment", "2025-Q3")
PECOS_REASSIGN = os.path.join(PECOS_DIR, "PPEF_Reassignment_Extract_2025.10.01.csv")
PECOS_ENROLL = os.path.join(PECOS_DIR, "PPEF_Enrollment_Extract_2025.10.01.csv")

# Output File
OUTPUT_FILE = os.path.join(DATA_STAGING, "stg_psych_metrics.csv")

# Target Codes (Comprehensive Behavioral Health Set)
TARGET_CODES = ['90791', '90792', '90832', '90833', '90834', '90836', '90837', '90838']
HIGH_SCRUTINY_CODES = ['90837', '90838']  # 60-minute codes with high audit risk

def load_pecos_bridge():
    """
    Load PECOS Reassignment Bridge to map Individual NPI -> Organization NPI.
    Returns DataFrame with columns ['indiv_npi', 'org_npi'] or None if unavailable.
    """
    print("   Loading PECOS Reassignment Bridge...")
    if not os.path.exists(PECOS_REASSIGN) or not os.path.exists(PECOS_ENROLL):
        print("   ⚠️  PECOS files not found. Skipping Bridge.")
        return None

    # 1. Load Enrollment (Map ID -> NPI)
    print("   Loading Enrollment Map...")
    enrl = pd.read_csv(PECOS_ENROLL, usecols=['NPI', 'ENRLMT_ID'], dtype={'NPI': 'int64', 'ENRLMT_ID': str}, encoding='latin1')
    
    # 2. Load Reassignment (Map Indiv ID -> Org ID)
    print("   Loading Reassignment Map...")
    reas = pd.read_csv(PECOS_REASSIGN, usecols=['REASGN_BNFT_ENRLMT_ID', 'RCV_BNFT_ENRLMT_ID'], dtype=str, encoding='latin1')
    
    # 3. Join to get Indiv NPI -> Org NPI
    merged = reas.merge(enrl, left_on='REASGN_BNFT_ENRLMT_ID', right_on='ENRLMT_ID', how='inner')
    merged.rename(columns={'NPI': 'indiv_npi'}, inplace=True)
    
    merged = merged.merge(enrl, left_on='RCV_BNFT_ENRLMT_ID', right_on='ENRLMT_ID', how='inner')
    merged.rename(columns={'NPI': 'org_npi'}, inplace=True)
    
    bridge = merged[['indiv_npi', 'org_npi']].drop_duplicates()
    print(f"   ✅ Built Bridge: {len(bridge):,} links (Indiv -> Org)")
    return bridge

def process_utilization_with_bridge(bridge):
    """
    Process Medicare utilization data in chunks, merging with PECOS bridge
    to aggregate directly by Organization NPI.
    
    Args:
        bridge: DataFrame with columns ['indiv_npi', 'org_npi'] or None
        
    Returns:
        DataFrame with columns ['npi', 'total_psych_codes', 'psych_risk_ratio']
    """
    print(f"🧠 Starting Behavioral Health Mining on {UTIL_FILE}")
    
    if not os.path.exists(UTIL_FILE):
        print(f"   ❌ Medicare file not found: {UTIL_FILE}")
        return None
    
    chunk_size = 100000
    org_chunks = []
    total_rows = 0
    matched_rows = 0
    
    # Process in chunks
    for chunk in pd.read_csv(UTIL_FILE, chunksize=chunk_size, 
                            usecols=['Rndrng_NPI', 'HCPCS_Cd', 'Tot_Srvcs'], 
                            dtype={'Rndrng_NPI': 'int64', 'HCPCS_Cd': str, 'Tot_Srvcs': float}):
        
        # Filter for target codes
        filtered = chunk[chunk['HCPCS_Cd'].isin(TARGET_CODES)].copy()
        
        if not filtered.empty:
            if bridge is not None:
                # Merge with bridge to get Org NPI
                filtered = filtered.merge(bridge, left_on='Rndrng_NPI', right_on='indiv_npi', how='inner')
                matched_rows += len(filtered)
                
                # Aggregate by Org NPI and Code
                agg = filtered.groupby(['org_npi', 'HCPCS_Cd'])['Tot_Srvcs'].sum().reset_index()
                agg.rename(columns={'org_npi': 'npi'}, inplace=True)
            else:
                # Fallback: use individual NPI as proxy for org
                agg = filtered.groupby(['Rndrng_NPI', 'HCPCS_Cd'])['Tot_Srvcs'].sum().reset_index()
                agg.rename(columns={'Rndrng_NPI': 'npi'}, inplace=True)
            
            org_chunks.append(agg)
        
        total_rows += len(chunk)
        sys.stdout.write(f"\r   Processed {total_rows:,} rows...")
        sys.stdout.flush()
        
    print("\n   ✅ Finished processing chunks.")
    
    if bridge is not None:
        print(f"   Mapped {matched_rows:,} utilization records to organizations via bridge.")
    
    if not org_chunks:
        print("   ⚠️  No psychotherapy codes found.")
        return None
        
    # Combine all chunks and aggregate by Org NPI
    print("   Aggregating results by Organization NPI...")
    full_df = pd.concat(org_chunks, ignore_index=True)
    final_agg = full_df.groupby(['npi', 'HCPCS_Cd'])['Tot_Srvcs'].sum().reset_index()
    
    # Pivot to get columns
    print("   Pivoting data...")
    pivot = final_agg.pivot(index='npi', columns='HCPCS_Cd', values='Tot_Srvcs').fillna(0)
    
    # Ensure all target columns exist
    for code in TARGET_CODES:
        if code not in pivot.columns:
            pivot[code] = 0
    
    # Calculate total psych codes
    pivot['total_psych_codes'] = pivot[TARGET_CODES].sum(axis=1)
    
    # Calculate high-scrutiny codes (60-min)
    pivot['high_scrutiny_codes'] = pivot[HIGH_SCRUTINY_CODES].sum(axis=1)
    
    # Filter for meaningful volume (e.g., at least 10 codes)
    pivot = pivot[pivot['total_psych_codes'] >= 10].copy()
    
    # Calculate psych risk ratio
    # Risk = (60-min codes) / (all psych codes)
    pivot['psych_risk_ratio'] = np.where(
        pivot['total_psych_codes'] > 0,
        pivot['high_scrutiny_codes'] / pivot['total_psych_codes'],
        0
    )
    
    print(f"   Identified {len(pivot):,} organizations with relevant behavioral health volume.")
    
    # Return only needed columns
    result = pivot.reset_index()[['npi', 'total_psych_codes', 'psych_risk_ratio', '90834', '90837']]
    return result

def main():
    print("="*80)
    print(" MINE BEHAVIORAL HEALTH CODES - AUDIT RISK METRICS (ORG-LEVEL)")
    print("="*80)
    
    # 1. Load PECOS Bridge
    bridge = load_pecos_bridge()
    
    if bridge is None:
        print("\n   ⚠️  WARNING: No bridge available. Using individual NPIs as proxy.")
        print("   💡 For production use, ensure PECOS files are available.")
    
    # 2. Process Utilization with Bridge
    org_metrics = process_utilization_with_bridge(bridge)
    
    if org_metrics is not None:
        # 3. Save
        org_metrics.to_csv(OUTPUT_FILE, index=False)
        print(f"\n   ✅ Saved Behavioral Health Metrics to: {OUTPUT_FILE}")
        print(f"   📊 Total Organizations: {len(org_metrics):,}")
        
        # 4. Report
        high_risk = org_metrics[org_metrics['psych_risk_ratio'] > 0.80]
        print(f"   🚨 High Audit Risk (> 0.80): {len(high_risk):,} organizations ({len(high_risk)/len(org_metrics)*100:.1f}%)")
        
        moderate_risk = org_metrics[(org_metrics['psych_risk_ratio'] >= 0.60) & (org_metrics['psych_risk_ratio'] <= 0.80)]
        print(f"   ⚠️  Moderate Risk (0.60-0.80): {len(moderate_risk):,} organizations ({len(moderate_risk)/len(org_metrics)*100:.1f}%)")
        
        low_risk = org_metrics[org_metrics['psych_risk_ratio'] < 0.60]
        print(f"   ✅ Low Risk (< 0.60): {len(low_risk):,} organizations ({len(low_risk)/len(org_metrics)*100:.1f}%)")
        
        # Distribution stats
        print(f"\n   📈 Psych Risk Ratio Distribution:")
        print(f"      Mean:   {org_metrics['psych_risk_ratio'].mean():.3f}")
        print(f"      Median: {org_metrics['psych_risk_ratio'].median():.3f}")
        print(f"      Min:    {org_metrics['psych_risk_ratio'].min():.3f}")
        print(f"      Max:    {org_metrics['psych_risk_ratio'].max():.3f}")
        
        # Volume stats
        print(f"\n   📊 Total Psych Codes Distribution:")
        print(f"      Mean:   {org_metrics['total_psych_codes'].mean():.0f}")
        print(f"      Median: {org_metrics['total_psych_codes'].median():.0f}")
        print(f"      Max:    {org_metrics['total_psych_codes'].max():.0f}")
    else:
        print("\n   ❌ No metrics generated. Check input data.")

if __name__ == "__main__":
    main()
