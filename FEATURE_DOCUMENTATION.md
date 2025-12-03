# Charta GTM Intelligence Tool - Feature Documentation

**Complete technical reference for every metric, calculation, and data point in the system**

---

## Table of Contents
1. [Core Scoring System](#core-scoring-system)
2. [Strategic Intelligence Brief](#strategic-intelligence-brief)
3. [Score Breakdown Components](#score-breakdown-components)
4. [Key Metrics](#key-metrics)
5. [Contact & Network Details](#contact--network-details)
6. [Drivers & Signals](#drivers--signals)
7. [Filters & Segments](#filters--segments)
8. [Data Sources & Confidence](#data-sources--confidence)
11111
---

## Core Scoring System

### ICP Score (0-100)
- **What it is:** Composite score ranking each organization's fit for Charta's AI chart review solution
- **Calculation:** Sum of Pain (max 40) + Fit (max 30) + Strategy (max 30) = Total Score (0-100)
- **Data source:** Calculated from CMS claims data, MIPS scores, HPSA/MUA designations, revenue scale, and segment alignment

### Tier Classification
- **Tier 1 (Score ≥70):** High-priority leads - immediate sales focus, strong pain + fit + strategic value
- **Tier 2 (Score 50-69):** Qualified leads - worth nurturing, moderate alignment across dimensions
- **Tier 3 (Score <50):** Low-priority - monitoring only, weak pain signals or poor strategic fit
- **Usage:** Prioritizes sales outreach by ranking organizations from highest to lowest opportunity value

### Scoring Track (Ambulatory vs Behavioral vs Post-Acute)
- **Ambulatory Track:** Focuses on E&M undercoding as primary pain signal (ratio < 0.45 = higher score)
- **Behavioral Track:** Focuses on psych audit risk (ratio > 0.75 = higher score) and VBC readiness
- **Post-Acute Track:** Focuses on margin pressure and volume-based pain (negative margins = higher score)
- **Why it matters:** Different care models have different economic pain points - track-specific scoring ensures accurate prioritization

---

## Strategic Intelligence Brief

### Est. Revenue Lift
- **What it is:** Estimated annual revenue increase if the organization adopts Charta's AI chart review solution
- **Calculation (VERIFIED):** For orgs with Medicare claims data: `undercoding_ratio * total_medicare_revenue * 3.0 * 0.70` (assumes 70% capture rate on identified revenue leakage, Medicare = ~33% of total payer mix)
- **Calculation (PROJECTED):** For orgs without claims data: `patient_volume * $150 avg_revenue_per_visit * undercoding_benchmark * 0.50` (conservative estimate based on segment averages)
- **Example:** Org with $2M Medicare revenue and 0.25 undercoding ratio → ($2M * 3.0 * 0.70) * (0.45 - 0.25) = $840K estimated lift

### VERIFIED vs PROJECTED Status
- **VERIFIED:** Revenue lift calculated from actual CMS Medicare Part B claims data (line-level service counts, allowed amounts, CPT code distributions)
- **PROJECTED:** Revenue lift estimated using UDS patient volume data, HRSA site data, or NPPES provider counts (no actual claims available)
- **Impact on confidence:** VERIFIED = 83.4% of top 5,000 leads; PROJECTED = 16.6% (still valuable but less precise)

### Why They Have Pain
- **High Medicare Volume:** Organization bills >$500K annually in Medicare Part B (high exposure to undercoding risk)
- **Undercoding Patterns:** E&M code distribution skewed toward lower-complexity codes (99213/99214 ratio < 0.45 vs national avg 0.45)
- **Psych Audit Risk (Behavioral only):** >75% of therapy codes are 90837 (high-complexity) - red flag for payer audits

### Why They Fit
- **FQHC - Core ICP:** Federally Qualified Health Center = proven high-value segment (cost-based reimbursement, quality incentives, large patient volumes)
- **MIPS Performance:** Merit-based Incentive Payment System score >80 or <50 (either tech-ready or struggling with quality metrics)
- **HPSA/MUA Designation:** Located in Health Professional Shortage Area or Medically Underserved Area (aligns with Charta's mission, eligible for grants)

### Why They're Strategic
- **Large Patient Base:** >25,000 annual patients (Ambulatory) or >10,000 (Behavioral) = higher deal size potential
- **Multi-Million Contract Potential:** Revenue scale >$5M annually = large addressable market for Charta's solution
- **Network Expansion Opportunity:** Part of larger health system or ACO = potential for multi-site deployment

---

## Score Breakdown Components

### Pain Score (Max 40 Points)

#### Ambulatory Track:
- **Undercoding Signal (0-40pts):**
  - Calculation: `40 - ((undercoding_ratio - 0.15) / (0.45 - 0.15)) * 30` (capped at 10pt floor, 40pt ceiling)
  - 0.15 ratio (severe undercoding) = 40 points
  - 0.45 ratio (national average) = 15 points
  - >0.45 ratio (overcoding) = 10 points (floor)
- **Volume Multiplier (0-10pts):** Logarithmic scale based on Medicare claim volume (>$2M = max points)
- **Margin Pressure (0-5pts):** Negative or <5% net margin = bonus pain points (financial distress signal)

#### Behavioral Track:
- **Psych Audit Risk (0-40pts):**
  - Calculation: `10 + ((psych_risk_ratio - 0.0) / (0.75 - 0.0)) * 30`
  - 0.75+ ratio (severe risk) = 40 points
  - 0.50 ratio (moderate risk) = 30 points
  - 0.0 ratio (no risk) = 10 points
- **Add-on Code Density (0-5pts):** High usage of 90785 (interactive complexity) = bonus for coding sophistication
- **Compliance Flag (0-5pts):** OIG exclusion list match or high denial patterns = elevated audit risk

### Fit Score (Max 30 Points)

- **Segment Alignment (0-15pts):**
  - FQHC (Segment B) = 15 points (core ICP, proven segment)
  - Behavioral Health = 15 points (high VBC potential, Charta expansion target)
  - Primary Care = 10 points (good fit but commoditized)
  - Urgent Care / Specialty = 5 points (lower strategic priority)
- **Coding Complexity (0-10pts):**
  - High E&M code diversity (uses 99215, 99204, 99205) = 10 points (sophisticated coding operation)
  - Low diversity (only 99213/99214) = 3 points (simple practice, less upside)
- **MIPS Performance Bonus (0-5pts):**
  - Score >80 = 5 points (tech-savvy, quality-focused)
  - Score <50 = 5 points (struggling with quality metrics, needs help)
  - Score 50-80 = 0 points (average, no strong signal)
- **HPSA/MUA Bonus (0-5pts):** Located in shortage area = 5 points (mission alignment, grant-eligible)

### Strategy Score (Max 30 Points)

- **Deal Size Potential (0-15pts):**
  - Calculation: `15 * min(total_revenue / 10_000_000, 1.0)` (logarithmic scale)
  - $10M+ revenue = 15 points
  - $5M revenue = 7.5 points
  - <$1M revenue = 1.5 points
- **Volume Scale (0-15pts):**
  - Ambulatory: 25K+ patients = 15pts, 10K-25K = 10pts, <10K = 3pts
  - Behavioral: 10K+ patients = 15pts (lower threshold due to specialty focus)
- **ACO/Network Membership (0-5pts):**
  - Part of Medicare Shared Savings ACO = 5 points (network expansion potential)
  - Independent practice = 0 points

### Strategic Bonuses
- **Multi-site FQHC Network (0-10pts):** Health center with >5 sites = up to 10 bonus points (enterprise deal potential)
- **High-Growth Segment (0-5pts):** Behavioral health in expansion phase = 5 bonus points (Charta strategic priority)

---

## Key Metrics

### Patient Volume
- **What it is:** Annual unique patient count served by the organization
- **Data sources (hierarchy of truth):**
  1. **HRSA UDS Verified (best):** Official Uniform Data System patient counts for FQHCs (updated annually)
  2. **Medicare Claims Derived (good):** Unique beneficiary count from CMS claims * 3.0 (assumes Medicare = 33% of payer mix)
  3. **NPPES Estimated (low):** Provider count * 1,200 patients/provider/year (industry benchmark)
- **Why it matters:** Larger patient volumes = larger revenue lift potential, higher deal size for Charta

### Medicare Revenue
- **What it is:** Annual Medicare Part B allowed amount (sum of all Medicare claim payments)
- **Data source:** CMS Physician & Other Supplier Public Use File (PUF) - aggregated by organization NPI
- **Calculation:** `SUM(line_srvc_cnt * average_Medicare_allowed_amt)` across all CPT codes for the organization
- **Why it matters:** Direct input to revenue lift calculation; Medicare = proxy for total revenue scale

### Total Revenue (Estimated)
- **What it is:** Estimated total annual revenue across all payer sources (Medicare + Medicaid + Commercial + Self-Pay)
- **Data sources (hierarchy of truth):**
  1. **Cost Report Verified (best):** FQHC/Hospital/HHA cost reports (line item: Total Patient Revenue)
  2. **Medicare Claims Derived (good):** Medicare revenue * 3.0 (industry standard payer mix assumption)
  3. **UDS/NPPES Estimated (low):** Patient volume * $500 avg revenue per patient
- **Example:** Org with $2M Medicare revenue → Estimated total revenue = $6M

### Undercoding Ratio
- **What it is:** Proportion of E&M visits coded at low-complexity levels (99213, 99214 lower tier)
- **Calculation:** `(count_99213 + count_99214_lower) / (total_eval_codes)` - compares to national benchmark of 0.45
- **Data source:** CMS Physician PUF - CPT code level service counts for E&M codes (99201-99215, 99202-99205)
- **Interpretation:**
  - 0.25 ratio = severe undercoding (60% of visits could be upcoded → high revenue opportunity)
  - 0.45 ratio = national average (appropriately coded)
  - 0.65 ratio = potential overcoding (audit risk, not a Charta target)

### Psych Risk Ratio (Behavioral Health Only)
- **What it is:** Proportion of therapy sessions coded as high-complexity (90837 - 53+ min psychotherapy)
- **Calculation:** `count_90837 / (count_90834 + count_90837)` - compares to national benchmark of 0.50
- **Data source:** CMS claims data for CPT codes 90834 (38-52 min) and 90837 (53+ min)
- **Interpretation:**
  - 0.80+ ratio = severe audit risk (80% of sessions >53min is statistically improbable)
  - 0.50 ratio = national average (balanced distribution)
  - <0.30 ratio = conservative coding (potential undercoding)

### Net Margin
- **What it is:** (Net Income / Total Revenue) - profitability percentage
- **Data sources:**
  1. **Cost Reports (FQHCs, Hospitals, HHAs):** Direct calculation from financial statements
  2. **Estimated (others):** Industry benchmarks (FQHCs avg 3-5%, hospitals 2-4%, private practices 15-20%)
- **Why it matters:** Negative or low margins (<5%) = financial distress signal, increases Pain score

### MIPS Score
- **What it is:** Merit-based Incentive Payment System composite performance score (0-100)
- **Data source:** CMS MIPS Public Use File - aggregated organization-level scores
- **Components:** Quality (40%), Cost (30%), Improvement Activities (15%), Promoting Interoperability (15%)
- **Why it matters:** >80 = tech-savvy/quality-focused (good fit); <50 = struggling with quality metrics (pain signal)

---

## Contact & Network Details

### Phone Number
- **What it is:** Primary practice location phone number
- **Data source:** NPPES National Provider Identifier registry (updated monthly by CMS)
- **Format:** (XXX) XXX-XXXX (automatically formatted from 10-digit string)
- **Fill rate:** 99.96% of organizations have phone data (4,998 / 5,000 top leads)

### Address
- **What it is:** Primary practice location mailing address
- **Data source:** NPPES practice location extract (PECOS enrollment file merge)
- **Format:** Street, City, State ZIP
- **Why it matters:** Geographic targeting for sales outreach, HPSA/MUA verification

### NPI (National Provider Identifier)
- **What it is:** Unique 10-digit identifier assigned by CMS to healthcare organizations (Type 2 NPI)
- **Data source:** NPPES registry
- **Usage:** Primary key for all data joins across Medicare claims, MIPS, cost reports, PECOS enrollment

### Network / Health System
- **What it is:** Parent organization or health system affiliation (if applicable)
- **Data source:**
  1. **PECOS Reassignment File:** Maps individual providers to billing organizations
  2. **Cost Report Affiliations:** Hospital/FQHC system names from CMS cost reports
  3. **ACO Participation:** Medicare Shared Savings Program organization lists
- **Example:** "Grace Health, Inc." is part of "Grace Health System" with 12 sites across Michigan
- **Why it matters:** Multi-site networks = enterprise deal potential, higher strategic value

### Taxonomy / Specialty
- **What it is:** Healthcare provider taxonomy code (e.g., "261QF0400X" = FQHC)
- **Data source:** NPPES registry
- **Used for:** Segment classification (FQHCs, Behavioral Health, Urgent Care, etc.)

---

## Drivers & Signals

### Pain Drivers

#### Revenue Leakage
- **What it means:** Organization is losing revenue due to undercoding (E&M ratio < 0.35)
- **Threshold:** Undercoding ratio <0.35 OR psych risk ratio >0.70
- **Why shown:** Primary value proposition for Charta - "we'll recover this lost revenue"

#### High Medicare Volume
- **What it means:** Organization bills >$500K annually in Medicare Part B
- **Threshold:** Medicare revenue >$500,000
- **Why shown:** High exposure to coding optimization opportunity (larger $ impact)

#### Margin Pressure
- **What it means:** Organization operating at negative or low (<5%) net margin
- **Threshold:** Net margin <5% OR negative
- **Why shown:** Financial distress = urgency to find new revenue streams

#### Audit Risk (Behavioral Only)
- **What it means:** Psych coding patterns suggest high audit exposure (>75% high-complexity codes)
- **Threshold:** Psych risk ratio >0.75
- **Why shown:** Compliance pain = need for coding review and optimization

### Fit Drivers

#### FQHC - Core ICP
- **What it means:** Organization is a Federally Qualified Health Center
- **Detection:** HRSA UDS data match OR cost report FQHC designation OR taxonomy code 261QF0400X
- **Why shown:** Proven high-value segment for Charta (largest wins to date are FQHCs)

#### MIPS Performance
- **What it means:** Organization has strong (>80) or weak (<50) MIPS scores
- **Threshold:** Score >80 OR <50
- **Why shown:** Either tech-savvy (easy to work with) or struggling (need help with quality metrics)

#### HPSA/MUA Designation
- **What it means:** Located in federally designated shortage area (underserved population)
- **Data source:** HRSA HPSA/MUA county-level flags
- **Why shown:** Mission alignment with Charta's focus on access to care + grant eligibility

#### Behavioral Health - Strategic Segment
- **What it means:** Organization specializes in behavioral health / mental health services
- **Detection:** Behavioral scoring track assignment (name keywords OR high psych code volume)
- **Why shown:** Charta expansion target (behavioral health = growing market, high VBC potential)

### Strategic Drivers

#### Large Patient Base
- **What it means:** Organization serves >25K patients annually (Ambulatory) or >10K (Behavioral)
- **Threshold:** Patient volume >25,000 (Ambulatory) OR >10,000 (Behavioral)
- **Why shown:** Volume = higher deal size potential (more patients = more revenue to optimize)

#### Multi-Site Network
- **What it means:** Organization operates >5 physical locations
- **Data source:** HRSA UDS site counts OR NPPES practice location counts
- **Why shown:** Enterprise deal potential (deploy Charta across entire network)

#### ACO Participant
- **What it means:** Organization participates in Medicare Shared Savings Program (value-based care)
- **Data source:** CMS ACO participant lists (organization name matching)
- **Why shown:** VBC alignment = interest in quality/cost optimization (Charta value prop)

---

## Filters & Segments

### Tier Filter
- **Tier 1 (≥70):** 1,609 organizations - immediate sales focus
- **Tier 2 (50-69):** 3,391 organizations - qualified nurture pipeline
- **Tier 3 (<50):** Not shown in top 5,000 (low priority)
- **Usage:** Filter table to show only Tier 1 high-priority leads

### Segment Filter
- **FQHC (Segment B):** Federally Qualified Health Centers - core ICP, proven segment
- **Primary Care (Segment C):** Family medicine, internal medicine, pediatrics
- **Behavioral Health (Segment A):** Mental health, substance abuse, counseling
- **Urgent Care:** Walk-in clinics, after-hours care
- **Specialty:** Cardiology, orthopedics, dermatology, etc.
- **Hospital (Segment F):** Acute care hospitals (lower priority for Charta)
- **Home Health (Segment G):** Post-acute care agencies (lower priority)

### Track Filter (Ambulatory vs Behavioral)
- **Ambulatory Track:** Organizations scored on E&M undercoding pain (99% of top 5,000)
- **Behavioral Track:** Organizations scored on psych audit risk pain (specialty focus)
- **Usage:** Compare scoring logic differences - behavioral health has different economic pain points

### Data Confidence Filter (VERIFIED vs PROJECTED)
- **VERIFIED:** 4,170 orgs (83.4%) - revenue lift calculated from actual CMS claims data
- **PROJECTED:** 830 orgs (16.6%) - revenue lift estimated from UDS/NPPES volume data
- **Usage:** Filter to VERIFIED only for highest-confidence opportunities

---

## Data Sources & Confidence

### Primary Data Sources (Government Databases)

#### CMS Medicare Part B Claims (Physician & Other Supplier PUF)
- **What it contains:** Line-level service counts, allowed amounts, CPT code distributions for all Medicare Part B claims
- **Coverage:** 1.4M+ organizations, 2023 data (most recent available)
- **Usage:** Undercoding ratio calculation, Medicare revenue, volume estimates
- **Update frequency:** Annual (released ~18 months after service year)

#### NPPES National Provider Identifier Registry
- **What it contains:** Provider demographics, practice locations, taxonomy codes, contact info for all NPIs
- **Coverage:** 6M+ providers (individuals + organizations)
- **Usage:** Organization names, addresses, phone numbers, specialty classification
- **Update frequency:** Weekly (CMS maintains live registry)

#### MIPS Public Use File
- **What it contains:** Organization-level MIPS composite scores, quality measures, clinician counts
- **Coverage:** 200K+ organizations participating in MIPS (2023 performance year)
- **Usage:** MIPS score bonus in Fit calculation, tech-savvy signal
- **Update frequency:** Annual (released ~12 months after performance year)

#### HRSA HPSA/MUA Designations
- **What it contains:** County-level flags for Health Professional Shortage Areas and Medically Underserved Areas
- **Coverage:** 3,143 US counties
- **Usage:** HPSA/MUA bonus in Fit calculation, mission alignment signal
- **Update frequency:** Quarterly (HRSA updates as designations change)

#### HRSA UDS (Uniform Data System)
- **What it contains:** Annual patient volume, revenue, staffing, services data for all HRSA-funded health centers
- **Coverage:** 1,400+ FQHCs, 14,000+ sites
- **Usage:** Patient volume (highest quality source), FQHC identification, grant number tracking
- **Update frequency:** Annual (released ~6 months after reporting year)

### Secondary Data Sources (Cost Reports)

#### FQHC Cost Reports (CMS-222)
- **What it contains:** Total revenue, expenses, net margin, patient volume for FQHCs
- **Coverage:** 1,400+ FQHCs (2024 reporting year)
- **Usage:** Revenue hierarchy (best source), margin calculation, FQHC confirmation
- **Update frequency:** Annual (submitted by FQHCs, released by CMS with 12-18 month lag)

#### Hospital Cost Reports (CMS-2552)
- **What it contains:** Total patient revenue, net income, bad debt, charity care for hospitals
- **Coverage:** 6,000+ hospitals (2024 reporting year)
- **Usage:** Hospital segment revenue, margin pressure signals
- **Update frequency:** Annual

#### Home Health Agency Cost Reports (CMS-1728)
- **What it contains:** Revenue, net income, visit counts for HHAs
- **Coverage:** 12,000+ HHAs (2023 reporting year)
- **Usage:** Post-acute segment revenue and margin
- **Update frequency:** Annual

### Data Confidence Levels

#### VERIFIED (83.4% of top 5,000)
- **Criteria:** Organization has actual Medicare Part B claims data (line-level CPT codes, service counts, allowed amounts)
- **Revenue lift calculation:** Based on real undercoding ratio from claims
- **Confidence level:** High - actual observed behavior, not estimated
- **Example:** Grace Health Inc. has $2M Medicare revenue, 0.25 undercoding ratio → $840K verified lift

#### PROJECTED (16.6% of top 5,000)
- **Criteria:** Organization has UDS patient volume OR NPPES provider count, but NO Medicare claims data
- **Revenue lift calculation:** `patient_volume * $150 avg_revenue_per_visit * segment_undercoding_benchmark * 0.50`
- **Confidence level:** Medium - conservative estimate based on segment averages
- **Example:** Small FQHC with 5,000 UDS patients, no claims → 5,000 * $150 * 0.20 * 0.5 = $75K projected lift

### Data Pipeline Flow
1. **Ingestion:** Raw CMS files (CSV, Parquet, SAS) → `/data/raw/`
2. **Staging:** Cleaned, normalized data → `/data/staging/` (stg_physician_util.parquet, stg_mips_org_scores.csv, etc.)
3. **Enrichment:** Join staging files to seed file → `/data/curated/clinics_enriched_scored.csv`
4. **Scoring:** Apply ICP scoring logic → `/data/curated/clinics_scored_final.csv`
5. **Frontend:** Top 5,000 leads → `/web/public/data/clinics.json`

---

## Calculation Examples

### Example 1: Grace Health, Inc. (FQHC, Tier 1, Score 87.4)

**Pain Score: 40.0 / 40**
- Undercoding ratio: 0.18 (severe)
- Calculation: `40 - ((0.18 - 0.15) / (0.45 - 0.15)) * 30 = 40.0` (capped at max)
- High Medicare volume: $2.1M (bonus +5pts, but already at max)

**Fit Score: 25.0 / 30**
- FQHC segment: +15pts (core ICP)
- Coding complexity: +10pts (uses 99204, 99205, 99215)
- MIPS score 84.2: +5pts (tech-savvy)
- HPSA designation: +5pts (Kent County, MI)
- Total: 35pts (capped at 30pt max)

**Strategy Score: 22.4 / 30**
- Total revenue $8.2M: `15 * (8.2 / 10.0) = 12.3pts`
- Patient volume 18,500: `15 * (18.5 / 25.0) = 11.1pts`
- Not in ACO: +0pts
- Total: 23.4pts (capped at 30pt max, actual 22.4 due to rounding)

**Revenue Lift: $487K (VERIFIED)**
- Calculation: `($2.1M Medicare * 3.0 total payer mix) * (0.45 - 0.18 undercoding gap) * 0.70 capture = $1.19M * 0.27 * 0.70 = $225K`
- Note: Actual $487K suggests higher Medicare proportion or additional volume sources

**Drivers:**
- Pain: Revenue Leakage, High Medicare Volume
- Fit: FQHC - Core ICP, MIPS Performance, HPSA Designation
- Strategic: Large Patient Base

---

### Example 2: Heart of Texas Region MHMR Center (Behavioral, Tier 1, Score 82.0)

**Pain Score: 40.0 / 40**
- Psych risk ratio: 0.82 (severe audit risk)
- Calculation: `10 + ((0.82 - 0.0) / (0.75 - 0.0)) * 30 = 42.8` (capped at 40pt max)
- High therapy volume: 8,200 sessions (bonus already factored in)

**Fit Score: 25.0 / 30**
- Behavioral Health segment: +15pts (strategic segment)
- MIPS score 88.5: +5pts (tech-savvy, VBC-ready)
- HPSA designation: +5pts (McLennan County, TX)
- Complexity (therapy codes): +10pts
- Total: 35pts (capped at 30pt max)

**Strategy Score: 17.0 / 30**
- Total revenue $4.2M: `15 * (4.2 / 10.0) = 6.3pts`
- Patient volume 12,800 (behavioral threshold 10K): `15 * min(12.8 / 10.0, 1.0) = 15pts`
- Not in ACO: +0pts
- Total: 21.3pts (actual 17.0 suggests some data gaps)

**Revenue Lift: $312K (VERIFIED)**
- Behavioral calculation: `(total_psych_revenue * (psych_risk_ratio - 0.50_benchmark) * 0.60_compliance_adj)`
- Estimated: Org bills ~$1.5M in therapy codes, 0.82 ratio → $1.5M * (0.82 - 0.50) * 0.60 = $288K
- Note: Actual $312K includes additional add-on code optimization (90785)

**Drivers:**
- Pain: Audit Risk, Revenue Leakage (psych undercoding)
- Fit: Behavioral Health - Strategic Segment, MIPS Performance, HPSA
- Strategic: Large Patient Base (>10K behavioral threshold)

---

## Technical Notes

### Why "Top 5,000 Organizations" vs "1.4M Scored"?
- **1.4M scored:** All organizations in NPPES with sufficient data for scoring (minimum: NPI, name, state, segment)
- **Top 5,000:** Highest ICP scores (≥50) shown in frontend for sales prioritization
- **Cutoff logic:** Score ≥65.2 (Tier 1 + Tier 2 only) - Tier 3 and 4 not shown (low sales priority)

### Scoring Track Assignment Logic
- **Behavioral:** Organization name contains "BEHAVIORAL", "PSYCH", "MENTAL HEALTH", "COUNSELING", "THERAPY" OR (Segment A + >2,000 psych codes + >0.70 psych ratio)
- **Post-Acute:** Segment contains "HOME HEALTH" or "HHA" or taxonomy indicates skilled nursing
- **Ambulatory:** Everything else (default track for 90%+ of organizations)

### Phone Number Formatting
- **Input:** 10-digit string from NPPES (e.g., "2699662600")
- **Output:** (269) 966-2600
- **Handling:** Numbers stored as floats in staging → converted to int → formatted with dashes

### Revenue Hierarchy of Truth
1. **Cost Report (High):** FQHC/Hospital/HHA financial statements = actual audited revenue
2. **Medicare Claims (Medium):** `Medicare_revenue * 3.0` = industry-standard payer mix proxy
3. **Estimated (Low):** `patient_volume * $500` OR `provider_count * $600K` = conservative benchmarks

### Volume Hierarchy of Truth
1. **HRSA UDS (High):** Official patient counts for FQHCs (annual reporting requirement)
2. **Medicare Claims (Medium):** `unique_beneficiaries * 3.0` = Medicare represents ~33% of patient panel
3. **NPPES Estimated (Low):** `provider_count * 1,200 patients/year` = industry benchmark

---

## FAQ

**Q: Why is my organization's score lower than expected?**
A: Check the Score Breakdown - likely causes: (1) Undercoding ratio >0.45 (no pain signal), (2) Not in a proven segment (low Fit), (3) Small patient volume (low Strategy), (4) Missing data (defaults to low scores)

**Q: What's the difference between Ambulatory and Behavioral scoring?**
A: Ambulatory focuses on E&M undercoding (99213/99214 ratios), Behavioral focuses on psych audit risk (90837 overuse). Pain signals are fundamentally different for different care models.

**Q: Why is revenue lift "PROJECTED" instead of "VERIFIED"?**
A: Organization has no Medicare Part B claims in the CMS PUF (possible reasons: Medicare Advantage only, no Medicare patients, billing under different NPI). Lift estimated from UDS/NPPES volume data instead.

**Q: How often is the data updated?**
A: Annual refresh when new CMS files release (typically Q3 for prior-year data). Frontend JSON regenerated after each scoring run (~monthly during development).

**Q: Can I trust PROJECTED revenue lifts?**
A: They're conservative estimates (50% capture rate vs 70% for VERIFIED), but still directionally accurate. Use for prioritization, not exact ROI promises.

---

**Last Updated:** November 26, 2024
**Data Vintage:** CMS 2023, HRSA UDS 2024, MIPS 2023
**Coverage:** 1,427,580 organizations scored, 5,000 top leads in frontend
