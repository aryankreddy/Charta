"""
DATA ATLAS GENERATOR
Author: Charta Health GTM Strategy

OBJECTIVE:
Crawl the entire 'data/' directory and generate a detailed inventory log.
For every file, identify:
1. File Size & Row Count
2. Key Join Columns (NPI, CCN, Name, Zip, State)
3. Potential Strategic Value (Revenue, Income, Margin, Profit, Cost, Utilization, Visit, Encounter, Patient, Email, Phone)
"""

import os
import pandas as pd
import datetime

# Configuration
# We assume the script is run from project root, so we find 'data' relative to it
ROOT_DIR = os.getcwd()
DATA_DIR = os.path.join(ROOT_DIR, "data")
OUTPUT_LOG = os.path.join(ROOT_DIR, "DATA_ATLAS_LOG.md")

# Key identifiers/Signals we are hunting for (Case Insensitive partial matches)
JOIN_KEYS = ['npi', 'provider', 'ccn', 'ein', 'tax_id', 'zip', 'state', 'city', 'address']
VALUE_KEYS = ['revenue', 'income', 'margin', 'profit', 'cost', 'utilization', 'visit', 'encounter', 'patient', 'email', 'phone', 'risk', 'score']

def get_file_info(filepath):
    """Peeks into a file to get metadata without loading the whole thing."""
    ext = os.path.splitext(filepath)[1].lower()
    info = {
        'rows': 'N/A',
        'cols': [],
        'join_keys': [],
        'value_signals': []
    }
    
    try:
        if ext == '.csv':
            # Read only header and first 5 rows
            df_peek = pd.read_csv(filepath, nrows=5, low_memory=False)
            info['cols'] = list(df_peek.columns)
            info['rows'] = "Unknown (CSV)" 
        elif ext == '.parquet':
            # Parquet metadata is fast
            df = pd.read_parquet(filepath)
            info['cols'] = list(df.columns)
            info['rows'] = len(df)
        elif ext in ['.xls', '.xlsx']:
            df = pd.read_excel(filepath, nrows=5)
            info['cols'] = list(df.columns)
            info['rows'] = "Excel Sheet"
        else:
            return None # Skip non-data files
        
        # Analyze Columns
        lower_cols = [str(c).lower() for c in info['cols']]
        info['join_keys'] = [c for c in lower_cols if any(k in c for k in JOIN_KEYS)]
        info['value_signals'] = [c for c in lower_cols if any(v in c for v in VALUE_KEYS)]
        
    except Exception as e:
        info['error'] = str(e)
        
    return info

def generate_atlas():
    print(f"🗺️  STARTING DATA EXPEDITION IN: {DATA_DIR}")
    
    with open(OUTPUT_LOG, 'w') as f:
        f.write(f"# CHARTA HEALTH DATA ATLAS\n")
        f.write(f"**Generated:** {datetime.datetime.now()}\n\n")
        f.write("> This document lists every data file available to the scoring engine, enabling us to identify 'Dark Matter' data assets.\n\n")
        
        # Walk through the data directory
        total_files = 0
        for root, dirs, files in os.walk(DATA_DIR):
            # Skip hidden folders or system folders
            if '/.' in root or '__' in root: continue
            
            # Calculate relative path for clean display
            rel_path = os.path.relpath(root, DATA_DIR)
            if rel_path == ".": rel_path = "/"
            
            # Create Section Header
            level = rel_path.count(os.sep)
            indent = '#' * (min(level + 2, 6))
            f.write(f"\n{indent} 📂 /{rel_path}\n")
            
            for file in sorted(files):
                if file.startswith('.'): continue
                
                filepath = os.path.join(root, file)
                filesize_mb = os.path.getsize(filepath) / (1024 * 1024)
                
                # Only log significant files or known data types
                if not file.endswith(('.csv', '.parquet', '.xlsx', '.xls', '.json', '.txt')):
                    continue

                total_files += 1
                print(f"Scanning: {file}...")
                
                f.write(f"\n- **📄 {file}** ({filesize_mb:.2f} MB)\n")
                
                # Deep Inspection for Data Files
                if file.endswith(('.csv', '.parquet', '.xlsx', '.xls')):
                    meta = get_file_info(filepath)
                    
                    if meta:
                        if 'error' in meta:
                            f.write(f"  - ⚠️ **Error:** {meta['error']}\n")
                        else:
                            if meta['rows'] != 'N/A':
                                f.write(f"  - 📊 **Rows:** {meta['rows']}\n")
                            
                            if meta['join_keys']:
                                f.write(f"  - 🔗 **KEYS:** `{', '.join(meta['join_keys'])}`\n")
                            
                            if meta['value_signals']:
                                f.write(f"  - 💰 **VALUE:** `{', '.join(meta['value_signals'])}`\n")
                            
                            # List columns (truncated if too long)
                            all_cols = [str(c) for c in meta['cols']]
                            if len(all_cols) > 10:
                                col_str = ", ".join(all_cols[:10]) + f", ... (+{len(all_cols)-10} more)"
                            else:
                                col_str = ", ".join(all_cols)
                            f.write(f"  - 📋 **Cols:** {col_str}\n")

    print(f"✅ ATLAS GENERATED: {OUTPUT_LOG}")
    print(f"Total Files Scanned: {total_files}")

if __name__ == "__main__":
    generate_atlas()