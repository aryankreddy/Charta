# 🎥 LOOM DEMO SCRIPT - COMPREHENSIVE DRAWER WALKTHROUGH

**Goal:** Show every element in the drawer and explain what it means, where it comes from, and how it's calculated.  
**Duration:** 2-3 minutes (detailed version) or 90 seconds (fast version)  
**Audience:** Sales team, prospects, investors

---

## 🎬 INTRO (10 seconds)

*[Dashboard visible]*

**SAY:**
- "This is Charta's GTM Intelligence Platform"
- "Built entirely from public government data sources"
- "1.4 million organizations scored, top 5,000 surfaced here"

---

## 📊 DATA SOURCES (15 seconds)

*[Still on dashboard, gesture broadly]*

**SAY:**
- "Six federal data sources merged together:"
  - "CMS Medicare claims (Part B physician utilization)"
  - "NPPES provider records (demographics and contact info)"
  - "HRSA grant data (FQHCs and health centers)"
  - "CMS MIPS quality scores"
  - "HRSA HPSA/MUA designations (underserved areas)"
  - "OIG exclusion lists"
- "No web scraping, no purchased data - all official government sources"

---

## 👁️ FRONTEND OVERVIEW (10 seconds)

*[Gesture to table]*

**SAY:**
- "Top 5,000 organizations ranked by ICP score (0-100 scale)"
- "Can filter by Tier (priority level), Segment (FQHC, Behavioral, etc.), Track (scoring methodology), and Data Status (VERIFIED vs PROJECTED)"
- "Right now showing [X] Tier 1 high-priority leads"

---

## 🔍 LEAD DEEP DIVE - COMPREHENSIVE DRAWER WALKTHROUGH (90-120 seconds)

*[Click on top FQHC lead with VERIFIED status]*

**SAY:** "Let me walk through every element in this lead profile - I'll explain what each thing means and where the data comes from."

---

### 1️⃣ TIER & CONFIDENCE BADGES (5s)

*[Point to badges at top right]*

**WHAT TO SAY:**
- "**Tier 1** means ICP score ≥ 70 (high priority)"
- "**High Confidence** means we have data from multiple verified sources"
- "Confidence score is calculated based on data completeness:"
  - "High (70%+) = multiple sources (claims, revenue reports, volume data)"
  - "Medium (40-69%) = partial data with some gaps"
  - "Low (<40%) = limited data, more estimates used"

**WHERE IT COMES FROM:**
- Tier: Calculated from ICP score (Pain + Fit + Strategy)
- Confidence: Automated based on which data fields are populated

---

### 2️⃣ STRATEGIC INTELLIGENCE BRIEF (10s)

*[Point to text box at top]*

**WHAT TO SAY:**
- "This is an **auto-generated summary** of WHY this lead scores high"
- "It's not a sales pitch - it's an analyst report"
- "Synthesizes key pain points, strategic fit indicators, and opportunity size"
- "Gives sales the talking points they need for first outreach"

**WHERE IT COMES FROM:**
- Generated from scoring logic and data signals
- Mentions specific metrics like undercoding ratio, volume scale, margin pressure
- Different summary for each track (Ambulatory vs Behavioral vs Post-Acute)

---

### 3️⃣ ESTIMATED REVENUE LIFT (15s)

*[Point to large dollar amount with VERIFIED or PROJECTED badge]*

**WHAT TO SAY:**

**"This is the revenue opportunity - how much they're leaving on the table."**

#### If VERIFIED Badge:
- "**VERIFIED means we calculated this from their actual Medicare claims data**"
- "Here's exactly how:"
  - "Step 1: Pull their CMS Part B claims (every E&M visit they billed)"
  - "Step 2: Calculate their Level 4/5 usage ratio (high-complexity codes)"
  - "Step 3: Compare to national benchmark (45% for most specialties)"
  - "Step 4: If they're at 25% when they should be at 45%, that's a 20-point gap"
  - "Step 5: Apply reimbursement rate differences ($150 vs $110 per visit) × volume"
- "Example: If they bill 10,000 E&M visits/year and undercode by 20%, that's 2,000 visits × $40 difference = $80K opportunity"

#### If PROJECTED Badge:
- "**PROJECTED means incomplete claims data - we're using statistical models**"
- "How we estimate:"
  - "We have their segment (FQHC, primary care, etc.)"
  - "We know their revenue scale from cost reports or estimates"
  - "We apply industry benchmark: 5% revenue lift opportunity"
  - "Conservative estimate for when we don't have complete claims"
- "We always disclose PROJECTED vs VERIFIED - transparency is key"

**WHERE IT COMES FROM:**
- VERIFIED: CMS Physician Utilization Public Use File (claims data)
- PROJECTED: Statistical model based on segment and revenue
- Lift Basis field shows the calculation method

---

### 4️⃣ UNDERCODING ANALYSIS (if present) (15s)

*[Scroll to Undercoding Analysis section]*

**WHAT TO SAY:**
- "This shows their **actual coding patterns vs. national benchmarks**"
- "Current Ratio: [X]% - this is the percentage of their E&M visits coded as Level 4 or 5"
- "Benchmark: 45% - this is the national average for similar practices"
- "If they're **below 45%, they're undercoding** - leaving money on the table"
- "If they're **above 45%, they're coding well** - potentially at risk of audit"

**WHAT THE BAR COLORS MEAN:**
- Red bar: Underperforming (undercoding, opportunity exists)
- Green bar: Outperforming (coding at/above benchmark)
- Gray bar: Benchmark comparison line

**WHERE IT COMES FROM:**
- CMS Part B claims data (Medicare Physician Utilization)
- Undercoding ratio = (Level 4 + Level 5 visits) / (Total E&M visits)
- National average calculated from 1M+ providers in CMS dataset

---

### 5️⃣ BEHAVIORAL HEALTH AUDIT RISK (if present) (12s)

*[Point to Psych Audit Risk section]*

**WHAT TO SAY:**
- "For behavioral health practices, we measure **audit risk instead of undercoding**"
- "Risk Ratio: [X]% - this is their max-level psych code usage"
- "We calculate: (90837+ codes) / (Total psych visits)"
- "**High ratio (>75%) = severe risk** - billing at dangerous intensity levels"
- "**Moderate ratio (25-50%) = normal complexity** - appropriate for therapy"
- "**Low ratio (<25%) = clean billing** - VBC-ready for collaborative care codes"

**WHERE IT COMES FROM:**
- CMS Part B claims data (psych CPT codes: 90832-90837)
- Compared to peer behavioral health practices
- High intensity = audit target OR high complexity patient mix

---

### 6️⃣ ICP SCORE BREAKDOWN (20s)

*[Scroll to Score Breakdown section, point to track badge]*

**WHAT TO SAY:**

**"Notice the track badge - this org is scored on the [AMBULATORY/BEHAVIORAL/POST-ACUTE] track."**

#### Track-Specific Explanation:

**If AMBULATORY Track:**
- "**Economic Pain (Revenue Leakage) - Max 40 pts**"
  - "Measures revenue recovery opportunity from E&M undercoding"
  - "Calculated using their undercoding ratio from CMS claims"
  - "Formula: If ratio = 0.25 (25%), they score 35/40 pain points"
  - "Lower ratio = more undercoding = higher pain = higher score"

**If BEHAVIORAL Track:**
- "**Economic Pain (Audit Risk) - Max 40 pts**"
  - "Measures therapy complexity and VBC readiness"
  - "Calculated using psych audit risk ratio"
  - "Formula: Risk ratio 0.50 (50%) = 30/40 pain points"
  - "We don't penalize clean billing - we reward VBC potential"

**If POST-ACUTE Track:**
- "**Economic Pain (Margin Pressure) - Max 40 pts**"
  - "Measures financial sustainability risk"
  - "Calculated from net margin in cost reports"
  - "Formula: Margin <2% = 40/40 pain points (severe pressure)"

**THEN EXPLAIN FIT & STRATEGY:**

**"Strategic Fit - Max 30 pts"**
- "Alignment with proven segments (FQHC = 15 pts, Behavioral = 15 pts)"
- "MIPS quality score bonus:"
  - "MIPS >80 = +5 pts (tech-ready, good documentation)"
  - "MIPS <50 = +5 pts (distressed performer, needs help)"
- "HPSA/MUA designation = +5 pts (complex population, mission-driven)"
- "Provider count (complexity): 1 provider = 0 pts, 50+ providers = 10 pts"

**"Strategic Value - Max 30 pts"**
- "Deal size potential based on volume and revenue scale"
- "Volume scoring:"
  - "Ambulatory: 50K+ patients = 15 pts, 10K+ = 8 pts"
  - "Behavioral: 20K+ patients = 15 pts, 5K+ = 8 pts (lower threshold)"
- "Revenue scoring:"
  - "FQHC: $5M+ = 15 pts, $2M+ = 7 pts"
  - "Other: $15M+ = 15 pts, $5M+ = 7 pts"

*[Hover over Pain bar]*
**"Hover any bar to see exact reasoning - fully transparent math receipts"**

**WHERE IT COMES FROM:**
- Pain: CMS claims data (undercoding ratio or psych risk ratio)
- Fit: NPPES taxonomy codes, CMS MIPS program, HRSA HPSA/MUA database
- Strategy: Claims volume + reported revenue (cost reports or estimates)

---

### 7️⃣ KEY METRICS (ORGANIZATION METRICS) (15s)

*[Scroll to Key Metrics or Organization Metrics section]*

**WHAT TO SAY:**

**"Revenue: $[X]M"**
- "Where it comes from (in priority order):"
  1. "FQHC Cost Reports (UDS) - most reliable"
  2. "Hospital Cost Reports (CMS HCRIS) - for hospital-affiliated"
  3. "Medicare Claims Volume × Reimbursement Rate - calculated"
  4. "Statistical estimate - if none of the above available"
- "Hover the info icon to see exact data source for this org"

**"Volume: [X] patients"**
- "Where it comes from:"
  1. "HRSA UDS reports - verified patient count for FQHCs"
  2. "Medicare beneficiary count from claims - minimum baseline"
  3. "Estimated from revenue ÷ average visit value"
- "VERIFIED volume badge means it's from UDS or claims, not estimated"

**"MIPS Score: [X]"** (if present)
- "Quality performance from CMS Merit-based Incentive Payment System"
- "Score range: 0-100"
- "High scores (>80) indicate:"
  - "Good EHR documentation"
  - "Tech-ready for integration"
  - "Quality reporting infrastructure in place"
- "Low scores (<50) indicate:"
  - "Potential compliance issues"
  - "Documentation gaps"
  - "Opportunity for improvement"

**"HPSA/MUA"** (if flagged)
- "Health Professional Shortage Area or Medically Underserved Area"
- "From HRSA designations database"
- "Indicates complex patient population, likely high Medicaid/uninsured mix"
- "Often mission-driven organizations with compliance challenges"

**WHERE IT COMES FROM:**
- Revenue: FQHC UDS → Hospital HCRIS → Claims calculation → Estimate
- Volume: HRSA UDS → Claims beneficiaries → Estimate
- MIPS: CMS MIPS Public Use File
- HPSA/MUA: HRSA designation database (county-level matching)

---

### 8️⃣ CONTACT INFORMATION (8s)

*[Scroll to Contact section]*

**WHAT TO SAY:**
- "**NPI (National Provider Identifier)**:"
  - "Unique 10-digit ID from NPPES (CMS provider database)"
  - "Used to link all data sources together"
  
- "**Phone Number**:"
  - "From NPPES provider records"
  - "This is their official business phone filed with CMS"
  
- "**Address**:"
  - "Primary practice location from NPPES"
  - "Some orgs have multiple sites - this is headquarters"

- "**Network Affiliations** (if shown):"
  - "From CMS provider reassignment files"
  - "Shows if they're part of a larger health system"
  - "ACO participation from CMS ACO public use file"

**WHERE IT COMES FROM:**
- All contact info: NPPES (National Plan and Provider Enumeration System)
- Network data: CMS PECOS reassignment bridge
- ACO status: CMS ACO Public Use File

---

### 9️⃣ KEY SIGNALS / DRIVERS (5s)

*[Point to driver tags/badges]*

**WHAT TO SAY:**
- "These are the **top buying signals** for this lead"
- "Examples:"
  - "**🩸 Severe Undercoding** = high pain, urgent need"
  - "**🐋 High Volume** = 25K+ patients, large contract potential"
  - "**✅ FQHC - Core ICP** = proven segment, high win rate"
  - "**🚨 SEVERE Psych Risk** = behavioral health audit exposure"
- "Tells sales which pain point to lead with on discovery call"

**WHERE IT COMES FROM:**
- Generated from scoring logic
- Prioritizes highest-impact signals
- Different drivers for different tracks

---

### 🔟 DATA GAPS (if present) (5s)

*[Point to yellow "Missing Data" box if visible]*

**WHAT TO SAY:**
- "We're transparent about what we DON'T know"
- "Missing data examples:"
  - "Margin data (only available for FQHCs/Hospitals with cost reports)"
  - "Complete provider roster (NPPES shows affiliated NPIs but not all staff)"
  - "Non-Medicare revenue (we only see Medicare claims)"
- "Gaps reduce confidence score but don't disqualify the lead"

---

## 🔀 AMBULATORY vs BEHAVIORAL COMPARISON (15 seconds)

*[Close drawer, go back to table]*

**SAY:** "Let me show you why we use different scoring tracks..."

*[Switch to Behavioral filter, click a Behavioral lead]*

**SAY:**
- "Notice the pain bar says **'Audit Risk'** not 'Revenue Leakage'"
- "Behavioral health practices have different workflows:"
  - "Longer therapy sessions (45-60 min vs 15 min)"
  - "Lower visit volumes but higher per-visit value"
  - "Different pain points: therapy complexity and audit risk vs E&M undercoding"
- "If we measured them on E&M undercoding, clean practices would score low"
- "But they're VBC-ready for collaborative care codes (99492-99494)"
- "Different tracks, different metrics, same goal: find motivated buyers"

---

## 🎯 CLOSING (10 seconds)

*[Close drawer, back to main table]*

**SAY:**
- "Bottom line: **data-driven GTM prioritization**"
- "[X] Tier 1 leads with VERIFIED opportunities"
- "Multi-million dollar pipeline identified from government data"
- "Export to HubSpot or CSV for immediate sales follow-up"
- "Every number traceable back to official sources"
- "Thanks for watching!"

---

## ⏱️ TIMING OPTIONS

### COMPREHENSIVE VERSION (2.5-3 minutes)
Perfect for internal training, investor demos, or detailed sales enablement.

| Section | Time | Duration |
|---------|------|----------|
| Intro | 0:00-0:10 | 10s |
| Datasets | 0:10-0:25 | 15s |
| Frontend Overview | 0:25-0:35 | 10s |
| **DRAWER WALKTHROUGH** | **0:35-2:20** | **105s** |
| ↳ Tier & Confidence | 0:35-0:40 | 5s |
| ↳ Strategic Brief | 0:40-0:50 | 10s |
| ↳ Revenue Lift (VERIFIED/PROJECTED) | 0:50-1:05 | 15s |
| ↳ Undercoding or Audit Risk | 1:05-1:20 | 15s |
| ↳ ICP Score Breakdown | 1:20-1:40 | 20s |
| ↳ Key Metrics | 1:40-1:55 | 15s |
| ↳ Contact Info | 1:55-2:03 | 8s |
| ↳ Drivers | 2:03-2:08 | 5s |
| ↳ Data Gaps | 2:08-2:13 | 5s |
| Ambulatory vs Behavioral | 2:20-2:35 | 15s |
| Closing | 2:35-2:45 | 10s |
| **TOTAL** | | **2:45 (165s)** |

---

### STREAMLINED VERSION (90 seconds)
Perfect for quick Loom demos, prospect follow-ups, or social media clips.

| Section | Time | Duration |
|---------|------|----------|
| Intro | 0:00-0:10 | 10s |
| Datasets | 0:10-0:20 | 10s |
| Frontend Overview | 0:20-0:25 | 5s |
| **DRAWER WALKTHROUGH (Focused)** | **0:25-1:10** | **45s** |
| ↳ Strategic Brief | 0:25-0:30 | 5s |
| ↳ Revenue Lift (emphasize VERIFIED) | 0:30-0:45 | 15s |
| ↳ Score Breakdown (hover to show tooltip) | 0:45-1:05 | 20s |
| ↳ Quick scroll past metrics | 1:05-1:10 | 5s |
| Closing with impact | 1:10-1:30 | 20s |
| **TOTAL** | | **90s** |

**What to SKIP in 90s version:**
- Detailed confidence explanation
- Undercoding analysis deep dive
- Individual metrics breakdown
- Contact info details
- Data gaps section
- Ambulatory vs Behavioral comparison

---

## 🗣️ WHAT TO SAY FOR EACH ELEMENT - QUICK REFERENCE

### Tier Badge
**"Tier 1 means ICP score ≥70 - high priority. Calculated from Pain + Fit + Strategy."**

### Confidence Badge
**"High Confidence means multiple verified sources. We rate data completeness 0-100%."**

### Strategic Brief
**"Auto-generated summary of WHY they score high. Not a sales pitch - analyst report."**

### Revenue Lift - VERIFIED
**"Calculated from actual Medicare claims. We analyzed their E&M coding patterns, compared to benchmark, calculated revenue gap from reimbursement rate differences."**

### Revenue Lift - PROJECTED
**"Estimated using statistical models when complete claims data unavailable. Industry benchmark: 5% lift opportunity. We always disclose projected vs verified."**

### Undercoding Ratio
**"Percentage of E&M visits coded as Level 4/5. National benchmark: 45%. Below = undercoding opportunity. Above = coding well or potential audit risk."**

### Psych Audit Risk
**"Max-level psych code usage ratio. >75% = severe audit risk. 25-50% = normal complexity. <25% = clean, VBC-ready."**

### Pain Score
**"Max 40 pts. Ambulatory = revenue leakage from undercoding. Behavioral = audit risk. Post-Acute = margin pressure. All from CMS data."**

### Fit Score
**"Max 30 pts. Segment alignment (FQHC/Behavioral = 15pts) + MIPS bonus + HPSA/MUA bonus + provider complexity."**

### Strategy Score
**"Max 30 pts. Volume scale (50K+ patients = 15pts for ambulatory, 20K+ = 15pts for behavioral) + Revenue scale ($5M+ FQHC, $15M+ other)."**

### Revenue Source
**"Priority: FQHC UDS → Hospital Cost Reports → Claims calculation → Statistical estimate. Hover info icon to see which."**

### Volume Source
**"Priority: HRSA UDS (verified) → Medicare beneficiary count → Estimate from revenue."**

### MIPS Score
**"CMS quality performance 0-100. >80 = tech-ready, good documentation. <50 = compliance gaps, opportunity for improvement."**

### HPSA/MUA
**"Health Professional Shortage Area or Medically Underserved Area from HRSA. Complex population, often high Medicaid mix."**

### NPI
**"10-digit National Provider Identifier from NPPES. Used to link all data sources."**

### Phone/Address
**"From NPPES provider database - official business phone and primary practice location."**

### Drivers
**"Top buying signals: Severe Undercoding, High Volume, FQHC Core ICP, Psych Risk. Tells sales which pain point to lead with."**

### Data Gaps
**"Transparent about missing data. Examples: margin data, non-Medicare revenue, complete provider roster. Reduces confidence but doesn't disqualify."**

---

## 💡 KEY CALCULATION FORMULAS (Memorize These)

### Revenue Lift (VERIFIED)
```
Step 1: Pull CMS claims → Count E&M visits by level
Step 2: Calculate ratio = (Level 4 + Level 5) / Total E&M
Step 3: Compare to benchmark (usually 45%)
Step 4: Gap = Benchmark - Actual (e.g., 45% - 25% = 20%)
Step 5: Opportunity = Gap × Total Visits × Rate Difference
Example: 20% × 10,000 visits × $40 = $80,000
```

### Revenue Lift (PROJECTED)
```
Revenue × 5% Industry Benchmark
Example: $5M revenue × 5% = $250K opportunity
```

### Pain Score (Ambulatory)
```
If undercoding_ratio <= 0.15: score = 40 pts
If undercoding_ratio >= 0.45: score = 10 pts
Else: Linear interpolation between 40 and 10
Example: 0.25 ratio = 30 pts, 0.35 ratio = 20 pts
```

### Fit Score (Behavioral)
```
Base: 15 pts (Behavioral = Core ICP)
+ MIPS >80: +5 pts
+ ACO participant: +5 pts
+ HPSA/MUA: +5 pts
+ Provider count bonus: +0-5 pts
Max: 30 pts (can't exceed)
```

### Strategy Score (Volume)
```
Ambulatory: 50K+ = 15pts, 25K+ = 12pts, 10K+ = 8pts
Behavioral: 20K+ = 15pts, 10K+ = 12pts, 5K+ = 8pts
(Lower thresholds for behavioral due to therapy session length)
```

---

## 🎯 PRO TIPS FOR RECORDING

### Pacing
- **Slow down for calculations** - this shows sophistication
- **Pause after "VERIFIED"** - let credibility land
- **Don't rush the drawer walkthrough** - it's the "wow" moment
- **Use hand gestures** to point to specific elements

### Energy Distribution
- Start strong (confident intro)
- Build through datasets
- **PEAK during drawer walkthrough** (most important)
- Stay high through calculations
- End strong with impact statement

### Language Precision
Use these exact phrases:
- ✅ "calculated from actual Medicare claims"
- ✅ "compared to national benchmarks"
- ✅ "from official government databases"
- ✅ "fully transparent - hover to see reasoning"
- ✅ "VERIFIED means we have complete claims data"
- ✅ "PROJECTED means statistical model-based estimate"

Avoid these:
- ❌ "I think..." / "maybe..." / "kind of..."
- ❌ "We tried to..." / "hopefully..."
- ❌ "estimated" without specifying PROJECTED badge
- ❌ "we scraped" (we don't scrape anything!)

### What Makes This Demo Different
- **Most demos:** Show features, click around
- **This demo:** Explain methodology, show data science rigor
- **Result:** Proves you understand healthcare data + analytics
- **Impact:** Not just a pretty UI - real intelligence engine

---

## ❓ COMMON QUESTIONS & ANSWERS

### Q: "How accurate is the revenue lift for VERIFIED opportunities?"
**A:** "As accurate as the government data. For VERIFIED, we're using their actual Medicare claims from CMS - every visit they billed. The only variable is whether their commercial payers show the same pattern, which they usually do."

### Q: "What if they don't use Medicare?"
**A:** "Medicare represents 40%+ of most ambulatory revenue, so it's a strong proxy. And undercoding patterns in Medicare typically apply to commercial payers too - it's a documentation issue, not a payer issue."

### Q: "Why is PROJECTED less reliable?"
**A:** "PROJECTED means we don't have their complete claims data. We're using industry benchmarks (5% revenue lift) which is conservative. It's an order-of-magnitude estimate, not a precise calculation. We always disclose this clearly."

### Q: "How do you get FQHC revenue data?"
**A:** "FQHCs file UDS (Uniform Data System) reports with HRSA annually. These include total revenue, patient count, and visit volume. It's public data matched via grant number."

### Q: "What if MIPS score is 0 or missing?"
**A:** "MIPS is only required for clinicians billing >$90K/year in Medicare. Missing MIPS could mean: (1) they're below the threshold, (2) they're hospital-based (exempt), or (3) they're new (not yet reporting). We don't penalize missing MIPS - we just don't add bonus points."

### Q: "Why does Behavioral Health use different scoring?"
**A:** "Therapy sessions are 45-60 minutes vs 15 minutes for primary care. Different workflows, different economics, different pain points. Using E&M undercoding doesn't make sense for psych practices - we score on therapy complexity and audit risk instead."

### Q: "Can I export this data to HubSpot?"
**A:** "Yes! Export button coming soon. Right now you can query the JSON directly at `web/public/data/clinics.json` - all 5,000 scored leads with complete metadata."

---

## ✅ PRE-RECORDING CHECKLIST

### Before You Hit Record
- [ ] Start web server: `cd web && npm run dev`
- [ ] Open dashboard: `http://localhost:3000`
- [ ] Identify which lead you'll click on (top FQHC with VERIFIED status preferred)
- [ ] Note exact revenue lift value (so you can say it confidently)
- [ ] Note exact Pain/Fit/Strategy scores (so you can reference them)
- [ ] Practice saying "calculated from actual Medicare claims" 3 times out loud
- [ ] Decide: Comprehensive (2:45) or Streamlined (90s) version?
- [ ] Have LOOM_BULLETS.md open in another window for reference

### During Recording
- [ ] Speak at normal conversational pace (don't rush!)
- [ ] Point to elements as you explain them
- [ ] Pause briefly after mentioning "VERIFIED"
- [ ] Hover over Pain bar to show tooltip
- [ ] Use confident language: "calculated from", "measured via"
- [ ] Emphasize "official government sources" at least twice

### After Recording
- [ ] Watch it back - does it feel educational or salesy? (Aim for educational)
- [ ] Check audio quality - calculations should be crystal clear
- [ ] Verify you explained VERIFIED vs PROJECTED clearly
- [ ] Confirm you showed at least one hover tooltip
- [ ] Make sure you mentioned where data comes from for 2-3 key metrics

---

## 🎬 FINAL NOTES

**This comprehensive walkthrough accomplishes three goals:**

1. **Credibility:** Shows every number traces to official sources
2. **Transparency:** Explains calculations step-by-step, shows "math receipts"
3. **Sophistication:** Proves you built an intelligence engine, not just a dashboard

**The drawer is your "wow" moment.** Most people build dashboards that show scores without explanation. You built a system that shows the score AND the complete calculation methodology. That's what makes this special.

**Take your time with this demo.** The 2:45 comprehensive version is worth it for training and high-stakes demos. The 90-second version is great for quick follow-ups and social proof.

---

**🚀 You've got this! Now go record that Loom!** 🎥
