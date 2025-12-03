"""
HRSA FQHC Site Enrichment - SIMPLE VERSION

Uses HRSA sites directory to flag verified FQHCs by NPI.

USAGE:
python scripts/enrich_fqhc_simple.py
"""

import pandas as pd

HRSA_INPUT = "data/raw/hrsa_fqhc/hrsa_sites.csv"
CLINICS_INPUT = "data/curated/clinics_seed.csv"
OUTPUT = "data/curated/clinics_enriched_hrsa_fqhc.csv"

print("\n" + "="*60)
print("HRSA FQHC SITE ENRICHMENT")
print("="*60)

print("\nLoading HRSA sites...")
hrsa = pd.read_csv(HRSA_INPUT, low_memory=False)
print(f"  ✅ Loaded {len(hrsa):,} rows")
print(f"  Columns: {hrsa.columns.tolist()}")

# Standardize columns
hrsa_clean = hrsa.rename(columns={
    'FQHC Site NPI Number': 'npi',
    'Site Name': 'site_name',
    'Site State Abbreviation': 'state'
})

hrsa_clean = hrsa_clean[['npi', 'site_name', 'state']].copy()
hrsa_clean = hrsa_clean.dropna(subset=['npi'])
hrsa_clean['npi'] = hrsa_clean['npi'].astype(str).str.strip()
hrsa_clean['is_verified_fqhc'] = 1

print(f"  ✅ Processed {len(hrsa_clean):,} FQHC site records")

print("\nLoading clinics...")
clinics = pd.read_csv(CLINICS_INPUT, low_memory=False)
clinics['npi'] = clinics['npi'].astype(str).str.strip()
print(f"  ✅ Loaded {len(clinics):,} clinics")

print("\nMerging HRSA FQHC flags into clinics...")
enriched = clinics.merge(
    hrsa_clean[['npi', 'is_verified_fqhc', 'site_name']],
    on='npi',
    how='left'
)

enriched['is_verified_fqhc'] = enriched['is_verified_fqhc'].fillna(0).astype(int)

matches = enriched['is_verified_fqhc'].sum()
print(f"  ✅ Matched {matches:,} verified FQHCs "
      f"({100 * matches / len(enriched):.2f}% of clinics)")

print("\nSaving enriched file...")
enriched.to_csv(OUTPUT, index=False)
print(f"  ✅ Saved to: {OUTPUT}")
print("\nDone.\n")
