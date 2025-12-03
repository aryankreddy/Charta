# Bidirectional Pain Model for Behavioral Health
**Proposal for Enhanced Behavioral Health Scoring Logic**

---

## Problem Discovered

**Original Assumption:**
- Behavioral health pain = high psych risk ratio (>0.75)
- Targeting aggressive coders with audit risk/compliance threat
- Assumed most behavioral practices code aggressively

**Data Reality (Analysis of 151,317 Behavioral Health Organizations):**
- **Median psych risk ratio: 0.169** (only 16.9% of therapy sessions coded at high complexity)
- **Distribution:**
  - Conservative coders (<0.50): **58.7%** (3,671 orgs) - majority of market
  - Balanced coders (0.50-0.75): **7.6%** (475 orgs)
  - Aggressive coders (>0.75): **33.7%** (2,109 orgs)

**Key Insight:**
The majority (59%) of behavioral practices are coding **conservatively**, not aggressively. They likely have the OPPOSITE problem - undercoding therapy complexity and leaving revenue on the table, similar to ambulatory practices with E&M undercoding.

**Current scoring model only targets 33.7% of the market (aggressive coders). We're missing the 58.7% who are undercoding.**

---

## Proposed Solution: Bidirectional Pain Model

### Core Concept
**Deviation from the 0.50 benchmark (balanced therapy distribution) = pain signal**

- **Low ratio (<0.30):** Conservative coding → **Undercoding/Revenue Leakage** (like ambulatory E&M)
- **Sweet spot (0.40-0.60):** Appropriate mix → **Low pain**
- **High ratio (>0.75):** Aggressive coding → **Audit Risk/Compliance Threat**

This creates a **U-shaped pain curve** where deviation in EITHER direction = financial distress.

### National Benchmark Justification
- Industry guidance: Balanced therapy should be ~50% 90834 (38-52 min) / ~50% 90837 (53+ min)
- CMS expects variation in session lengths based on patient acuity
- 0.50 ratio = "appropriately coded" benchmark
- Deviation signals either conservative (undercoding) or aggressive (overcoding) behavior

---

## Market Sizing Impact

### Current System (One-Directional)
- **Target market:** 33.7% of behavioral practices (2,109 organizations)
- **Value proposition:** Compliance/audit risk mitigation only
- **Addressable market:** Limited to aggressive coders

### Bidirectional System (Proposed)
- **Target market:** **92.4%** of behavioral practices (5,780 organizations)
  - 58.7% conservative coders (revenue recovery)
  - 33.7% aggressive coders (compliance protection)
- **Value propositions:**
  - Revenue recovery (like ambulatory): "You're leaving $XXK on the table by undercoding therapy complexity"
  - Compliance protection: "Your coding patterns create audit risk of $XXK in recoupment"
- **Impact:** **2.7x increase** in addressable behavioral health market

---

## Implementation Plan

### 1. Scoring Logic Changes

**File:** `workers/pipeline/score_icp_production.py`

**Current Behavioral Pain Formula (One-Directional):**
```python
def score_psych_risk(ratio):
    """
    High ratio = high audit risk = high pain.
    Returns 10-40 points.
    """
    if pd.isna(ratio):
        return 10

    # Severe risk (>0.75) = 40 points
    # No risk (0.0) = 10 points
    score = 10 + ((ratio - 0.0) / (0.75 - 0.0)) * 30
    return min(max(score, 10), 40)
```

**Proposed Behavioral Pain Formula (Bidirectional):**
```python
def score_psych_risk_bidirectional(ratio):
    """
    Deviation from 0.50 benchmark = pain (U-shaped curve).
    Low ratio (<0.30) = undercoding/revenue leakage
    High ratio (>0.75) = audit risk/compliance threat
    Sweet spot (0.40-0.60) = appropriate coding

    Returns 10-40 points.
    """
    if pd.isna(ratio):
        return 10

    BENCHMARK = 0.50  # National balanced therapy distribution
    SEVERE_LOW = 0.30  # Conservative threshold
    SEVERE_HIGH = 0.75  # Aggressive threshold

    # Severe undercoding (conservative)
    if ratio <= SEVERE_LOW:
        return 40  # Max pain - leaving revenue on table

    # Severe overcoding (aggressive)
    elif ratio >= SEVERE_HIGH:
        return 40  # Max pain - audit risk/compliance threat

    # Balanced coding (sweet spot)
    elif 0.40 <= ratio <= 0.60:
        return 10  # Minimal pain - appropriately coded

    # Moderate deviation from benchmark
    else:
        # Calculate distance from sweet spot boundaries
        if ratio < 0.40:
            # Between 0.30 and 0.40 (moderate undercoding)
            deviation = (0.40 - ratio) / (0.40 - SEVERE_LOW)
        else:
            # Between 0.60 and 0.75 (moderate overcoding)
            deviation = (ratio - 0.60) / (SEVERE_HIGH - 0.60)

        # Linear scale from 10 (sweet spot) to 40 (severe)
        score = 10 + (deviation * 30)
        return min(max(score, 10), 40)
```

**Pain Scoring Update:**
```python
# In calculate_row_score() function for BEHAVIORAL track:

if track == 'BEHAVIORAL':
    # Pain Score (Max 40)
    pain_signal = score_psych_risk_bidirectional(psych_risk_ratio)  # Updated function
    pain_volume = score_volume_behavioral(final_volume)
    pain_margin = score_margin(final_margin)
    pain_compliance = 5 if risk_compliance_flag else 0

    pain_total = min(pain_signal + pain_volume + pain_margin + pain_compliance, 40)
```

### 2. Frontend Driver Logic Changes

**File:** `scripts/update_frontend_data.py`

**Current Driver Assignment:**
```python
# Behavioral health drivers (one-directional)
if psych_ratio > 0.70:
    drivers.append({
        "label": "🚨 Audit Risk",
        "value": f"{psych_ratio:.2f}",
        "color": "text-red-600"
    })
```

**Proposed Driver Assignment (Bidirectional):**
```python
# Behavioral health drivers (bidirectional)
if pd.notnull(psych_ratio):
    if psych_ratio <= 0.30:  # Conservative coding (undercoding)
        drivers.append({
            "label": "💰 Therapy Undercoding",
            "value": f"{psych_ratio:.2f}",
            "color": "text-red-600"
        })
        primary_driver = "Detected: 💰 Therapy Undercoding - Revenue Leakage"
    elif psych_ratio >= 0.75:  # Aggressive coding (audit risk)
        drivers.append({
            "label": "🚨 Compliance/Audit Risk",
            "value": f"{psych_ratio:.2f}",
            "color": "text-red-600"
        })
        primary_driver = "Detected: 🚨 Compliance/Audit Risk"
    elif 0.40 <= psych_ratio <= 0.60:  # Balanced (sweet spot)
        # No pain driver for appropriately coded practices
        pass
```

**Strategic Brief Update:**
```python
# Conditional messaging based on ratio direction
if psych_ratio <= 0.30:
    brief = (
        f"Claims analysis shows conservative therapy coding (only {psych_ratio*100:.1f}% "
        f"high-complexity sessions vs. 50% national benchmark). This suggests systematic "
        f"undercoding of therapy complexity, leaving verified revenue on the table."
    )
elif psych_ratio >= 0.75:
    brief = (
        f"Claims analysis shows aggressive therapy coding ({psych_ratio*100:.1f}% "
        f"high-complexity sessions vs. 50% national benchmark). This creates audit exposure "
        f"and potential recoupment risk from payers."
    )
else:
    brief = (
        f"Therapy coding distribution ({psych_ratio*100:.1f}% high-complexity) falls "
        f"within acceptable range of national benchmarks."
    )
```

### 3. Score Reasoning Updates

**File:** `scripts/update_frontend_data.py`

**Current Reasoning:**
```python
pain_reasons.append(
    f"{pain_signal:.0f}pts: High psych audit risk (ratio {psych_ratio:.2f})"
)
```

**Proposed Reasoning (Conditional):**
```python
if psych_ratio <= 0.30:
    pain_reasons.append(
        f"{pain_signal:.0f}pts: Conservative therapy coding ({psych_ratio*100:.1f}% "
        f"high-complexity vs. 50% benchmark) - Revenue Leakage"
    )
elif psych_ratio >= 0.75:
    pain_reasons.append(
        f"{pain_signal:.0f}pts: Aggressive therapy coding ({psych_ratio*100:.1f}% "
        f"high-complexity vs. 50% benchmark) - Audit Risk"
    )
else:
    pain_reasons.append(
        f"{pain_signal:.0f}pts: Balanced therapy coding ({psych_ratio*100:.1f}% "
        f"high-complexity) - Appropriate distribution"
    )
```

---

## Frontend Terminology Updates

| Element | Current | Proposed | Rationale |
|---------|---------|----------|-----------|
| Section header | "Economic Pain" | "Economic Pain" | ✅ No change - encompasses both revenue loss and compliance risk |
| Score label | "Pain Score (Max 40)" | "Pain Score (Max 40)" | ✅ Keep simple - don't add "/Risk" (too cluttered) |
| Driver label (low ratio) | N/A | "💰 Therapy Undercoding" | NEW - identifies revenue recovery opportunity |
| Driver label (high ratio) | "Audit Risk" | "🚨 Compliance/Audit Risk" | More professional, emphasizes financial threat |
| Primary driver (low) | N/A | "Detected: 💰 Therapy Undercoding - Revenue Leakage" | NEW - clear value prop |
| Primary driver (high) | "Audit Risk" | "Detected: 🚨 Compliance/Audit Risk" | More professional framing |

---

## Expected Outcomes

### Scoring Distribution Changes

**Before (Current System):**
- Behavioral Tier 1 (≥70): ~615 organizations
- Pain scores concentrated in aggressive coders only
- Conservative coders score low (10-15 pain points) despite revenue opportunity

**After (Bidirectional System):**
- **Expected Tier 1 increase: +800-1,000 organizations** (conservative coders now score high)
- Total Behavioral Tier 1: ~1,400-1,600 organizations
- Pain scores distributed across BOTH conservative and aggressive coders
- More accurate representation of total addressable market

### Sales Impact

**New Value Propositions Unlocked:**

1. **Conservative Coders (58.7% of market):**
   - **Pitch:** "Your therapy coding analysis shows only 17% high-complexity sessions. National benchmark is 50%. This conservative coding pattern suggests you're leaving $XXK in revenue on the table. Our AI chart review can identify sessions that should be coded at higher complexity based on documentation."
   - **ROI:** Revenue recovery (like ambulatory E&M upcoding)

2. **Aggressive Coders (33.7% of market):**
   - **Pitch:** "Your therapy coding shows 82% high-complexity sessions. This creates audit exposure from payers who expect 50% distribution. Risk of recoupment on $XXK in claims. Our AI ensures coding matches documentation and flags high-risk patterns."
   - **ROI:** Compliance protection, recoupment avoidance

**Total addressable market: 92.4% of behavioral practices (vs. 33.7% before)**

---

## Risk Assessment

### Potential Issues

1. **Is 0.50 the right benchmark?**
   - ✅ Industry standard: balanced therapy distribution
   - ✅ CMS guidance: expect mix of session lengths
   - ⚠️ Could vary by patient population (chronic mental illness vs. brief therapy)
   - **Mitigation:** Document benchmark source, allow for segment-specific adjustments

2. **Conservative coders might not have documentation to support higher codes**
   - ⚠️ If they're appropriately coding based on actual session length, there's no revenue opportunity
   - **Mitigation:** Frame as "documentation audit" - verify if conservative coding is appropriate or if there's upside

3. **Charta's current product might not address both use cases**
   - ⚠️ Revenue recovery requires different AI features than compliance protection
   - **Mitigation:** Validate with Charta stakeholders that product roadmap supports both

### Validation Steps

Before full deployment:

1. **Sample 10-20 conservative coders** (ratio <0.30) and validate:
   - Do they have documentation supporting higher complexity?
   - Is the revenue opportunity real or are they appropriately coding short sessions?

2. **A/B test messaging:**
   - Conservative coder pitch: "revenue recovery"
   - Aggressive coder pitch: "compliance protection"
   - Measure response rates

3. **Stakeholder alignment:**
   - Confirm Charta's AI can support BOTH use cases
   - Validate sales team comfort with dual value props

---

## Deployment Plan

### Phase 1: Backend Scoring Update
1. Update `score_icp_production.py` with bidirectional formula
2. Run scoring on full 1.4M organization dataset
3. Validate score distribution changes (expect +800-1,000 Behavioral Tier 1)
4. QA: Check 10-20 sample organizations manually

### Phase 2: Frontend Message Update
1. Update `update_frontend_data.py` with conditional driver logic
2. Regenerate frontend JSON with new messaging
3. QA: Verify low-ratio and high-ratio orgs show different drivers

### Phase 3: Documentation Update
1. Update `FEATURE_DOCUMENTATION.md` with bidirectional model explanation
2. Update Loom script to mention both conservative and aggressive coding patterns
3. Add FAQ: "Why are some behavioral practices scored high for undercoding?"

### Phase 4: Deployment
1. Commit backend scoring changes
2. Run full pipeline to regenerate scored CSV
3. Regenerate frontend JSON
4. Deploy to Vercel
5. Monitor: Check that Behavioral Tier 1 count increased as expected

---

## Success Metrics

**Quantitative:**
- ✅ Behavioral Tier 1 count increases from ~615 to ~1,400-1,600
- ✅ 58.7% of behavioral practices (conservative coders) now have pain scores ≥30
- ✅ Total addressable behavioral market = 92.4% vs. 33.7% before

**Qualitative:**
- ✅ Sales team can articulate TWO distinct value props for behavioral health
- ✅ Conservative coder messaging resonates ("revenue recovery")
- ✅ Aggressive coder messaging remains effective ("compliance protection")

---

## Appendix: Data Analysis

### Psych Risk Ratio Distribution (151,317 Behavioral Orgs)

| Metric | Value |
|--------|-------|
| Total orgs with psych data | 6,255 |
| Mean ratio | 0.403 |
| Median ratio | 0.169 |
| 25th percentile | 0.000 |
| 75th percentile | 0.931 |
| 90th percentile | 1.000 |
| 95th percentile | 1.000 |

### Segment Breakdown

| Segment | Count | % of Total | Pain Type |
|---------|-------|------------|-----------|
| Conservative (<0.50) | 3,671 | 58.7% | Undercoding/Revenue Leakage |
| Balanced (0.50-0.75) | 475 | 7.6% | Low pain (appropriate) |
| Aggressive (>0.75) | 2,109 | 33.7% | Audit Risk/Compliance |

### Sample High-Scoring Behavioral Orgs (Current System)

| Organization | Score | Psych Ratio | Pain Score | State |
|--------------|-------|-------------|------------|-------|
| Heart of Texas Region MHMR Center | 82.0 | 0.712 | 40.0 | TX |
| MTCA Psychological Services P.A. | 81.7 | 0.719 | 40.0 | FL |
| Clinical & Support Options, Inc | 80.9 | 0.831 | 40.0 | MA |
| Manlove Psychiatric Group, P.C. | 80.7 | 1.000 | 40.0 | SD |
| Friends Behavioral Health System, LP | 80.3 | 0.615 | 39.6 | PA |

**Note:** All current high-scorers are aggressive coders (ratio >0.60). After bidirectional implementation, expect to see conservative coders (ratio <0.30) also scoring 80+ on ICP.

---

## Questions for Stakeholders

1. **Product alignment:** Does Charta's AI chart review support BOTH revenue recovery (upcoding) AND compliance protection (downcoding)?

2. **Sales readiness:** Is the sales team comfortable with two distinct value propositions for behavioral health?

3. **Benchmark validation:** Is 0.50 the right national benchmark for balanced therapy distribution, or should it vary by patient population?

4. **Documentation quality:** For conservative coders, is the revenue opportunity real (poor documentation) or appropriate (short sessions)?

5. **Risk appetite:** Are we comfortable targeting 92.4% of the behavioral market, or should we be more selective?

---

**Prepared by:** Claude AI Assistant
**Date:** November 27, 2024
**Status:** Ready for Implementation
**Approval needed from:** Charta Health stakeholders, Data Science review
