"""
ICP SCORING ENGINE v12.0 (DESCRIPTIVE SEGMENTS)
Author: Charta Health GTM Strategy

CHANGELOG v12.0:
- **DESCRIPTIVE SEGMENTS:** Replaced Segment A-F with descriptive labels.
- **TAXONOMY-DRIVEN LOGIC:** Scoring now adapts to new labels from `enrich_features.py`.
- **SIMPLIFIED TRACKING:** `detect_track` now uses descriptive labels.
"""

import pandas as pd
import numpy as np
import os
import math

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_FILE = os.path.join(ROOT, "data", "curated", "clinics_enriched_scored.csv")
OUTPUT_FILE = os.path.join(ROOT, "data", "curated", "clinics_scored_final.csv")

MIPS_STAGING = os.path.join(ROOT, "data", "staging", "stg_mips_org_scores.csv")
HPSA_MUA_STAGING = os.path.join(ROOT, "data", "staging", "stg_hpsa_mua_flags.csv")

UNDERCODING_SEVERE = 0.15
UNDERCODING_NATIONAL_AVG = 0.45
UNDERCODING_FLOOR_SCORE = 10
PSYCH_RISK_SEVERE = 0.75
PSYCH_RISK_MILD = 0.0

# Specialty Procedure Alignment Targets
# Maps taxonomy prefixes to expected procedure ratios (procedures / total claims)
# National averages for procedure-heavy specialties
SPECIALTY_PROCEDURE_TARGETS = {
    '213E': 0.60,  # Podiatry - expect 60% procedures (foot/ankle care)
    '207X': 0.50,  # Orthopedics - expect 50% procedures (musculoskeletal)
    '207W': 0.60,  # Ophthalmology - expect 60% procedures (eye surgery/procedures)
    '207N': 0.50,  # Dermatology - expect 50% procedures (skin procedures)
    '204C': 0.40,  # Sports Medicine - expect 40% procedures
    '204D': 0.40,  # Surgical Oncology - expect high procedures
    '208200': 0.40,  # Plastic Surgery - expect high procedures
    '207V': 0.50,  # General Surgery - expect 50% procedures
    '207T': 0.45,  # Pain Medicine - expect 45% procedures (injections)
}

# Minimum procedure deficit to flag (e.g., 20% below target)
PROCEDURE_DEFICIT_THRESHOLD = 0.20

# Data quality tracking for procedure alignment
PROCEDURE_DATA_QUALITY_STATS = {
    'procedure_heavy_specialties': 0,
    'has_data': 0,
    'missing_data': 0,
    'low_volume': 0,
    'by_specialty': {},
    'missing_by_specialty': {}
}

# Taxonomy to specialty name mapping
TAXONOMY_TO_SPECIALTY = {
    '213E': 'Podiatry',
    '207X': 'Orthopedics',
    '207W': 'Ophthalmology',
    '207N': 'Dermatology',
    '204C': 'Sports Medicine',
    '204D': 'Surgical Oncology',
    '208200': 'Plastic Surgery',
    '207V': 'General Surgery',
    '207T': 'Pain Medicine'
}

def get_specialty_name(taxonomy_str):
    """Return human-readable specialty name from taxonomy code."""
    if pd.isna(taxonomy_str) or taxonomy_str == "":
        return "Unknown"

    codes = [c.strip() for c in str(taxonomy_str).split(';') if c.strip()]
    for code in codes:
        for prefix, specialty in TAXONOMY_TO_SPECIALTY.items():
            if code.startswith(prefix):
                return specialty
    return "Other Specialty"

def get_expected_procedure_ratio(taxonomy_str):
    """
    Given a taxonomy string, return the expected procedure ratio if it matches
    a procedure-heavy specialty. Returns None if no match.
    """
    if pd.isna(taxonomy_str) or taxonomy_str == "":
        return None

    # Check each taxonomy code in the string (may have multiple separated by ;)
    codes = [c.strip() for c in str(taxonomy_str).split(';') if c.strip()]

    for code in codes:
        # Check for exact matches or prefix matches
        for taxonomy_prefix, expected_ratio in SPECIALTY_PROCEDURE_TARGETS.items():
            if code.startswith(taxonomy_prefix):
                return expected_ratio

    return None

def score_procedure_alignment(row):
    """
    Score procedure alignment pain for procedure-heavy specialties.

    Returns: (pain_score, reasoning)

    Logic:
    - Only applies to Private Practice or Specialty Group segments
    - Checks if taxonomy indicates a procedure-heavy specialty
    - Compares actual procedure ratio to expected ratio
    - Flags if procedures are significantly below expected

    Data Quality Tracking:
    - Tracks when procedure-heavy specialties are missing procedure data
    - Uses global counter PROCEDURE_DATA_QUALITY_STATS
    """
    segment = str(row.get('segment_label', ''))

    # Only apply to relevant segments
    if segment not in ['Private Practice', 'Specialty Group']:
        return 0, ""

    # Get expected procedure ratio based on taxonomy
    taxonomy = row.get('taxonomy', '')
    expected_ratio = get_expected_procedure_ratio(taxonomy)

    if expected_ratio is None:
        # Not a procedure-heavy specialty
        return 0, ""

    # DATA QUALITY TRACKING: This is a procedure-heavy specialty
    global PROCEDURE_DATA_QUALITY_STATS
    specialty_name = get_specialty_name(taxonomy)
    PROCEDURE_DATA_QUALITY_STATS['procedure_heavy_specialties'] += 1
    PROCEDURE_DATA_QUALITY_STATS['by_specialty'][specialty_name] = PROCEDURE_DATA_QUALITY_STATS['by_specialty'].get(specialty_name, 0) + 1

    # Get actual procedure data
    procedure_ratio = row.get('procedure_ratio', 0)
    original_procedure_ratio = row.get('procedure_ratio', None)

    if pd.isna(procedure_ratio):
        procedure_ratio = 0

    total_procedure_codes = row.get('total_procedure_codes', 0)
    if pd.isna(total_procedure_codes):
        total_procedure_codes = 0

    total_eval_codes = row.get('total_eval_codes', 0)
    if pd.isna(total_eval_codes):
        total_eval_codes = 0

    # Need meaningful volume to assess (at least 50 total claims)
    total_claims = total_procedure_codes + total_eval_codes
    if total_claims < 50:
        # DATA QUALITY: Low volume, can't assess
        PROCEDURE_DATA_QUALITY_STATS['low_volume'] += 1
        return 0, ""

    # DATA QUALITY CHECK: Missing procedure data for procedure-heavy specialty
    if pd.isna(original_procedure_ratio):
        PROCEDURE_DATA_QUALITY_STATS['missing_data'] += 1
        PROCEDURE_DATA_QUALITY_STATS['missing_by_specialty'][specialty_name] = PROCEDURE_DATA_QUALITY_STATS['missing_by_specialty'].get(specialty_name, 0) + 1
        # Silently return 0 (conservative approach)
        return 0, ""
    else:
        PROCEDURE_DATA_QUALITY_STATS['has_data'] += 1

    # Calculate deficit
    deficit = expected_ratio - procedure_ratio

    # Flag if deficit exceeds threshold
    if deficit >= PROCEDURE_DEFICIT_THRESHOLD:
        # Score based on severity of deficit
        # INCREASED: Max score from 5 → 10 points (competitive with E&M/therapy pain)
        # Severe deficit (>40% below): 10 points
        # Moderate deficit (20-40% below): 4-10 points
        if deficit >= 0.40:
            pain_score = 10
            reason = f"Severe procedure deficit: {procedure_ratio:.1%} vs expected {expected_ratio:.1%}"
        else:
            pain_score = 4 + ((deficit - PROCEDURE_DEFICIT_THRESHOLD) / 0.20) * 6
            pain_score = round(pain_score, 1)
            reason = f"Procedure deficit: {procedure_ratio:.1%} vs expected {expected_ratio:.1%}"

        return pain_score, reason

    return 0, ""

def detect_track(row):
    """
    Determine which scoring track to use based on the new descriptive segment labels.
    """
    segment = str(row.get('segment_label', ''))
    org_name = str(row.get('org_name', '')).upper()

    if segment == 'Behavioral Health':
        return 'BEHAVIORAL'

    behavioral_keywords = ['BEHAVIORAL', 'PSYCH', 'MENTAL HEALTH', 'COUNSELING', 'THERAPY']
    if any(keyword in org_name for keyword in behavioral_keywords):
        return 'BEHAVIORAL'

    if segment in ['Home Health', 'Hospital']:
        return 'POST_ACUTE'

    return 'AMBULATORY'

def score_undercoding_continuous(ratio):
    if ratio <= 0 or pd.isna(ratio):
        return 10, "No undercoding data available"
    if ratio >= UNDERCODING_NATIONAL_AVG:
        # WINNING: Above national average means strong E&M documentation
        return 0, f"Strong E&M documentation ({ratio:.3f})"
    if ratio <= UNDERCODING_SEVERE:
        return 40, f"Severe undercoding ({ratio:.3f})"
    score = 40 - ((ratio - UNDERCODING_SEVERE) / (UNDERCODING_NATIONAL_AVG - UNDERCODING_SEVERE)) * 25
    return round(score, 1), f"Undercoding ratio {ratio:.3f}"

def score_psych_risk_continuous(ratio):
    if ratio <= 0 or pd.isna(ratio):
        return 10, "No psych risk data available"

    BENCHMARK = 0.50
    SEVERE_LOW = 0.30
    SEVERE_HIGH = 0.75
    SWEET_SPOT_LOW = 0.40
    SWEET_SPOT_HIGH = 0.60

    if ratio <= SEVERE_LOW:
        return 40, f"Severe therapy undercoding ({ratio:.3f}) - Revenue Leakage"
    elif ratio >= SEVERE_HIGH:
        return 40, f"Severe psych audit risk ({ratio:.3f}) - Compliance Threat"
    elif SWEET_SPOT_LOW <= ratio <= SWEET_SPOT_HIGH:
        return 10, f"Balanced therapy coding ({ratio:.3f}) - Appropriate"
    elif ratio < SWEET_SPOT_LOW:
        deviation = (SWEET_SPOT_LOW - ratio) / (SWEET_SPOT_LOW - SEVERE_LOW)
        score = 10 + (deviation * 30)
        return round(score, 1), f"Moderate therapy undercoding ({ratio:.3f})"
    else:
        deviation = (ratio - SWEET_SPOT_HIGH) / (SEVERE_HIGH - SWEET_SPOT_HIGH)
        score = 10 + (deviation * 30)
        return round(score, 1), f"Elevated psych audit risk ({ratio:.3f})"

def score_behavioral_vbc_readiness(row):
    score = 0
    reasoning = []
    avg_mips = row.get('avg_mips_score', None)
    if pd.notna(avg_mips) and avg_mips > 80:
        score += 5
        reasoning.append(f"MIPS {avg_mips:.1f} = VBC-ready tech infrastructure")
    elif pd.notna(avg_mips) and avg_mips >= 60:
        score += 3
        reasoning.append(f"MIPS {avg_mips:.1f} = moderate tech readiness")
    
    is_aco = str(row.get('is_aco_participant', '')).lower() == 'true'
    if is_aco:
        score += 5
        reasoning.append("ACO participant = VBC experience")
    
    is_hpsa = str(row.get('is_hpsa', 'False')).lower() == 'true'
    is_mua = str(row.get('is_mua', 'False')).lower() == 'true'
    if is_hpsa or is_mua:
        score += 5
        designation = []
        if is_hpsa: designation.append("HPSA")
        if is_mua: designation.append("MUA")
        reasoning.append(f"{'/'.join(designation)} = complex population, BHI opportunity")
    
    return min(score, 15), reasoning

def score_provider_count_continuous(npi_count):
    if npi_count <= 1:
        return 0
    if npi_count >= 100:
        return 10
    score = (math.log(npi_count) / math.log(100)) * 10
    return round(score, 1)

def score_revenue_continuous(revenue, segment):
    if pd.isna(revenue) or revenue <= 0:
        return 2
    is_fqhc = segment == 'FQHC'
    if is_fqhc:
        min_rev, mid_rev, max_rev = 100_000, 2_000_000, 5_000_000
    else:
        min_rev, mid_rev, max_rev = 500_000, 5_000_000, 15_000_000
    if revenue >= max_rev:
        return 15
    if revenue <= min_rev:
        return 2
    log_revenue = math.log(revenue)
    log_min = math.log(min_rev)
    log_max = math.log(max_rev)
    score = 2 + ((log_revenue - log_min) / (log_max - log_min)) * 13
    return round(min(15, max(2, score)), 1)

def score_volume_continuous(volume, is_verified):
    if pd.isna(volume) or volume <= 0:
        return 3
    max_score = 15 if is_verified else 10
    if volume >= 50_000:
        return max_score
    if volume <= 1_000:
        return 3
    log_volume = math.log(volume)
    log_min = math.log(1_000)
    log_max = math.log(50_000)
    score = 3 + ((log_volume - log_min) / (log_max - log_min)) * (max_score - 3)
    return round(min(max_score, max(3, score)), 1)

def score_behavioral_volume_continuous(volume, is_verified):
    if pd.isna(volume) or volume <= 0:
        return 3
    max_score = 15 if is_verified else 10
    if volume >= 20_000:
        return max_score
    if volume <= 500:
        return 3
    log_volume = math.log(volume)
    log_min = math.log(500)
    log_max = math.log(20_000)
    score = 3 + ((log_volume - log_min) / (log_max - log_min)) * (max_score - 3)
    return round(min(max_score, max(3, score)), 1)

def calculate_row_score(row):
    real_revenue = row.get('total_revenue')
    if pd.isna(real_revenue): real_revenue = row.get('hospital_total_revenue')
    if pd.isna(real_revenue): real_revenue = row.get('fqhc_revenue')
    if pd.isna(real_revenue): real_revenue = row.get('hha_revenue')
    if pd.isna(real_revenue): real_revenue = row.get('real_medicare_revenue')

    real_enc = row.get('services_count')
    est_enc = row.get('final_volume')
    vol_metric = real_enc if (pd.notnull(real_enc) and real_enc > 0) else (est_enc if pd.notnull(est_enc) else 0)

    volume_source = str(row.get('volume_source', '')).upper()
    is_verified_volume = 'UDS' in volume_source or 'VERIFIED' in volume_source or 'CLAIMS' in volume_source or 'HRSA' in volume_source

    undercoding = row.get('undercoding_ratio', 0)
    if pd.isna(undercoding): undercoding = 0
    psych_risk = row.get('psych_risk_ratio', 0)
    if pd.isna(psych_risk): psych_risk = 0

    is_aco = str(row.get('is_aco_participant', '')).lower() == 'true'
    is_risk = str(row.get('risk_compliance_flag', '')).lower() == 'true' or str(row.get('oig_leie_flag', '')).lower() == 'true'
    npi_count = float(row.get('npi_count', 1))
    site_count = float(row.get('site_count', 1))

    segment = str(row.get('segment_label', 'Multi-specialty'))
    
    # Revenue-based downgrade for Hospitals
    if segment == 'Hospital' and pd.notna(real_revenue) and real_revenue < 10_000_000:
        segment = 'Ambulatory Center'

    corrected_fqhc_flag = row.get('fqhc_flag', 0)

    confidence = 0
    pain_reasoning = []
    fit_reasoning = []
    strategy_reasoning = []

    track = detect_track(row)

    if track == 'BEHAVIORAL':
        pain, reason = score_psych_risk_continuous(psych_risk)
        pain_reasoning.append(f"+{pain:.1f}pts: {reason}")
        total_psych = row.get('total_psych_codes', 0)
        if pd.notna(total_psych) and total_psych > 500:
            addon_bonus = min(5, (total_psych / 1000) * 5)
            pain += addon_bonus
            pain = min(40, pain)
            pain_reasoning.append(f"+{addon_bonus:.1f}pts: High psych volume ({int(total_psych)} codes) = documentation lift")
        if pain >= 20:
            confidence += 40
    elif track == 'POST_ACUTE':
        real_margin = row.get('net_margin')
        if pd.notna(real_margin):
            if real_margin < 0.0:
                pain = 40
                pain_reasoning.append(f"+40pts: Negative margin ({real_margin:.1%})")
            elif real_margin < 0.05:
                pain = 25 + (0.05 - real_margin) / 0.05 * 15
                pain = round(pain, 1)
                pain_reasoning.append(f"+{pain:.1f}pts: Low margin ({real_margin:.1%})")
            else:
                pain = 15
                pain_reasoning.append(f"+15pts: Stable margin ({real_margin:.1%})")
            confidence += 30
        else:
            pain = 10
            pain_reasoning.append("+10pts: No margin data")
    else:
        pain_undercoding, reason_undercoding = score_undercoding_continuous(undercoding)

        # --- THERAPY RELEVANCE GATE (STRICT PERCENTAGE-BASED) ---
        total_psych_codes = row.get('total_psych_codes', 0)
        if pd.isna(total_psych_codes): total_psych_codes = 0

        total_eval_codes = row.get('total_eval_codes', 0)
        eval_codes_available = pd.notna(total_eval_codes) and total_eval_codes > 0
        if pd.isna(total_eval_codes): total_eval_codes = 0

        pain_therapy = 0
        reason_therapy = ""

        # Calculate therapy as percentage of total ambulatory volume
        # EDGE CASE: If eval_codes is missing, we can't calculate a valid percentage
        # Conservative approach: set percentage to 0 (won't pass gate)
        if not eval_codes_available:
            psych_percentage = 0
        else:
            total_ambulatory_claims = total_psych_codes + total_eval_codes
            if total_ambulatory_claims > 0:
                psych_percentage = total_psych_codes / total_ambulatory_claims
            else:
                psych_percentage = 0

        # STRICT GATE: Therapy must be >20% of ambulatory volume AND >100 absolute codes
        # This prevents large multi-specialty groups with incidental psych billing from being flagged
        # Examples that should NOT be flagged:
        #   - Froedtert: 2,306 psych / 173,901 total = 1.3%
        #   - Montefiore: 3,855 psych / 226,016 total = 1.7%
        #   - NORTH SHORE: 302 psych / NaN eval = no valid percentage (edge case)
        # Examples that SHOULD be flagged:
        #   - True BH clinic: 800 psych / 1,000 total = 80%
        #   - Integrated BH (FQHC): 300 psych / 1,200 total = 25%
        if psych_percentage > 0.20 and total_psych_codes >= 100:
            if pd.notnull(psych_risk) and psych_risk > 0:
                pain_therapy, reason_therapy = score_psych_risk_continuous(psych_risk)

        # --- PROCEDURE ALIGNMENT AUDIT ---
        pain_procedure_alignment, reason_procedure_alignment = score_procedure_alignment(row)

        # Determine primary pain signal
        if pain_therapy > pain_undercoding:
            pain = pain_therapy
            pain_reasoning.append(f"+{pain:.1f}pts: {reason_therapy} (therapy coding dominates)")
            pain_reasoning.append(f"  (Alternative: {pain_undercoding:.1f}pts E&M undercoding)")
        else:
            pain = pain_undercoding
            pain_reasoning.append(f"+{pain:.1f}pts: {reason_undercoding}")
            if pain_therapy > 10:
                pain_reasoning.append(f"  (Secondary: {pain_therapy:.1f}pts therapy coding)")

        # Add procedure alignment pain if detected
        if pain_procedure_alignment > 0:
            pain += pain_procedure_alignment
            pain = min(40, pain)  # Cap at 40 total
            pain_reasoning.append(f"+{pain_procedure_alignment:.1f}pts: {reason_procedure_alignment}")

        if pain >= 30:
            confidence += 50

    s2_align, s2_complex, s2_tech_risk, s2_mips, s2_hpsa_mua = 0, 0, 0, 0, 0
    if track == 'BEHAVIORAL':
        s2_align = 10
        fit_reasoning.append(f"+10pts: Behavioral Health - Core ICP segment")
        vbc_score, vbc_reasons = score_behavioral_vbc_readiness(row)
        for reason in vbc_reasons:
            fit_reasoning.append(reason)
        s2_complex = score_provider_count_continuous(npi_count)
        if s2_complex > 0:
            fit_reasoning.append(f"+{s2_complex:.1f}pts: {int(npi_count)} providers (operational capacity)")
        fit = round(s2_align + vbc_score + min(s2_complex, 5), 1)
    else:
        segment_alignment_scores = {
            'FQHC': 15,
            'Urgent Care': 15,
            'Behavioral Health': 10,
            'Private Practice': 10,
            'Hospital': 8,
            'Home Health': 5,
            'Ambulatory Clinic': 5,
            'Multi-specialty': 5
        }
        s2_align = segment_alignment_scores.get(segment, 5)
        fit_reasoning.append(f"+{s2_align}pts: {segment} alignment")
        s2_complex = score_provider_count_continuous(npi_count)
        if s2_complex > 0:
            fit_reasoning.append(f"+{s2_complex:.1f}pts: {int(npi_count)} providers")
        if is_aco:
            s2_tech_risk += 3
            fit_reasoning.append("+3pts: ACO participant")
        if is_risk:
            s2_tech_risk += 2
            fit_reasoning.append("+2pts: Compliance flag")
        avg_mips_score = row.get('avg_mips_score', None)
        if pd.notna(avg_mips_score):
            if avg_mips_score > 80:
                s2_mips = 5
                fit_reasoning.append(f"+5pts: High MIPS quality ({avg_mips_score:.1f})")
            elif avg_mips_score < 50:
                s2_mips = 5
                fit_reasoning.append(f"+5pts: Distressed MIPS performer ({avg_mips_score:.1f})")
        is_hpsa = str(row.get('is_hpsa', 'False')).lower() == 'true'
        is_mua = str(row.get('is_mua', 'False')).lower() == 'true'
        if is_hpsa or is_mua:
            s2_hpsa_mua = 5
            designation = []
            if is_hpsa: designation.append("HPSA")
            if is_mua: designation.append("MUA")
            fit_reasoning.append(f"+5pts: {'/'.join(designation)} designated area")
        fit = round(s2_align + s2_complex + s2_tech_risk + s2_mips + s2_hpsa_mua, 1)

    if track == 'BEHAVIORAL':
        est_rev = real_revenue if pd.notnull(real_revenue) else (vol_metric * 150)
        # EQUALIZED THRESHOLDS: Use same revenue scale as AMBULATORY track
        # Old: $250k-$5M, New: $1M-$15M (matches deal size economics)
        if pd.isna(est_rev) or est_rev <= 0:
            s3_revenue = 2
        elif est_rev >= 15_000_000:
            s3_revenue = 15
        elif est_rev <= 1_000_000:
            s3_revenue = 2
        else:
            log_revenue = math.log(est_rev)
            log_min = math.log(1_000_000)
            log_max = math.log(15_000_000)
            s3_revenue = 2 + ((log_revenue - log_min) / (log_max - log_min)) * 13
            s3_revenue = round(min(15, max(2, s3_revenue)), 1)
        strategy_reasoning.append(f"+{s3_revenue:.1f}pts: ${est_rev/1_000_000:.2f}M revenue (equalized thresholds)")
        s3_volume = score_behavioral_volume_continuous(vol_metric, is_verified_volume)
        if vol_metric > 0:
            verified_label = "verified" if is_verified_volume else "estimated"
            strategy_reasoning.append(f"+{s3_volume:.1f}pts: {int(vol_metric):,} {verified_label} volume (behavioral thresholds)")
        else:
            strategy_reasoning.append(f"+{s3_volume:.1f}pts: No volume data")
        strat = round(s3_revenue + s3_volume, 1)
    else:
        if segment == 'FQHC':
            est_rev = real_revenue if pd.notnull(real_revenue) else (vol_metric * 300)
        else:
            est_rev = real_revenue if pd.notnull(real_revenue) else (vol_metric * 100)
        s3_revenue = score_revenue_continuous(est_rev, segment)
        strategy_reasoning.append(f"+{s3_revenue:.1f}pts: ${est_rev/1_000_000:.2f}M revenue")
        s3_volume = score_volume_continuous(vol_metric, is_verified_volume)
        if vol_metric > 0:
            verified_label = "verified" if is_verified_volume else "estimated"
            strategy_reasoning.append(f"+{s3_volume:.1f}pts: {int(vol_metric):,} {verified_label} volume")
        else:
            strategy_reasoning.append(f"+{s3_volume:.1f}pts: No volume data")
        strat = round(s3_revenue + s3_volume, 1)

    total = round(pain + fit + strat, 1)
    tier = 'Tier 4'
    if total >= 70: tier = 'Tier 1'
    elif total >= 50: tier = 'Tier 2'
    elif total >= 30: tier = 'Tier 3'

    drivers = []
    if track == 'BEHAVIORAL':
        if pain >= 25:
            if psych_risk <= 0.30:
                drivers.append(f"💰 Therapy Undercoding ({psych_risk:.2f})")
            elif psych_risk >= 0.75:
                drivers.append(f"🚨 Compliance/Audit Risk ({psych_risk:.2f})")
            else:
                drivers.append(f"Therapy Coding Risk ({psych_risk:.2f})")
        else:
            drivers.append(f"{track} Track: Benchmark")
    elif track == 'POST_ACUTE':
        if pain >= 25:
            real_margin = row.get('net_margin')
            if pd.notna(real_margin):
                if real_margin < 0:
                    drivers.append(f"Financial Distress (margin {real_margin:.1%})")
                else:
                    drivers.append(f"Margin Pressure (margin {real_margin:.1%})")
            else:
                drivers.append(f"Margin Pressure")
        else:
            drivers.append(f"{track} Track: Benchmark")
    else:
        if pain >= 25:
            # Check if procedure alignment is a significant signal
            if pain_procedure_alignment >= 3:
                procedure_ratio = row.get('procedure_ratio', 0)
                expected_ratio = get_expected_procedure_ratio(row.get('taxonomy', ''))
                if expected_ratio:
                    drivers.append(f"⚠️ Procedure Alignment ({procedure_ratio:.0%} vs {expected_ratio:.0%} expected)")

            # Calculate therapy percentage for driver logic
            total_psych_codes_driver = row.get('total_psych_codes', 0)
            total_eval_codes_driver = row.get('total_eval_codes', 0)
            if pd.isna(total_psych_codes_driver): total_psych_codes_driver = 0
            if pd.isna(total_eval_codes_driver): total_eval_codes_driver = 0

            total_ambulatory_driver = total_psych_codes_driver + total_eval_codes_driver
            psych_pct_driver = total_psych_codes_driver / total_ambulatory_driver if total_ambulatory_driver > 0 else 0

            dominant_signal = "undercoding"
            # STRICT GATE: Only show therapy drivers if >20% of volume is therapy
            if psych_pct_driver > 0.20 and total_psych_codes_driver >= 100 and pd.notnull(psych_risk) and psych_risk > 0:
                pain_therapy_check, _ = score_psych_risk_continuous(psych_risk)
                pain_undercoding_check, _ = score_undercoding_continuous(undercoding)
                if pain_therapy_check > pain_undercoding_check:
                    dominant_signal = "therapy"

            if dominant_signal == "therapy":
                if psych_risk <= 0.30:
                    drivers.append(f"💰 Therapy Undercoding ({psych_risk:.2f})")
                elif psych_risk >= 0.75:
                    drivers.append(f"🚨 Therapy Audit Risk ({psych_risk:.2f})")
                else:
                    drivers.append(f"Therapy Coding Risk ({psych_risk:.2f})")
            else:
                # Only show undercoding driver if actually undercoding
                if undercoding >= UNDERCODING_NATIONAL_AVG:
                    drivers.append(f"✅ Strong E&M Documentation ({undercoding:.2f})")
                elif pain >= 35:
                    drivers.append(f"🩸 SEVERE Undercoding ({undercoding:.2f})")
                elif undercoding < UNDERCODING_NATIONAL_AVG:
                    drivers.append(f"E&M Undercoding ({undercoding:.2f})")
        else:
            drivers.append(f"{track} Track: Benchmark")

    if s2_align >= 15:
        if segment == 'FQHC':
            drivers.append("FQHC - Core ICP")
        elif segment == 'Urgent Care':
            drivers.append("Urgent Care - High Fit")
    elif track == 'BEHAVIORAL':
        drivers.append("Behavioral Health - Core ICP")

    volume_unit = "encounters"
    if pd.notna(volume_source):
        if 'UDS' in volume_source.upper() or 'HRSA UDS' in volume_source.upper():
            volume_unit = "patients"
        elif 'CLAIMS' in volume_source.upper() or 'MEDICARE' in volume_source.upper():
            volume_unit = "encounters"
    if s3_volume >= 12:
        drivers.append(f"High Volume ({int(vol_metric/1000)}k {volume_unit})")
    elif site_count > 5:
        drivers.append(f"Multi-Site Network ({int(site_count)} sites)")
    if est_rev > 5_000_000:
        drivers.append(f"Strong Rev (${est_rev/1000000:.1f}M)")
    if is_risk:
        drivers.append("Compliance Flag")
    if is_aco:
        drivers.append("ACO Participant")

    pain_label = "Economic Pain"
    if track == 'BEHAVIORAL':
        # --- APPLY THERAPY RELEVANCE GATE FOR BEHAVIORAL TRACK ---
        total_psych_codes_bh = row.get('total_psych_codes', 0)
        if pd.isna(total_psych_codes_bh): total_psych_codes_bh = 0

        total_eval_codes_bh = row.get('total_eval_codes', 0)
        eval_codes_available_bh = pd.notna(total_eval_codes_bh) and total_eval_codes_bh > 0
        if pd.isna(total_eval_codes_bh): total_eval_codes_bh = 0

        # Calculate therapy percentage
        # EDGE CASE: If eval_codes is missing, we can't calculate a valid percentage
        if not eval_codes_available_bh:
            psych_pct_bh = 0
        else:
            total_ambulatory_bh = total_psych_codes_bh + total_eval_codes_bh
            psych_pct_bh = total_psych_codes_bh / total_ambulatory_bh if total_ambulatory_bh > 0 else 0

        # Calculate actual pain scores to determine which is dominant
        pain_therapy_bh, _ = score_psych_risk_continuous(psych_risk)
        pain_undercoding_bh, _ = score_undercoding_continuous(undercoding)

        # Check if this is a "winner" (strong documentation, no real pain)
        is_winning_bh = (undercoding >= UNDERCODING_NATIONAL_AVG and pain_therapy_bh == 0)

        if is_winning_bh:
            pain_label = "Low Pain - Strong Documentation"
        # STRICT GATE: Only label as therapy pain if >20% of volume is therapy AND therapy pain > undercoding pain
        elif psych_pct_bh > 0.20 and total_psych_codes_bh >= 100 and pd.notnull(psych_risk) and psych_risk > 0 and pain_therapy_bh > pain_undercoding_bh:
            if psych_risk <= 0.30:
                pain_label = "Therapy Undercoding Pain"
            elif psych_risk >= 0.75:
                pain_label = "Audit Risk Pain"
            else:
                pain_label = "Therapy Coding Risk"
        else:
            # If therapy volume is too low OR undercoding pain is higher, fallback to undercoding pain
            pain_label = "Undercoding Pain"
    elif track == 'POST_ACUTE':
        pain_label = "Margin Pressure"
    else:  # AMBULATORY
        # --- RE-APPLY RELEVANCE GATE for LABEL ---
        total_psych_codes = row.get('total_psych_codes', 0)
        if pd.isna(total_psych_codes): total_psych_codes = 0

        total_eval_codes = row.get('total_eval_codes', 0)
        eval_codes_available_label = pd.notna(total_eval_codes) and total_eval_codes > 0
        if pd.isna(total_eval_codes): total_eval_codes = 0

        # Calculate therapy percentage (same logic as above)
        # EDGE CASE: If eval_codes is missing, we can't calculate a valid percentage
        if not eval_codes_available_label:
            psych_percentage = 0
        else:
            total_ambulatory_claims = total_psych_codes + total_eval_codes
            if total_ambulatory_claims > 0:
                psych_percentage = total_psych_codes / total_ambulatory_claims
            else:
                psych_percentage = 0

        pain_therapy_check, _ = score_psych_risk_continuous(psych_risk)
        pain_undercoding_check, _ = score_undercoding_continuous(undercoding)

        # Check if this is a "winner" (strong documentation, no pain)
        is_winning = (undercoding >= UNDERCODING_NATIONAL_AVG and pain_therapy_check == 0 and pain_procedure_alignment == 0)

        if is_winning:
            pain_label = "Low Pain - Strong Documentation"
        # Check if procedure alignment is the dominant signal
        elif pain_procedure_alignment >= 3 and pain_procedure_alignment >= pain_therapy_check and pain_procedure_alignment >= pain_undercoding_check:
            pain_label = "Procedure Alignment Pain"
        # STRICT GATE: Only label as therapy pain if >20% of volume is therapy
        elif psych_percentage > 0.20 and total_psych_codes >= 100 and pd.notnull(psych_risk) and psych_risk > 0 and pain_therapy_check > pain_undercoding_check:
             if psych_risk <= 0.30: pain_label = "Therapy Undercoding Pain"
             elif psych_risk >= 0.75: pain_label = "Therapy Audit Risk"
             else: pain_label = "Therapy Coding Risk"
        else:
            pain_label = "Undercoding Pain"

    return {
        'icp_score': min(100, total),
        'icp_tier': tier,
        'segment_label': segment,
        'fqhc_flag': corrected_fqhc_flag,
        'scoring_track': track,
        'pain_label': pain_label,
        'data_confidence': min(100, confidence),
        'scoring_drivers': " | ".join(drivers) if drivers else "Standard",
        'score_pain_total': round(pain, 1),
        'score_pain_signal': round(pain, 1),
        'score_pain_volume': 0, 'score_pain_margin': 0, 'score_pain_compliance': 0,
        'score_fit_total': round(fit, 1),
        'score_fit_align': s2_align,
        'score_fit_complex': round(s2_complex, 1),
        'score_fit_chaos': 0, 'score_fit_risk': s2_tech_risk, 'score_fit_mips': s2_mips, 'score_fit_hpsa_mua': s2_hpsa_mua,
        'score_strat_total': round(strat, 1),
        'score_strat_deal': round(s3_revenue, 1),
        'score_strat_expand': round(s3_volume, 1),
        'score_strat_ref': 0,
        'score_bonus_strategic_scale': 0,
        'score_base_before_bonus': min(100, total),
        'metric_est_revenue': est_rev,
        'metric_used_volume': vol_metric,
        'volume_unit': volume_unit,
        'score_reasoning_pain': " | ".join(pain_reasoning),
        'score_reasoning_fit': " | ".join(fit_reasoning),
        'score_reasoning_strategy': " | ".join(strategy_reasoning)
    }

def calculate_score(row_dict):
    row = pd.Series(row_dict)
    result = calculate_row_score(row)
    return {
        'total': result['icp_score'], 'tier': result['icp_tier'], 'confidence': result['data_confidence'], 'rationale': result['scoring_drivers'],
        'estimates': {'revenue': result['metric_est_revenue'], 'encounters': result['metric_used_volume']},
        'breakdown': {
            'pain_total': result['score_pain_total'], 'pain_signal': result['score_pain_signal'], 'pain_volume': result['score_pain_volume'], 'pain_margin': result['score_pain_margin'],
            'fit_total': result['score_fit_total'], 'fit_align': result['score_fit_align'], 'fit_complex': result['score_fit_complex'], 'fit_chaos': result['score_fit_chaos'],
            'strat_total': result['score_strat_total'], 'strat_deal': result['score_strat_deal'], 'strat_expand': result['score_strat_expand']
        }
    }

def main():
    print("🚀 RUNNING CONTINUOUS SCORING ENGINE v12.0...")
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file missing: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE, low_memory=False)
    print(f"Loaded {len(df):,} clinics.")

    if os.path.exists(MIPS_STAGING):
        print(f"📥 Loading MIPS data from {MIPS_STAGING}...")
        mips_df = pd.read_csv(MIPS_STAGING)
        mips_df['npi'] = mips_df['org_npi'].astype(str)
        df['npi'] = df['npi'].astype(str)
        df = df.merge(mips_df[['npi', 'avg_mips_score', 'mips_clinician_count']], on='npi', how='left')
        print(f"   ✅ Matched {df['avg_mips_score'].notna().sum():,} clinics with MIPS data")
    else:
        print(f"   ⚠️  MIPS staging file not found. Skipping MIPS scoring.")
        df['avg_mips_score'] = None
        df['mips_clinician_count'] = None

    if os.path.exists(HPSA_MUA_STAGING):
        print(f"📥 Loading HPSA/MUA data from {HPSA_MUA_STAGING}...")
        hpsa_mua_df = pd.read_csv(HPSA_MUA_STAGING)
        if 'county_name' in df.columns and df['county_name'].notna().sum() > 0:
            print(f"   ✅ County data available - using county-level matching")
            df['state_norm'] = df['state_code'].str.upper().str.strip()
            df['county_norm'] = df['county_name'].str.strip().str.title()
            hpsa_mua_df['state_norm'] = hpsa_mua_df['state'].str.upper().str.strip()
            hpsa_mua_df['county_norm'] = hpsa_mua_df['county_name'].str.strip().str.title()
            df = df.merge(hpsa_mua_df[['state_norm', 'county_norm', 'is_hpsa', 'is_mua']], on=['state_norm', 'county_norm'], how='left')
            df.drop(columns=['state_norm', 'county_norm'], inplace=True)
            df['is_hpsa'] = df['is_hpsa'].fillna(False).astype(bool)
            df['is_mua'] = df['is_mua'].fillna(False).astype(bool)
            print(f"   ✅ Matched {df['is_hpsa'].sum():,} clinics in HPSA counties")
            print(f"   ✅ Matched {df['is_mua'].sum():,} clinics in MUA counties")
        else:
            print(f"   ⚠️  No county data available - using state-level fallback")
            hpsa_states = set(hpsa_mua_df[hpsa_mua_df['is_hpsa']]['state'].unique())
            mua_states = set(hpsa_mua_df[hpsa_mua_df['is_mua']]['state'].unique())
            df['is_hpsa'] = df['state_code'].isin(hpsa_states)
            df['is_mua'] = df['state_code'].isin(mua_states)
            print(f"   ✅ Marked {df['is_hpsa'].sum():,} clinics in HPSA states")
            print(f"   ✅ Marked {df['is_mua'].sum():,} clinics in MUA states")
    else:
        print(f"   ⚠️  HPSA/MUA staging file not found. Skipping HPSA/MUA scoring.")
        df['is_hpsa'] = False
        df['is_mua'] = False

    cols_to_numeric = ['services_count', 'final_volume', 'total_revenue', 'npi_count', 'undercoding_ratio', 'net_margin', 'hospital_margin', 'hha_margin', 'fqhc_margin', 'hospital_total_revenue', 'fqhc_revenue', 'hha_revenue', 'real_medicare_revenue', 'psych_risk_ratio', 'total_psych_codes', 'site_count']
    for c in cols_to_numeric:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce')

    print("Calculating continuous scores...")
    scores = df.apply(calculate_row_score, axis=1, result_type='expand')
    
    cols_to_drop = [c for c in scores.columns if c in df.columns]
    if cols_to_drop: df.drop(columns=cols_to_drop, inplace=True)

    final_df = pd.concat([df, scores], axis=1)
    final_df.sort_values('icp_score', ascending=False, inplace=True)

    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"💾 Saved to {OUTPUT_FILE}")

    print("\n📊 CONTINUOUS SCORING RESULTS BY TRACK:")
    for track in ['AMBULATORY', 'BEHAVIORAL', 'POST_ACUTE']:
        track_df = final_df[final_df['scoring_track'] == track]
        if len(track_df) > 0:
            print(f"\n{track} Track ({len(track_df):,} clinics):")
            print(f"  Avg Score: {track_df['icp_score'].mean():.1f}")
            print(f"  Score Range: {track_df['icp_score'].min():.1f} - {track_df['icp_score'].max():.1f}")
            tier_counts = track_df['icp_tier'].value_counts()
            for tier in ['Tier 1', 'Tier 2', 'Tier 3', 'Tier 4']:
                print(f"  {tier}: {tier_counts.get(tier, 0):,}")

    print("\n📊 OVERALL TIER DISTRIBUTION:")
    print(final_df['icp_tier'].value_counts())
    print(f"\n✨ UNIQUE SCORES: {final_df['icp_score'].nunique():,} (vs ~10 in v8.0)")

    print("\n📋 SAMPLE CONTINUOUS SCORES:")
    sample = final_df.head(5)[['org_name', 'icp_score', 'score_pain_total', 'score_fit_total', 'score_strat_total']]
    print(sample.to_string(index=False))

    # DATA QUALITY REPORT: Procedure Alignment Coverage
    print("\n" + "="*80)
    print("📊 PROCEDURE ALIGNMENT DATA QUALITY REPORT")
    print("="*80)

    if PROCEDURE_DATA_QUALITY_STATS['procedure_heavy_specialties'] > 0:
        total_proc_heavy = PROCEDURE_DATA_QUALITY_STATS['procedure_heavy_specialties']
        has_data = PROCEDURE_DATA_QUALITY_STATS['has_data']
        missing_data = PROCEDURE_DATA_QUALITY_STATS['missing_data']
        low_volume = PROCEDURE_DATA_QUALITY_STATS['low_volume']

        print(f"\nProcedure-Heavy Specialties Found: {total_proc_heavy:,}")
        print(f"  ✅ With procedure data: {has_data:,} ({has_data/total_proc_heavy*100:.1f}%)")
        print(f"  ❌ Missing procedure data: {missing_data:,} ({missing_data/total_proc_heavy*100:.1f}%)")
        print(f"  ⚠️  Low volume (<50 claims): {low_volume:,} ({low_volume/total_proc_heavy*100:.1f}%)")

        print("\n📋 Breakdown by Specialty:")
        for specialty in sorted(PROCEDURE_DATA_QUALITY_STATS['by_specialty'].keys()):
            total = PROCEDURE_DATA_QUALITY_STATS['by_specialty'][specialty]
            missing = PROCEDURE_DATA_QUALITY_STATS['missing_by_specialty'].get(specialty, 0)
            coverage = ((total - missing) / total * 100) if total > 0 else 0
            status = "✅" if coverage >= 50 else "⚠️" if coverage >= 20 else "❌"
            print(f"  {status} {specialty:20s}: {total:5,} total | {missing:5,} missing ({coverage:5.1f}% coverage)")

        if missing_data > 0:
            print("\n⚠️  WARNING: High percentage of procedure-heavy specialties missing data.")
            print("   Recommendation: Investigate mine_cpt_codes.py procedure extraction logic.")
            print("   Impact: These clinics may have undetected procedure alignment pain.")
    else:
        print("\n✅ No procedure-heavy specialties found in this dataset.")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
