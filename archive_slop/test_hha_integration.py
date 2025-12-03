"""
Test HHA Integration
"""
import pandas as pd
import numpy as np
import os

# Configuration
ROOT = os.getcwd()
DATA_RAW = os.path.join(ROOT, "data", "raw")
DATA_STAGING = os.path.join(ROOT, "data", "curated", "staging")

def normalize_name(name):
    """Normalize organization name for matching."""
    if pd.isna(name): return ""
    name = str(name).upper().strip()
    name = name.replace(".", "").replace(",", "").replace(" INC", "").replace(" LLC", "").replace(" PC", "")
    name = name.replace(" CLINIC", "").replace(" CENTER", "").replace(" HEALTH", "")
    return name

print("🏥 TESTING HHA INTEGRATION")
print("="*80)

# 1. Load HHA data
hha_dir = os.path.join(DATA_RAW, "cost_reports_hha", "HHA20-REPORTS (1)")
hha_file = os.path.join(hha_dir, "CostReporthha_Final_23.csv")

print(f"\n1. Loading HHA file: {hha_file}...")
hha = pd.read_csv(hha_file)
print(f"   ✅ Loaded {len(hha):,} HHA records")

# 2. Extract financials
rev_col = 'Net Patient Revenues (line 1 minus line 2) Total'
inc_col = 'Net Income or Loss for the period (line 18 plus line 32)'

hha_extract = hha[['Provider CCN', 'HHA Name', rev_col, inc_col]].copy()
hha_extract.rename(columns={
    'Provider CCN': 'ccn',
    'HHA Name': 'hha_name',
    rev_col: 'hha_revenue',
    inc_col: 'hha_net_income'
}, inplace=True)

# Calculate margin
hha_extract['hha_margin'] = hha_extract.apply(
    lambda row: (row['hha_net_income'] / row['hha_revenue']) if pd.notnull(row['hha_revenue']) and row['hha_revenue'] > 0 else None,
    axis=1
)

# Remove rows with missing financials
hha_extract = hha_extract[hha_extract['hha_revenue'].notnull() | hha_extract['hha_net_income'].notnull()]

print(f"\n2. Extracted Financial Data:")
print(f"   - Total HHAs: {len(hha_extract):,}")
print(f"   - With Revenue: {hha_extract['hha_revenue'].notnull().sum():,}")
print(f"   - With Net Income: {hha_extract['hha_net_income'].notnull().sum():,}")
print(f"   - With Margin: {hha_extract['hha_margin'].notnull().sum():,}")

print(f"\n3. Sample Data:")
print(hha_extract.head(5))

print(f"\n4. Financial Summary:")
print(f"   - Avg Revenue: ${hha_extract['hha_revenue'].mean():,.0f}")
print(f"   - Avg Net Income: ${hha_extract['hha_net_income'].mean():,.0f}")
print(f"   - Avg Margin: {hha_extract['hha_margin'].mean():.2%}")

# 5. Test name normalization
print(f"\n5. Name Normalization Test:")
hha_extract['norm_name'] = hha_extract['hha_name'].apply(normalize_name)
print(f"   Sample normalized names:")
for i, row in hha_extract.head(5).iterrows():
    print(f"   {row['hha_name']} -> {row['norm_name']}")

# Save
hha_staging_path = os.path.join(DATA_STAGING, "stg_hha_2023.csv")
hha_extract.to_csv(hha_staging_path, index=False)
print(f"\n6. ✅ Saved to: {hha_staging_path}")

print("\n" + "="*80)
print("✅ HHA INTEGRATION TEST COMPLETE")
