# HCRIS Data Extraction - Handles Headerless Format
# The FQHC cost reports use HCRIS format with position-based columns
# We need to map position → column name using HCRIS_DataDictionary.csv

import os
import pandas as pd
import numpy as np

print("\n" + "="*80)
print("STEP 1: LOAD HCRIS DATA DICTIONARY")
print("="*80)

# Load the data dictionary
dict_path = "data/raw/cost_reports_fqhc/FQHC14-DOCUMENTATION/HCRIS_DataDictionary.csv"

if os.path.exists(dict_path):
    data_dict = pd.read_csv(dict_path)
    print(f"✅ Loaded HCRIS data dictionary")
    print(f"   Rows: {len(data_dict)}")
    print(f"   Columns: {data_dict.columns.tolist()}")
    print(f"\nFirst 10 rows:")
    print(data_dict.head(10)[['Column Code', 'Title', 'Description']])
else:
    print(f"❌ Data dictionary not found: {dict_path}")

print("\n" + "="*80)
print("STEP 2: INVESTIGATE FQHC NUMERIC FILE STRUCTURE")
print("="*80)

fqhc_nmrc_2024 = "data/raw/cost_reports_fqhc/FQHC14-ALL-YEARS (1)/FQHC14_2024_nmrc.csv"

if os.path.exists(fqhc_nmrc_2024):
    print(f"Loading {fqhc_nmrc_2024}...")
    
    # Load WITHOUT header to see raw structure
    fqhc_raw = pd.read_csv(fqhc_nmrc_2024, header=None, nrows=5)
    
    print(f"\n📊 Raw data (first 5 rows, first 10 columns):")
    print(fqhc_raw.iloc[:, :10])
    
    print(f"\n📊 Full column count: {len(fqhc_raw.columns)}")
    print(f"Row count: {len(pd.read_csv(fqhc_nmrc_2024, header=None)):,}")
    
    # Load entire file WITHOUT header
    fqhc_full = pd.read_csv(fqhc_nmrc_2024, header=None)
    print(f"\n✅ Loaded FQHC numeric data: {len(fqhc_full):,} rows × {len(fqhc_full.columns)} columns")
    
    # Print first 3 rows to understand data structure
    print(f"\nFirst 3 rows of FQHC data:")
    for i in range(min(3, len(fqhc_full))):
        print(f"Row {i}: {fqhc_full.iloc[i, :10].values}")
    
    # Check if there's a pattern - HCRIS files typically have:
    # Report metadata columns, then repeating (LINE_NUM, CLMN_NUM, VALUE) triplets
    
    print(f"\n🔍 Analyzing column structure...")
    print(f"Sample values from first row:")
    for col_idx in range(min(10, len(fqhc_full.columns))):
        print(f"   Column {col_idx}: {fqhc_full.iloc[0, col_idx]}")
    
    # Try to identify NPI column (should be numeric)
    print(f"\nSearching for NPI (numeric identifier)...")
    for col_idx in range(min(20, len(fqhc_full.columns))):
        try:
            val = float(fqhc_full.iloc[0, col_idx])
            if 1000000000 <= val <= 9999999999:  # NPI range
                print(f"   🎯 Found potential NPI in column {col_idx}: {val}")
        except:
            pass

else:
    print(f"❌ File not found: {fqhc_nmrc_2024}")

print("\n" + "="*80)
print("STEP 3: UNDERSTANDING HCRIS STRUCTURE")
print("="*80)

print("""
HCRIS Format Notes:
- FQHC14_2024_nmrc.csv = Numeric data (contains revenue, expenses, patient counts)
- FQHC14_2024_rpt.csv = Report metadata (facility info, filing dates)
- FQHC14_2024_alpha.csv = Alphanumeric data (text fields)

Key fields we need to extract:
1. NPI or Provider Number (to join with clinics_seed.csv)
2. Total Revenue (worksheet S-10, line ~0100)
3. Total Expenses (worksheet S-10, line ~0200)
4. Patient Encounters (worksheet G-3, line ~3000)
5. Medicaid Revenue (worksheet S-10, line ~0102)
6. Medicare Revenue (worksheet S-10, line ~0101)
7. Commercial/Other Revenue (worksheet S-10, line ~0103)

The data dictionary maps:
- Column Code → Field name
- LINE_NUM (e.g., 0100) → What the data represents
- CLMN_NUM (e.g., 01) → Sub-column for multi-part fields
- VALUE → The actual number

Next: We need to:
1. Check the _rpt.csv file for NPI + facility identifiers
2. Understand the position of key worksheets in _nmrc.csv
3. Parse line numbers to extract revenue components
""")

print("\n" + "="*80)
print("STEP 4: CHECK REPORT METADATA")
print("="*80)

fqhc_rpt_2024 = "data/raw/cost_reports_fqhc/FQHC14-ALL-YEARS (1)/FQHC14_2024_rpt.csv"

if os.path.exists(fqhc_rpt_2024):
    print(f"Loading {fqhc_rpt_2024}...")
    fqhc_rpt = pd.read_csv(fqhc_rpt_2024, header=None, nrows=3)
    
    print(f"\nFirst 3 rows of report file:")
    for i in range(min(3, len(fqhc_rpt))):
        print(f"Row {i}: {fqhc_rpt.iloc[i, :].values}")
    
    print(f"\nTotal rows in report file: {len(pd.read_csv(fqhc_rpt_2024, header=None)):,}")
    print(f"Total columns: {len(pd.read_csv(fqhc_rpt_2024, header=None).columns)}")

else:
    print(f"❌ Report file not found: {fqhc_rpt_2024}")

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)

print("""
The HCRIS format is complex. To properly extract data, we need:

1. HCRIS_TABLE_DESCRIPTIONS_AND_SQL.txt 
   - Shows which worksheets (e.g., S-10, G-3) contain which data
   - Maps LINE_NUM values to their meanings

2. Exact column position mapping
   - The CSV has fixed positions for metadata vs data
   - Position 0-15: Usually metadata (NPI, facility#, dates, etc.)
   - Positions 16+: Repeating (LINE_NUM, CLMN_NUM, VALUE) triplets

NEXT STEP: Read the TABLE_DESCRIPTIONS file to understand structure.
""")

print("\n" + "="*80)
print("END INVESTIGATION")
print("="*80)