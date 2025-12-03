"""
EVIDENCE-BASED GTM INTELLIGENCE BUILDER
Transparency over Scoring - Show the "Smoking Gun"

This script builds comprehensive evidence objects for each clinic,
exposing ALL available data with context and sources.
"""

import pandas as pd
import numpy as np
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_FILE = os.path.join(ROOT, "data", "curated", "clinics_final_enriched.csv")
OUTPUT_FILE = os.path.join(ROOT, "web", "public", "data", "clinics_evidence.json")

# Specialty benchmarks for E&M codes (from our extracted data)
EM_BENCHMARKS = {
    'default': {'99213': 37.6, '99214': 51.8, '99215': 6.8}
}

def build_evidence_object(row):
    """
    Build a comprehensive evidence object for a clinic.
    Shows ALL data with context - no hiding behind scores.
    """
    
    # === BASIC PROFILE ===
    profile = {
        "id": str(row.get('clinic_id', row.get('npi', ''))),
        "name": str(row.get('org_name', 'Unknown')),
        "state": str(row.get('state_code', '')),
        "track": get_track(row),
        "segment": str(row.get('segment_label', ''))
    }
    
    # === SMOKING GUN (Primary Opportunity) ===
    smoking_gun = identify_smoking_gun(row)
    
    # === EVIDENCE SECTIONS ===
    
    # 1. REVENUE OPPORTUNITY
    revenue_evidence = build_revenue_evidence(row)
    
    # 2. VOLUME & SCALE
    volume_evidence = build_volume_evidence(row)
    
    # 3. CLINIC PROFILE
    clinic_profile = build_clinic_profile(row)
    
    # 4. BILLING INTELLIGENCE (if available)
    billing_intelligence = build_billing_intelligence(row)
    
    # 5. BEHAVIORAL HEALTH (if applicable)
    behavioral_evidence = build_behavioral_evidence(row)
    
    # 6. FQHC SPECIFICS (if applicable)
    fqhc_evidence = build_fqhc_evidence(row)
    
    # 7. RISK SIGNALS
    risk_signals = build_risk_signals(row)
    
    return {
        **profile,
        "smoking_gun": smoking_gun,
        "evidence": {
            "revenue": revenue_evidence,
            "volume": volume_evidence,
            "profile": clinic_profile,
            "billing": billing_intelligence if billing_intelligence else None,
            "behavioral": behavioral_evidence if behavioral_evidence else None,
            "fqhc": fqhc_evidence if fqhc_evidence else None,
            "risks": risk_signals
        }
    }

def get_track(row):
    """Determine primary track for this clinic"""
    segment = str(row.get('segment_label', '')).upper()
    psych_codes = float(row.get('total_psych_codes', 0))
    
    if 'SEGMENT B' in segment:
        return "FQHC"
    elif psych_codes > 1000:
        return "Behavioral"
    elif 'SEGMENT D' in segment:
        return "Urgent Care"
    elif 'SEGMENT C' in segment:
        return "Hospital"
    else:
        return "Primary Care"

def identify_smoking_gun(row):
    """
    The #1 datapoint that justifies the sales call.
    This is what the rep leads with.
    """
    
    # Check for verified undercoding
    undercoding = float(row.get('undercoding_ratio', 0))
    if undercoding > 0.20:
        revenue = float(row.get('metric_est_revenue', 0))
        opportunity = revenue * undercoding
        return {
            "type": "revenue_leakage",
            "headline": f"${opportunity/1_000_000:.1f}M Revenue Opportunity",
            "detail": f"Verified {undercoding*100:.0f}% undercoding rate",
            "confidence": "verified",
            "source": "Medicare Claims 2023"
        }
    
    # Check for psych audit risk
    psych_risk = float(row.get('psych_risk_ratio', 0))
    psych_codes = float(row.get('total_psych_codes', 0))
    if psych_risk > 1.5 and psych_codes > 500:
        return {
            "type": "audit_risk",
            "headline": "Critical Audit Risk Detected",
            "detail": f"{psych_risk:.1f}x overcoding ratio on psychotherapy codes",
            "confidence": "verified",
            "source": "Medicare Claims 2023"
        }
    
    # Check for high volume FQHC
    segment = str(row.get('segment_label', '')).upper()
    volume = float(row.get('metric_used_volume', 0))
    if 'SEGMENT B' in segment and volume > 20000:
        return {
            "type": "high_volume_fqhc",
            "headline": f"{volume/1000:.0f}k Annual Encounters",
            "detail": "High-volume FQHC likely overwhelmed",
            "confidence": "verified" if row.get('volume_source') == 'real' else "estimated",
            "source": "HRSA UDS 2023" if row.get('volume_source') == 'real' else "Estimated"
        }
    
    # Fallback: projected opportunity
    return {
        "type": "projected_opportunity",
        "headline": "Potential Revenue Optimization",
        "detail": "Specialty benchmarks suggest coding opportunity",
        "confidence": "projected",
        "source": "CERT Benchmarks"
    }

def build_revenue_evidence(row):
    """Build comprehensive revenue opportunity evidence"""
    
    undercoding = float(row.get('undercoding_ratio', 0))
    revenue = float(row.get('metric_est_revenue', 0))
    leakage_source = str(row.get('leakage_source', 'none'))
    
    if undercoding > 0:
        opportunity = revenue * undercoding
        return {
            "opportunity_amount": round(opportunity),
            "current_revenue": round(revenue),
            "undercoding_rate": round(undercoding * 100, 1),
            "confidence": "verified" if leakage_source == "verified" else "projected",
            "source": "Medicare Claims 2023" if leakage_source == "verified" else "CERT Benchmarks",
            "context": f"Clinic is leaving ${opportunity/1_000_000:.1f}M on the table annually",
            "smoking_gun": f"Undercoding at {undercoding*100:.0f}% vs. peers"
        }
    else:
        return {
            "opportunity_amount": 0,
            "current_revenue": round(revenue),
            "undercoding_rate": 0,
            "confidence": "unknown",
            "source": "No claims data available",
            "context": "Unable to verify coding patterns",
            "smoking_gun": None
        }

def build_billing_intelligence(row):
    """Build comprehensive billing intelligence with E&M code distribution"""
    
    total_em = float(row.get('total_em_codes', 0))
    
    if total_em < 50:  # Need meaningful sample size
        return None
    
    # Get E&M code distribution
    em_dist = {}
    for code in ['99213', '99214', '99215']:
        pct_col = f'{code}_pct'
        if pct_col in row and pd.notna(row[pct_col]):
            em_dist[code] = round(float(row[pct_col]), 1)
    
    if not em_dist:
        return None
    
    # Calculate gaps vs. benchmark
    benchmark = EM_BENCHMARKS['default']
    gaps = []
    total_gap_value = 0
    
    for code, current_pct in em_dist.items():
        if code in benchmark:
            benchmark_pct = benchmark[code]
            gap_pct = current_pct - benchmark_pct
            
            # Calculate revenue opportunity for this gap
            # Assume average reimbursement: 99213=$75, 99214=$110, 99215=$150
            code_values = {'99213': 75, '99214': 110, '99215': 150}
            
            if code in code_values and abs(gap_pct) > 5:  # Only show significant gaps
                # If underutilizing higher-value codes, that's an opportunity
                if code in ['99214', '99215'] and gap_pct < 0:
                    opportunity = abs(gap_pct) / 100 * total_em * code_values[code]
                    total_gap_value += opportunity
                    
                    gaps.append({
                        "code": code,
                        "current": current_pct,
                        "benchmark": benchmark_pct,
                        "gap": round(gap_pct, 1),
                        "opportunity": round(opportunity)
                    })
    
    # Build smoking gun for billing
    smoking_gun = None
    if gaps:
        top_gap = max(gaps, key=lambda x: abs(x['gap']))
        if top_gap['code'] == '99214':
            smoking_gun = f"Underutilizing Level 4 codes by {abs(top_gap['gap']):.0f} percentage points"
        elif top_gap['code'] == '99215':
            smoking_gun = f"Underutilizing Level 5 codes by {abs(top_gap['gap']):.0f} percentage points"
    
    return {
        "total_em_codes": round(total_em),
        "em_distribution": em_dist,
        "specialty_benchmark": benchmark,
        "gaps": gaps if gaps else [],
        "total_opportunity": round(total_gap_value) if total_gap_value > 0 else 0,
        "source": "Medicare Claims 2023",
        "confidence": "verified",
        "smoking_gun": smoking_gun
    }

def build_volume_evidence(row):
    """Build volume and scale evidence"""
    
    volume = float(row.get('metric_used_volume', 0))
    volume_source = str(row.get('volume_source', 'proxy'))
    npi_count = int(row.get('npi_count', 1))
    site_count = int(row.get('site_count', 1))
    
    # Calculate volume per provider
    vol_per_provider = volume / npi_count if npi_count > 0 else 0
    
    return {
        "annual_encounters": round(volume),
        "source": "HRSA UDS" if volume_source == "real" else "Estimated (Proxy)",
        "confidence": "verified" if volume_source == "real" else "estimated",
        "providers": npi_count,
        "sites": site_count,
        "encounters_per_provider": round(vol_per_provider),
        "context": get_volume_context(volume, vol_per_provider, npi_count),
        "smoking_gun": f"{volume/1000:.0f}k encounters across {npi_count} providers" if volume > 10000 else None
    }

def get_volume_context(volume, vol_per_provider, npi_count):
    """Provide context for volume numbers"""
    if vol_per_provider > 4000:
        return f"High burnout risk: {vol_per_provider:.0f} encounters/provider (industry avg: 2,500)"
    elif volume > 25000:
        return f"Top 10% volume for clinic size"
    elif npi_count > 15:
        return f"Large multi-provider practice ({npi_count} providers)"
    else:
        return "Standard volume"

def build_clinic_profile(row):
    """Build comprehensive clinic profile"""
    
    segment = str(row.get('segment_label', ''))
    npi_count = int(row.get('npi_count', 1))
    site_count = int(row.get('site_count', 1))
    taxonomy = str(row.get('taxonomy', ''))
    
    return {
        "segment": segment,
        "provider_count": npi_count,
        "site_count": site_count,
        "specialty": taxonomy,
        "organization_type": get_org_type(segment, npi_count, site_count),
        "context": get_profile_context(segment, npi_count, site_count)
    }

def get_org_type(segment, npi_count, site_count):
    """Determine organization type"""
    if 'SEGMENT B' in segment.upper():
        return f"Multi-site FQHC" if site_count > 1 else "Single-site FQHC"
    elif npi_count > 15:
        return "Large Group Practice"
    elif npi_count > 5:
        return "Medium Group Practice"
    elif site_count > 1:
        return "Multi-location Practice"
    else:
        return "Solo/Small Practice"

def get_profile_context(segment, npi_count, site_count):
    """Provide context for clinic profile"""
    if 'SEGMENT B' in segment.upper():
        return f"FQHC with {npi_count} providers across {site_count} sites"
    elif npi_count > 15:
        return f"Large practice with {npi_count} providers - likely complex RCM needs"
    else:
        return f"{npi_count} provider practice"

def build_behavioral_evidence(row):
    """Build behavioral health specific evidence"""
    
    psych_codes = float(row.get('total_psych_codes', 0))
    psych_risk = float(row.get('psych_risk_ratio', 0))
    
    if psych_codes < 100:
        return None  # Not a behavioral clinic
    
    return {
        "annual_sessions": round(psych_codes),
        "audit_risk_ratio": round(psych_risk, 2),
        "risk_level": get_psych_risk_level(psych_risk),
        "source": "Medicare Claims 2023",
        "confidence": "verified",
        "context": get_psych_context(psych_codes, psych_risk),
        "smoking_gun": f"{psych_risk:.1f}x overcoding ratio - audit risk" if psych_risk > 1.5 else None
    }

def get_psych_risk_level(ratio):
    """Categorize psych audit risk"""
    if ratio > 2.0:
        return "Critical"
    elif ratio > 1.5:
        return "High"
    elif ratio > 1.2:
        return "Moderate"
    else:
        return "Low"

def get_psych_context(codes, ratio):
    """Provide context for psych metrics"""
    if ratio > 1.5:
        return f"{codes:.0f} sessions/year with {ratio:.1f}x overcoding ratio suggests 90837 overuse - high audit risk"
    else:
        return f"{codes:.0f} behavioral health sessions annually"

def build_fqhc_evidence(row):
    """Build FQHC-specific evidence"""
    
    segment = str(row.get('segment_label', '')).upper()
    if 'SEGMENT B' not in segment:
        return None
    
    fqhc_revenue = float(row.get('fqhc_revenue', 0))
    fqhc_margin = float(row.get('fqhc_margin', 0))
    volume = float(row.get('metric_used_volume', 0))
    
    return {
        "annual_revenue": round(fqhc_revenue) if fqhc_revenue > 0 else None,
        "net_margin": round(fqhc_margin * 100, 1) if fqhc_margin else None,
        "uds_encounters": round(volume) if row.get('volume_source') == 'real' else None,
        "source": "HRSA Cost Reports & UDS",
        "confidence": "verified" if fqhc_revenue > 0 else "estimated",
        "context": get_fqhc_context(fqhc_margin, volume),
        "smoking_gun": f"{volume/1000:.0f}k UDS encounters - high grant funding" if volume > 20000 else None
    }

def get_fqhc_context(margin, volume):
    """Provide context for FQHC metrics"""
    if margin and margin < 0.03:
        return "Low margin - financial pressure despite grant funding"
    elif volume > 25000:
        return "High-volume FQHC - likely overwhelmed staff"
    else:
        return "Standard FQHC operations"

def build_risk_signals(row):
    """Build risk and compliance signals"""
    
    oig_flag = row.get('oig_leie_flag', False)
    psych_risk = float(row.get('psych_risk_ratio', 0))
    
    risks = []
    
    if oig_flag:
        risks.append({
            "type": "oig_exclusion",
            "severity": "high",
            "detail": "Provider on OIG exclusion list",
            "source": "OIG LEIE Database"
        })
    
    if psych_risk > 1.5:
        risks.append({
            "type": "audit_risk",
            "severity": "high" if psych_risk > 2.0 else "moderate",
            "detail": f"Psychotherapy overcoding ratio: {psych_risk:.1f}x",
            "source": "Medicare Claims 2023"
        })
    
    return risks if risks else []

def main():
    print("🔍 BUILDING EVIDENCE-BASED GTM INTELLIGENCE...")
    
    # Load data
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    print(f"Loaded {len(df):,} clinics")
    
    # EXPANDED FILTERING: Include ALL clinics with verified signals
    # Don't rely on tier - look for actual evidence
    
    conditions = (
        # Verified undercoding
        (df['undercoding_ratio'] > 0.15) |
        # High psych volume with risk
        ((df['total_psych_codes'] > 500) & (df['psych_risk_ratio'] > 1.3)) |
        # High-volume FQHC
        ((df['segment_label'].str.contains('Segment B', na=False)) & (df['metric_used_volume'] > 15000)) |
        # Tier 1 & 2 (keep existing top tier)
        (df['icp_tier'].isin(['Tier 1', 'Tier 2']))
    )
    
    top_clinics = df[conditions].copy()
    print(f"Processing {len(top_clinics)} high-value clinics")
    print(f"  - Verified undercoding: {len(df[df['undercoding_ratio'] > 0.15])}")
    print(f"  - Behavioral risk: {len(df[(df['total_psych_codes'] > 500) & (df['psych_risk_ratio'] > 1.3)])}")
    print(f"  - High-volume FQHC: {len(df[(df['segment_label'].str.contains('Segment B', na=False)) & (df['metric_used_volume'] > 15000)])}")
    
    # Build evidence objects
    evidence_objects = []
    for idx, row in top_clinics.iterrows():
        try:
            evidence = build_evidence_object(row)
            evidence_objects.append(evidence)
        except Exception as e:
            print(f"Error processing clinic {row.get('clinic_id')}: {e}")
            continue
    
    # Save to JSON
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(evidence_objects, f, indent=2)
    
    print(f"\n✅ Saved {len(evidence_objects)} evidence objects to {OUTPUT_FILE}")
    
    # Print smoking gun distribution
    from collections import Counter
    smoking_guns = Counter([e['smoking_gun']['type'] for e in evidence_objects])
    print("\n📊 SMOKING GUN DISTRIBUTION:")
    for gun_type, count in smoking_guns.most_common():
        print(f"  {gun_type}: {count}")
    
    # Print sample of each type
    print("\n📋 SAMPLE EVIDENCE OBJECTS:")
    for gun_type in smoking_guns.keys():
        sample = next((e for e in evidence_objects if e['smoking_gun']['type'] == gun_type), None)
        if sample:
            print(f"\n{gun_type.upper()}:")
            print(f"  {sample['name']} ({sample['track']})")
            print(f"  {sample['smoking_gun']['headline']}")
            print(f"  {sample['smoking_gun']['detail']}")

if __name__ == "__main__":
    main()
