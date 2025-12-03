# Network-Level ICP Scoring System

## Overview

The Network-Level ICP Scoring system identifies clinic networks (groups of clinics operating under the same brand/organization) and calculates aggregated ICP scores at the network level. This enables sales teams to target large healthcare organizations strategically.

---

## Key Features

### 1. **Network Identification**
- **Name Normalization**: Removes legal suffixes (Inc., LLC, Corp., etc.), punctuation, and standardizes formatting
- **Precision-Focused Grouping**: Only groups clinics with identical normalized names
- **Multi-Clinic Validation**: Requires either:
  - Multi-state operations (2+ states), OR
  - Single-state with 3+ clinic locations
- **Avoids False Positives**: Conservative approach prevents accidental grouping of unrelated organizations

### 2. **Network-Level Aggregation**
Each network receives:
- **Network ICP Score**: Weighted average of member clinics (weighted by site_count)
- **Tier Assignment**: Same logic as clinics (Tier 1: ≥70, Tier 2: 50-69, Tier 3: <50)
- **Segment Classification**: Dominant segment (A, B, or C) based on member clinics
- **Metadata**: Number of clinics, states covered, total NPIs, total sites
- **Anchor Clinic**: Highest-scoring clinic identified as primary contact point

### 3. **Clinic-Level Enrichment**
Each clinic retains individual ICP score PLUS:
- `network_id`: Unique identifier for parent network
- `network_name`: Normalized organization name
- `network_icp_score`: Aggregated network score
- `network_tier`: Network-level tier (1, 2, or 3)
- `network_tier_label`: Network tier description
- `is_network_anchor`: Boolean flag (True for highest-scoring clinic in network)
- `num_clinics`: Number of clinics in network

---

## How It Works

### Step 1: Name Normalization

```python
normalize_network_name("KANSAS UNIVERSITY PHYSICIANS INC")
# Returns: "kansas university physicians"
```

**Transformations:**
1. Convert to lowercase
2. Remove legal suffixes: Inc., LLC, Corp., Ltd., PA, PC, LP, Co.
3. Remove punctuation (except spaces and hyphens)
4. Collapse multiple spaces
5. Trim whitespace

### Step 2: Network Grouping

**Criteria for network formation:**
- **Minimum 2 clinics** with identical normalized names
- **AND** either:
  - **Multi-state**: Operates in 2+ states, OR
  - **Multi-site**: 3+ clinics in same state

**Example:**
```
Input:
  - CHRISTIANA CARE HEALTH SERVICES INC (DE)
  - CHRISTIANA CARE HEALTH SERVICES INC (PA)

Output:
  - Network ID: net_ebac5a35e974
  - Network Name: christiana care health services
  - Num Clinics: 2
  - States: DE, PA
```

### Step 3: Network ICP Calculation

**Category Scores** (weighted average):
- Weight by `site_count` if available, otherwise equal weights
- Calculate for each of 6 categories: Fit, Pain, Compliance, Propensity, Scale, Segment

**Network ICP Total**: Sum of 6 category scores (0-100)

**Tier Assignment**:
- Tier 1 (HOT): Network ICP ≥ 70
- Tier 2 (Qualified): 50 ≤ Network ICP < 70
- Tier 3 (Monitor): Network ICP < 50

### Step 4: Anchor Clinic Identification

- Selects clinic with **highest individual ICP score** within network
- Flags as `is_network_anchor = True`
- Use for initial outreach to network

---

## Output Files

### 1. `networks_icp.csv`
**One row per network** with aggregated scores

| Column | Description |
|--------|-------------|
| `network_id` | Unique identifier (e.g., `net_f2a9755b4311`) |
| `network_name` | Normalized organization name |
| `num_clinics` | Number of clinics in network |
| `num_states` | Number of states covered |
| `states_covered` | Comma-separated state codes |
| `network_icp_total_score` | Aggregated ICP score (0-100) |
| `network_icp_tier` | Tier (1, 2, or 3) |
| `network_icp_tier_label` | Tier description (e.g., "Tier 2 - Qualified") |
| `network_icp_segment` | Dominant segment (A, B, or C) |
| `network_icp_fit_score` | Aggregated Fit score (0-20) |
| `network_icp_pain_score` | Aggregated Pain score (0-20) |
| `network_icp_compliance_score` | Aggregated Compliance score (0-10) |
| `network_icp_propensity_score` | Aggregated Propensity score (0-10) |
| `network_icp_scale_score` | Aggregated Scale score (0-20) |
| `network_icp_segment_score` | Aggregated Segment score (0-20) |
| `total_npi_count` | Total NPIs across all clinics |
| `total_site_count` | Total sites across all clinics |
| `avg_clinic_icp_score` | Average individual clinic ICP score |
| `fqhc_clinics_count` | Number of FQHC-flagged clinics |
| `aco_clinics_count` | Number of ACO member clinics |
| `anchor_clinic_id` | Clinic ID of highest-scoring clinic |

### 2. `clinics_icp_with_networks.csv`
**One row per clinic** with network enrichment

All clinic-level ICP fields PLUS:
- `network_id`
- `network_name`
- `network_icp_score`
- `network_tier`
- `network_tier_label`
- `is_network_anchor`
- `num_clinics`

---

## API Endpoints

### **GET /icp/networks**

Get list of networks with filtering and sorting.

**Query Parameters:**
- `tier` (string): Filter by tier (1, 2, 3, or comma-separated)
- `segment` (string): Filter by segment (A, B, or C)
- `min_clinics` (int): Minimum number of clinics in network
- `min_states` (int): Minimum number of states covered
- `min_score` (float): Minimum network ICP score
- `limit` (int): Max results (default: 100)
- `sort_by` (string): Field to sort by (default: `network_icp_total_score`)
- `sort_dir` (string): Sort direction (`asc` or `desc`, default: `desc`)

**Example Requests:**
```bash
# Get top 20 Tier 2 networks
curl "http://localhost:8000/icp/networks?tier=2&limit=20"

# Get multi-state networks with 5+ clinics
curl "http://localhost:8000/icp/networks?min_clinics=5&min_states=2"

# Get Segment A networks with ICP ≥ 60
curl "http://localhost:8000/icp/networks?segment=A&min_score=60"
```

**Response:**
```json
{
  "total": 150,
  "returned": 20,
  "networks": [
    {
      "network_id": "net_ebac5a35e974",
      "network_name": "christiana care health services",
      "num_clinics": 12,
      "num_states": 3,
      "states_covered": "DE,PA,MD",
      "network_icp_total_score": 72.5,
      "network_icp_tier": 2,
      "network_icp_tier_label": "Tier 2 - Qualified",
      "network_icp_segment": "C",
      "network_icp_fit_score": 16.2,
      "network_icp_pain_score": 14.8,
      "network_icp_compliance_score": 7.5,
      "network_icp_propensity_score": 6.8,
      "network_icp_scale_score": 17.2,
      "network_icp_segment_score": 10.0,
      "total_npi_count": 850,
      "total_site_count": 28,
      "avg_clinic_icp_score": 68.3,
      "fqhc_clinics_count": 0,
      "aco_clinics_count": 8,
      "anchor_clinic_id": "christiana-care-health-services-inc-DE"
    }
  ],
  "filters_applied": {
    "tier": "2",
    "segment": null,
    "min_clinics": null,
    "min_states": null,
    "min_score": null
  }
}
```

### **GET /icp/networks/{network_id}**

Get detailed information about a specific network, including all member clinics.

**Example Request:**
```bash
curl "http://localhost:8000/icp/networks/net_ebac5a35e974"
```

**Response:**
```json
{
  "network_id": "net_ebac5a35e974",
  "network_name": "christiana care health services",
  "num_clinics": 12,
  "num_states": 3,
  "states_covered": "DE,PA,MD",
  "network_icp_total_score": 72.5,
  "network_icp_tier": 2,
  "network_icp_tier_label": "Tier 2 - Qualified",
  "network_icp_segment": "C",
  "clinics": [
    {
      "clinic_id": "christiana-care-health-services-inc-DE",
      "account_name": "CHRISTIANA CARE HEALTH SERVICES INC",
      "state_code": "DE",
      "icp_total_score": 74.2,
      "icp_tier_label": "Tier 2 - Qualified",
      "is_network_anchor": true
    },
    {
      "clinic_id": "christiana-care-health-services-inc-PA",
      "account_name": "CHRISTIANA CARE HEALTH SERVICES INC",
      "state_code": "PA",
      "icp_total_score": 68.5,
      "icp_tier_label": "Tier 2 - Qualified",
      "is_network_anchor": false
    }
  ]
}
```

---

## Usage

### Running Network Scoring

```bash
cd /Users/nageshkothacheruvu/FinalChartaTool

# Run full ICP scoring with network grouping
python3 workers/score_icp.py
```

**Output:**
- `data/curated/clinics_icp.csv` - Full clinic dataset (original format)
- `data/curated/icp_scores.csv` - Clinic scores summary (original format)
- `data/curated/networks_icp.csv` - **NEW**: Network-level scores
- `data/curated/clinics_icp_with_networks.csv` - **NEW**: Clinics with network enrichment

### Testing the API

```bash
# Start API server
uvicorn api.app:app --reload --port 8000

# Test networks endpoint
curl "http://localhost:8000/icp/networks?limit=10"

# Test network detail
curl "http://localhost:8000/icp/networks/net_ebac5a35e974"
```

---

## Sales Workflow: Network Targeting

### Step 1: Identify High-Value Networks
```bash
# Get Tier 1 and 2 networks with 5+ clinics
curl "http://localhost:8000/icp/networks?tier=1,2&min_clinics=5&limit=50"
```

### Step 2: Review Network Details
```bash
# Get full network profile
curl "http://localhost:8000/icp/networks/{network_id}"
```

**Use network data to:**
- Understand multi-state footprint
- See total provider count (NPIs)
- Identify anchor clinic for initial contact
- Review segment classification

### Step 3: Contact Anchor Clinic First
- Flag: `is_network_anchor = true`
- Rationale: Highest-scoring = most likely to have decision-making authority
- Strategy: Lead with network-wide value prop

### Step 4: Expand to Other Locations
- After successful pilot at anchor site
- Reference network ICP score in conversations
- Emphasize standardization across locations

---

## Algorithm Details

### Name Normalization Edge Cases

| Original Name | Normalized Name | Notes |
|---------------|-----------------|-------|
| `St. Mary's Hospital, Inc.` | `st marys hospital` | Punctuation removed |
| `JOHNS HOPKINS PHYSICIANS, LLC` | `johns hopkins physicians` | Legal suffix removed |
| `Children's Hospital of Philadelphia` | `childrens hospital of philadelphia` | Apostrophe handled |
| `UCSF Medical Center - Mission Bay` | `ucsf medical center  mission bay` | Hyphens removed |

### Grouping Precision

**Will NOT group** (false positive prevention):
- Same name, different state, only 1 clinic each → Too ambiguous
- Partial name matches (e.g., "Family Health" ≠ "Family Health Center")
- Similar but not identical names (requires exact match after normalization)

**Will group**:
- Exact normalized name match + multi-state
- Exact normalized name match + 3+ clinics in same state

### Weighted Aggregation

**If `site_count` available:**
```python
weight = clinic.site_count / sum(all_clinics.site_count)
network_score = sum(clinic_score * weight)
```

**If `site_count` missing:**
```python
weight = 1 / num_clinics  # Equal weighting
network_score = mean(clinic_scores)
```

---

## Performance Metrics

### Expected Results (based on 1.4M+ clinics)

- **Networks identified**: ~10,000-15,000 (0.7-1.0% of clinics)
- **Clinics in networks**: ~50,000-100,000 (3-7% of total)
- **Standalone clinics**: ~1.35M-1.40M (93-97% of total)
- **Average clinics per network**: 3-8
- **Largest networks**: 50-200+ clinics

### Processing Time

- **Full scoring with networks**: ~5-15 minutes (1.4M clinics)
- **Name normalization**: ~30 seconds
- **Network grouping**: ~1-2 minutes
- **Network scoring**: ~30 seconds
- **Clinic enrichment**: ~30 seconds

---

## Limitations and Future Enhancements

### Current Limitations

1. **Exact Name Match Required**: Won't catch variations like:
   - "University of Pennsylvania" vs "Penn Medicine"
   - "Johns Hopkins" vs "JHU Health System"

2. **No Ownership Data**: Grouping based solely on name, not corporate ownership

3. **No Parent-Subsidiary Detection**: Can't detect holding companies or complex org structures

### Future Enhancements

**Phase 2 (Fuzzy Matching):**
- Implement Levenshtein distance for near-matches
- Allow 85%+ similarity with manual review threshold

**Phase 3 (External Enrichment):**
- Integrate CMS Pecos Group Practice data
- Use NPI Taxonomy parent org field
- Add ACO network membership data

**Phase 4 (Manual Curation):**
- Admin UI for network merging/splitting
- Override mechanism for known networks
- Manual anchor clinic selection

---

## Troubleshooting

### Issue: No networks found

**Cause**: Data quality - all clinics have unique names

**Solution**:
1. Check `account_name` column has multi-location orgs
2. Review `normalized_network_name` distribution
3. Lower validation threshold (remove 3+ clinic requirement)

### Issue: Too many false positives

**Cause**: Generic names grouping unrelated clinics

**Solution**:
1. Add state validation (require multi-state or 5+ clinics)
2. Add manual exclusion list for common generic names
3. Review and add to name normalization rules

### Issue: Network scores don't match expectations

**Cause**: Weighting logic or aggregation method

**Solution**:
1. Check `site_count` data quality
2. Review weight calculation in `calculate_network_icp_scores()`
3. Consider using median instead of weighted average

---

## Related Documentation

- [ICP Scoring System](./ICP_SCORING_SYSTEM.md) - Clinic-level ICP scoring
- [API Documentation](../api/README.md) - Full API reference
- [Data Model](./DATA_MODEL.md) - Database schema

---

## Questions?

For questions or issues, contact the data team or open an issue in the repository.

**Last Updated**: November 2025
**Version**: 1.0.0

