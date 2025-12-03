# 07_Implementation_Plan.md — Build Plan (No day-by-day, just the plan)

> Purpose: a **practical, end-to-end plan** to ship the MVP in Cursor. Organized by **tracks** (Data, Scoring, API, UI, Ops), with clear milestones, handoffs, and acceptance criteria.

---

## 1) Repo & Project Setup

**Structure**

```
/apps
  /api         # FastAPI
  /web         # Next.js + Tailwind + shadcn/ui
  /workers     # Python ingestion/enrichment/score jobs
/config         # keywords.yaml, scoring.yaml, sources.yaml
/data           # raw/ curated/ exports/
/scripts        # make-like helpers
```

**Key dependencies**

* **Python**: `pydantic`, `pandas`, `httpx`, `rapidfuzz`, `beautifulsoup4`, `duckdb` or `psycopg`, `python-slugify`, `tqdm`
* **API**: `fastapi`, `uvicorn`
* **Web**: `next`, `react`, `tailwindcss`, `framer-motion`, `@tanstack/react-table`, `lucide-react`, `react-leaflet`, `zod`, `swr` or `tanstack/query`

**Config files**

* `/config/keywords.yaml` (EMR/RCM/denial/compliance keywords)
* `/config/scoring.yaml` (weights & rules)
* `/config/sources.yaml` (bulk URLs, rate limits)

---

## 2) Data Track (Backbone → Features → Evidence)

### Milestone A — **Backbone Ingestion**

* Workers:

  * `workers/ingest_npi.py` → `npi_org.parquet`, `npi_members.parquet`
  * `workers/ingest_hrsa_fqhc.py` → `hrsa_fqhc_sites.parquet`
  * `workers/ingest_pecos.py` → `pecos_flags.parquet`
  * (optional) `workers/ingest_home_health.py`
* Output: `/data/raw/*` preserved; `/data/curated/base_*` normalized.

**Acceptance**

* ≥3 target segments populated (Primary, BH, Home Health).
* Unique org spine with candidate **clinic_id** per entity.

### Milestone B — **Entity Resolution & Normalization**

* `workers/normalize_entities.py`

  * Standardize names/phones/addresses; generate deterministic `clinic_id`.
  * Link org⇄member; compute `num_clinicians_proxy`.
* Output: `/data/curated/clinics.parquet`, `locations.parquet`.

**Acceptance**

* Dedupe rate documented; collision log exists.
* `clinics` has `segments`, `state_code`, `num_locations`, `num_clinicians_proxy`.

### Milestone C — **Web Enrichment & Signals**

* `workers/scrape_org_sites.py` (locations/services)
* `workers/scrape_careers.py` (ATS & /careers → EMR/RCM/denial/coder signals)
* `workers/ingest_conferences.py` (exhibitors)
* `workers/ingest_places.py` (review_count for pilot states)
* Persist **evidence**: snippet + URL + source.

**Acceptance**

* `features` table populated; `signals` & `evidence` rows present.
* ≥25–40% clinics with **EMR hints** (confidence tagged).

---

## 3) Scoring Track (Explainable ICF)

### Milestone D — **ICF v1**

* `workers/enrich_features.py` (one-hot segments, breadth, flags)
* `workers/score_icf.py` (rule-based axes; top-3 drivers with evidence links)
* Versioning: `scores.model_version = icf_v1.0` from `/config/scoring.yaml`

**Acceptance**

* Each clinic has `icf_score` and **driver list** with evidence ids.
* Reproducible run; score distribution sane (p95/p50 exposed in log).

---

## 4) API Track (Serve for UI & Exports)

### Milestone E — **Read-only API**

* `apps/api/main.py`

  * `GET /clinics` (filters: segment[], state[], icf_min, emr[], size buckets; pagination)
  * `GET /clinic/{id}` (facts + features + latest score + evidence)
  * `GET /export` (returns CSV for current filters)
* Data access via DuckDB (local files) **or** Postgres.

**Acceptance**

* P95 query latency reasonable for 5k–20k rows.
* CSV export contains narrative snippet field.

---

## 5) UI Track (GTM Dashboard)

### Milestone F — **Leads View & Filters**

* Next.js page `/` with:

  * **KPI header strip** (Projected RVU, Top Drivers mix, Export CTA)
  * Left **Filters** (segments, states, ICF, EMR, size, flags)
  * **Leads table** with columns & driver pills
  * Right **Narrative rail** (two-liner builder + evidence links)

**Acceptance**

* “Two clicks to value”: filter + export works.
* Performance smooth with server-paginated data.

### Milestone G — **Clinic Detail & Evidence**

* `/clinic/[id]` tabs:

  * Overview (facts + drivers + “Integration Path Hypothesis”)
  * Locations (list + map)
  * Evidence (cards with snippets/links)
  * Notes (with “Mark Contacted”)

**Acceptance**

* Each driver shows a **because** snippet; links open in new tab.
* Single-clinic export produces a clean CSV row.

### Milestone H — **Saved Views**

* `/views` to create & load JSON-serialized filters.
* Preload 3 “Charta-grade” views (BH-TX-ICF≥75, HH-Medicare-3+, PC-Multi-state-EMR Common).

**Acceptance**

* Views hydrate filters reliably; counts match.

---

## 6) Ops Track (Quality, Tasks, Evidence)

### Milestone I — **Research Tasks**

* `tasks` endpoint/UI element:

  * Add task (“verify_emr”, “dedupe_check”, “verify_segment”)
  * Resolve with `resolved_value`; update `features` + `evidence` optionally.

**Acceptance**

* At least one closed loop where task → feature updated → score recomputed.

### Milestone J — **Exports & CRM Handoff**

* `/exports` history page listing: filter JSON, row count, CSV link.
* CSV column contract matches **05_Workflow_Automation.md**.

**Acceptance**

* CSV imports into HubSpot/Sheets with no extra cleaning.

---

## 7) Testing & Validation

* **Data sanity**: unique `clinic_id`, non-null `state_code`, segments not empty.
* **Score sanity**: median ICF in expected band; outliers reviewed.
* **API**: contract tests for filters, pagination, export.
* **UI**: a11y (focus rings, contrast), responsiveness, loading states.
* **E2E smoke**: seed filter → open clinic → copy narrative → export CSV.

---

## 8) Security, Compliance, Ethics

* Public sources only; respect robots.txt and rate limits.
* Store `source_url`, `first_seen`, `last_seen`, `license` where applicable.
* No PHI; only org-level and public role-level info.
* Provide a visible **Attribution** note in About modal.

---

## 9) Risks & Mitigations

| Risk                | Mitigation                                                                  |
| ------------------- | --------------------------------------------------------------------------- |
| Sparse EMR signals  | Multiple weak signals + confidence; add task queue; keep “unknown” graceful |
| Dedupe errors       | Deterministic composite keys + collision review list                        |
| Rate limits         | Caching, backoff; prioritize bulk/open datasets                             |
| Overfitting scoring | Versioned weights; check against outcomes once outreach starts              |
| UI performance      | Server-side pagination; debounce filters; lightweight row rendering         |

---

## 10) Deliverables & “Done” Criteria (MVP)

* **Dataset**: ≥3,000 deduped clinics across target segments with features and **ICF v1**.
* **Explainability**: every top driver has at least one **evidence link/snippet**.
* **Dashboard**: filters, table, KPI header, narrative rail, clinic detail with evidence.
* **Exports**: CSV with narrative snippet; import-ready for CRM.
* **Ops**: research task loop demonstrated.
* **Demo**: 5-minute click-through showing **value math**, **drivers**, and **export**.

---

## 11) Stretch Enhancements (post-MVP)

* **State denial heat map** overlay on Leads.
* **Score A/B** toggle (Denial-first vs Growth-first).
* **EMR normalization service** (string → canonical vendor + confidence).
* **Simple ML assist** to rank drivers (learning from won/lost labels).
* **Multi-user notes & team views** if you demo to Charta’s GTM team.

---

## 12) What makes this “beyond ChatGPT + Cursor”

* Real **entity resolution** and **evidence-backed** scoring (not just scraped lists).
* **Charta-specific math** (pre-bill focus, denial pressure, EMR friction) that maps to their GTM.
* **Immediate pipeline utility** (narratives + CSV handoff) with an ops loop for learning.

This plan is ready to execute in Cursor straight away. If you want, I can generate the **shadcn/Tailwind tokens file** and a **FastAPI skeleton** next so you can paste and run.
