"""
MIPS Performance Data Ingestion Pipeline
Author: Charta Health GTM Engineering

Purpose: Load MIPS (Merit-based Incentive Payment System) performance data
         and roll up to Organization NPI using PECOS bridge.

Input:
  - data/raw/qpps-mips/2023/puf_output_file_output.csv (MIPS PUF)
  - data/raw/pecos/.../PPEF_Enrollment_Extract_2025.10.01.csv (PECOS Enrollment)
  - data/raw/pecos/.../PPEF_Reassignment_Extract_2025.10.01.csv (PECOS Reassignment)

Output:
  - data/staging/stg_mips_org_scores.csv
    Schema: org_npi, avg_mips_score, mips_clinician_count
    Keyed by: org_npi

Logic:
  1. Load MIPS PUF (Individual NPI + Final Score)
  2. Load PECOS Bridge (Individual NPI -> Organization NPI)
  3. Merge MIPS data onto Bridge
  4. Aggregate by Organization NPI:
     - Average MIPS Final Score
     - Count of MIPS-eligible clinicians
  5. Save to staging directory
"""

import pandas as pd
import os

# Paths
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DATA_RAW = os.path.join(ROOT, "data", "raw")

# MIPS PUF
MIPS_FILE = os.path.join(DATA_RAW, "qpps-mips", "2023", "puf_output_file_output.csv")

# PECOS Bridge
PECOS_DIR = os.path.join(DATA_RAW, "pecos", "Medicare Fee-For-Service  Public Provider Enrollment", "2025-Q3")
PECOS_REASSIGN = os.path.join(PECOS_DIR, "PPEF_Reassignment_Extract_2025.10.01.csv")
PECOS_ENROLL = os.path.join(PECOS_DIR, "PPEF_Enrollment_Extract_2025.10.01.csv")

# Output
OUTPUT_FILE = os.path.join(ROOT, "data", "staging", "stg_mips_org_scores.csv")


def load_pecos_bridge():
    """
    Load PECOS Enrollment and Reassignment data to build Individual NPI -> Org NPI bridge.

    Returns:
        DataFrame with columns: indiv_npi, org_npi
        None if PECOS files not found
    """
    print("📥 Loading PECOS Bridge...")

    if not os.path.exists(PECOS_REASSIGN) or not os.path.exists(PECOS_ENROLL):
        print("   ⚠️  PECOS files not found. Cannot build bridge.")
        return None

    # 1. Load Enrollment (Map ENRLMT_ID -> NPI)
    print("   Loading Enrollment Map...")
    enrl = pd.read_csv(
        PECOS_ENROLL,
        usecols=['NPI', 'ENRLMT_ID'],
        dtype={'NPI': 'int64', 'ENRLMT_ID': str},
        encoding='latin1'
    )
    print(f"   Loaded {len(enrl):,} enrollment records")

    # 2. Load Reassignment (Map Individual ENRLMT_ID -> Org ENRLMT_ID)
    print("   Loading Reassignment Map...")
    reas = pd.read_csv(
        PECOS_REASSIGN,
        usecols=['REASGN_BNFT_ENRLMT_ID', 'RCV_BNFT_ENRLMT_ID'],
        dtype=str,
        encoding='latin1'
    )
    print(f"   Loaded {len(reas):,} reassignment records")

    # 3. Join to get Individual NPI
    print("   Merging Individual NPI...")
    merged = reas.merge(
        enrl,
        left_on='REASGN_BNFT_ENRLMT_ID',
        right_on='ENRLMT_ID',
        how='inner'
    )
    merged.rename(columns={'NPI': 'indiv_npi'}, inplace=True)

    # 4. Join to get Organization NPI
    print("   Merging Organization NPI...")
    merged = merged.merge(
        enrl,
        left_on='RCV_BNFT_ENRLMT_ID',
        right_on='ENRLMT_ID',
        how='inner'
    )
    merged.rename(columns={'NPI': 'org_npi'}, inplace=True)

    # 5. Extract bridge
    bridge = merged[['indiv_npi', 'org_npi']].drop_duplicates()

    print(f"   ✅ Built PECOS Bridge: {len(bridge):,} Individual NPI → Org NPI links")

    return bridge


def load_mips_data():
    """
    Load MIPS PUF data with Individual NPI and Final Score.

    Returns:
        DataFrame with columns: npi, final_score
    """
    print("📥 Loading MIPS PUF data...")

    if not os.path.exists(MIPS_FILE):
        print(f"   ⚠️  MIPS file not found: {MIPS_FILE}")
        return None

    # Load only necessary columns
    mips = pd.read_csv(
        MIPS_FILE,
        usecols=['npi', 'final score'],
        dtype={'npi': 'int64', 'final score': 'float64'}
    )

    # Rename for consistency
    mips.rename(columns={'npi': 'indiv_npi', 'final score': 'final_score'}, inplace=True)

    # Remove rows with missing scores
    mips = mips.dropna(subset=['final_score'])

    print(f"   Loaded {len(mips):,} MIPS clinicians with final scores")
    print(f"   Score Range: {mips['final_score'].min():.2f} - {mips['final_score'].max():.2f}")
    print(f"   Average Score: {mips['final_score'].mean():.2f}")

    return mips


def merge_and_aggregate(mips, bridge):
    """
    Merge MIPS data with PECOS bridge and aggregate by Organization NPI.

    Args:
        mips: DataFrame with columns [indiv_npi, final_score]
        bridge: DataFrame with columns [indiv_npi, org_npi]

    Returns:
        DataFrame with columns: org_npi, avg_mips_score, mips_clinician_count
    """
    print("\n🔗 Merging MIPS data with PECOS Bridge...")

    # Merge MIPS onto Bridge
    merged = mips.merge(bridge, on='indiv_npi', how='inner')

    print(f"   Matched {len(merged):,} MIPS clinicians to organizations")
    print(f"   Unmatched: {len(mips) - len(merged):,} clinicians (not in PECOS bridge)")

    # Aggregate by Organization NPI
    print("\n📊 Aggregating by Organization NPI...")
    agg_df = merged.groupby('org_npi').agg(
        avg_mips_score=('final_score', 'mean'),
        mips_clinician_count=('indiv_npi', 'count')
    ).reset_index()

    # Round average score to 2 decimals
    agg_df['avg_mips_score'] = agg_df['avg_mips_score'].round(2)

    print(f"   Total Organizations: {len(agg_df):,}")
    print(f"   Average MIPS Score: {agg_df['avg_mips_score'].mean():.2f}")
    print(f"   Median MIPS Score: {agg_df['avg_mips_score'].median():.2f}")
    print(f"\n   Organizations by Clinician Count:")
    print(f"      1 clinician:   {(agg_df['mips_clinician_count'] == 1).sum():,}")
    print(f"      2-5 clinicians: {((agg_df['mips_clinician_count'] >= 2) & (agg_df['mips_clinician_count'] <= 5)).sum():,}")
    print(f"      6-10 clinicians: {((agg_df['mips_clinician_count'] >= 6) & (agg_df['mips_clinician_count'] <= 10)).sum():,}")
    print(f"      11+ clinicians: {(agg_df['mips_clinician_count'] >= 11).sum():,}")

    return agg_df


def main():
    """Main execution function."""
    print("🚀 MIPS DATA INGESTION PIPELINE")
    print("=" * 80)

    # Step 1: Load PECOS Bridge
    bridge = load_pecos_bridge()
    if bridge is None:
        print("\n❌ FAILED: Cannot proceed without PECOS bridge")
        return

    # Step 2: Load MIPS data
    mips = load_mips_data()
    if mips is None:
        print("\n❌ FAILED: Cannot proceed without MIPS data")
        return

    # Step 3: Merge and aggregate
    output_df = merge_and_aggregate(mips, bridge)

    # Step 4: Save to staging
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    output_df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n✅ SUCCESS")
    print(f"   Output: {OUTPUT_FILE}")
    print(f"   Total Organizations: {len(output_df):,}")

    print(f"\n📊 Sample Output (Top 10 by MIPS Score):")
    sample = output_df.nlargest(10, 'avg_mips_score')
    print(sample.to_string(index=False))


if __name__ == "__main__":
    main()
