"""
Frontend Data Generator for Charta Health Dashboard
Author: Charta Health GTM Engineering

Purpose: Transform production scoring data into UI-friendly JSON format.
Input: data/curated/clinics_scored_final.csv
Output: web/public/data/clinics.json

Key Features:
- Revenue unit normalization (fix values < $10k)
- Top 5,000 leads (expanded from 2,500)
- Glass box analysis with ranking logic, gaps, benchmarks
- Multi-level sorting (icp_score DESC, then est_revenue_lift DESC)
"""

import pandas as pd
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCORED_FILE = os.path.join(ROOT, "data", "curated", "clinics_scored_final.csv")
OUTPUT_JSON = os.path.join(ROOT, "web", "public", "data", "clinics.json")

# Benchmarks
NATIONAL_UNDERCODING_AVG = 0.45  # National average for undercoding ratio


def remove_emojis(text):
    """
    Remove all emojis from text.

    Used to clean driver labels and strategic brief text for professional display.
    """
    if not text or pd.isna(text):
        return text

    # Comprehensive emoji pattern covering all Unicode emoji ranges
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F700-\U0001F77F"  # alchemical symbols
        u"\U0001F780-\U0001F7FF"  # geometric shapes extended
        u"\U0001F800-\U0001F8FF"  # supplemental arrows-C
        u"\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        u"\U0001FA00-\U0001FA6F"  # chess symbols
        u"\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A (includes 🩸)
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"  # dingbats
        u"\U000024C2-\U0001F251"
        u"\U0001F004"             # mahjong tile
        u"\U0001F0CF"             # playing card
        u"\U0001F18E"             # negative squared ab
        u"\U0001F191-\U0001F19A"  # squared cl, cool, free, etc
        u"\U0001F201-\U0001F251"  # squared katakana
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text).strip()


def normalize_revenue(value):
    """
    Fix revenue unit issues (Critique #9).

    If value < 10,000, assume source was in 'Thousands' and multiply by 1,000.
    Logic: No clinic has $2 annual revenue - this is a data quality issue.
    """
    if pd.isna(value) or value == 0:
        return 0

    # If suspiciously low, assume it's in thousands
    if value < 10_000:
        return value * 1_000

    return value


def format_revenue(value):
    """Format revenue as $12.52M or $450k."""
    if pd.isna(value) or value == 0:
        return "N/A"
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value/1_000:.0f}k"
    else:
        return f"${value:.0f}"


def format_volume(value):
    """Format volume as 45,000."""
    if pd.isna(value) or value == 0:
        return "N/A"
    return f"{int(value):,}"


def format_phone(value):
    """Format phone number to xxx-xxx-xxxx."""
    if pd.isna(value) or value == '' or str(value).lower() == 'nan':
        return ""

    # Convert to string and remove any .0 suffix
    phone_str = str(value).replace('.0', '').strip()

    # Remove any non-digit characters
    digits = ''.join(filter(str.isdigit, phone_str))

    # Format as xxx-xxx-xxxx if we have 10 digits
    if len(digits) == 10:
        return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    elif len(digits) == 11 and digits[0] == '1':
        # Handle 1-xxx-xxx-xxxx format
        return f"{digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
    elif len(digits) > 0:
        # Return as-is if not standard format
        return digits
    else:
        return ""


def parse_drivers(scoring_drivers_str):
    """
    Parse emoji-based scoring_drivers string into UI tags.

    Emoji mappings:
    - 🐋 -> green (High Volume - was purple/Strategic)
    - 🩸 or 🚨 -> red (Urgent)
    - ✅ -> green (Verified)

    Pain keywords for red styling:
    - Pain, Audit Risk, Undercoding, Margin Pressure
    """
    if pd.isna(scoring_drivers_str) or scoring_drivers_str == '':
        return []

    # Pain-related keywords that should be styled red
    pain_keywords = ['Pain', 'Audit Risk', 'Undercoding', 'Margin Pressure', 'Risk', 'Coding Risk']

    drivers = []
    parts = str(scoring_drivers_str).split(' | ')

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Replace "Whale Scale" with "High Volume"
        part = part.replace('🐋 Whale Scale', 'High Volume')

        # Extract label and value before removing emojis
        if '(' in part:
            label = part.split('(')[0].strip()
            value = part.split('(')[1].replace(')', '').strip()
        else:
            label = part
            value = ""

        # Remove emojis from label
        label = remove_emojis(label)

        # Determine color based on emoji or label content
        color = "text-gray-600"  # default

        # Check for pain-related keywords first (highest priority)
        if any(keyword in label for keyword in pain_keywords):
            color = "text-red-600"
        # Then check for High Volume
        elif 'High Volume' in label:
            color = "text-green-600"
        # Then check for Verified
        elif any(word in label for word in ['Verified', 'Quality']):
            color = "text-green-600"

        drivers.append({
            "label": label,
            "value": value,
            "color": color
        })

    return drivers[:3]  # Limit to top 3 drivers


def calculate_lift(final_revenue, undercoding_ratio, psych_risk_ratio, segment_label, scoring_track):
    """
    Calculate revenue opportunity with payer mix economics and denial prevention.

    NEW LOGIC (v12.0):
    1. "Winning" Check: Organizations already at/above benchmark get $0 coding lift
       - AMBULATORY: undercoding_ratio >= 0.45 → WINNING
       - BEHAVIORAL: psych_risk_ratio in [0.40, 0.60] OR > 0.60 → WINNING
    2. FQHC Payer Mix Discount: Segment B gets coding_lift * 0.20 (80% PPS, 20% FFS)
    3. Denial Prevention: Always calculated at 5% of revenue (separate from coding)

    Returns dict with 7 fields:
    - total_opportunity_value: coding_lift + denial_prevention (main display)
    - coding_lift_value: Track-specific lift calculation
    - denial_prevention_value: Always 5% of revenue
    - is_projected_lift: Whether lift is verified or estimated
    - lift_basis: Human-readable label
    - payer_mix_applied: Boolean if FQHC discount applied
    - winning_status: 'WINNING' | 'OPPORTUNITY' | 'UNKNOWN'
    """
    # Initialize default values
    coding_lift = 0
    denial_prevention = final_revenue * 0.05 if final_revenue > 0 else 0
    is_projected = False
    lift_basis = "Unknown"
    payer_mix_applied = False
    winning_status = "UNKNOWN"

    # Validate inputs - return zeros if no revenue
    if pd.isna(final_revenue) or final_revenue == 0:
        return {
            'total_opportunity_value': 0,
            'coding_lift_value': 0,
            'denial_prevention_value': 0,
            'is_projected_lift': True,
            'lift_basis': "N/A",
            'payer_mix_applied': False,
            'winning_status': "UNKNOWN"
        }

    # TRACK-SPECIFIC WINNING LOGIC
    if scoring_track == 'AMBULATORY':
        # E&M/Medical Track - Uses undercoding_ratio
        if pd.notna(undercoding_ratio) and 0 < undercoding_ratio < 1.0:
            # Winning check: If >= 0.45 (national avg), no coding lift
            if undercoding_ratio >= 0.45:
                coding_lift = 0
                lift_basis = "Already Winning (E&M)"
                winning_status = "WINNING"
                is_projected = False
            else:
                # Opportunity: Calculate gap to 50% target
                coding_lift = final_revenue * (0.50 - undercoding_ratio)
                lift_basis = "Verified Opportunity (E&M)"
                winning_status = "OPPORTUNITY"
                is_projected = False
        else:
            # Fallback: 5% benchmark when no valid data
            coding_lift = final_revenue * 0.05
            lift_basis = "Est. Opportunity (E&M)"
            winning_status = "UNKNOWN"
            is_projected = True

    elif scoring_track == 'BEHAVIORAL':
        # Therapy/Behavioral Track - Uses psych_risk_ratio
        if pd.notna(psych_risk_ratio) and 0 < psych_risk_ratio < 1.0:
            # Winning check: If in sweet spot (0.40-0.60) OR audit risk (>0.60)
            if psych_risk_ratio >= 0.40 and psych_risk_ratio <= 0.60:
                coding_lift = 0
                lift_basis = "Already Winning (Therapy - Optimal Range)"
                winning_status = "WINNING"
                is_projected = False
            elif psych_risk_ratio > 0.60:
                coding_lift = 0
                lift_basis = "Already Winning (Therapy - Audit Risk)"
                winning_status = "WINNING"
                is_projected = False
            else:  # psych_risk_ratio < 0.40 (conservative coding)
                # Opportunity: Calculate gap to 50% target
                coding_lift = final_revenue * (0.50 - psych_risk_ratio)
                lift_basis = "Verified Opportunity (Therapy)"
                winning_status = "OPPORTUNITY"
                is_projected = False
        else:
            # Fallback: 5% benchmark when no valid data
            coding_lift = final_revenue * 0.05
            lift_basis = "Est. Opportunity (Therapy)"
            winning_status = "UNKNOWN"
            is_projected = True

    else:
        # POST_ACUTE or other tracks - Use 5% benchmark
        coding_lift = final_revenue * 0.05
        lift_basis = "Est. Opportunity (Post-Acute)"
        winning_status = "UNKNOWN"
        is_projected = True

    # FQHC PAYER MIX DISCOUNT
    # Apply AFTER winning check, BEFORE summing with denial prevention
    if segment_label == 'FQHC' and coding_lift > 0:
        # Discounting for estimated 20% Commercial/FFS Payer Mix
        # FQHCs receive 80% PPS (flat rate), only 20% benefit from coding optimization
        coding_lift = coding_lift * 0.20
        payer_mix_applied = True
        lift_basis = lift_basis + " (FQHC Discounted)"

    # CALCULATE TOTAL OPPORTUNITY
    total_opportunity = coding_lift + denial_prevention

    return {
        'total_opportunity_value': total_opportunity,
        'coding_lift_value': coding_lift,
        'denial_prevention_value': denial_prevention,
        'is_projected_lift': is_projected,
        'lift_basis': lift_basis,
        'payer_mix_applied': payer_mix_applied,
        'winning_status': winning_status
    }


def calculate_billing_ratio(undercoding_ratio):
    """
    Calculate billing ratio chart data.

    Logic:
    - If undercoding_ratio is valid:
      - Level 4 % = undercoding_ratio * 100
      - Level 3 % = 100 - (undercoding_ratio * 100)
    - Else:
      - Use 50/50 default
    """
    if pd.notna(undercoding_ratio) and 0 < undercoding_ratio < 1.0:
        level4_pct = int(undercoding_ratio * 100)
        level3_pct = 100 - level4_pct
    else:
        # Default 50/50 split
        level3_pct = 50
        level4_pct = 50

    return {"level3": level3_pct, "level4": level4_pct}


def identify_data_gaps(row):
    """
    Identify missing or low-quality data (Critique #4).

    Returns list of gap descriptions.
    """
    gaps = []

    # Critical financial data
    if pd.isna(row.get('undercoding_ratio')) or row.get('undercoding_ratio') == 0:
        gaps.append("Missing CPT billing data")

    if pd.isna(row.get('psych_risk_ratio')):
        gaps.append("No psych audit risk data")

    if pd.isna(row.get('final_margin')) or row.get('final_margin') == 0:
        gaps.append("Missing margin data")

    # Volume verification
    volume_source = str(row.get('volume_source', ''))
    if 'Unknown' in volume_source or volume_source == 'nan':
        gaps.append("Unverified volume estimate")

    # Revenue verification
    revenue_source = str(row.get('revenue_source', ''))
    if 'Unknown' in revenue_source or revenue_source == 'nan':
        gaps.append("Unverified revenue estimate")

    # Data confidence
    data_confidence = row.get('data_confidence', '')
    if pd.isna(data_confidence) or data_confidence == 'Low':
        gaps.append("Low overall data confidence")

    return gaps


def generate_strategic_brief(row, lift_value):
    """
    Generate analyst-tone strategic brief based on data signals.

    This is NOT a sales pitch. This is an objective operational assessment
    based on claims data, billing patterns, and organizational characteristics.
    """
    segment = row.get('segment_label', 'Unknown')
    undercoding_ratio = row.get('undercoding_ratio')
    psych_risk_ratio = row.get('psych_risk_ratio')
    total_volume = row.get('total_medicare_volume', 0)
    uds_volume = row.get('uds_patient_total', 0)
    margin = row.get('margin')

    # Determine primary operational reality
    brief_parts = []

    # === SEVERE UNDERCODING SIGNAL ===
    if pd.notna(undercoding_ratio) and undercoding_ratio < 0.35:
        brief_parts.append(
            f"Claims analysis proves systemic under-coding (only {undercoding_ratio:.1%} Level 4/5 usage vs. 45% benchmark). "
            f"This suggests a risk-averse culture leaving verified revenue on the table."
        )
    elif pd.notna(undercoding_ratio) and undercoding_ratio < 0.50:
        brief_parts.append(
            f"Billing patterns show {undercoding_ratio:.1%} Level 4/5 usage, below 50% optimal target. "
            f"Data indicates room for documentation improvement without changing clinical care."
        )

    # === BEHAVIORAL HEALTH CODING SIGNALS (BIDIRECTIONAL) ===
    if pd.notna(psych_risk_ratio):
        # Conservative coding (undercoding therapy complexity)
        if psych_risk_ratio <= 0.30:
            brief_parts.append(
                f"Claims analysis shows conservative therapy coding (only {psych_risk_ratio:.1%} high-complexity sessions vs. 50% national benchmark). "
                f"This suggests systematic undercoding of therapy complexity, leaving verified revenue on the table."
            )
        # Aggressive coding (audit risk)
        elif psych_risk_ratio >= 0.75:
            brief_parts.append(
                f"Billing patterns show statistical anomaly in high-complexity codes ({psych_risk_ratio:.1%} of therapy sessions vs. 50% benchmark), "
                f"creating immediate audit liability and potential recoupment exposure under payer scrutiny."
            )
        # Moderate overcoding
        elif psych_risk_ratio > 0.60:
            brief_parts.append(
                f"Elevated use of high-complexity therapy codes ({psych_risk_ratio:.1%} vs. 50% benchmark) suggests potential compliance exposure."
            )

    # === HIGH VOLUME OPERATIONAL REALITY ===
    whale_volume = max(total_volume, uds_volume) if pd.notna(uds_volume) else total_volume
    if whale_volume > 50_000:
        brief_parts.append(
            f"Scale of operations ({whale_volume:,.0f} annual visits) implies manual auditing is mathematically impossible. "
            f"Likely reliant on spot-checks, creating systemic blind spots."
        )
    elif whale_volume > 25_000:
        brief_parts.append(
            f"Volume profile ({whale_volume:,.0f} visits) suggests chart review bottlenecks limit coding accuracy feedback loops."
        )

    # === FQHC MARGIN PRESSURE ===
    if segment == 'FQHC':
        if pd.notna(margin) and margin < 0.02:
            brief_parts.append(
                f"Grant-funded status with thin margins ({margin:.1%}) creates extreme sensitivity to revenue leakage. "
                f"Even small billing errors compound into existential risk."
            )
        else:
            brief_parts.append(
                f"Safety-net mission with PPS reimbursement creates complex compliance requirements and coding dependencies."
            )

    # === STRATEGIC VALUE (if significant lift) ===
    if lift_value > 1_000_000:
        brief_parts.append(
            f"Financial modeling suggests ${lift_value/1_000_000:.1f}M annual opportunity from billing optimization alone."
        )

    # Fallback if no strong signals
    if not brief_parts:
        brief_parts.append(
            "Operational profile suggests standard market opportunity with likely optimization potential pending deeper analysis."
        )

    return " ".join(brief_parts)


def generate_benchmarks(row):
    """
    Compare clinic metrics to national benchmarks (Critique #4).
    """
    benchmarks = {}

    # Undercoding ratio benchmark
    undercoding = row.get('undercoding_ratio')
    if pd.notna(undercoding) and undercoding > 0:
        vs_national = undercoding - NATIONAL_UNDERCODING_AVG
        if undercoding > NATIONAL_UNDERCODING_AVG:  # Higher = GOOD (more Level 4/5 usage = less undercoding)
            benchmarks['undercoding'] = {
                'value': round(undercoding, 3),
                'national_avg': NATIONAL_UNDERCODING_AVG,
                'comparison': f"{abs(vs_national):.2%} better than national average (less undercoding)",
                'status': 'outperforming'
            }
        else:  # Lower = BAD (fewer Level 4/5 usage = more undercoding)
            benchmarks['undercoding'] = {
                'value': round(undercoding, 3),
                'national_avg': NATIONAL_UNDERCODING_AVG,
                'comparison': f"{abs(vs_national):.2%} worse than national average (more undercoding)",
                'status': 'underperforming'
            }
    else:
        benchmarks['undercoding'] = {
            'value': None,
            'national_avg': NATIONAL_UNDERCODING_AVG,
            'comparison': "No data available",
            'status': 'unknown'
        }

    # Psych risk benchmark (assume 0.20 is high risk threshold)
    psych_risk = row.get('psych_risk_ratio')
    if pd.notna(psych_risk) and psych_risk > 0:
        if psych_risk > 0.75:
            benchmarks['psych_audit_risk'] = {
                'value': round(psych_risk, 3),
                'threshold': 0.75,
                'status': 'severe',
                'description': 'Critical audit risk - immediate attention needed'
            }
        elif psych_risk > 0.50:
            benchmarks['psych_audit_risk'] = {
                'value': round(psych_risk, 3),
                'threshold': 0.50,
                'status': 'elevated',
                'description': 'Moderate audit risk detected'
            }
        else:
            benchmarks['psych_audit_risk'] = {
                'value': round(psych_risk, 3),
                'threshold': 0.50,
                'status': 'normal',
                'description': 'Acceptable audit risk profile'
            }

    return benchmarks


def extract_raw_scores(row):
    """
    V8.0 STRICT 100-POINT SCALE
    Extract exact point breakdowns for transparency.
    
    Pain (40) + Fit (30) + Strategy (30) = 100
    No bonuses. Clean additive math.
    """
    def safe_float(val):
        """Preserve decimal precision from continuous scoring."""
        return round(float(val), 1) if pd.notna(val) else 0

    def safe_int(val):
        """Convert to integer for legacy sub-component scores."""
        return int(val) if pd.notna(val) else 0

    # Extract component scores (preserve decimal precision)
    pain_total = safe_float(row.get('score_pain_total'))
    fit_total = safe_float(row.get('score_fit_total'))
    strat_total = safe_float(row.get('score_strat_total'))
    icp_score = safe_float(row.get('icp_score'))
    
    # Verify strict 100-point scale: pain + fit + strategy = icp_score
    # (Allow small rounding differences)
    calculated_total = pain_total + fit_total + strat_total
    if abs(calculated_total - icp_score) > 1:
        # Log warning but don't fail
        pass  # Could add logging here if needed
    
    return {
        'pain': {
            'total': pain_total,
            'signal': safe_float(row.get('score_pain_signal')),
            'volume': 0,      # Removed in v8.0
            'margin': 0,      # Removed in v8.0
            'compliance': 0   # Removed in v8.0
        },
        'fit': {
            'total': fit_total,
            'alignment': safe_float(row.get('score_fit_align')),
            'complexity': safe_float(row.get('score_fit_complex')),
            'chaos': 0,       # Removed in v8.0
            'risk': safe_float(row.get('score_fit_risk'))
        },
        'strategy': {
            'total': strat_total,
            'deal_size': safe_float(row.get('score_strat_deal')),      # Revenue score
            'expansion': safe_float(row.get('score_strat_expand')),    # Whale scale
            'referrals': 0    # Removed in v8.0
        },
        'bonus': {
            'strategic_scale': 0  # No bonuses in v8.0 (MIPS/HPSA bonuses included in fit total)
        },
        'base_before_bonus': icp_score,  # Same as total in v8.0
        'final_score': icp_score
    }


def parse_reasoning_string(reasoning_str):
    """
    Parse backend reasoning string (pipe-delimited) into list.
    Example: "+40pts: Severe undercoding | +5pts: HPSA area"
    Returns: ["+40pts: Severe undercoding", "+5pts: HPSA area"]
    """
    if not reasoning_str or pd.isna(reasoning_str) or reasoning_str == '':
        return []

    # Split by pipe and strip whitespace
    items = [item.strip() for item in str(reasoning_str).split('|') if item.strip()]
    return items


def generate_score_reasoning(row):
    """
    V8.0 STRICT 100-POINT SCALE
    Generate explicit scoring math showing exact statistical conditions.

    Returns structured object with every threshold check and points awarded.
    This matches score_icp_production.py v8.0 logic exactly.
    
    Pain (40) + Fit (30) + Strategy (30) = 100
    """
    reasoning = {
        'pain': [],
        'fit': [],
        'strategy': [],
        'bonus': []  # Empty in v8.0, kept for compatibility
    }

    # Get metrics
    undercoding = row.get('undercoding_ratio')
    if pd.isna(undercoding): undercoding = 0
    
    psych_risk = row.get('psych_risk_ratio')
    if pd.isna(psych_risk): psych_risk = 0
    
    vol_metric = row.get('metric_used_volume', row.get('real_annual_encounters', 0))
    if pd.isna(vol_metric): vol_metric = 0
    
    volume_source = str(row.get('volume_source', '')).upper()
    is_verified_volume = 'UDS' in volume_source or 'VERIFIED' in volume_source or 'CLAIMS' in volume_source

    npi_count = row.get('npi_count', 1)
    if pd.isna(npi_count): npi_count = 1
    
    site_count = row.get('site_count', 1)
    if pd.isna(site_count): site_count = 1

    est_revenue = row.get('metric_est_revenue', row.get('final_revenue', 0))
    if pd.isna(est_revenue): est_revenue = 0

    segment = str(row.get('segment_label', 'Unknown'))
    track = str(row.get('scoring_track', 'AMBULATORY'))
    is_aco = str(row.get('is_aco_participant', '')).lower() == 'true'
    is_risk = str(row.get('risk_compliance_flag', '')).lower() == 'true' or str(row.get('oig_leie_flag', '')).lower() == 'true'
    
    pain_total = row.get('score_pain_total', 0)
    if pd.isna(pain_total): pain_total = 0

    # ========================================
    # V8.0 PAIN SCORING (MAX 40)
    # ========================================
    if track == 'BEHAVIORAL':
        if psych_risk > 0.75:
            reasoning['pain'].append(f"40pts: Psych Risk {psych_risk:.3f} > 0.75 (SEVERE Audit Exposure)")
        elif psych_risk > 0:
            reasoning['pain'].append(f"30pts: Psych Risk {psych_risk:.3f} detected (Verified)")
        else:
            reasoning['pain'].append(f"10pts: Behavioral Track - Benchmark projection")
    
    elif track == 'POST_ACUTE':
        margin = row.get('net_margin')
        if pd.notna(margin):
            if margin < 0.02:
                reasoning['pain'].append(f"40pts: Margin {margin:.1%} < 2% (SEVERE Pressure)")
            else:
                reasoning['pain'].append(f"30pts: Margin {margin:.1%} tracked (Verified)")
        else:
            reasoning['pain'].append(f"10pts: Post-Acute Track - Benchmark projection")
    
    else:  # AMBULATORY
        if undercoding > 0 and undercoding < 0.35:
            reasoning['pain'].append(f"40pts: Only {undercoding:.1%} Level 4/5 usage (< 35% benchmark) - SEVERE Undercoding")
        elif undercoding > 0 and undercoding < 0.50:
            reasoning['pain'].append(f"30pts: Only {undercoding:.1%} Level 4/5 usage (< 50% target) - Moderate Undercoding")
        else:
            reasoning['pain'].append(f"10pts: Ambulatory Track - Benchmark projection")

    # ========================================
    # V8.0 FIT SCORING (MAX 30)
    # ========================================
    
    # Alignment (Max 15)
    if segment == 'FQHC':
        reasoning['fit'].append(f"15pts: FQHC - Core ICP alignment")
    elif segment == 'Urgent Care':
        reasoning['fit'].append(f"15pts: Urgent Care - High alignment")
    elif segment in ['Behavioral Health', 'Private Practice']:
        reasoning['fit'].append(f"10pts: Primary/Behavioral alignment")
    else:
        reasoning['fit'].append(f"5pts: Standard alignment")

    # Complexity (Max 10)
    if segment == 'FQHC':
        reasoning['fit'].append(f"10pts: FQHC complexity")
    elif segment == 'Hospital':
        reasoning['fit'].append(f"10pts: Hospital complexity")
    elif npi_count > 10:
        reasoning['fit'].append(f"10pts: Large multi-specialty ({int(npi_count)} providers)")
    elif npi_count > 3:
        reasoning['fit'].append(f"5pts: Medium group ({int(npi_count)} providers)")
    
    # Tech/Risk (Max 5)
    if is_aco or is_risk:
        reasoning['fit'].append(f"5pts: ACO or OIG compliance flag")

    # ========================================
    # V8.0 STRATEGY SCORING (MAX 30)
    # ========================================
    
    # Revenue (Max 15)
    if segment == 'FQHC':
        # FQHC: >$5M = 15pts
        if est_revenue > 5_000_000:
            reasoning['strategy'].append(f"15pts: Revenue ${est_revenue/1_000_000:.1f}M > $5M (FQHC)")
        elif est_revenue > 2_000_000:
            reasoning['strategy'].append(f"10pts: Revenue ${est_revenue/1_000_000:.1f}M > $2M")
        else:
            reasoning['strategy'].append(f"5pts: Revenue ${est_revenue/1_000_000:.1f}M (FQHC)")
    else:
        # Standard: >$15M = 15pts
        if est_revenue > 15_000_000:
            reasoning['strategy'].append(f"15pts: Revenue ${est_revenue/1_000_000:.1f}M > $15M")
        elif est_revenue > 5_000_000:
            reasoning['strategy'].append(f"10pts: Revenue ${est_revenue/1_000_000:.1f}M > $5M")
        else:
            reasoning['strategy'].append(f"5pts: Revenue ${est_revenue/1_000_000:.1f}M")
    
    # High Volume (Max 15)
    if is_verified_volume and vol_metric > 25000:
        reasoning['strategy'].append(f"15pts: High Volume - Verified volume {int(vol_metric):,} patients > 25k threshold")
    elif site_count > 5:
        reasoning['strategy'].append(f"10pts: Multi-Site Network ({int(site_count)} sites)")
    else:
        reasoning['strategy'].append(f"5pts: Standard scale")

    # No bonuses in v8.0 - bonus array stays empty for compatibility
    
    return reasoning


def generate_json():
    """Main function to generate frontend JSON from production data."""

    if not os.path.exists(SCORED_FILE):
        print(f"❌ Scored file not found: {SCORED_FILE}")
        return

    print("📦 Generating Frontend JSON from Production Data...")
    print(f"   Input: {SCORED_FILE}")

    # Load production data
    df = pd.read_csv(SCORED_FILE, low_memory=False)
    print(f"   Loaded {len(df):,} total clinics")

    # Attach phone numbers from NPI staging (if available)
    npi_staging_path = os.path.join(ROOT, "data", "curated", "staging", "stg_npi_orgs.parquet")
    if os.path.exists(npi_staging_path):
        try:
            npi_df = pd.read_parquet(npi_staging_path)[["npi", "phone"]]
            npi_df["npi"] = npi_df["npi"].astype(str)
            df["npi"] = df["npi"].astype(str)
            before_merge = df["npi"].nunique()
            df = df.merge(npi_df, on="npi", how="left")
            print(f"   📞 Attached phone numbers from NPI staging (unique NPIs: {before_merge} → {df['npi'].nunique()})")
        except Exception as e:
            print(f"   ⚠️  Failed to attach phone numbers from NPI staging: {e}")
    else:
        print("   ⚠️  NPI staging file not found, phone numbers will be blank in frontend.")

    # Normalize revenue units BEFORE sorting
    print("   🔧 Normalizing revenue units...")
    df['final_revenue'] = df['final_revenue'].apply(normalize_revenue)

    # Calculate lift values for sorting
    df['_lift_value'] = df.apply(
        lambda row: calculate_lift(
            final_revenue=row['final_revenue'],
            undercoding_ratio=row.get('undercoding_ratio'),
            psych_risk_ratio=row.get('psych_risk_ratio'),
            segment_label=str(row.get('segment_label', 'Unknown')),
            scoring_track=str(row.get('scoring_track', 'AMBULATORY'))
        )['total_opportunity_value'],
        axis=1
    )

    # Sort by ICP Score DESC, then Lift Value DESC
    df = df.sort_values(['icp_score', '_lift_value'], ascending=[False, False])

    # Filter: Top 5,000 by ICP Score
    top_clinics = df.head(5000)
    print(f"   Selected Top 5,000 leads (scores: {top_clinics['icp_score'].min()}-{top_clinics['icp_score'].max()})")

    # Transform data
    output_data = []
    verified_count = 0
    projected_count = 0
    revenue_normalized_count = 0
    fqhc_discounted_count = 0
    winning_clinics_count = 0

    for _, row in top_clinics.iterrows():
        # Extract production columns
        npi = str(row.get('npi', ''))
        org_name = str(row.get('org_name', 'Unknown Clinic')).title()
        state = str(row.get('state_code', 'Unknown'))
        city = str(row.get('city', ''))
        icp_score = round(float(row.get('icp_score', 0)), 1)  # Preserve decimal precision
        icp_tier = str(row.get('icp_tier', 'Tier 4'))
        segment_label = str(row.get('segment_label', 'Unknown'))

        # Volume & Revenue (normalized)
        real_annual_encounters = row.get('real_annual_encounters')
        final_revenue = row.get('final_revenue')

        # Track normalization
        original_revenue = row.get('final_revenue')
        if pd.notna(original_revenue) and original_revenue > 0 and original_revenue < 10_000:
            revenue_normalized_count += 1

        volume = format_volume(real_annual_encounters)
        revenue = format_revenue(final_revenue)

        # Drivers (parse emoji-based string)
        scoring_drivers = row.get('scoring_drivers', '')
        drivers = parse_drivers(scoring_drivers)

        # Lift Calculation - NEW: Enhanced with payer mix and denial prevention
        undercoding_ratio = row.get('undercoding_ratio')
        psych_risk_ratio = row.get('psych_risk_ratio')
        scoring_track = str(row.get('scoring_track', 'AMBULATORY'))

        # Call enhanced lift calculation
        lift_result = calculate_lift(
            final_revenue=final_revenue,
            undercoding_ratio=undercoding_ratio,
            psych_risk_ratio=psych_risk_ratio,
            segment_label=segment_label,
            scoring_track=scoring_track
        )

        # Unpack for backward compatibility
        lift_value = lift_result['total_opportunity_value']
        lift_label = lift_result['lift_basis']
        is_projected = lift_result['is_projected_lift']
        est_revenue_lift = format_revenue(lift_value)

        # Track statistics
        if is_projected:
            projected_count += 1
        else:
            verified_count += 1

        if lift_result['payer_mix_applied']:
            fqhc_discounted_count += 1

        if lift_result['winning_status'] == 'WINNING':
            winning_clinics_count += 1

        # Billing Ratio Chart
        billing_ratio = calculate_billing_ratio(undercoding_ratio)

        # Primary driver (first driver or default)
        if drivers:
            primary_driver = f"Detected: {drivers[0]['label']}"
        else:
            primary_driver = "Detected: Standard Opportunity"

        # Fit reason (simplified)
        if icp_score >= 70:
            fit_reason = "High-priority target with strong operational fit and verified pain signals."
        elif icp_score >= 50:
            fit_reason = "Qualified prospect with good fit profile."
        else:
            fit_reason = "Standard opportunity."

        # Contact info
        phone = format_phone(row.get('phone'))
        address = f"{city.title()}, {state}" if city else state

        # ========================================
        # GLASS BOX ANALYSIS (Critique #4, #8)
        # ========================================
        analysis = {
            'strategic_brief': generate_strategic_brief(row, lift_value),  # Analyst report (not sales pitch)
            'gaps': identify_data_gaps(row),
            'benchmarks': generate_benchmarks(row),
            'raw_scores': extract_raw_scores(row),
            'score_reasoning': {
                'pain': parse_reasoning_string(row.get('score_reasoning_pain', '')),
                'fit': parse_reasoning_string(row.get('score_reasoning_fit', '')),
                'strategy': parse_reasoning_string(row.get('score_reasoning_strategy', '')),
                'bonus': []  # Keep for compatibility
            },  # Use backend's detailed clinic-specific reasoning
            'data_confidence': str(row.get('data_confidence', 'Unknown'))
        }

        # MIPS and HPSA/MUA data
        avg_mips_score = row.get('avg_mips_score')
        mips_clinician_count = row.get('mips_clinician_count')
        is_hpsa = str(row.get('is_hpsa', '')).lower() == 'true'
        is_mua = str(row.get('is_mua', '')).lower() == 'true'
        county_name = str(row.get('county_name', ''))

        # Scoring Track (for transparency)
        scoring_track = str(row.get('scoring_track', 'AMBULATORY'))

        # Dynamic Pain Label (NEW) - Remove emojis for professional display
        pain_label = remove_emojis(str(row.get('pain_label', 'Economic Pain')))

        # Volume Unit (NEW) - Critical for accurate labeling
        volume_unit = str(row.get('volume_unit', 'encounters'))  # Default to encounters (conservative)

        # Assemble clinic object
        clinic = {
            "id": npi,
            "name": org_name,
            "tier": icp_tier,
            "score": icp_score,
            "segment": segment_label,
            "state": state,
            "revenue": revenue,
            "volume": volume,
            "volume_unit": volume_unit,  # NEW: "patients" or "encounters" for UI labeling
            "est_revenue_lift": est_revenue_lift,
            "is_projected_lift": is_projected,
            "lift_basis": lift_label,
            "opportunity_breakdown": {
                "total": format_revenue(lift_result['total_opportunity_value']),
                "coding_lift": format_revenue(lift_result['coding_lift_value']),
                "denial_prevention": format_revenue(lift_result['denial_prevention_value']),
                "payer_mix_applied": lift_result['payer_mix_applied'],
                "winning_status": lift_result['winning_status']
            },
            "billing_ratio": billing_ratio,
            "primary_driver": primary_driver,
            "drivers": drivers,
            "scoring_track": scoring_track,  # NEW: Track transparency
            "pain_label": pain_label,  # NEW: Dynamic pain driver label
            "contact": {
                "phone": phone,
                "email": "N/A",
                "address": address
            },
            "fit_reason": fit_reason,
            "details": {
                "raw": {
                    "undercoding_ratio": float(undercoding_ratio) if pd.notna(undercoding_ratio) else None,
                    "volume_source": str(row.get('volume_source', 'Unknown')),
                    "volume_unit": volume_unit,  # NEW: Add to raw details for tooltip logic
                    "revenue_source": str(row.get('revenue_source', 'Unknown')),
                    "avg_mips_score": float(avg_mips_score) if pd.notna(avg_mips_score) else None,
                    "mips_clinician_count": int(mips_clinician_count) if pd.notna(mips_clinician_count) else None,
                    "is_hpsa": is_hpsa,
                    "is_mua": is_mua,
                    "county_name": county_name if pd.notna(county_name) and county_name != 'nan' else None,
                    "procedure_ratio": float(row.get('procedure_ratio')) if pd.notna(row.get('procedure_ratio')) else None,
                    "total_procedure_codes": float(row.get('total_procedure_codes')) if pd.notna(row.get('total_procedure_codes')) else None,
                    "total_eval_codes": float(row.get('total_eval_codes')) if pd.notna(row.get('total_eval_codes')) else None,
                    "total_psych_codes": float(row.get('total_psych_codes')) if pd.notna(row.get('total_psych_codes')) else None
                }
            },
            "analysis": analysis  # NEW: Glass box insights
        }

        output_data.append(clinic)

    # Save to JSON
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(output_data, f, indent=2)

    # Summary
    print(f"\n✅ Frontend JSON Generated: {OUTPUT_JSON}")
    print(f"   Total Records: {len(output_data):,}")
    print(f"   Revenue Normalized: {revenue_normalized_count:,} clinics (< $10k → * 1,000)")
    print(f"   Verified Opportunities: {verified_count} ({verified_count/len(output_data)*100:.1f}%)")
    print(f"   Projected Opportunities: {projected_count} ({projected_count/len(output_data)*100:.1f}%)")
    print(f"   FQHCs with Payer Mix Discount: {fqhc_discounted_count} ({fqhc_discounted_count/len(output_data)*100:.1f}%)")
    print(f"   'Winning' Clinics (0 Coding Lift): {winning_clinics_count} ({winning_clinics_count/len(output_data)*100:.1f}%)")
    print(f"\n📊 Score Distribution:")
    print(f"   Tier 1 (≥70): {sum(1 for c in output_data if c['score'] >= 70)}")
    print(f"   Tier 2 (50-69): {sum(1 for c in output_data if 50 <= c['score'] < 70)}")
    print(f"   Tier 3 (<50): {sum(1 for c in output_data if c['score'] < 50)}")
    print(f"\n🔍 Data Quality:")
    avg_gaps = sum(len(c['analysis']['gaps']) for c in output_data) / len(output_data)
    print(f"   Average Data Gaps: {avg_gaps:.1f} per clinic")


if __name__ == "__main__":
    generate_json()
