# HCRIS Parser - Correctly Extract FQHC Financial Data
# Format: [RPT_REC_NUM, FACILITY_ID, LINE_NUM, CLMN_NUM, VALUE]

import os
import pandas as pd
import numpy as np

print("\n" + "="*80)
print("HCRIS DATA EXTRACTION: FQHC COST REPORTS 2024")
print("="*80)

# ============================================================================
# STEP 1: Load Report Metadata (_rpt.csv)
# ============================================================================

print("\nSTEP 1: Load Report Metadata")
fqhc_rpt_path = "data/raw/cost_reports_fqhc/FQHC14-ALL-YEARS (1)/FQHC14_2024_rpt.csv"

fqhc_rpt = pd.read_csv(fqhc_rpt_path, header=None)

# Based on HCRIS data dictionary, the columns should be:
# 0: RPT_REC_NUM
# 1: PRVDR_NUM (facility number, state code + facility)
# 2: ? (check with more columns)
fqhc_rpt.columns = [f'col{i}' for i in range(len(fqhc_rpt.columns))]
fqhc_rpt.rename(columns={'col0': 'RPT_REC_NUM', 'col2': 'PRVDR_NUM'}, inplace=True)

# Only assign as many as we have
# fqhc_rpt.columns = rpt_cols[:len(fqhc_rpt.columns)]

print(f"✅ Loaded report metadata: {len(fqhc_rpt):,} FQHCs")
print(f"   Columns: {list(fqhc_rpt.columns)}")
print(f"\nFirst row:")
print(fqhc_rpt.iloc[0])

# Try to find NPI - it should be in the first 18 columns
print(f"\n🔍 Looking for NPI (should be 10-digit number)...")
for col_idx in range(len(fqhc_rpt.columns)):
    try:
        val = fqhc_rpt.iloc[0, col_idx]
        if isinstance(val, (int, float)) and not pd.isna(val):
            if 1000000000 <= float(val) <= 9999999999:
                print(f"   ✅ Found potential NPI in column {col_idx}: {int(val)}")
    except:
        pass

# Save for inspection
fqhc_rpt.to_csv('data/curated/staging/fqhc_rpt_2024_debug.csv', index=False)
print(f"\n💾 Saved report metadata to: data/curated/staging/fqhc_rpt_2024_debug.csv")

# ============================================================================
# STEP 2: Load Numeric Data (_nmrc.csv)
# ============================================================================

print("\n" + "="*80)
print("STEP 2: Load Numeric Data (Financial Info)")
print("="*80)

fqhc_nmrc_path = "data/raw/cost_reports_fqhc/FQHC14-ALL-YEARS (1)/FQHC14_2024_nmrc.csv"

fqhc_nmrc = pd.read_csv(fqhc_nmrc_path, header=None)
fqhc_nmrc.columns = ['RPT_REC_NUM', 'FACILITY_ID', 'LINE_NUM', 'CLMN_NUM', 'VALUE']

print(f"✅ Loaded numeric data: {len(fqhc_nmrc):,} rows")
print(f"   Format: [RPT_REC_NUM, FACILITY_ID, LINE_NUM, CLMN_NUM, VALUE]")

print(f"\nUnique LINE_NUMs (worksheets):")
line_nums = fqhc_nmrc['LINE_NUM'].unique()
print(f"   {sorted(line_nums[:20])}...")  # Show first 20

print(f"\nSample data rows:")
print(fqhc_nmrc.head(10))

# ============================================================================
# STEP 3: Extract Key Financial Data Points
# ============================================================================

print("\n" + "="*80)
print("STEP 3: Extract Financial Data")
print("="*80)

# Key Line Numbers for FQHC Form 14:
# 0100 = Total Patient Revenue
# 0110 = Medicare Revenue (Inpatient)
# 0120 = Medicaid Revenue (Inpatient)
# 0130 = Other Revenue (Inpatient)
# 0200 = Total Operating Expenses
# 0300 = Net Income

# Try to extract common fields
key_lines = {
    '100': 'total_revenue',
    '110': 'medicare_revenue',
    '120': 'medicaid_revenue',
    '130': 'other_revenue',
    '200': 'total_expenses',
    '300': 'net_income',
    '3000': 'patient_encounters',  # G-3 worksheet
}

# Convert LINE_NUM to string for matching (it's int 100, not string "100")
fqhc_nmrc['LINE_NUM_STR'] = fqhc_nmrc['LINE_NUM'].astype(str).str.zfill(5)

print("\nExtracting by LINE_NUM:")
for line_code, field_name in key_lines.items():
    line_code_padded = line_code.zfill(5)
    matches = fqhc_nmrc[fqhc_nmrc['LINE_NUM_STR'] == line_code_padded]
    print(f"  {field_name} (line {line_code}): {len(matches):,} records")
    if len(matches) > 0:
        print(f"    Sample values: {matches['VALUE'].head(3).values}")

# ============================================================================
# STEP 4: Pivot Data for Easy Access
# ============================================================================

print("\n" + "="*80)
print("STEP 4: Pivot Numeric Data")
print("="*80)

# Pivot so each LINE_NUM becomes a column
fqhc_pivot = fqhc_nmrc.pivot_table(
    index='RPT_REC_NUM',
    columns='LINE_NUM',
    values='VALUE',
    aggfunc='first'  # If duplicates, take first
)

print(f"✅ Pivoted data: {len(fqhc_pivot):,} reports × {len(fqhc_pivot.columns)} line items")
print(f"\nTop columns (Line Numbers):")
print(f"   {list(fqhc_pivot.columns[:10])}")

# Check if our key fields exist
for line_num in [100, 110, 120, 130, 200, 300, 3000]:
    if line_num in fqhc_pivot.columns:
        non_null = fqhc_pivot[line_num].notna().sum()
        print(f"   Line {line_num}: {non_null:,} FQHCs have data")

fqhc_pivot.to_csv('data/curated/staging/fqhc_nmrc_2024_pivoted.csv')
print(f"\n💾 Saved pivoted data to: data/curated/staging/fqhc_nmrc_2024_pivoted.csv")

# ============================================================================
# STEP 5: Join with Report Metadata
# ============================================================================

print("\n" + "="*80)
print("STEP 5: Join Report + Numeric Data")
print("="*80)

# Reset index so RPT_REC_NUM is a column
fqhc_pivot_reset = fqhc_pivot.reset_index()

# Join on RPT_REC_NUM
fqhc_combined = fqhc_rpt.merge(
    fqhc_pivot_reset,
    on='RPT_REC_NUM',
    how='inner'
)

print(f"✅ Combined report + numeric data: {len(fqhc_combined):,} FQHCs")
print(f"   Columns: {len(fqhc_combined)}")

# ============================================================================
# STEP 6: Calculate Derived Metrics
# ============================================================================

print("\n" + "="*80)
print("STEP 6: Calculate Financial Metrics")
print("="*80)

if 100 in fqhc_combined.columns and 200 in fqhc_combined.columns:
    # Column 100 = total revenue, 200 = total expenses
    fqhc_combined['total_revenue'] = fqhc_combined[100]
    fqhc_combined['total_expenses'] = fqhc_combined[200]
    fqhc_combined['net_margin'] = (
        (fqhc_combined['total_revenue'] - fqhc_combined['total_expenses']) 
        / fqhc_combined['total_revenue']
    ).where(fqhc_combined['total_revenue'] > 0, np.nan)
    
    print(f"✅ Calculated margins:")
    print(f"   Mean margin: {fqhc_combined['net_margin'].mean():.3f}")
    print(f"   Median margin: {fqhc_combined['net_margin'].median():.3f}")
    print(f"   Min: {fqhc_combined['net_margin'].min():.3f}")
    print(f"   Max: {fqhc_combined['net_margin'].max():.3f}")

# Calculate payer mix if we have payer-specific revenue
if all(col in fqhc_combined.columns for col in [110, 120, 130]):
    fqhc_combined['medicare_revenue'] = fqhc_combined[110]
    fqhc_combined['medicaid_revenue'] = fqhc_combined[120]
    fqhc_combined['other_revenue'] = fqhc_combined[130]
    
    total_payer_revenue = (
        fqhc_combined['medicare_revenue'] + 
        fqhc_combined['medicaid_revenue'] + 
        fqhc_combined['other_revenue']
    )
    
    fqhc_combined['medicare_pct'] = fqhc_combined['medicare_revenue'] / total_payer_revenue
    fqhc_combined['medicaid_pct'] = fqhc_combined['medicaid_revenue'] / total_payer_revenue
    fqhc_combined['other_pct'] = fqhc_combined['other_revenue'] / total_payer_revenue
    
    print(f"\n✅ Calculated payer mix:")
    print(f"   Mean Medicare %: {fqhc_combined['medicare_pct'].mean():.1%}")
    print(f"   Mean Medicaid %: {fqhc_combined['medicaid_pct'].mean():.1%}")
    print(f"   Mean Other %: {fqhc_combined['other_pct'].mean():.1%}")

# ============================================================================
# STEP 7: Save Enriched FQHC Data
# ============================================================================

print("\n" + "="*80)
print("STEP 7: Save Enriched Data")
print("="*80)

# Keep only useful columns
output_cols = [
    'RPT_REC_NUM', 'PRVDR_NUM', 'total_revenue', 'total_expenses', 'net_margin',
    'medicare_revenue', 'medicaid_revenue', 'other_revenue',
    'medicare_pct', 'medicaid_pct', 'other_pct'
]

output_cols = [col for col in output_cols if col in fqhc_combined.columns]

fqhc_output = fqhc_combined[output_cols]
fqhc_output.to_csv('data/curated/staging/fqhc_enriched_2024.csv', index=False)

print(f"✅ Saved enriched FQHC data: {len(fqhc_output):,} FQHCs")
print(f"   Location: data/curated/staging/fqhc_enriched_2024.csv")
print(f"\nSample data:")
print(fqhc_output.head())

print("\n" + "="*80)
print("EXTRACTION COMPLETE")
print("="*80)
print(f"""
Next Steps:
1. Check if NPI is in the report file (columns to inspect)
2. Join FQHC enriched data to clinics_seed.csv on NPI
3. Apply same process to HHA and Hospital cost reports
4. Merge all enriched data with clinics_seed.csv
5. Re-run ICP scoring with real financial data
""")