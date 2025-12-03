import pandas as pd
import os
import sys

# Configuration
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_FILE = os.path.join(ROOT, "data", "curated", "clinics_scored_final.csv")

def main():
    print("🚀 RUNNING LEAD VALIDATION...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file missing: {INPUT_FILE}")
        return

    print(f"   Loading {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    print(f"   Loaded {len(df):,} total clinics.")
    
    # Check for real_annual_encounters bug
    print("\n🔍 CHECKING FOR GHOST DATA BUG...")
    real_vol_count = df['real_annual_encounters'].notnull().sum()
    real_vol_zeros = (df['real_annual_encounters'] == 0).sum()
    print(f"   Clinics with Real Volume: {real_vol_count:,}")
    print(f"   Clinics with Real Volume = 0: {real_vol_zeros:,}")
    
    if real_vol_count > 0 and real_vol_zeros / real_vol_count > 0.5:
        print("   ⚠️  WARNING: High percentage of zeros in real volume data. Bug might persist.")
    else:
        print("   ✅ Real volume data looks healthy.")

    # Filter Tier 1
    tier1 = df[df['icp_tier'] == 'Tier 1'].copy()
    print(f"\n🏆 TIER 1 LEADS: {len(tier1):,}")
    
    if len(tier1) == 0:
        print("   ❌ No Tier 1 leads found. Scoring might be too strict.")
        return

    # Stats
    print("\n📊 TIER 1 STATS:")
    print(f"   Avg Score: {tier1['icp_score'].mean():.1f}")
    print(f"   Avg Confidence: {tier1['data_confidence'].mean():.1f}")
    
    # Segment Distribution
    print("\n   Segment Distribution:")
    print(tier1['segment_label'].value_counts().head(5))
    
    # Phone Coverage
    phone_cov = tier1['phone'].notnull().sum() / len(tier1) * 100
    print(f"\n   Phone Coverage: {phone_cov:.1f}%")
    
    # Top 100 Smell Test
    print("\n👀 TOP 20 LEADS (SMELL TEST):")
    cols = ['org_name', 'state', 'icp_score', 'icp_tier', 'segment_label', 'scoring_drivers', 'real_annual_encounters', 'undercoding_ratio']
    
    # Ensure columns exist
    cols = [c for c in cols if c in tier1.columns]
    
    top20 = tier1.sort_values('icp_score', ascending=False).head(20)
    
    for i, row in top20.iterrows():
        print("-" * 80)
        print(f"#{i} {row.get('org_name', 'N/A')} ({row.get('state', 'N/A')})")
        print(f"   Score: {row.get('icp_score')} | Tier: {row.get('icp_tier')}")
        print(f"   Segment: {row.get('segment_label')}")
        print(f"   Drivers: {row.get('scoring_drivers')}")
        print(f"   Real Vol: {row.get('real_annual_encounters')} | Undercoding: {row.get('undercoding_ratio')}")

if __name__ == "__main__":
    main()
