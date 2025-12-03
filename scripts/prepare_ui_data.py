"""
PREPARE UI DATA
Converts the scored CSV into a lightweight JSON for the frontend.
Optimized for the "Clinical Minimalism" design.
"""

import pandas as pd
import json
import os

# Paths
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_FILE = os.path.join(ROOT, "data", "curated", "clinics_scored_final.csv")
OUTPUT_FILE = os.path.join(ROOT, "web", "public", "data", "clinics.json")

def format_currency(val):
    if pd.isna(val) or val == 0: return "N/A"
    if val >= 1_000_000: return f"${val/1_000_000:.1f}M"
    if val >= 1_000: return f"${val/1_000:.0f}k"
    return f"${val:.0f}"

def format_number(val):
    if pd.isna(val) or val == 0: return "N/A"
    return f"{val:,.0f}"

def get_drivers(row):
    drivers = []
    
    # Parse the drivers string from scoring engine
    raw_drivers = str(row.get('scoring_drivers', ''))
    if raw_drivers and raw_drivers != 'nan':
        parts = raw_drivers.split(' | ')
        for p in parts:
            color = "text-gray-600"
            if "Undercoding" in p: color = "text-red-600"
            elif "Margin" in p: color = "text-orange-600"
            elif "Volume" in p: color = "text-blue-600"
            elif "ACO" in p: color = "text-green-600"
            
            # Extract score value if present (e.g. "Severe Undercoding (0.25)")
            # We want to map this to points if possible, or just show the label
            label = p.split('(')[0].strip()
            
            drivers.append({
                "label": label,
                "value": "High", # Simplified for UI
                "color": color
            })
            
    return drivers[:3] # Limit to top 3

def prepare_data():
    print("🚀 PREPARING UI DATA...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file missing: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE, low_memory=False)
    print(f"Loaded {len(df):,} clinics.")
    
    # Filter for UI (Top 2000 for performance prototype)
    # In production, this would be an API. For now, static JSON.
    top_clinics = df.sort_values('icp_score', ascending=False).head(2000)
    
    output_data = []
    
    for _, row in top_clinics.iterrows():
        
        # Determine Segment Label
        seg = str(row.get('segment_label', 'Unknown'))
        if ' - ' in seg: seg = seg.split(' - ')[0]
        
        # Fit Reason Logic
        fit_reason = "Strong operational fit."
        if row['icp_score'] > 70:
            fit_reason = "High-priority target. "
            if row.get('score_pain_undercoding', 0) > 10:
                fit_reason += "Severe undercoding indicates immediate revenue opportunity. "
            if row.get('score_pain_margin', 0) > 5:
                fit_reason += "Margin pressure creates urgency. "
            if row.get('score_fit_align', 0) > 10:
                fit_reason += "Perfect strategic alignment with core ICP."
        
        clinic = {
            "id": str(row.get('npi', '')),
            "name": str(row.get('org_name', 'Unknown Clinic')).title(),
            "tier": str(row.get('icp_tier', 'Tier 4')),
            "score": int(row.get('icp_score', 0)),
            "segment": seg,
            "state": str(row.get('state_code', 'Unknown')),
            "revenue": format_currency(row.get('metric_est_revenue', 0)),
            "volume": format_number(row.get('metric_used_volume', 0)),
            "drivers": get_drivers(row),
            "contact": {
                "phone": str(row.get('phone', 'N/A')),
                "email": "N/A", # Placeholder
                "address": f"{str(row.get('city', '')).title()}, {str(row.get('state_code', ''))}"
            },
            "fit_reason": fit_reason
        }
        output_data.append(clinic)
        
    # Ensure directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    print(f"✅ Saved {len(output_data):,} clinics to {OUTPUT_FILE}")

if __name__ == "__main__":
    prepare_data()
