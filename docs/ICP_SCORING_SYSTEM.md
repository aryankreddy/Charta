# ICP Scoring System Documentation

## 📋 Overview

The **ICP (Ideal Customer Profile) Scoring System** is a comprehensive 6-category evaluation framework that scores healthcare clinics on a 0-100 scale to identify the most promising prospects for Charta Health's pre-bill AI chart review solution.

**Created:** November 2025  
**Module:** `workers/score_icp.py`  
**API Endpoints:** `/icp/*`  
**Output:** `data/curated/clinics_icp.csv`, `data/curated/icp_scores.csv`

---

## 🎯 Scoring Categories (Total: 0-100)

| Category | Points | Description | Data Sources |
|----------|--------|-------------|--------------|
| **Fit Score** | 0-20 | Specialty type, clinic structure, service type | `segment_label`, `npi_count`, `site_count`, `services_count` |
| **Pain Score** | 0-20 | Denial rates, staffing shortages, revenue loss | `denial_pressure`, `allowed_amt`, `bene_count`, `coding_complexity` |
| **Compliance Risk** | 0-10 | Audit triggers, OIG flags, CMS participation | `oig_leie_flag`, `segment_label`, `aco_member`, `fqhc_flag` |
| **Propensity to Buy** | 0-10 | Payer mix, billing complexity, RCM staff presence | `roi_readiness`, `pecos_enrolled`, `aco_member`, `coding_complexity` |
| **Operational Scale** | 0-20 | Provider count, patient volume, billing size | `npi_count`, `site_count`, `bene_count`, `allowed_amt` |
| **Strategic Segment** | 0-20 | Match to Segment A/B/C definitions | `segment_label`, `sector`, `npi_count`, `fqhc_flag` |

---

## 🏆 Tier Assignment

Clinics are assigned to one of three tiers based on their **Total ICP Score**:

| Tier | Score Range | Label | Description |
|------|-------------|-------|-------------|
| **Tier 1** | ≥ 80 | **HOT** | High-priority targets with strong fit and urgent pain |
| **Tier 2** | 60-79 | **Qualified** | Solid prospects with moderate fit and pain |
| **Tier 3** | < 60 | **Monitor** | Lower priority, may require nurturing |

---

## 🎨 Segment Classification

Clinics are classified into one of three strategic segments:

| Segment | Description | Keywords | Scoring Logic |
|---------|-------------|----------|---------------|
| **A** | Behavioral Health / Home Health / Hospice | `behavioral health`, `mental health`, `substance abuse`, `home health`, `hospice`, `palliative` | Perfect match = 20 points |
| **B** | FQHC / Rural Health / HRSA Grantee | `fqhc`, `federally qualified`, `rural health`, `community health`, `hrsa` | Perfect match = 20 points |
| **C** | Multi-Specialty / Growth / PE-Backed | `multi-specialty`, `health system`, `hospital-affiliated`, `private equity`, `100+ providers` | Perfect match = 20 points |

---

## 📊 Category Details

### 1. Fit Score (0-20)

**Purpose:** Evaluate how well the clinic's specialty matches Charta's best-fit segments.

**Scoring Logic:**

| Specialty | Base Score | Modifiers |
|-----------|------------|-----------|
| Behavioral Health / Home Health | 18 | +2 for multi-site (≥5 locations) |
| FQHC / Community Health | 16 | +3 for high service count (≥10) |
| Primary Care / Family Medicine | 15 | +2 for complexity indicators |
| Multi-Specialty | 13 | +3 for service breadth |
| Other specialties | 10 | +2-5 for complexity |

**Data Sources:**
- `segment_label` (primary)
- `sector`
- `site_count`
- `services_count`

**Missing Data Handling:**
- If `segment_label` is NULL → score = 0, status = "MISSING"
- If `site_count` is NULL → no complexity bonus
- If `services_count` is NULL → no service breadth bonus

---

### 2. Pain Score (0-20)

**Purpose:** Quantify the urgency of the clinic's reimbursement and operational pain.

**Scoring Logic:**

| Pain Indicator | Points | Threshold |
|----------------|--------|-----------|
| High denial pressure | 8-10 | `denial_pressure` ≥ 7.0 |
| Very low revenue per patient | 7 | `allowed_amt / bene_count` < $300 |
| Low revenue per patient | 5 | < $600 |
| Moderate revenue | 3 | < $1000 |
| High coding complexity | 3 | `coding_complexity` ≥ 10 |
| Moderate complexity | 1.5 | `coding_complexity` ≥ 5 |

**Data Sources:**
- `denial_pressure` (0-10 scale from existing enrichment)
- `allowed_amt` (total Medicare reimbursement)
- `bene_count` (patient volume)
- `coding_complexity` (0-15 scale)

**Missing Data Handling:**
- If `denial_pressure` is NULL → no denial points, marked "MISSING"
- If `allowed_amt` or `bene_count` is NULL → no revenue strain points, marked "MISSING"
- If both are missing → Pain Score will be very low (possibly 0)

---

### 3. Compliance Risk Score (0-10)

**Purpose:** Assess regulatory scrutiny and compliance exposure.

**Scoring Logic:**

| Risk Factor | Points | Source |
|-------------|--------|--------|
| **OIG LEIE match** | 10 | `oig_leie_flag` = TRUE (highest priority) |
| Home Health / Post-Acute | 8 | `segment_label` (high CMS scrutiny) |
| Behavioral Health + high denials | 7 | `segment_label` + `denial_pressure` ≥ 7.0 |
| Behavioral Health | 4 | `segment_label` |
| FQHC designation | 5 | `fqhc_flag` = 1 |
| ACO participation | 4 | `aco_member` = 1 |
| Default baseline | 2 | If no specific indicators |

**Data Sources:**
- `oig_leie_flag` (from OIG LEIE enrichment)
- `segment_label`
- `denial_pressure`
- `fqhc_flag`
- `aco_member`

**Missing Data Handling:**
- If `oig_leie_flag` is NULL → fall back to segment-based risk
- If no risk indicators → baseline score = 2.0

---

### 4. Propensity to Buy Score (0-10)

**Purpose:** Evaluate buying intent based on technology adoption and RCM sophistication.

**Scoring Logic:**

| Buying Signal | Points | Threshold |
|---------------|--------|-----------|
| High ROI readiness | 4 | `roi_readiness` ≥ 7.0 |
| Moderate ROI readiness | 2 | `roi_readiness` ≥ 4.0 |
| Some ROI readiness | 1 | `roi_readiness` > 0 |
| PECOS enrollment | 2 | `pecos_enrolled` = 1 |
| ACO participation | 2 | `aco_member` = 1 |
| High coding complexity | 2 | `coding_complexity` ≥ 8.0 |

**Data Sources:**
- `roi_readiness` (0-10 scale, existing enrichment)
- `pecos_enrolled` (Medicare enrollment flag)
- `aco_member` (ACO participation flag)
- `coding_complexity`

**Missing Data Handling:**
- If all indicators are NULL/0 → score = 0, status = "MISSING"
- Partial data is acceptable (score based on available signals)

---

### 5. Operational Scale Score (0-20)

**Purpose:** Measure organization size and complexity to estimate revenue potential.

**Scoring Logic:**

#### Provider Count (0-8 points)

| Provider Range | Points | Reason |
|----------------|--------|--------|
| 100+ | 8.0 | Large provider network |
| 50-99 | 7.0 | Mid-size provider network |
| 20-49 | 5.5 | Growing provider network |
| 10-19 | 4.0 | Small-medium provider group |
| 5-9 | 2.5 | Small provider group |
| 1-4 | 1.0 | Very small practice |

#### Site Count (0-4 points)

| Site Range | Points | Reason |
|------------|--------|--------|
| 10+ | 4.0 | Multi-site organization |
| 5-9 | 3.0 | Multi-site organization |
| 3-4 | 2.0 | Multi-site |
| 1-2 | 1.0 | Single or dual-site |

#### Patient Volume (0-4 points)

| Patient Range | Points | Reason |
|---------------|--------|--------|
| 10,000+ | 4.0 | Very high patient volume |
| 5,000-9,999 | 3.5 | High patient volume |
| 1,000-4,999 | 2.5 | Moderate patient volume |
| 500-999 | 1.5 | Small patient volume |
| < 500 | 0.5 | Low patient volume |

#### Billing Size (0-4 points)

| Billing Range | Points | Reason |
|---------------|--------|--------|
| $10M+ | 4.0 | Enterprise billing volume |
| $5M-$10M | 3.5 | Large billing volume |
| $1M-$5M | 2.5 | Mid-size billing volume |
| $500K-$1M | 1.5 | Small billing volume |
| < $500K | 0.5 | Low billing volume |

**Data Sources:**
- `npi_count` (provider count)
- `site_count` (location count)
- `bene_count` (Medicare patient volume)
- `allowed_amt` (total Medicare reimbursement)

**Missing Data Handling:**
- If `npi_count` is NULL → no provider points, marked "MISSING"
- If `site_count` is NULL → no site points
- If `bene_count` is NULL → no volume points
- If `allowed_amt` is NULL → no billing size points
- Score is sum of available components (partial data acceptable)

---

### 6. Strategic Segment Score (0-20)

**Purpose:** Assign segment classification and score based on strategic fit.

**Scoring Logic:**

| Match Quality | Score | Criteria |
|---------------|-------|----------|
| **Perfect Segment A** | 20 | Keywords: `behavioral health`, `mental health`, `home health`, `hospice` in `segment_label` |
| **Perfect Segment B** | 20 | `fqhc_flag` = 1 OR keywords: `fqhc`, `rural health`, `hrsa` in `segment_label` or `sector` |
| **Perfect Segment C** | 20 | Keywords: `multi-specialty`, `health system` in `segment_label` OR `npi_count` ≥ 100 |
| Moderate match (C) | 12-15 | Primary Care OR `npi_count` 50-99 |
| Weak match (C) | 8-12 | `npi_count` 20-49 OR generic specialty |

**Segment Assignment:**
- Clinics are assigned to **one** segment (A, B, or C)
- Priority order: A > B > C (if multiple matches, choose highest priority)
- Default segment: C (Multi-Specialty/Growth)

**Data Sources:**
- `segment_label` (primary)
- `sector`
- `npi_count`
- `fqhc_flag`

**Missing Data Handling:**
- If all sources are NULL → default to Segment C with score = 8.0

---

## 📖 Bibliography System

Every score includes a **bibliography** that tracks which data sources were used and identifies missing data.

### Bibliography Entry Format

```python
{
    "score": "fit" | "pain" | "compliance_risk" | "propensity_to_buy" | "scale" | "strategic_segment",
    "sources": ["column_name1", "column_name2"],
    "value": "actual_value_used",
    "reason": "Human-readable explanation",
    "status": "MISSING" (optional, only if data unavailable),
    "note": "Additional context" (optional)
}
```

### Example Bibliography Entries

```python
# Data available
{
    "score": "fit",
    "sources": ["segment_label"],
    "value": "behavioral health",
    "reason": "Behavioral Health / Home Health (high fit)"
}

# Data missing
{
    "score": "pain",
    "sources": ["allowed_amt", "bene_count"],
    "status": "MISSING",
    "note": "No Medicare utilization data available"
}

# Partial data
{
    "score": "scale",
    "sources": ["npi_count"],
    "value": 55,
    "reason": "Mid-size provider network (50-99 providers)"
}
```

---

## 🚀 Usage

### Running the Scorer

```bash
# Run ICP scoring on all clinics
cd /Users/nageshkothacheruvu/FinalChartaTool
python3 workers/score_icp.py
```

**Output:**
- `data/curated/clinics_icp.csv` (full dataset with ICP scores)
- `data/curated/icp_scores.csv` (scores-only summary)

### API Endpoints

#### 1. Get ICP Clinics (with filters)

```bash
GET /icp/clinics?tier=1&segment=A&state=TX&min_score=60&limit=100&offset=0
```

**Query Parameters:**
- `tier` (optional): Filter by tier (1, 2, or 3)
- `segment` (optional): Filter by segment (A, B, or C)
- `state` (optional): Filter by state code
- `min_score` (optional): Minimum ICP score (0-100)
- `limit` (optional): Max results (default: 100, max: 10000)
- `offset` (optional): Pagination offset (default: 0)

**Response:**

```json
{
  "total": 538,
  "limit": 100,
  "offset": 0,
  "clinics": [
    {
      "clinic_id": "caprock-home-health-services-inc--TX",
      "account_name": "CAPROCK HOME HEALTH SERVICES, INC.",
      "state_code": "TX",
      "segment_label": "Home Health / Post-Acute",
      "icp_total_score": 68.0,
      "icp_tier": 2,
      "icp_tier_label": "Tier 2 - Qualified",
      "icp_segment": "A",
      "icp_fit_score": 20.0,
      "icp_pain_score": 5.0,
      "icp_compliance_score": 8.0,
      "icp_propensity_score": 4.0,
      "icp_scale_score": 11.0,
      "icp_segment_score": 20.0,
      "npi_count": 55,
      "site_count": 10,
      "bene_count": null,
      "allowed_amt": null
    }
  ]
}
```

#### 2. Get Clinic Detail (with bibliography)

```bash
GET /icp/clinic/caprock-home-health-services-inc--TX
```

**Response:**

```json
{
  "clinic_id": "caprock-home-health-services-inc--TX",
  "account_name": "CAPROCK HOME HEALTH SERVICES, INC.",
  "state_code": "TX",
  "segment_label": "Home Health / Post-Acute",
  "icp_score": {
    "total": 68.0,
    "breakdown": {
      "fit": 20.0,
      "pain": 5.0,
      "compliance_risk": 8.0,
      "propensity_to_buy": 4.0,
      "operational_scale": 11.0,
      "strategic_segment": 20.0
    }
  },
  "tier": {
    "number": 2,
    "label": "Tier 2 - Qualified"
  },
  "segment": {
    "letter": "A",
    "description": "Behavioral Health / Home Health / Hospice"
  },
  "operational_data": {
    "npi_count": 55,
    "site_count": 10,
    "bene_count": 0,
    "allowed_amt": 0.0,
    "fqhc_flag": false,
    "aco_member": false,
    "pecos_enrolled": false
  },
  "bibliography": [
    {
      "score": "fit",
      "sources": ["segment_label"],
      "value": "home health / post-acute",
      "reason": "Behavioral Health / Home Health (high fit)"
    },
    {
      "score": "fit",
      "sources": ["site_count"],
      "value": 10.0,
      "reason": "Multi-site complexity bonus"
    },
    {
      "score": "pain",
      "sources": ["denial_pressure"],
      "value": 5.0,
      "reason": "Denial pressure indicates reimbursement pain"
    },
    {
      "score": "pain",
      "sources": ["allowed_amt", "bene_count"],
      "status": "MISSING",
      "note": "No Medicare utilization data available"
    }
  ]
}
```

#### 3. Get Aggregate Statistics

```bash
GET /icp/stats
```

**Response:**

```json
{
  "total_clinics": 1448807,
  "score_distribution": {
    "mean": 46.4,
    "median": 45.0,
    "min": 27.0,
    "max": 68.0,
    "std": 8.2
  },
  "tier_distribution": {
    "tier_1_hot": 0,
    "tier_2_qualified": 538,
    "tier_3_monitor": 1448269
  },
  "segment_distribution": {
    "segment_a_behavioral_home_health": 185546,
    "segment_b_fqhc_compliance": 0,
    "segment_c_multi_specialty_growth": 1263261
  },
  "category_averages": {
    "fit": 13.2,
    "pain": 4.8,
    "compliance_risk": 3.1,
    "propensity_to_buy": 2.4,
    "operational_scale": 9.7,
    "strategic_segment": 13.2
  },
  "top_10_clinics": [...]
}
```

---

## 🔍 Current Data Availability & Gaps

### ✅ Available Data

| Field | Availability | Source | Notes |
|-------|--------------|--------|-------|
| `segment_label` | ✓ 100% | Enrichment pipeline | Well-populated |
| `npi_count` | ✓ 100% | NPI registry aggregation | Accurate |
| `site_count` | ✓ ~95% | Multi-source enrichment | Generally good |
| `denial_pressure` | ✓ ~80% | Existing ICF scoring | Derived metric |
| `coding_complexity` | ✓ ~75% | Existing ICF scoring | Derived metric |
| `roi_readiness` | ✓ ~70% | Existing ICF scoring | Derived metric |

### ⚠️ Missing/Incomplete Data

| Field | Availability | Impact | Workaround |
|-------|--------------|--------|------------|
| `fqhc_flag` | ❌ 0% (all = 0) | No Segment B clinics detected | Need FQHC enrichment |
| `oig_leie_flag` | ❌ Not in dataset | Compliance scores lower | Need OIG LEIE join |
| `bene_count` | ⚠️ ~40% | Pain scores lower | Use proxies when available |
| `allowed_amt` | ⚠️ ~40% | Pain/Scale scores lower | Use proxies when available |
| `services_count` | ⚠️ ~60% | Fit scores slightly lower | Not critical |

### 📋 Data Quality Improvement Roadmap

1. **High Priority:**
   - ✅ **FQHC Flag Enrichment** - Add join to HRSA FQHC list
   - ✅ **OIG LEIE Integration** - Already implemented, needs to be joined to main dataset
   - ⚠️ **Medicare Utilization Data** - Expand `bene_count` and `allowed_amt` coverage

2. **Medium Priority:**
   - Services count enrichment (from NPI taxonomy codes)
   - PE-backed flag (from ownership data)
   - Billing staff count (from careers page scraping)

3. **Low Priority:**
   - EMR vendor (already have `emr_friction`)
   - Payer mix details (can derive from existing flags)

---

## 📈 Validation & Testing

### Test Script

```bash
# Run test script
python3 scripts/test_icp_scoring.py
```

### Expected Results

With current data (Nov 2025):
- **Total clinics**: ~1.45M
- **Tier 1 (HOT)**: 0-100 clinics (limited by data completeness)
- **Tier 2 (Qualified)**: 500-1000 clinics
- **Tier 3 (Monitor)**: Majority (>99%)
- **Segment A**: 12-15% (Behavioral/Home Health)
- **Segment B**: 0-5% (FQHC - currently 0%)
- **Segment C**: 80-85% (Multi-Specialty/Other)

### Score Range Expectations

| Category | Expected Min | Expected Max | Expected Mean |
|----------|--------------|--------------|---------------|
| Fit | 8 | 20 | 13 |
| Pain | 0 | 18 | 5 |
| Compliance | 2 | 10 | 3-4 |
| Propensity | 0 | 10 | 2-3 |
| Scale | 1 | 20 | 9-10 |
| Segment | 8 | 20 | 13 |
| **Total** | **27** | **80** | **46** |

---

## 🔄 Comparison with Existing ICF Scoring

| Aspect | ICP Scoring (New) | ICF Scoring (Existing) |
|--------|-------------------|------------------------|
| **Total Score Range** | 0-100 | 0-10 |
| **Categories** | 6 explicit categories | 2 axes (Structural Fit, Propensity) |
| **Tier Logic** | ICP ≥ 80 → Tier 1 | Fit ≥ 6.0 AND Prop ≥ 4.5 → Tier 1 |
| **Segments** | A, B, C (explicit assignment) | Inferred from `segment_label` |
| **Bibliography** | ✓ Explicit tracking | ❌ Not tracked |
| **Missing Data Handling** | ✓ Explicit "UNKNOWN" | Implicit (defaults to 0) |
| **API Endpoints** | `/icp/*` | `/clinics/*` (includes ICF in response) |
| **Use Case** | Strategic prospect prioritization | Operational fit + urgency |

**Note:** Both systems coexist. ICP provides strategic prioritization, while ICF provides operational fit assessment.

---

## 📞 Support & Feedback

For questions or issues:
1. Check this documentation
2. Review `workers/score_icp.py` source code
3. Test with `scripts/test_icp_scoring.py`
4. Review API responses with `/icp/stats` endpoint

---

**Last Updated:** November 16, 2025  
**Version:** 1.0  
**Maintainer:** Charta Health Data Team


