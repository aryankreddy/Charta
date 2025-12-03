"""
Test Hospital SAS Integration
"""
import pandas as pd
import pyreadstat
import os

# Configuration
ROOT = os.getcwd()
DATA_RAW = os.path.join(ROOT, "data", "raw")
DATA_STAGING = os.path.join(ROOT, "data", "curated", "staging")

sas_dir = os.path.join(DATA_RAW, "cost_reports_hospitals", "hosp10-sas ")
sas_file = os.path.join(sas_dir, "prds_hosp10_yr2024.sas7bdat")

print("🏥 TESTING HOSPITAL SAS INTEGRATION")
print("="*80)

print(f"\n1. Loading SAS file: {sas_file}...")
hosp, meta = pyreadstat.read_sas7bdat(sas_file, encoding='iso-8859-1')
print(f"   ✅ Loaded {len(hosp):,} hospital records")

# Extract Key Metrics
hosp_extract = hosp[['prvdr_num', 'G3_C1_1', 'G3_C1_29']].copy()
hosp_extract.rename(columns={
    'prvdr_num': 'ccn',
    'G3_C1_1': 'hosp_revenue',
    'G3_C1_29': 'hosp_net_income'
}, inplace=True)

# Calculate margin
hosp_extract['hosp_margin'] = hosp_extract.apply(
    lambda row: (row['hosp_net_income'] / row['hosp_revenue']) if pd.notnull(row['hosp_revenue']) and row['hosp_revenue'] > 0 else None,
    axis=1
)

# Clean CCN
hosp_extract['ccn'] = hosp_extract['ccn'].astype(str).str.strip()

# Remove rows with missing financials
hosp_extract = hosp_extract[hosp_extract['hosp_revenue'].notnull() | hosp_extract['hosp_net_income'].notnull()]

print(f"\n2. Extracted Financial Data:")
print(f"   - Total Hospitals: {len(hosp_extract):,}")
print(f"   - With Revenue: {hosp_extract['hosp_revenue'].notnull().sum():,}")
print(f"   - With Net Income: {hosp_extract['hosp_net_income'].notnull().sum():,}")
print(f"   - With Margin: {hosp_extract['hosp_margin'].notnull().sum():,}")

print(f"\n3. Sample Data:")
print(hosp_extract.head(5))

print(f"\n4. Financial Summary:")
print(f"   - Avg Revenue: ${hosp_extract['hosp_revenue'].mean():,.0f}")
print(f"   - Avg Net Income: ${hosp_extract['hosp_net_income'].mean():,.0f}")
print(f"   - Avg Margin: {hosp_extract['hosp_margin'].mean():.2%}")

# Save
hosp_staging_path = os.path.join(DATA_STAGING, "stg_hospital_sas_2024.csv")
hosp_extract.to_csv(hosp_staging_path, index=False)
print(f"\n5. ✅ Saved to: {hosp_staging_path}")

print("\n" + "="*80)
print("✅ HOSPITAL SAS INTEGRATION TEST COMPLETE")
