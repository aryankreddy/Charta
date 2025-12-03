"""
Test Strategic Data Integration (OIG & ACO)
"""
import pandas as pd
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from workers.pipeline_main import integrate_strategic_data, normalize_name

print("🧪 TESTING STRATEGIC DATA INTEGRATION")
print("="*80)

# Create Dummy Data
data = {
    'npi': [1972902351, 1234567890, 9999999999],  # 1st is OIG excluded
    'org_name': ['101 FIRST CARE PHARMACY INC', 'ABC Network', 'Random Clinic'], # 2nd is ACO participant
    'norm_name': ['', '', '']
}
df = pd.DataFrame(data)
df['norm_name'] = df['org_name'].apply(normalize_name)

print("Input Data:")
print(df)

# Run Integration
print("\nRunning integrate_strategic_data()...")
df_enriched = integrate_strategic_data(df)

print("\nOutput Data:")
print(df_enriched[['npi', 'org_name', 'risk_compliance_flag', 'is_aco_participant']])

# Verify
print("\nVerifying Results:")
oig_match = df_enriched.loc[df_enriched['npi'] == 1972902351, 'risk_compliance_flag'].values[0]
aco_match = df_enriched.loc[df_enriched['org_name'] == 'ABC Network', 'is_aco_participant'].values[0]

print(f"   OIG Match (Expect True): {oig_match}")
print(f"   ACO Match (Expect True): {aco_match}")

if oig_match and aco_match:
    print("\n✅ TEST PASSED")
else:
    print("\n❌ TEST FAILED")
