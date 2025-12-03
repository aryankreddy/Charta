"""
Examine G3 Worksheet Columns (Income Statement)
"""
import pandas as pd
import pyreadstat

sas_path = "data/raw/cost_reports_hospitals/hosp10-sas /prds_hosp10_yr2024.sas7bdat"

print("Loading SAS file...")
df, meta = pyreadstat.read_sas7bdat(sas_path, encoding='iso-8859-1')

# Get all G3 columns
g3_cols = [c for c in df.columns if c.startswith('G3_')]
print(f"\n📊 Found {len(g3_cols)} G3 columns")

# According to HCRIS documentation:
# G3_C1_1 = Total Patient Revenue (Line 1)
# G3_C1_29 = Net Income (Line 29)

key_cols = {
    'G3_C1_1': 'Total Patient Revenue (Line 1)',
    'G3_C1_29': 'Net Income (Line 29)',
    'G3_C1_3': 'Total Operating Revenue (Line 3)',
    'G3_C1_25': 'Total Expenses (Line 25)'
}

print(f"\n🔑 Key Financial Columns:")
for col, desc in key_cols.items():
    if col in df.columns:
        print(f"✅ {col}: {desc}")
        print(f"   Sample values: {df[col].head(3).tolist()}")
        print(f"   Non-null: {df[col].notnull().sum():,} / {len(df):,}")
    else:
        print(f"❌ {col}: NOT FOUND")

# Check for provider name
print(f"\n📛 Provider Name:")
if '_NAME_' in df.columns:
    print(f"Column: _NAME_")
    print(f"Sample: {df['_NAME_'].head(3).tolist()}")
else:
    # Look for other name columns
    name_candidates = [c for c in df.columns if 'name' in c.lower()]
    print(f"Name candidates: {name_candidates[:5]}")

# Sample record
print(f"\n📄 Sample Hospital Record:")
sample_cols = ['prvdr_num', 'state'] + [c for c in key_cols.keys() if c in df.columns]
print(df[sample_cols].head(3))

# Check data types
print(f"\n📋 Data Types:")
for col in sample_cols:
    if col in df.columns:
        print(f"{col}: {df[col].dtype}")
