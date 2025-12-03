import pandas as pd
import os

SEED_FILE = "data/curated/clinics_seed.csv"
ALPHA_FILE = "data/raw/cost_reports_fqhc/FQHC14-ALL-YEARS (1)/FQHC14_2024_alpha.csv"

def normalize_name(name):
    if pd.isna(name): return ""
    name = str(name).upper().strip()
    name = name.replace(".", "").replace(",", "").replace(" INC", "").replace(" LLC", "").replace(" PC", "")
    name = name.replace(" CLINIC", "").replace(" CENTER", "").replace(" HEALTH", "")
    return name

print("Loading Seed...")
seed = pd.read_csv(SEED_FILE, usecols=['org_name'], nrows=10000)
seed['norm_name'] = seed['org_name'].apply(normalize_name)
print(f"Sample Seed Names: {seed['norm_name'].head(5).tolist()}")

print("\nLoading Alpha...")
alpha = pd.read_csv(ALPHA_FILE, header=None, names=['RPT_REC_NUM', 'WKSHT_CD', 'LINE_NUM', 'CLMN_NUM', 'VALUE'], dtype=str)
names = alpha[
    (alpha['WKSHT_CD'] == 'S100001') & 
    (alpha['LINE_NUM'] == '00100') & 
    (alpha['CLMN_NUM'] == '00100')
]
names['norm_name'] = names['VALUE'].apply(normalize_name)
print(f"Sample FQHC Names: {names['norm_name'].head(5).tolist()}")

print("\nChecking Overlap...")
seed_names = set(seed['norm_name'])
fqhc_names = set(names['norm_name'])
overlap = seed_names.intersection(fqhc_names)
print(f"Overlap Count (in sample): {len(overlap)}")
if len(overlap) > 0:
    print(f"Sample Matches: {list(overlap)[:5]}")
else:
    print("No overlap found in sample.")
    # Print some close calls?
    print("First 5 FQHC names vs First 5 Seed names:")
    print("FQHC:", list(fqhc_names)[:5])
    print("Seed:", list(seed_names)[:5])
