"""
Inspect HHA Cost Report Structure
"""
import pandas as pd

# Paths
hha_dir = "data/raw/cost_reports_hha/HHA20-REPORTS (1)"
cost_report = f"{hha_dir}/CostReporthha_Final_23.csv"
provider_info = f"{hha_dir}/HHA20_PRVDR_ID_INFO.CSV"

print("🏥 INSPECTING HHA COST REPORTS")
print("="*80)

# 1. Cost Report File
print(f"\n1. Cost Report File: {cost_report}")
df_cost = pd.read_csv(cost_report, nrows=10)
print(f"   Rows (sample): 10")
print(f"   Columns: {len(df_cost.columns)}")
print(f"\n   Column Names (first 30):")
for i, col in enumerate(df_cost.columns[:30]):
    print(f"   {i+1}. {col}")

print(f"\n   Sample Data:")
print(df_cost.head(3))

# 2. Provider Info File
print(f"\n2. Provider Info File: {provider_info}")
df_prov = pd.read_csv(provider_info, nrows=10)
print(f"   Rows (sample): 10")
print(f"   Columns: {len(df_prov.columns)}")
print(f"\n   Column Names:")
for i, col in enumerate(df_prov.columns):
    print(f"   {i+1}. {col}")

print(f"\n   Sample Data:")
print(df_prov.head(3))

# 3. Look for key columns
print(f"\n3. Looking for Key Columns in Cost Report:")

# Provider Number
prvdr_cols = [c for c in df_cost.columns if 'PRVDR' in c.upper() or 'PROVIDER' in c.upper()]
print(f"   Provider columns: {prvdr_cols[:5]}")

# Revenue/Income
rev_cols = [c for c in df_cost.columns if 'REV' in c.upper() or 'INCOME' in c.upper() or 'G2' in c.upper() or 'G3' in c.upper()]
print(f"   Revenue/Income columns (first 10): {rev_cols[:10]}")

# Worksheet columns
wksht_cols = [c for c in df_cost.columns if 'WKSHT' in c.upper() or 'LINE' in c.upper()]
print(f"   Worksheet columns (first 10): {wksht_cols[:10]}")

print("\n" + "="*80)
