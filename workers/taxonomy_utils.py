import os
import pandas as pd
from typing import Dict, Optional

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TAXONOMY_FILE = os.path.join(ROOT, "config", "taxonomy_codes.csv")

_TAXONOMY_MAP: Dict[str, str] = {}

def load_taxonomy_map() -> Dict[str, str]:
    """
    Loads the NUCC taxonomy mapping from CSV.
    Returns a dictionary of {code: description}.
    """
    global _TAXONOMY_MAP
    if _TAXONOMY_MAP:
        return _TAXONOMY_MAP
    
    if not os.path.exists(TAXONOMY_FILE):
        print(f"Warning: Taxonomy file not found at {TAXONOMY_FILE}")
        return {}

    try:
        df = pd.read_csv(TAXONOMY_FILE, dtype=str)
        # NUCC file columns: Code, Grouping, Classification, Specialization, ...
        # We want to combine Classification + Specialization for a full description
        
        mapping = {}
        for _, row in df.iterrows():
            code = str(row.get("Code", "")).strip()
            if not code:
                continue
                
            classification = str(row.get("Classification", "")).strip()
            specialization = str(row.get("Specialization", "")).strip()
            
            if specialization and specialization.lower() != "nan":
                desc = f"{classification} - {specialization}"
            else:
                desc = classification
                
            mapping[code] = desc
            
        _TAXONOMY_MAP = mapping
        print(f"Loaded {len(mapping)} taxonomy codes.")
        return mapping
    except Exception as e:
        print(f"Error loading taxonomy map: {e}")
        return {}

def get_taxonomy_description(code: str) -> str:
    """
    Returns the description for a given taxonomy code.
    """
    if not _TAXONOMY_MAP:
        load_taxonomy_map()
    return _TAXONOMY_MAP.get(str(code).strip(), "Unknown")

if __name__ == "__main__":
    # Verification block
    load_taxonomy_map()
    
    test_codes = ["3336C0003X", "251G00000X"]
    print("\n--- Verification ---")
    for code in test_codes:
        print(f"Code: {code} -> {get_taxonomy_description(code)}")
