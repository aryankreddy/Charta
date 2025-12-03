"""
Run Strategic Integration on Seed File to get Counts
"""
import pandas as pd
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from workers.pipeline_main import integrate_strategic_data, load_seed, ROOT, DATA_RAW, DATA_STAGING

print("🚀 Running Strategic Integration on Seed File...")

# Load Seed
df = load_seed()
print(f"Loaded {len(df):,} seed records.")

# Run Integration
df = integrate_strategic_data(df)

# Report
oig_count = df['risk_compliance_flag'].sum()
aco_count = df['is_aco_participant'].sum()

print("\n" + "="*80)
print(f"📊 FINAL RESULTS:")
print(f"   🚨 Flagged {oig_count:,} Clinics with Compliance Risks (OIG).")
print(f"   ✅ Identified {aco_count:,} Clinics participating in ACOs.")
print("="*80)
