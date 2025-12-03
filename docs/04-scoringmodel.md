# 04_ScoringModel.md — Ideal Customer Fit (ICF) Logic & Examples

> Purpose: define the math, rules, and interpretation of each scoring axis in the **ICF (Ideal Customer Fit)** framework.
> Ensures that every score is **explainable**, **data-driven**, and **aligned with Charta’s GTM logic** — i.e., *who benefits most from pre-bill AI chart review.*

---

## 0) Overview

The **ICF Score (0–100)** ranks clinics by their likelihood to see rapid, defensible ROI from Charta Health.
It combines six axes weighted by strategic impact:

| Axis                        | Weight | Description                                            | Reflects           |
| --------------------------- | ------ | ------------------------------------------------------ | ------------------ |
| **Segment Fit**             | 25     | Does this clinic operate in Charta’s proven verticals? | Product-market fit |
| **Scale & Velocity**        | 20     | How big and fast-growing is the org?                   | Revenue potential  |
| **EMR Friction (inverted)** | 15     | How easy is integration?                               | Sales cycle length |
| **Coding Complexity**       | 15     | How complex are their billing patterns?                | Automation ROI     |
| **Denial Pressure**         | 15     | How acute are their reimbursement issues?              | Pain urgency       |
| **ROI Readiness**           | 10     | Do they show appetite for automation / quality focus?  | Buying intent      |

[
\text{ICF} = \sum_{i=1}^{6} w_i \times \frac{x_i}{x_{i,\text{max}}}
]

All axes scored 0–their max weight, producing a 0–100 composite.

---

## 1) Axis 1 — Segment Fit (0–25)

**Definition:** measures how directly the clinic’s specialty matches Charta’s best-fit segments.

| Segment           | Base | Modifiers                              |
| ----------------- | ---- | -------------------------------------- |
| Primary Care      | 25   | +2 if multi-location (>5)              |
| Behavioral Health | 23   | +2 if Medicaid participant             |
| Home Health       | 22   | +3 if Medicare participant             |
| Urgent Care       | 20   | +2 if review_count > 200               |
| Other Specialty   | 10   | +0–10 depending on complexity keywords |

**Signals used:**

* `segments[]` (from taxonomy + site)
* `medicare_participating`, `medicaid_flag`
* `review_count`, `num_locations`

---

## 2) Axis 2 — Scale & Velocity (0–20)

**Goal:** larger, faster-growing orgs yield higher recurring revenue and immediate operational pain.

| Feature                  | Range | Score Logic            |
| ------------------------ | ----- | ---------------------- |
| `num_locations`          | 1–50  | 0–8 points (log scale) |
| `num_clinicians_proxy`   | 1–500 | 0–8 points (log scale) |
| `has_coding_hiring`      | bool  | +2 if True             |
| `has_denial_mgmt_hiring` | bool  | +2 if True             |

Formula:
[
S_{scale} = 8 \cdot \log_{10}(1 + L) + 8 \cdot \log_{10}(1 + C/10) + 2H_c + 2H_d
]
Clamped to 20 max.

**Interpretation:** High-growth orgs (multi-site, active hiring) = “pain from scale” = better fit.

---

## 3) Axis 3 — EMR Friction (0–15, inverted)

**Definition:** evaluates integration effort. Charta wins faster when clinics use common, cloud-based EMRs.

| EMR Vendor                                                                      | Score | Confidence |
| ------------------------------------------------------------------------------- | ----- | ---------- |
| Epic, athenahealth, eClinicalWorks, NextGen, AdvancedMD, Kareo, ModMed, Elation | 15    | high       |
| Unknown                                                                         | 8     | med        |
| Rare/Exotic or On-prem (Cerner, Greenway, Meditech, custom)                     | 4     | high       |

If `emr_confidence = low`, reduce score by 25%.
If multiple EMRs detected, take mean of top two.

**Interpretation:** Lower friction → faster onboarding → higher immediate GTM value.

---

## 4) Axis 4 — Coding Complexity (0–15)

**Definition:** how many revenue opportunities are likely hidden in their documentation.

| Proxy                          | Detection            | Points |
| ------------------------------ | -------------------- | ------ |
| `services_breadth ≥ 10`        | multi-service clinic | +6     |
| `has_coding_hiring`            | active coder hiring  | +4     |
| `mentions_prebill_audit`       | in careers text      | +3     |
| `segments` ∈ {home_health, BH} | inherently complex   | +2     |

Capped at 15.

**Interpretation:** Complexity means more missed codes → higher incremental RVU gain potential.

---

## 5) Axis 5 — Denial Pressure (0–15)

**Definition:** how strongly the clinic feels the pain of payer denials or compliance scrutiny.

| Signal                   | Weight   | Example                               |
| ------------------------ | -------- | ------------------------------------- |
| `state_denial_prior`     | up to 10 | TX=high(10), CA=med(6), others=low(3) |
| `has_denial_mgmt_hiring` | +3       | “Denial Analyst,” “RCM Lead”          |
| `mentions_prebill_audit` | +2       | proactive compliance behavior         |

Formula:
[
S_{denial} = base_{state} + 3H_d + 2A_p
]
Clamped 0–15.

**Interpretation:** Denial pain = urgency → easier sale.

---

## 6) Axis 6 — ROI Readiness (0–10)

**Definition:** leadership focus on efficiency, compliance, or value-based care—signals purchase intent.

| Proxy                                                             | Points | Source          |
| ----------------------------------------------------------------- | ------ | --------------- |
| `aco_flag`                                                        | +4     | CMS ACO list    |
| `mentions_prebill_audit`                                          | +2     | careers text    |
| `has_quality_program_terms` (`value-based`, `HEDIS`, `CMS audit`) | +2     | site/careers    |
| `press_hits` or `conference_presence`                             | +2     | exhibitors/news |

Cap at 10.

**Interpretation:** proactive orgs that already invest in compliance automation adopt faster.

---

## 7) Composite & Driver Logic

```python
weights = {
  "segment_fit": 25,
  "scale_velocity": 20,
  "emr_friction": 15,
  "coding_complexity": 15,
  "denial_pressure": 15,
  "roi_readiness": 10
}

icf = sum(axis_score[a] for a in weights)
```

**Top Drivers Extraction**

```python
drivers = sorted(axis_score.items(), key=lambda x: x[1], reverse=True)[:3]
```

Each driver references evidence (URLs/snippets) for transparency.

---

## 8) Example Calculations

### Example 1: Behavioral Health Network in Texas

| Axis              | Subscores                              | Final  |
| ----------------- | -------------------------------------- | ------ |
| Segment Fit       | BH + Medicaid + 4 locations → 24       | 24     |
| Scale             | 20 clinicians, coder hiring → 14       | 14     |
| EMR               | athenahealth (common) → 15             | 15     |
| Coding Complexity | multi-service + coders + pre-bill → 15 | 15     |
| Denial Pressure   | TX high + denial hires → 15            | 15     |
| ROI Readiness     | ACO + quality keywords → 8             | 8      |
| **ICF**           | —                                      | **91** |

**Top Drivers:** Denial Pressure, Segment Fit, EMR Friction
→ “High-growth BH provider in TX using athenahealth; likely experiencing payer scrutiny.”

---

### Example 2: 2-Site Urgent Care in Iowa

| Axis              | Final                     |
| ----------------- | ------------------------- |
| Segment Fit       | 20                        |
| Scale             | 8                         |
| EMR               | Unknown → 8               |
| Coding Complexity | 6                         |
| Denial Pressure   | State low + no hiring → 3 |
| ROI Readiness     | 2                         |
| **ICF**           | **47**                    |

**Interpretation:** Not urgent to target; low denial pain, small scale.

---

### Example 3: Home Health Provider (Medicare) in Florida

| Axis              | Final                   |
| ----------------- | ----------------------- |
| Segment Fit       | 25                      |
| Scale             | 16                      |
| EMR               | NextGen → 15            |
| Coding Complexity | 12                      |
| Denial Pressure   | high (FL) + hiring → 15 |
| ROI Readiness     | 6                       |
| **ICF**           | **89**                  |

High-fit; Medicare focus + NextGen EMR = short sales cycle.

---

## 9) Output Fields (for `/score_icf.py`)

| Field            | Type       | Description                   |
| ---------------- | ---------- | ----------------------------- |
| `icf_score`      | int        | 0–100                         |
| `axis_breakdown` | dict       | axis:score                    |
| `top_drivers`    | list[dict] | `{name, reason, evidence_id}` |
| `model_version`  | str        | e.g., `"icf_v1.0"`            |
| `computed_at`    | datetime   | UTC                           |

---

## 10) Evidence Generation Examples

| Axis              | Evidence Source | Example Snippet                                               |
| ----------------- | --------------- | ------------------------------------------------------------- |
| EMR Friction      | Careers page    | “… experience with Athenahealth EHR required”                 |
| Denial Pressure   | Job listing     | “Denials Management Specialist – Revenue Cycle”               |
| ROI Readiness     | Conference list | “Exhibitor at Becker’s Healthcare AI Summit 2025”             |
| Coding Complexity | Services page   | “We provide chronic care, telepsychiatry, and med management” |

Each snippet stored in `evidence` table with source URL.

---

## 11) Scoring Confidence

Each axis returns `(score, confidence)` where confidence is derived from:

* Signal count and source diversity (NPI + careers + site → high).
* Single weak hint → low.
  Low confidence automatically downweights 20%.

---

## 12) Acceptance Criteria

* Deterministic rule-based scoring works from existing features.
* Outputs ICF + top 3 drivers with evidence.
* Weighted constants editable in `/config/scoring.yaml`.
* Produces explainable results on ≥3k clinics with <1s latency/query.
* Feeds directly into the dashboard filtering & export modules.

---

## 13) Why This Impresses Charta

* **Emulates their own AI audit logic** — rule-driven, evidence-backed, tunable.
* **Translates product language into GTM math** (RVU uplift → ICF).
* **Demonstrates structured reasoning** rather than superficial scraping.
* **Scalable**: can later integrate ML regression or feedback learning once Charta’s GTM team feeds labeled “won/lost” accounts.

---
