import pandas as pd
from fuzzywuzzy import fuzz

clinics = pd.read_csv("data/curated/clinics_seed.csv", nrows=2000)
irs = pd.read_csv("data/raw/index_2024.csv", nrows=20000)

matches = 0
for _, c in clinics.iterrows():
    cname = str(c['org_name']).upper()
    best = 0
    for _, r in irs.iterrows():
        rname = str(r['TAXPAYER_NAME']).upper()
        s = fuzz.token_set_ratio(cname, rname)
        if s > best:
            best = s
    if best >= 85:
        matches += 1

print(f"Matched {matches} / {len(clinics)} = {matches/len(clinics):.1%}")
