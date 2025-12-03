"""
HPSA/MUA Data Ingestion Pipeline
Author: Charta Health GTM Engineering

Purpose: Load and standardize HPSA and MUA/P designation data from HRSA.

Input:
  - data/raw/hrsa/hpsa.csv (Health Professional Shortage Areas)
  - data/raw/hrsa/muap.csv (Medically Underserved Areas/Populations)

Output:
  - data/staging/stg_hpsa_mua_flags.csv
    Schema: state, county_name, is_hpsa, is_mua
    Keyed by: (state, county_name)

Logic:
  1. Load both HPSA and MUA/P files
  2. Standardize state abbreviations and county names
  3. Filter to active designations only
  4. Create boolean flags by unique state+county combination
  5. Save to staging directory
"""

import pandas as pd
import os
import re

# Paths
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
HPSA_FILE = os.path.join(ROOT, "data", "raw", "hrsa", "hpsa.csv")
MUAP_FILE = os.path.join(ROOT, "data", "raw", "hrsa", "muap.csv")
OUTPUT_FILE = os.path.join(ROOT, "data", "staging", "stg_hpsa_mua_flags.csv")


def clean_state(state_str):
    """
    Standardize state abbreviation.

    Examples:
      - 'CA' -> 'CA'
      - 'california' -> 'CA'
      - None -> None
    """
    if pd.isna(state_str):
        return None

    state_str = str(state_str).strip().upper()

    # Already a 2-letter abbreviation
    if len(state_str) == 2:
        return state_str

    # Could add full state name mapping if needed
    return state_str


def clean_county_name(county_str, state_abbr):
    """
    Standardize county name.

    Examples:
      - 'Los Angeles County, CA' -> 'Los Angeles'
      - 'Los Angeles, CA' -> 'Los Angeles'
      - 'Los Angeles County' -> 'Los Angeles'
      - 'Los Angeles' -> 'Los Angeles'

    Logic:
      1. Remove state suffix (', CA')
      2. Remove 'County' suffix
      3. Strip whitespace
      4. Title case
    """
    if pd.isna(county_str):
        return None

    county_str = str(county_str).strip()

    # Remove state suffix if present (e.g., 'Los Angeles, CA' -> 'Los Angeles')
    if state_abbr and f", {state_abbr}" in county_str:
        county_str = county_str.replace(f", {state_abbr}", "")

    # Remove 'County' suffix (case insensitive)
    county_str = re.sub(r'\s+County\s*$', '', county_str, flags=re.IGNORECASE)

    # Clean whitespace and title case
    county_str = county_str.strip().title()

    return county_str


def load_hpsa_data():
    """
    Load HPSA designations and extract active state+county combinations.

    Returns:
        DataFrame with columns: state, county_name
    """
    print("📥 Loading HPSA data...")
    df = pd.read_csv(HPSA_FILE, low_memory=False)

    print(f"   Loaded {len(df):,} HPSA records")

    # Extract state and county
    df['state'] = df['Primary State Abbreviation'].apply(clean_state)
    df['county_name_raw'] = df['Common County Name']

    # Filter to active designations only
    active_df = df[df['HPSA Status'] == 'Designated'].copy()
    print(f"   Filtered to {len(active_df):,} active designations")

    # Clean county names
    active_df['county_name'] = active_df.apply(
        lambda row: clean_county_name(row['county_name_raw'], row['state']),
        axis=1
    )

    # Drop rows with missing state or county
    active_df = active_df.dropna(subset=['state', 'county_name'])

    # Get unique state+county combinations
    unique_counties = active_df[['state', 'county_name']].drop_duplicates()

    print(f"   Extracted {len(unique_counties):,} unique state+county combinations")

    return unique_counties


def load_mua_data():
    """
    Load MUA/P designations and extract active state+county combinations.

    Returns:
        DataFrame with columns: state, county_name
    """
    print("📥 Loading MUA/P data...")
    df = pd.read_csv(MUAP_FILE, low_memory=False)

    print(f"   Loaded {len(df):,} MUA/P records")

    # Extract state and county
    df['state'] = df['Primary State Abbreviation'].apply(clean_state)
    df['county_name_raw'] = df['Common County Name']

    # Filter to active designations (not Withdrawn)
    active_df = df[df['MUA/P Status Description'] != 'Withdrawn'].copy()
    print(f"   Filtered to {len(active_df):,} active designations")

    # Clean county names
    active_df['county_name'] = active_df.apply(
        lambda row: clean_county_name(row['county_name_raw'], row['state']),
        axis=1
    )

    # Drop rows with missing state or county
    active_df = active_df.dropna(subset=['state', 'county_name'])

    # Get unique state+county combinations
    unique_counties = active_df[['state', 'county_name']].drop_duplicates()

    print(f"   Extracted {len(unique_counties):,} unique state+county combinations")

    return unique_counties


def merge_and_flag():
    """
    Merge HPSA and MUA data, create boolean flags.

    Returns:
        DataFrame with columns: state, county_name, is_hpsa, is_mua
    """
    # Load both datasets
    hpsa_counties = load_hpsa_data()
    mua_counties = load_mua_data()

    # Add flags
    hpsa_counties['is_hpsa'] = True
    mua_counties['is_mua'] = True

    print("\n🔗 Merging HPSA and MUA/P data...")

    # Full outer merge on state+county_name
    merged = pd.merge(
        hpsa_counties,
        mua_counties,
        on=['state', 'county_name'],
        how='outer'
    )

    # Fill missing flags with False (convert to bool to avoid future warning)
    merged['is_hpsa'] = merged['is_hpsa'].fillna(False).astype(bool)
    merged['is_mua'] = merged['is_mua'].fillna(False).astype(bool)

    # Sort for readability
    merged = merged.sort_values(['state', 'county_name'])

    print(f"   Total unique state+county combinations: {len(merged):,}")
    print(f"   HPSA counties: {merged['is_hpsa'].sum():,}")
    print(f"   MUA counties: {merged['is_mua'].sum():,}")
    print(f"   Both HPSA + MUA: {((merged['is_hpsa']) & (merged['is_mua'])).sum():,}")

    return merged


def main():
    """Main execution function."""
    print("🚀 HPSA/MUA DATA INGESTION PIPELINE")
    print("=" * 80)

    # Merge and flag
    output_df = merge_and_flag()

    # Save to staging
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    output_df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n✅ SUCCESS")
    print(f"   Output: {OUTPUT_FILE}")
    print(f"   Total Records: {len(output_df):,}")
    print(f"\n📊 Sample Output:")
    print(output_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
