import importlib.util as import_util
import json
import math
import os
import glob
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from workers.config import load_all
from workers.utils import download_api_pages, read_hcris_multi, stream_csv

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_RAW = os.path.join(ROOT, "data", "raw")
DATA_CURATED = os.path.join(ROOT, "data", "curated")
STAGING_DIR = os.path.join(DATA_CURATED, "staging")


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def abs_path(relative: str) -> str:
    return os.path.abspath(os.path.join(ROOT, relative))


def normalize_zip(value: str) -> str:
    if value is None or value == "":
        return ""
    cleaned = str(value).strip().replace(" ", "")
    if len(cleaned) >= 5:
        return cleaned[:5]
    return cleaned


def write_parquet(df: pd.DataFrame, path: str) -> None:
    ensure_dir(os.path.dirname(path))
    engine_available = import_util.find_spec('pyarrow') is not None
    if df.empty:
        empty = pd.DataFrame()
        if engine_available:
            empty.to_parquet(path, index=False)
        else:
            empty.to_csv(path.replace('.parquet', '.csv'), index=False)
        return
    if engine_available:
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path.replace('.parquet', '.csv'), index=False)


# --- NPI robust loader --------------------------------------------------------

NPI_COL_ALIASES: Dict[str, List[str]] = {
    "npi": ["NPI"],
    "org_name": [
        "Provider Organization Name (Legal Business Name)",
        "Provider Organization Name (Legal Business Name) ",
    ],
    "entity_type": ["Entity Type Code"],
    "city": [
        "Provider Business Practice Location Address City Name",
        "Provider Business Practice Location City Name",
    ],
    "state": [
        "Provider Business Practice Location Address State Name",
        "Provider Business Practice Location State Name",
    ],
    "zip": [
        "Provider Business Practice Location Address Postal Code",
        "Provider Business Practice Location Postal Code",
    ],
    "phone": [
        "Provider Business Practice Location Address Telephone Number",
        "Provider Business Practice Location Telephone Number",
    ],
    "tax1": ["Healthcare Provider Taxonomy Code_1", "Healthcare Provider Taxonomy Code 1"],
    "tax2": ["Healthcare Provider Taxonomy Code_2", "Healthcare Provider Taxonomy Code 2"],
    "tax3": ["Healthcare Provider Taxonomy Code_3", "Healthcare Provider Taxonomy Code 3"],
}

def _resolve_npi_renames(actual_cols: List[str]) -> Dict[str, str]:
    renames: Dict[str, str] = {}
    for canon, variants in NPI_COL_ALIASES.items():
        found = next((col for col in variants if col in actual_cols), None)
        if found:
            renames[found] = canon
    return renames

def process_npi_zip() -> pd.DataFrame:
    """
    Finds the NPI zip file in data/raw/npi_registry, opens the largest CSV inside,
    and streams it to build the staging parquet.
    """
    npi_dir = os.path.join(DATA_RAW, "npi_registry")
    zips = glob.glob(os.path.join(npi_dir, "*.zip"))
    
    if not zips:
        print(f"Skipping NPI ingestion; no .zip file found in {npi_dir}")
        return pd.DataFrame(columns=["npi", "org_name", "city", "state", "zip", "phone", "tax1", "tax2", "tax3"])
    
    # Use the first zip found (or largest if multiple)
    zip_path = zips[0]
    print(f"Processing NPI Registry from: {zip_path}")
    
    frames: List[pd.DataFrame] = []
    first_chunk = True
    rename_map: Dict[str, str] = {}

    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Find the largest CSV file in the zip (assumed to be the main data file)
        csv_files = [f for f in zf.namelist() if f.lower().endswith('.csv') and "fileheader" not in f.lower()]
        if not csv_files:
             print("No CSV files found in NPI zip")
             return pd.DataFrame()
        
        target_file = max(csv_files, key=lambda x: zf.getinfo(x).file_size)
        print(f"Extracting from internal file: {target_file}")

        with zf.open(target_file) as handle:
            for chunk in stream_csv(
                handle,
                chunksize=100_000,
                dtype={"NPI": "string", "Entity Type Code": "string"},
                encoding="latin-1",
                low_memory=False
            ):
                if first_chunk:
                    rename_map = _resolve_npi_renames(list(chunk.columns))
                    if "npi" not in rename_map.values() and "NPI" not in chunk.columns:
                        raise ValueError(f"NPI column not found. Got columns: {list(chunk.columns)[:20]}")
                    process_npi_zip._rename_map = rename_map  # type: ignore[attr-defined]
                    first_chunk = False
                else:
                    rename_map = getattr(process_npi_zip, "_rename_map")  # type: ignore[attr-defined]

                chunk = chunk.rename(columns=rename_map)
                keep = [c for c in ["npi", "org_name", "entity_type", "city", "state", "zip", "phone", "tax1", "tax2", "tax3"] if c in chunk.columns]
                chunk = chunk[keep]
                
                # Filter for Organizations (Entity Type 2)
                if "entity_type" in chunk.columns:
                    chunk = chunk[chunk["entity_type"] == "2"]
                
                if chunk.empty:
                    continue
                frames.append(chunk)

    if not frames:
        return pd.DataFrame(columns=["npi", "org_name", "city", "state", "zip", "phone", "tax1", "tax2", "tax3"])

    out = pd.concat(frames, ignore_index=True)
    if "zip" in out.columns:
        out["zip"] = out["zip"].astype(str).str.extract(r"(^\d{5})", expand=False)
    if "state" in out.columns:
        out["state"] = out["state"].astype(str).str.upper().str[:2]
    out["npi"] = out["npi"].astype(str)
    return out


def process_hrsa(source_cfg: Dict) -> pd.DataFrame:
    path = abs_path(source_cfg.get("url"))
    if not os.path.exists(path):
        print(f'Skipping HRSA ingestion; file not found: {path}')
        return pd.DataFrame(columns=["site_id", "org_name", "site_name", "address", "city", "state", "zip", "npi", "fqhc_flag"])
    df = pd.read_csv(path, dtype="string", low_memory=False)

    def first_match(candidates: List[str]) -> str:
        for candidate in candidates:
            if candidate in df.columns:
                return candidate
        return ""

    def column_or_blank(col_name: str) -> pd.Series:
        if col_name and col_name in df.columns:
            return df[col_name].fillna("").astype(str)
        return pd.Series(["" for _ in range(len(df))], index=df.index)

    name_col = first_match(["site_name", "Site Name", "site"])
    org_col = first_match(["parent_organization_name", "Parent Organization", "organization_name", "Health Center Name", name_col])
    state_col = first_match(["state", "State", "state_abbr", "Site State Abbreviation"])
    city_col = first_match(["city", "City", "Site City"])
    zip_col = first_match(["zip", "Zip", "zip_code", "Site Postal Code"])
    address_col = first_match(["address", "Site Address", "street_address", "Street Address"])
    npi_col = first_match(["npi", "NPI", "FQHC Site NPI Number"])

    site_ids = column_or_blank("site_id") if "site_id" in df.columns else pd.Series(df.index.astype(str), index=df.index)

    data = pd.DataFrame(
        {
            "site_id": site_ids,
            "org_name": column_or_blank(org_col).str.upper(),
            "site_name": column_or_blank(name_col),
            "address": column_or_blank(address_col),
            "city": column_or_blank(city_col).str.title(),
            "state": column_or_blank(state_col).str.upper(),
            "zip": column_or_blank(zip_col).map(normalize_zip),
            "npi": column_or_blank(npi_col),
            "fqhc_flag": 1,  # All HRSA records are FQHCs or Look-Alikes by definition
        }
    )

    mask = data["org_name"] == ""
    if mask.any():
        data.loc[mask, "org_name"] = data.loc[mask, "site_name"].str.upper()

    staging_path = os.path.join(STAGING_DIR, "stg_hrsa_sites.parquet")
    write_parquet(data, staging_path)
    return data


def find_latest_hcris_files(base_dir: str, prefix: str) -> Dict[str, str]:
    """
    Scans a directory for RPT, NMRC, and ALPHA CSV files matching the latest year.
    Expects filenames like {prefix}_YYYY_rpt.csv
    """
    files = glob.glob(os.path.join(base_dir, "**", f"*{prefix}*rpt.csv"), recursive=True)
    if not files:
        return {}
    
    # Extract years and find max
    years = []
    for f in files:
        try:
            # Simple heuristic: look for 4 digit year in filename
            parts = os.path.basename(f).split('_')
            for p in parts:
                if p.isdigit() and len(p) == 4 and p.startswith('20'):
                    years.append(int(p))
        except:
            pass
    
    if not years:
        # Fallback: just take the last file alphabetically
        latest_rpt = sorted(files)[-1]
        # Try to guess the year from that file
        year = "unknown"
    else:
        year = max(years)
        # Filter files for that year
        latest_rpt = next((f for f in files if str(year) in f), None)

    if not latest_rpt:
        return {}
    
    # Infer other files
    base_name = latest_rpt.replace("_rpt.csv", "")
    nmrc = latest_rpt.replace("_rpt.csv", "_nmrc.csv")
    alpha = latest_rpt.replace("_rpt.csv", "_alpha.csv")
    
    # Verify they exist
    result = {"rpt": latest_rpt}
    if os.path.exists(nmrc):
        result["nmrc"] = nmrc
    if os.path.exists(alpha):
        result["alphnmrc"] = alpha
        
    print(f"Found latest HCRIS files for {prefix} (Year {year}): {result}")
    return result

def process_hcris_csv(name: str, files: Dict[str, str], facility_type: str) -> pd.DataFrame:
    if not files:
        return pd.DataFrame(columns=["provider_num", "facility_type"])
    
    # Read ALPHA file to get Provider Number (col 0)
    # HCRIS CSVs usually don't have headers. 
    # ALPHA: RPT_REC_NUM, WKSHT_CD, LINE_NUM, COL_NUM, ITM_VAL_NUM
    # But we need the Provider Number which is usually in S-2 worksheet.
    # Actually, simpler approach: The RPT file usually contains the Provider Number in the first few columns?
    # No, RPT file links RPT_REC_NUM to PRVDR_CTRL_TYPE_CD etc.
    # We need a way to link RPT_REC_NUM to Provider Number (CCN).
    # Usually there is a separate file or it's in the ALPHA file (Worksheet S-2, Line 1, Column 1 is usually CCN).
    
    # Let's try to read the ALPHA file and look for Worksheet S-2, Line 1, Col 1 (or similar)
    # Or just extract all unique values that look like CCNs (6 digits)
    
    provider_numbers = set()
    
    if "alphnmrc" in files:
        # Read headerless CSV
        try:
            # Streaming to avoid memory issues
            for chunk in stream_csv(files["alphnmrc"], header=None, names=["rpt_rec_num", "wksht_cd", "line_num", "col_num", "itm_val_num"]):
                # Filter for S-2 worksheet (General Info) and Line 1 or 2 (Provider Number)
                # This is specific to form type, but generally CCN is in S-2.
                # Let's just grab anything that looks like a CCN from the value column
                # CCNs are 6 alphanumeric chars.
                
                # Heuristic: Just get all unique values from column 4 (itm_val_num)
                # This is too broad.
                
                # Better: Filter for wksht_cd like 'S2%' and line_num like '100' (Line 1.00)
                # FQHC (Form 224-14): Worksheet S-1, Part I, Line 1, Column 1 is Site Name. Line 3 is CCN.
                # Hospital (Form 2552-10): Worksheet S-2, Part I, Line 3, Column 1 is CCN.
                
                mask = chunk["itm_val_num"].astype(str).str.len().between(6, 10) # CCNs are usually 6 chars
                candidates = chunk[mask]["itm_val_num"].unique()
                provider_numbers.update(candidates)
        except Exception as e:
            print(f"Error reading HCRIS ALPHA file: {e}")

    # If we couldn't extract from ALPHA, try to see if there's a PRVDR_ID_INFO file in the directory
    base_dir = os.path.dirname(files.get("rpt", ""))
    prvdr_info = glob.glob(os.path.join(base_dir, "*PRVDR_ID_INFO.CSV"))
    if prvdr_info:
        try:
            pdf = pd.read_csv(prvdr_info[0])
            # Look for column with 'provider' or 'num'
            col = next((c for c in pdf.columns if "prvdr_num" in c.lower() or "provider" in c.lower()), None)
            if col:
                provider_numbers.update(pdf[col].astype(str).unique())
        except:
            pass

    metrics = pd.DataFrame(
        {
            "provider_num": list(provider_numbers),
            "facility_type": facility_type,
        }
    )
    staging_path = os.path.join(STAGING_DIR, f"stg_hcris_{name}.parquet")
    write_parquet(metrics, staging_path)
    return metrics


def process_utilization_csv() -> pd.DataFrame:
    util_dir = os.path.join(DATA_RAW, "physician_utilization")
    files = glob.glob(os.path.join(util_dir, "**", "*.csv"), recursive=True)
    if not files:
        return pd.DataFrame(columns=["npi", "services_count", "allowed_amt", "bene_count"])
    
    path = files[0] # Take first found
    print(f"Processing Utilization from: {path}")
    
    # Columns in 2023 file: Rndrng_NPI, Tot_Srvcs, Tot_Benes, Avg_Sbmtd_Chrg, Avg_Mdcr_Alowd_Amt...
    # We need to aggregate by NPI.
    
    # Use stream_csv to handle large file
    agg_data = defaultdict(lambda: {"services": 0.0, "allowed": 0.0, "benes": 0.0})
    
    for chunk in stream_csv(path, low_memory=False):
        # Identify columns
        cols = chunk.columns
        npi_col = next((c for c in cols if "npi" in c.lower()), None)
        srv_col = next((c for c in cols if "srvcs" in c.lower() or "services" in c.lower()), None)
        bene_col = next((c for c in cols if "benes" in c.lower()), None)
        allowed_col = next((c for c in cols if "alowd" in c.lower() or "allowed" in c.lower()), None)
        
        if not npi_col:
            continue
            
        # Convert to numeric
        if srv_col: chunk[srv_col] = pd.to_numeric(chunk[srv_col], errors='coerce').fillna(0)
        if allowed_col: chunk[allowed_col] = pd.to_numeric(chunk[allowed_col], errors='coerce').fillna(0)
        if bene_col: chunk[bene_col] = pd.to_numeric(chunk[bene_col], errors='coerce').fillna(0)
        
        # Group by NPI in this chunk
        grouped = chunk.groupby(npi_col).agg({
            srv_col: "sum" if srv_col else "count",
            allowed_col: "sum" if allowed_col else "count",
            bene_col: "max" if bene_col else "count" # Max benes is a reasonable proxy for total unique patients seen
        })
        
        for npi, row in grouped.iterrows():
            agg_data[str(npi)]["services"] += row[srv_col] if srv_col else 0
            agg_data[str(npi)]["allowed"] += row[allowed_col] if allowed_col else 0
            agg_data[str(npi)]["benes"] = max(agg_data[str(npi)]["benes"], row[bene_col] if bene_col else 0)

    # Convert to DataFrame
    rows = []
    for npi, data in agg_data.items():
        rows.append({
            "npi": npi,
            "services_count": data["services"],
            "allowed_amt": data["allowed"],
            "bene_count": data["benes"]
        })
        
    df = pd.DataFrame(rows)
    staging_path = os.path.join(STAGING_DIR, "stg_physician_util.parquet")
    write_parquet(df, staging_path)
    return df

def process_pecos_csv() -> pd.DataFrame:
    pecos_dir = os.path.join(DATA_RAW, "pecos")
    files = glob.glob(os.path.join(pecos_dir, "**", "*Enrollment*.csv"), recursive=True)
    if not files:
        return pd.DataFrame(columns=["npi", "org_name", "state"])
    
    path = files[0]
    print(f"Processing PECOS from: {path}")
    
    # Columns: NPI, PAC_ID, ENRLMT_ID, LBN, STATE_CD...
    try:
        df = pd.read_csv(path, dtype=str, low_memory=False, encoding="latin-1")
    except UnicodeDecodeError:
        df = pd.read_csv(path, dtype=str, low_memory=False, encoding="cp1252")
    
    # Normalize
    npi_col = next((c for c in df.columns if "npi" in c.lower()), None)
    name_col = next((c for c in df.columns if "lbn" in c.lower() or "legal" in c.lower()), None)
    state_col = next((c for c in df.columns if "state" in c.lower()), None)
    
    if not npi_col:
        return pd.DataFrame()
        
    out = pd.DataFrame({
        "npi": df[npi_col],
        "org_name": df[name_col] if name_col else "",
        "state": df[state_col] if state_col else ""
    })
    out = out.drop_duplicates("npi")
    
    staging_path = os.path.join(STAGING_DIR, "stg_pecos_orgs.parquet")
    write_parquet(out, staging_path)
    return out

def process_aco_csv() -> pd.DataFrame:
    aco_dir = os.path.join(DATA_RAW, "aco")
    files = glob.glob(os.path.join(aco_dir, "**", "*ACO*.csv"), recursive=True)
    if not files:
        return pd.DataFrame(columns=["aco_id", "org_name"])
        
    path = files[0]
    print(f"Processing ACO from: {path}")
    
    try:
        df = pd.read_csv(path, dtype=str, low_memory=False, encoding="latin-1")
    except UnicodeDecodeError:
        df = pd.read_csv(path, dtype=str, low_memory=False, encoding="cp1252")
    
    # Columns: ACO_ID, ACO_Name...
    # We need Participant List to link to NPIs. 
    # If this file only has ACO level info, we can't link to NPIs without a participant file.
    # The user provided `PY2025_PC_Flex_ACO.csv`.
    # Let's check if there is a participant file.
    
    # If no participant file, we just stage the ACOs themselves.
    
    out = df.copy()
    out.columns = [c.lower().replace(" ", "_") for c in out.columns]
    
    staging_path = os.path.join(STAGING_DIR, "stg_aco_orgs.parquet")
    write_parquet(out, staging_path)
    return out


def main():
    cfg = load_all()
    sources = cfg["sources"]
    bulk = sources.get("bulk_sources", {})
    ensure_dir(DATA_RAW)
    ensure_dir(DATA_CURATED)
    ensure_dir(STAGING_DIR)

    counts = {}

    # 1. NPI Registry (ZIP)
    print("--- Processing NPI Registry ---")
    npi_path = os.path.join(STAGING_DIR, "stg_npi_orgs.parquet")
    if os.path.exists(npi_path):
        print(f"Skipping NPI (found {npi_path})")
        try:
            npi = pd.read_parquet(npi_path)
        except:
            npi = process_npi_zip()
    else:
        npi = process_npi_zip()
    
    if not npi.empty and not os.path.exists(npi_path):
        taxonomy_cols = [col for col in ["tax1", "tax2", "tax3"] if col in npi.columns]
        if taxonomy_cols:
            npi["taxonomy"] = npi[taxonomy_cols].fillna("").agg(
                lambda row: ";".join([val for val in row if val != ""]), axis=1
            )
        else:
            npi["taxonomy"] = ""
        
        # Ensure columns exist
        for col in ["address", "phone", "city", "state", "zip"]:
            if col not in npi.columns:
                npi[col] = ""
                
        order = ["npi", "org_name", "address", "city", "state", "zip", "phone", "taxonomy"]
        npi = npi[[col for col in order if col in npi.columns]]
        write_parquet(npi, npi_path)
    counts["stg_npi_orgs"] = len(npi)

    # 2. HRSA
    print("--- Processing HRSA ---")
    hrsa = process_hrsa(bulk.get("hrsa_fqhc_sites", {}))
    counts["stg_hrsa_sites"] = len(hrsa)

    # 3. Cost Reports
    print("--- Processing Cost Reports ---")
    # FQHC
    files = find_latest_hcris_files(os.path.join(DATA_RAW, "cost_reports_fqhc"), "FQHC")
    process_hcris_csv("fqhc", files, "FQHC")
    
    # Hospital
    files = find_latest_hcris_files(os.path.join(DATA_RAW, "cost_reports_hospitals"), "HOSP")
    process_hcris_csv("hospital", files, "Hospital")
    
    # HHA
    files = find_latest_hcris_files(os.path.join(DATA_RAW, "cost_reports_hha"), "HHA")
    process_hcris_csv("hha", files, "HHA")

    # 4. Utilization
    print("--- Processing Utilization ---")
    util_path = os.path.join(STAGING_DIR, "stg_physician_util.parquet")
    if os.path.exists(util_path):
        print(f"Skipping Utilization (found {util_path})")
        try:
            util = pd.read_parquet(util_path)
        except:
            util = process_utilization_csv()
    else:
        util = process_utilization_csv()
    counts["stg_physician_util"] = len(util)

    # 5. PECOS
    print("--- Processing PECOS ---")
    pecos = process_pecos_csv()
    counts["stg_pecos_orgs"] = len(pecos)

    # 6. ACO
    print("--- Processing ACO ---")
    aco = process_aco_csv()
    counts["stg_aco_orgs"] = len(aco)

    print("\nStaging counts:")
    for key, value in counts.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
