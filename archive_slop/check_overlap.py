import pandas as pd
import os
import numpy as np

SEED = "data/curated/clinics_seed.csv"
UTIL = "data/curated/staging/stg_physician_util.parquet"

print("Checking NPI Overlap...")

if os.path.exists(SEED) and os.path.exists(UTIL):
    seed = pd.read_csv(SEED, usecols=['npi'])
    util = pd.read_parquet(UTIL, columns=['npi'])
    
    # Normalize
    seed_npis = set(pd.to_numeric(seed['npi'], errors='coerce').fillna(0).astype(np.int64))
    util_npis = set(pd.to_numeric(util['npi'], errors='coerce').fillna(0).astype(np.int64))
    
    # Remove 0
    seed_npis.discard(0)
    util_npis.discard(0)
    
    print(f"Seed NPIs: {len(seed_npis):,}")
    print(f"Util NPIs: {len(util_npis):,}")
    
    overlap = seed_npis.intersection(util_npis)
    print(f"Overlap: {len(overlap):,}")
    
    if len(overlap) > 0:
        print(f"Sample Overlap: {list(overlap)[:5]}")
    else:
        print("❌ NO OVERLAP FOUND")
else:
    print("Files not found")
