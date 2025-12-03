# ICP Scoring System - Quick Start Guide

## 🚀 What is ICP Scoring?

The **ICP (Ideal Customer Profile) Scoring System** evaluates 1.4M+ healthcare clinics on a **0-100 scale** using 6 categories to identify the most promising prospects for Charta Health.

---

## 📊 Score Breakdown (Total: 0-100)

| Category | Points | What It Measures |
|----------|--------|------------------|
| **Fit** | 0-20 | Specialty match (Behavioral Health, Home Health = best fit) |
| **Pain** | 0-20 | Revenue pressure, denial rates, cash flow strain |
| **Compliance** | 0-10 | Audit risk, OIG flags, CMS scrutiny |
| **Propensity** | 0-10 | Technology adoption, RCM sophistication, buying intent |
| **Scale** | 0-20 | Provider count, patient volume, billing size |
| **Segment** | 0-20 | Strategic segment match (A/B/C classification) |

---

## 🏆 Tier & Segment Classification

### Tiers (Based on Total Score) - **UPDATED Nov 2025**

| Tier | Score | Label | Current Count |
|------|-------|-------|---------------|
| **1** | ≥**70** | 🔥 **HOT** | 0 (max score: 68.0, gap: 2.0 pts) |
| **2** | **50-69** | ✅ **Qualified** | **198,664 (13.7%)** |
| **3** | <**50** | 👀 **Monitor** | 1.25M (86.3%) |

**Tier Threshold Changes (Nov 2025):**
- Tier 1: 80 → **70** (reduced to address score compression)
- Tier 2: 60-79 → **50-69** (expanded by 10 points)
- **Impact:** Tier 2 grew from 538 to 198,664 clinics (+37,000%)

### Segments (Strategic Classification) - **UPDATED Nov 2025**

| Segment | Description | Current Count |
|---------|-------------|---------------|
| **A** | Behavioral Health / Home Health / Hospice | 185,546 (12.8%) |
| **B** | FQHC / Rural Health / HRSA Grantee | **1,623 (0.1%)** ✅ |
| **C** | Multi-Specialty / Growth / PE-Backed | 1,261,638 (87.1%) |

**Data Enrichment (Nov 2025):**
- FQHC flags: 0 → **1,632** (NPI-level matching)
- ACO flags: 0 → **146** (organization-level matching)
- Segment B now populated with 1,623 clinics

---

## 🎯 Quick Start

### 1. Run the Scorer

```bash
cd /Users/nageshkothacheruvu/FinalChartaTool
python3 workers/score_icp.py
```

**Output:**
- `data/curated/clinics_icp.csv` (full dataset with ICP scores)
- `data/curated/icp_scores.csv` (scores summary)

**Time:** ~30 seconds for 1.4M clinics

---

### 2. Test the Scorer

```bash
python3 scripts/test_icp_scoring.py
```

**Tests:**
- ✅ Data availability
- ✅ Score range validation
- ✅ Tier/segment distribution
- ✅ Bibliography completeness
- ✅ Top scorers inspection
- ✅ Data gap analysis

---

### 3. Use the API

Start the API server:

```bash
cd /Users/nageshkothacheruvu/FinalChartaTool
uvicorn api.app:app --reload --port 8000
```

#### API Endpoints

**Get ICP Clinics (with filters):**

```bash
curl "http://localhost:8000/icp/clinics?tier=2&segment=A&limit=10"
```

**Get Clinic Detail (with bibliography):**

```bash
curl "http://localhost:8000/icp/clinic/caprock-home-health-services-inc--TX"
```

**Get Statistics:**

```bash
curl "http://localhost:8000/icp/stats"
```

---

## 📈 Current Results (Nov 2025) - **UPDATED WITH ENRICHMENT**

### Score Distribution

| Metric | Value |
|--------|-------|
| **Mean** | 46.4/100 |
| **Median** | 46.0/100 |
| **Range** | 27.0 - 68.0 |
| **Std Dev** | 4.11 |

### Category Averages

| Category | Average Score | Max Possible |
|----------|---------------|--------------|
| Fit | 13.7 | 20 |
| Pain | 5.0 | 20 |
| Compliance | 2.4 | 10 |
| Propensity | 3.9 | 10 |
| Scale | 2.1 | 20 |
| Segment | 19.3 | 20 |

### Top 10 Clinics (Overall)

All **Tier 2** (score: 50-68), all **Segment A** (Home Health):

1. CAPROCK HOME HEALTH SERVICES, INC. (TX) - 68.0
2. BAYADA HOME HEALTH CARE, INC. (NJ) - 68.0
3. BAYADA HOME HEALTH CARE, INC. (NC) - 68.0
4. BAYADA HOME HEALTH CARE, INC. (PA) - 68.0
5. SUTTER VISITING NURSE ASSOCIATION AND HOSPICE (CA) - 66.5
6. VISITING NURSE SERVICES OF MICHIGAN (MI) - 66.5
7. VNA HEALTH CARE (IL) - 66.5
8. BAYADA HOME HEALTH CARE, INC. (MA) - 66.5
9. CONTINUUM II HOME HEALTH & HOSPICE, INC. (NC) - 66.5
10. HOUSECALL HOME HEALTH, LLC (FL) - 66.5

### Top 5 Segment B (FQHC) Clinics ✨ NEW

1. NORTH BROWARD HOSPITAL DISTRICT (FL) - 66.0
2. THE BOARD OF TRUSTEES OF THE UNIVERSITY OF ILLINOIS (IL) - 63.5
3. MCR HEALTH, INC. (FL) - 62.5
4. MONTEFIORE MEDICAL CENTER (NY) - 62.5
5. DALLAS COUNTY HOSPITAL DISTRICT (TX) - 61.0

---

## ⚠️ Known Data Gaps - **UPDATED Nov 2025**

### ✅ Fixed (Nov 2025)

| Fixed Data | Before | After | Method |
|------------|--------|-------|--------|
| **FQHC Flag** | 0 clinics | **1,632 clinics** ✅ | NPI-level matching with HRSA data |
| **ACO Participation** | 0 clinics | **146 clinics** ✅ | Organization-level matching |
| **Segment B** | 0 clinics | **1,623 clinics** ✅ | Enabled by FQHC enrichment |

### ❌ Still Missing

| Gap | Impact | Status |
|-----|--------|--------|
| **OIG LEIE Flag** | Compliance scores lower than they could be | ❌ Not joined to main dataset |
| **PECOS Enrollment** | Propensity scores lower | ❌ All values = 0 |
| **Medicare Utilization** | Complete coverage (100%) | ✅ No gap |

### Why No Tier 1 Clinics?

**Max ICP Score: 68/100** (need ≥**70** for Tier 1 after threshold adjustment)

**Gap Analysis for Top Clinics:**
- Fit: 20/20 ✅ (maxed out)
- Pain: 5/20 ❌ (limited by missing denial/revenue data)
- Compliance: 8/10 ✅ (near max for Home Health)
- Propensity: 4/10 ⚠️ (ACO flag now enriched, but PECOS still 0)
- Scale: 11/20 ⚠️ (limited by patient volume/billing data)
- Segment: 20/20 ✅ (maxed out)

**Gap to Tier 1:** Just **2.0 points!**

**To reach Tier 1 (≥70):**
1. ~~Enrich FQHC flag~~ → ✅ **DONE** (+1,632 clinics)
2. ~~Add ACO enrichment~~ → ✅ **DONE** (+146 clinics)
3. Add OIG LEIE flag → +1-2 points (Compliance)
4. Improve Pain/Scale data → +3-5 points
5. Add PECOS enrollment → +1-2 points (Propensity)

**Potential:** With remaining enrichment, ~50-100 clinics could reach Tier 1 (≥70)

---

## 📖 Key Features

### ✅ Bibliography Tracking

Every score includes a **bibliography** that documents:
- Which data columns were used
- What values were found
- Why the score was assigned
- Which data was missing

**Example:**

```json
{
  "score": "fit",
  "sources": ["segment_label", "site_count"],
  "value": "home health / post-acute, 10 sites",
  "reason": "Behavioral Health / Home Health (high fit) + Multi-site complexity bonus"
}
```

### ✅ Missing Data Handling

When data is unavailable:
- Score component = 0 or baseline
- Bibliography entry marked "MISSING"
- Total ICP score calculated from available data

**Example:**

```json
{
  "score": "pain",
  "sources": ["allowed_amt", "bene_count"],
  "status": "MISSING",
  "note": "No Medicare utilization data available"
}
```

### ✅ Explainability

Every clinic's score is **fully auditable**:
1. View breakdown by category (6 scores)
2. See which data sources were used
3. Understand scoring logic via bibliography
4. Identify data gaps for improvement

---

## 🔧 Troubleshooting

### Score Too Low?

Check bibliography for "MISSING" entries:

```bash
curl "http://localhost:8000/icp/clinic/{clinic_id}" | jq '.bibliography[] | select(.status == "MISSING")'
```

### No Segment B Clinics?

FQHC flag is all zeros. Run FQHC enrichment:

```bash
python3 workers/enrich_fqhc.py  # (needs to be created)
```

### No Tier 1 Clinics?

This is expected with current data completeness. See "Why No Tier 1 Clinics?" section above.

---

## 📚 Documentation

- **Full Specification:** `docs/ICP_SCORING_SYSTEM.md`
- **Source Code:** `workers/score_icp.py`
- **Test Suite:** `scripts/test_icp_scoring.py`
- **API Endpoints:** `/icp/*` (see `api/app.py`)

---

## 🆚 ICP vs ICF Scoring

| Aspect | ICP Scoring (New) | ICF Scoring (Existing) |
|--------|-------------------|------------------------|
| **Total Score** | 0-100 | 0-10 |
| **Categories** | 6 explicit (Fit, Pain, Compliance, Propensity, Scale, Segment) | 2 axes (Structural Fit, Propensity) |
| **Tier Logic** | ICP ≥ 80 → Tier 1 | Fit ≥ 6.0 AND Prop ≥ 4.5 → Tier 1 |
| **Segments** | A, B, C (explicit assignment) | Derived from `segment_label` |
| **Bibliography** | ✅ Full tracking | ❌ Not tracked |
| **Missing Data** | ✅ Explicit "UNKNOWN" | Implicit (defaults to 0) |
| **Use Case** | Strategic prospect prioritization | Operational fit assessment |

**Both systems coexist** and serve different purposes.

---

## 🎉 Success Metrics

### Validation Results

```
✅ All 7 tests passed
✅ Score ranges valid (0-100 scale)
✅ Tier logic correct (Tier 2: 60-79, Tier 3: <60)
✅ Segment distribution reasonable (12.8% A, 87.2% C)
✅ Bibliography working (87% data availability, 13% missing)
✅ Top 10 clinics inspected (all Home Health, scores 60-68)
✅ Data gaps identified and documented
```

### Performance

- **Scoring Time:** ~30 seconds for 1.4M clinics
- **Output Size:** ~1.9 GB (full dataset with ICP scores)
- **API Response Time:** <100ms per request
- **Test Suite:** 7/7 passed in ~5 seconds

---

**Last Updated:** November 16, 2025  
**Version:** 1.0  
**Status:** ✅ Production Ready (with documented data gaps)

