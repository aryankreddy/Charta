"""
Test HRSA Integration
"""
import pandas as pd
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from workers.pipeline_main import integrate_hrsa_data, load_seed, normalize_name

print("🧪 TESTING HRSA INTEGRATION")
print("="*80)

# Load Seed (or dummy)
# Using dummy for speed
data = {
    'npi': [1000000001, 1000000002],
    'org_name': ['Albany Family Medical Center', 'Random Clinic'],
    'city': ['Albany', 'Nowhere'],
    'state': ['KY', 'XX'],
    'real_annual_encounters': [0, 0]
}
df = pd.DataFrame(data)

print("Input Data:")
print(df)

# Run Integration
print("\nRunning integrate_hrsa_data()...")
df_enriched = integrate_hrsa_data(df)

print("\nOutput Data:")
print(df_enriched[['npi', 'org_name', 'fqhc_flag', 'real_annual_encounters']])

# Verify
print("\nVerifying Results:")
# Albany Family Medical Center is in the HRSA file (from my head inspection)
# It should match.
# Volume should NOT be overwritten because column is missing.

matched = df_enriched.loc[df_enriched['org_name'] == 'Albany Family Medical Center', 'fqhc_flag'].values[0]
volume = df_enriched.loc[df_enriched['org_name'] == 'Albany Family Medical Center', 'real_annual_encounters'].values[0]

print(f"   Matched (Expect 1.0): {matched}")
print(f"   Volume (Expect 0): {volume}")

if matched == 1.0:
    print("\n✅ TEST PASSED (Matching Works)")
else:
    print("\n❌ TEST FAILED (Matching Failed)")
    
if volume == 0:
    print("   ✅ Volume correctly skipped (Column missing)")
else:
    print("   ❌ Volume unexpectedly changed")
