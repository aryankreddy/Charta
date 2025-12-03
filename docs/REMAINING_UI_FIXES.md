# REMAINING UI FIXES FOR CHARTA GTM FRONTEND
**Status**: Ready for Implementation
**Priority**: Critical for deployment

---

## COMPLETED ✅
1. Changed "top 2,500" to "top 5,000" in ClinicDrawer.tsx:886
2. Fixed duplicate bonus points in Strategic Fit tooltip (ScoreBreakdown.tsx:148-153)
3. Updated denial prevention tooltip with "70% of denials prevented" stat
4. Removed advertising tone from strategic brief
5. Fixed all "Segment B/C/D/E" references to descriptive labels

---

## REMAINING CRITICAL FIXES

### 1. HIGH VOLUME TAG - SAGE/MOSSY GREEN COLOR
**File**: `web/components/ClinicDrawer.tsx`
**Line**: 196
**Current**:
```typescript
{clinic.score >= 90 ? 'High Volume' : clinic.tier}
```

**Issue**: The "High Volume" tag currently uses same green as tier tags (`getTierColor()` function).
**Fix Needed**: Change to sage/mossy green tone.

**Solution**:
```typescript
// Around line 89-94, update getTierColor function:
const getTierColor = (tier: string, score: number) => {
  if (score >= 90) return 'bg-emerald-700/90 text-white border-2 border-emerald-800'; // Sage/mossy green with bold border
  if (tier === 'Tier 1') return 'bg-brand-600 text-white';
  if (tier === 'Tier 2') return 'bg-brand-500 text-white';
  return 'bg-brand-700 text-white';
};
```

**Color Palette** (sage/mossy greens):
- `bg-emerald-700/90` - Dark sage green background
- `bg-emerald-800` - Darker mossy green for border
- Alternative: `bg-green-700/80`, `bg-teal-700/90`

---

### 2. PAIN POINT TAGS - RED STYLING
**Files**: Multiple (ClinicDrawer.tsx, DriverTag.tsx, update_frontend_data.py)

**Pain-related labels to style as red**:
- "Undercoding Pain"
- "Therapy Undercoding Pain"
- "Therapy Audit Risk"
- "Therapy Coding Risk"
- "Procedure Alignment Pain"
- "Severe Undercoding"
- "Margin Pressure"

**Solution** (in `update_frontend_data.py` where driver colors are set):
```python
# Around line 750-800 where drivers are generated
pain_keywords = ['Pain', 'Audit Risk', 'Undercoding', 'Margin Pressure']
driver_color = '#dc2626'  # Red-600 for pain points
driver_border = 'border-2 border-red-700'  # Bold red border

if any(keyword in driver_label for keyword in pain_keywords):
    driver_color = '#dc2626'  # Red
else:
    driver_color = '#059669'  # Default green
```

---

### 3. REMOVE EMOJIS FROM TAGS
**Files**: `scripts/update_frontend_data.py`

**Search for emojis in**:
- Driver labels (lines ~750-850)
- Strategic brief generation (lines ~300-500)
- Score reasoning strings

**Common emojis to remove**:
- 🏥 🔬 💰 📊 ⚠️ ✅ ❌ 🎯 📈 🔍

**Solution**:
```python
# Add at top of update_frontend_data.py
import re

def remove_emojis(text):
    """Remove all emojis from text"""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

# Apply to all driver labels and strategic brief text
```

---

### 4. DIM BACKGROUND COLOR
**Files**: `web/app/page.tsx`, `web/app/layout.tsx`

**Current**: `bg-brand-50` (bright beige/cream)
**Target**: Dimmer, less bright background

**Solution** (in page.tsx lines 107, 117):
```typescript
// BEFORE:
<div className="min-h-screen bg-brand-50 ...">

// AFTER:
<div className="min-h-screen bg-brand-100/50 ...">
// OR
<div className="min-h-screen bg-gray-50/80 ...">
// OR
<div className="min-h-screen bg-stone-50 ...">
```

**Test options**:
- `bg-brand-100/50` - 50% opacity brand color
- `bg-gray-50/80` - Slightly gray
- `bg-stone-50` - Warmer gray tone

---

### 5. DUPLICATE STATE DISPLAY
**File**: `web/components/ClinicDrawer.tsx`
**Need to locate**: Lines ~230-280 (clinic name/location section)

**Issue**: State appears twice - once in "segment · state" line, once below

**Search for**:
```typescript
{clinic.segment} · {clinic.state}
```
AND separately:
```typescript
<div>{clinic.state}</div>
```

**Fix**: Remove the standalone state line, keep only "segment · state" format.

---

### 6. DROPDOWN FILTER OPTIMIZATION
**File**: `web/app/page.tsx`

**Current filters** (lines 14-16):
- TIERS: All Tiers, Tier 1, Tier 2, Tier 3
- DATA_STATUS: All Data, Verified Only
- TRACKS: All Tracks, Ambulatory, Behavioral, Post-Acute

**Issue**: Some filters may show no results for top 5,000 clinics.

**Solution**: Test which filters return 0 results and either:
1. Remove them from dropdown if they're not in top 5k
2. Keep them but show count: "Post-Acute (0)"

**Command to test**:
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('data/curated/clinics_scored_final.csv').head(5000)
print('Track Distribution:')
print(df['scoring_track'].value_counts())
print('\nTier Distribution:')
print(df['icp_tier'].value_counts())
print('\nSegment Distribution (top 10):')
print(df['segment_label'].value_counts().head(10))
"
```

---

### 7. TAG BORDER STYLING
**Global Change**: Make all tag borders bolder

**Files**: ClinicDrawer.tsx, ScoreBreakdown.tsx, ClinicCard.tsx

**Find all**:
```typescript
border border-brand-200
```

**Replace with**:
```typescript
border-2 border-brand-300
```

This gives tags more visual weight and definition.

---

## TESTING CHECKLIST

After implementing fixes:

1. ✅ Run `python3 scripts/update_frontend_data.py`
2. ✅ Check web UI:
   - High Volume tag is sage/mossy green
   - Pain tags are red with red text
   - No emojis visible
   - Background is dimmer
   - State not duplicated
   - Filters show accurate counts
   - Borders are bolder
3. ✅ Test tooltips still work
4. ✅ Test drawer scrolling
5. ✅ Test on different screen sizes

---

## COLOR REFERENCE

**Sage/Mossy Green Palette**:
```css
/* Tailwind classes to use */
bg-emerald-700/90   /* Main sage background */
bg-emerald-800      /* Border/accent */
bg-green-700/80     /* Alternative darker */
bg-teal-700/90      /* Alternative cooler */
text-emerald-50     /* Light text on dark bg */
```

**Pain/Alert Red Palette**:
```css
bg-red-600          /* #dc2626 - Main red */
bg-red-700          /* Border */
text-red-900        /* Dark text */
border-red-700      /* Border color */
```

**Dimmer Background Options**:
```css
bg-brand-100/50     /* Faded brand color */
bg-gray-50/80       /* Subtle gray */
bg-stone-50         /* Warm neutral */
```

---

## NEXT STEPS

1. Implement fixes 1-7 above
2. Run `python3 scripts/update_frontend_data.py`
3. Start dev server: `cd web && npm run dev`
4. Test all changes visually
5. Commit and deploy

---

**Estimated Time**: 1-2 hours for all remaining fixes
**Priority Order**: #1 (colors), #2 (pain tags), #3 (emojis), #5 (state), #4 (background), #6 (filters), #7 (borders)
