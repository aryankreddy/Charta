"""
OIG LEIE (List of Excluded Individuals/Entities) Enrichment Worker

Downloads the OIG LEIE exclusion list and matches it against clinic NPIs and names
to flag compliance risk.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import pandas as pd
import requests
from fuzzywuzzy import fuzz

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_STAGING = os.path.join(ROOT, "data", "staging")
DATA_CURATED = os.path.join(ROOT, "data", "curated")
STAGING_DIR = os.path.join(DATA_CURATED, "staging")

# OIG LEIE download URLs (CSV format) - try primary, fallback to secondary
OIG_LEIE_URLS = [
    "https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv",  # Primary URL (working as of 2025)
    "https://oig.hhs.gov/exclusions/downloadables/LEIE_NPI.csv",  # Fallback URL
    "https://exclusions.oig.hhs.gov/exclusions/content/public/LEIE_NPI.csv",  # Secondary fallback
]
OIG_LEIE_RAW = os.path.join(DATA_STAGING, "oig_leie_raw.csv")
OIG_LEIE_MATCHES = os.path.join(STAGING_DIR, "oig_leie_matches.csv")

# Ensure directories exist
Path(DATA_STAGING).mkdir(parents=True, exist_ok=True)
Path(STAGING_DIR).mkdir(parents=True, exist_ok=True)


def download_leie_csv(force_refresh: bool = False) -> str:
    """
    Download OIG LEIE CSV file with fallback URLs.
    
    Args:
        force_refresh: If True, re-download even if file exists
        
    Returns:
        Path to downloaded CSV file
        
    Raises:
        FileNotFoundError: If all download attempts fail and no cached file exists
    """
    # Check if file exists and is recent (within 30 days)
    if os.path.exists(OIG_LEIE_RAW) and not force_refresh:
        file_age = time.time() - os.path.getmtime(OIG_LEIE_RAW)
        if file_age < 30 * 24 * 60 * 60:  # 30 days in seconds
            print(f"Using cached LEIE file (age: {file_age / (24*60*60):.1f} days)")
            return OIG_LEIE_RAW
    
    # Try each URL in order
    last_error = None
    for i, url in enumerate(OIG_LEIE_URLS, 1):
        try:
            print(f"Attempting to download OIG LEIE from URL {i}/{len(OIG_LEIE_URLS)}: {url}")
            response = requests.get(
                url,
                timeout=60,
                allow_redirects=True,  # Follow redirects (302, etc.)
                headers={
                    "User-Agent": "ChartaHealth/1.0 (compliance-checker)"
                }
            )
            response.raise_for_status()
            
            # Verify we got actual CSV content (not HTML error page)
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" in content_type:
                print(f"  ✗ URL returned HTML instead of CSV (status {response.status_code}), trying next URL...")
                continue
            
            # Check if content looks like CSV (starts with expected headers or is reasonable size)
            content_preview = response.content[:200].decode("utf-8", errors="ignore")
            if len(response.content) < 1000:  # Too small to be real data
                print(f"  ✗ Downloaded content too small ({len(response.content)} bytes), trying next URL...")
                continue
            
            # Save to file
            with open(OIG_LEIE_RAW, "wb") as f:
                f.write(response.content)
            
            print(f"✓ Successfully downloaded {len(response.content):,} bytes from {url}")
            print(f"  Saved to: {OIG_LEIE_RAW}")
            return OIG_LEIE_RAW
            
        except requests.exceptions.HTTPError as e:
            last_error = e
            if e.response.status_code == 404:
                print(f"  ✗ URL returned 404 (not found), trying next URL...")
            else:
                print(f"  ✗ HTTP error {e.response.status_code}: {e}, trying next URL...")
            continue
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"  ✗ Request failed: {e}, trying next URL...")
            continue
    
    # All URLs failed - check for existing cached file
    if os.path.exists(OIG_LEIE_RAW):
        print(f"\n⚠ Warning: All download URLs failed. Using existing cached file: {OIG_LEIE_RAW}")
        print(f"  Last error: {last_error}")
        return OIG_LEIE_RAW
    
    # No cached file and all downloads failed
    error_msg = f"Failed to download LEIE from all URLs. Last error: {last_error}"
    print(f"\n✗ {error_msg}")
    raise FileNotFoundError(error_msg)


def load_leie_data(csv_path: str) -> pd.DataFrame:
    """
    Load and parse OIG LEIE CSV.
    
    Expected columns:
    - NPI (may be empty)
    - First Name
    - Last Name
    - Business Name
    - Exclusion Date
    - Exclusion Type
    """
    print(f"Loading LEIE data from {csv_path}...")
    
    try:
        # Try reading with different encodings
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(
                    csv_path,
                    encoding=encoding,
                    encoding_errors="ignore",  # pandas 2.0+ uses encoding_errors
                    low_memory=False,
                    dtype=str
                )
                break
            except (UnicodeDecodeError, TypeError):
                # If encoding_errors doesn't work, try without it (older pandas)
                try:
                    df = pd.read_csv(
                        csv_path,
                        encoding=encoding,
                        low_memory=False,
                        dtype=str,
                        on_bad_lines="skip"  # pandas 1.3+
                    )
                    break
                except (UnicodeDecodeError, TypeError):
                    continue
        else:
            raise ValueError("Could not decode LEIE CSV with any encoding")
        
        # Normalize column names (handle variations)
        df.columns = df.columns.str.strip().str.lower()
        
        # Map common column name variations
        column_map = {
            "npi": ["npi", "national provider identifier"],
            "first_name": ["first name", "firstname", "first"],
            "last_name": ["last name", "lastname", "last"],
            "business_name": ["business name", "businessname", "entity name", "entity"],
            "exclusion_date": ["exclusion date", "exclusiondate", "date"],
            "exclusion_type": ["exclusion type", "exclusiontype", "type"],
        }
        
        normalized_cols = {}
        for target, variants in column_map.items():
            for col in df.columns:
                if any(variant in col.lower() for variant in variants):
                    normalized_cols[col] = target
                    break
        
        df = df.rename(columns=normalized_cols)
        
        # Ensure required columns exist (fill with empty if missing)
        for col in ["npi", "first_name", "last_name", "business_name", "exclusion_date", "exclusion_type"]:
            if col not in df.columns:
                df[col] = ""
        
        # Clean NPI: remove non-digits, pad to 10 digits
        df["npi"] = df["npi"].astype(str).str.replace(r"[^0-9]", "", regex=True).str.zfill(10)
        df.loc[df["npi"] == "0000000000", "npi"] = ""
        
        # Clean business names
        df["business_name"] = df["business_name"].astype(str).str.strip().str.upper()
        df.loc[df["business_name"] == "NAN", "business_name"] = ""
        
        print(f"Loaded {len(df)} LEIE records")
        return df
    
    except Exception as e:
        print(f"Error loading LEIE CSV: {e}")
        raise


def load_clinic_data() -> pd.DataFrame:
    """Load clinic data with NPIs and names for matching."""
    # Try multiple sources
    sources = [
        os.path.join(STAGING_DIR, "stg_npi_orgs.parquet"),
        os.path.join(STAGING_DIR, "stg_npi_orgs.csv"),
        os.path.join(DATA_CURATED, "clinics_seed.csv"),
    ]
    
    for source in sources:
        if os.path.exists(source):
            print(f"Loading clinic data from {source}...")
            try:
                if source.endswith(".parquet"):
                    df = pd.read_parquet(source)
                else:
                    df = pd.read_csv(source, low_memory=False)
                
                # Ensure we have required columns
                if "npi" not in df.columns:
                    print(f"Warning: {source} does not have 'npi' column")
                    continue
                
                if "clinic_id" not in df.columns:
                    # Generate clinic_id if missing
                    if "org_name" in df.columns and "state" in df.columns:
                        df["clinic_id"] = (
                            df["org_name"].astype(str) + "-" + df["state"].astype(str)
                        ).str.lower().str.replace(r"[^a-z0-9-]", "-", regex=True)
                    else:
                        df["clinic_id"] = df["npi"].astype(str)
                
                # Normalize NPI
                df["npi"] = df["npi"].astype(str).str.replace(r"[^0-9]", "", regex=True).str.zfill(10)
                
                # Get clinic name
                if "org_name" in df.columns:
                    df["clinic_name"] = df["org_name"].astype(str).str.strip().str.upper()
                elif "account_name" in df.columns:
                    df["clinic_name"] = df["account_name"].astype(str).str.strip().str.upper()
                else:
                    df["clinic_name"] = ""
                
                # Keep only relevant columns
                keep_cols = ["clinic_id", "npi", "clinic_name"]
                df = df[[c for c in keep_cols if c in df.columns]].copy()
                
                print(f"Loaded {len(df)} clinic records")
                return df
            except Exception as e:
                print(f"Error loading {source}: {e}")
                continue
    
    raise FileNotFoundError("Could not find clinic data file. Run ingest_api first.")


def match_exact_npi(clinics: pd.DataFrame, leie: pd.DataFrame) -> pd.DataFrame:
    """Match clinics to LEIE by exact NPI."""
    # Filter LEIE to records with NPIs
    leie_with_npi = leie[leie["npi"].str.len() == 10].copy()
    if leie_with_npi.empty:
        return pd.DataFrame()
    
    # Merge on NPI
    matches = clinics.merge(
        leie_with_npi[["npi", "business_name", "exclusion_date", "exclusion_type"]],
        on="npi",
        how="inner",
        suffixes=("_clinic", "_leie")
    )
    
    if not matches.empty:
        matches["match_type"] = "exact_npi"
        matches["match_confidence"] = 100
        matches["leie_npi"] = matches["npi"]
        matches = matches.rename(columns={"business_name": "leie_business_name"})
    
    return matches


def match_fuzzy_name(
    clinics: pd.DataFrame,
    leie: pd.DataFrame,
    threshold: int = 85
) -> pd.DataFrame:
    """
    Match clinics to LEIE by fuzzy name matching.
    
    Args:
        clinics: Clinic dataframe with clinic_name
        leie: LEIE dataframe with business_name
        threshold: Minimum fuzzy match score (0-100)
    
    Returns:
        DataFrame with matches
    """
    # Filter to clinics not already matched and with names
    clinics_unmatched = clinics[
        clinics["clinic_name"].str.len() > 3
    ].copy()
    
    # Filter LEIE to records with business names
    leie_with_names = leie[
        leie["business_name"].str.len() > 3
    ].copy()
    
    if clinics_unmatched.empty or leie_with_names.empty:
        return pd.DataFrame()
    
    matches = []
    
    print(f"Fuzzy matching {len(clinics_unmatched)} clinics against {len(leie_with_names)} LEIE entities...")
    
    # Use a sample for testing (first 1000) if dataset is large
    sample_size = min(1000, len(clinics_unmatched))
    if len(clinics_unmatched) > 1000:
        print(f"Sampling first {sample_size} clinics for fuzzy matching (full run will process all)")
        clinics_sample = clinics_unmatched.head(sample_size)
    else:
        clinics_sample = clinics_unmatched
    
    for _, clinic in clinics_sample.iterrows():
        clinic_name = clinic["clinic_name"]
        if not clinic_name or len(clinic_name) < 3:
            continue
        
        best_match = None
        best_score = 0
        
        for _, leie_row in leie_with_names.iterrows():
            leie_name = leie_row["business_name"]
            if not leie_name or len(leie_name) < 3:
                continue
            
            # Use ratio for fuzzy matching
            score = fuzz.ratio(clinic_name, leie_name)
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = leie_row
        
        if best_match is not None:
            matches.append({
                "clinic_id": clinic["clinic_id"],
                "clinic_npi": clinic["npi"],
                "clinic_name": clinic_name,
                "leie_npi": best_match.get("npi", ""),
                "leie_business_name": best_match["business_name"],
                "exclusion_type": best_match.get("exclusion_type", ""),
                "exclusion_date": best_match.get("exclusion_date", ""),
                "match_type": "fuzzy_name",
                "match_confidence": best_score,
            })
    
    if matches:
        return pd.DataFrame(matches)
    return pd.DataFrame()


def main():
    """Main enrichment function."""
    print("=" * 60)
    print("OIG LEIE Enrichment Worker")
    print("=" * 60)
    
    # Download LEIE data
    try:
        leie_path = download_leie_csv()
        leie_df = load_leie_data(leie_path)
    except Exception as e:
        print(f"Failed to load LEIE data: {e}")
        return
    
    # Load clinic data
    try:
        clinics_df = load_clinic_data()
    except Exception as e:
        print(f"Failed to load clinic data: {e}")
        return
    
    # Remove duplicates from clinics (keep first)
    clinics_df = clinics_df.drop_duplicates(subset=["clinic_id"], keep="first")
    
    print(f"\nMatching {len(clinics_df)} clinics against LEIE...")
    
    # Match by exact NPI
    exact_matches = match_exact_npi(clinics_df, leie_df)
    exact_count = len(exact_matches)
    print(f"Found {exact_count} exact NPI matches")
    
    # Match by fuzzy name (exclude already matched)
    if exact_count > 0:
        matched_clinic_ids = set(exact_matches["clinic_id"])
        clinics_unmatched = clinics_df[~clinics_df["clinic_id"].isin(matched_clinic_ids)]
    else:
        clinics_unmatched = clinics_df
    
    fuzzy_matches = match_fuzzy_name(clinics_unmatched, leie_df, threshold=85)
    fuzzy_count = len(fuzzy_matches)
    print(f"Found {fuzzy_count} fuzzy name matches (threshold: 85%)")
    
    # Combine matches
    if exact_count > 0 and fuzzy_count > 0:
        all_matches = pd.concat([exact_matches, fuzzy_matches], ignore_index=True)
    elif exact_count > 0:
        all_matches = exact_matches
    elif fuzzy_count > 0:
        all_matches = fuzzy_matches
    else:
        all_matches = pd.DataFrame(columns=[
            "clinic_id", "clinic_npi", "clinic_name",
            "leie_npi", "leie_business_name",
            "exclusion_type", "exclusion_date",
            "match_type", "match_confidence"
        ])
    
    # Save matches
    if not all_matches.empty:
        all_matches.to_csv(OIG_LEIE_MATCHES, index=False)
        print(f"\nSaved {len(all_matches)} matches to {OIG_LEIE_MATCHES}")
        
        # Print sample matches for review
        print("\nSample matches (first 10):")
        for _, match in all_matches.head(10).iterrows():
            print(f"  {match['clinic_name'][:40]:<40} | {match['leie_business_name'][:40]:<40} | {match['match_type']} ({match.get('match_confidence', 100)})")
    else:
        # Create empty file with headers
        pd.DataFrame(columns=[
            "clinic_id", "clinic_npi", "clinic_name",
            "leie_npi", "leie_business_name",
            "exclusion_type", "exclusion_date",
            "match_type", "match_confidence"
        ]).to_csv(OIG_LEIE_MATCHES, index=False)
        print(f"\nNo matches found. Created empty file: {OIG_LEIE_MATCHES}")
    
    print(f"\nSummary:")
    print(f"  Exact NPI matches: {exact_count}")
    print(f"  Fuzzy name matches: {fuzzy_count}")
    print(f"  Total matches: {len(all_matches)}")
    print(f"  Match rate: {len(all_matches) / len(clinics_df) * 100:.2f}%")


if __name__ == "__main__":
    main()

