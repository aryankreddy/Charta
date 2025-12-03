# Comprehensive Data Extraction & Enrichment Pipeline
# Purpose: Extract ALL available datapoints from raw files into enriched dataset
# Output: clinics_enriched_complete.csv with 60%+ real data for ICP scoring

import os
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# STEP 1: EXTRACT PHYSICIAN UTILIZATION DATA (Medicare 2023)
# ============================================================================

print("\n" + "="*80)
print("STEP 1: EXTRACT PHYSICIAN UTILIZATION DATA")
print("="*80)

physician_util_path = "data/raw/physician_utilization/Medicare Physician & Other Practitioners - by Provider and Service/2023/MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv"

if os.path.exists(physician_util_path):
    print(f"Loading {physician_util_path}...")
    util = pd.read_csv(physician_util_path, dtype={'Rndrng_NPI': str})
    
    print(f"Raw rows: {len(util):,}")
    print(f"Columns: {util.columns.tolist()}")
    
    # Extract encounter volume by NPI
    npi_services = util.groupby('Rndrng_NPI').agg({
        'Tot_Srvcs': 'sum',
        'Tot_Benes': 'sum',
        'Avg_Mdcr_Alowd_Amt': 'mean',
        'Tot_Bene_Day_Srvcs': 'sum'
    }).reset_index()
    
    npi_services.columns = ['npi', 'total_services', 'total_beneficiaries', 'avg_medicare_allowed', 'total_patient_days']
    
    # E/M code percentage (CPT codes 99xxx)
    util['is_em'] = util['HCPCS_Cd'].astype(str).str.startswith('992')
    em_pct = util.groupby('Rndrng_NPI')['is_em'].mean().reset_index()
    em_pct.columns = ['npi', 'em_code_pct']
    
    # Merge
    npi_services = npi_services.merge(em_pct, on='npi', how='left')
    
    # Calculate Medicare revenue proxy
    npi_services['medicare_revenue_estimate'] = (
        npi_services['total_services'] * npi_services['avg_medicare_allowed']
    )
    
    print(f"✅ Extracted {len(npi_services):,} NPIs from physician utilization")
    print(f"   Fields: {npi_services.columns.tolist()}")
else:
    print(f"❌ File not found: {physician_util_path}")
    npi_services = pd.DataFrame()


# ============================================================================
# STEP 2: EXTRACT FQHC COST REPORT DATA (2024 Most Recent)
# ============================================================================

print("\n" + "="*80)
print("STEP 2: EXTRACT FQHC COST REPORT DATA")
print("="*80)

fqhc_base = "data/raw/cost_reports_fqhc/FQHC14-ALL-YEARS (1)"

# Use 2024 as most recent complete year
fqhc_rpt_2024 = os.path.join(fqhc_base, "FQHC14_2024_rpt.csv")
fqhc_nmrc_2024 = os.path.join(fqhc_base, "FQHC14_2024_nmrc.csv")

fqhc_data = pd.DataFrame()

if os.path.exists(fqhc_nmrc_2024):
    print(f"Loading FQHC numeric data (2024)...")
    
    # Load numeric data
    fqhc_nmrc = pd.read_csv(fqhc_nmrc_2024, dtype={'NPI': str})
    print(f"Raw FQHC rows: {len(fqhc_nmrc):,}")
    print(f"Columns: {fqhc_nmrc.columns.tolist()}")
    
    # HCRIS structure: LINE_NUM and CLMN_NUM identify specific data points
    # We need to extract key worksheets:
    # - S-10: Revenue by source (lines identify Medicaid, Medicare, commercial revenue)
    # - G-3: Patient volume data
    # - A: Administrative data (including IT costs)
    
    # Extract revenue data (S-10 worksheet)
    # Line 0100 = Total Patient Revenue
    # Line 0100.01 = Medicare
    # Line 0100.02 = Medicaid
    # Line 0100.03 = Other
    
    revenue_data = fqhc_nmrc[fqhc_nmrc['LINE_NUM'].isin([100, 10001, 10002, 10003])].copy()
    
    # Pivot by LINE_NUM to get revenue components
    if len(revenue_data) > 0:
        revenue_pivot = revenue_data.pivot_table(
            index='NPI',
            columns='LINE_NUM',
            values='ITM_VAL_NUM',
            aggfunc='sum'
        ).reset_index()
        
        revenue_pivot.columns.name = None
        revenue_pivot.columns = ['npi'] + [f'line_{int(c)}' if isinstance(c, (int, float)) else c for c in revenue_pivot.columns[1:]]
        
        print(f"✅ Extracted revenue data for {len(revenue_pivot):,} FQHCs")
        fqhc_data = revenue_pivot
    
    # Try to extract encounter volume (G-3 worksheet, around line 03000)
    encounters_data = fqhc_nmrc[fqhc_nmrc['LINE_NUM'].isin([3000, 3001, 3002])].copy()
    if len(encounters_data) > 0:
        encounters_pivot = encounters_data.pivot_table(
            index='NPI',
            columns='LINE_NUM',
            values='ITM_VAL_NUM',
            aggfunc='sum'
        ).reset_index()
        
        if len(fqhc_data) > 0:
            fqhc_data = fqhc_data.merge(encounters_pivot, on='NPI', how='left', suffixes=('_revenue', '_encounters'))
        else:
            fqhc_data = encounters_pivot
        
        print(f"✅ Extracted encounter data from G-3 worksheet")
    
    # Save to see structure
    if len(fqhc_data) > 0:
        fqhc_data.to_csv('data/curated/staging/fqhc_extracted_2024.csv', index=False)
        print(f"   Saved to data/curated/staging/fqhc_extracted_2024.csv")
else:
    print(f"❌ FQHC numeric file not found: {fqhc_nmrc_2024}")


# ============================================================================
# STEP 3: EXTRACT NPI REGISTRY DATA
# ============================================================================

print("\n" + "="*80)
print("STEP 3: EXTRACT NPI REGISTRY DATA")
print("="*80)

# You have a zip file - need to unzip first
npi_zip = "data/raw/npi_registry/NPPES_Data_Dissemination_November_2025.zip"

if os.path.exists(npi_zip):
    print(f"NPI registry exists as zip: {npi_zip}")
    print("⚠️  Need to unzip to extract provider data")
    print("   Columns expected: NPI, Provider Name, Taxonomy Code, Address, City, State, etc.")
else:
    print(f"❌ NPI registry zip not found")


# ============================================================================
# STEP 4: JOIN ALL DATA TO clinics_seed
# ============================================================================

print("\n" + "="*80)
print("STEP 4: JOIN ALL DATA TO clinics_seed.csv")
print("="*80)

clinics_seed = pd.read_csv("data/curated/clinics_seed.csv", low_memory=False)
print(f"Loaded clinics_seed: {len(clinics_seed):,} rows, {clinics_seed.columns.tolist()}")

# Join physician utilization
clinics_enriched = clinics_seed.merge(
    npi_services[['npi', 'total_services', 'em_code_pct', 'medicare_revenue_estimate']],
    left_on='npi',
    right_on='npi',
    how='left'
)

print(f"\n✅ After physician util join: {len(clinics_enriched):,} rows")
print(f"   Filled services_count: {clinics_enriched['total_services'].notna().sum():,} clinics")
print(f"   Filled em_code_pct: {clinics_enriched['em_code_pct'].notna().sum():,} clinics")

# Output enriched dataset
clinics_enriched.to_csv('data/curated/clinics_enriched_physician_util.csv', index=False)
print(f"\n✅ Saved enriched dataset: data/curated/clinics_enriched_physician_util.csv")


# ============================================================================
# STEP 5: DATA GAP ANALYSIS
# ============================================================================

print("\n" + "="*80)
print("STEP 5: DATA GAP ANALYSIS")
print("="*80)

print(f"\n📊 CURRENT COVERAGE:")
print(f"   Total clinics: {len(clinics_enriched):,}")
print(f"   ✅ Physician util data: {clinics_enriched['total_services'].notna().sum():,} ({100*clinics_enriched['total_services'].notna().sum()/len(clinics_enriched):.1f}%)")
print(f"   ✅ E/M code %: {clinics_enriched['em_code_pct'].notna().sum():,} ({100*clinics_enriched['em_code_pct'].notna().sum()/len(clinics_enriched):.1f}%)")
print(f"   ❌ FQHC margin data: Limited (only 101 FQHCs in processed file)")
print(f"   ❌ Payer mix breakdown: Need to extract from FQHC cost reports")
print(f"   ❌ Procedures vs E/M: Partial (from physician util CPT codes)")

print(f"\n🔧 NEXT STEPS TO MAXIMIZE DATA:")
print(f"   1. Unzip NPI registry → Extract provider count, taxonomy, organization type")
print(f"   2. Parse FQHC cost report numeric lines → Extract revenue, expenses, encounters")
print(f"   3. Extract payer mix from FQHC worksheets (S-10 revenue lines)")
print(f"   4. Join hospital cost reports (same structure as FQHC)")
print(f"   5. Use OIG LEIE matches for audit flag")

print("\n" + "="*80)
print("EXTRACTION COMPLETE")
print("="*80)