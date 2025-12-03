#!/usr/bin/env python3
"""
Test Network-Level ICP Scoring System

This script validates the network grouping and scoring logic.
"""

import os
import sys
import pandas as pd

# Add parent directory to path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from workers.score_icp import (
    normalize_network_name,
    create_network_id,
    group_clinics_into_networks,
    calculate_network_icp_scores,
    enrich_clinics_with_network_data
)

def test_name_normalization():
    """Test name normalization logic."""
    print("\n" + "=" * 70)
    print("TEST 1: Name Normalization")
    print("=" * 70)
    
    test_cases = [
        ("KANSAS UNIVERSITY PHYSICIANS INC", "kansas university physicians"),
        ("St. Mary's Hospital, LLC", "st marys hospital"),
        ("Children's Hospital of Philadelphia", "childrens hospital of philadelphia"),
        ("JOHNS HOPKINS PHYSICIANS, LLC", "johns hopkins physicians"),
        ("UCSF Medical Center - Mission Bay", "ucsf medical center  mission bay"),
        ("", ""),
        (None, ""),
    ]
    
    passed = 0
    failed = 0
    
    for original, expected in test_cases:
        result = normalize_network_name(original)
        if result == expected:
            print(f"  ✓ '{original}' → '{result}'")
            passed += 1
        else:
            print(f"  ✗ '{original}' → '{result}' (expected: '{expected}')")
            failed += 1
    
    print(f"\n  Results: {passed} passed, {failed} failed")
    return failed == 0


def test_network_id_creation():
    """Test network ID generation."""
    print("\n" + "=" * 70)
    print("TEST 2: Network ID Creation")
    print("=" * 70)
    
    # Test consistency
    name = "kansas university physicians"
    id1 = create_network_id(name)
    id2 = create_network_id(name)
    
    if id1 == id2:
        print(f"  ✓ Consistent IDs: {id1}")
    else:
        print(f"  ✗ Inconsistent IDs: {id1} vs {id2}")
        return False
    
    # Test uniqueness
    name1 = "kansas university physicians"
    name2 = "kansas state university physicians"
    id1 = create_network_id(name1)
    id2 = create_network_id(name2)
    
    if id1 != id2:
        print(f"  ✓ Unique IDs: {id1} vs {id2}")
    else:
        print(f"  ✗ Same ID for different names: {id1}")
        return False
    
    # Test format
    if id1.startswith("net_") and len(id1) == 16:
        print(f"  ✓ Correct format: {id1}")
    else:
        print(f"  ✗ Invalid format: {id1}")
        return False
    
    print(f"\n  Results: All tests passed")
    return True


def test_network_grouping():
    """Test network grouping logic on sample data."""
    print("\n" + "=" * 70)
    print("TEST 3: Network Grouping")
    print("=" * 70)
    
    # Create sample data
    sample_data = {
        'clinic_id': [
            'clinic-1-DE', 'clinic-2-PA', 'clinic-3-NY',
            'clinic-4-TX', 'clinic-5-CA', 'clinic-6-FL',
            'clinic-7-DE', 'clinic-8-DE', 'clinic-9-DE'
        ],
        'account_name': [
            'CHRISTIANA CARE HEALTH SERVICES INC',  # Network 1
            'CHRISTIANA CARE HEALTH SERVICES INC',  # Network 1
            'JOHNS HOPKINS PHYSICIANS LLC',         # Standalone (single clinic)
            'MEMORIAL HERMANN HEALTH SYSTEM',       # Network 2
            'MEMORIAL HERMANN HEALTH SYSTEM',       # Network 2
            'MEMORIAL HERMANN HEALTH SYSTEM',       # Network 2
            'UNIQUE CLINIC INC',                    # Standalone (single clinic)
            'DELAWARE MEDICAL GROUP',               # Network 3 (3+ clinics, same state)
            'DELAWARE MEDICAL GROUP',               # Network 3
        ],
        'state_code': ['DE', 'PA', 'NY', 'TX', 'TX', 'TX', 'DE', 'DE', 'DE'],
        'icp_total_score': [70, 65, 75, 80, 78, 72, 60, 62, 64],
        'icp_fit_score': [15, 14, 16, 17, 16, 15, 13, 13, 14],
        'icp_pain_score': [14, 13, 15, 16, 15, 14, 12, 12, 13],
        'icp_compliance_score': [7, 6, 8, 8, 8, 7, 6, 6, 6],
        'icp_propensity_score': [7, 6, 8, 8, 8, 7, 6, 6, 6],
        'icp_scale_score': [17, 16, 18, 19, 19, 18, 15, 16, 16],
        'icp_segment_score': [10, 10, 10, 12, 12, 11, 8, 9, 9],
        'icp_tier': [2, 2, 2, 2, 2, 2, 2, 2, 2],
        'icp_segment': ['C', 'C', 'C', 'C', 'C', 'C', 'B', 'B', 'B'],
        'site_count': [5, 3, 2, 8, 6, 4, 1, 1, 1],
        'npi_count': [50, 30, 20, 80, 60, 40, 10, 10, 10],
        'fqhc_flag': [0, 0, 0, 0, 0, 0, 0, 0, 0],
        'aco_member': [1, 1, 0, 1, 1, 1, 0, 0, 0],
    }
    
    df = pd.DataFrame(sample_data)
    
    # Test grouping
    result = group_clinics_into_networks(df)
    
    # Validate results
    networks = result[result['network_id'].notna()]
    standalone = result[result['network_id'].isna()]
    
    print(f"\n  Validation:")
    print(f"    • Total clinics: {len(result)}")
    print(f"    • Clinics in networks: {len(networks)}")
    print(f"    • Standalone clinics: {len(standalone)}")
    print(f"    • Unique networks: {result['network_id'].nunique() - 1}")  # -1 for NaN
    
    # Check expected groupings
    christiana_network = result[result['normalized_network_name'] == 'christiana care health services']
    memorial_network = result[result['normalized_network_name'] == 'memorial hermann health system']
    delaware_network = result[result['normalized_network_name'] == 'delaware medical group']
    
    success = True
    
    if len(christiana_network) == 2:
        print(f"    ✓ Christiana Care network: 2 clinics (multi-state)")
    else:
        print(f"    ✗ Christiana Care network: {len(christiana_network)} clinics (expected 2)")
        success = False
    
    if len(memorial_network) == 3:
        print(f"    ✓ Memorial Hermann network: 3 clinics (multi-clinic, same state)")
    else:
        print(f"    ✗ Memorial Hermann network: {len(memorial_network)} clinics (expected 3)")
        success = False
    
    if len(delaware_network) >= 2:  # Should be grouped due to 3+ clinics
        print(f"    ✓ Delaware Medical Group network: {len(delaware_network)} clinics (3+ clinics, same state)")
    else:
        print(f"    ⚠️  Delaware Medical Group: {len(delaware_network)} clinics (expected 2+)")
    
    print(f"\n  Results: {'All tests passed' if success else 'Some tests failed'}")
    return success


def test_network_scoring():
    """Test network scoring calculation."""
    print("\n" + "=" * 70)
    print("TEST 4: Network Scoring")
    print("=" * 70)
    
    # Create sample data with a network
    sample_data = {
        'clinic_id': ['clinic-1-DE', 'clinic-2-PA', 'clinic-3-MD'],
        'account_name': [
            'CHRISTIANA CARE HEALTH SERVICES INC',
            'CHRISTIANA CARE HEALTH SERVICES INC',
            'CHRISTIANA CARE HEALTH SERVICES INC'
        ],
        'state_code': ['DE', 'PA', 'MD'],
        'icp_total_score': [70, 65, 75],
        'icp_fit_score': [15, 14, 16],
        'icp_pain_score': [14, 13, 15],
        'icp_compliance_score': [7, 6, 8],
        'icp_propensity_score': [7, 6, 8],
        'icp_scale_score': [17, 16, 18],
        'icp_segment_score': [10, 10, 10],
        'icp_tier': [2, 2, 2],
        'icp_tier_label': ['Tier 2 - Qualified'] * 3,
        'icp_segment': ['C', 'C', 'C'],
        'site_count': [5, 3, 4],
        'npi_count': [50, 30, 40],
        'fqhc_flag': [0, 0, 0],
        'aco_member': [1, 1, 1],
    }
    
    df = pd.DataFrame(sample_data)
    
    # Group into networks
    df_with_networks = group_clinics_into_networks(df)
    
    # Calculate network scores
    networks_df = calculate_network_icp_scores(df_with_networks)
    
    # Validate
    if len(networks_df) > 0:
        network = networks_df.iloc[0]
        print(f"\n  Network Details:")
        print(f"    • Network ID: {network['network_id']}")
        print(f"    • Network Name: {network['network_name']}")
        print(f"    • Num Clinics: {network['num_clinics']}")
        print(f"    • Num States: {network['num_states']}")
        print(f"    • Network ICP Score: {network['network_icp_total_score']:.1f}")
        print(f"    • Network Tier: {network['network_icp_tier_label']}")
        print(f"    • Network Segment: {network['network_icp_segment']}")
        
        # Check weighted average is reasonable
        expected_score = (70 * 5 + 65 * 3 + 75 * 4) / (5 + 3 + 4)  # Weighted by site_count
        actual_score = network['network_icp_total_score']
        
        if abs(actual_score - expected_score) < 1.0:
            print(f"    ✓ Score calculation correct: {actual_score:.1f} (expected: {expected_score:.1f})")
            success = True
        else:
            print(f"    ✗ Score calculation incorrect: {actual_score:.1f} (expected: {expected_score:.1f})")
            success = False
    else:
        print(f"    ✗ No networks created")
        success = False
    
    print(f"\n  Results: {'All tests passed' if success else 'Some tests failed'}")
    return success


def test_clinic_enrichment():
    """Test clinic enrichment with network data."""
    print("\n" + "=" * 70)
    print("TEST 5: Clinic Enrichment")
    print("=" * 70)
    
    # Create sample data
    sample_data = {
        'clinic_id': ['clinic-1-DE', 'clinic-2-PA', 'clinic-3-NY'],
        'account_name': [
            'CHRISTIANA CARE HEALTH SERVICES INC',
            'CHRISTIANA CARE HEALTH SERVICES INC',
            'UNIQUE CLINIC INC'
        ],
        'state_code': ['DE', 'PA', 'NY'],
        'icp_total_score': [75, 65, 70],
        'icp_fit_score': [16, 14, 15],
        'icp_pain_score': [15, 13, 14],
        'icp_compliance_score': [8, 6, 7],
        'icp_propensity_score': [8, 6, 7],
        'icp_scale_score': [18, 16, 17],
        'icp_segment_score': [10, 10, 10],
        'icp_tier': [2, 2, 2],
        'icp_tier_label': ['Tier 2 - Qualified'] * 3,
        'icp_segment': ['C', 'C', 'C'],
        'site_count': [5, 3, 2],
        'npi_count': [50, 30, 20],
        'fqhc_flag': [0, 0, 0],
        'aco_member': [1, 1, 0],
    }
    
    df = pd.DataFrame(sample_data)
    
    # Group and score
    df_with_networks = group_clinics_into_networks(df)
    networks_df = calculate_network_icp_scores(df_with_networks)
    enriched_df = enrich_clinics_with_network_data(df_with_networks, networks_df)
    
    # Validate enrichment
    print(f"\n  Enrichment Results:")
    
    # Check columns added
    expected_cols = ['network_icp_score', 'network_tier', 'network_tier_label', 'is_network_anchor', 'num_clinics']
    missing_cols = [col for col in expected_cols if col not in enriched_df.columns]
    
    if not missing_cols:
        print(f"    ✓ All expected columns present")
    else:
        print(f"    ✗ Missing columns: {missing_cols}")
        return False
    
    # Check anchor clinic identification
    anchors = enriched_df[enriched_df['is_network_anchor'] == True]
    
    if len(anchors) > 0:
        anchor = anchors.iloc[0]
        print(f"    ✓ Anchor clinic identified: {anchor['clinic_id']} (score: {anchor['icp_total_score']})")
        
        # Anchor should be highest scoring clinic in network
        network_clinics = enriched_df[enriched_df['network_id'] == anchor['network_id']]
        if anchor['icp_total_score'] == network_clinics['icp_total_score'].max():
            print(f"    ✓ Anchor is highest-scoring clinic in network")
        else:
            print(f"    ✗ Anchor is not highest-scoring clinic")
            return False
    else:
        print(f"    ⚠️  No anchor clinics identified")
    
    # Check standalone clinic has no network data
    standalone = enriched_df[enriched_df['clinic_id'] == 'clinic-3-NY'].iloc[0]
    if pd.isna(standalone['network_icp_score']):
        print(f"    ✓ Standalone clinic has no network score")
    else:
        print(f"    ✗ Standalone clinic incorrectly has network score")
        return False
    
    print(f"\n  Results: All tests passed")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("NETWORK ICP SCORING - TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Name Normalization", test_name_normalization),
        ("Network ID Creation", test_network_id_creation),
        ("Network Grouping", test_network_grouping),
        ("Network Scoring", test_network_scoring),
        ("Clinic Enrichment", test_clinic_enrichment),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n  ✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Total: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n  🎉 All tests passed!")
        return 0
    else:
        print(f"\n  ⚠️  {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

