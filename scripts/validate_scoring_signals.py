"""
Data Validation Script for Scoring Signals

This script performs several checks to validate the integrity of the
scoring logic, specifically around E&M and Therapy coding patterns.

Check A: The "E&M Bell Curve"
- Picks 3 "Green" (low pain) clinics and checks their E&M code distribution.
- Expectation: Level 4 should be a significant portion of E&M claims.

Check B: The "Therapy Cliff"
- Picks 3 "Red" (high therapy pain) clinics and checks their therapy code usage.
- Expectation: A heavy skew towards 90834 over 90837, or zero 90837.

Check C: The "Zero Check"
- Finds clinics with high therapy pain scores but very low therapy claim volume.
- Expectation: Should find few or no such clinics, validating the "Relevance Gate".
"""
import pandas as pd
import os

# --- Configuration ---
SCORED_FILE = "data/curated/clinics_scored_final.csv"
UNDERCODING_METRICS_FILE = "data/curated/staging/stg_undercoding_metrics.csv"
PSYCH_METRICS_FILE = "data/curated/staging/stg_psych_metrics.csv"

def print_header(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def check_a_em_bell_curve(df, undercoding_df):
    """Picks 3 'Green' clinics with E&M data and checks their code distribution."""
    print_header("Check A: The E&M Bell Curve")
    
    # Ensure there's data to sample from
    green_clinics_with_data = df[(df['score_pain_total'] < 15) & (df['total_eval_codes'] > 100)]
    if green_clinics_with_data.empty:
        print("No 'Green' clinics with sufficient E&M codes (>100) found to test.")
        return

    green_clinics = green_clinics_with_data.sample(min(3, len(green_clinics_with_data)))

    for _, clinic in green_clinics.iterrows():
        npi = str(clinic['npi'])
        name = clinic['org_name']
        print(f"\n--- Analyzing Green Clinic: {name} (NPI: {npi}) ---")
        
        # NPIs in CSVs might be float, ensure string comparison
        clinic_metrics = undercoding_df[undercoding_df['npi'].astype(str).str.startswith(npi)]
        
        if clinic_metrics.empty:
            print("No undercoding metrics found for this NPI.")
            continue
            
        total_em_services = clinic_metrics['total_eval_codes'].iloc[0]
        level4_5_services = clinic_metrics['count_level_4_5'].iloc[0]

        if total_em_services > 0:
            level4_5_ratio = level4_5_services / total_em_services
            print(f"Level 4+5 E&M Ratio: {level4_5_ratio:.2%}")
            # "Green" clinics should be close to or better than the 45% national average
            if level4_5_ratio >= 0.40:
                print(f"✅ Verified: Ratio ({level4_5_ratio:.1%}) is strong, as expected for a 'Green' clinic.")
            else:
                print(f"⚠️ Observation: Ratio is lower than expected for a 'Green' clinic.")
        else:
            print("No E&M services found to calculate ratio.")

def check_b_therapy_cliff(df, psych_df):
    """Picks 3 'Red' clinics with psych data and checks their therapy code usage."""
    print_header("Check B: The Therapy Cliff")

    # Ensure there's data to sample from
    red_clinics_with_data = df[(df['score_pain_total'] > 30) & 
                               (df['pain_label'].str.contains("Therapy", na=False)) & 
                               (df['total_psych_codes'] > 100)]
    if red_clinics_with_data.empty:
        print("No 'Red' therapy-pain clinics with sufficient psych codes (>100) found to test.")
        return

    red_clinics = red_clinics_with_data.sample(min(3, len(red_clinics_with_data)))

    for _, clinic in red_clinics.iterrows():
        npi = str(clinic['npi'])
        name = clinic['org_name']
        print(f"\n--- Analyzing Red Clinic: {name} (NPI: {npi}) ---")

        clinic_metrics = psych_df[psych_df['npi'].astype(str).str.startswith(npi)]
        
        if clinic_metrics.empty:
            print(f"No psych metrics found for this NPI ({npi}).")
            continue
            
        high_code_services = clinic_metrics['90837'].iloc[0]
        mid_code_services = clinic_metrics['90834'].iloc[0]
        
        total_therapy_services = high_code_services + mid_code_services

        if total_therapy_services > 0:
            high_code_ratio = high_code_services / total_therapy_services
            print(f"High-Complexity (90837) Ratio: {high_code_ratio:.2%}")
            if high_code_ratio < 0.2:
                print("✅ Verified: Clear evidence of 'Therapy Cliff' (low 90837 usage).")
            elif high_code_ratio > 0.8:
                print("✅ Verified: Clear evidence of 'Audit Risk Spike' (high 90837 usage).")
            else:
                print("⚠️ Observation: Clinic has a moderate portion of high-complexity therapy codes.")
        else:
            print("No relevant therapy services (90834, 90837) found to calculate ratio.")

def check_c_zero_check(df):
    """Finds clinics with high therapy pain but low therapy claim volume."""
    print_header("Check C: The 'Zero' Check (Therapy Relevance Gate Validation)")
    
    high_pain_low_volume = df[
        (df['scoring_track'] == 'AMBULATORY') &
        (df['score_pain_total'] > 30) &
        (df['pain_label'].str.contains("Therapy", na=False)) &
        (df['total_psych_codes'] < 100)
    ]
    
    count = len(high_pain_low_volume)
    
    if count == 0:
        print("✅ Verified: The 'Therapy Relevance Gate' appears to be working correctly.")
    else:
        print(f"❌ Bug Alert: Found {count} clinics with high therapy pain despite low volume.")
        print("These clinics should have had their therapy pain score gated to 0.")
        print("Sample of problematic clinics:")
        print(high_pain_low_volume[['org_name', 'npi', 'score_pain_total', 'pain_label', 'total_psych_codes']].head())

def main():
    """Run all validation checks."""
    if not os.path.exists(SCORED_FILE):
        print(f"❌ Scored file not found at: {SCORED_FILE}")
        return
        
    df = pd.read_csv(SCORED_FILE, low_memory=False, dtype={'npi': str})
    
    undercoding_df = pd.read_csv(UNDERCODING_METRICS_FILE, dtype={'npi': str}) if os.path.exists(UNDERCODING_METRICS_FILE) else pd.DataFrame()
    psych_df = pd.read_csv(PSYCH_METRICS_FILE, dtype={'npi': str}) if os.path.exists(PSYCH_METRICS_FILE) else pd.DataFrame()

    # Run checks
    check_a_em_bell_curve(df, undercoding_df)
    check_b_therapy_cliff(df, psych_df)
    check_c_zero_check(df)

if __name__ == "__main__":
    main()
