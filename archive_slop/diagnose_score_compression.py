"""
Diagnostic script to identify score compression issues in ICP scoring.

This script analyzes the ICP scores to show:
1. How many clinics have identical total scores
2. How many have identical component scores
3. Distribution of scores
"""

import pandas as pd
import os
from collections import Counter

# Paths
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CURATED = os.path.join(ROOT, "data", "curated")
ICP_FILE = os.path.join(CURATED, "clinics_icp.csv")

def main():
    print("=" * 80)
    print("ICP SCORE COMPRESSION DIAGNOSTIC")
    print("=" * 80)
    
    # Load data
    df = pd.read_csv(ICP_FILE, low_memory=False)
    
    print(f"\nTotal clinics: {len(df):,}")
    
    # Check total score distribution
    print("\n" + "-" * 80)
    print("TOTAL SCORE DISTRIBUTION")
    print("-" * 80)
    
    total_scores = df['icp_total_score'].round(1)
    score_counts = total_scores.value_counts().sort_index(ascending=False)
    
    print(f"Unique total scores: {len(score_counts)}")
    print(f"Score range: {total_scores.min():.1f} - {total_scores.max():.1f}")
    print()
    print("Top 10 most common scores:")
    for score, count in score_counts.head(10).items():
        pct = count / len(df) * 100
        print(f"  {score:5.1f}: {count:7,} clinics ({pct:5.2f}%)")
    
    # Check component score compression
    print("\n" + "-" * 80)
    print("COMPONENT SCORE COMPRESSION")
    print("-" * 80)
    
    components = [
        "icp_fit_score",
        "icp_pain_score",
        "icp_compliance_score",
        "icp_propensity_score",
        "icp_scale_score",
        "icp_segment_score"
    ]
    
    for component in components:
        if component in df.columns:
            unique_vals = df[component].nunique()
            print(f"{component:30}: {unique_vals:5} unique values")
    
    # Check for identical score patterns
    print("\n" + "-" * 80)
    print("IDENTICAL SCORE PATTERNS")
    print("-" * 80)
    
    # Create a composite key of all component scores
    df['score_pattern'] = (
        df['icp_fit_score'].astype(str) + '_' +
        df['icp_pain_score'].astype(str) + '_' +
        df['icp_compliance_score'].astype(str) + '_' +
        df['icp_propensity_score'].astype(str) + '_' +
        df['icp_scale_score'].astype(str) + '_' +
        df['icp_segment_score'].astype(str)
    )
    
    pattern_counts = df['score_pattern'].value_counts()
    print(f"Unique score patterns: {len(pattern_counts):,}")
    print(f"Clinics with unique patterns: {(pattern_counts == 1).sum():,} ({(pattern_counts == 1).sum() / len(df) * 100:.1f}%)")
    print(f"Clinics with duplicate patterns: {(pattern_counts > 1).sum():,}")
    print()
    print("Top 5 most common patterns:")
    for i, (pattern, count) in enumerate(pattern_counts.head(5).items(), 1):
        scores = pattern.split('_')
        total = sum(float(s) for s in scores)
        print(f"  {i}. Pattern: Fit={scores[0]}, Pain={scores[1]}, Comp={scores[2]}, Prop={scores[3]}, Scale={scores[4]}, Seg={scores[5]} → Total={total:.1f}")
        print(f"     Clinics: {count:,} ({count/len(df)*100:.2f}%)")
    
    # Check FQHCs specifically
    print("\n" + "-" * 80)
    print("FQHC SCORE ANALYSIS")
    print("-" * 80)
    
    if 'fqhc_flag' in df.columns:
        fqhc_df = df[df['fqhc_flag'] == 1]
        print(f"Total FQHCs: {len(fqhc_df):,}")
        
        if len(fqhc_df) > 0:
            fqhc_scores = fqhc_df['icp_total_score'].round(1)
            fqhc_unique = fqhc_scores.nunique()
            print(f"Unique FQHC scores: {fqhc_unique}")
            print(f"FQHC score range: {fqhc_scores.min():.1f} - {fqhc_scores.max():.1f}")
            print()
            print("Top 5 FQHC scores:")
            for score, count in fqhc_scores.value_counts().head(5).items():
                print(f"  {score:5.1f}: {count:4} FQHCs")
    
    # Segment analysis
    print("\n" + "-" * 80)
    print("SEGMENT SCORE ANALYSIS")
    print("-" * 80)
    
    for segment in ['A', 'B', 'C']:
        seg_df = df[df['icp_segment'] == segment]
        if len(seg_df) > 0:
            seg_scores = seg_df['icp_total_score'].round(1)
            print(f"\nSegment {segment}: {len(seg_df):,} clinics")
            print(f"  Unique scores: {seg_scores.nunique()}")
            print(f"  Score range: {seg_scores.min():.1f} - {seg_scores.max():.1f}")
            print(f"  Avg score: {seg_scores.mean():.1f}")
    
    print("\n" + "=" * 80)
    print("DIAGNOSIS COMPLETE")
    print("=" * 80)
    print()
    print("💡 KEY FINDINGS:")
    print("   - If unique score patterns < 10% of total clinics → HIGH compression")
    print("   - If top patterns cover > 20% of clinics → MODERATE compression")
    print("   - Target: Each clinic should have unique or near-unique score")
    print()


if __name__ == "__main__":
    main()

