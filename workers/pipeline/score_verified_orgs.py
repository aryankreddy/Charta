"""
VERIFIED ORGANIZATION SCORER
Generates Financial Intelligence and ICP Scores for Verified Organizations.
"""

import pandas as pd
import numpy as np
import os
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
INPUT_FILE = ROOT / "data/curated/verified_organizations.csv"
CERT_FILE = ROOT / "data/raw/cert_specialty_benchmarks.csv"
OUTPUT_FILE = ROOT / "web/public/data/leads_database.json"

# Constants
AVG_REIMBURSEMENT = 150.0 
COMMERCIAL_MULTIPLIER = 3.0
BENCHMARK_LEVEL_4_RATIO = 0.45

# Lists for Smart Filter
WHITELIST_KEYWORDS = [
    'HEALTH', 'CLINIC', 'HOSPITAL', 'CENTER', 'MEDICAL', 
    'PLANNED PARENTHOOD', 'KAISER', 'FOUNDATION', 'DEPARTMENT', 'ASSOCIATES'
]

RETAIL_BLACKLIST = [
    'CVS', 'WALGREEN', 'QUEST', 'LABCORP', 'LABORATORY CORPORATION', 
    'RITE AID', 'WAL-MART', 'KROGER', 'COSTCO'
]

# Categories that need whitelist check
RESTRICTED_SPECIALTIES = [
    'Clinical Laboratory', 
    'Pharmacy',
    'Mass Immunization Roster Biller',
    'Public Health or Welfare Agency' # Added back to be checked
]

# Categories to always exclude if not whitelisted (or maybe just use the logic below)
ALWAYS_EXCLUDE = [
    'Ambulance', 
    'Diagnostic Radiology',
    'Centralized Flu'
]

def score_verified_orgs():
    print("🚨 SCORING VERIFIED ORGANIZATIONS (SMART FILTER)")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return
        
    if not os.path.exists(CERT_FILE):
        print(f"❌ CERT file not found: {CERT_FILE}")
        return

    # Load Data
    print("📊 Loading data...")
    df = pd.read_csv(INPUT_FILE)
    cert_df = pd.read_csv(CERT_FILE)
    
    # Create CERT dictionary for fast lookup
    # Normalize keys to lower case for better matching
    cert_map = dict(zip(cert_df['provider_type'].str.lower(), cert_df['improper_payment_rate']))
    
    print(f"   Loaded {len(df):,} organizations")
    print(f"   Loaded {len(cert_map)} CERT benchmarks")
    
    results = []
    filtered_count = 0
    recovered_whales = 0
    
    print("🔄 Processing organizations...")
    
    for _, row in df.iterrows():
        # 1. Parse Billing Codes
        try:
            billing_codes = json.loads(row['billing_codes']) if isinstance(row['billing_codes'], str) else {}
        except:
            billing_codes = {}
            
        # 2. Determine Track & Filter
        org_name = str(row['organization_name']).upper()
        specialty = str(row['specialty'])
        
        # SMART FILTER LOGIC
        keep = True
        
        # Step A: Retail Purge
        if any(retail in org_name for retail in RETAIL_BLACKLIST):
            keep = False
            
        # Step B: Category Check
        if keep:
            # Check if specialty is in restricted list
            is_restricted = any(r.lower() in specialty.lower() for r in RESTRICTED_SPECIALTIES)
            is_excluded = any(e.lower() in specialty.lower() for e in ALWAYS_EXCLUDE)
            
            if is_excluded:
                keep = False
            elif is_restricted:
                # Check Whitelist
                has_whitelist = any(w in org_name for w in WHITELIST_KEYWORDS)
                if not has_whitelist:
                    keep = False
                else:
                    # It's a restricted category but whitelisted (e.g. Kaiser Lab)
                    # We keep it.
                    pass
        
        if not keep:
            filtered_count += 1
            continue
        
        # Track assignment
        if 'HEALTH CENTER' in org_name or 'FQHC' in org_name:
            track = 'FQHC'
        elif any(x in specialty for x in ['Psych', 'Behavioral']):
            track = 'Behavioral'
        elif 'Chiro' in specialty:
            track = 'Chiropractic'
        else:
            track = 'Primary/Specialty'
            
        # 3. Calculate Revenue Proxy
        # Addressable Volume = E&M + Psych + Chiro
        addressable_volume = 0.0
        
        for code, count in billing_codes.items():
            try:
                if code.isdigit():
                    code_num = int(code)
                    if (99202 <= code_num <= 99215) or \
                       (90832 <= code_num <= 90838) or \
                       (98940 <= code_num <= 98942):
                        addressable_volume += count
            except:
                continue
        
        total_claims = float(row['total_claims_volume'])
        est_revenue = 0.0
        evidence = ""
        
        # Whale Logic
        if addressable_volume > 0:
            est_revenue = addressable_volume * AVG_REIMBURSEMENT * COMMERCIAL_MULTIPLIER
        elif total_claims > 10000:
            # Whale with no addressable volume (yet)
            # Discounted rate for non-E&M volume
            est_revenue = total_claims * 50.0 
            evidence = "High Volume Organization (Requires Claims Analysis)"
            recovered_whales += 1
        else:
            # Low volume, no addressable -> Likely irrelevant or very small
            est_revenue = 0.0
        
        # 4. Calculate The "Smoking Gun" (Evidence)
        gap = 0.0
        
        if not evidence: # Only calculate if not already set as Whale
            # Check 1: Real Data (E&M Codes)
            em_codes = ['99213', '99214', '99215']
            total_em = sum(billing_codes.get(c, 0) for c in em_codes)
            
            if total_em > 10: 
                level_4_count = billing_codes.get('99214', 0)
                ratio = level_4_count / total_em
                
                if ratio < 0.35:
                    gap = BENCHMARK_LEVEL_4_RATIO - ratio
                    evidence = f"Verified: Under-coding Level 4 by {gap:.0%}"
            
            # Check 2: Benchmark
            if gap == 0.0:
                spec_key = specialty.lower()
                cert_rate = cert_map.get(spec_key)
                
                if cert_rate is None:
                    for k, v in cert_map.items():
                        if k in spec_key or spec_key in k:
                            cert_rate = v
                            break
                
                if cert_rate:
                    gap = cert_rate
                    evidence = f"Projected: {specialty} Avg Error Rate {gap:.0%}"
                else:
                    gap = 0.05
                    evidence = f"Projected: Standard Risk 5%"
        else:
            # Whale evidence set, use standard gap for dollars calculation
            gap = 0.05 # Default risk
            
        opportunity_dollars = est_revenue * gap
        
        # 5. Calculate ICP Score (0-100)
        # Revenue Score (Max 40)
        if est_revenue > 5_000_000:
            rev_score = 40
        elif est_revenue > 1_000_000:
            rev_score = 20
        else:
            rev_score = 5
            
        # Pain Score (Max 40)
        if gap > 0.15:
            pain_score = 40
        elif gap > 0.05:
            pain_score = 20
        else:
            pain_score = 5
            
        # Confidence (Max 20)
        conf_score = 20 # Verified Orgs
        
        icp_score = rev_score + pain_score + conf_score
        
        # Format for JSON
        results.append({
            "organization_name": row['organization_name'], # Use original case
            "track_label": track,
            "est_revenue": f"${est_revenue:,.0f}",
            "opportunity_dollars": f"${opportunity_dollars:,.0f}",
            "primary_evidence": evidence,
            "icp_score": icp_score,
            "specialty": specialty,
            # Keep raw values for sorting if needed later, but user asked for specific JSON structure
            # Adding raw values as hidden fields just in case
            "_raw_revenue": est_revenue,
            "_raw_opportunity": opportunity_dollars
        })
        
    # Sort by Opportunity Dollars descending
    results.sort(key=lambda x: x['_raw_opportunity'], reverse=True)
    
    # Remove raw fields for final output
    final_output = []
    for r in results:
        final_output.append({k: v for k, v in r.items() if not k.startswith('_')})
        
    # EXPORT
    os.makedirs(OUTPUT_FILE.parent, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(final_output, f, indent=2)
        
    print(f"\n💾 Saved to: {OUTPUT_FILE}")
    
    # Stats
    avg_score = np.mean([r['icp_score'] for r in results]) if results else 0
    top_opp = results[0] if results else None
    
    print(f"✅ Scored {len(results):,} Organizations.")
    print(f"🚫 Filtered out {filtered_count:,} Retail/Non-Clinical Organizations.")
    print(f"🐳 Recovered {recovered_whales:,} Whales (High Volume, No E&M).")
    if top_opp:
        print(f"   Top Opportunity: {top_opp['opportunity_dollars']} ({top_opp['organization_name']})")
    print(f"   Average Score: {avg_score:.1f}")

if __name__ == "__main__":
    score_verified_orgs()
