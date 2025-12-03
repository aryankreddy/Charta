"""
ENHANCED UNDERCODING EXTRACTION v2.0
Author: Charta Health GTM Strategy

IMPROVEMENTS:
1. Provider-to-Clinic Rollup: Uses PECOS bridge to aggregate provider data
2. Lower Volume Threshold: 10+ codes (was 100+)
3. Expanded E&M Codes: Includes consultation, ER, and preventive codes

Target: 70-85% coverage (vs 16.8% current)
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PHYSICIAN_UTIL = os.path.join(ROOT, "data", "raw", "physician_utilization", 
                               "Medicare Physician & Other Practitioners - by Provider and Service", 
                               "2023", "MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv")
PECOS_BRIDGE = os.path.join(ROOT, "data", "curated", "staging", "stg_pecos_bridge.csv")
OUTPUT_FILE = os.path.join(ROOT, "data", "curated", "staging", "stg_undercoding_metrics.csv")

# EXPANDED E&M CODE RANGES
EM_CODES = {
    # Office Visits (Original)
    'office_new': ['99201', '99202', '99203', '99204', '99205'],
    'office_est': ['99211', '99212', '99213', '99214', '99215'],
    
    # Consultations (NEW)
    'consult_office': ['99241', '99242', '99243', '99244', '99245'],
    
    # Emergency Room (NEW)
    'er_visits': ['99281', '99282', '99283', '99284', '99285'],
    
    # Preventive Medicine (NEW)
    'preventive_new': ['99381', '99382', '99383', '99384', '99385', '99386', '99387'],
    'preventive_est': ['99391', '99392', '99393', '99394', '99395', '99396', '99397']
}

# Flatten all codes
ALL_EM_CODES = []
for category, codes in EM_CODES.items():
    ALL_EM_CODES.extend(codes)

# National Benchmark: Level 3 vs Level 4 distribution
# Based on CMS data, healthy distribution is ~50% Level 3, 50% Level 4+
LEVEL_3_CODES = ['99203', '99213', '99243', '99283', '99393']  # Representative Level 3
LEVEL_4_CODES = ['99204', '99214', '99244', '99284', '99394']  # Representative Level 4
LEVEL_5_CODES = ['99205', '99215', '99245', '99285', '99395']  # Representative Level 5

def extract_undercoding():
    print("🔍 ENHANCED UNDERCODING EXTRACTION v2.0")
    print("="*80)
    
    if not os.path.exists(PHYSICIAN_UTIL):
        print(f"❌ Physician Utilization file not found: {PHYSICIAN_UTIL}")
        return
    
    # STEP 1: Extract E&M Codes (Chunked Processing)
    print("\n📊 STEP 1: Extracting E&M codes from Medicare claims...")
    print(f"   Target Codes: {len(ALL_EM_CODES)} E&M codes (expanded range)")
    
    em_data = []
    chunk_size = 500000
    chunks_processed = 0
    
    for chunk in pd.read_csv(PHYSICIAN_UTIL, chunksize=chunk_size, low_memory=False, dtype=str):
        chunks_processed += 1
        
        # Filter for E&M codes
        em_chunk = chunk[chunk['HCPCS_Cd'].isin(ALL_EM_CODES)].copy()
        
        if not em_chunk.empty:
            # Keep only needed columns
            em_chunk = em_chunk[['Rndrng_NPI', 'HCPCS_Cd', 'Tot_Srvcs']].copy()
            em_chunk['Tot_Srvcs'] = pd.to_numeric(em_chunk['Tot_Srvcs'], errors='coerce').fillna(0)
            em_data.append(em_chunk)
        
        if chunks_processed % 5 == 0:
            print(f"   Processed {chunks_processed} chunks...")
    
    if not em_data:
        print("❌ No E&M codes found in claims data.")
        return
    
    # Combine all chunks
    em_df = pd.concat(em_data, ignore_index=True)
    print(f"✅ Found {len(em_df):,} E&M claim records")
    
    # STEP 2: Calculate Undercoding at Provider Level
    print("\n📈 STEP 2: Calculating undercoding ratios...")
    
    # Pivot to get counts per code
    provider_em = em_df.pivot_table(
        index='Rndrng_NPI',
        columns='HCPCS_Cd',
        values='Tot_Srvcs',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # Calculate Level 3 vs Level 4+ distribution
    level3_cols = [c for c in LEVEL_3_CODES if c in provider_em.columns]
    level4_cols = [c for c in LEVEL_4_CODES + LEVEL_5_CODES if c in provider_em.columns]
    
    provider_em['level3_count'] = provider_em[level3_cols].sum(axis=1) if level3_cols else 0
    provider_em['level4_count'] = provider_em[level4_cols].sum(axis=1) if level4_cols else 0
    provider_em['total_eval_codes'] = provider_em['level3_count'] + provider_em['level4_count']
    
    # Undercoding Ratio = Level 3 / (Level 3 + Level 4)
    # Higher ratio = more Level 3 codes = potential undercoding
    provider_em['undercoding_ratio'] = np.where(
        provider_em['total_eval_codes'] > 0,
        provider_em['level3_count'] / provider_em['total_eval_codes'],
        np.nan
    )
    
    # LOWERED THRESHOLD: Keep providers with 10+ codes (was 100+)
    provider_em = provider_em[provider_em['total_eval_codes'] >= 10].copy()
    
    print(f"✅ {len(provider_em):,} providers with 10+ E&M codes")
    print(f"   Mean Undercoding Ratio: {provider_em['undercoding_ratio'].mean():.3f}")
    print(f"   Severe Undercoding (<0.30): {len(provider_em[provider_em['undercoding_ratio'] < 0.30]):,}")
    
    # STEP 3: Roll Up to Clinic Level (via PECOS Bridge)
    print("\n🏥 STEP 3: Rolling up to clinic level...")
    
    if not os.path.exists(PECOS_BRIDGE):
        print(f"⚠️  PECOS Bridge not found. Saving provider-level data only.")
        clinic_em = provider_em.rename(columns={'Rndrng_NPI': 'npi'})
        clinic_em['npi'] = pd.to_numeric(clinic_em['npi'], errors='coerce').astype('Int64')
    else:
        # Load PECOS bridge
        bridge = pd.read_csv(PECOS_BRIDGE, dtype=str)
        bridge = bridge[['provider_npi', 'clinic_npi']].drop_duplicates()
        
        print(f"   Loaded {len(bridge):,} provider-to-clinic mappings")
        
        # Merge provider data with bridge
        provider_em['provider_npi'] = provider_em['Rndrng_NPI']
        merged = provider_em.merge(bridge, on='provider_npi', how='left')
        
        # Use clinic_npi if available, else use provider_npi (solo practitioners)
        merged['npi'] = merged['clinic_npi'].fillna(merged['provider_npi'])
        
        # Aggregate to clinic level
        clinic_em = merged.groupby('npi').agg({
            'level3_count': 'sum',
            'level4_count': 'sum',
            'total_eval_codes': 'sum'
        }).reset_index()
        
        # Recalculate ratio at clinic level
        clinic_em['undercoding_ratio'] = np.where(
            clinic_em['total_eval_codes'] > 0,
            clinic_em['level3_count'] / clinic_em['total_eval_codes'],
            np.nan
        )
        
        # Convert NPI to Int64
        clinic_em['npi'] = pd.to_numeric(clinic_em['npi'], errors='coerce').astype('Int64')
        
        print(f"✅ Rolled up to {len(clinic_em):,} clinics")
        print(f"   Mean Undercoding Ratio: {clinic_em['undercoding_ratio'].mean():.3f}")
        print(f"   Severe Undercoding (<0.30): {len(clinic_em[clinic_em['undercoding_ratio'] < 0.30]):,}")
    
    # STEP 4: Save Output
    print("\n💾 STEP 4: Saving output...")
    
    # Keep only needed columns
    output_cols = ['npi', 'total_eval_codes', 'undercoding_ratio']
    clinic_em[output_cols].to_csv(OUTPUT_FILE, index=False)
    
    print(f"✅ Saved to {OUTPUT_FILE}")
    
    # STEP 5: Coverage Report
    print("\n📊 COVERAGE IMPROVEMENT REPORT:")
    print(f"   Total Clinics with Undercoding Data: {len(clinic_em):,}")
    print(f"   Avg E&M Codes per Clinic: {clinic_em['total_eval_codes'].mean():.0f}")
    print(f"   Median E&M Codes: {clinic_em['total_eval_codes'].median():.0f}")
    
    print(f"\n   Distribution by Undercoding Severity:")
    severe = len(clinic_em[clinic_em['undercoding_ratio'] < 0.30])
    moderate = len(clinic_em[(clinic_em['undercoding_ratio'] >= 0.30) & (clinic_em['undercoding_ratio'] < 0.45)])
    mild = len(clinic_em[clinic_em['undercoding_ratio'] >= 0.45])
    
    print(f"      Severe (<0.30): {severe:,} ({severe/len(clinic_em):.1%})")
    print(f"      Moderate (0.30-0.45): {moderate:,} ({moderate/len(clinic_em):.1%})")
    print(f"      Mild (>0.45): {mild:,} ({mild/len(clinic_em):.1%})")
    
    print(f"\n🎯 EXPECTED IMPACT:")
    print(f"   Previous Coverage: ~113,905 clinics (16.8% of 1.4M)")
    print(f"   New Coverage: {len(clinic_em):,} clinics")
    print(f"   Improvement: {(len(clinic_em) - 113905):,} additional clinics")

if __name__ == "__main__":
    extract_undercoding()
