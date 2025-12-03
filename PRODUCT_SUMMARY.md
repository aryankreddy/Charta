# Charta GTM Intelligence Platform - Product Summary

**Version:** v11.0 (Segmented Scoring Tracks)  
**Status:** Production Ready  
**Date:** November 2025

---

## Executive Summary

The Charta GTM Intelligence Platform is a data-driven lead prioritization system that scores and ranks 1.4 million healthcare organizations using exclusively public federal data sources. The platform surfaces the top 5,000 highest-value prospects with transparent, explainable scoring methodology and complete data lineage.

**Core Value Proposition:** Transform healthcare GTM from intuition-based prospecting to data-driven prioritization using verified government datasets.

---

## What We Built

### Data Pipeline
- **Input:** Six federal data sources (CMS Medicare claims, NPPES provider registry, HRSA grant data, CMS MIPS quality scores, HRSA HPSA/MUA designations, OIG exclusion lists)
- **Processing:** 1.4 million organizations scored across three specialized tracks (Ambulatory, Behavioral Health, Post-Acute)
- **Output:** Top 5,000 leads ranked by ICP score with complete transparency documentation

### Scoring Engine
- **Segment-Aware Logic:** Different scoring methodologies for different care models
- **Track A (Ambulatory):** E&M undercoding and revenue leakage focus
- **Track B (Behavioral Health):** VBC readiness and therapy complexity focus
- **Track C (Post-Acute):** Margin pressure and financial sustainability focus

### Frontend Dashboard
- **Interactive Table:** Sortable, filterable, searchable lead database
- **Detail Drawer:** Comprehensive organization intelligence with full calculation transparency
- **Export Capabilities:** JSON, CSV, and clipboard export for sales enablement

---

## End Product

A production-ready web application that enables sales teams to:
1. **Prioritize leads** using data-driven ICP scores (0-100 scale)
2. **Understand why** each organization scores high through transparent calculation breakdowns
3. **Filter and segment** by tier, care model, data quality, and buying signals
4. **Access complete intelligence** including revenue opportunities, compliance risks, and contact information
5. **Export leads** directly to CRM or sales workflows

**Technical Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS  
**Data Sources:** 100% public federal databases (no purchased data, no web scraping)  
**Deployment:** Vercel-hosted web application

---

## Feature Catalog

### 1. Dashboard Table View

- Displays top 5,000 organizations ranked by ICP score in a sortable, paginated table
- Shows key metrics at a glance: organization name, location, tier, score, volume, estimated revenue lift, and primary buying signals
- Real-time search across organization names, NPIs, and state locations
- Responsive design with 50 leads per page and pagination controls

### 2. Multi-Dimensional Filtering System

- **Tier Filter:** Filter by priority level (Tier 1: 70+, Tier 2: 50-69, Tier 3: <50)
- **Segment Filter:** Filter by care model (FQHC, Behavioral Health, Primary Care, Hospital, Urgent Care, Other)
- **Track Filter:** Filter by scoring methodology (Ambulatory, Behavioral, Post-Acute)
- **Data Status Filter:** Filter by data quality (All Data, Verified Only)
- **Driver Tag Filter:** Filter by buying signals (SEVERE Undercoding, Therapy Undercoding, High Volume, ACO Participant, etc.)
- All filters work in combination to create precise lead segments

### 3. Search Functionality

- Full-text search across organization names, NPIs, and state codes
- Real-time filtering as user types
- Case-insensitive matching with partial string support
- Automatically resets pagination when search criteria change

### 4. Clinic Detail Drawer

- Slide-out panel displaying comprehensive organization intelligence
- Organized into logical sections: Score Breakdown, Intelligence Brief, Evidence, Key Signals, Metrics, Contact
- All calculations explained with tooltips and data source attribution
- Export functionality for individual leads (JSON, CSV, clipboard)

### 5. ICP Score Breakdown

- Three-component scoring system displayed as progress bars: Pain (40 pts max), Fit (30 pts max), Strategy (30 pts max)
- Track-specific labels: "Economic Pain (Revenue Leakage)" for Ambulatory, "Economic Pain (Audit Risk)" for Behavioral, "Economic Pain (Margin Pressure)" for Post-Acute
- Hover tooltips explain what each component measures and why it matters
- Explicit scoring breakdown showing point allocation with reasoning strings

### 6. Strategic Intelligence Brief

- AI-generated summary explaining why the organization scores high
- Synthesizes pain points, strategic fit indicators, and opportunity size
- Written in analyst tone (not sales pitch) based on verified data signals
- Provides sales teams with talking points for first outreach

### 7. Total Opportunity Value

- Combined revenue opportunity from coding optimization and denial prevention
- Displays as large dollar amount with VERIFIED or PROJECTED badge
- VERIFIED means calculated from actual Medicare claims data
- PROJECTED means estimated using statistical models when complete data unavailable
- Always discloses calculation method and data source

### 8. Opportunity Breakdown

- **Coding Optimization (Revenue Growth):** Revenue recovery from improving coding accuracy
  - For VERIFIED: Calculated from actual undercoding gaps in Medicare claims
  - For PROJECTED: 5% industry benchmark applied conservatively
  - FQHC adjustment: Accounts for PPS revenue (only 20% of revenue benefits from coding optimization)
- **Denial Prevention (Revenue Defense):** Protected revenue from AI-powered pre-bill review
  - Industry benchmark: ~5% of revenue lost to preventable denials
  - Represents revenue protected through improved documentation and compliance
  - Separate from coding optimization to show complete financial impact

### 9. E&M Coding Performance Analysis

- Visual bar chart showing Level 4/5 E&M visit percentage vs. 45% national benchmark
- Color-coded status: Red (underperforming/undercoding), Green (outperforming), Gray (at benchmark)
- Displays actual ratio (e.g., 28.5%) with comparison to benchmark
- Tooltip explains E&M coding levels and what the ratio means for revenue opportunity

### 10. Behavioral Health Audit Risk Analysis

- For behavioral health organizations, shows psych audit risk ratio instead of E&M undercoding
- Measures percentage of max-level psych codes (90837+) vs. total psych visits
- Risk categories: Severe (>75%), Elevated (50-75%), Normal (<50%)
- Tooltip explains audit risk patterns and compliance implications

### 11. MIPS Performance Analysis

- Displays CMS Merit-based Incentive Payment System quality score (0-100 scale)
- High scores (>80) indicate tech-ready infrastructure and good documentation
- Low scores (<50) indicate compliance gaps and improvement opportunities
- Included in Strategic Fit scoring with bonus points for exceptional or distressed performers

### 12. HPSA/MUA Designations

- Health Professional Shortage Area (HPSA) and Medically Underserved Area (MUA) flags
- Indicates complex patient population with high Medicaid/uninsured mix
- Often correlates with mission-driven organizations and compliance challenges
- Adds bonus points to Strategic Fit score (5 pts for HPSA or MUA designation)

### 13. Organization Metrics

- **Revenue:** Total annual revenue from Medicare claims, cost reports, or statistical estimates
- **Volume:** Patient visit count from HRSA UDS reports, Medicare beneficiary counts, or estimates
- **Volume Unit:** Displays as "patients" or "encounters" based on data source
- All metrics show data source on hover (FQHC Cost Reports, Hospital HCRIS, Medicare Claims, Estimated)

### 14. Contact Information

- **NPI:** 10-digit National Provider Identifier from NPPES database
- **Phone:** Business phone number from NPPES provider records (formatted as xxx-xxx-xxxx)
- **Address:** Primary practice location from NPPES (city, state)
- All contact data sourced from official CMS provider enumeration system

### 15. Key Signals / Driver Tags

- Visual badges showing top buying signals for each organization
- Examples: "🩸 SEVERE Undercoding", "💰 Therapy Undercoding", "🚨 Compliance/Audit Risk", "High Volume", "ACO Participant"
- Helps sales teams identify which pain point to lead with on discovery calls
- Filterable via Driver Tag filter in main dashboard

### 16. Data Gaps Transparency

- Yellow alert box showing missing or low-quality data when present
- Examples: "Missing margin data", "Unverified volume estimate", "No psych audit risk data"
- Reduces confidence score but doesn't disqualify the lead
- Demonstrates transparency about data limitations

### 17. Data Confidence Indicator

- Badge showing High/Medium/Low confidence based on data completeness
- High (70%+): Multiple verified sources (claims, revenue reports, volume data)
- Medium (40-69%): Partial data with some gaps
- Low (<40%): Limited data, more estimates used
- Tooltip explains confidence calculation methodology

### 18. Track-Specific Scoring Display

- Visual badge showing which scoring track applies: "AMBULATORY TRACK", "BEHAVIORAL HEALTH TRACK", "POST-ACUTE TRACK"
- Pain bar labels change based on track (Revenue Leakage vs. Audit Risk vs. Margin Pressure)
- Tooltips adapt to explain track-specific metrics and calculations
- Ensures users understand why different organizations are scored differently

### 19. Export Functionality

- **JSON Export:** Complete lead data in structured JSON format for API integration
- **CSV Export:** Formatted spreadsheet-ready data for bulk import to CRM systems
- **Clipboard Copy:** Quick copy-to-clipboard for pasting into emails or notes
- Toast notifications confirm successful export operations

### 20. Tier Information Tooltip

- Hover icon in header explains tier breakdown
- Tier 1 (70+): High priority, immediate outreach recommended
- Tier 2 (50-69): Qualified prospects, good fit profile
- Tier 3 (<50): Standard opportunities, lower priority
- Helps users understand prioritization framework

### 21. Revenue Lift Calculation Transparency

- VERIFIED badge: Revenue opportunity calculated from actual Medicare claims
  - Step-by-step explanation: Analyzed E&M coding patterns, compared to 45% benchmark, calculated gap × volume × reimbursement difference
- PROJECTED badge: Statistical estimate when complete claims data unavailable
  - Conservative 5% industry benchmark applied
  - Always disclosed clearly to maintain transparency

### 22. Undercoding Ratio Tooltip

- Explains E&M coding levels (Level 1-5) and what Level 4/5 represents
- National benchmark context (45% is typical for similar practices)
- Interpretation guide: Below 45% = undercoding opportunity, Above 45% = strong coding or potential audit risk
- Data source attribution (CMS Part B claims)

### 23. Psych Audit Risk Tooltip

- Explains behavioral health coding patterns and audit risk calculation
- Risk categories and what they mean for compliance exposure
- VBC readiness context: Low risk organizations are candidates for collaborative care models
- Data source attribution (CMS psych CPT codes: 90832-90837)

### 24. Score Reasoning Display

- Every score component shows explicit point allocation with reasoning
- Pain reasoning: "+35pts: Severe undercoding (0.25 ratio)"
- Fit reasoning: "+15pts: FQHC alignment", "+5pts: MIPS quality (85.2)"
- Strategy reasoning: "+12pts: Revenue $5.2M", "+15pts: High Volume - Verified volume 45,000 patients"
- Provides "math receipts" for every calculation

### 25. Pagination System

- 50 leads per page with Previous/Next navigation
- Shows current range: "Showing 1 to 50 of 2,306 results"
- Automatically resets to page 1 when filters change
- Disabled states for navigation buttons at boundaries

### 26. Real-Time Statistics

- Header displays Tier 1 lead count based on current filters
- Updates dynamically as filters change
- Provides immediate feedback on filter impact

### 27. Responsive Design

- Mobile-friendly layout with collapsible filters
- Table scrolls horizontally on smaller screens
- Drawer adapts to viewport size
- Touch-friendly interactions for tablet users

### 28. Loading States

- Animated loading indicator during initial data fetch
- "Accessing Intelligence Database..." message
- Prevents interaction until data is ready

### 29. Error Handling

- Graceful error messages if data fails to load
- Console logging for debugging
- User-friendly error states

### 30. Track Detection Logic

- Automatic track assignment based on segment, organization name, psych code volume, and risk patterns
- Behavioral Health: Detected via segment label, org name keywords (BEHAVIORAL, PSYCH, MENTAL, COUNSELING, THERAPY), psych codes >100, or psych risk ratio >0.10
- Post-Acute: Detected via HOME HEALTH, HHA, or SEGMENT F labels
- Ambulatory: Default track for all other organizations

---

## Data Quality Metrics

- **Total Organizations Scored:** 1,427,580
- **Top 5,000 Cutoff Score:** 66.5
- **Data Completeness:**
  - Undercoding ratio available: 91.3%
  - MIPS score available: 87.3%
  - Volume data available: 100%
  - Revenue data available: 100%
- **Track Distribution (Top 5,000):**
  - Ambulatory: 3,093 orgs (61.9%)
  - Behavioral: 1,876 orgs (37.5%)
  - Post-Acute: 31 orgs (0.6%)

---

## Technical Architecture

### Backend
- **Scoring Engine:** Python-based continuous scoring functions with logarithmic scaling
- **Data Pipeline:** Pandas-based ETL processing 1.4M+ records
- **Track Detection:** Multi-signal pattern matching (segment, name, codes, ratios)
- **Output:** CSV files with complete scoring breakdowns

### Frontend
- **Framework:** Next.js 16 with React 19
- **Language:** TypeScript for type safety
- **Styling:** Tailwind CSS with custom brand color palette (Sage Green)
- **State Management:** React hooks (useState, useMemo, useEffect)
- **Data Format:** JSON files served statically from `/public/data/`

### Data Sources
1. **CMS Medicare Claims (Part B):** Physician utilization, E&M coding patterns, psych CPT codes
2. **NPPES:** Provider demographics, contact information, taxonomy codes
3. **HRSA UDS:** FQHC patient volume, revenue, expense data
4. **CMS MIPS:** Quality performance scores, clinician counts
5. **HRSA HPSA/MUA:** Underserved area designations (county-level matching)
6. **OIG LEIE:** Exclusion and compliance flags

---

## Key Differentiators

1. **100% Public Data:** No purchased data, no web scraping, all official government sources
2. **Full Transparency:** Every score explained with explicit calculations and data sources
3. **Segment-Aware:** Different scoring logic for different care models (not one-size-fits-all)
4. **VERIFIED vs PROJECTED:** Clear distinction between calculated and estimated opportunities
5. **Track-Specific Metrics:** Behavioral health scored on VBC readiness, not E&M undercoding
6. **Complete Data Lineage:** Every metric shows where it came from and how it was calculated

---

## Use Cases

1. **Sales Prioritization:** Identify top-tier leads for immediate outreach
2. **Territory Planning:** Filter by state/segment to build territory lists
3. **Segment Analysis:** Understand which care models represent best opportunities
4. **Data-Driven Outreach:** Use intelligence briefs and pain signals for personalized messaging
5. **CRM Integration:** Export leads directly to HubSpot, Salesforce, or other systems
6. **Market Research:** Analyze coding patterns and compliance risks across segments

---

## Future Enhancements (Not Yet Implemented)

- HubSpot direct integration (export button placeholder exists)
- Bulk export of filtered results
- Saved filter presets
- Lead comparison tool
- Historical score tracking
- Custom scoring model configuration

---

**Document Version:** 1.0  
**Last Updated:** November 2025

