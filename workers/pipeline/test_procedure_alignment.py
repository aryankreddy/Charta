"""
Test script for Procedure Alignment Pain Score
Author: Charta Health GTM Strategy

This script tests the procedure alignment logic with synthetic data
to verify it correctly identifies procedure-heavy specialties that are
only billing E&M codes.
"""

import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from workers.pipeline.score_icp_production import (
    get_expected_procedure_ratio,
    score_procedure_alignment,
    calculate_row_score
)

def test_taxonomy_detection():
    """Test that we correctly identify procedure-heavy specialties."""
    print("="*80)
    print("TEST 1: Taxonomy Detection")
    print("="*80)

    test_cases = [
        ("213E00000X", 0.60, "Podiatry"),
        ("207X00000X", 0.50, "Orthopedics"),
        ("207W00000X", 0.60, "Ophthalmology"),
        ("207N00000X", 0.50, "Dermatology"),
        ("207Q00000X", None, "Family Medicine (not procedure-heavy)"),
    ]

    for taxonomy, expected, specialty in test_cases:
        result = get_expected_procedure_ratio(taxonomy)
        if result == expected:
            print(f"✅ {specialty} ({taxonomy}): Expected {expected}, Got {result}")
        else:
            print(f"❌ {specialty} ({taxonomy}): Expected {expected}, Got {result}")

def test_procedure_alignment_scoring():
    """Test the procedure alignment scoring logic."""
    print("\n" + "="*80)
    print("TEST 2: Procedure Alignment Scoring")
    print("="*80)

    # Test Case 1: Podiatrist with low procedure ratio (should flag)
    test_case_1 = pd.Series({
        'org_name': 'Bazzi Podiatry',
        'segment_label': 'Private Practice',
        'taxonomy': '213E00000X',
        'procedure_ratio': 0.10,  # Only 10% procedures (expected 60%)
        'total_procedure_codes': 100,
        'total_eval_codes': 900,
    })

    score_1, reason_1 = score_procedure_alignment(test_case_1)
    print(f"\n📋 Test Case 1: Podiatry with 10% procedures (expected 60%)")
    print(f"   Score: {score_1:.1f} points")
    print(f"   Reason: {reason_1}")
    if score_1 >= 4:
        print(f"   ✅ Correctly flagged severe deficit")
    else:
        print(f"   ❌ Should have flagged severe deficit")

    # Test Case 2: Podiatrist with appropriate procedure ratio (should not flag)
    test_case_2 = pd.Series({
        'org_name': 'Good Podiatry',
        'segment_label': 'Private Practice',
        'taxonomy': '213E00000X',
        'procedure_ratio': 0.58,  # 58% procedures (close to 60% expected)
        'total_procedure_codes': 580,
        'total_eval_codes': 420,
    })

    score_2, reason_2 = score_procedure_alignment(test_case_2)
    print(f"\n📋 Test Case 2: Podiatry with 58% procedures (expected 60%)")
    print(f"   Score: {score_2:.1f} points")
    print(f"   Reason: {reason_2 if reason_2 else 'No deficit'}")
    if score_2 == 0:
        print(f"   ✅ Correctly did not flag")
    else:
        print(f"   ❌ Should not have flagged")

    # Test Case 3: Family Medicine (not procedure-heavy, should not flag)
    test_case_3 = pd.Series({
        'org_name': 'Smith Family Medicine',
        'segment_label': 'Private Practice',
        'taxonomy': '207Q00000X',
        'procedure_ratio': 0.10,  # Low procedures, but not expected
        'total_procedure_codes': 100,
        'total_eval_codes': 900,
    })

    score_3, reason_3 = score_procedure_alignment(test_case_3)
    print(f"\n📋 Test Case 3: Family Medicine with 10% procedures (no expectation)")
    print(f"   Score: {score_3:.1f} points")
    print(f"   Reason: {reason_3 if reason_3 else 'Not procedure-heavy specialty'}")
    if score_3 == 0:
        print(f"   ✅ Correctly did not flag")
    else:
        print(f"   ❌ Should not have flagged")

def test_full_scoring():
    """Test the full scoring integration."""
    print("\n" + "="*80)
    print("TEST 3: Full Scoring Integration")
    print("="*80)

    # Test Case: Podiatrist with both undercoding and procedure alignment issues
    test_case = pd.Series({
        'org_name': 'Bazzi Podiatry',
        'npi': '1234567890',
        'segment_label': 'Private Practice',
        'taxonomy': '213E00000X',
        'state_code': 'MI',

        # E&M Undercoding
        'undercoding_ratio': 0.25,  # Severe undercoding
        'total_eval_codes': 900,

        # Procedure Alignment Issue
        'procedure_ratio': 0.10,  # Only 10% procedures (expected 60%)
        'total_procedure_codes': 100,

        # Therapy (not relevant)
        'total_psych_codes': 0,
        'psych_risk_ratio': 0,

        # Volume/Revenue
        'services_count': 1000,
        'final_volume': 1000,
        'total_revenue': 500_000,
        'volume_source': 'CLAIMS',

        # Fit factors
        'npi_count': 3,
        'site_count': 1,
        'fqhc_flag': 0,
        'is_aco_participant': 'false',
        'risk_compliance_flag': 'false',
        'oig_leie_flag': 'false',
    })

    result = calculate_row_score(test_case)

    print(f"\n📊 Scoring Results for Bazzi Podiatry:")
    print(f"   ICP Score: {result['icp_score']:.1f} / 100")
    print(f"   ICP Tier: {result['icp_tier']}")
    print(f"   Pain Label: {result['pain_label']}")
    print(f"   Pain Score: {result['score_pain_total']:.1f} / 40")
    print(f"   Pain Reasoning: {result['score_reasoning_pain']}")
    print(f"   Drivers: {result['scoring_drivers']}")

    # Check if procedure alignment is mentioned
    if 'Procedure' in result['score_reasoning_pain'] or 'procedure' in result['score_reasoning_pain'].lower():
        print(f"\n   ✅ Procedure alignment pain is included in reasoning")
    else:
        print(f"\n   ❌ Procedure alignment pain is NOT mentioned in reasoning")

    if result['score_pain_total'] >= 30:
        print(f"   ✅ High pain score (>= 30) as expected")
    else:
        print(f"   ⚠️  Pain score lower than expected")

if __name__ == "__main__":
    test_taxonomy_detection()
    test_procedure_alignment_scoring()
    test_full_scoring()

    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80)
