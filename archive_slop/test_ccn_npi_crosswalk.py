"""
Test CCN-to-NPI Crosswalk Integration
"""
import pandas as pd
import os

# Configuration
ROOT = os.getcwd()
DATA_RAW = os.path.join(ROOT, "data", "raw")

print("🔗 TESTING CCN-TO-NPI CROSSWALK")
print("="*80)

# Load crosswalk
crosswalk_path = os.path.join(DATA_RAW, "crosswalk_npi2ccn_one2many_updated_20240429.csv")

print(f"\n1. Loading crosswalk: {crosswalk_path}...")
xwalk = pd.read_csv(crosswalk_path)

print(f"   Total records: {len(xwalk):,}")
print(f"   Columns: {xwalk.columns.tolist()}")

# Filter for recent
xwalk['last_observed_date'] = pd.to_datetime(xwalk['last_observed_date'])
xwalk_recent = xwalk[xwalk['last_observed_date'] >= '2023-01-01'].copy()

print(f"\n2. Filtered for recent (>= 2023-01-01):")
print(f"   Active links: {len(xwalk_recent):,}")

# Dedup
xwalk_recent = xwalk_recent.sort_values('last_observed_date', ascending=False)
xwalk_dedup = xwalk_recent.drop_duplicates(subset='ccn', keep='first')

print(f"\n3. Deduplicated:")
print(f"   Unique CCN-to-NPI mappings: {len(xwalk_dedup):,}")

# By facility type
print(f"\n4. Facility Types:")
for ftype, count in xwalk_dedup['facility_type'].value_counts().items():
    print(f"   - {ftype}: {count:,}")

# Create dictionary
xwalk_dedup['ccn_str'] = xwalk_dedup['ccn'].astype(str)
xwalk_dict = dict(zip(xwalk_dedup['ccn_str'], xwalk_dedup['npi'].astype(int)))

print(f"\n5. Dictionary created:")
print(f"   Total mappings: {len(xwalk_dict):,}")

# Test lookups
print(f"\n6. Sample Lookups:")
sample_ccns = list(xwalk_dedup['ccn_str'].head(5))
for ccn in sample_ccns:
    npi = xwalk_dict.get(ccn)
    ftype = xwalk_dedup[xwalk_dedup['ccn_str'] == ccn]['facility_type'].values[0]
    print(f"   CCN {ccn} -> NPI {npi} ({ftype})")

print("\n" + "="*80)
print("✅ CROSSWALK TEST COMPLETE")
