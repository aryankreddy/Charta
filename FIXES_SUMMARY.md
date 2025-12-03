# Fixes Summary - November 16, 2025

## Issues Addressed

### 1. ✅ Statistics Mismatch Between Breakdown and Detailed View

**Problem**: The drawer view in `TargetsView.tsx` was showing old ICF scores (`structural_fit_score`, `propensity_score`) and ICF "drivers" that didn't match the ICP scoring model.

**Solution**: 
- Completely replaced the drawer content to show ICP score breakdown instead of ICF drivers
- Now displays all 6 ICP category scores:
  - Fit Score (0-20)
  - Pain Score (0-20)
  - Compliance Risk (0-10)
  - Propensity to Buy (0-10)
  - Operational Scale (0-20)
  - Strategic Segment (0-20)
- Each category score includes:
  - Progress bar visualization
  - Hover tooltip with detailed explanation (using `ICPScoreTooltip`)
  - Max score indicator
- Removed old ICF filter options (Min Fit, Min Propensity) since they don't map to the new ICP system
- Updated subtitle to show ICP tier label instead of ICF scores

**Files Modified**:
- `/Users/nageshkothacheruvu/FinalChartaTool/web/components/targets/TargetsView.tsx`
  - Removed unused imports: `AXIS_ORDER`, `buildDriverInsights`, `buildOpeningAngle`, `AxisKey`
  - Removed `insights` from `EnrichedClinic` type
  - Removed old ICF driver display logic
  - Replaced `DrawerContent` with ICP-focused breakdown
  - Removed `minFit` and `minPropensity` filters and state
  - Removed Min Fit and Min Propensity filter UI elements

### 2. ⚠️ Clinic Website Links

**Problem**: The "Open ↗" link currently creates a Google search instead of linking directly to clinic websites.

**Root Cause**: Our current data pipeline doesn't include website URLs. The schema documentation mentions a `website` field, but it's not populated in the actual `clinics_scored.csv` or `icp_scores.csv` files.

**Current State**:
- NPI Registry data doesn't include website URLs
- HRSA data doesn't include website URLs
- No website URLs in curated data files

**Options**:

#### Option A: Keep Google Search (Current - No Changes Needed)
- Link remains as: `https://www.google.com/search?q={clinicName} {state} clinic`
- Pros: Works immediately, usually finds the right clinic
- Cons: Not a direct link, requires extra click

#### Option B: Add Website Data Enrichment (Requires Implementation)
If you have access to a data source with clinic websites, you can:
1. Add website enrichment to `workers/score_icp.py` or create a new enrichment script
2. Update the API to include `website_url` in the response
3. Update the frontend to use direct links when available, fallback to Google search

Example implementation:
```python
# In workers/enrich_websites.py (new file)
def enrich_website_urls(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich clinics with website URLs from external data source.
    This is a placeholder - implement based on your data source.
    """
    # Example: Load from external CSV
    # websites_df = pd.read_csv('data/external/clinic_websites.csv')
    # df = df.merge(websites_df[['clinic_id', 'website_url']], 
    #               on='clinic_id', how='left')
    return df
```

#### Option C: Remove the "Open" Link Entirely
- Simply remove the external link if it's not useful
- Focus on internal "Why this account" and "Campaign" actions

**Recommendation**: Keep Option A (Google search) for now. If you have a data source with clinic websites, I can help implement Option B.

## Testing

### What to Test:

1. **Targets List View**:
   - Open `/targets`
   - Click "Why this account" on any clinic
   - Verify drawer shows:
     - ICP total score with tier label
     - 6 category score cards with progress bars
     - Hover tooltips on each score showing detailed explanations
     - No old ICF "drivers"

2. **Filter Behavior**:
   - Verify Min Fit and Min Propensity filters are removed
   - Verify Min ICP filter still works
   - Verify Tier and Segment (GTM) filters still work

3. **Score Consistency**:
   - Verify scores in table match scores in drawer
   - Verify scores in drawer match scores in detail view
   - All should show ICP scores (0-100), not ICF scores (0-10)

### Expected Behavior:

**Before**:
```
Drawer shows:
- Fit: 7.5/10 (ICF structural_fit_score)
- Propensity: 6.2/10 (ICF propensity_score)
- Old ICF drivers (segment_fit, scale_velocity, etc.)
```

**After**:
```
Drawer shows:
- Overall ICP: 68/100
- Tier: Tier 2 - Qualified
- Fit Score: 18/20 [with tooltip]
- Pain Score: 12/20 [with tooltip]
- Compliance Risk: 7/10 [with tooltip]
- Propensity to Buy: 6/10 [with tooltip]
- Operational Scale: 15/20 [with tooltip]
- Strategic Segment: 10/20 [with tooltip]
```

## Files Changed

### Modified (1 file):
- `web/components/targets/TargetsView.tsx` (~200 lines changed)
  - Removed ICF driver logic
  - Added ICP breakdown UI
  - Removed old filter options
  - Cleaned up unused imports

### No Changes Needed (Website Links):
- Current Google search behavior maintained
- No data pipeline changes required until website data source is available

## Next Steps

1. **Test the Changes**:
   ```bash
   cd web
   npm run dev
   ```
   Navigate to http://localhost:3000/targets and test drawer functionality

2. **Optional - Add Website Data**:
   If you want to add direct clinic website links:
   - Identify your data source for clinic websites
   - Let me know and I can implement the enrichment pipeline
   - Or provide a CSV with `clinic_id` and `website_url` columns

## Summary

✅ **Fixed**: Statistics mismatch - drawer now shows correct ICP breakdown matching the scoring model
✅ **Clarified**: Website links - currently using Google search (no website data available)
✅ **Improved**: Removed confusing old ICF filters that didn't map to new ICP system
✅ **Consistent**: All views now show ICP scores consistently (table, drawer, detail view)

Status: **COMPLETE** (except optional website enrichment)


