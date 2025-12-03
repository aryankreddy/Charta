import pandas as pd
import os
from fuzzywuzzy import fuzz

# --- CONFIGURATION ---
SCORED_PATH = "data/curated/clinics_scored.csv"
SEGMENT_MAP = {
    "Segment A": "Behavioral Health",
    "Segment B": "FQHC / Rural",
    "Segment C": "Multi-Specialty",
    "Segment D": "Urgent Care",
    "Segment E": "Primary Care",
    "Segment F": "Hospital / System"
}

# --- Charta's Known Customers (Source List) ---
# We use names and keywords for fuzzier matching
KNOWN_CUSTOMERS = [
    "Kaiser Permanente",
    "Eventus WholeHealth",
    "Family Care Center",
    "Preventive Measures",
    "KidsCare Home Health",
]

def normalize_name_for_search(name: str) -> str:
    """
    Removes common legal structures and formats for better fuzzy matching.
    FIX: Ensure name is treated as a string before calling .upper().
    """
    if pd.isna(name) or not name: # Check for NaN and None/Empty
        return ""
        
    name = str(name).upper().replace('.', '').replace(',', '')
    name = name.replace('INC', '').replace('LLC', '').replace('MD', '')
    name = name.replace('GROUP', '').replace('P A', '').replace('P C', '')
    return name.strip()

def search_customers(df: pd.DataFrame):
    """Searches the scored dataframe for known customer names using fuzzy matching."""
    print("====================================================")
    print("🔎 Searching Database for Known Charta Customers")
    print("====================================================")
    
    if df.empty:
        print("❌ Error: Scored data is empty. Run score_icp.py first.")
        return

    # Normalize a dedicated search column in the DataFrame
    if 'org_name' not in df.columns:
        print("❌ Missing 'org_name' column for matching.")
        return
        
    # We apply the fixed normalization function
    df['search_name'] = df['org_name'].apply(normalize_name_for_search)
    
    results = []
    
    for target_name in KNOWN_CUSTOMERS:
        norm_target = normalize_name_for_search(target_name)
        best_match = None
        best_score = 0
        
        # Look for a high-confidence fuzzy match (Fuzz Ratio > 90)
        for index, row in df.iterrows():
            ratio = fuzz.ratio(norm_target, row['search_name'])
            
            if ratio > 90: # High confidence match threshold
                
                # If we find a Tier 1 match, we take it instantly
                if row['icp_tier'] == 1:
                    best_match = row
                    best_score = ratio
                    break
                
                if ratio > best_score:
                    best_score = ratio
                    best_match = row

        if best_match is not None and best_score >= 80: # Ensure final score is decent
            results.append({
                'Target': target_name,
                'Found Name': best_match.get('org_name'),
                'Segment': SEGMENT_MAP.get(best_match.get('segment_label', 'N/A'), 'N/A'),
                'Score': f"{best_match.get('icp_total_score'):.1f}",
                'Tier': best_match.get('icp_tier'),
                'Match Confidence': f"{best_score}%",
                'Network Size': f"{int(best_match.get('num_clinics', 1)):,} sites" if pd.notna(best_match.get('num_clinics')) else 'N/A',
                'Status': 'FOUND (Tier 1 Expected)' if best_match.get('icp_tier') == 1 else 'FOUND (Tier 2/3)'
            })
        else:
            results.append({
                'Target': target_name,
                'Status': 'NOT FOUND (Low Confidence)',
                'Segment': 'N/A',
                'Score': 'N/A',
                'Tier': 'N/A',
                'Match Confidence': 'N/A',
                'Found Name': 'N/A',
                'Network Size': 'N/A'
            })
            
    if not results:
        print("No matches found.")
        return
        
    results_df = pd.DataFrame(results)
    print("\n--- RESULTS SUMMARY ---")
    print(results_df.to_string())
    print("\n====================================================")
    print("Conclusion: Check if 'Score' and 'Tier' match expectations.")

if __name__ == "__main__":
    try:
        # Note: num_clinics may be NaN from merge, but the search handles it now.
        df_scored = pd.read_csv(SCORED_PATH, low_memory=False)
        search_customers(df_scored)
    except FileNotFoundError:
        print(f"❌ Error: Scored data file not found at {SCORED_PATH}. Please run score_icp.py first.")
    except Exception as e:
        print(f"An unexpected error occurred during search: {e}")