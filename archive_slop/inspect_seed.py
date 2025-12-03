import pandas as pd
import os

SEED_FILE = "data/curated/clinics_seed.csv"

if os.path.exists(SEED_FILE):
    df = pd.read_csv(SEED_FILE, low_memory=False)
    print(f"Seed Rows: {len(df):,}")
    if 'npi' in df.columns:
        print(f"NPI Column Type: {df['npi'].dtype}")
        non_null = df['npi'].notnull().sum()
        print(f"Non-null NPIs: {non_null:,} ({non_null/len(df):.1%})")
        print(f"Sample NPIs: {df['npi'].head(5).tolist()}")
    else:
        print("❌ 'npi' column missing in seed file")
else:
    print("❌ Seed file not found")
