"""
FORENSIC DATA DIAGNOSIS - ENRICHED FILE
Inspects the ENRICHED file to verify the state of key columns.
"""

import pandas as pd
import os

SEED_FILE = 'data/curated/clinics_seed.csv'
ENRICHED_FILE = 'data/curated/clinics_enriched_scored.csv'

def diagnose_enriched():
    print("="*80)
    print(" COMPARING SEED vs ENRICHED FILES")
    print("="*80)
    
    # Check Seed File
    if os.path.exists(SEED_FILE):
        seed_df = pd.read_csv(SEED_FILE, low_memory=False)
        print(f"\n📄 SEED FILE: {len(seed_df):,} rows, {len(seed_df.columns)} columns")
        print(f"   Columns: {list(seed_df.columns)}")
    else:
        print("\n❌ Seed file not found")
        seed_df = None
    
    # Check Enriched File
    if os.path.exists(ENRICHED_FILE):
        enriched_df = pd.read_csv(ENRICHED_FILE, low_memory=False)
        print(f"\n📄 ENRICHED FILE: {len(enriched_df):,} rows, {len(enriched_df.columns)} columns")
        print(f"   Columns (first 30): {list(enriched_df.columns)[:30]}")
        
        # Check Volume Columns
        vol_cols = [c for c in enriched_df.columns if 'count' in c.lower() or 'vol' in c.lower() or 'encounters' in c.lower() or 'services' in c.lower()]
        print(f"\n{'='*80}")
        print(f" VOLUME COLUMNS IN ENRICHED FILE: {len(vol_cols)}")
        print(f"{'='*80}")
        for c in vol_cols:
            non_null = enriched_df[c].notnull().sum()
            non_zero = (pd.to_numeric(enriched_df[c], errors='coerce').fillna(0) > 0).sum()
            print(f"  {c}: {non_null:,} Non-Null | {non_zero:,} > 0")
        
        # Check Financial Columns
        fin_cols = [c for c in enriched_df.columns if 'rev' in c.lower() or 'margin' in c.lower() or 'income' in c.lower() or 'expense' in c.lower()]
        print(f"\n{'='*80}")
        print(f" FINANCIAL COLUMNS IN ENRICHED FILE: {len(fin_cols)}")
        print(f"{'='*80}")
        for c in fin_cols:
            non_null = enriched_df[c].notnull().sum()
            non_zero = (pd.to_numeric(enriched_df[c], errors='coerce').fillna(0) > 0).sum()
            print(f"  {c}: {non_null:,} Non-Null | {non_zero:,} > 0")
        
        # Check Undercoding
        print(f"\n{'='*80}")
        print(f" UNDERCODING DATA IN ENRICHED FILE")
        print(f"{'='*80}")
        if 'undercoding_ratio' in enriched_df.columns:
            count = enriched_df['undercoding_ratio'].notnull().sum()
            print(f"  ✅ 'undercoding_ratio': {count:,} records")
            if count > 0:
                print(f"     Min: {enriched_df['undercoding_ratio'].min():.3f}")
                print(f"     Max: {enriched_df['undercoding_ratio'].max():.3f}")
                print(f"     Mean: {enriched_df['undercoding_ratio'].mean():.3f}")
        else:
            print("  ❌ 'undercoding_ratio' column MISSING")
        
        # Check Contact Info
        print(f"\n{'='*80}")
        print(f" CONTACT INFORMATION IN ENRICHED FILE")
        print(f"{'='*80}")
        if 'phone' in enriched_df.columns:
            count = enriched_df['phone'].notnull().sum()
            print(f"  ✅ Phone Numbers: {count:,} ({count/len(enriched_df)*100:.1f}%)")
        else:
            print(f"  ❌ Phone column MISSING")
        
        # Summary
        print(f"\n{'='*80}")
        print(f" KEY FINDINGS")
        print(f"{'='*80}")
        
        # Check for real_annual_encounters specifically
        if 'real_annual_encounters' in enriched_df.columns:
            count = enriched_df['real_annual_encounters'].notnull().sum()
            non_zero = (enriched_df['real_annual_encounters'] > 0).sum()
            print(f"  ✅ 'real_annual_encounters': {count:,} Non-Null | {non_zero:,} > 0")
        else:
            print(f"  ❌ 'real_annual_encounters' MISSING")
        
        # Check for final_volume
        if 'final_volume' in enriched_df.columns:
            count = enriched_df['final_volume'].notnull().sum()
            non_zero = (pd.to_numeric(enriched_df['final_volume'], errors='coerce').fillna(0) > 0).sum()
            print(f"  ✅ 'final_volume': {count:,} Non-Null | {non_zero:,} > 0")
        else:
            print(f"  ❌ 'final_volume' MISSING")
        
        # Check for services_count
        if 'services_count' in enriched_df.columns:
            count = enriched_df['services_count'].notnull().sum()
            non_zero = (pd.to_numeric(enriched_df['services_count'], errors='coerce').fillna(0) > 0).sum()
            print(f"  ✅ 'services_count': {count:,} Non-Null | {non_zero:,} > 0")
        else:
            print(f"  ❌ 'services_count' MISSING")
        
    else:
        print("\n❌ Enriched file not found")

if __name__ == "__main__":
    diagnose_enriched()
