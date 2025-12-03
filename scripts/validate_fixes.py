"""
GTM Intelligence Fix Validation Script
Author: Charta Health Engineering

Purpose: Validate the recent fixes to therapy relevance gate,
segment labeling, and procedure alignment.

This script will:
1. Test therapy relevance logic with percentage-based filtering
2. Validate segment labeling is using descriptive names
3. Verify procedure alignment data exists and is scoring properly
4. Generate a summary report

Run this AFTER running the full scoring pipeline:
  python3 workers/pipeline/score_icp_production.py
"""

import pandas as pd
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCORED_FILE = os.path.join(ROOT, "data", "curated", "clinics_scored_final.csv")

print("="*80)
print(" GTM INTELLIGENCE FIX VALIDATION")
print("="*80)

if not os.path.exists(SCORED_FILE):
    print(f"\n❌ ERROR: Scored file not found: {SCORED_FILE}")
    print("   Please run: python3 workers/pipeline/score_icp_production.py")
    sys.exit(1)

df = pd.read_csv(SCORED_FILE, low_memory=False)
print(f"\n✅ Loaded {len(df):,} scored clinics")

# ============================================================================
# TEST 1: Therapy Relevance Gate (Percentage-Based)
# ============================================================================
print("\n" + "="*80)
print(" TEST 1: THERAPY RELEVANCE GATE")
print("="*80)

therapy_pain = df[df['pain_label'].str.contains('Therapy', na=False)].copy()
print(f"\nTotal clinics with Therapy Pain: {len(therapy_pain):,}")

# Calculate therapy percentage for those flagged
if 'total_psych_codes' in df.columns and 'total_eval_codes' in df.columns:
    def calc_psych_pct(row):
        psych = row['total_psych_codes'] if pd.notna(row['total_psych_codes']) else 0
        eval_codes = row['total_eval_codes'] if pd.notna(row['total_eval_codes']) else 0
        total = psych + eval_codes
        if total > 0:
            return psych / total
        else:
            return 0

    therapy_pain['psych_percentage'] = therapy_pain.apply(calc_psych_pct, axis=1)

    # Expected: All therapy pain clinics should have >20% psych volume
    low_psych = therapy_pain[therapy_pain['psych_percentage'] < 0.20]

    print(f"\n📊 Therapy Pain Distribution by Psych %:")
    print(f"   >50% psych volume: {len(therapy_pain[therapy_pain['psych_percentage'] >= 0.50]):,}")
    print(f"   20-50% psych volume: {len(therapy_pain[(therapy_pain['psych_percentage'] >= 0.20) & (therapy_pain['psych_percentage'] < 0.50)]):,}")
    print(f"   <20% psych volume: {len(low_psych):,} 🚨")

    if len(low_psych) > 0:
        print(f"\n❌ FAIL: Found {len(low_psych):,} clinics with therapy pain but <20% psych volume")
        print("\nSample problem cases:")
        print(low_psych[['org_name', 'segment_label', 'pain_label', 'total_psych_codes', 'total_eval_codes', 'psych_percentage']].head(5).to_string(index=False))
        print("\n⚠️  The therapy relevance gate is NOT working correctly.")
    else:
        print(f"\n✅ PASS: All therapy pain clinics have >20% psych volume")
else:
    print("\n⚠️  Cannot validate: total_psych_codes or total_eval_codes columns missing")

# Check for major health systems with therapy pain
major_systems = ['FROEDTERT', 'MONTEFIORE', 'NORTH SHORE', 'SUTTER', 'KAISER', 'CLEVELAND CLINIC']
for system in major_systems:
    system_therapy = therapy_pain[therapy_pain['org_name'].str.contains(system, case=False, na=False)]
    if len(system_therapy) > 0:
        print(f"\n❌ FAIL: Found {system} with therapy pain")
        print(system_therapy[['org_name', 'pain_label', 'total_psych_codes', 'total_eval_codes']].head(1).to_string(index=False))

# ============================================================================
# TEST 2: Segment Labeling
# ============================================================================
print("\n" + "="*80)
print(" TEST 2: SEGMENT LABELING")
print("="*80)

segment_dist = df['segment_label'].value_counts()
print(f"\nSegment Distribution:")
for seg, count in segment_dist.head(10).items():
    print(f"   {seg}: {count:,}")

# Check for old A-F labels
old_labels = df[df['segment_label'].str.contains('Segment [A-F]', na=False, regex=True)]
if len(old_labels) > 0:
    print(f"\n❌ FAIL: Found {len(old_labels):,} clinics with old Segment A-F labels")
    print("   This means the pipeline wasn't re-run after fixing segment labels")
else:
    print(f"\n✅ PASS: No old Segment A-F labels found")

# Check for descriptive labels
descriptive_labels = ['FQHC', 'Hospital', 'Home Health', 'Private Practice', 'Multi-specialty', 'Urgent Care', 'Behavioral Health', 'Specialty Group']
descriptive_count = df[df['segment_label'].isin(descriptive_labels)].shape[0]
print(f"\nClinics with descriptive labels: {descriptive_count:,} ({descriptive_count/len(df)*100:.1f}%)")

# ============================================================================
# TEST 3: Procedure Alignment Data
# ============================================================================
print("\n" + "="*80)
print(" TEST 3: PROCEDURE ALIGNMENT DATA")
print("="*80)

if 'total_procedure_codes' in df.columns and 'procedure_ratio' in df.columns:
    print(f"\n✅ Procedure columns exist in scored data")

    proc_data = df[df['total_procedure_codes'].gt(0)]
    print(f"   Clinics with procedure data: {len(proc_data):,} ({len(proc_data)/len(df)*100:.1f}%)")

    if len(proc_data) > 0:
        print(f"   Average procedure ratio: {proc_data['procedure_ratio'].mean():.1%}")
        print(f"   Median procedure ratio: {proc_data['procedure_ratio'].median():.1%}")

        # Check for procedure alignment in drivers
        proc_drivers = df[df['scoring_drivers'].str.contains('Procedure Alignment', na=False)]
        print(f"\n   Clinics with procedure alignment driver: {len(proc_drivers):,}")

        if len(proc_drivers) > 0:
            print("\nSample procedure alignment cases:")
            print(proc_drivers[['org_name', 'segment_label', 'pain_label', 'procedure_ratio', 'scoring_drivers']].head(3).to_string(index=False))
        else:
            print("\n⚠️  No clinics have procedure alignment drivers (may be working as intended if no deficits found)")
    else:
        print("\n⚠️  No clinics have procedure code data")
else:
    print(f"\n❌ FAIL: Procedure columns missing from scored data")
    print("   This means either:")
    print("   1. CPT mining wasn't run with new procedure logic, OR")
    print("   2. Pipeline didn't merge procedure columns, OR")
    print("   3. Scoring pipeline wasn't re-run after CPT mining")

# ============================================================================
# TEST 4: Pain Label Distribution
# ============================================================================
print("\n" + "="*80)
print(" TEST 4: PAIN LABEL DISTRIBUTION")
print("="*80)

pain_dist = df['pain_label'].value_counts()
print(f"\nPain Label Distribution:")
for label, count in pain_dist.items():
    pct = count / len(df) * 100
    print(f"   {label}: {count:,} ({pct:.1f}%)")

# Expected: Most should be "Undercoding Pain" for E&M
# Only specialized BH clinics should have therapy pain
therapy_total = pain_dist[pain_dist.index.str.contains('Therapy', na=False)].sum()
print(f"\nTotal Therapy Pain: {therapy_total:,} ({therapy_total/len(df)*100:.1f}%)")

if therapy_total / len(df) > 0.20:
    print(f"⚠️  WARNING: >20% of clinics have therapy pain - may still be too broad")
else:
    print(f"✅ Therapy pain is under 20% of total clinics")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print(" VALIDATION SUMMARY")
print("="*80)

issues = []

# Check therapy gate
if 'total_psych_codes' in df.columns:
    therapy_low_pct = len(therapy_pain[therapy_pain['psych_percentage'] < 0.20]) if len(therapy_pain) > 0 else 0
    if therapy_low_pct > 0:
        issues.append(f"Therapy relevance gate: {therapy_low_pct:,} clinics with therapy pain but <20% psych volume")

# Check segment labels
if len(old_labels) > 0:
    issues.append(f"Old segment labels: {len(old_labels):,} clinics still using Segment A-F notation")

# Check procedure data
if 'total_procedure_codes' not in df.columns:
    issues.append("Procedure alignment data missing from scored file")

if len(issues) > 0:
    print("\n❌ ISSUES FOUND:")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")

    print("\n🔧 RECOMMENDED FIXES:")
    if any('procedure' in i.lower() for i in issues):
        print("   1. Re-run CPT mining: python3 workers/pipeline/mine_cpt_codes.py")
    if any('segment' in i.lower() or 'therapy' in i.lower() for i in issues):
        print("   2. Re-run scoring pipeline: python3 workers/pipeline/score_icp_production.py")
    print("   3. Update frontend data: python3 scripts/update_frontend_data.py")
else:
    print("\n✅ ALL TESTS PASSED!")
    print("\n📋 NEXT STEPS:")
    print("   1. Review sample clinics in the frontend")
    print("   2. Verify therapy pain only appears for true BH clinics")
    print("   3. Check procedure alignment is showing for applicable specialties")
    print("   4. Validate segment labels are descriptive and accurate")

print("\n" + "="*80)
