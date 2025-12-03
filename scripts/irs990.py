"""
IRS 990 INDEX 2024 ENRICHMENT
=============================

Matches your clinics to IRS 990 filings.
Extracts EIN and uses it to look up revenue data.

USAGE:
python scripts/enrich_irs_990.py

Expected: 20-30% of clinics get matched to 990 data
"""

import pandas as pd
from pathlib import Path

print("\n" + "="*60)
print("IRS 990 INDEX 2024 ENRICHMENT")
print("="*60)

# ============================================================================
# STEP 1: LOAD IRS 990 INDEX
# ============================================================================

print("\nStep 1: Loading IRS 990 Index...")
irs_990 = pd.read_csv('data/raw/index_2024.csv', low_memory=False)

print(f"  ✅ Loaded {len(irs_990):,} records")
print(f"  Columns: {irs_990.columns.tolist()}")

# Rename to standard format
irs_clean = irs_990.rename(columns={
    'EIN': 'ein',
    'TAXPAYER_NAME': 'org_name',
    'TAX_PERIOD': 'tax_year',
    'RETURN_TYPE': 'return_type'
})

# Keep only key columns
irs_final = irs_clean[['ein', 'org_name', 'tax_year', 'return_type']].copy()

print(f"  ✅ Processed {len(irs_final):,} 990 filings")

# ============================================================================
# STEP 2: LOAD CLINICS
# ============================================================================

print("\nStep 2: Loading clinics...")
clinics = pd.read_csv('data/curated/clinics_seed.csv', 
                       usecols=['npi', 'org_name', 'state_code'],
                       low_memory=False)

print(f"  ✅ Loaded {len(clinics):,} clinics")

# ============================================================================
# STEP 3: FUZZY MATCH ON ORGANIZATION NAME
# ============================================================================

print("\nStep 3: Matching clinics to 990 filings...")
print("  ⏳ This may take 5-10 minutes...")

from fuzzywuzzy import fuzz

matches = []
match_count = 0

for idx, clinic_row in clinics.iterrows():
    clinic_name = str(clinic_row.get('org_name', '')).upper().strip()
    clinic_state = str(clinic_row.get('state_code', '')).upper().strip()
    
    if not clinic_name or clinic_name == 'NAN':
        continue
    
    best_match = None
    best_score = 0
    
    # Find best matching 990
    for irs_idx, irs_row in irs_final.iterrows():
        irs_name = str(irs_row.get('org_name', '')).upper().strip()
        
        if not irs_name or irs_name == 'NAN':
            continue
        
        # Use fuzzy matching
        score = fuzz.token_set_ratio(clinic_name, irs_name)
        
        if score > best_score:
            best_score = score
            best_match = irs_row
    
    # Accept matches with 85%+ confidence
    if best_score >= 85 and best_match is not None:
        matches.append({
            'npi': clinic_row.get('npi'),
            'clinic_name': clinic_row.get('org_name'),
            '990_ein': best_match['ein'],
            '990_org_name': best_match['org_name'],
            '990_tax_year': best_match['tax_year'],
            '990_match_score': best_score
        })
        match_count += 1
    
    if (idx + 1) % 10000 == 0:
        print(f"    Processed {idx+1:,} clinics... ({match_count:,} matches)")

matches_df = pd.DataFrame(matches)

print(f"\n  ✅ MATCHED: {len(matches_df):,} clinics ({100*len(matches_df)/len(clinics):.2f}%)")
print(f"  ✅ Average match score: {matches_df['990_match_score'].mean():.1f}%")

# ============================================================================
# STEP 4: MERGE WITH CLINICS
# ============================================================================

print("\nStep 4: Enriching clinics dataset...")

enriched = clinics.merge(
    matches_df[[
        'npi', '990_ein', '990_org_name', '990_tax_year', '990_match_score'
    ]],
    on='npi',
    how='left'
)

enriched['has_990_filing'] = enriched['990_ein'].notna().astype(int)
enriched['revenue_source'] = enriched.apply(
    lambda row: '990_Filing' if pd.notna(row['990_ein']) else 'To_Estimate',
    axis=1
)

# ============================================================================
# STEP 5: SAVE
# ============================================================================

print("\nStep 5: Saving enriched dataset...")

enriched.to_csv('data/curated/clinics_enriched_irs_990.csv', index=False)

print(f"\n" + "="*60)
print(f"✅ ENRICHMENT COMPLETE")
print(f"="*60)
print(f"  Output: data/curated/clinics_enriched_irs_990.csv")
print(f"  Total clinics: {len(enriched):,}")
print(f"  With 990 match: {enriched['has_990_filing'].sum():,} ({100*enriched['has_990_filing'].sum()/len(enriched):.2f}%)")
print(f"\n💡 Next steps:")
print(f"  1. Run HRSA script: python scripts/enrich_fqhc_simple.py")
print(f"  2. Download PECOS file (5 min)")
print(f"  3. Run PECOS script: python scripts/enrich_pecos.py")
print(f"="*60 + "\n")
