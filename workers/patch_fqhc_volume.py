"""
FQHC VOLUME PATCH
Author: Charta Health GTM Data Engineering

Purpose: Impute missing volume for FQHCs (Segment B) using provider count proxy.
Logic: If real volume is missing or low (<100), Proxy = NPI Count * 3,200 (Industry Avg).
"""

import pandas as pd
import numpy as np
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_FILE = os.path.join(ROOT, "data", "curated", "clinics_enriched_scored.csv")
OUTPUT_FILE = os.path.join(ROOT, "data", "curated", "clinics_enriched_scored.csv") # Overwrite

def patch_fqhc_volume():
    print("🚑 RUNNING FQHC VOLUME PATCH...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE, low_memory=False)
    print(f"   Loaded {len(df):,} clinics.")
    
    # Filter for Segment B (FQHCs)
    # Check for "Segment B" OR "FQHC" in segment_label
    fqhc_mask = df['segment_label'].astype(str).str.contains('Segment B|FQHC', case=False, na=False)
    fqhcs = df[fqhc_mask].copy()
    
    print(f"   Found {len(fqhcs):,} FQHCs.")
    
    # Ensure numeric columns
    cols = ['final_volume', 'npi_count', 'real_annual_encounters']
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
    # Logic: If real_annual_encounters is 0, null, or < 100
    # Note: We patch 'final_volume' which is used for scoring
    
    # Check if real_annual_encounters exists, if not use final_volume as proxy for check
    vol_check_col = 'real_annual_encounters' if 'real_annual_encounters' in df.columns else 'final_volume'
    
    patch_mask = fqhc_mask & (df[vol_check_col] < 100)
    to_patch = df[patch_mask]
    
    print(f"   Identified {len(to_patch):,} FQHCs with missing/low volume (<100).")
    
    if len(to_patch) == 0:
        print("   ✅ No FQHCs need patching.")
        return

    # Calculate Proxy
    # Proxy = NPI Count * 3200
    # If NPI Count is 0, default to 1 * 3200 = 3200
    
    def calculate_proxy(row):
        npi_cnt = row.get('npi_count', 0)
        if npi_cnt <= 0: npi_cnt = 1
        return npi_cnt * 3200

    proxies = df.loc[patch_mask].apply(calculate_proxy, axis=1)
    
    # Apply Patch
    df.loc[patch_mask, 'final_volume'] = proxies
    df.loc[patch_mask, 'volume_source'] = 'Imputed (NPI Proxy)'
    
    # Set data_confidence to 50 (Medium)
    # Check if data_confidence exists and its type
    if 'data_confidence' in df.columns:
        # If it's numeric, set to 50. If string, set to 'Medium'.
        # The scoring script usually outputs numeric 0-100.
        # But let's be safe.
        df.loc[patch_mask, 'data_confidence'] = 50
    else:
        df.loc[patch_mask, 'data_confidence'] = 50

    # Add "Imputed Volume" to scoring_drivers (or create it)
    # We'll append it to 'scoring_drivers' if it exists, or create 'data_notes'
    # User suggested 'data_notes' or 'scoring_drivers'. 
    # Let's use 'scoring_drivers' so it shows up in UI, but scoring script might overwrite it.
    # Actually, scoring script RE-CALCULATES scoring_drivers.
    # So patching scoring_drivers here is useless if we run score_icp.py right after.
    # Instead, let's add a column 'is_imputed_volume' that score_icp.py COULD use, 
    # OR just rely on the fact that volume is now high.
    # The user instruction says: "ADD 'Imputed Volume' to a new column 'data_notes' (or append to scoring_drivers if easier) so we know which ones were patched."
    # Since we re-score immediately, let's use 'data_notes' to persist the info.
    
    if 'data_notes' not in df.columns:
        df['data_notes'] = ""
    
    # Append "Imputed Volume"
    # We need to handle existing text
    df.loc[patch_mask, 'data_notes'] = df.loc[patch_mask, 'data_notes'].apply(
        lambda x: str(x) + " | Imputed Volume" if pd.notnull(x) and str(x) != "" else "Imputed Volume"
    )

    print(f"   ✅ Patched {len(to_patch):,} FQHCs with proxy volume.")
    print(f"      Avg Proxy Volume: {proxies.mean():,.0f}")
    
    # Save
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"   💾 Saved patched data to {OUTPUT_FILE}")
    
    # Re-trigger Scoring
    print("\n🔄 RE-TRIGGERING SCORING ENGINE...")
    import workers.score_icp
    workers.score_icp.main()
    
    # Re-trigger Frontend Update
    print("\n🔄 RE-TRIGGERING FRONTEND UPDATE...")
    import scripts.update_frontend_data
    scripts.update_frontend_data.generate_json()

if __name__ == "__main__":
    patch_fqhc_volume()
