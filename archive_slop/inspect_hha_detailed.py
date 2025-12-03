"""
Detailed HHA Cost Report Inspection
"""
import pandas as pd

# Paths
hha_dir = "data/raw/cost_reports_hha/HHA20-REPORTS (1)"
cost_report = f"{hha_dir}/CostReporthha_Final_23.csv"
provider_info = f"{hha_dir}/HHA20_PRVDR_ID_INFO.CSV"

print("🏥 HHA COST REPORT DETAILED INSPECTION")
print("="*80)

# Load full file
print(f"\n1. Loading Cost Report...")
df_cost = pd.read_csv(cost_report)
print(f"   Total Rows: {len(df_cost):,}")
print(f"   Total Columns: {len(df_cost.columns)}")

# Show all columns
print(f"\n2. All Column Names:")
for i, col in enumerate(df_cost.columns):
    print(f"   {i+1}. {col}")

# Look for key financial columns
print(f"\n3. Key Financial Columns:")
key_cols = [
    'Net Patient Revenues (line 1 minus line 2) Total',
    'Net Income from service to patients (line 3 minus line 17)',
    'Net Income or Loss for the period (line 18 plus line 32)'
]

for col in key_cols:
    if col in df_cost.columns:
        print(f"   ✅ {col}")
        print(f"      Non-null: {df_cost[col].notnull().sum():,}")
        print(f"      Sample: {df_cost[col].head(3).tolist()}")

# Provider info
print(f"\n4. Provider Info File:")
df_prov = pd.read_csv(provider_info)
print(f"   Total Rows: {len(df_prov):,}")
print(f"   Columns: {list(df_prov.columns)}")
print(f"\n   Sample:")
print(df_prov.head(3))

# Check if cost report has provider info
print(f"\n5. Checking for Provider ID in Cost Report:")
prov_cols = [c for c in df_cost.columns if 'provider' in c.lower() or 'prvdr' in c.lower() or 'ccn' in c.lower()]
print(f"   Provider columns: {prov_cols}")

if prov_cols:
    print(f"\n   Sample data:")
    print(df_cost[prov_cols[:3]].head(3))
