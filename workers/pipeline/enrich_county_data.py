"""
County Data Enrichment Module
Author: Charta Health GTM Engineering

Purpose: Extract and standardize county names for clinics using ZIP code lookup.

This module provides helpers to enrich clinic data with standardized county names
needed for HPSA/MUA designation matching.

Dependencies:
  pip install zipcodes
"""

import pandas as pd
import zipcodes
import re


def extract_zip_from_text(text):
    """
    Extract 5-digit ZIP code from address text.

    Args:
        text: String that may contain a ZIP code

    Returns:
        str: 5-digit ZIP code or None
    """
    if pd.isna(text) or text == '':
        return None

    # Look for 5-digit ZIP code pattern
    match = re.search(r'\b(\d{5})(?:-\d{4})?\b', str(text))
    if match:
        return match.group(1)

    return None


def zip_to_county(zip_code):
    """
    Look up county name from ZIP code using zipcodes library.

    Args:
        zip_code: str or int, 5-digit ZIP code

    Returns:
        tuple: (county_name, state_abbr) or (None, None) if not found
    """
    if pd.isna(zip_code) or zip_code == '':
        return None, None

    # Ensure 5-digit string
    zip_str = str(zip_code).zfill(5)[:5]

    if not zip_str.isdigit() or len(zip_str) != 5:
        return None, None

    try:
        result = zipcodes.matching(zip_str)

        if result and len(result) > 0:
            # Get first match
            zip_data = result[0]

            county = zip_data.get('county', None)
            state = zip_data.get('state', None)

            if county:
                # Normalize county name (remove " County" suffix)
                county = county.strip()
                if county.endswith(' County'):
                    county = county[:-7].strip()

                # Title case
                county = county.title()

                return county, state
    except Exception as e:
        pass

    return None, None


def enrich_dataframe_with_county(df, zip_col='zip_code'):
    """
    Enrich a dataframe with county and state information from ZIP codes.

    Args:
        df: pandas DataFrame
        zip_col: str, name of the column containing ZIP codes

    Returns:
        pandas DataFrame with added 'county_name' and 'county_state' columns
    """
    print(f"🗺️  Enriching {len(df):,} records with county data from ZIP codes...")

    if zip_col not in df.columns:
        print(f"   ⚠️  Column '{zip_col}' not found. Skipping enrichment.")
        df['county_name'] = None
        df['county_state'] = None
        return df

    # Apply ZIP to county lookup
    results = df[zip_col].apply(lambda z: zip_to_county(z))

    df['county_name'] = results.apply(lambda x: x[0])
    df['county_state'] = results.apply(lambda x: x[1])

    # Count matches
    matched = df['county_name'].notna().sum()
    match_rate = (matched / len(df)) * 100

    print(f"   ✅ Matched {matched:,} records to counties ({match_rate:.1f}%)")

    # Show sample
    sample = df[df['county_name'].notna()][['org_name', 'state_code', zip_col, 'county_name']].head(5) if 'org_name' in df.columns else None
    if sample is not None and len(sample) > 0:
        print(f"\n   📋 Sample County Enrichment:")
        print(sample.to_string(index=False))

    return df


def main():
    """Test the county enrichment with sample ZIP codes."""
    print("🧪 Testing County Enrichment")
    print("=" * 80)

    # Test ZIP codes
    test_zips = [
        '94103',  # San Francisco, CA
        '10001',  # New York, NY
        '60601',  # Chicago, IL
        '02108',  # Boston, MA
        '90001',  # Los Angeles, CA
    ]

    print("\nTesting ZIP → County lookups:")
    for zip_code in test_zips:
        county, state = zip_to_county(zip_code)
        print(f"  ZIP {zip_code}: {county}, {state}")

    # Test with DataFrame
    print("\n" + "=" * 80)
    print("Testing DataFrame enrichment:")

    test_df = pd.DataFrame({
        'org_name': ['Clinic A', 'Clinic B', 'Clinic C'],
        'state_code': ['CA', 'NY', 'IL'],
        'zip_code': ['94103', '10001', '60601']
    })

    enriched_df = enrich_dataframe_with_county(test_df, zip_col='zip_code')
    print("\nEnriched DataFrame:")
    print(enriched_df[['org_name', 'state_code', 'zip_code', 'county_name', 'county_state']])


if __name__ == "__main__":
    main()
