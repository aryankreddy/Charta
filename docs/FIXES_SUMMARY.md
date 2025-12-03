# GTM INTELLIGENCE: CRITICAL FIXES IMPLEMENTED

**Date:** 2025-12-02
**Status:** Ready for Testing - Pipeline Re-run Required

---

## 🎯 VISION ALIGNMENT

**Goal:** A Scored Lead Database with ICP scores derived from public data, focusing on relevant pain signals for each specialty.

**Problems Fixed:**
1. **Therapy coding applied too broadly** → Large health systems with incidental psych billing were flagged
2. **Procedure alignment invisible** → Backend logic existed but wasn't showing on frontend
3. **Vague segment labels** → "Segment A-F" instead of descriptive names
4. **Scoring hierarchy broken** → Therapy pain dominated when it shouldn't

---

## ✅ FIX #1: STRICT THERAPY RELEVANCE GATE (Percentage-Based)

### Problem
Health systems like Froedtert, Montefiore, and North Shore-LIJ were showing "Therapy Undercoding Pain" despite having <3% behavioral health volume. They do incidental screening/referrals, not specialized BH services.

### Solution
**Changed from absolute count gate to percentage-based gate:**

**OLD Logic (Broken):**
```python
if total_psych_codes >= 100:
    # Flag for therapy pain
```

**NEW Logic (Fixed):**
```python
# EDGE CASE: If eval_codes is missing, we can't calculate a valid percentage
# Conservative approach: set percentage to 0 (won't pass gate)
if not eval_codes_available:
    psych_percentage = 0
else:
    # Calculate therapy as % of total ambulatory volume
    psych_percentage = total_psych_codes / (total_psych_codes + total_eval_codes)

# STRICT GATE: Must be >20% of volume AND >100 absolute codes
if psych_percentage > 0.20 and total_psych_codes >= 100:
    # Flag for therapy pain
```

### Impact Examples

| Clinic | Psych Codes | Eval Codes | Percentage | OLD | NEW |
|--------|------------|------------|------------|-----|-----|
| Froedtert | 2,306 | 173,901 | **1.3%** | ❌ Flagged | ✅ Not flagged |
| Montefiore | 3,855 | 226,016 | **1.7%** | ❌ Flagged | ✅ Not flagged |
| North Shore Center | 302 | **NaN (missing)** | **N/A** | ❌ Flagged (100%) | ✅ Not flagged (edge case) |
| True BH Clinic | 800 | 1,000 | **80%** | ✅ Flagged | ✅ Flagged |
| FQHC with BH | 300 | 1,200 | **25%** | ✅ Flagged | ✅ Flagged |

**Edge Case Fixed (Dec 3, 2025):** Clinics with missing `total_eval_codes` now default to 0% psych percentage (conservative approach), preventing false positives where only psych codes exist without denominator data.

### Files Changed
- `workers/pipeline/score_icp_production.py` (lines 336-363, 571-597, 514-544)

---

## ✅ FIX #2: DESCRIPTIVE SEGMENT LABELS

### Problem
Clinics were labeled "Segment A", "Segment B", "Segment C" instead of meaningful names like "FQHC", "Hospital", "Private Practice".

### Solution
**Updated all segment assignments in pipeline:**

**OLD Labels:**
- Segment A → (ambiguous)
- Segment B → FQHC
- Segment C → (ambiguous)
- Segment D → (ambiguous)
- Segment E → (ambiguous)
- Segment F → Hospital

**NEW Labels:**
- **FQHC** - Federally Qualified Health Centers
- **Hospital** - Acute care hospitals
- **Home Health** - Home health agencies
- **Private Practice** - Single/small provider groups
- **Multi-specialty** - Large provider networks
- **Urgent Care** - Urgent care centers
- **Behavioral Health** - Mental health specialists
- **Specialty Group** - Specialty surgical groups

### Files Changed
- `workers/pipeline/pipeline_main.py` (lines 402-403, 424-425, 512, 610, 714, 749, 851, 1010)

---

## ✅ FIX #3: PROCEDURE ALIGNMENT VISIBILITY

### Problem
Procedure alignment logic was implemented in the backend but:
1. Not showing on frontend (data columns missing from JSON)
2. Not visible in scored data

### Solution

**Added procedure columns to frontend data:**
```python
"procedure_ratio": float(row.get('procedure_ratio')),
"total_procedure_codes": float(row.get('total_procedure_codes')),
"total_eval_codes": float(row.get('total_eval_codes')),
"total_psych_codes": float(row.get('total_psych_codes'))
```

**Verified staging data exists:**
- ✅ 70,017 clinics have procedure data in `stg_undercoding_metrics.csv`
- ✅ Average procedure ratio: 33.9%
- ✅ Scoring logic properly identifies deficits (e.g., Podiatry at 10% vs 60% expected)

### What This Enables
For procedure-heavy specialties (Podiatry, Orthopedics, Dermatology, Ophthalmology):
- **Pain Driver:** "⚠️ Procedure Alignment (10% vs 60% expected)"
- **Pain Label:** "Procedure Alignment Pain" (when dominant signal)
- **Specialty Targets:**
  - Podiatry: 60% procedures expected
  - Orthopedics: 50% procedures expected
  - Ophthalmology: 60% procedures expected
  - Dermatology: 50% procedures expected

### Files Changed
- `scripts/update_frontend_data.py` (lines 870-873)

---

## 🔧 REQUIRED NEXT STEPS

**CRITICAL: You must re-run the pipeline for these fixes to take effect.**

### Step 1: Verify CPT Mining Has Procedure Data
```bash
# Check if procedure columns exist
head -1 data/curated/staging/stg_undercoding_metrics.csv

# Expected output should include: total_procedure_codes,procedure_ratio
```

### Step 2: Re-run Scoring Pipeline
```bash
python3 workers/pipeline/score_icp_production.py
```

**This will:**
- Apply the new 20% therapy relevance gate
- Use descriptive segment labels (FQHC, Hospital, etc.)
- Merge procedure alignment data
- Generate new `clinics_scored_final.csv`

### Step 3: Update Frontend Data
```bash
python3 scripts/update_frontend_data.py
```

**This will:**
- Include procedure alignment columns in JSON
- Export top 5,000 leads with new scoring

### Step 4: Validate Fixes
```bash
python3 scripts/validate_fixes.py
```

**This will:**
- Test therapy relevance gate (should filter out <20% psych volume)
- Check segment labels (should be descriptive, not A-F)
- Verify procedure alignment data exists
- Generate validation report

---

## 📊 EXPECTED OUTCOMES

### Before Fixes
- **Therapy Pain:** 152,821 clinics (includes major health systems)
- **Segment Labels:** "Segment A-F" (unclear meaning)
- **Procedure Alignment:** Not visible on frontend
- **Problem:** Froedtert, Montefiore showing "Therapy Undercoding Pain"

### After Fixes
- **Therapy Pain:** ~5,000-10,000 clinics (only true BH specialists with >20% volume)
- **Segment Labels:** "FQHC", "Hospital", "Private Practice" (clear meaning)
- **Procedure Alignment:** Visible for applicable specialties
- **Fix:** Froedtert, Montefiore show "E&M Undercoding" or other appropriate pain

### Pain Distribution (Expected)
```
Undercoding Pain:           90-95% (E&M is universal)
Therapy Undercoding Pain:    2-5% (only BH specialists)
Procedure Alignment Pain:    1-2% (specialty-specific)
Margin Pressure:            <1% (hospitals/HHAs)
```

---

## 🧪 TEST CASES

### Test Case 1: Major Health System
**Clinic:** Froedtert & The Medical College of Wisconsin
- **Data:** 2,306 psych / 173,901 total = 1.3%
- **Expected:** Pain Label = "E&M Undercoding" (NOT therapy)
- **Validation:** No therapy-related drivers in frontend

### Test Case 2: True Behavioral Health Clinic
**Clinic:** Community Mental Health Center
- **Data:** 800 psych / 1,000 total = 80%
- **Expected:** Pain Label = "Therapy Undercoding Pain" OR "Therapy Audit Risk"
- **Validation:** Therapy driver in frontend

### Test Case 3: Podiatry Practice
**Clinic:** Any podiatry practice
- **Data:** Taxonomy 213E, procedure_ratio = 0.10 (expected 0.60)
- **Expected:** Pain Label = "Procedure Alignment Pain"
- **Validation:** Driver shows "⚠️ Procedure Alignment (10% vs 60% expected)"

### Test Case 4: FQHC
**Clinic:** Any FQHC
- **Data:** Has fqhc_revenue data
- **Expected:** Segment Label = "FQHC" (not "Segment B")
- **Validation:** Segment shows clearly in frontend

---

## 🎓 TECHNICAL NOTES

### Why 20% Threshold?
- **True BH clinics:** 60-90% of volume is psych codes
- **Integrated BH (FQHCs):** 20-40% of volume is psych codes
- **Incidental screening:** <5% of volume is psych codes

The 20% threshold ensures we only flag clinics where behavioral health is a **core service line**, not just incidental.

### Why Percentage vs. Absolute?
A 20,000-patient cardiology practice with 150 psych codes (0.75%) is NOT a behavioral health clinic.
A 500-patient mental health clinic with 400 psych codes (80%) IS a behavioral health clinic.

Absolute counts don't account for clinic scale.

### Procedure Alignment Methodology
Based on Medicare national benchmarks by specialty:
- **Podiatry:** Should be 60% procedures (bunionectomies, nail care, wound debridement)
- **Ophthalmology:** Should be 60% procedures (cataract surgery, laser treatments)
- **Dermatology:** Should be 50% procedures (biopsies, lesion removal)

When actual ratio is 20%+ below expected → flags as "Procedure Alignment Pain"

---

## 📝 CODE QUALITY

### Tests Added
- `scripts/validate_fixes.py` - Comprehensive validation suite
- `workers/pipeline/test_procedure_alignment.py` - Unit tests for procedure logic

### Documentation Updated
- `Gemini.md` - Added Law 5: Specialty Procedure Alignment Audit
- `docs/CLAUDE.md` - Should be updated to reflect new segment labels
- `docs/FIXES_SUMMARY.md` - This document

### Backward Compatibility
- Frontend can handle missing procedure columns (graceful fallback)
- Old segment labels will be replaced on next pipeline run
- No breaking changes to existing API/JSON structure

---

## 🚨 KNOWN LIMITATIONS

1. **Pipeline must be re-run** - Fixes won't appear until scoring is re-executed
2. **Procedure data coverage** - Only 70k/1.4M clinics have procedure data (5%)
3. **Taxonomy accuracy** - Relies on NPI Registry taxonomy being up-to-date
4. **20% threshold** - Conservative; may need tuning based on real-world feedback

---

## ✅ FIX #4: FQHC PAYER MIX DISCOUNT (Dec 3, 2025)

### Problem
After migrating from "Segment A-F" to descriptive labels (FQHC, Hospital, etc.), the FQHC payer mix discount logic broke. The code was checking for `'Segment B'` instead of `'FQHC'`, causing:
- **0 FQHCs** getting the 0.20x multiplier
- All FQHCs showing **5x inflated** revenue lift projections
- Sales team overselling opportunity to FQHCs

### Why This Matters
FQHCs receive **80% of revenue from PPS** (Prospective Payment System - flat rate per visit). Only ~20% is commercial/FFS billing where coding optimization applies. Without the discount, we project $500k lift when reality is $100k.

### Solution
**Fixed segment label check in `scripts/update_frontend_data.py`:**

**OLD (Broken after v11.0):**
```python
if segment_label == 'Segment B' and coding_lift > 0:  # ❌ Never matches
    coding_lift = coding_lift * 0.20
```

**NEW (Fixed):**
```python
if segment_label == 'FQHC' and coding_lift > 0:  # ✅ Correct
    coding_lift = coding_lift * 0.20
```

### Impact
- FQHCs now show realistic revenue projections
- `payer_mix_applied` flag now accurately tracks discounted orgs
- Frontend will display "(FQHC Discounted)" label on lift calculations

### Files Changed
- `scripts/update_frontend_data.py` (line 236)

---

## ✅ FIX #5: PROCEDURE ALIGNMENT DATA QUALITY TRACKING (Dec 3, 2025)

### Problem
The procedure alignment scoring logic worked correctly but **silently skipped** clinics missing procedure data. No visibility into:
- How many procedure-heavy specialties (Podiatry, Ortho, Derm) exist in the database
- What % have procedure data populated
- Which specialties have poor data coverage

From validation: Only **4.4%** of clinics have procedure data. This suggests data pipeline issues.

### Solution
**Added comprehensive data quality tracking:**

1. **Global statistics counter** in `score_icp_production.py`:
   ```python
   PROCEDURE_DATA_QUALITY_STATS = {
       'procedure_heavy_specialties': 0,  # Total specialties that should have data
       'has_data': 0,                     # Clinics with valid procedure_ratio
       'missing_data': 0,                 # Clinics missing procedure_ratio
       'low_volume': 0,                   # Clinics with <50 claims
       'by_specialty': {},                # Breakdown by specialty type
       'missing_by_specialty': {}         # Missing data by specialty
   }
   ```

2. **Inline tracking** in `score_procedure_alignment()`:
   - Increments counters when procedure-heavy specialty detected
   - Tracks when data is missing (NaN procedure_ratio)
   - Records which specialty has the gap

3. **End-of-pipeline report**:
   ```
   📊 PROCEDURE ALIGNMENT DATA QUALITY REPORT
   ================================================================
   Procedure-Heavy Specialties Found: 12,450
     ✅ With procedure data: 550 (4.4%)
     ❌ Missing procedure data: 11,900 (95.6%)
     ⚠️  Low volume (<50 claims): 200 (1.6%)

   📋 Breakdown by Specialty:
     ❌ Podiatry          :  3,200 total |  3,100 missing ( 3.1% coverage)
     ❌ Orthopedics       :  4,500 total |  4,350 missing ( 3.3% coverage)
     ❌ Dermatology       :  2,800 total |  2,700 missing ( 3.6% coverage)
   ```

### What This Enables
- **Visibility:** Now see exact data coverage for each specialty
- **Root Cause Analysis:** Can identify if issue is in `mine_cpt_codes.py` extraction logic
- **Impact Assessment:** Know how many clinics have undetected procedure alignment pain
- **Action Items:** Data quality report flags when coverage is <50%

### Files Changed
- `workers/pipeline/score_icp_production.py` (lines 47-80, 96-131, 846-877)

---

## ✅ FINAL CHECKLIST

Before presenting to stakeholders:

- [ ] Re-run CPT mining (if not already done)
- [ ] Re-run scoring pipeline
- [ ] Update frontend data
- [ ] Run validation script
- [ ] Spot-check 10 clinics in frontend:
  - [ ] 3 major health systems (should NOT have therapy pain)
  - [ ] 3 true BH clinics (SHOULD have therapy pain)
  - [ ] 2 procedure-heavy specialties (should show procedure alignment if deficit)
  - [ ] 2 FQHCs (should show "FQHC" segment label)
- [ ] Verify therapy pain count is <15% of total leads

---

**Ready to ship once pipeline is re-run and validated.** 🚀
