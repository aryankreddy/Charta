"""
v10.0 ORGANIZATION SCORING ENGINE
Dynamic Financial Modeling & Specialty Benchmarking

Logic:
1. Revenue = Volume * $100 (Avg Rate) * 3.0 (Commercial Multiplier)
2. Leakage Rate = Specific Specialty Benchmark (CERT)
3. Opportunity = Revenue * Leakage Rate

Output: Scored Organizations with dynamic financials
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
INPUT_FILE = ROOT / "data/curated/staging/billing_intelligence_orgs.csv"
CERT_FILE = ROOT / "data/raw/cert_specialty_benchmarks.csv"
OUTPUT_FILE = ROOT / "data/curated/leads_scored.csv"

# E&M Benchmarks (Default fallback)
EM_BENCHMARKS = {'99213': 38.3, '99214': 50.7, '99215': 7.0}

def load_cert_benchmarks():
    """Load CERT benchmarks into a dictionary"""
    try:
        df = pd.read_csv(CERT_FILE)
        # Normalize keys
        return dict(zip(df['provider_type'].str.lower(), df['improper_payment_rate']))
    except Exception as e:
        print(f"⚠️ Warning: Could not load CERT benchmarks: {e}")
        return {}

def calculate_scores(row, cert_benchmarks):
    """
    Calculate ICP Score (0-100) and Financials based on Bell Curve Logic.
    """
    
    # 1. BOTTOM-UP REVENUE
    volume = float(row.get('total_claims_volume', 0))
    provider_count = int(row.get('provider_count', 1))
    
    # Medicare Revenue Estimate ($100 avg rate)
    medicare_rev = volume * 100
    
    # Total Est Revenue (3.0x Commercial Multiplier)
    est_revenue = medicare_rev * 3.0
    
    # 2. DYNAMIC LEAKAGE RATE
    specialty = str(row.get('primary_specialty', '')).lower()
    
    # Look up specific benchmark
    leakage_rate = 0.05  # Default conservative
    if specialty in cert_benchmarks:
        leakage_rate = cert_benchmarks[specialty]
    else:
        for key, rate in cert_benchmarks.items():
            if key in specialty or specialty in key:
                leakage_rate = rate
                break
    
    # 3. CALCULATE OPPORTUNITY
    opportunity = est_revenue * leakage_rate
    
    # 4. BELL CURVE SCORING (The User's Formula)
    
    # A. Financial Magnitude (Max 40)
    score_revenue = 5
    if est_revenue > 5_000_000:
        score_revenue = 40
    elif est_revenue > 1_000_000:
        score_revenue = 20
        
    # B. Operational Pain (Max 30)
    score_pain = 0
    if leakage_rate > 0.15:
        score_pain = 30
    elif leakage_rate > 0.05:
        score_pain = 15
        
    # C. Chaos Scale (Max 30)
    score_chaos = 0
    if provider_count > 10:
        score_chaos = 30
    elif provider_count > 3:
        score_chaos = 15
        
    icp_score = score_revenue + score_pain + score_chaos
    
    # 5. CONFIDENCE BADGE (Separate from Score)
    # High = >1000 claims, Med = >500 claims, Low = <500
    confidence = 50
    if volume > 1000:
        confidence = 90
    elif volume > 500:
        confidence = 75
        
    return int(est_revenue), int(opportunity), leakage_rate, icp_score, confidence

def identify_smoking_gun(row, leakage_rate):
    """Identify the primary evidence string"""
    
    track = str(row.get('track', 'Other'))
    specialty = str(row.get('primary_specialty', 'Unknown'))
    
    # Behavioral
    if track == 'Behavioral Health':
        risk_ratio = float(row.get('psych_risk_ratio', 0))
        if risk_ratio > 0.6:
            return {
                "headline": "High Audit Risk",
                "detail": f"Bills 60-min sessions {(risk_ratio*100):.0f}% of time (High Risk)",
                "type": "audit_risk"
            }
    
    # Primary Care / E&M
    if track == 'Primary Care' or float(row.get('total_em', 0)) > 50:
        pct_99214 = float(row.get('99214_pct', 0))
        if pct_99214 < 40:
            return {
                "headline": "E&M Undercoding",
                "detail": f"Level 4 usage is {pct_99214:.0f}% (Benchmark: ~50%)",
                "type": "em_gap"
            }
            
    # Default based on leakage
    return {
        "headline": f"{specialty} Leakage",
        "detail": f"Projected {leakage_rate*100:.1f}% revenue leakage based on {specialty} benchmarks",
        "type": "revenue_leakage"
    }

def score_orgs():
    print("🎯 v10.0 ORGANIZATION SCORING ENGINE (BELL CURVE)")
    print("=" * 60)
    
    # Load data
    print("📂 Loading data...")
    df = pd.read_csv(INPUT_FILE)
    cert_benchmarks = load_cert_benchmarks()
    print(f"   Loaded {len(df):,} organizations")
    
    # Filter to meaningful volume (>50 claims)
    active = df[df['total_claims_volume'] > 50].copy()
    print(f"   Filtered to {len(active):,} active organizations (>50 claims)")
    
    # Calculate Scores & Financials
    print("💰 Calculating Bell Curve Scores...")
    scores = active.apply(
        lambda row: pd.Series(calculate_scores(row, cert_benchmarks)), 
        axis=1
    )
    active['est_revenue'] = scores[0]
    active['est_opportunity'] = scores[1]
    active['leakage_rate'] = scores[2]
    active['icp_score'] = scores[3]
    active['confidence'] = scores[4]
    
    # Identify Smoking Gun
    print("🔍 Identifying smoking guns...")
    smoking_guns = active.apply(
        lambda row: pd.Series(identify_smoking_gun(row, row['leakage_rate'])), 
        axis=1
    )
    active['primary_evidence'] = smoking_guns['detail']
    active['evidence_type'] = smoking_guns['type']
    active['evidence_headline'] = smoking_guns['headline']
    
    # Save
    active.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved scored organizations to: {OUTPUT_FILE}")
    
    # Stats
    print(f"\n📈 SCORING RESULTS:")
    print(f"   Total Scored: {len(active):,}")
    print(f"   Avg ICP Score: {active['icp_score'].mean():.1f}")
    print(f"   Avg Revenue: ${active['est_revenue'].mean():,.0f}")
    
    print(f"\n   Score Distribution:")
    print(active['icp_score'].value_counts(bins=5).sort_index())
    
    print(f"\n   Top Opportunities:")
    top = active.nlargest(5, 'icp_score')
    for _, row in top.iterrows():
        print(f"     {row['org_name']} ({row['provider_count']} Provs)")
        print(f"       Score: {row['icp_score']} | Rev: ${row['est_revenue']:,}")
        print(f"       Evidence: {row['primary_evidence']}")

if __name__ == "__main__":
    score_orgs()
