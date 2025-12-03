import pandas as pd
import os

path = "data/curated/clinics_seed.csv"

def validate():
    if not os.path.exists(path):
        print("❌ File not found.")
        return

    print(f"🔍 Inspecting Data Quality in {path}...")
    df = pd.read_csv(path, low_memory=False)
    
    # 1. SEGMENT DISTRIBUTION (The most important check)
    print("\n--- 1. SEGMENT BREAKDOWN (A-F) ---")
    if "segment_label" in df.columns:
        print(df["segment_label"].value_counts(dropna=False))
    else:
        print("❌ 'segment_label' column missing!")

    # 2. ZERO CHECK (Are the '100% filled' columns actually usable?)
    print("\n--- 2. DATA DENSITY (Non-Zero Values) ---")
    
    metrics = ["allowed_amt", "services_count", "npi_count", "site_count"]
    
    for col in metrics:
        if col in df.columns:
            # Force numeric
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            non_zero = (df[col] > 0).sum()
            total = len(df)
            pct = (non_zero / total) * 100
            
            print(f"{col.ljust(15)}: {non_zero:,} rows > 0 ({pct:.1f}%)")
            
            if pct < 50:
                print(f"   ⚠️ WARNING: Low data density for {col}. Imputation required.")
        else:
            print(f"{col}: ❌ Missing")

    # 3. FQHC CHECK
    print("\n--- 3. FQHC VALIDATION ---")
    fqhcs = df[df['segment_label'] == 'Segment B']
    print(f"Total 'Segment B' Rows: {len(fqhcs)}")
    print(f"FQHC Flags (Total): {df['fqhc_flag'].sum()}")

if __name__ == "__main__":
    validate()
