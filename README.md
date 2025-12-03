# FinalChartaTool

Data pipeline and APIs that power the Charta Clinic Intelligence UI.

## Project Structure

- `workers/` — ingestion, enrichment, and scoring jobs
- `data/` — raw, staging, and curated outputs
- `api/` — FastAPI service serving /clinics endpoints
- `web/` — Next.js frontend (see `web/README.md` for UI instructions)

## Setup (macOS)

Install dependencies:
```bash
pip3 install -r requirements.txt
```

Note: On macOS, use `python3` and `pip3` (not `python`/`pip`).

## Data Pipeline

```bash
# 1) Ingest APIs & local files into curated staging
python3 -m workers.ingest_api

# 2) OIG LEIE compliance enrichment (optional, but recommended)
# Downloads OIG exclusion list and matches against clinic NPIs/names
# LEIE data refreshed monthly; run to update compliance flags
python3 -m workers.enrich_oig_leie

# 3) Feature engineering (joins from staging to unified clinics)
python3 -m workers.enrich_features

# 4) Scoring
python3 -m workers.score_icf

# 5) Run API
uvicorn api.app:app --reload --port 8000

# 6) Run UI (from /web)
cd web
npm run dev
```

### OIG LEIE Compliance Data

The OIG LEIE (List of Excluded Individuals/Entities) enrichment step flags clinics that appear on the federal exclusion list, which is a strong compliance risk signal.

- **Data source**: Public OIG exclusion list (https://oig.hhs.gov/exclusions/)
- **Update frequency**: Monthly (OIG updates the list monthly)
- **Matching**: Exact NPI matches + fuzzy name matching (85% threshold)
- **Output**: `data/curated/staging/oig_leie_matches.csv` with matched clinics
- **Usage**: Flags are merged into `clinics_seed.csv` as `oig_leie_flag` and `oig_exclusion_type`
- **Scoring impact**: Clinics with `oig_leie_flag=TRUE` get maximum compliance_exposure score (2.0)

To refresh LEIE data:
```bash
python3 -m workers.enrich_oig_leie
```

The script caches the downloaded LEIE CSV for 30 days to avoid unnecessary downloads.

## Smoke Test

After running the three pipeline commands, execute:

```bash
python3 scripts/dev_smoke.py
```

It verifies curated files exist and checks the REST API contracts.
