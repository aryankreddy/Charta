"""
v9.0 LEAD SCORING ENGINE
Calculate Financial Opportunity & Confidence for ALL 530k Leads

Applies intelligence to the giant database:
- Financial Opportunity ($)
- Confidence Score (0-100)
- Track Assignment
- Primary Evidence
"""

import pandas as pd
import numpy as np
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Input
BILLING_FILE = os.path.join(ROOT, "data", "curated", "staging", "billing_intelligence_full.csv")
MAIN_FILE = os.path.join(ROOT, "data", "curated", "clinics_final_enriched.csv")

# Output
OUTPUT_FILE = os.path.join(ROOT, "data", "curated", "leads_scored.csv")

# Revenue benchmarks by track
REVENUE_BENCHMARKS = {
    'Primary Care': 300000,  # Per provider
    'Behavioral': 200000,
    'Chiropractic': 200000,
    'Other': 250000
}

# E&M Benchmarks
EM_BENCHMARKS = {'99213': 38.3, '99214': 50.7, '99215': 7.0}

def calculate_financial_opportunity(row):
    """
    Calculate financial opportunity for a lead.
    
    Returns: (opportunity_dollars, leakage_rate, revenue_proxy, primary_evidence)
    """
    
    track = str(row.get('primary_track', 'Other'))
    
    # 1. REVENUE PROXY
    # Try to get real revenue first
    est_revenue = float(row.get('est_revenue', 0)) if 'est_revenue' in row else 0
    
    if est_revenue == 0:
        # Use provider count if available
        provider_count = int(row.get('provider_count', 1)) if 'provider_count' in row else 1
        benchmark = REVENUE_BENCHMARKS.get(track, 250000)
        revenue_proxy = provider_count * benchmark
    else:
        revenue_proxy = est_revenue
    
    # 2. LEAKAGE RATE
    leakage_rate = 0.03  # Conservative default
    primary_evidence = "Standard opportunity"
    
    # Check for E&M gaps (Primary Care)
    if track == 'Primary Care':
        total_em = float(row.get('total_em', 0))
        
        if total_em > 50:
            # Check Level 4 gap
            pct_99214 = float(row.get('99214_pct', 0))
            benchmark_99214 = EM_BENCHMARKS['99214']
            gap_99214 = benchmark_99214 - pct_99214
            
            # Check Level 5 gap
            pct_99215 = float(row.get('99215_pct', 0))
            benchmark_99215 = EM_BENCHMARKS['99215']
            gap_99215 = benchmark_99215 - pct_99215
            
            # Use the larger gap
            if gap_99214 > 5:
                leakage_rate = min(gap_99214 / 100, 0.25)  # Cap at 25%
                primary_evidence = f"Under-coding Level 4 by {gap_99214:.0f}%"
            elif gap_99215 > 3:
                leakage_rate = min(gap_99215 / 100, 0.15)  # Cap at 15%
                primary_evidence = f"Under-coding Level 5 by {gap_99215:.0f}%"
            elif gap_99214 > 0 or gap_99215 > 0:
                # Small gap
                leakage_rate = 0.05
                primary_evidence = "Minor E&M coding opportunity"
    
    # Check for Behavioral audit risk
    elif track == 'Behavioral':
        risk_ratio = float(row.get('psych_risk_ratio', 0))
        total_psych = float(row.get('total_psych', 0))
        
        if risk_ratio > 0.7 and total_psych > 100:
            leakage_rate = 0.15  # Risk reversal opportunity
            primary_evidence = f"High audit risk - {risk_ratio*100:.0f}% 60-min sessions"
        elif risk_ratio > 0.6 and total_psych > 100:
            leakage_rate = 0.10
            primary_evidence = f"Moderate audit risk - {risk_ratio*100:.0f}% 60-min sessions"
        elif total_psych > 500:
            leakage_rate = 0.05
            primary_evidence = f"High-volume behavioral ({total_psych:.0f} sessions/year)"
    
    # Chiropractic
    elif track == 'Chiropractic':
        total_chiro = float(row.get('total_chiro', 0))
        if total_chiro > 500:
            leakage_rate = 0.05
            primary_evidence = f"High-volume chiropractic ({total_chiro:.0f} adjustments/year)"
    
    # 3. CALCULATE OPPORTUNITY
    opportunity = revenue_proxy * leakage_rate
    
    return opportunity, leakage_rate, revenue_proxy, primary_evidence

def calculate_confidence_score(row):
    """
    Calculate confidence score (0-100) based on data quality.
    """
    
    score = 0
    
    # +50 for billing data
    total_em = float(row.get('total_em', 0))
    total_psych = float(row.get('total_psych', 0))
    total_chiro = float(row.get('total_chiro', 0))
    
    if total_em > 50 or total_psych > 50 or total_chiro > 50:
        score += 50
    
    # +20 for verified volume
    if 'volume_source' in row and str(row.get('volume_source')) == 'real':
        score += 20
    elif total_em > 100 or total_psych > 100:
        score += 10  # High billing volume is a proxy for verified data
    
    # +10 for each risk flag
    if 'psych_risk_ratio' in row:
        risk_ratio = float(row.get('psych_risk_ratio', 0))
        if risk_ratio > 0.7:
            score += 10
    
    # +10 for E&M gap
    if 'is_em_track' in row and row.get('is_em_track'):
        pct_99214 = float(row.get('99214_pct', 0))
        if pct_99214 < 45:
            score += 10
    
    # +10 for organization name (not just NPI)
    if 'org_name' in row and str(row.get('org_name')) not in ['nan', '', 'Unknown']:
        score += 10
    
    return min(score, 100)  # Cap at 100

def assign_track_label(row):
    """Assign human-readable track label"""
    
    track = str(row.get('primary_track', 'Other'))
    
    # Map to display labels
    track_map = {
        'Primary Care': 'Primary Care',
        'Behavioral': 'Behavioral Health',
        'Chiropractic': 'Chiropractic',
        'Other': 'Other'
    }
    
    return track_map.get(track, 'Other')

def score_leads():
    """
    Score all leads in the billing intelligence database.
    """
    
    print("🎯 v9.0 LEAD SCORING ENGINE")
    print("=" * 60)
    
    # Load billing intelligence
    print(f"\n📂 Loading billing intelligence...")
    df = pd.read_csv(BILLING_FILE, low_memory=False)
    print(f"   Loaded {len(df):,} providers")
    
    # Filter to meaningful leads (>50 codes)
    meaningful = df[
        ((df['is_em_track']) & (df['total_em'] > 50)) |
        ((df['is_psych_track']) & (df['total_psych'] > 50)) |
        ((df['is_chiro_track']) & (df['total_chiro'] > 50))
    ].copy()
    
    print(f"   Filtered to {len(meaningful):,} meaningful leads")
    
    # Calculate scores
    print(f"\n💰 Calculating financial opportunities...")
    
    results = meaningful.apply(
        lambda row: pd.Series(calculate_financial_opportunity(row)),
        axis=1
    )
    
    meaningful['est_opportunity_dollars'] = results[0].round(0).astype(int)
    meaningful['leakage_rate'] = results[1].round(3)
    meaningful['revenue_proxy'] = results[2].round(0).astype(int)
    meaningful['primary_evidence'] = results[3]
    
    # Calculate confidence
    print(f"📊 Calculating confidence scores...")
    meaningful['data_confidence_score'] = meaningful.apply(calculate_confidence_score, axis=1)
    
    # Assign track labels
    meaningful['track_label'] = meaningful.apply(assign_track_label, axis=1)
    
    # Save
    meaningful.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved scored leads to: {OUTPUT_FILE}")
    
    # Stats
    print(f"\n📈 SCORING RESULTS:")
    print(f"   Total Leads Scored: {len(meaningful):,}")
    
    # By track
    print(f"\n   By Track:")
    for track in meaningful['track_label'].unique():
        track_df = meaningful[meaningful['track_label'] == track]
        avg_opp = track_df['est_opportunity_dollars'].mean()
        avg_conf = track_df['data_confidence_score'].mean()
        print(f"     {track}:")
        print(f"       Count: {len(track_df):,}")
        print(f"       Avg Opportunity: ${avg_opp:,.0f}")
        print(f"       Avg Confidence: {avg_conf:.0f}")
    
    # Opportunity distribution
    print(f"\n   Opportunity Distribution:")
    print(f"     >$100k: {len(meaningful[meaningful['est_opportunity_dollars'] > 100000]):,}")
    print(f"     >$50k: {len(meaningful[meaningful['est_opportunity_dollars'] > 50000]):,}")
    print(f"     >$25k: {len(meaningful[meaningful['est_opportunity_dollars'] > 25000]):,}")
    
    # Confidence distribution
    print(f"\n   Confidence Distribution:")
    print(f"     High (>70): {len(meaningful[meaningful['data_confidence_score'] > 70]):,}")
    print(f"     Medium (50-70): {len(meaningful[(meaningful['data_confidence_score'] >= 50) & (meaningful['data_confidence_score'] <= 70)]):,}")
    print(f"     Low (<50): {len(meaningful[meaningful['data_confidence_score'] < 50]):,}")
    
    # Top opportunities
    print(f"\n🏆 TOP 10 OPPORTUNITIES:")
    top_10 = meaningful.nlargest(10, 'est_opportunity_dollars')[
        ['org_name', 'state', 'track_label', 'est_opportunity_dollars', 'primary_evidence', 'data_confidence_score']
    ]
    for idx, row in top_10.iterrows():
        print(f"\n   {row['org_name']} ({row['state']})")
        print(f"     Track: {row['track_label']}")
        print(f"     Opportunity: ${row['est_opportunity_dollars']:,}")
        print(f"     Evidence: {row['primary_evidence']}")
        print(f"     Confidence: {row['data_confidence_score']}")

if __name__ == "__main__":
    score_leads()
