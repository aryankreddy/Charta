import pandas as pd

# Check enriched file
print("Checking enriched file...")
df = pd.read_csv('data/curated/clinics_enriched_scored.csv', low_memory=False, nrows=100000)
print(f"Loaded {len(df)} rows")

psych_cols = [c for c in df.columns if 'psych' in c.lower()]
print(f"\nPsych-related columns: {psych_cols}")

if 'total_psych_codes' in df.columns:
    psych = df[df['total_psych_codes'] > 0]
    print(f"\nClinics with psych codes: {len(psych)}")
    if len(psych) > 0:
        print(f"Max psych_risk_ratio: {psych['psych_risk_ratio'].max()}")
        print("\nTop 3:")
        print(psych.nlargest(3, 'psych_risk_ratio')[['org_name', 'total_psych_codes', 'psych_risk_ratio']])
else:
    print("\nNo total_psych_codes column found!")
