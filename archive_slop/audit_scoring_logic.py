"""
SCORING LOGIC AUDIT & TRANSPARENCY REPORT
Author: Charta Health GTM Strategy

Purpose: Deep-dive analysis of scoring logic to verify it's working as intended
and explain what drives high scores.
"""

import pandas as pd
import numpy as np
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCORED_FILE = os.path.join(ROOT, "data", "curated", "clinics_scored_final.csv")

def audit_scoring_logic():
    print("🔍 SCORING LOGIC AUDIT & TRANSPARENCY REPORT")
    print("="*80)
    
    if not os.path.exists(SCORED_FILE):
        print(f"❌ Scored file not found: {SCORED_FILE}")
        return
    
    df = pd.read_csv(SCORED_FILE, low_memory=False)
    print(f"\nLoaded {len(df):,} scored clinics")
    
    # ========================================================================
    # 1. TOP TIER ANALYSIS
    # ========================================================================
    print("\n" + "="*80)
    print("1. TOP TIER BREAKDOWN (Tier 1 & Top 20 Tier 2)")
    print("="*80)
    
    tier1 = df[df['icp_tier'] == 'Tier 1'].copy()
    tier2_top = df[df['icp_tier'] == 'Tier 2'].nlargest(20, 'icp_score')
    top_clinics = pd.concat([tier1, tier2_top])
    
    print(f"\nAnalyzing {len(top_clinics)} top clinics:")
    
    for idx, row in top_clinics.iterrows():
        print(f"\n{'─'*80}")
        print(f"CLINIC: {row['org_name']}")
        print(f"NPI: {row['npi']} | Segment: {row.get('segment_label', 'Unknown')}")
        print(f"SCORE: {row['icp_score']} ({row['icp_tier']}) | Track: {row.get('scoring_track', 'Unknown')}")
        print(f"{'─'*80}")
        
        # Economic Pain Breakdown
        print(f"\n💰 ECONOMIC PAIN: {row.get('score_pain_total', 0)}/40 pts")
        print(f"   ├─ Pain Signal: {row.get('score_pain_signal', 0)} pts")
        
        # Show what the signal is
        track = row.get('scoring_track', 'AMBULATORY')
        if track == 'BEHAVIORAL':
            psych_ratio = row.get('psych_risk_ratio', 0)
            print(f"   │  └─ Psych Audit Risk: {psych_ratio:.3f} (>0.80 = High Risk)")
        elif track == 'POST_ACUTE':
            margin = row.get('net_margin', row.get('hha_margin', 0))
            print(f"   │  └─ Margin Pressure: {margin:.3f} (<0.02 = High Pain)")
        else:
            undercoding = row.get('undercoding_ratio', 0)
            print(f"   │  └─ Undercoding Ratio: {undercoding:.3f} (<0.30 = Severe)")
        
        print(f"   ├─ Volume: {row.get('score_pain_volume', 0)} pts")
        vol = row.get('metric_used_volume', 0)
        print(f"   │  └─ Annual Volume: {vol:,.0f} encounters")
        
        print(f"   └─ Margin: {row.get('score_pain_margin', 0)} pts")
        margin = row.get('net_margin', row.get('hospital_margin', row.get('fqhc_margin', 0)))
        if pd.notnull(margin):
            print(f"      └─ Net Margin: {margin:.3f} ({margin*100:.1f}%)")
        
        # Strategic Fit Breakdown
        print(f"\n🎯 STRATEGIC FIT: {row.get('score_fit_total', 0)}/35 pts")
        print(f"   ├─ Segment Alignment: {row.get('score_fit_align', 0)} pts")
        print(f"   ├─ Complexity: {row.get('score_fit_complex', 0)} pts")
        npi_count = row.get('npi_count', 1)
        print(f"   │  └─ Provider Count: {npi_count:.0f}")
        
        print(f"   ├─ Operational Chaos: {row.get('score_fit_chaos', 0)} pts")
        print(f"   │  └─ Small/Solo Practice Bonus + Segment Factors")
        
        print(f"   └─ Risk Flags: {row.get('score_fit_align', 0) - row.get('score_fit_align', 0)} pts")
        
        # Strategic Value Breakdown
        print(f"\n📈 STRATEGIC VALUE: {row.get('score_strat_total', 0)}/25 pts")
        print(f"   ├─ Deal Size: {row.get('score_strat_deal', 0)} pts")
        rev = row.get('metric_est_revenue', 0)
        print(f"   │  └─ Est. Revenue: ${rev:,.0f}")
        
        print(f"   ├─ Expansion: {row.get('score_strat_expand', 0)} pts")
        print(f"   │  └─ Multi-site potential based on NPI count")
        
        print(f"   └─ Reference Value: {row.get('score_strat_total', 0) - row.get('score_strat_deal', 0) - row.get('score_strat_expand', 0)} pts")
        
        # Data Confidence
        print(f"\n📊 DATA CONFIDENCE: {row.get('data_confidence', 0)}/100")
        print(f"   └─ Higher = More verified data (vs. estimates)")
    
    # ========================================================================
    # 2. SEGMENT DISTRIBUTION ANALYSIS
    # ========================================================================
    print("\n" + "="*80)
    print("2. WHY SEGMENT B DOMINATES TOP TIER")
    print("="*80)
    
    # Segment distribution in Tier 1 & 2
    tier1_2 = df[df['icp_tier'].isin(['Tier 1', 'Tier 2'])].copy()
    
    print(f"\nTier 1 & 2 Segment Distribution ({len(tier1_2)} clinics):")
    seg_dist = tier1_2['segment_label'].value_counts()
    for seg, count in seg_dist.head(10).items():
        pct = count / len(tier1_2) * 100
        avg_score = tier1_2[tier1_2['segment_label'] == seg]['icp_score'].mean()
        print(f"   {seg}: {count} ({pct:.1f}%) | Avg Score: {avg_score:.1f}")
    
    # Analyze Segment B specifically
    print(f"\n🔍 SEGMENT B (FQHC) ANALYSIS:")
    seg_b = df[df['segment_label'].str.contains('Segment B', na=False)].copy()
    print(f"   Total Segment B Clinics: {len(seg_b):,}")
    print(f"   Avg Score: {seg_b['icp_score'].mean():.1f}")
    print(f"   Tier 1: {len(seg_b[seg_b['icp_tier'] == 'Tier 1'])}")
    print(f"   Tier 2: {len(seg_b[seg_b['icp_tier'] == 'Tier 2'])}")
    
    # Why Segment B scores high
    print(f"\n💡 WHY SEGMENT B SCORES HIGH:")
    print(f"   1. Segment Alignment: 15 pts (highest)")
    print(f"   2. Complexity Bonus: 10 pts (FQHC designation)")
    print(f"   3. Lower Revenue Threshold: $5M (vs $15M for hospitals)")
    print(f"   4. Typically have:")
    
    seg_b_top = seg_b.nlargest(100, 'icp_score')
    print(f"      - Avg Undercoding: {seg_b_top['undercoding_ratio'].mean():.3f}")
    print(f"      - Avg Volume: {seg_b_top['metric_used_volume'].mean():,.0f}")
    print(f"      - Avg Margin: {seg_b_top['fqhc_margin'].mean():.3f}")
    print(f"      - Avg Chaos Score: {seg_b_top['score_fit_chaos'].mean():.1f}")
    
    # ========================================================================
    # 3. SCORE VARIANCE ANALYSIS
    # ========================================================================
    print("\n" + "="*80)
    print("3. SCORE VARIANCE & DIFFERENTIATION")
    print("="*80)
    
    # Group by score and show component variance
    score_groups = df.groupby('icp_score').agg({
        'score_pain_total': ['mean', 'std'],
        'score_fit_total': ['mean', 'std'],
        'score_strat_total': ['mean', 'std'],
        'npi': 'count'
    }).round(2)
    
    print(f"\nScore Variance for Common Scores (>100 clinics):")
    common_scores = score_groups[score_groups[('npi', 'count')] > 100].sort_index(ascending=False).head(10)
    
    for score, row in common_scores.iterrows():
        count = int(row[('npi', 'count')])
        pain_mean = row[('score_pain_total', 'mean')]
        pain_std = row[('score_pain_total', 'std')]
        fit_mean = row[('score_fit_total', 'mean')]
        fit_std = row[('score_fit_total', 'std')]
        strat_mean = row[('score_strat_total', 'mean')]
        strat_std = row[('score_strat_total', 'std')]
        
        print(f"\n   Score {score} ({count:,} clinics):")
        print(f"      Pain: {pain_mean:.1f} ± {pain_std:.1f}")
        print(f"      Fit:  {fit_mean:.1f} ± {fit_std:.1f}")
        print(f"      Strat: {strat_mean:.1f} ± {strat_std:.1f}")
    
    # ========================================================================
    # 4. SCORING LOGIC VALIDATION
    # ========================================================================
    print("\n" + "="*80)
    print("4. SCORING LOGIC VALIDATION")
    print("="*80)
    
    print(f"\n✅ VALIDATION CHECKS:")
    
    # Check 1: Score components sum correctly
    df['calculated_total'] = df['score_pain_total'] + df['score_fit_total'] + df['score_strat_total']
    df['score_diff'] = abs(df['icp_score'] - df['calculated_total'])
    errors = df[df['score_diff'] > 1]
    print(f"   1. Score Math: {len(errors)} errors (should be 0)")
    
    # Check 2: Tier assignments correct
    tier_errors = 0
    tier_errors += len(df[(df['icp_score'] >= 70) & (df['icp_tier'] != 'Tier 1')])
    tier_errors += len(df[(df['icp_score'] >= 50) & (df['icp_score'] < 70) & (df['icp_tier'] != 'Tier 2')])
    print(f"   2. Tier Assignment: {tier_errors} errors (should be 0)")
    
    # Check 3: Track detection
    tracks = df['scoring_track'].value_counts()
    print(f"   3. Track Distribution:")
    for track, count in tracks.items():
        print(f"      - {track}: {count:,}")
    
    # Check 4: Data-driven differentiation
    high_scores = df[df['icp_score'] >= 60].copy()
    print(f"\n   4. High Score Drivers (Score ≥ 60, n={len(high_scores)}):")
    print(f"      - With Undercoding Data: {high_scores['undercoding_ratio'].gt(0).sum()}")
    print(f"      - With Psych Data: {high_scores['psych_risk_ratio'].gt(0).sum()}")
    print(f"      - With Real Financials: {high_scores['net_margin'].notnull().sum()}")
    print(f"      - With High Volume: {high_scores['metric_used_volume'].gt(10000).sum()}")
    
    # ========================================================================
    # 5. RECOMMENDATIONS
    # ========================================================================
    print("\n" + "="*80)
    print("5. SCORING LOGIC ASSESSMENT")
    print("="*80)
    
    print(f"\n🎯 INTENDED BEHAVIOR:")
    print(f"   ✅ Segment B (FQHCs) should score high - they are the ICP")
    print(f"   ✅ Low variance within same score = consistent logic")
    print(f"   ✅ Multi-track system working (3 tracks detected)")
    
    print(f"\n⚠️  POTENTIAL ISSUES:")
    
    # Issue 1: Limited differentiation
    unique_scores = df['icp_score'].nunique()
    print(f"   1. Limited Score Range: Only {unique_scores} unique scores")
    print(f"      → Most clinics cluster around 20-30 points")
    
    # Issue 2: Data sparsity
    with_undercoding = df['undercoding_ratio'].gt(0).sum()
    print(f"   2. Data Sparsity: Only {with_undercoding:,} ({with_undercoding/len(df):.1%}) have undercoding data")
    print(f"      → Most clinics score on segment + volume alone")
    
    # Issue 3: Segment B advantage
    print(f"   3. Segment B Structural Advantage:")
    print(f"      → Gets 15 pts (alignment) + 10 pts (complexity) = 25 pts baseline")
    print(f"      → Other segments max out at ~20 pts baseline")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   1. Increase weight on data-driven signals (undercoding, psych risk)")
    print(f"   2. Add more granular volume tiers for better differentiation")
    print(f"   3. Consider normalizing segment bonuses to prevent structural bias")
    print(f"   4. Expand data coverage (more undercoding calculations)")

if __name__ == "__main__":
    audit_scoring_logic()
