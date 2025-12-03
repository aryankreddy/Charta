import pandas as pd
import os

path = "data/curated/clinics_seed.csv"
if os.path.exists(path):
    print(f"Reading {path}...")
    df = pd.read_csv(path, usecols=["segment_label"])
    print("\n--- SEGMENT DISTRIBUTION ---")
    print(df["segment_label"].value_counts(dropna=False))
else:
    print("File not found! Make sure you ran the enrichment script first.")
