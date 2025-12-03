#!/usr/bin/env python3
"""
Phase 1 ICP Scoring Validation
Tests Economic Pain component (40 points)
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from workers.score_icp import calculate_icp_score

def run_validation():
    print("=" * 60)
    print("PHASE 1 VALIDATION - ECONOMIC PAIN SCORING")
    print("=" * 60)
    
    # Test 1: Ideal FQHC (Should score 38-40)
    print("\n" + "=" * 60)
    print("TEST 1: Ideal FQHC (Expected: 38-40/40)")
    print("=" * 60)
    
    test_fqhc = {
        'practice_type': 'FQHC',
        'provider_count': 30,
        'estimated_encounters': 52000,
        'net_margin': 0.008,
        'medicaid_pct': 0.68,
        'location_count': 6,
        'em_code_pct': 0.85,
        'offers_ccm': True,
        'has_billing_staff': False
    }
    
    result1 = calculate_icp_score(test_fqhc)
    
    print(f"\n📊 Score: {result1['economic_pain']}/40")
    print(f"🎯 Tier: {result1['tier']}")
    print(f"\n📈 Breakdown:")
    print(f"  - Margin Pressure: {result1['breakdown']['margin_pressure']}/15")
    print(f"  - Volume Leverage: {result1['breakdown']['volume_leverage']}/12")
    print(f"  - Leakage Indicators: {result1['breakdown']['leakage_indicators']}/13")
    
    print(f"\n💡 Justification:")
    for j in result1['justification']:
        print(f"  • {j}")
    
    # Validation
    try:
        assert result1['economic_pain'] >= 38, f"❌ FAIL: FQHC scored too low: {result1['economic_pain']}"
        assert result1['breakdown']['margin_pressure'] == 15, "❌ FAIL: Margin pressure should be 15"
        assert result1['breakdown']['volume_leverage'] == 12, "❌ FAIL: Volume leverage should be 12"
        assert result1['breakdown']['leakage_indicators'] >= 11, "❌ FAIL: Leakage indicators too low"
        print("\n✅ TEST 1 PASSED")
    except AssertionError as e:
        print(f"\n{e}")
        return False
    
    # Test 2: Small Primary Care (Should score ~20)
    print("\n" + "=" * 60)
    print("TEST 2: Small Primary Care (Expected: 17-24/40)")
    print("=" * 60)
    
    test_small_pc = {
        'practice_type': 'Primary Care',
        'provider_count': 4,
        'estimated_encounters': 9600,
        'medicaid_pct': 0.25,
        'location_count': 1,
        'em_code_pct': 0.75,
        'offers_ccm': False,
        'has_billing_staff': True
    }
    
    result2 = calculate_icp_score(test_small_pc)
    
    print(f"\n📊 Score: {result2['economic_pain']}/40")
    print(f"🎯 Tier: {result2['tier']}")
    print(f"\n📈 Breakdown:")
    print(f"  - Margin Pressure: {result2['breakdown']['margin_pressure']}/15")
    print(f"  - Volume Leverage: {result2['breakdown']['volume_leverage']}/12")
    print(f"  - Leakage Indicators: {result2['breakdown']['leakage_indicators']}/13")
    
    try:
        assert result2['economic_pain'] >= 17, f"❌ FAIL: Primary care too low: {result2['economic_pain']}"
        assert result2['economic_pain'] <= 24, f"❌ FAIL: Primary care too high: {result2['economic_pain']}"
        print("\n✅ TEST 2 PASSED")
    except AssertionError as e:
        print(f"\n{e}")
        return False
    
    # Test 3: High-Reimbursement Specialty (Should score 8-10)
    print("\n" + "=" * 60)
    print("TEST 3: Cardiology - Low Fit (Expected: 8-12/40)")
    print("=" * 60)
    
    test_cardiology = {
        'practice_type': 'Cardiology',
        'provider_count': 6,
        'estimated_encounters': 8000,
        'medicaid_pct': 0.10,
        'location_count': 1,
        'em_code_pct': 0.40,
        'has_billing_staff': True
    }
    
    result3 = calculate_icp_score(test_cardiology)
    
    print(f"\n📊 Score: {result3['economic_pain']}/40")
    print(f"🎯 Tier: {result3['tier']}")
    print(f"\n📈 Breakdown:")
    print(f"  - Margin Pressure: {result3['breakdown']['margin_pressure']}/15")
    print(f"  - Volume Leverage: {result3['breakdown']['volume_leverage']}/12")
    print(f"  - Leakage Indicators: {result3['breakdown']['leakage_indicators']}/13")
    
    try:
        assert result3['economic_pain'] <= 12, f"❌ FAIL: Cardiology too high: {result3['economic_pain']}"
        assert result3['economic_pain'] >= 8, f"❌ FAIL: Cardiology too low: {result3['economic_pain']}"
        print("\n✅ TEST 3 PASSED")
    except AssertionError as e:
        print(f"\n{e}")
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 ALL PHASE 1 TESTS PASSED!")
    print("=" * 60)
    print("\n✅ Economic Pain scoring is working correctly")
    print("✅ Ready to proceed to Phase 2 (Product-Market Fit)")
    print("\n" + "=" * 60)
    
    return True

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
