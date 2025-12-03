import pandas as pd
import json
import os

INPUT_FILE = "data/curated/verified_organizations.csv"

def diagnose_data():
    print("🚨 DIAGNOSTIC: ANALYZING VERIFIED ORGS DATASET")
    
    if not os.path.exists(INPUT_FILE):
        print("❌ File not found.")
        return

    df = pd.read_csv(INPUT_FILE)
    print(f"📊 Total Rows: {len(df):,}")
    
    # 1. Specialty Distribution
    print("\n--- TOP 20 SPECIALTIES ---")
    print(df['specialty'].value_counts().head(20))
    
    # 2. Clinical Check
    clinical_specs = ['Internal Medicine', 'Family Practice', 'Cardiology', 'General Practice', 'Nurse Practitioner']
    
    print("\n--- CLINICAL SPECIALTY ANALYSIS (Type 2 NPIs) ---")
    for spec in clinical_specs:
        subset = df[df['specialty'].str.contains(spec, case=False, na=False)]
        print(f"\nSpecialty: {spec}")
        print(f"Count: {len(subset)}")
        
        if len(subset) == 0:
            continue
            
        # Check E&M Volume
        has_em = 0
        total_vol = 0
        em_vol = 0
        
        for _, row in subset.iterrows():
            try:
                codes = json.loads(row['billing_codes'])
                # E&M Range: 99202-99215
                row_em = 0
                for c, v in codes.items():
                    if c.isdigit() and 99202 <= int(c) <= 99215:
                        row_em += v
                
                if row_em > 0:
                    has_em += 1
                em_vol += row_em
                total_vol += row['total_claims_volume']
            except:
                pass
                
        print(f"Orgs with >0 E&M Codes: {has_em} ({has_em/len(subset):.1%})")
        print(f"Avg Total Volume: {total_vol/len(subset):.1f}")
        print(f"Avg E&M Volume: {em_vol/len(subset):.1f}")
        
    # 3. Who HAS the E&M codes?
    print("\n--- WHO HAS THE E&M CODES? (Top 10 by E&M Vol) ---")
    
    results = []
    for _, row in df.iterrows():
        try:
            codes = json.loads(row['billing_codes'])
            row_em = 0
            for c, v in codes.items():
                if c.isdigit() and 99202 <= int(c) <= 99215:
                    row_em += v
            if row_em > 0:
                results.append({
                    'name': row['organization_name'],
                    'specialty': row['specialty'],
                    'em_vol': row_em
                })
        except:
            pass
            
    results.sort(key=lambda x: x['em_vol'], reverse=True)
    for r in results[:10]:
        print(f"{r['name']} ({r['specialty']}): {r['em_vol']:,} E&M Codes")

if __name__ == "__main__":
    diagnose_data()
