"""
Segment Dataset Script

Applies v2 segmentation logic to the full clinics_icp.csv dataset.
Creates a new file with segment_v2 column added.
"""

import os
import sys
import pandas as pd
from collections import Counter

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from v2_core.segmentation import classify_segment, get_segment_description

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_CURATED = os.path.join(ROOT, "data", "curated")
INPUT_FILE = os.path.join(DATA_CURATED, "clinics_icp.csv")
OUTPUT_FILE = os.path.join(DATA_CURATED, "clinics_segmented_v2.csv")


def main():
    print("=" * 80)
    print("SEGMENTATION SCRIPT - v2 Clean Implementation")
    print("=" * 80)
    
    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Input file not found: {INPUT_FILE}")
        return
    
    print(f"\n📂 Loading data from: {INPUT_FILE}")
    
    # Load data
    try:
        df = pd.read_csv(INPUT_FILE, low_memory=False)
        print(f"✅ Loaded {len(df):,} clinics")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return
    
    # Check for required columns
    required_cols = ["npi", "org_name"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ Missing required columns: {missing_cols}")
        return
    
    print(f"\n📊 Dataset columns: {len(df.columns)}")
    print(f"   Sample columns: {list(df.columns[:10])}")
    
    # Check for segmentation input columns
    segmentation_cols = ["fqhc_flag", "taxonomy", "segment_label", "npi_count", "site_count"]
    available_cols = [col for col in segmentation_cols if col in df.columns]
    print(f"\n🔍 Segmentation input columns available: {available_cols}")
    
    # Add missing columns with defaults
    for col in segmentation_cols:
        if col not in df.columns:
            if col in ["fqhc_flag", "npi_count", "site_count"]:
                df[col] = 0
            else:
                df[col] = ""
            print(f"   ⚠️  Added missing column '{col}' with default values")
    
    # Apply segmentation
    print(f"\n🔄 Applying segmentation logic to {len(df):,} clinics...")
    print("   Priority: B (FQHC/HRSA) > A (Specialty/Behavioral) > C (Hospital/Health System) > D (Other)")
    
    # Process in chunks for progress reporting
    chunk_size = 100000
    segments = []
    
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        chunk_segments = []
        
        for _, row in chunk.iterrows():
            clinic_data = {
                "fqhc_flag": row.get("fqhc_flag", 0),
                "taxonomy": row.get("taxonomy", ""),
                "segment_label": row.get("segment_label", ""),
                "org_name": row.get("org_name", ""),
                "npi_count": row.get("npi_count", 0),
                "site_count": row.get("site_count", 0),
            }
            segment = classify_segment(clinic_data)
            chunk_segments.append(segment)
        
        segments.extend(chunk_segments)
        progress = min(i + chunk_size, len(df))
        print(f"   Progress: {progress:,} / {len(df):,} ({100*progress/len(df):.1f}%)")
    
    # Add segment column
    df["segment_v2"] = segments
    
    # Calculate distribution
    segment_counts = Counter(segments)
    total = len(df)
    
    print("\n" + "=" * 80)
    print("SEGMENTATION RESULTS")
    print("=" * 80)
    
    for segment in ["B", "A", "C", "D"]:
        count = segment_counts[segment]
        pct = 100 * count / total
        desc = get_segment_description(segment)
        print(f"\n{segment}: {count:,} clinics ({pct:.2f}%)")
        print(f"   {desc}")
    
    print(f"\n{'='*80}")
    print(f"TOTAL: {total:,} clinics")
    print(f"{'='*80}")
    
    # Show sample clinics from each segment
    print("\n" + "=" * 80)
    print("SAMPLE CLINICS BY SEGMENT")
    print("=" * 80)
    
    for segment in ["B", "A", "C", "D"]:
        segment_df = df[df["segment_v2"] == segment]
        if len(segment_df) > 0:
            print(f"\n--- Segment {segment} (showing 5 samples) ---")
            sample = segment_df.head(5)
            for _, row in sample.iterrows():
                npi = row.get("npi", "N/A")
                org_name = row.get("org_name", "N/A")
                fqhc = row.get("fqhc_flag", 0)
                npi_count = row.get("npi_count", 0)
                site_count = row.get("site_count", 0)
                taxonomy = row.get("taxonomy", "")[:20] + "..." if len(str(row.get("taxonomy", ""))) > 20 else row.get("taxonomy", "")
                
                print(f"  • {org_name[:50]}")
                print(f"    NPI: {npi} | FQHC: {fqhc} | Providers: {npi_count} | Sites: {site_count}")
                print(f"    Taxonomy: {taxonomy}")
    
    # Save output
    print(f"\n💾 Saving segmented data to: {OUTPUT_FILE}")
    try:
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"✅ Successfully saved {len(df):,} clinics with segment_v2 column")
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return
    
    # Validation checks
    print("\n" + "=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)
    
    # Check 1: All rows have segments
    null_segments = df["segment_v2"].isnull().sum()
    print(f"✅ Null segments: {null_segments} (should be 0)")
    
    # Check 2: All segments are valid
    valid_segments = set(["A", "B", "C", "D"])
    invalid = df[~df["segment_v2"].isin(valid_segments)]
    print(f"✅ Invalid segments: {len(invalid)} (should be 0)")
    
    # Check 3: Total count matches
    segment_sum = sum(segment_counts.values())
    print(f"✅ Segment sum: {segment_sum:,} == Total: {total:,} ({'PASS' if segment_sum == total else 'FAIL'})")
    
    print("\n" + "=" * 80)
    print("✅ SEGMENTATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
