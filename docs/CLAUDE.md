# CHARTA HEALTH GTM INTELLIGENCE: PROJECT CONSTITUTION

> ⚠️ **CRITICAL INSTRUCTION FOR AI:**
> This document is the **Single Source of Truth**.
> 1. **Role:** You are a Data Engineer & Product Strategist for Charta Health.
> 2. **Constraint:** Do NOT deviate from the Schema or Scoring Logic defined below.
> 3. **Philosophy:** We sell "Financial Immunity," not just software. [cite_start]We target "High Volume, Low Margin" providers[cite: 5, 197].

---

## 1. PROJECT ARCHITECTURE & CODEBASE

### The "Self-Healing" Pipeline
Our backend is a deterministic Python engine that transforms raw government data into scored sales leads.

* **Orchestration:** `scripts/run_full_pipeline.sh` (The "Big Red Button").
    * Orchestrates `workers/pipeline/pipeline_main.py`.
* **Ingestion (The Bridge):**
    * `ingest_api.py`: Raw CSV -> Parquet Staging.
    * `ingest_uds_volume.py`: Parses HRSA UDS 2024 Excel files to verify FQHC patient volume (The "Whale" source).
* **Miners (The Heavy Lifters):**
    * `mine_cpt_codes.py`: Processes 2.9GB Medicare claims. Maps Dr. NPI -> Org NPI. Calculates `undercoding_ratio`.
    * `mine_psych_codes.py`: Hunts for audit-risk codes (90837). Calculates `psych_risk_ratio`.
* **Scoring Engine:**
    * `score_icp_production.py`: The "Clean 100" logic engine. No black boxes.
* **Frontend:**
    * `web/app/page.tsx`: Next.js Dashboard.
    * `scripts/update_frontend_data.py`: Generates the "Glass Box" JSON for the UI.

---

## 2. DATA INVENTORY: THE "GOLDEN RECORD"

We do not guess. We verify. Our database covers **1.4M Organizations**.

| Data Asset | Source | Strategic Value | Status |
| :--- | :--- | :--- | :--- |
| **Identity** | NPI Registry | The "Phone Book" (Name, Address, Taxonomy). | ✅ 100% Coverage |
| **Volume (Medicare)** | Physician Utilization | The "Work Logs". Aggregated via PECOS Bridge. | [cite_start]✅ 164k Verified Orgs [cite: 17] |
| **Volume (UDS)** | HRSA UDS 2024 | The "FQHC Truth". Verified patient counts for Safety Net. | ✅ ~1,500 Verified FQHCs |
| **Revenue Leakage** | CPT Mining (Medicare) | **The Smoking Gun.** Proof they are under-billing Level 4 visits. | [cite_start]✅ 104k Matches [cite: 31] |
| **Audit Risk** | Psych Mining | **The Compliance Trap.** Proof of over-billing 60-min therapy. | ✅ 16k Matches |
| **Financials** | Cost Reports (HCRIS) | **The Margin.** Net Income for Hospitals, FQHCs, HHAs. | [cite_start]✅ 3k+ Hospitals, 700 FQHCs [cite: 20] |

---

## 3. THE ICP SCORING MODEL ("CLEAN 100")

We score leads on a strict 100-point scale. We prioritize **Pain** over Fit.

### A. Economic Pain (Max 40 pts)
*Targeting the "Bleeding Whale."*
* **Severe Undercoding (40 pts):** `undercoding_ratio < 0.35`. They are billing way below peer benchmarks. Losing millions.
* **Severe Audit Risk (40 pts):** `psych_risk_ratio > 0.75`. They are flagging for OIG audits. Urgent need for compliance.
* **Verified Gap (30 pts):** `undercoding_ratio < 0.50`. Clear room for improvement.
* **Projected (10 pts):** No claims data, but specialty benchmark suggests opportunity.

### B. Strategic Fit (Max 30 pts)
*Targeting the "Perfect Customer."*
* **Segment Alignment:** FQHCs, Urgent Care, Behavioral Health.
* **Complexity:** Multi-specialty or FQHC billing rules (PPS).
* **Tech Readiness:** ACO Membership or large provider count (>10).

### C. Strategic Value (Max 30 pts)
*Targeting the "Deep Pockets."*
* **Deal Size:** Revenue > $15M (or >$5M for FQHCs).
* **Whale Scale:** Verified Volume > 25,000 patients (UDS/Medicare).

---

## 4. QUALITATIVE INTELLIGENCE (THE "WHY")

This section defines the "Talk Track" for the Sales Team, based on deep research into Charta's value prop.

### The "Why Buy" Narrative
1.  **Financial Immunity:** We don't just code; we protect revenue. [cite_start]For FQHCs operating on <2% margins, a 5% loss is existential[cite: 69, 197].
2.  [cite_start]**The 15.2% Lift:** We target clinics with low `undercoding_ratios` because we can mathematically promise a ~15% lift in RVUs per encounter[cite: 129].
3.  **Audit Insurance:** For Behavioral Health, we target high `psych_risk_ratios` because CMS scrutiny on "time-based codes" (90837) is increasing. [cite_start]We sell sleep[cite: 145].
4.  **Operational Velocity:** For high-volume clinics (>50k visits), the manual chart review process is a bottleneck. [cite_start]We sell velocity[cite: 5].

### Tier Definitions
* **Tier 1 ("Bleeding Whale"):** High Volume + Verified Pain. "I know you are huge, and I can prove you are losing money."
* **Tier 2 ("Strategic Whale"):** High Volume + Good Fit. "You are the perfect size for us, likely have hidden pain."
* **Tier 3 ("Growth"):** Smaller clinics with verified pain. Good for velocity sales.

---

## 5. OPERATIONAL COMMANDS

### To Run the Pipeline (Data Engineering)
```bash
./scripts/run_full_pipeline.sh       # Standard run (uses cache)
./scripts/run_full_pipeline.sh --force # Force re-mine (if logic changes)

## 5. INTELLIGENCE GENERATION LOGIC (The Strategic Brief)
Generate a `strategic_brief` that diagnoses the clinic's operational reality.
**Do NOT write a sales script.** Write an intelligence report.

**Logic Table:**
1.  **The "Cash Flow" Diagnosis:**
    * *Signal:* `undercoding_ratio < 0.35`
    * *Implication:* "Severe revenue leakage detected. Indicates a highly conservative coding culture or lack of certified coding staff. Organization is mathematically under-performing peers by ~15%."
2.  **The "Operational" Diagnosis:**
    * *Signal:* `real_annual_encounters > 50000` (FQHC)
    * *Implication:* "High-volume operation likely suffering from administrative drag. Scale suggests complex EHR infrastructure (NextGen/eCW) where manual chart review is a bottleneck."
3.  **The "Risk" Diagnosis:**
    * *Signal:* `psych_risk_ratio > 0.80`
    * *Implication:* "Aggressive billing on time-based codes (90837). High exposure to OIG scrutiny. Compliance/Risk Officer is the likely key stakeholder."
4.  **The "Blindspot" Diagnosis:**
    * *Signal:* High Volume but No Claims Data.
    * *Implication:* "Data blackout suggests heavy Medicaid/Capitation mix. Financial pain is likely hidden in state-level reimbursement cuts rather than federal claims."