"""
AUDIT SCORING RESULTS
Inspects the top scorers and component distributions to diagnose why Tier 1 is empty.
"""

import pandas as pd
import os

OUTPUT_FILE = 'data/curated/clinics_scored_final.csv'

def audit():
    if not os.path.exists(OUTPUT_FILE):
        print("❌ Scored file not found.")
        return

    print(f"Loading {OUTPUT_FILE}...")
    df = pd.read_csv(OUTPUT_FILE, low_memory=False)
    print(f"Loaded {len(df):,} rows.")
    
    # Check Score Distribution
    print("\n=== SCORE DISTRIBUTION ===")
    print(df['icp_score'].describe())
    
    print("\n=== TIER DISTRIBUTION ===")
    print(df['icp_tier'].value_counts())
    
    # Check Component Stats
    components = [c for c in df.columns if 'score_' in c and 'drivers' not in c]
    print("\n=== COMPONENT STATISTICS ===")
    for c in components:
        print(f"{c}: Mean={df[c].mean():.1f}, Max={df[c].max():.1f}")
        
    # Inspect Top 20 Scorers
    print("\n=== TOP 20 SCORERS ===")
    cols = ['org_name', 'icp_score', 'icp_tier', 'data_confidence', 
            'score_pain_total', 'score_fit_total', 'score_strat_total',
            'segment_label', 'undercoding_ratio', 'final_volume']
    
    top = df.sort_values('icp_score', ascending=False).head(20)
    print(top[cols].to_string(index=False))
    
    # Inspect Top Confidence Scorers
    print("\n=== TOP 20 HIGH CONFIDENCE SCORERS ===")
    top_conf = df.sort_values('data_confidence', ascending=False).head(20)
    print(top_conf[cols].to_string(index=False))

if __name__ == "__main__":
    audit()