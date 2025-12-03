from __future__ import annotations

import math
import os
from typing import Dict, Tuple

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_CURATED = os.path.join(ROOT, "data", "curated")
CLINICS_SCORED = os.path.join(DATA_CURATED, "clinics_scored.csv")
CLINICS_SEED = os.path.join(DATA_CURATED, "clinics_seed.csv")
SCORES_SEED = os.path.join(DATA_CURATED, "scores_seed.csv")


COMPLEX_SEGMENTS = {
    "behavioral health",
    "home health",
    "post-acute",
    "post acute",
    "multi-specialty",
    "multi specialty",
    "orthopedic",
    "surgery",
}

PRIMARY_CARE_SEGMENTS = {"primary care", "family medicine", "internal medicine"}

GROWTH_SEGMENTS = {"multi-specialty", "health system / hospital-affiliated", "specialty / other"}

PRIMARY_DRIVER_LABELS = {
    "denial_pressure": "Denial pressure",
    "cash_flow_strain": "Cash-flow strain",
    "compliance_exposure": "Compliance exposure",
    "workforce_crisis": "Workforce crisis",
    "change_readiness": "Change readiness",
}


def read_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)


def safe_float(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default: int = 0) -> int:
    return int(round(safe_float(value, default)))


def normalise_text(value: str) -> str:
    return (value or "").strip().lower()


def chart_volume_complexity(row: Dict[str, object]) -> float:
    providers = safe_float(row.get("npi_count"))
    points = 0.0
    if providers >= 150:
        points = 2.5
    elif 30 <= providers <= 150:
        points = 2.0
    elif 15 <= providers < 30:
        points = 1.0
    elif providers >= 5:
        points = 0.5

    segment = normalise_text(row.get("segment_label") or row.get("segment"))
    if any(token in segment for token in COMPLEX_SEGMENTS):
        points += 1.0

    return min(3.0, points)


def billing_model_fit(row: Dict[str, object]) -> float:
    fqhc_flag = safe_int(row.get("fqhc_flag"))
    aco_member = safe_int(row.get("aco_member"))
    segment = normalise_text(row.get("segment_label") or row.get("segment"))
    sector = normalise_text(row.get("sector"))

    if fqhc_flag >= 1 or "fqhc" in segment:
        return 0.0

    if aco_member >= 1:
        return 2.0

    if "value" in sector:
        return 2.0

    if any(token in segment for token in COMPLEX_SEGMENTS):
        return 3.0

    return 3.0


def emr_integration(row: Dict[str, object]) -> float:
    # Historical pipeline stores EMR friction (higher = worse). Convert to integration ease.
    friction = max(0.0, min(10.0, safe_float(row.get("emr_friction"), 5.0)))
    integration_ease = 10.0 - friction
    if integration_ease >= 7.0:
        return 2.0
    if integration_ease >= 4.0:
        return 1.5
    return 0.5


def coding_setup(row: Dict[str, object]) -> float:
    site_count = safe_float(row.get("site_count"))
    providers = safe_float(row.get("npi_count"))
    segment = normalise_text(row.get("segment_label") or row.get("segment"))

    if site_count <= 2 and providers <= 60:
        return 2.0
    if site_count <= 5 and providers <= 150:
        return 1.5

    if "behavioral" in segment or "home health" in segment:
        return 1.5

    return 0.5


def structural_components(row: Dict[str, object]) -> Tuple[Dict[str, float], float]:
    components = {
        "fit_chart_volume_complexity": round(chart_volume_complexity(row), 2),
        "fit_billing_model_fit": round(billing_model_fit(row), 2),
        "fit_emr_integration": round(emr_integration(row), 2),
        "fit_coding_setup": round(coding_setup(row), 2),
    }
    structural_total = sum(components.values())
    return components, round(structural_total, 2)


def denial_pressure_component(row: Dict[str, object]) -> float:
    score = safe_float(row.get("denial_pressure"))
    if score >= 7.5:
        return 3.0
    if score >= 5.5:
        return 2.0
    if score >= 3.5:
        return 1.0
    return 0.0


def cash_flow_component(row: Dict[str, object]) -> float:
    allowed_amt = safe_float(row.get("allowed_amt"))
    bene_count = safe_float(row.get("bene_count"))
    segment = normalise_text(row.get("segment_label") or row.get("segment"))
    fqhc_flag = safe_int(row.get("fqhc_flag"))

    if allowed_amt > 0 and bene_count > 0:
        per_bene = allowed_amt / max(bene_count, 1.0)
        if per_bene < 300.0:
            return 2.0
        if per_bene < 600.0:
            return 1.0

    if fqhc_flag >= 1 or "fqhc" in segment:
        return 2.0

    if segment in PRIMARY_CARE_SEGMENTS or "behavioral" in segment:
        return 1.0

    return 0.0


def compliance_component(row: Dict[str, object], denial_points: float) -> float:
    """
    Calculate compliance exposure component.
    
    Priority:
    1. OIG LEIE flag (max signal, not guessed) = 2.0
    2. Recent audit flag (if exists) = 1.5
    3. Fallback to existing heuristics
    """
    # Check OIG LEIE flag first (highest priority, real signal)
    oig_leie_flag = row.get("oig_leie_flag")
    if oig_leie_flag is True or (isinstance(oig_leie_flag, (int, float)) and oig_leie_flag >= 1):
        return 2.0
    
    # Check for recent audit flag (if we add this in the future)
    # For now, we don't have this data, so skip
    
    # Fallback to existing heuristics
    segment = normalise_text(row.get("segment_label") or row.get("segment"))
    aco_member = safe_int(row.get("aco_member"))
    fqhc_flag = safe_int(row.get("fqhc_flag"))
    coding_complexity = safe_float(row.get("coding_complexity"))

    if "home health" in segment or "post acute" in segment:
        return 2.0
    if "behavioral" in segment and (denial_points >= 2.0 or coding_complexity >= 7.0):
        return 2.0
    if fqhc_flag >= 1:
        return max(1.0, 1.0)
    if aco_member >= 1:
        return 1.0
    return 0.0


def workforce_component(row: Dict[str, object]) -> float:
    scale_velocity = safe_float(row.get("scale_velocity"))
    site_count = safe_float(row.get("site_count"))

    if scale_velocity >= 7.0 or site_count >= 6:
        return 2.0
    if scale_velocity >= 4.5 or site_count >= 4:
        return 1.0
    return 0.0


def change_readiness_component(row: Dict[str, object]) -> float:
    roi_readiness = safe_float(row.get("roi_readiness"))
    pecos_enrolled = safe_int(row.get("pecos_enrolled"))
    aco_member = safe_int(row.get("aco_member"))
    segment = normalise_text(row.get("segment_label") or row.get("segment"))

    if roi_readiness >= 6.5 or pecos_enrolled >= 1 or aco_member >= 1:
        return 1.0
    if any(token in segment for token in GROWTH_SEGMENTS):
        return 1.0
    return 0.0


def propensity_components(row: Dict[str, object]) -> Tuple[Dict[str, float], float, Dict[str, float], str]:
    denial_points = round(denial_pressure_component(row), 2)
    cash_points = round(cash_flow_component(row), 2)
    compliance_points = round(compliance_component(row, denial_points), 2)
    workforce_points = round(workforce_component(row), 2)
    change_points = round(change_readiness_component(row), 2)

    components = {
        "prop_denial_pressure": denial_points,
        "prop_cash_flow_strain": cash_points,
        "prop_compliance_exposure": compliance_points,
        "prop_workforce_crisis": workforce_points,
        "prop_change_readiness": change_points,
    }

    weight_totals = {
        "denial_pressure": (denial_points / 3.0 if 3.0 else 0.0) * 1.0,
        "cash_flow_strain": (cash_points / 2.0 if 2.0 else 0.0) * 0.7,
        "compliance_exposure": (compliance_points / 2.0 if 2.0 else 0.0) * 0.7,
        "workforce_crisis": (workforce_points / 2.0 if 2.0 else 0.0) * 0.5,
        "change_readiness": (change_points / 1.0 if 1.0 else 0.0) * 0.3,
    }

    denominator = 1.0 + 0.7 + 0.7 + 0.5 + 0.3
    propensity_score = (
        weight_totals["denial_pressure"]
        + weight_totals["cash_flow_strain"]
        + weight_totals["compliance_exposure"]
        + weight_totals["workforce_crisis"]
        + weight_totals["change_readiness"]
    ) / denominator * 10.0

    primary_key = max(weight_totals.items(), key=lambda item: item[1])[0]
    primary_label = PRIMARY_DRIVER_LABELS[primary_key]

    return components, round(propensity_score, 2), weight_totals, primary_label


def compute_tier(structural: float, propensity: float) -> int:
    """
    Assign tier based on structural fit and propensity scores.
    
    Updated thresholds (calibrated to data distribution for realistic tiering):
    - Tier 1: Fit ≥ 6.0 AND Propensity ≥ 4.5 (high-fit + moderate urgency)
    - Tier 2: Fit ≥ 5.0 AND Propensity ≥ 3.0 (decent fit + moderate urgency)
    - Tier 3: Everything else (lower readiness or pain profile)
    
    Note: Max propensity in data is ~5.73, so thresholds are adjusted to ensure
    Tier 1 has meaningful representation (~1000+ clinics).
    """
    if structural >= 6.0 and propensity >= 4.5:
        return 1
    if structural >= 5.0 and propensity >= 3.0:
        return 2
    return 3


def tier_rationale(tier: int, primary_label: str) -> str:
    if tier == 1:
        return f"High fit + high urgency: {primary_label.lower()}"
    if tier == 2:
        return f"Solid fit with emerging urgency: {primary_label.lower()}"
    return f"Lower readiness or pain profile ({primary_label.lower()})"


def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in df.iterrows():
        base = row.to_dict()

        structural, structural_total = structural_components(base)
        propensity, propensity_total, contributions, primary_label = propensity_components(base)

        total_fit = min(10.0, structural_total)
        total_propensity = min(10.0, propensity_total)

        tier = compute_tier(total_fit, total_propensity)
        primary_driver = primary_label
        icf_score = round((total_fit * total_propensity) / 10.0, 2)

        updated = {
            **base,
            **structural,
            **propensity,
            "structural_fit_score": round(total_fit, 2),
            "propensity_score": round(total_propensity, 2),
            "icf_score": icf_score,
            "tier": tier,
            "icf_tier": tier,
            "primary_pain_driver": primary_driver,
            "primary_driver": primary_driver,
            "tier_rationale": tier_rationale(tier, primary_driver),
        }

        records.append(updated)

    columns_order = list(df.columns)
    # Ensure newly added fields appear in a predictable order
    new_cols = [
        "fit_chart_volume_complexity",
        "fit_billing_model_fit",
        "fit_emr_integration",
        "fit_coding_setup",
        "structural_fit_score",
        "prop_denial_pressure",
        "prop_cash_flow_strain",
        "prop_compliance_exposure",
        "prop_workforce_crisis",
        "prop_change_readiness",
        "propensity_score",
        "icf_score",
        "tier",
        "icf_tier",
        "primary_pain_driver",
        "primary_driver",
        "tier_rationale",
    ]
    for col in new_cols:
        if col not in columns_order:
            columns_order.append(col)

    scored_df = pd.DataFrame(records)
    # Reorder columns for readability
    scored_df = scored_df.reindex(columns=columns_order)
    return scored_df


def load_source_dataframe() -> pd.DataFrame:
    """
    Load the enriched clinic dataset. Prefer the DuckDB-enriched `clinics_scored.csv`
    (which carries the latest joins), falling back to the seed file if needed.
    """
    df = read_csv(CLINICS_SCORED)
    if not df.empty:
        return df
    return read_csv(CLINICS_SEED)


def main() -> None:
    df = load_source_dataframe()
    if df.empty:
        print("No clinics to score. Run enrichment first.")
        return

    scored = compute_scores(df)

    scored.to_csv(CLINICS_SCORED, index=False)

    score_columns = [
        "clinic_id",
        "structural_fit_score",
        "propensity_score",
        "icf_score",
        "tier",
        "icf_tier",
        "primary_pain_driver",
        "primary_driver",
        "fit_chart_volume_complexity",
        "fit_billing_model_fit",
        "fit_emr_integration",
        "fit_coding_setup",
        "prop_denial_pressure",
        "prop_cash_flow_strain",
        "prop_compliance_exposure",
        "prop_workforce_crisis",
        "prop_change_readiness",
        "tier_rationale",
    ]
    available_score_columns = [col for col in score_columns if col in scored.columns]
    scored[available_score_columns].to_csv(SCORES_SEED, index=False)

    print(f"Wrote: {SCORES_SEED} rows={len(scored)}")
    print(f"Wrote: {CLINICS_SCORED} rows={len(scored)}")


if __name__ == "__main__":
    main()
