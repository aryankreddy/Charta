# 03_Schema.md — Data Model, Types, Enums, and Contracts

> Purpose: a precise, implementation-ready schema for ingestion, enrichment, scoring, evidence, API, and UI. Optimized for **SQLite/Postgres**. All fields are **public, org-level** (no PHI).

---

## 0) Conventions

* **snake_case** column names.
* **UTC** timestamps (`*_at`) as ISO strings in API; `TIMESTAMPTZ` in DB.
* **IDs** are stable UUIDv4 generated on first resolution.
* **Enums** stored as `TEXT CHECK (...)` in SQLite; as `ENUM` in Postgres (or `TEXT` + check).

Primary entities: `clinics`, `locations`, `contacts`
Feature/edge entities: `features`, `signals`, `scores`, `evidence`, `sources`, `views`, `tasks`

---

## 1) Core Entities

### 1.1 `clinics`

Represents the deduped organization (account).

| Column                 | Type            | Required | Description                                                                                  |
| ---------------------- | --------------- | -------- | -------------------------------------------------------------------------------------------- |
| clinic_id              | UUID (PK)       | ✓        | Stable org id                                                                                |
| legal_name             | TEXT            | ✓        | Legal or registry name                                                                       |
| brand_name             | TEXT            |          | Public-facing brand                                                                          |
| aliases                | TEXT[]          |          | Known alternate names/DBAs                                                                   |
| npi_org                | TEXT            |          | NPI-2 (org-level) if present                                                                 |
| phone                  | TEXT            |          | Main public phone (E.164 if possible)                                                        |
| website                | TEXT            |          | Root domain ([https://example.com](https://example.com))                                     |
| hq_address             | JSON            |          | `{street, city, state, zip}` normalized                                                      |
| state_code             | TEXT            | ✓        | Two-letter USPS (from HQ)                                                                    |
| segments               | TEXT[] (enum)   | ✓        | Mapped: `primary_care`, `urgent_care`, `behavioral_health`, `home_health`, `other_specialty` |
| status                 | TEXT (enum)     | ✓        | `active`, `inactive`, `unknown`                                                              |
| num_locations          | INTEGER         |          | Derived count of child `locations`                                                           |
| num_clinicians_proxy   | INTEGER         |          | Count of linked NPIs (approx)                                                                |
| aco_flag               | BOOLEAN         |          | In ACO/MSSP                                                                                  |
| medicare_participating | BOOLEAN         |          | From PECOS                                                                                   |
| medicaid_states        | TEXT[]          |          | Two-letter codes                                                                             |
| emr_vendor             | TEXT (enum-ish) |          | Normalized value (see §5)                                                                    |
| rcm_vendor             | TEXT            |          | If detected                                                                                  |
| clearinghouse          | TEXT            |          | e.g., Waystar, Availity                                                                      |
| review_count           | INTEGER         |          | From Google Places/Healthgrades                                                              |
| created_at             | TIMESTAMPTZ     | ✓        | First seen                                                                                   |
| updated_at             | TIMESTAMPTZ     | ✓        | Last refresh                                                                                 |

**Indexes**

* `idx_clinics_state_seg` on `(state_code, segments)`
* `idx_clinics_name` on `brand_name`
* `idx_clinics_emr` on `emr_vendor`

---

### 1.2 `locations`

Child sites for a clinic.

| Column      | Type              | Required | Description                                      |
| ----------- | ----------------- | -------- | ------------------------------------------------ |
| location_id | UUID (PK)         | ✓        |                                                  |
| clinic_id   | UUID (FK clinics) | ✓        |                                                  |
| address     | JSON              | ✓        | `{street, city, state, zip}`                     |
| lat         | NUMERIC           |          | Optional geocode                                 |
| lng         | NUMERIC           |          | Optional geocode                                 |
| phone       | TEXT              |          | Site phone                                       |
| services    | TEXT[]            |          | Parsed from site (e.g., “wellness visit”, “CCM”) |
| hours       | JSON              |          | `{mon: "8-5", ...}`                              |
| place_id    | TEXT              |          | Google Places id                                 |
| created_at  | TIMESTAMPTZ       | ✓        |                                                  |
| updated_at  | TIMESTAMPTZ       | ✓        |                                                  |

Index: `idx_locations_clinic` on `(clinic_id)`

---

### 1.3 `contacts` (optional/public only)

Role-level contacts if explicitly public.

| Column       | Type               | Required | Description                     |
| ------------ | ------------------ | -------- | ------------------------------- |
| contact_id   | UUID (PK)          | ✓        |                                 |
| clinic_id    | UUID (FK)          | ✓        |                                 |
| name         | TEXT               |          | Publicly listed name            |
| title        | TEXT               |          | e.g., “Director, Revenue Cycle” |
| email        | TEXT               |          | Only if publicly posted         |
| linkedin_url | TEXT               |          | Public profile link             |
| evidence_id  | UUID (FK evidence) |          | Source                          |
| created_at   | TIMESTAMPTZ        | ✓        |                                 |
| updated_at   | TIMESTAMPTZ        | ✓        |                                 |

---

## 2) Feature & Signal Layer

### 2.1 `features`

Canonical single-row feature vector per clinic (flattened for scoring).

| Column                    | Type         | Required | Notes                    |
| ------------------------- | ------------ | -------- | ------------------------ |
| clinic_id                 | UUID (PK/FK) | ✓        |                          |
| segment_primary_care      | BOOLEAN      |          | one-hot                  |
| segment_urgent_care       | BOOLEAN      |          |                          |
| segment_behavioral_health | BOOLEAN      |          |                          |
| segment_home_health       | BOOLEAN      |          |                          |
| segment_other_specialty   | BOOLEAN      |          |                          |
| providers_count_proxy     | INTEGER      |          | from NPI linkage         |
| locations_count           | INTEGER      |          | from child count         |
| emr_vendor                | TEXT         |          | normalized               |
| emr_confidence            | TEXT (enum)  |          | `high`, `med`, `low`     |
| rcm_vendor                | TEXT         |          |                          |
| clearinghouse             | TEXT         |          |                          |
| has_coding_hiring         | BOOLEAN      |          | careers signal           |
| has_denial_mgmt_hiring    | BOOLEAN      |          | careers                  |
| mentions_prebill_audit    | BOOLEAN      |          | careers/site             |
| has_aco_flag              | BOOLEAN      |          |                          |
| medicare_participating    | BOOLEAN      |          |                          |
| medicaid_flag             | BOOLEAN      |          | any state true           |
| review_count              | INTEGER      |          |                          |
| services_breadth          | INTEGER      |          | count of unique services |
| state_denial_prior        | TEXT (enum)  |          | `low`,`med`,`high`       |
| last_feature_refresh      | TIMESTAMPTZ  | ✓        |                          |

---

### 2.2 `signals`

Tokenized detections (keyword → value) with provenance.

| Column      | Type               | Required | Description                                                                               |
| ----------- | ------------------ | -------- | ----------------------------------------------------------------------------------------- |
| signal_id   | UUID (PK)          | ✓        |                                                                                           |
| clinic_id   | UUID (FK)          | ✓        |                                                                                           |
| signal_type | TEXT (enum)        | ✓        | `emr_hint`, `rcm_hint`, `clearinghouse_hint`, `hiring_role`, `policy_term`, `service_tag` |
| key         | TEXT               | ✓        | e.g., `Epic`, `athenahealth`, `837`, `denial management`                                  |
| value       | TEXT               |          | optional payload                                                                          |
| confidence  | TEXT (enum)        | ✓        | `high`,`med`,`low`                                                                        |
| evidence_id | UUID (FK evidence) | ✓        | link to snippet/url                                                                       |
| first_seen  | TIMESTAMPTZ        | ✓        |                                                                                           |
| last_seen   | TIMESTAMPTZ        | ✓        |                                                                                           |

Index: `idx_signals_clinic_type` on `(clinic_id, signal_type)`

---

## 3) Scoring & Explainability

### 3.1 `scores`

Stores current and historical score runs.

| Column            | Type        | Required | Description                                                                |
| ----------------- | ----------- | -------- | -------------------------------------------------------------------------- |
| score_id          | UUID (PK)   | ✓        |                                                                            |
| clinic_id         | UUID (FK)   | ✓        |                                                                            |
| model_version     | TEXT        | ✓        | semantic version (e.g., `icf_v1.0`)                                        |
| icf_score         | INTEGER     | ✓        | 0–100                                                                      |
| segment_fit       | INTEGER     | ✓        | 0–25                                                                       |
| scale_velocity    | INTEGER     | ✓        | 0–20                                                                       |
| emr_friction      | INTEGER     | ✓        | 0–15 (inverted in calc)                                                    |
| coding_complexity | INTEGER     | ✓        | 0–15                                                                       |
| denial_pressure   | INTEGER     | ✓        | 0–15                                                                       |
| roi_readiness     | INTEGER     | ✓        | 0–10                                                                       |
| drivers           | JSON        | ✓        | top 3: `[{"name":"emr_friction","reason":"...","evidence_id":"..."}, ...]` |
| computed_at       | TIMESTAMPTZ | ✓        |                                                                            |
| is_current        | BOOLEAN     | ✓        | only one true per clinic                                                   |

Indexes:

* `idx_scores_current` on `(is_current DESC, icf_score DESC)`
* `idx_scores_clinic` on `(clinic_id)`

**Scoring config (YAML) reference (stored in `/config/scoring.yaml`):**

```yaml
model_version: icf_v1.0
weights:
  segment_fit: 25
  scale_velocity: 20
  emr_friction: 15
  coding_complexity: 15
  denial_pressure: 15
  roi_readiness: 10
rules:
  emr_friction:
    common_vendors: ["epic","athenahealth","ecw","nextgen","advancedmd","kareo","veradigm","modmed","elation"]
    score_common: 15
    score_unknown: 8
    score_exotic: 4
  denial_pressure:
    state_prior:
      high: 10
      med: 6
      low: 3
    hiring_denial_roles_bonus: 3
```

---

### 3.2 `evidence`

Atomic, attributable proofs that power explainability.

| Column      | Type              | Required | Description              |
| ----------- | ----------------- | -------- | ------------------------ |
| evidence_id | UUID (PK)         | ✓        |                          |
| clinic_id   | UUID (FK)         | ✓        |                          |
| source_id   | UUID (FK sources) | ✓        |                          |
| url         | TEXT              | ✓        | full URL                 |
| title       | TEXT              |          | page title               |
| snippet     | TEXT              | ✓        | 200–500 chars, HTML-safe |
| captured_at | TIMESTAMPTZ       | ✓        |                          |
| hash        | TEXT              | ✓        | content hash to dedupe   |

Index: `idx_evidence_clinic` on `(clinic_id)`

---

### 3.3 `sources`

Normalized description of a source.

| Column         | Type        | Required |                                           |
| -------------- | ----------- | -------- | ----------------------------------------- |
| source_id      | UUID (PK)   | ✓        |                                           |
| source_name    | TEXT        | ✓        | e.g., `npi_bulk`, `careers`, `places_api` |
| source_url     | TEXT        |          |                                           |
| license        | TEXT        |          |                                           |
| robots_policy  | TEXT        |          |                                           |
| last_pulled_at | TIMESTAMPTZ |          |                                           |

---

## 4) Ops & Workflow

### 4.1 `tasks`

Manual research/verification queue.

| Column         | Type        | Required | Description                                                       |
| -------------- | ----------- | -------- | ----------------------------------------------------------------- |
| task_id        | UUID (PK)   | ✓        |                                                                   |
| clinic_id      | UUID (FK)   | ✓        |                                                                   |
| task_type      | TEXT (enum) | ✓        | `verify_emr`, `verify_segment`, `dedupe_check`, `verify_location` |
| status         | TEXT (enum) | ✓        | `open`, `in_progress`, `done`, `won't_do`                         |
| note           | TEXT        |          | instructions or context                                           |
| created_at     | TIMESTAMPTZ | ✓        |                                                                   |
| updated_at     | TIMESTAMPTZ | ✓        |                                                                   |
| resolved_value | TEXT        |          | e.g., “athenahealth”                                              |
| resolver       | TEXT        |          | your initials                                                     |

Index: `idx_tasks_status` on `(status)`

---

### 4.2 `views` (Saved filters for GTM)

Simple saved queries for one-click GTM handoff.

| Column      | Type        | Required |                                                                                                |
| ----------- | ----------- | -------- | ---------------------------------------------------------------------------------------------- |
| view_id     | UUID (PK)   | ✓        |                                                                                                |
| name        | TEXT        | ✓        |                                                                                                |
| description | TEXT        |          |                                                                                                |
| query       | JSON        | ✓        | serialized filter, e.g., `{"segments":["behavioral_health"],"state_code":["TX"],"icf_min":70}` |
| created_at  | TIMESTAMPTZ | ✓        |                                                                                                |
| updated_at  | TIMESTAMPTZ | ✓        |                                                                                                |

---

## 5) Normalizations & Enums

### 5.1 `segments` enum (TEXT)

* `primary_care`
* `urgent_care`
* `behavioral_health`
* `home_health`
* `other_specialty`

### 5.2 `emr_vendor` normalization

Lowercased canonical set:

* `epic`, `cerner`, `athenahealth`, `eclinicalworks` (`ecw`), `nextgen`, `advancedmd`, `kareo`, `veradigm` (`allscripts`), `modmed`, `elation`, `drchrono`, `practice_fusion`, `office_ally`, `eclinicalworks`, `unknown`, `other`

`emr_confidence`: `high`, `med`, `low`

### 5.3 `state_denial_prior`

* `low`, `med`, `high` (state-level heuristic from simple news/agency indicators)

---

## 6) SQL DDL (SQLite/Postgres-friendly)

> Note: Adjust types for SQLite (`TEXT` for enums) as needed.

```sql
-- clinics
CREATE TABLE clinics (
  clinic_id UUID PRIMARY KEY,
  legal_name TEXT NOT NULL,
  brand_name TEXT,
  aliases TEXT[],
  npi_org TEXT,
  phone TEXT,
  website TEXT,
  hq_address JSONB,
  state_code TEXT NOT NULL,
  segments TEXT[] NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active','inactive','unknown')),
  num_locations INTEGER,
  num_clinicians_proxy INTEGER,
  aco_flag BOOLEAN,
  medicare_participating BOOLEAN,
  medicaid_states TEXT[],
  emr_vendor TEXT,
  rcm_vendor TEXT,
  clearinghouse TEXT,
  review_count INTEGER,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

-- locations
CREATE TABLE locations (
  location_id UUID PRIMARY KEY,
  clinic_id UUID REFERENCES clinics(clinic_id),
  address JSONB NOT NULL,
  lat NUMERIC,
  lng NUMERIC,
  phone TEXT,
  services TEXT[],
  hours JSONB,
  place_id TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

-- features
CREATE TABLE features (
  clinic_id UUID PRIMARY KEY REFERENCES clinics(clinic_id),
  segment_primary_care BOOLEAN,
  segment_urgent_care BOOLEAN,
  segment_behavioral_health BOOLEAN,
  segment_home_health BOOLEAN,
  segment_other_specialty BOOLEAN,
  providers_count_proxy INTEGER,
  locations_count INTEGER,
  emr_vendor TEXT,
  emr_confidence TEXT CHECK (emr_confidence IN ('high','med','low')),
  rcm_vendor TEXT,
  clearinghouse TEXT,
  has_coding_hiring BOOLEAN,
  has_denial_mgmt_hiring BOOLEAN,
  mentions_prebill_audit BOOLEAN,
  has_aco_flag BOOLEAN,
  medicare_participating BOOLEAN,
  medicaid_flag BOOLEAN,
  review_count INTEGER,
  services_breadth INTEGER,
  state_denial_prior TEXT CHECK (state_denial_prior IN ('low','med','high')),
  last_feature_refresh TIMESTAMPTZ NOT NULL
);

-- sources
CREATE TABLE sources (
  source_id UUID PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_url TEXT,
  license TEXT,
  robots_policy TEXT,
  last_pulled_at TIMESTAMPTZ
);

-- evidence
CREATE TABLE evidence (
  evidence_id UUID PRIMARY KEY,
  clinic_id UUID REFERENCES clinics(clinic_id),
  source_id UUID REFERENCES sources(source_id),
  url TEXT NOT NULL,
  title TEXT,
  snippet TEXT NOT NULL,
  captured_at TIMESTAMPTZ NOT NULL,
  hash TEXT NOT NULL
);

-- signals
CREATE TABLE signals (
  signal_id UUID PRIMARY KEY,
  clinic_id UUID REFERENCES clinics(clinic_id),
  signal_type TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT,
  confidence TEXT NOT NULL CHECK (confidence IN ('high','med','low')),
  evidence_id UUID REFERENCES evidence(evidence_id),
  first_seen TIMESTAMPTZ NOT NULL,
  last_seen TIMESTAMPTZ NOT NULL
);

-- scores
CREATE TABLE scores (
  score_id UUID PRIMARY KEY,
  clinic_id UUID REFERENCES clinics(clinic_id),
  model_version TEXT NOT NULL,
  icf_score INTEGER NOT NULL,
  segment_fit INTEGER NOT NULL,
  scale_velocity INTEGER NOT NULL,
  emr_friction INTEGER NOT NULL,
  coding_complexity INTEGER NOT NULL,
  denial_pressure INTEGER NOT NULL,
  roi_readiness INTEGER NOT NULL,
  drivers JSONB NOT NULL,
  computed_at TIMESTAMPTZ NOT NULL,
  is_current BOOLEAN NOT NULL
);

-- tasks
CREATE TABLE tasks (
  task_id UUID PRIMARY KEY,
  clinic_id UUID REFERENCES clinics(clinic_id),
  task_type TEXT NOT NULL,
  status TEXT NOT NULL,
  note TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  resolved_value TEXT,
  resolver TEXT
);

-- views
CREATE TABLE views (
  view_id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  query JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
```

---

## 7) API Contracts (FastAPI)

### `GET /clinics`

**Query params**: `segment[]`, `state[]`, `icf_min`, `emr[]`, `page`, `page_size`
**Response**

```json
{
  "items": [
    {
      "clinic_id": "uuid",
      "brand_name": "Family Care Center",
      "state_code": "TX",
      "segments": ["behavioral_health"],
      "num_locations": 5,
      "num_clinicians_proxy": 42,
      "emr_vendor": "athenahealth",
      "icf_score": 82,
      "top_drivers": [
        {"name":"denial_pressure","reason":"state prior=high + denial roles","evidence_id":"uuid"},
        {"name":"emr_friction","reason":"common EMR","evidence_id":"uuid"}
      ]
    }
  ],
  "total": 1234,
  "page": 1,
  "page_size": 50
}
```

### `GET /clinic/{clinic_id}`

Returns **clinic**, **locations**, **features**, **latest score**, and **evidence summaries**.

### `GET /export`

Accepts same filters as `/clinics`; returns CSV with:
`account_name, state, segments, emr_vendor, locations, providers_proxy, icf_score, note_snippet, evidence_urls`

---

## 8) Evidence & Explainability Rules

* Every **score driver** must reference at least one **evidence_id**.
* Each **signal** should map to one **evidence** (or more).
* UI must display **“because”** reasons with clickable sources.

---

## 9) Acceptance Criteria

* Schema supports **MVP ingestion** (NPI, HRSA, PECOS, org sites, careers, exhibitors, Places TX).
* **ICF** stored with **versioning** and **top-3 explainable drivers**.
* **Evidence-first**: no opaque score—every driver is traceable.
* **Saved views** serialize filters to JSON and rehydrate in UI.
* **Tasks** enable human-in-loop corrections for EMR/segment/dedupes.

---

## 10) What Makes This “Charta-Grade”

* Fields explicitly model **pre-bill, denial pressure, EMR friction**—not generic TAM.
* Schema bakes in **ops rigor** (evidence, sources, tasks, versioned scores).
* Outputs are **GTM-ready** (filters, exports, narratives) from day one.

