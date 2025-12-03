import pandas as pd
import os

# Configuration
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_FILE = os.path.join(ROOT, "data", "curated", "clinics_scored_final.csv")
EXPORT_DIR = os.path.join(ROOT, "data", "exports")

def main():
    print("🚀 GENERATING SALES EXPORTS...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file missing: {INPUT_FILE}")
        return
        
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
        
    print(f"   Loading {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    
    # Ensure numeric columns
    cols = ['undercoding_ratio', 'psych_risk_ratio', 'services_count', 'final_volume']
    for c in cols:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce')
    
    # 1. Tier 1 FQHC Track (Verified Undercoding)
    print("   Generating Tier 1 FQHC Track...")
    t1_fqhc = df[
        (df['icp_tier'] == 'Tier 1') & 
        (df['segment_label'].str.contains('Segment B', na=False)) &
        (df['undercoding_ratio'].notnull())
    ].copy()
    t1_fqhc.to_csv(os.path.join(EXPORT_DIR, "tier1_fqhc_track.csv"), index=False)
    print(f"   ✅ Saved {len(t1_fqhc):,} records to tier1_fqhc_track.csv")
    
    # 2. Tier 1 Behavioral Track (Psych Risk)
    print("   Generating Tier 1 Behavioral Track...")
    t1_psych = df[
        (df['scoring_track'] == 'BEHAVIORAL') & 
        (df['icp_tier'] == 'Tier 1')
    ].copy()
    t1_psych.to_csv(os.path.join(EXPORT_DIR, "tier1_behavioral_track.csv"), index=False)
    print(f"   ✅ Saved {len(t1_psych):,} records to tier1_behavioral_track.csv")
    
    # 3. Tier 2 High Volume Primary Care
    print("   Generating Tier 2 High Volume Primary...")
    t2_vol = df[
        (df['icp_tier'] == 'Tier 2') & 
        (df['scoring_track'] == 'AMBULATORY') &
        (df['final_volume'] > 50000)
    ].copy()
    t2_vol.to_csv(os.path.join(EXPORT_DIR, "tier2_high_volume_primary.csv"), index=False)
    print(f"   ✅ Saved {len(t2_vol):,} records to tier2_high_volume_primary.csv")
    
    # 4. Tier 2 FQHC Expansion (High Volume, No Undercoding Data)
    print("   Generating Tier 2 FQHC Expansion...")
    t2_fqhc = df[
        (df['icp_tier'] == 'Tier 2') & 
        (df['segment_label'].str.contains('Segment B', na=False)) &
        (df['final_volume'] > 20000)
    ].copy()
    t2_fqhc.to_csv(os.path.join(EXPORT_DIR, "tier2_fqhc_expansion.csv"), index=False)
    print(f"   ✅ Saved {len(t2_fqhc):,} records to tier2_fqhc_expansion.csv")
    
    print("\n🎉 All exports generated successfully!")

if __name__ == "__main__":
    main()
