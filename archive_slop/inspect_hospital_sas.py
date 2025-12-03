"""
Inspect Hospital SAS File Structure
"""
import pandas as pd
import pyreadstat

# Load the latest SAS file
sas_path = "data/raw/cost_reports_hospitals/hosp10-sas /prds_hosp10_yr2024.sas7bdat"

print("Loading SAS file...")
df, meta = pyreadstat.read_sas7bdat(sas_path, encoding='iso-8859-1')

print(f"\n📊 File Info:")
print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")

print(f"\n📋 Column Names (first 30):")
for i, col in enumerate(df.columns[:30]):
    print(f"{i+1}. {col}")

print(f"\n🔍 Looking for Key Columns:")

# Provider Number
prvdr_cols = [c for c in df.columns if 'PRVDR' in c.upper() and 'NUM' in c.upper()]
print(f"\nProvider Number candidates: {prvdr_cols}")

# Revenue
rev_cols = [c for c in df.columns if 'REV' in c.upper() or 'INCOME' in c.upper()]
print(f"\nRevenue/Income candidates (first 10): {rev_cols[:10]}")

# Name
name_cols = [c for c in df.columns if 'NAME' in c.upper() or 'PRVDR' in c.upper()]
print(f"\nName candidates (first 10): {name_cols[:10]}")

# Worksheet G-3 related
g3_cols = [c for c in df.columns if 'G3' in c.upper() or 'WKSHT' in c.upper()]
print(f"\nWorksheet G-3 candidates (first 10): {g3_cols[:10]}")

print(f"\n📄 Sample Data (first 3 rows, key columns):")
if prvdr_cols:
    sample_cols = prvdr_cols[:2] + name_cols[:2] + rev_cols[:3]
    print(df[sample_cols].head(3))
else:
    print(df.iloc[:3, :10])

print(f"\n💡 Column Metadata:")
print(f"Total columns: {len(meta.column_names)}")
print(f"Column labels available: {len(meta.column_labels) if meta.column_labels else 0}")
