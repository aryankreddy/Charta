02_DataSources.md — Public Data Inputs & Extraction Plan

Goal: enumerate feasible, high-signal public sources, what we’ll pull from each, how we’ll extract it, and how each source maps to the ICF scoring axes. Priority favors bulk/open datasets and lightweight, robots-friendly scraping that a single builder can ship.

0) Sourcing Strategy (TL;DR)

Tier 1 (Bulk/Open) — fastest path to national coverage; forms the backbone.

Tier 2 (Semi-Structured Web) — adds rich fit signals (EMR, hiring, scale).

Tier 3 (Proxies/Context) — fuels Denial Pressure, ROI readiness, narratives.

Each source entry includes: What we get, How to ingest, Maps to scores, Difficulty, Notes/ethics.

1) Priority Tiers
Tier	Category	Why It Matters	Build Effort
1	CMS/NPPES/HRSA bulk data	National coverage, clean identifiers (NPI), specialties, locations	Low–Medium
1	State Medicaid provider rosters	Payer participation flags by state	Medium
2	Org sites & Careers	EMR hints, RCM maturity, growth signals	Medium
2	Conference exhibitor lists	Warm ICP clusters by specialty/size	Low
2	ACO/MSSP participant lists	Value-based care & compliance orientation	Low
3	Directories/Reviews (Yelp/Healthgrades)	Presence & scale proxies	Medium (API limits)
3	News/press & job boards	Denial pressure, ROI narratives	Medium
2) Source Catalog (by Phase)
A) Tier 1 — Bulk/Open Backbone

NPPES / NPI Registry (Org + Individual)

What we get: Organization legal/brand names, addresses, phones, taxonomy (specialty), enumerations of clinician NPIs linked to an org via practice location; decent dedupe keys.

Ingest: Download bulk files (monthly), parse to /data/raw/npi, normalize; link individuals→orgs by addresses/phones.

Maps to scores: Segment Fit, Scale & Velocity (clinician count proxy), Coding Complexity (taxonomy).

Difficulty: Low.

Notes: Use as primary entity spine; keep both org + member records.

CMS Care Compare / Provider Data APIs (where applicable to outpatient)

What we get: Facility/clinic identifiers, locations, sometimes quality indicators by setting (e.g., home health).

Ingest: API/CSV pulls; join on name/address to NPI spine.

Maps to scores: Segment Fit, Scale, ROI Readiness (quality programs).

Difficulty: Low–Medium (joins).

CMS PECOS / Medicare Participation Flags (public enrollment extracts)

What we get: Medicare participation status by org/clinician.

Ingest: CSV where available; otherwise state-level extracts.

Maps to scores: Payer flags → boosts ROI Readiness, Denial Pressure baseline.

Difficulty: Medium (matching).

HRSA Health Center Program / FQHC Lists

What we get: Federally Qualified Health Centers and look-alikes (names, addresses, sites).

Ingest: CSV/API; join to NPI.

Maps to scores: Segment Fit (primary care), Scale, ROI Readiness (margin pressure).

Difficulty: Low.

Home Health Compare / OASIS Facility Lists

What we get: Home health orgs, locations, sometimes volume/quality meta.

Ingest: CSV/API; join to NPI.

Maps to scores: Segment Fit (home health), Scale, Coding Complexity.

Difficulty: Low–Medium.

State Medicaid Enrolled Provider Rosters (per state; CSV/PDF)

What we get: Medicaid participation at provider/organization level.

Ingest: Scripted downloads; PDF→table when needed; store state_code flags.

Maps to scores: Payer flags → Denial Pressure, ROI Readiness.

Difficulty: Medium (heterogeneous formats).

ACO/MSSP Participant Lists (CMS)

What we get: Organizations participating in value-based programs.

Ingest: CSV; join to NPI.

Maps to scores: ROI Readiness (process maturity), Compliance orientation.

Difficulty: Low.

B) Tier 2 — Semi-Structured Web (High Signal Fit)

Organization Websites (About/Locations/Services pages)

What we get: Locations, service lines, branches (true org vs franchise), care settings.

Ingest: Polite scraping (robots-aware), sitemap crawl; parse addresses, phones, services.

Maps to scores: Scale, Segment Fit, Coding Complexity (service diversity).

Difficulty: Medium (varied HTML).

Careers/Jobs Pages (on-site or ATS like Greenhouse/Lever/Workday)

What we get: EMR/RCM/clearinghouse mentions in job reqs; denials, compliance, coding roles; hiring velocity.

Ingest: Targeted crawl of /careers, /jobs, ATS feeds; extract keywords (athenahealth, Epic, eClinicalWorks, NextGen, AdvancedMD, DrChrono, Waystar, Availity, Change Healthcare, TriZetto, 837/835).

Maps to scores: EMR Friction, Coding Complexity, Denial Pressure, ROI Readiness.

Difficulty: Medium.

Notes: Only public pages; no login; store evidence snippets.

Conference Exhibitor Lists (HLTH, Becker’s, NAACOS, state MGMA)

What we get: Clinic groups who invest in ops tooling; often cluster by segment/size.

Ingest: HTML/CSV lists; normalize names; join to NPI.

Maps to scores: ROI Readiness, Scale, warm outreach clusters.

Difficulty: Low.

ONC Certified Health IT Product List (CHPL) & Vendor Resources

What we get: EMR vendor taxonomy; sometimes public customer showcases.

Ingest: Use for EMR vocabulary/normalization, not direct org mapping (CHPL isn’t a who-uses-what directory).

Maps to scores: Improves EMR normalization; indirect input to EMR Friction.

Difficulty: Low.

State Licensing Boards / Business Registries

What we get: Additional org addresses, DBA/aliases, status.

Ingest: CSV/HTML; name resolution to reduce dupes.

Maps to scores: Entity quality, Scale (site counts).

Difficulty: Medium (varied access).

C) Tier 3 — Proxies & Context

Yelp / Google Places / Healthgrades (presence & review counts)

What we get: Public listings, review/ratings volume (scale proxy), categories (urgent care, BH).

Ingest: Prefer Google Places API (cleaner, rate-limited); store review_count only.

Maps to scores: Scale, Segment Fit (category).

Difficulty: Medium (API quotas).

Notes: Respect terms; no scraping behind auth; store place_ids for dedupe.

Press/News (Clinic/Regional)

What we get: Denials headlines, payer disputes, margin pressure narratives.

Ingest: Lightweight news search per state/clinic name; extract title/date/source; store state-level denial heuristics first.

Maps to scores: Denial Pressure, ROI Readiness.

Difficulty: Medium.

Notes: Use state-level priors initially to avoid noisy per-clinic news crawl.

Payer Directories (UHC/BCBS/etc.)

What we get: In-network indicators (but often gated/captcha).

Ingest: De-prioritize for MVP (access & ToS).

Maps to scores: Would improve Payer flags later.

Difficulty: High (skip for v1).

3) Field Map → Scoring Axes
Field (example)	Source(s)	Score Axis
segments[] from taxonomy/categories	NPI, Yelp/Places, Org sites	Segment Fit
num_clinicians_proxy	NPI org→member linking	Scale & Velocity
num_locations	Org sites, HRSA, Care Compare	Scale & Velocity
emr_vendor (hint)	Careers pages, vendor PDFs	EMR Friction
rcm/clearinghouse hints	Careers pages	EMR Friction, Denial Pressure
coding/RCM hiring	Careers pages	Coding Complexity, ROI Readiness
medicare/medicaid flags	PECOS, State rosters	Payer flags, Denial Pressure
review_count	Places/Healthgrades	Scale proxy
aco_flag	CMS ACO lists	ROI Readiness
state_denial_prior	News/state signals	Denial Pressure
services[] breadth	Org sites	Coding Complexity
4) Extraction Plan (Scripts & Outputs)

Workers (Python)

ingest_npi.py → npi_org.parquet, npi_members.parquet

ingest_cms_carecompare.py → care_compare.parquet

ingest_cms_pecos.py → pecos_medicare_flags.parquet

ingest_hrsa_fqhc.py → hrsa_fqhc_sites.parquet

ingest_state_medicaid.py → medicaid_{state}.parquet

ingest_conferences.py → exhibitors.parquet

scrape_org_sites.py → org_locations.parquet, services.parquet

scrape_careers.py → careers_signals.parquet (emr/rcm keywords + snippets)

ingest_places.py → places_signal.parquet (place_id, review_count, category)

ingest_news_state.py → state_denial_priors.parquet (light heuristic)

Normalization

normalize_entities.py → clinics.parquet (resolved), locations.parquet

enrich_features.py → feature columns (segment, scale, emr_hints, payer flags…)

score_icf.py → add scores + top driver explanations with evidence links

Data Contracts

Every dataset has: source_name, source_url, first_seen, last_seen, evidence_snippet?.

5) Feasibility & Ethics

Public only: No logins, no paywalled directories, no PHI.

robots.txt aware: throttle, cache, polite headers.

Attribution: store source URLs; enable spot-checks.

Confidence: each signal gets confidence (high/med/low); ambiguous EMR → “unknown” + task queue.

6) MVP Scope (What We’ll Actually Pull First)

Week 1–2 (Backbone + high-signal web):

NPI (org + member linkage)

HRSA FQHC + Home Health lists

CMS PECOS flags (where straightforward)

Organization sites (locations/services)

Careers pages (EMR/RCM/coding/denials keywords)

Conference exhibitors (HLTH/Becker’s one recent year)

Google Places (review_count) for a single pilot state (TX) to validate proxy

Result: ≥3,000 deduped clinics across Primary Care, BH, Home Health, Urgent with: segment, state, scale proxy, payer flags, at least 25–40% EMR hints, and ICF v1.

7) Charta-Specific Keyword Packs (for Careers Parsing)

EMR vendors: Epic, Cerner, athenahealth, eClinicalWorks, NextGen, Allscripts/Veradigm, AdvancedMD, DrChrono, Practice Fusion, Kareo, ModMed, Elation, Office Ally.

Clearinghouse/RCM: Waystar, Availity, Change Healthcare, TriZetto/Facets, 837/835, X12, remittance, denial management, prior auth.

Compliance/Quality: LCD/NCD, medical necessity, pre-bill review, audit, coder, CDI, HCC, RAF.

Signals of pressure: denial rates, appeals backlog, audit backlog, RAC, MAC, payer takebacks.

(Keep in /config/keywords.yaml so non-devs can tune.)

8) Data Quality & Dedupe Rules (Entity Resolution)

Primary keys: (normalized_name, phone, address) + NPI where available.

Fuzzy thresholding with manual override queue for colliding names.

Branch logic: if brand name repeats across distinct cities/phones → treat as single org with multi-locations.

9) Acceptance Criteria (for this doc’s scope)

Clear, actionable source list with extraction steps per source.

Mapped fields → ICF axes so scoring is explainable.

MVP pull list small enough to ship in ≤ 2 weeks of part-time work.

Ethical/robots-aware plan with evidence storage.

10) What Makes This Beyond “ChatGPT + Scraper”

National backbone via bulk datasets (not one-off scraping).

Explainable, Charta-specific fit (pre-bill, denial, EMR friction) with stored evidence.

Operational loops (task queue, versioned scoring) built into sourcing.

Segment presets & saved views ready for GTM handoff.