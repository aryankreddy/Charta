"""
SCORING READINESS ASSESSMENT
Analyzes the enriched dataset to determine if we have sufficient data
to execute the proposed ICP scoring framework.
"""

import pandas as pd
import numpy as np
import os

# Paths
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_CURATED = os.path.join(ROOT, "data", "curated")
ENRICHED_FILE = os.path.join(DATA_CURATED, "clinics_enriched_scored.csv")

def assess_data_availability():
    """Assess availability of data for each scoring component."""
    
    print("="*80)
    print(" SCORING READINESS ASSESSMENT")
    print("="*80)
    
    # Load data
    print(f"\nLoading: {ENRICHED_FILE}")
    df = pd.read_csv(ENRICHED_FILE, low_memory=False)
    total = len(df)
    print(f"Total records: {total:,}\n")
    
    # Define scoring components and required fields
    components = {
        "1. ECONOMIC PAIN (40 pts)": {
            "Margin Pressure (15 pts)": {
                "required_fields": ["fqhc_margin", "hosp_margin", "hha_margin"],
                "fallback_fields": ["taxonomy_desc", "segment_label"],
                "logic": "Net margin from cost reports; fallback to segment average"
            },
            "Volume Leverage (12 pts)": {
                "required_fields": ["real_annual_encounters"],
                "fallback_fields": ["final_volume"],
                "logic": "Real patient encounters from utilization data"
            },
            "Revenue Leakage (13 pts)": {
                "required_fields": ["undercoding_ratio"],
                "fallback_fields": [],
                "logic": "CPT code complexity ratio from claims analysis"
            }
        },
        "2. PRODUCT-MARKET FIT (35 pts)": {
            "Practice Alignment (12 pts)": {
                "required_fields": ["taxonomy_desc", "segment_label"],
                "fallback_fields": [],
                "logic": "Taxonomy classification and segment assignment"
            },
            "Complexity Score (10 pts)": {
                "required_fields": ["medicaid_pct", "site_count"],
                "fallback_fields": ["npi_count"],
                "logic": "Medicaid percentage + multi-site indicator"
            },
            "Tech Readiness (8 pts)": {
                "required_fields": ["is_aco_participant", "npi_count"],
                "fallback_fields": [],
                "logic": "ACO participation + provider count"
            },
            "Compliance Risk (5 pts)": {
                "required_fields": ["risk_compliance_flag", "oig_leie_flag"],
                "fallback_fields": ["segment_label"],
                "logic": "OIG exclusion match + high-audit segment"
            }
        },
        "3. STRATEGIC VALUE (25 pts)": {
            "Deal Size (10 pts)": {
                "required_fields": ["fqhc_revenue", "hosp_revenue", "hha_revenue"],
                "fallback_fields": ["final_revenue", "real_medicare_revenue"],
                "logic": "Total revenue from cost reports or claims"
            },
            "Expansion Potential (7 pts)": {
                "required_fields": ["site_count"],
                "fallback_fields": ["npi_count"],
                "logic": "Number of sites/locations"
            },
            "Reference Value (8 pts)": {
                "required_fields": ["is_aco_participant", "real_annual_encounters"],
                "fallback_fields": ["final_volume"],
                "logic": "ACO participation + volume ranking"
            }
        }
    }
    
    # Assess each component
    results = {}
    
    for category, subcomponents in components.items():
        print(f"\n{category}")
        print("-" * 80)
        
        for component, details in subcomponents.items():
            # Check required fields
            required_available = []
            for field in details["required_fields"]:
                if field in df.columns:
                    count = df[field].notnull().sum()
                    pct = count / total * 100
                    required_available.append({
                        'field': field,
                        'count': count,
                        'pct': pct
                    })
            
            # Check fallback fields
            fallback_available = []
            for field in details["fallback_fields"]:
                if field in df.columns:
                    count = df[field].notnull().sum()
                    pct = count / total * 100
                    fallback_available.append({
                        'field': field,
                        'count': count,
                        'pct': pct
                    })
            
            # Determine status
            max_coverage = 0
            if required_available:
                max_coverage = max([x['pct'] for x in required_available])
            if fallback_available:
                max_coverage = max(max_coverage, max([x['pct'] for x in fallback_available]))
            
            if max_coverage >= 50:
                status = "✅ READY"
            elif max_coverage >= 10:
                status = "⚠️  LIMITED"
            else:
                status = "❌ MISSING"
            
            print(f"\n{component}")
            print(f"  Status: {status}")
            print(f"  Logic: {details['logic']}")
            
            if required_available:
                print(f"  Primary Data:")
                for item in required_available:
                    print(f"    • {item['field']}: {item['count']:,} ({item['pct']:.1f}%)")
            
            if fallback_available:
                print(f"  Fallback Data:")
                for item in fallback_available:
                    print(f"    • {item['field']}: {item['count']:,} ({item['pct']:.1f}%)")
            
            # Store results
            results[component] = {
                'status': status,
                'max_coverage': max_coverage,
                'required': required_available,
                'fallback': fallback_available
            }
    
    # Overall assessment
    print("\n" + "="*80)
    print(" OVERALL ASSESSMENT")
    print("="*80)
    
    ready_count = sum(1 for r in results.values() if "READY" in r['status'])
    limited_count = sum(1 for r in results.values() if "LIMITED" in r['status'])
    missing_count = sum(1 for r in results.values() if "MISSING" in r['status'])
    
    print(f"\n✅ Ready Components: {ready_count}/{len(results)}")
    print(f"⚠️  Limited Components: {limited_count}/{len(results)}")
    print(f"❌ Missing Components: {missing_count}/{len(results)}")
    
    # Recommendations
    print("\n" + "="*80)
    print(" RECOMMENDATIONS")
    print("="*80)
    
    if ready_count >= 7:
        print("\n🟢 PROCEED WITH SCORING")
        print("   We have sufficient data to execute the ICP scoring framework.")
        print("   Use fallback logic for limited components.")
    elif ready_count >= 5:
        print("\n🟡 PROCEED WITH CAUTION")
        print("   We have moderate data coverage. Scoring is possible but will rely")
        print("   heavily on fallback logic and estimations.")
    else:
        print("\n🔴 NOT READY")
        print("   Insufficient data coverage. Need to integrate additional sources")
        print("   before executing scoring framework.")
    
    # Specific gaps
    print("\n" + "="*80)
    print(" KEY GAPS & SOLUTIONS")
    print("="*80)
    
    gaps = []
    
    # Check specific critical fields
    if 'medicaid_pct' not in df.columns or df.get('medicaid_pct', pd.Series()).notnull().sum() < total * 0.01:
        gaps.append({
            'gap': 'Medicaid Percentage',
            'impact': 'Cannot score Complexity component accurately',
            'solution': 'Extract from cost reports or use state-level averages by taxonomy'
        })
    
    if 'site_count' not in df.columns or df.get('site_count', pd.Series()).notnull().sum() < total * 0.01:
        gaps.append({
            'gap': 'Site Count',
            'impact': 'Cannot score Expansion Potential',
            'solution': 'Derive from PECOS enrollment data or use npi_count as proxy'
        })
    
    margin_fields = ['fqhc_margin', 'hosp_margin', 'hha_margin']
    margin_coverage = sum(df.get(f, pd.Series()).notnull().sum() for f in margin_fields if f in df.columns)
    if margin_coverage < total * 0.01:
        gaps.append({
            'gap': 'Net Margin Data',
            'impact': 'Cannot accurately score Economic Pain (Margin Pressure)',
            'solution': 'Use segment-level average margins from cost report benchmarks'
        })
    
    if gaps:
        for i, gap in enumerate(gaps, 1):
            print(f"\n{i}. {gap['gap']}")
            print(f"   Impact: {gap['impact']}")
            print(f"   Solution: {gap['solution']}")
    else:
        print("\n✅ No critical gaps identified!")
    
    # Sample scoring preview
    print("\n" + "="*80)
    print(" SAMPLE SCORING PREVIEW")
    print("="*80)
    
    # Find a record with good data coverage
    sample_idx = None
    for idx in range(min(1000, len(df))):
        row = df.iloc[idx]
        if (row.get('undercoding_ratio', 0) > 0 and 
            row.get('real_annual_encounters', 0) > 0):
            sample_idx = idx
            break
    
    if sample_idx is not None:
        sample = df.iloc[sample_idx]
        print(f"\nSample Clinic: {sample.get('org_name', 'Unknown')}")
        print(f"NPI: {sample.get('npi', 'N/A')}")
        print(f"\nAvailable Data:")
        print(f"  • Undercoding Ratio: {sample.get('undercoding_ratio', 'N/A')}")
        print(f"  • Annual Encounters: {sample.get('real_annual_encounters', 'N/A'):,.0f}" if pd.notnull(sample.get('real_annual_encounters')) else "  • Annual Encounters: N/A")
        print(f"  • Segment: {sample.get('segment_label', 'N/A')}")
        print(f"  • ACO Participant: {sample.get('is_aco_participant', 'N/A')}")
        print(f"  • OIG Flag: {sample.get('oig_leie_flag', 'N/A')}")
    
    print("\n" + "="*80)
    print(" CONCLUSION")
    print("="*80)
    
    if ready_count >= 7:
        print("\n✅ READY TO PROCEED")
        print("   The proposed ICP scoring framework can be implemented with the")
        print("   current dataset. Use fallback logic and segment averages for")
        print("   missing data points.")
        print("\n   Next Step: Implement workers/score_icp.py with the defined logic.")
    else:
        print("\n⚠️  PROCEED WITH MODIFICATIONS")
        print("   The scoring framework needs to be adjusted to work with available")
        print("   data. Focus on components with >50% coverage and use proxy metrics")
        print("   for missing fields.")

if __name__ == "__main__":
    assess_data_availability()
