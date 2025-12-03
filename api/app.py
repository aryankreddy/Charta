# api/app.py
import os
import time
from functools import lru_cache
from typing import List, Dict, Any, Optional

import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Charta Clinic Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Paths --------------------------------------------------------------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CURATED = os.path.join(ROOT, "data", "curated")
STAGING = os.path.join(CURATED, "staging")
PRIMARY_FILE = os.path.join(CURATED, "clinics_scored.csv")
FALLBACK_FILE = os.path.join(CURATED, "scores_seed.csv")
ICP_SCORES_FILE = os.path.join(CURATED, "icp_scores.csv")
NETWORKS_ICP_FILE = os.path.join(CURATED, "networks_icp.csv")


def _derive_display_name_from_id(clinic_id: str) -> str:
    if not isinstance(clinic_id, str) or clinic_id.strip() == "":
        return "Unknown"
    parts = clinic_id.rsplit("-", 1)
    base = parts[0] if len(parts) == 2 and len(parts[1]) in (2, 3) else clinic_id
    return base.replace("-", " ").title()


def load_clinics() -> pd.DataFrame:
    # Prefer enriched file; fallback to seed
    path = PRIMARY_FILE if os.path.exists(PRIMARY_FILE) else FALLBACK_FILE
    if not os.path.exists(path):
        return pd.DataFrame()

    dtypes = {
        "clinic_id": "string",
        "account_name": "string",
        "org_name": "string",
        "state_code": "string",
    }
    df = pd.read_csv(path, dtype=dtypes, low_memory=False)

    # Make a robust display_name
    if "display_name" not in df.columns:
        if "org_name" in df.columns:
            disp = df["account_name"].fillna("").replace("", pd.NA)
            df["display_name"] = disp.fillna(df["org_name"]).fillna("Unknown")
        elif "account_name" in df.columns:
            df["display_name"] = df["account_name"].fillna("Unknown")
        else:
            # derive from clinic_id
            df["display_name"] = df["clinic_id"].fillna("").apply(_derive_display_name_from_id)

    if "icf_score" not in df.columns:
        df["icf_score"] = 0.0

    # Normalize state_code
    if "state_code" in df.columns:
        df["state_code"] = df["state_code"].fillna("").str.upper().str[:2]

    # Merge ICP scores if available (prefer clinics_icp_with_networks for network data)
    clinics_with_networks_file = os.path.join(CURATED, "clinics_icp_with_networks.csv")
    
    if os.path.exists(clinics_with_networks_file):
        try:
            icp_df = pd.read_csv(clinics_with_networks_file, dtype={"clinic_id": "string", "network_id": "string"}, low_memory=False)
            
            # Select ICP columns to merge (including network fields)
            icp_cols = [
                "clinic_id",
                "icp_total_score",
                "icp_tier",
                "icp_tier_label", 
                "icp_segment",
                "icp_fit_score",
                "icp_pain_score",
                "icp_compliance_score",
                "icp_propensity_score",
                "icp_scale_score",
                "icp_segment_score",
                "icp_bibliography",
                "network_id",
                "network_name",
                "network_icp_score",
                "network_tier",
                "network_tier_label",
                "is_network_anchor",
                "num_clinics",
            ]
            # Only keep columns that exist in icp_df
            icp_cols = [col for col in icp_cols if col in icp_df.columns]
            
            if icp_cols and "clinic_id" in icp_cols:
                df = df.merge(icp_df[icp_cols], on="clinic_id", how="left")
                print(f"✓ Merged ICP scores with network data for {df['icp_total_score'].notna().sum():,} clinics")
                if 'network_id' in df.columns:
                    print(f"✓ Network data: {df['network_id'].notna().sum():,} clinics in networks")
        except Exception as e:
            print(f"⚠️  Could not merge ICP scores with networks: {e}")
    elif os.path.exists(ICP_SCORES_FILE):
        try:
            icp_df = pd.read_csv(ICP_SCORES_FILE, dtype={"clinic_id": "string"}, low_memory=False)
            
            # Select ICP columns to merge
            icp_cols = [
                "clinic_id",
                "icp_total_score",
                "icp_tier",
                "icp_tier_label", 
                "icp_segment",
                "icp_fit_score",
                "icp_pain_score",
                "icp_compliance_score",
                "icp_propensity_score",
                "icp_scale_score",
                "icp_segment_score",
                "icp_bibliography",
            ]
            # Only keep columns that exist in icp_df
            icp_cols = [col for col in icp_cols if col in icp_df.columns]
            
            if icp_cols and "clinic_id" in icp_cols:
                df = df.merge(icp_df[icp_cols], on="clinic_id", how="left")
                print(f"✓ Merged ICP scores for {df['icp_total_score'].notna().sum():,} clinics")
        except Exception as e:
            print(f"⚠️  Could not merge ICP scores: {e}")

    return df


@lru_cache(maxsize=8)
def load_staging(filename: str) -> pd.DataFrame:
    """Load parquet or csv from /data/curated/staging with a small cache."""
    path = os.path.join(STAGING, filename)
    csv_path = path.replace(".parquet", ".csv")
    if os.path.exists(csv_path):
        try:
            return pd.read_csv(csv_path, low_memory=False)
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
    if os.path.exists(path):
        try:
            return pd.read_parquet(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


@app.get("/health")
def health() -> Dict[str, Any]:
    src = PRIMARY_FILE if os.path.exists(PRIMARY_FILE) else (FALLBACK_FILE if os.path.exists(FALLBACK_FILE) else None)
    df = load_clinics()
    return {"ok": True, "source": src, "rows": int(df.shape[0])}


@app.get("/clinics")
def clinics(
    limit: int = Query(200, ge=0),  # 0 means no limit, return all
    min_score: float = Query(0.0, ge=0, le=100),
    state: str = Query("", max_length=2),
    q: str = Query("", max_length=120),
    score_type: str = Query("icp", regex="^(icf|icp)$"),  # Which score to use for filtering/sorting
):
    df = load_clinics().copy()
    if df.empty:
        return {"total": 0, "rows": []}

    # Determine which score column to use
    score_col = "icp_total_score" if score_type == "icp" and "icp_total_score" in df.columns else "icf_score"

    # filters
    if min_score > 0:
        if score_col in df.columns:
            df = df[df[score_col] >= min_score]
    if state:
        df = df[df["state_code"] == state.upper()]
    if q:
        qlower = q.strip().lower()
        cols = [c for c in ["display_name", "account_name", "org_name", "clinic_id"] if c in df.columns]
        if cols:
            mask = False
            for c in cols:
                mask = mask | df[c].astype(str).str.lower().str.contains(qlower, na=False)
            df = df[mask]

    # Sort by the selected score type
    if score_col in df.columns:
        df = df.sort_values(score_col, ascending=False, na_position='last')

    total = len(df)
    # Apply limit only if > 0 (0 means return all)
    if limit > 0:
        df = df.head(limit)

    keep = [c for c in [
        "clinic_id","display_name","org_name","state_code","icf_score",
        "segment","sector","segment_label",
        "structural_fit_score","propensity_score","icf_tier","tier",
        "primary_driver","primary_pain_driver","tier_rationale",
        "fit_chart_volume_complexity","fit_billing_model_fit","fit_emr_integration","fit_coding_setup",
        "prop_denial_pressure","prop_cash_flow_strain","prop_compliance_exposure","prop_workforce_crisis","prop_change_readiness",
        "segment_fit","scale_velocity","emr_friction","coding_complexity",
        "denial_pressure","roi_readiness","aco_member","org_like","site_count",
        "fqhc_flag","pecos_enrolled","services_count","allowed_amt","bene_count",
        # ICP fields
        "icp_total_score","icp_tier","icp_tier_label","icp_segment",
        "icp_fit_score","icp_pain_score","icp_compliance_score",
        "icp_propensity_score","icp_scale_score","icp_segment_score",
        "icp_bibliography"
    ] if c in df.columns]
    records = df[keep].to_dict(orient="records")
    # Normalize GTM fields for proper JSON serialization
    records = [normalize_gtm_fields(r) for r in records]
    return {"total": total, "rows": records}


def normalize_gtm_fields(record: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize GTM intelligence fields to proper types, handling NaN/None."""
    float_fields = [
        "icf_score",
        "structural_fit_score",
        "propensity_score",
        "fit_chart_volume_complexity",
        "fit_billing_model_fit",
        "fit_emr_integration",
        "fit_coding_setup",
        "prop_denial_pressure",
        "prop_cash_flow_strain",
        "prop_compliance_exposure",
        "prop_workforce_crisis",
        "prop_change_readiness",
        # ICP float fields
        "icp_total_score",
        "icp_fit_score",
        "icp_pain_score",
        "icp_compliance_score",
        "icp_propensity_score",
        "icp_scale_score",
        "icp_segment_score",
    ]
    for field in float_fields:
        if field in record:
            val = record[field]
            record[field] = float(val) if pd.notna(val) and val is not None else None

    int_fields = ["icf_tier", "tier", "icp_tier"]
    for field in int_fields:
        if field in record:
            val = record[field]
            record[field] = int(float(val)) if pd.notna(val) and val is not None else None

    str_fields = ["segment_label", "primary_driver", "primary_pain_driver", "tier_rationale", "icp_tier_label", "icp_segment", "icp_bibliography"]
    for field in str_fields:
        if field in record:
            val = record[field]
            record[field] = str(val) if pd.notna(val) and val is not None else None

    return record


def build_driver_payload(row: pd.Series) -> List[dict]:
    drivers = []
    mapping = {
        "segment_fit": "Segment Fit",
        "scale_velocity": "Scale & Velocity",
        "emr_friction": "Integration Ease",
        "coding_complexity": "Coding Complexity",
        "denial_pressure": "Denial Pressure",
        "roi_readiness": "ROI Readiness",
    }
    for key, label in mapping.items():
        if key in row:
            drivers.append({"axis": key, "label": label, "score": float(row.get(key, 0) or 0)})
    return drivers


@app.get("/clinics/top-targets")
def top_targets(
    tier: str = Query("1,2", description="Comma-separated tier values (e.g., '1,2' for Tier 1 and 2)"),
    limit: int = Query(5000, ge=1, le=50000),
    score_type: str = Query("icp", regex="^(icf|icp)$"),  # Which scoring system to use
):
    """
    Get top target clinics filtered by tier.
    
    Default: Returns Tier 1 and Tier 2 clinics, sorted by ICP total score DESC.
    Perfect for demo UI showing high-value targets.
    
    Returns up to 5,000 clinics by default (configurable via limit parameter).
    """
    df = load_clinics().copy()
    if df.empty:
        return {"total": 0, "rows": [], "message": "No clinic data available"}
    
    # Parse tier filter (e.g., "1,2" -> [1, 2])
    try:
        tier_values = [int(t.strip()) for t in tier.split(",") if t.strip().isdigit()]
    except (ValueError, AttributeError):
        tier_values = [1, 2]  # Default to Tier 1 and 2
    
    if not tier_values:
        tier_values = [1, 2]
    
    # Filter by tier (prefer ICP tier if available, fallback to ICF tier)
    if score_type == "icp" and "icp_tier" in df.columns:
        tier_col = "icp_tier"
        sort_col = "icp_total_score"
    else:
        tier_col = "tier" if "tier" in df.columns else "icf_tier"
        sort_col = "icf_score"
    
    if tier_col not in df.columns:
        return {"total": 0, "rows": [], "message": "Tier column not found in data"}
    
    df = df[df[tier_col].isin(tier_values)]
    
    # Sort by selected score type
    if sort_col in df.columns:
        df = df.sort_values(sort_col, ascending=False, na_position='last')
    
    total = len(df)
    
    # Apply limit
    if limit > 0:
        df = df.head(limit)
    
    # Count by tier for summary
    tier_counts = {}
    if tier_col in df.columns:
        tier_counts = df[tier_col].value_counts().to_dict()
    
    keep = [c for c in [
        "clinic_id","display_name","org_name","state_code","icf_score",
        "segment","sector","segment_label",
        "structural_fit_score","propensity_score","icf_tier","tier",
        "primary_driver","primary_pain_driver","tier_rationale",
        "fit_chart_volume_complexity","fit_billing_model_fit","fit_emr_integration","fit_coding_setup",
        "prop_denial_pressure","prop_cash_flow_strain","prop_compliance_exposure","prop_workforce_crisis","prop_change_readiness",
        "segment_fit","scale_velocity","emr_friction","coding_complexity",
        "denial_pressure","roi_readiness","aco_member","org_like","site_count",
        "fqhc_flag","pecos_enrolled","services_count","allowed_amt","bene_count",
        # ICP fields
        "icp_total_score","icp_tier","icp_tier_label","icp_segment",
        "icp_fit_score","icp_pain_score","icp_compliance_score",
        "icp_propensity_score","icp_scale_score","icp_segment_score",
        "icp_bibliography"
    ] if c in df.columns]
    records = df[keep].to_dict(orient="records")
    # Normalize GTM fields for proper JSON serialization
    records = [normalize_gtm_fields(r) for r in records]
    return {
        "total": total,
        "returned": len(records),
        "rows": records,
        "tiers": tier_values,
        "tier_counts": tier_counts,
        "score_type": score_type,
        "message": f"Showing top {len(records):,} of {total:,} Tier {','.join(map(str, tier_values))} clinics"
    }


@app.get("/clinics/{clinic_id}/score-breakdown")
def clinic_score_breakdown(clinic_id: str) -> Dict[str, Any]:
    df = load_clinics()
    if df.empty:
        raise HTTPException(status_code=404, detail="Clinic not found")

    match = df[df["clinic_id"] == clinic_id]
    if match.empty:
        raise HTTPException(status_code=404, detail="Clinic not found")

    row = match.iloc[0]

    structural_components = {
        "chart_volume_complexity": float(row.get("fit_chart_volume_complexity", 0.0) or 0.0),
        "billing_model_fit": float(row.get("fit_billing_model_fit", 0.0) or 0.0),
        "emr_integration": float(row.get("fit_emr_integration", 0.0) or 0.0),
        "coding_setup": float(row.get("fit_coding_setup", 0.0) or 0.0),
    }

    propensity_components = {
        "denial_pressure": float(row.get("prop_denial_pressure", 0.0) or 0.0),
        "cash_flow_strain": float(row.get("prop_cash_flow_strain", 0.0) or 0.0),
        "compliance_exposure": float(row.get("prop_compliance_exposure", 0.0) or 0.0),
        "workforce_crisis": float(row.get("prop_workforce_crisis", 0.0) or 0.0),
        "change_readiness": float(row.get("prop_change_readiness", 0.0) or 0.0),
    }

    primary_driver = row.get("primary_pain_driver") or row.get("primary_driver") or ""
    try:
        tier_value = int(float(row.get("tier") or row.get("icf_tier") or 3))
    except (TypeError, ValueError):
        tier_value = 0

    response = {
        "clinic_id": clinic_id,
        "structural_fit": {
            "score": float(row.get("structural_fit_score", 0.0) or 0.0),
            "components": structural_components,
        },
        "propensity": {
            "score": float(row.get("propensity_score", 0.0) or 0.0),
            "components": propensity_components,
            "primary_pain_driver": str(primary_driver) if primary_driver else None,
        },
        "tier": tier_value,
        "tier_rationale": str(row.get("tier_rationale") or ""),
    }

    return response


@app.get("/clinics/{clinic_id}")
def clinic_detail(clinic_id: str):
    df = load_clinics()
    if df.empty:
        return {"clinic": None}
    match = df[df["clinic_id"] == clinic_id]
    if match.empty:
        return {"clinic": None}
    row = match.iloc[0].copy()
    if "display_name" not in row or not row["display_name"]:
        row["display_name"] = _derive_display_name_from_id(row.get("clinic_id", ""))
    payload = row.to_dict()
    
    # Normalize GTM intelligence fields for proper JSON serialization
    payload = normalize_gtm_fields(payload)
    
    payload["drivers"] = build_driver_payload(row)
    return {"clinic": payload}


# --- Campaign Generation ------------------------------------------------------

# Lazy import to avoid requiring openai if not used
def get_campaign_generator():
    """Lazy load campaign generator to avoid import errors if openai not installed."""
    try:
        from api.campaign_generator import CampaignGenerator
        from workers.campaign_prompts import infer_segment_from_clinic
        return CampaignGenerator(), infer_segment_from_clinic
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Campaign generation unavailable. Install openai package: pip install openai. Error: {str(e)}"
        )


@app.post("/campaigns/generate")
def generate_campaign(clinic_id: str, segment_override: Optional[str] = None):
    """
    Generate a personalized 7-email campaign sequence for a clinic.
    
    Args:
        clinic_id: Clinic identifier
        segment_override: Optional segment override ("A", "B", or "C")
        
    Returns:
        Campaign data with email sequence, call script, talking points, etc.
    """
    # Load campaign generator
    campaign_gen, infer_segment = get_campaign_generator()
    
    # Find clinic in scored data
    df = load_clinics()
    if df.empty:
        raise HTTPException(status_code=503, detail="Clinic data not available")
    
    match = df[df["clinic_id"] == clinic_id]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Clinic {clinic_id} not found")
    
    clinic_data_raw = match.iloc[0].to_dict()
    
    # Determine segment (auto-detect or use override)
    segment = segment_override or infer_segment(clinic_data_raw)
    if segment not in ["A", "B", "C"]:
        segment = "A"  # Fallback
    
    # Map clinic fields to campaign generator expected format
    campaign_input = {
        "clinic_name": clinic_data_raw.get("display_name") or clinic_data_raw.get("org_name") or clinic_data_raw.get("account_name") or "Your Clinic",
        "specialty": clinic_data_raw.get("segment_label") or clinic_data_raw.get("segment") or "healthcare",
        "state": clinic_data_raw.get("state_code", "US"),
        "provider_count": int(clinic_data_raw.get("npi_count") or clinic_data_raw.get("site_count") or 50),
        "pain_driver": clinic_data_raw.get("primary_pain_driver") or clinic_data_raw.get("primary_driver") or "operational efficiency",
        "denial_rate": 15 if segment == "A" else 12,  # Estimated based on segment
        "ar_days": 70 if segment == "A" else 65,
        "patient_population": "Medicaid-heavy" if clinic_data_raw.get("fqhc_flag") else "mixed payer",
        "trigger": "UDS reporting pressure" if clinic_data_raw.get("fqhc_flag") else "recent growth",
        "compliance_risk": "audit exposure" if clinic_data_raw.get("oig_leie_flag") else "standard compliance",
        "investor": "PE-backed" if segment == "C" else "Independent",
        "recent_event": "recent acquisitions" if segment == "C" else "operational changes",
        "margin_pressure": "EBITDA optimization" if segment == "C" else "margin improvement"
    }
    
    # Generate campaign
    result = campaign_gen.generate_campaign(segment, campaign_input)
    
    if result["status"] == "success":
        campaign_data = result["campaign"]
        return {
            "campaign_id": f"camp_{clinic_id}_{int(time.time())}",
            "clinic_id": clinic_id,
            "clinic_name": campaign_input["clinic_name"],
            "segment": segment,
            "tier": int(clinic_data_raw.get("icf_tier") or clinic_data_raw.get("tier") or 3),
            "email_sequence": campaign_data.get("emails", []),
            "call_script": campaign_data.get("call_script"),
            "talking_points": campaign_data.get("talking_points", []),
            "objection_handlers": campaign_data.get("objection_handlers", {}),
            "pilot_offer": campaign_data.get("pilot_offer", "Free clinic assessment"),
            "tokens_used": result.get("tokens_used", 0),
            "cost_estimate": result.get("cost_estimate", 0.0)
        }
    else:
        raise HTTPException(
            status_code=500,
            detail={
                "error": result.get("error"),
                "type": result.get("type"),
                "detail": result.get("detail")
            }
        )


# ============================================================================
# ICP SCORING ENDPOINTS
# ============================================================================

ICP_FILE = os.path.join(CURATED, "clinics_icp.csv")
ICP_SCORES_FILE = os.path.join(CURATED, "icp_scores.csv")


@lru_cache(maxsize=1)
def load_icp_data() -> pd.DataFrame:
    """Load ICP scored clinic data."""
    if os.path.exists(ICP_FILE):
        return pd.read_csv(ICP_FILE, low_memory=False)
    return pd.DataFrame()


@app.get("/icp/clinics")
def get_icp_clinics(
    tier: Optional[int] = Query(None, description="Filter by ICP tier (1, 2, or 3)"),
    segment: Optional[str] = Query(None, description="Filter by segment (A, B, or C)"),
    state: Optional[str] = Query(None, description="Filter by state code"),
    min_score: Optional[float] = Query(None, description="Minimum ICP score (0-100)"),
    limit: Optional[int] = Query(100, le=10000, description="Max results"),
    offset: Optional[int] = Query(0, description="Pagination offset")
) -> Dict[str, Any]:
    """
    Get clinics with ICP scores.
    
    Returns clinics scored using the 6-category ICP model:
    - Fit Score (0-20)
    - Pain Score (0-20)
    - Compliance Risk Score (0-10)
    - Propensity to Buy Score (0-10)
    - Operational Scale Score (0-20)
    - Strategic Segment Score (0-20)
    
    Total ICP Score: 0-100
    """
    df = load_icp_data()
    
    if df.empty:
        return {
            "total": 0,
            "limit": limit,
            "offset": offset,
            "clinics": [],
            "message": "No ICP data available. Run 'python workers/score_icp.py' first."
        }
    
    # Apply filters
    filtered = df.copy()
    
    if tier is not None:
        filtered = filtered[filtered["icp_tier"] == tier]
    
    if segment is not None:
        segment_upper = segment.upper()
        filtered = filtered[filtered["icp_segment"] == segment_upper]
    
    if state is not None:
        state_upper = state.upper()
        filtered = filtered[filtered["state_code"] == state_upper]
    
    if min_score is not None:
        filtered = filtered[filtered["icp_total_score"] >= min_score]
    
    # Sort by ICP score descending
    filtered = filtered.sort_values("icp_total_score", ascending=False)
    
    total = len(filtered)
    
    # Pagination
    paginated = filtered.iloc[offset:offset + limit]
    
    # Select columns to return
    output_columns = [
        "clinic_id", "account_name", "state_code", "segment_label",
        "icp_total_score", "icp_tier", "icp_tier_label", "icp_segment",
        "icp_fit_score", "icp_pain_score", "icp_compliance_score",
        "icp_propensity_score", "icp_scale_score", "icp_segment_score",
        "fqhc_flag", "aco_flag",  # Add flags for filtering
        "npi_count", "site_count", "bene_count", "allowed_amt"
    ]
    available_columns = [col for col in output_columns if col in paginated.columns]
    
    clinics = paginated[available_columns].fillna("").to_dict(orient="records")
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "clinics": clinics
    }


@app.get("/icp/clinic/{clinic_id}")
def get_icp_clinic_detail(clinic_id: str) -> Dict[str, Any]:
    """
    Get detailed ICP scoring breakdown for a specific clinic.
    
    Includes:
    - Full score breakdown
    - Tier assignment
    - Segment classification
    - Bibliography (data sources used for scoring)
    """
    df = load_icp_data()
    
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="No ICP data available. Run 'python workers/score_icp.py' first."
        )
    
    clinic = df[df["clinic_id"] == clinic_id]
    
    if clinic.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Clinic {clinic_id} not found in ICP dataset"
        )
    
    row = clinic.iloc[0]
    
    # Parse bibliography
    bibliography_raw = row.get("icp_bibliography", "[]")
    try:
        import ast
        bibliography = ast.literal_eval(bibliography_raw)
    except:
        bibliography = []
    
    return {
        "clinic_id": row.get("clinic_id"),
        "account_name": row.get("account_name"),
        "state_code": row.get("state_code"),
        "segment_label": row.get("segment_label"),
        "icp_score": {
            "total": float(row.get("icp_total_score", 0)),
            "breakdown": {
                "fit": float(row.get("icp_fit_score", 0)),
                "pain": float(row.get("icp_pain_score", 0)),
                "compliance_risk": float(row.get("icp_compliance_score", 0)),
                "propensity_to_buy": float(row.get("icp_propensity_score", 0)),
                "operational_scale": float(row.get("icp_scale_score", 0)),
                "strategic_segment": float(row.get("icp_segment_score", 0))
            }
        },
        "tier": {
            "number": int(row.get("icp_tier", 3)),
            "label": row.get("icp_tier_label", "Tier 3 - Monitor")
        },
        "segment": {
            "letter": row.get("icp_segment", "C"),
            "description": _get_segment_description(row.get("icp_segment", "C"))
        },
        "operational_data": {
            "npi_count": int(row.get("npi_count", 0)) if pd.notna(row.get("npi_count")) else 0,
            "site_count": int(row.get("site_count", 0)) if pd.notna(row.get("site_count")) else 0,
            "bene_count": int(row.get("bene_count", 0)) if pd.notna(row.get("bene_count")) else 0,
            "allowed_amt": float(row.get("allowed_amt", 0)) if pd.notna(row.get("allowed_amt")) else 0,
            "fqhc_flag": bool(row.get("fqhc_flag", 0)),
            "aco_member": bool(row.get("aco_member", 0)),
            "pecos_enrolled": bool(row.get("pecos_enrolled", 0))
        },
        "bibliography": bibliography
    }


def _get_segment_description(segment: str) -> str:
    """Get human-readable description of ICP segment."""
    descriptions = {
        "A": "Behavioral Health / Home Health / Hospice",
        "B": "FQHC / Rural Health Clinic / HRSA Grantee",
        "C": "Multi-Specialty / Growth / PE-Backed"
    }
    return descriptions.get(segment, "Unknown")


@app.get("/icp/stats")
def get_icp_statistics() -> Dict[str, Any]:
    """
    Get aggregate statistics about ICP scoring distribution.
    
    Returns:
    - Tier distribution
    - Segment distribution
    - Score distribution stats
    - Top scoring clinics
    """
    df = load_icp_data()
    
    if df.empty:
        return {
            "message": "No ICP data available. Run 'python workers/score_icp.py' first.",
            "total_clinics": 0
        }
    
    return {
        "total_clinics": len(df),
        "score_distribution": {
            "mean": float(df["icp_total_score"].mean()),
            "median": float(df["icp_total_score"].median()),
            "min": float(df["icp_total_score"].min()),
            "max": float(df["icp_total_score"].max()),
            "std": float(df["icp_total_score"].std())
        },
        "tier_distribution": {
            "tier_1_hot": int((df["icp_tier"] == 1).sum()),
            "tier_2_qualified": int((df["icp_tier"] == 2).sum()),
            "tier_3_monitor": int((df["icp_tier"] == 3).sum())
        },
        "segment_distribution": {
            "segment_a_behavioral_home_health": int((df["icp_segment"] == "A").sum()),
            "segment_b_fqhc_compliance": int((df["icp_segment"] == "B").sum()),
            "segment_c_multi_specialty_growth": int((df["icp_segment"] == "C").sum())
        },
        "category_averages": {
            "fit": float(df["icp_fit_score"].mean()),
            "pain": float(df["icp_pain_score"].mean()),
            "compliance_risk": float(df["icp_compliance_score"].mean()),
            "propensity_to_buy": float(df["icp_propensity_score"].mean()),
            "operational_scale": float(df["icp_scale_score"].mean()),
            "strategic_segment": float(df["icp_segment_score"].mean())
        },
        "top_10_clinics": df.nlargest(10, "icp_total_score")[
            ["clinic_id", "account_name", "state_code", "icp_total_score", "icp_tier_label", "icp_segment"]
        ].fillna("").to_dict(orient="records")
    }


@lru_cache(maxsize=1)
def load_networks() -> pd.DataFrame:
    """Load network-level ICP scores."""
    if not os.path.exists(NETWORKS_ICP_FILE):
        print(f"⚠️  Networks file not found: {NETWORKS_ICP_FILE}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(NETWORKS_ICP_FILE, dtype={"network_id": "string"}, low_memory=False)
        print(f"✓ Loaded {len(df):,} networks")
        return df
    except Exception as e:
        print(f"❌ Error loading networks: {e}")
        return pd.DataFrame()


@app.get("/icp/networks")
def get_networks(
    tier: Optional[str] = Query(None, description="Filter by tier: 1, 2, 3, or comma-separated"),
    segment: Optional[str] = Query(None, description="Filter by segment: A, B, or C"),
    min_clinics: Optional[int] = Query(None, description="Minimum number of clinics in network"),
    min_states: Optional[int] = Query(None, description="Minimum number of states covered"),
    min_score: Optional[float] = Query(None, description="Minimum network ICP score"),
    limit: int = Query(100, description="Max number of networks to return"),
    sort_by: str = Query("network_icp_total_score", description="Field to sort by"),
    sort_dir: str = Query("desc", description="Sort direction: asc or desc"),
):
    """
    Get network-level ICP scores with filtering and sorting.
    
    Returns aggregated scores for clinic networks (groups of clinics under same brand).
    """
    df = load_networks()
    
    if df.empty:
        return {
            "total": 0,
            "returned": 0,
            "networks": [],
            "message": "No network data available. Run network scoring first."
        }
    
    # Apply filters
    mask = pd.Series([True] * len(df), index=df.index)
    
    # Tier filter
    if tier:
        tier_values = [int(t.strip()) for t in tier.split(",") if t.strip().isdigit()]
        if tier_values:
            mask &= df["network_icp_tier"].isin(tier_values)
    
    # Segment filter
    if segment:
        segment = segment.upper()
        mask &= df["network_icp_segment"] == segment
    
    # Min clinics filter
    if min_clinics is not None:
        mask &= df["num_clinics"] >= min_clinics
    
    # Min states filter
    if min_states is not None:
        mask &= df["num_states"] >= min_states
    
    # Min score filter
    if min_score is not None:
        mask &= df["network_icp_total_score"] >= min_score
    
    filtered = df[mask].copy()
    
    # Sort
    if sort_by in filtered.columns:
        ascending = sort_dir.lower() == "asc"
        filtered = filtered.sort_values(by=sort_by, ascending=ascending)
    
    # Limit
    limited = filtered.head(limit)
    
    # Convert to records
    records = limited.fillna("").to_dict(orient="records")
    
    # Normalize types for JSON serialization
    for record in records:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Int64Dtype, pd.Int32Dtype, int, float)):
                if key in ["num_clinics", "num_states", "total_npi_count", "total_site_count", 
                          "fqhc_clinics_count", "aco_clinics_count", "network_icp_tier"]:
                    record[key] = int(value) if pd.notna(value) else None
                else:
                    record[key] = float(value) if pd.notna(value) else None
    
    return {
        "total": len(filtered),
        "returned": len(records),
        "networks": records,
        "filters_applied": {
            "tier": tier,
            "segment": segment,
            "min_clinics": min_clinics,
            "min_states": min_states,
            "min_score": min_score,
        }
    }


@app.get("/icp/networks/{network_id}")
def get_network_detail(network_id: str):
    """Get detailed information about a specific network."""
    networks_df = load_networks()
    
    if networks_df.empty:
        raise HTTPException(status_code=404, detail="Networks data not available")
    
    network = networks_df[networks_df["network_id"] == network_id]
    
    if network.empty:
        raise HTTPException(status_code=404, detail=f"Network {network_id} not found")
    
    network_record = network.iloc[0].to_dict()
    
    # Normalize types
    for key, value in network_record.items():
        if pd.isna(value):
            network_record[key] = None
        elif isinstance(value, (pd.Int64Dtype, pd.Int32Dtype, int, float)):
            if key in ["num_clinics", "num_states", "total_npi_count", "total_site_count",
                      "fqhc_clinics_count", "aco_clinics_count", "network_icp_tier"]:
                network_record[key] = int(value) if pd.notna(value) else None
            else:
                network_record[key] = float(value) if pd.notna(value) else None
    
    # Get clinics in this network
    clinics_df = load_clinics()
    if not clinics_df.empty and "network_id" in clinics_df.columns:
        network_clinics = clinics_df[clinics_df["network_id"] == network_id]
        
        if not network_clinics.empty:
            clinic_list = network_clinics[[
                "clinic_id", "account_name", "state_code", 
                "icp_total_score", "icp_tier_label", "is_network_anchor"
            ]].fillna("").to_dict(orient="records")
            
            network_record["clinics"] = clinic_list
        else:
            network_record["clinics"] = []
    else:
        network_record["clinics"] = []
    
    return network_record
