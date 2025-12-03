"""
TIER 2 PROFILE ANALYSIS & TOP 50 EXPORT
Analyzes the 12,340 new Tier 2 clinics to identify dominant drivers
"""

import pandas as pd
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCORED_FILE = os.path.join(ROOT, "data", "curated", "clinics_scored_final.csv")
OUTPUT_FILE = os.path.join(ROOT, "data", "curated", "top_50_clinics.csv")

def analyze_tier2():
    print("🔍 TIER 2 PROFILE ANALYSIS")
    print("="*80)
    
    df = pd.read_csv(SCORED_FILE, low_memory=False)
    
    # Filter Tier 2
    tier2 = df[df['icp_tier'] == 'Tier 2'].copy()
    print(f"\nTotal Tier 2 Clinics: {len(tier2):,}")
    
    # DRIVER ANALYSIS
    print("\n📊 DOMINANT DRIVERS ANALYSIS:")
    print("-"*80)
    
    # Parse scoring_drivers to count occurrences
    driver_counts = {}
    for drivers_str in tier2['scoring_drivers'].dropna():
        for driver in str(drivers_str).split(' | '):
            driver = driver.strip()
            if driver:
                driver_counts[driver] = driver_counts.get(driver, 0) + 1
    
    # Sort by frequency
    sorted_drivers = sorted(driver_counts.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\nTop 10 Most Common Drivers:")
    for i, (driver, count) in enumerate(sorted_drivers[:10], 1):
        pct = count / len(tier2) * 100
        print(f"   {i}. {driver}: {count:,} ({pct:.1f}%)")
    
    # KEY SIGNALS
    print(f"\n🎯 KEY SIGNAL BREAKDOWN:")
    print("-"*80)
    
    high_burnout = tier2['scoring_drivers'].str.contains('High Burnout', na=False).sum()
    financial_desp = tier2['scoring_drivers'].str.contains('Financial Desperation', na=False).sum()
    compliance_risk = tier2['scoring_drivers'].str.contains('Compliance Risk', na=False).sum()
    severe_underc = tier2['scoring_drivers'].str.contains('Severe Undercoding', na=False).sum()
    operational_chaos = tier2['scoring_drivers'].str.contains('Operational Chaos', na=False).sum()
    
    print(f"   High Burnout: {high_burnout:,} ({high_burnout/len(tier2):.1%})")
    print(f"   Financial Desperation: {financial_desp:,} ({financial_desp/len(tier2):.1%})")
    print(f"   Compliance Risk: {compliance_risk:,} ({compliance_risk/len(tier2):.1%})")
    print(f"   Severe Undercoding: {severe_underc:,} ({severe_underc/len(tier2):.1%})")
    print(f"   Operational Chaos: {operational_chaos:,} ({operational_chaos/len(tier2):.1%})")
    
    # PROFILE CLASSIFICATION
    print(f"\n💡 PROFILE CLASSIFICATION:")
    print("-"*80)
    
    busy_messy = high_burnout + operational_chaos
    broke_desperate = financial_desp
    
    print(f"   'Busy & Messy' (Burnout + Chaos): {busy_messy:,} ({busy_messy/len(tier2):.1%})")
    print(f"   'Broke & Desperate' (Financial): {broke_desperate:,} ({broke_desperate/len(tier2):.1%})")
    
    if busy_messy > broke_desperate:
        print(f"\n   ✅ PRIMARY TARGET: 'Busy & Messy' clinics")
        print(f"      → Focus messaging on automation & burnout relief")
    else:
        print(f"\n   ✅ PRIMARY TARGET: 'Broke & Desperate' clinics")
        print(f"      → Focus messaging on revenue recovery & financial survival")
    
    # SEGMENT DISTRIBUTION
    print(f"\n📈 SEGMENT DISTRIBUTION:")
    print("-"*80)
    seg_dist = tier2['segment_label'].value_counts().head(10)
    for seg, count in seg_dist.items():
        pct = count / len(tier2) * 100
        avg_score = tier2[tier2['segment_label'] == seg]['icp_score'].mean()
        print(f"   {seg}: {count:,} ({pct:.1f}%) | Avg Score: {avg_score:.1f}")
    
    # SCORE DISTRIBUTION
    print(f"\n📊 SCORE DISTRIBUTION:")
    print("-"*80)
    print(f"   Min Score: {tier2['icp_score'].min()}")
    print(f"   Max Score: {tier2['icp_score'].max()}")
    print(f"   Mean Score: {tier2['icp_score'].mean():.1f}")
    print(f"   Median Score: {tier2['icp_score'].median():.1f}")
    
    # EXPORT TOP 50
    print(f"\n💾 EXPORTING TOP 50 CLINICS:")
    print("-"*80)
    
    top50 = df.nlargest(50, 'icp_score')
    
    export_cols = [
        'npi', 'org_name', 'segment_label', 'state_code',
        'icp_score', 'icp_tier', 'scoring_track',
        'scoring_drivers',
        'score_pain_total', 'score_fit_total', 'score_strat_total',
        'metric_est_revenue', 'metric_used_volume',
        'undercoding_ratio', 'psych_risk_ratio',
        'net_margin', 'npi_count',
        'data_confidence'
    ]
    
    available_cols = [c for c in export_cols if c in top50.columns]
    top50[available_cols].to_csv(OUTPUT_FILE, index=False)
    
    print(f"   ✅ Saved to: {OUTPUT_FILE}")
    print(f"   Columns: {len(available_cols)}")
    print(f"\n   Top 5 Preview:")
    for idx, row in top50.head(5).iterrows():
        print(f"\n   {row['org_name']}")
        print(f"      Score: {row['icp_score']} | Tier: {row['icp_tier']}")
        print(f"      Drivers: {row.get('scoring_drivers', 'N/A')}")

if __name__ == "__main__":
    analyze_tier2()
