"""
Verify Data Assets and Metrics
"""
import pandas as pd
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from workers.pipeline_main import load_seed, integrate_strategic_data, integrate_fqhc_reports, load_ccn_to_npi_crosswalk, ROOT, DATA_RAW, DATA_STAGING

print("🔍 VERIFYING DATA ASSETS")
print("="*80)

# 1. The Master List
print("\n1. The Master List (clinics_seed.csv)")
df = load_seed()
print(f"   Count: {len(df):,} Organizations")

# 2. Real Patient Volume
print("\n2. Real Patient Volume")
util_path = os.path.join(DATA_STAGING, "stg_physician_util.parquet")
if os.path.exists(util_path):
    util = pd.read_parquet(util_path)
    print(f"   Clinics with Volume: {len(util):,}")
else:
    # Fallback to undercoding metrics if util parquet not found
    undercoding_path = os.path.join(DATA_STAGING, "stg_undercoding_metrics.csv")
    if os.path.exists(undercoding_path):
        undercoding = pd.read_csv(undercoding_path)
        print(f"   Clinics with Volume (Undercoding): {len(undercoding):,}")
    else:
        print("   ⚠️  Volume data not found.")

# 3. Undercoding Signals
print("\n3. Undercoding Signals")
undercoding_path = os.path.join(DATA_STAGING, "stg_undercoding_metrics.csv")
if os.path.exists(undercoding_path):
    undercoding = pd.read_csv(undercoding_path)
    severe = undercoding[undercoding['undercoding_ratio'] < 0.30]
    print(f"   Severe Undercoding Clinics: {len(severe):,}")
else:
    print("   ⚠️  Undercoding metrics not found.")

# 4. FQHC Financials
print("\n4. FQHC Financials")
# Run integration on seed to check matches
df_fqhc = integrate_fqhc_reports(df.copy())
fqhc_matches = df_fqhc['fqhc_revenue'].notnull().sum()
print(f"   FQHC Matches: {fqhc_matches:,}")

# 5. Hospital Financials
print("\n5. Hospital Financials")
hosp_path = os.path.join(DATA_STAGING, "stg_hospital_sas_2024.csv")
if os.path.exists(hosp_path):
    hosp = pd.read_csv(hosp_path)
    print(f"   Hospital Records: {len(hosp):,}")
else:
    print("   ⚠️  Hospital staging file not found.")

# 6. Home Health Financials
print("\n6. Home Health Financials")
hha_path = os.path.join(DATA_STAGING, "stg_hha_2023.csv")
if os.path.exists(hha_path):
    hha = pd.read_csv(hha_path)
    print(f"   HHA Records: {len(hha):,}")
else:
    print("   ⚠️  HHA staging file not found.")

# 7. Risk Flags (OIG) & 8. Value Flags (ACO)
print("\n7 & 8. Risk & Value Flags")
df_strat = integrate_strategic_data(df.copy())
oig_count = df_strat['risk_compliance_flag'].sum()
aco_count = df_strat['is_aco_participant'].sum()
print(f"   Risk Flags (OIG): {oig_count:,}")
print(f"   Value Flags (ACO): {aco_count:,}")

# 9. The Bridge
print("\n9. The Bridge (PECOS)")
# Check bridge size via mine_cpt_codes output or load raw
# Loading raw is slow, so we'll trust the previous output or check file size
pecos_reassign = os.path.join(DATA_RAW, "pecos", "Medicare Fee-For-Service  Public Provider Enrollment", "2025-Q3", "PPEF_Reassignment_Extract_2025.10.01.csv")
if os.path.exists(pecos_reassign):
    # Just count lines for speed
    import subprocess
    result = subprocess.run(['wc', '-l', pecos_reassign], capture_output=True, text=True)
    line_count = int(result.stdout.split()[0])
    print(f"   Bridge File Lines: {line_count:,}")
else:
    print("   ⚠️  PECOS Reassignment file not found.")

# 10. The Crosswalk
print("\n10. The Crosswalk")
xwalk = load_ccn_to_npi_crosswalk()
print(f"   Crosswalk Mappings: {len(xwalk):,}")

print("\n" + "="*80)
print("✅ VERIFICATION COMPLETE")
