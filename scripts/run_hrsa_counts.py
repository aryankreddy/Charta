"""
Run HRSA Integration on Seed File to get Counts
"""
import pandas as pd
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from workers.pipeline_main import integrate_hrsa_data, load_seed, ROOT, DATA_RAW

print("🚀 Running HRSA Integration on Seed File...")

# Load Seed
df = load_seed()
print(f"Loaded {len(df):,} seed records.")

# Run Integration
df = integrate_hrsa_data(df)

# Report
fqhc_count = df['fqhc_flag'].sum()
print("\n" + "="*80)
print(f"📊 FINAL RESULTS:")
print(f"   ✅ Total FQHCs Flagged: {fqhc_count:,}")
print("="*80)
