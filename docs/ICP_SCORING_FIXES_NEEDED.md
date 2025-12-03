# ICP Scoring System - Critical Fixes Needed

## 🚨 Problem Statement

**Severe score compression**: 76% of 1.4M clinics have IDENTICAL ICP scores, making ranking meaningless.

### Current State (Bad)

```
Component Score Unique Values:
- Fit Score:        7 values  (should be ~1000+)
- Pain Score:       3 values  (should be ~1000+)
- Compliance:       5 values  (should be ~1000+)
- Propensity:       4 values  (should be ~1000+)
- Scale Score:     17 values  (best, but still low)
- Segment Score:    3 values  (should be ~100+)

Result: Only 173 unique score patterns for 1,448,807 clinics
```

### Impact

1. **Rankings are meaningless**: 1.1M clinics tie at score=46
2. **Tier assignments are crude**: Most clinics bunch in Tier 3
3. **Sales can't prioritize**: No differentiation within tiers
4. **FQHCs invisible**: 494 FQHCs tie at 49.0 points

---

## 🎯 Solution: Continuous Percentile-Based Scoring

### Current Approach (Fixed Buckets) ❌

```python
# BAD: Fixed points create compression
if "behavioral health" in segment:
    score += 18.0  # ALL behavioral health get same points
elif "fqhc" in segment:
    score += 16.0  # ALL FQHCs get same points
elif "primary care" in segment:
    score += 15.0  # ALL primary care get same points
```

**Result**: All clinics in same segment get identical base scores.

### Improved Approach (Continuous Scoring) ✅

```python
# GOOD: Use actual data values with percentile-based scoring
def compute_fit_score_v2(row, stats):
    score = 0.0
    
    # 1. Segment base (use gradations, not fixed values)
    segment_scores = {
        "behavioral_health": 18.0,
        "home_health": 17.5,
        "fqhc": 16.0,
        "primary_care": 15.0,
        "multi_specialty": 13.0,
        "other": 10.0
    }
    base = segment_scores.get(segment, 10.0)
    
    # 2. Add continuous modifiers based on actual data
    # Provider count (0-3 points, continuous)
    npi_count = row.get('npi_count', 0)
    if stats['npi_count_max'] > 0:
        npi_percentile = npi_count / stats['npi_count_max']
        score += base + (npi_percentile * 3.0)  # Scales with actual size
    
    # 3. Service complexity (0-2 points, continuous)
    services = row.get('services_count', 0)
    if stats['services_max'] > 0:
        services_percentile = services / stats['services_max']
        score += services_percentile * 2.0  # NOT binary threshold
    
    # 4. Geographic spread (0-2 points, continuous)
    site_count = row.get('site_count', 1)
    if stats['site_count_max'] > 0:
        site_percentile = site_count / stats['site_count_max']
        score += site_percentile * 2.0
    
    return min(20.0, score)
```

**Result**: Each clinic gets unique score based on actual data.

---

## 📋 Specific Fixes Needed (By Component)

### 1. Fit Score (0-20) - Currently 7 unique values

**Problems:**
- Fixed segment values (18, 16, 15, 13, 10)
- Binary bonuses (+2 if site_count >= 5, +3 if services >= 10)

**Fixes:**
```python
# Replace lines 152-191 in score_icp.py with:

# Segment base (keep but add micro-adjustments)
base_score = segment_base_scores[segment]

# Add continuous modifiers:
# 1. Provider density (use percentile)
provider_percentile = np.clip(npi_count / stats['npi_75th'], 0, 1)
score += base_score + (provider_percentile * 2.0)

# 2. Service breadth (continuous, not threshold)
if services_count > 0:
    service_percentile = np.clip(services_count / stats['services_75th'], 0, 1)
    score += service_percentile * 3.0

# 3. Geographic spread (continuous)
if site_count > 1:
    site_percentile = np.clip(site_count / stats['site_75th'], 0, 1)
    score += site_percentile * 2.0

# 4. Add small jitter for tie-breaking (optional)
score += hash(clinic_id) % 100 / 1000.0  # 0.000-0.099 variation
```

### 2. Pain Score (0-20) - Currently 3 unique values

**Problems:**
- Only 3 fixed values: 15.0, 5.0, 2.0
- Based purely on segment, no clinic-specific variation

**Current Logic:**
```python
if segment in high_pain_segments:
    return 15.0  # ALL high-pain clinics get 15
elif segment in medium_pain_segments:
    return 5.0   # ALL medium-pain get 5
else:
    return 2.0   # ALL others get 2
```

**Fixes:**
```python
# Use segment as BASE, then add modifiers

base_pain = {
    "behavioral_health": 15.0,
    "home_health": 14.0,
    "fqhc": 12.0,
    "primary_care": 5.0,
    "multi_specialty": 4.0,
    "other": 2.0
}[segment]

# Add denial risk proxy (use claims volume as indicator)
if 'bene_count' in row:
    # Higher volume → higher denial risk
    bene_percentile = np.clip(bene_count / stats['bene_75th'], 0, 1)
    pain_modifier = bene_percentile * 3.0  # 0-3 points based on volume
    
# Add Medicaid exposure (proxy via FQHC/safety net)
if row.get('fqhc_flag') == 1:
    pain_modifier += 2.0  # FQHCs have Medicaid complexity
    
# Add staffing strain (proxy via provider count vs volume)
if npi_count > 0 and bene_count > 0:
    volume_per_provider = bene_count / npi_count
    if volume_per_provider > stats['volume_per_provider_75th']:
        pain_modifier += 1.5  # Understaffed

return min(20.0, base_pain + pain_modifier)
```

### 3. Compliance Score (0-10) - Currently 5 unique values

**Problems:**
- Simple threshold logic
- Doesn't differentiate within FQHC category

**Fixes:**
```python
# FQHC audit risk (use continuous scoring)
if fqhc_flag == 1:
    base = 6.0
    # Add modifiers based on complexity
    if 'bene_count' in row:
        # More patients → more audit risk
        patient_risk = np.clip(bene_count / stats['fqhc_bene_median'], 0, 2)
        base += patient_risk
    if 'services_count' in row:
        # More services → more coding risk
        service_risk = np.clip(services_count / 15, 0, 2)
        base += service_risk
    return min(10.0, base)

# Behavioral health prior auth risk
if "behavioral" in segment:
    base = 4.0
    # Add modifiers
    ...

# Use revenue as proxy for audit exposure
if 'allowed_amt' in row:
    revenue_percentile = np.clip(allowed_amt / stats['allowed_amt_90th'], 0, 1)
    return min(10.0, base + revenue_percentile * 3.0)
```

### 4. Propensity Score (0-10) - Currently 4 unique values

**Problems:**
- Only 4 fixed values: 8.0, 4.0, 3.0, 0.0
- No clinic-specific variation

**Fixes:**
```python
# Use multiple signals, weight them

propensity = 0.0

# 1. Financial pressure (revenue per provider)
if npi_count > 0 and allowed_amt > 0:
    revenue_per_provider = allowed_amt / npi_count
    if revenue_per_provider < stats['revenue_per_provider_25th']:
        propensity += 3.0  # Below median → higher propensity
    elif revenue_per_provider < stats['revenue_per_provider_median']:
        propensity += 2.0

# 2. Growth trajectory (site expansion)
if site_count >= 3:
    propensity += 2.0  # Multi-site → growth-oriented

# 3. Technology readiness (EHR adoption proxy)
# Use pecos_enrolled as proxy for digital maturity
if pecos_enrolled == 1:
    propensity += 1.5

# 4. Market pressure (use state-level metrics)
# States with high denial rates → higher propensity
state_denial_risk = STATE_DENIAL_RATES.get(state_code, 0.12)
propensity += (state_denial_risk - 0.10) * 20  # Scale to 0-2 points

return min(10.0, propensity)
```

### 5. Scale Score (0-20) - Currently 17 values (BEST)

**Status**: Already better than others, but can improve

**Fixes:**
```python
# Use continuous percentile-based scoring throughout
# Current approach uses some thresholds - make all continuous

# Provider count (0-8 points, continuous)
if stats['npi_count_max'] > 0:
    npi_score = (npi_count / stats['npi_count_max']) * 8.0

# Site count (0-4 points, continuous)
if stats['site_count_max'] > 0:
    site_score = (site_count / stats['site_count_max']) * 4.0

# Patient volume (0-4 points, continuous)
if stats['bene_count_max'] > 0:
    bene_score = (bene_count / stats['bene_count_max']) * 4.0

# Revenue (0-4 points, continuous)
if stats['allowed_amt_max'] > 0:
    revenue_score = (allowed_amt / stats['allowed_amt_max']) * 4.0

return min(20.0, npi_score + site_score + bene_score + revenue_score)
```

### 6. Segment Score (0-20) - Currently 3 unique values

**Problems:**
- Only 3 values: 20.0, 14.0, 8.0
- Pure segment classification, no variation

**Fixes:**
```python
# Keep segment as base, add strategic indicators

segment_base = {
    "behavioral_health": 20.0,  # High strategic value
    "home_health": 19.0,
    "fqhc": 18.0,
    "primary_care": 14.0,
    "multi_specialty": 12.0,
    "other": 8.0
}[segment]

# Add modifiers for strategic fit

# 1. Value-based care participation
if aco_member == 1:
    segment_base += 2.0  # VBC-ready

# 2. Market position (use revenue as proxy)
if allowed_amt > stats['allowed_amt_75th']:
    segment_base += 1.5  # Market leader

# 3. Innovation readiness (multi-site + high services)
if site_count >= 5 and services_count >= 15:
    segment_base += 1.0  # Sophisticated operation

return min(20.0, segment_base)
```

---

## 🔧 Implementation Plan

### Phase 1: Quick Wins (1-2 hours)

1. **Add tie-breaking hash** to all scores:
   ```python
   # At end of each compute_X_score function:
   score += hash(row['clinic_id']) % 100 / 1000.0  # 0.000-0.099
   ```

2. **Make Scale Score fully continuous** (already best, just refine)

3. **Add jitter to Fit Score** using actual data percentiles

**Result**: Unique scores for most clinics, minimal code changes

### Phase 2: Moderate Improvements (4-6 hours)

1. **Rewrite Fit Score** with continuous percentile-based scoring
2. **Rewrite Compliance Score** with FQHC-specific modifiers
3. **Improve Propensity Score** with multi-signal approach

**Result**: Much better differentiation, scores reflect actual data

### Phase 3: Complete Overhaul (8-12 hours)

1. **Rewrite all 6 scoring functions** with continuous scoring
2. **Add state-level benchmarking** (compare clinic to state peers)
3. **Implement percentile ranks** for all numeric features
4. **Add composite indices** (e.g., "efficiency score" = revenue per provider)

**Result**: Production-grade scoring system with meaningful rankings

---

## 📊 Validation Criteria

After implementing fixes, verify:

1. **Unique patterns**: Should cover >80% of clinics
2. **Top pattern**: Should represent <5% of clinics
3. **Component variance**: Each component should have 100+ unique values
4. **Segment differentiation**: Within-segment scores should vary widely
5. **FQHC distribution**: 1,632 FQHCs should have >500 unique scores

Run diagnostic:
```bash
python3 scripts/diagnose_score_compression.py
```

Target output:
```
Unique score patterns: 1,200,000+ (83%+)
Clinics with duplicate patterns: <250,000
Top pattern coverage: <3%
Component unique values: Fit=2000+, Pain=1000+, etc.
```

---

## 🚀 Quick Start for Developer

### Immediate Fix (30 minutes)

Add this to `score_icp.py` line 878 (before rounding):

```python
# Add tie-breaking variance based on clinic characteristics
# Use deterministic hash so scores are reproducible
clinic_hash = hash(base['clinic_id']) % 10000
tie_breaker = clinic_hash / 100000.0  # 0.00000-0.09999

total_icp = (
    fit_score + pain_score + compliance_score + 
    propensity_score + scale_score + segment_score +
    tie_breaker  # Adds up to 0.1 points variation
)
```

Then regenerate scores:
```bash
python3 workers/score_icp.py
```

**Impact**: Breaks most ties, minimal effort.

### For Full Fix

See Phase 2-3 above. Budget 1-2 days for complete overhaul.

---

## 📚 References

- Current scoring code: `workers/score_icp.py` lines 114-800
- Diagnostic script: `scripts/diagnose_score_compression.py`
- Original ICP methodology: `docs/ICP_SCORING_SYSTEM.md`

**Status**: CRITICAL - Scoring system needs overhaul for production use

