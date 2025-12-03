"""
FORENSIC DATA DIAGNOSIS
Inspects the seed file to verify the state of key columns and identify any data loss.
"""

import pandas as pd
import os

FILE_PATH = 'data/curated/clinics_seed.csv'

def diagnose():
    if not os.path.exists(FILE_PATH):
        print("❌ Seed file not found.")
        return

    df = pd.read_csv(FILE_PATH, low_memory=False)
    print(f"Loaded {len(df):,} rows.")
    print(f"\nTotal Columns: {len(df.columns)}")
    print(f"Columns: {list(df.columns)[:20]}...")  # Show first 20
    
    # Check Volume Columns
    vol_cols = [c for c in df.columns if 'count' in c.lower() or 'vol' in c.lower() or 'encounters' in c.lower() or 'services' in c.lower()]
    print(f"\n{'='*80}")
    print(f" VOLUME COLUMNS FOUND: {len(vol_cols)}")
    print(f"{'='*80}")
    for c in vol_cols:
        non_null = df[c].notnull().sum()
        non_zero = (pd.to_numeric(df[c], errors='coerce').fillna(0) > 0).sum()
        print(f"  {c}: {non_null:,} Non-Null | {non_zero:,} > 0")

    # Check Financial Columns
    fin_cols = [c for c in df.columns if 'rev' in c.lower() or 'margin' in c.lower() or 'income' in c.lower() or 'expense' in c.lower()]
    print(f"\n{'='*80}")
    print(f" FINANCIAL COLUMNS FOUND: {len(fin_cols)}")
    print(f"{'='*80}")
    for c in fin_cols:
        non_null = df[c].notnull().sum()
        non_zero = (pd.to_numeric(df[c], errors='coerce').fillna(0) > 0).sum()
        print(f"  {c}: {non_null:,} Non-Null | {non_zero:,} > 0")

    # Check Undercoding
    print(f"\n{'='*80}")
    print(f" UNDERCODING DATA")
    print(f"{'='*80}")
    if 'undercoding_ratio' in df.columns:
        count = df['undercoding_ratio'].notnull().sum()
        print(f"  ✅ 'undercoding_ratio' column FOUND: {count:,} records")
        if count > 0:
            print(f"     Min: {df['undercoding_ratio'].min():.3f}")
            print(f"     Max: {df['undercoding_ratio'].max():.3f}")
            print(f"     Mean: {df['undercoding_ratio'].mean():.3f}")
    else:
        print("  ❌ 'undercoding_ratio' column MISSING.")
    
    if 'total_eval_codes' in df.columns:
        count = df['total_eval_codes'].notnull().sum()
        print(f"  ✅ 'total_eval_codes' column FOUND: {count:,} records")
    
    # Check Strategic Signals
    print(f"\n{'='*80}")
    print(f" STRATEGIC SIGNALS")
    print(f"{'='*80}")
    
    if 'is_aco_participant' in df.columns:
        count = (df['is_aco_participant'] == True).sum()
        print(f"  ✅ ACO Participants: {count:,}")
    
    if 'oig_leie_flag' in df.columns or 'risk_compliance_flag' in df.columns:
        oig_col = 'oig_leie_flag' if 'oig_leie_flag' in df.columns else 'risk_compliance_flag'
        count = df[oig_col].notnull().sum()
        print(f"  ✅ OIG Flags: {count:,}")
    
    # Check Segment Data
    print(f"\n{'='*80}")
    print(f" SEGMENT DATA")
    print(f"{'='*80}")
    
    if 'segment_label' in df.columns:
        print(f"  ✅ Segment Labels:")
        for seg, count in df['segment_label'].value_counts().head(10).items():
            print(f"     {seg}: {count:,}")
    
    if 'fqhc_flag' in df.columns:
        count = (df['fqhc_flag'] == 1).sum()
        print(f"  ✅ FQHC Flag: {count:,} clinics")
    
    # Check Contact Info
    print(f"\n{'='*80}")
    print(f" CONTACT INFORMATION")
    print(f"{'='*80}")
    
    if 'phone' in df.columns:
        count = df['phone'].notnull().sum()
        print(f"  ✅ Phone Numbers: {count:,} ({count/len(df)*100:.1f}%)")
    else:
        print(f"  ❌ Phone column MISSING")
    
    # Summary
    print(f"\n{'='*80}")
    print(f" DIAGNOSIS SUMMARY")
    print(f"{'='*80}")
    
    issues = []
    
    # Check for volume data
    if not vol_cols:
        issues.append("❌ NO VOLUME COLUMNS FOUND")
    elif all(df[c].notnull().sum() == 0 for c in vol_cols):
        issues.append("❌ VOLUME COLUMNS EXIST BUT ARE EMPTY")
    else:
        vol_populated = [c for c in vol_cols if df[c].notnull().sum() > 0]
        print(f"  ✅ Volume Data: {len(vol_populated)} columns populated")
    
    # Check for financial data
    if not fin_cols:
        issues.append("❌ NO FINANCIAL COLUMNS FOUND")
    elif all(df[c].notnull().sum() == 0 for c in fin_cols):
        issues.append("❌ FINANCIAL COLUMNS EXIST BUT ARE EMPTY")
    else:
        fin_populated = [c for c in fin_cols if df[c].notnull().sum() > 0]
        print(f"  ✅ Financial Data: {len(fin_populated)} columns populated")
    
    # Check for undercoding
    if 'undercoding_ratio' not in df.columns:
        issues.append("❌ UNDERCODING COLUMN MISSING")
    elif df['undercoding_ratio'].notnull().sum() == 0:
        issues.append("❌ UNDERCODING COLUMN EXISTS BUT IS EMPTY")
    else:
        print(f"  ✅ Undercoding Data: Present")
    
    if issues:
        print(f"\n  ISSUES DETECTED:")
        for issue in issues:
            print(f"    {issue}")
    else:
        print(f"\n  ✅ ALL KEY DATA PRESENT")

if __name__ == "__main__":
    diagnose()
