import pandas as pd
import os

STAGING_DIR = "data/curated/staging"

files = [
    "stg_physician_util.parquet",
    "stg_aco_orgs.parquet",
    "stg_hrsa_sites.parquet"
]

print("="*60)
print("INSPECTING STAGING FILES")
print("="*60)

for f in files:
    path = os.path.join(STAGING_DIR, f)
    print(f"\n📄 File: {f}")
    if os.path.exists(path):
        try:
            df = pd.read_parquet(path)
            print(f"   Rows: {len(df):,}")
            print(f"   Columns: {df.columns.tolist()}")
            print("   Sample Data:")
            print(df.head(3).to_string())
            
            # Check NPI type
            if 'npi' in df.columns:
                print(f"   NPI Type: {df['npi'].dtype}")
                print(f"   Sample NPIs: {df['npi'].head(3).tolist()}")
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
    else:
        print("   ❌ File not found")
