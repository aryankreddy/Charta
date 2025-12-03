# 01_Architecture.md — Clinic Finder & GTM Engine (Charta Edition)

> Purpose: design a **feasible, high-impact** system that a single builder can ship in Cursor, using **public data only**, with a clear **Charta-specific value add** that goes **beyond “ChatGPT + a scraper.”**

---

## 0) Design Principles (mapped to your 3 constraints)

* **Feasible**

  * All inputs are **public or free-to-trial** (government datasets, directories, org sites, events).
  * HIPAA-safe: **no PHI**, only org-level and role-level data.
  * Ship as slices: **MVP in 7–10 build sessions**, then additive enrichers.

* **Valuable**

  * Optimized for **immediate GTM use**: deduped accounts, key contacts, **ICF (Ideal Customer Fit)** score, outreach cues, and region/segment filters.
  * **Charta spin**: features that align with **pre-bill review**, **denial prevention**, **RCM ops pain**, **EMR agnosticism**, and **RVU uplift** ROI narrative.

* **Beyond ChatGPT + Cursor**

  * Opinionated **scoring models** (Denial Pressure Index, EMR Friction Score, Coding Complexity Proxy).
  * **Entity resolution** across messy data sources + **explainable fit**.
  * A **mini knowledge graph** to reason across clinic→location→EMR→payer→specialty→policy context.

---

## 1) High-Level System Diagram

**Ingestion → Normalization → Enrichment → Scoring → Serving (API/UI) → Ops Loops**

1. **Ingestion Layer** (Python jobs)

   * Sources: NPI Registry, CMS (PECOS, Care Compare), state corp registries/Medicaid enrolled provider lists, payer directories (public), org websites, job postings, conference exhibitor lists, Healthgrades/Yelp (for basic presence/scale proxy), LinkedIn company pages (public metadata only).
   * Output: raw JSON/CSV files in `/data/raw/{source}/{date}.jsonl`.

2. **Normalization & Entity Resolution**

   * Standardize names/addresses (USPS addressing via simple regex + fuzzy matching).
   * **Entity resolution**: `clinic_id` via NPI + (name, phone, address) fuzzy key; dedupe branches.
   * Output: `/data/curated/clinics.parquet`.

3. **Enrichment Layer**

   * **Specialty mapping** (taxonomy → segments Charta wins in: primary care, urgent, BH, home health).
   * **Scale proxies**: #providers (count of NPIs per org), #locations, review volume, hiring signals.
   * **Tech stack cues**: EMR from careers pages, vendor pages, PDFs; claims clearinghouse hints; revcycle job posts.
   * **Payer context**: Medicare/Medicaid participation flags; ACO participation (if public); state denials headlines (press/AG reports) → light heuristic tags.

4. **Scoring Layer (Charta Fit)**

   * Composite: **ICF Score** = w₁ * Segment Fit + w₂ * Scale + w₃ * EMR Friction (inverted) + w₄ * Coding Complexity Proxy + w₅ * Denial Pressure Index + w₆ * ROI Readiness.
   * **Explainability**: top 3 drivers + evidence (URLs/snippets).

5. **Serving Layer**

   * **SQLite/Postgres** for data; a **FastAPI** read-only API (Cursor-friendly).
   * **Next.js + Tailwind dashboard**: filters, saved views, CSV export, lead sheets.

6. **Ops & Feedback**

   * “**Research tasks**” queue (missing EMR, confirm specialty) with single-click updates.
   * **Audit logs**: when a fact was seen, from where.
   * **Versioned scoring** to A/B fit models.

---

## 2) Data Model (Core Schema)

**Entity: `clinic`**

* `clinic_id` (uuid)
* `legal_name`, `brand_name`, `aliases[]`
* `npi_org` (if any), `npi_members[]` (linked to clinicians)
* `domains[]`, `phone`, `hq_address`, `locations[]`
* `segments[]` (mapped: Primary Care, Urgent Care, Behavioral Health, Home Health, Specialty Care-other)
* **Scale**: `num_locations`, `num_clinicians_proxy`, `visit_volume_proxy`
* **Tech**: `emr_vendor` (enum/unknown), `rcm_vendor?`, `clearinghouse?`
* **Payer flags**: `medicare_participating`, `medicaid_state_codes[]`, `aco_flag?`
* **Signals**: `hiring_roles[]` (coding, auditor, RCM), `policy_mentions[]`, `press_hits[]`
* **Scores**: `icf_score` (0–100), `denial_pressure_index`, `emr_friction`, `coding_complexity_proxy`, `roi_readiness`
* **Evidence**: `evidence_links[]`, `evidence_snippets[]`
* `updated_at`, `source_fingerprints[]`

**Entity: `location`** (child)

* `clinic_id`, `address`, `lat`, `lng`, `phone`, `services[]`, `hours`

**Entity: `contact`** (optional; public role-level only)

* `clinic_id`, `name`, `title` (CFO, RCM Director, Compliance, Coding Manager), `email?` (only if public), `linkedin_url?`, `evidence_link`

---

## 3) Scoring: Charta-Specific Fit Axes (explainable)

1. **Segment Fit (0–25)**

   * Boost: **Primary Care, Urgent Care, Behavioral Health, Home Health**.
   * Specialty-agnostic fallback if high volume + documented coding complexity.

2. **Scale & Velocity (0–20)**

   * #locations, #clinicians(NPI members), hiring growth, review volume proxies.

3. **EMR Integration Friction (0–15, inverted)**

   * +15 if EMR is common/EMR-agnostic integration known; +8 unknown; +4 exotic.

4. **Coding Complexity Proxy (0–15)**

   * Presence of multi-coder team hiring, specific coding roles, complex service lines, frequent E/M references.

5. **Denial Pressure Index (0–15)**

   * Signals of denial issues: careers (denial management roles), press mentions, payer/state headlines; segment-level priors (e.g., BH & HH higher documentation burden).

6. **ROI Readiness (0–10)**

   * Evidence of margin pressure, manual audits (1–10% review), appetite for automation, quality initiatives, value-based contracts.

**Output**:

* `icf_score` and **Top Drivers** with `because:` bullets referencing evidence.

---

## 4) Novel “Charta Spin” Features (Differentiators)

* **Pre-Bill Focused Cues**: flag clinics discussing **pre-bill audits**, **compliance policies**, **LCD/NCD** awareness.
* **Claims Denial Heat**: simple **state-level overlay** (Medicaid rules tightening, local payer disputes) to boost Denial Pressure Index.
* **EMR-Agnostic Narrative**: auto-generate a 1-liner “**Integration path hypothesis**” per clinic based on detected EMR and clearinghouse mentions.
* **RVU Uplift Story Seeds**: generate a **case-style “why now”** note for each high-fit clinic (e.g., “primary care, multisite, manual audits likely ≤10%, payer mix w/ X; expect 11% RVU uplift opportunity”).
* **Explainability Cards**: every score is backed by **clickable evidence**—a sales-enablement feature out of the box.

---

## 5) Data Pipeline (Step-by-Step)

**Batch v0 (MVP 1–2 weeks of evenings):**

1. **Seed Sources**

   * NPI Registry (org + clinician counts), CMS Care Compare (where applicable), state-level Medicaid enrolled lists (CSV/PDF to table), public directories (Healthgrades/Yelp for presence/volume proxy), org websites (About/Careers).
2. **Ingestion Scripts**

   * Python `ingest_{source}.py` → write JSONL to `/data/raw/...`.
3. **Normalize & Resolve**

   * Fuzzy match clinic names/phones/addresses; generate `clinic_id`; link members.
4. **Light Enrichment**

   * Specialty mapping (taxonomy→segment), scale proxies (count NPIs), hiring scrape (RCM/coder roles), EMR hints (careers pages).
5. **Score v1**

   * Deterministic rules + simple weights (tunable constants in `.env`/YAML).
6. **Serve**

   * FastAPI read endpoints: `/clinics?segment=&state=&min_score=`; CSV export.
   * Next.js table view with filters + “export selection.”

**Batch v1.5 (Polish in week 2–3):**

* Add **evidence snippet capture** (quote + URL).
* Add **saved views** (e.g., “Behavioral Health, TX, ICF ≥ 70”).
* Add **research task queue** for missing EMR.
* Add **basic map** (Leaflet) for geo heat.

**Batch v2 (Stretch):**

* A minimal **knowledge graph** (SQLite relations) powering “show me clinics using athenahealth in CO with ≥3 locations and denial pressure ≥ medium.”
* **Contact role inference** via public pages (no scraping behind auth).
* **Score A/B** versions (ops switch).

---

## 6) Frontend (GTM Dashboard Spec)

**Views**

* **Leads Table**: columns = Name, Segment, State, Locations, EMR, ICF, Top Drivers (hover), Actions (Export, Copy Notes).
* **Map**: cluster by ICF score; click → card with evidence.
* **Segment Panels**: “Primary Care,” “BH,” etc., each with saved filters.
* **Clinic Detail**: left (facts), right (Fit Drivers, Evidence links, “Charta angle” 1-pagers).

**Instant GTM Outputs**

* **CSV/HubSpot-ready export**: `account_name, domain, segment, state, emr, icf_score, note_snippet, links`.
* **Narrative Snippets**: per clinic, 2–3 lines (“why now + integration path + ROI angle”) to paste into outbound.

---

## 7) Security, Compliance, and Ethics

* **No PHI**; org-level only; public sources only; respect robots.txt.
* **Rate-limited** requests; cache responses; polite backoffs.
* **Attribution**: store `source_url`, `first_seen`, `last_confirmed`.
* **Human-in-the-loop** mode for any ambiguous inference.

---

## 8) Implementation Plan (Cursor-Friendly)

**Repo structure**

```
/apps
  /api (FastAPI)
  /web (Next.js)
  /workers (Python ingesters)
  /notebooks (EDA, scoring sandbox)
/data
  /raw
  /curated
  /exports
/config
  sources.yaml
  scoring.yaml
```

**Key modules**

* `/workers/ingest_npi.py`, `ingest_cms.py`, `ingest_state_medicaid.py`, `ingest_web_dirs.py`
* `/workers/normalize.py` (name/addr/phone clean, fuzzy match)
* `/workers/enrich.py` (taxonomy→segment, scale, EMR hints, hiring signals)
* `/workers/score.py` (ICF calc + top drivers)
* `/apps/api/main.py` (FastAPI: `/clinics`, `/clinic/{id}`, `/export`)
* `/apps/web` (Next.js pages: `/`, `/clinic/[id]`)

**Tooling**

* Python: `requests`, `httpx`, `pydantic`, `rapidfuzz`, `pandas`, `duckdb` or Postgres driver.
* Frontend: Next.js, Tailwind, React Table, Leaflet.
* DevX: `.env` for keys, `make ingest-all`, `pre-commit` with black/ruff.

---

## 9) Demo Storyline (for impress factor)

1. Open dashboard on **“Behavioral Health in TX, ICF ≥ 70”**.
2. Click top clinic → show **Top Drivers** with evidence links (careers page showing coder hiring, EMR hint from vendor PDF, Medicaid flag).
3. Hit **Export** → CSV with **ready notes**.
4. Show **A/B scores** by toggling “Denial-first vs Growth-first” model.
5. Add a research task (“Confirm EMR”) → demonstrate **ops loop** maturity.

---

## 10) Risks & Mitigations

* **Sparse EMR data** → Mitigate with multiple weak signals: careers text, vendor PDFs, integration pages, job posts; mark confidence.
* **Messy entities** → Strong dedupe keys + human override queue.
* **Over-scraping** → Respect robots.txt, rate limits, cache, prefer **bulk/open data** first.
* **Signal bias** → Keep **evidence links** and **confidence** per feature; allow manual edits.

---

## 11) What Makes This “Charta” (Value Add Summary)

* **Pre-bill & denial-centric** scoring, not generic TAM mapping.
* **Explainable ICF** tied to **revenue integrity** and **compliance** narratives.
* **Integration path hints** (EMR-agnostic stance) surfaced per account.
* **Immediate sales enablement** (exportable notes + saved segment views).
* **Ops-ready** (tasks, evidence, versioned scores) — shows you operate like a **scrappy GTM engineer**.

---

## 12) Acceptance Criteria (MVP)

* ≥ **3,000 deduped clinics** across 2–3 target segments.
* ≥ **70%** have segment, state, scale proxy; ≥ **30%** have EMR hint.
* **ICF scores** populated with **top-3 drivers & links**.
* **Filters + CSV export** working; **one saved view per segment**.
* A 5-minute **click-through demo** that tells a compelling Charta story.

---
