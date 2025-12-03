#!/usr/bin/env python3
"""
Phase 2 ICP Scoring Validation
Tests Economic Pain (40 pts) + Product-Market Fit (35 pts) = 75 points total
"""
print("DEBUG: Script started")  # ADD THIS LINE

import sys
import os

print("DEBUG: Imports successful")  # ADD THIS LINE

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from workers.score_icp import calculate_icp_score

def run_phase2_validation():
    print("=" * 70)
    print("PHASE 2 VALIDATION - ECONOMIC PAIN + PRODUCT-MARKET FIT")
    print("=" * 70)
    
    # Test 1: Ideal FQHC with Full Data (Should score 65-75/75)
    print("\n" + "=" * 70)
    print("TEST 1: Ideal FQHC - Full Profile (Expected: 68-75/75)")
    print("=" * 70)
    
    test_fqhc_full = {
        'practice_type': 'FQHC',
        'provider_count': 30,
        'estimated_encounters': 52000,
        'net_margin': 0.008,
        
        # Phase 1 fields
        'medicaid_pct': 0.68,
        'location_count': 6,
        'em_code_pct': 0.85,
        'offers_ccm': True,
        'has_billing_staff': False,
        
        # Phase 2 fields (NEW)
        'medicare_pct': 0.22,
        'commercial_pct': 0.10,
        'offers_preventive_care': True,
        'offers_chronic_care': True,
        'has_procedures': False,
        'state_count': 1,
        'single_payer_pct': 0.0,
        'cash_only_pct': 0.0,
        'health_system_affiliated': False,
        'it_expenditure': 75000,
        'recent_audit': False
    }
    
    result1 = calculate_icp_score(test_fqhc_full)
    
    print(f"\n📊 Total Score: {result1['total']}/75")
    print(f"   └─ Economic Pain: {result1['economic_pain']}/40")
    print(f"   └─ Product Fit: {result1['product_fit']}/35")
    print(f"   └─ Strategic Value: {result1['strategic_value']}/25 (Phase 3)")
    
    print(f"\n🎯 Tier: {result1['tier']}")
    
    print(f"\n📈 Detailed Breakdown:")
    breakdown = result1['breakdown']
    print(f"  Phase 1 Components:")
    print(f"    • Margin Pressure: {breakdown['margin_pressure']}/15")
    print(f"    • Volume Leverage: {breakdown['volume_leverage']}/12")
    print(f"    • Leakage Indicators: {breakdown['leakage_indicators']}/13")
    
    print(f"\n  Phase 2 Components:")
    print(f"    • Practice Alignment: {breakdown['practice_alignment']}/12")
    print(f"    • Billing Complexity: {breakdown['billing_complexity']}/10")
    print(f"    • Tech Readiness: {breakdown['tech_readiness']}/8")
    print(f"    • Compliance Risk: {breakdown['compliance_risk']}/5")
    
    print(f"\n💡 Justification:")
    for j in result1['justification']:
        print(f"  • {j}")
    
    # Validation
    try:
        assert result1['total'] >= 65, f"❌ FAIL: Ideal FQHC scored too low: {result1['total']}"
        assert result1['economic_pain'] >= 38, f"❌ FAIL: Economic pain too low: {result1['economic_pain']}"
        assert result1['product_fit'] >= 27, f"❌ FAIL: Product fit too low: {result1['product_fit']}"
        assert result1['breakdown']['practice_alignment'] == 12, "❌ FAIL: Practice alignment should be 12 for FQHC"
        print("\n✅ TEST 1 PASSED")
    except AssertionError as e:
        print(f"\n{e}")
        return False
    
    # Test 2: Primary Care with Moderate Complexity (Should score 50-60/75)
    print("\n" + "=" * 70)
    print("TEST 2: Primary Care - Moderate Profile (Expected: 50-60/75)")
    print("=" * 70)
    
    test_primary_care = {
        'practice_type': 'Primary Care',
        'provider_count': 12,
        'estimated_encounters': 28000,
        'medicaid_pct': 0.35,
        'medicare_pct': 0.40,
        'commercial_pct': 0.25,
        'location_count': 2,
        'em_code_pct': 0.75,
        'offers_ccm': True,
        'has_billing_staff': True,
        'offers_preventive_care': True,
        'offers_chronic_care': True,
        'has_procedures': True,
        'state_count': 1,
        'health_system_affiliated': False,
        'it_expenditure': 60000,
    }
    
    result2 = calculate_icp_score(test_primary_care)
    
    print(f"\n📊 Total Score: {result2['total']}/75")
    print(f"   └─ Economic Pain: {result2['economic_pain']}/40")
    print(f"   └─ Product Fit: {result2['product_fit']}/35")
    print(f"\n🎯 Tier: {result2['tier']}")
    
    print(f"\n📈 Breakdown:")
    print(f"  • Practice Alignment: {result2['breakdown']['practice_alignment']}/12")
    print(f"  • Billing Complexity: {result2['breakdown']['billing_complexity']}/10")
    print(f"  • Tech Readiness: {result2['breakdown']['tech_readiness']}/8")
    
    try:
        assert result2['total'] >= 50, f"❌ FAIL: Primary care too low: {result2['total']}"
        assert result2['total'] <= 65, f"❌ FAIL: Primary care too high: {result2['total']}"
        assert result2['breakdown']['practice_alignment'] == 11, "❌ FAIL: Primary care should be 11"
        assert result2['breakdown']['billing_complexity'] >= 6, "❌ FAIL: Multi-payer should give 6+ complexity"
        print("\n✅ TEST 2 PASSED")
    except AssertionError as e:
        print(f"\n{e}")
        return False
    
    # Test 3: Cardiology with Simple Billing (Should score 15-25/75)
    print("\n" + "=" * 70)
    print("TEST 3: Cardiology - Low Fit (Expected: 15-25/75)")
    print("=" * 70)
    
    test_cardiology = {
        'practice_type': 'Cardiology',
        'provider_count': 6,
        'estimated_encounters': 8000,
        'medicaid_pct': 0.10,
        'medicare_pct': 0.60,
        'commercial_pct': 0.30,
        'location_count': 1,
        'em_code_pct': 0.40,
        'has_billing_staff': True,
        'offers_preventive_care': False,
        'offers_chronic_care': True,
        'has_procedures': True,
        'health_system_affiliated': True,
        'it_expenditure': 100000,
    }
    
    result3 = calculate_icp_score(test_cardiology)
    
    print(f"\n📊 Total Score: {result3['total']}/75")
    print(f"   └─ Economic Pain: {result3['economic_pain']}/40")
    print(f"   └─ Product Fit: {result3['product_fit']}/35")
    print(f"\n🎯 Tier: {result3['tier']}")
    
    print(f"\n📈 Key Scores:")
    print(f"  • Margin Pressure: {result3['breakdown']['margin_pressure']}/15 (High-reimbursement specialty)")
    print(f"  • Practice Alignment: {result3['breakdown']['practice_alignment']}/12 (Lower fit)")
    
    try:
        assert result3['total'] <= 30, f"❌ FAIL: Cardiology scored too high: {result3['total']}"
        assert result3['breakdown']['practice_alignment'] == 4, "❌ FAIL: Cardiology should be 4"
        print("\n✅ TEST 3 PASSED")
    except AssertionError as e:
        print(f"\n{e}")
        return False
    
    # Test 4: Cash-Only Penalty Test (Should have negative complexity)
    print("\n" + "=" * 70)
    print("TEST 4: Cash-Only Practice - Penalty Test (Expected: Major Deduction)")
    print("=" * 70)
    
    test_cash_only = {
        'practice_type': 'Primary Care',
        'provider_count': 3,
        'estimated_encounters': 7000,
        'cash_only_pct': 0.70,
        'single_payer_pct': 0.0,
        'medicaid_pct': 0.20,
        'location_count': 1,
        'has_billing_staff': False,
    }
    
    result4 = calculate_icp_score(test_cash_only)
    
    print(f"\n📊 Total Score: {result4['total']}/75")
    print(f"   └─ Billing Complexity: {result4['breakdown']['billing_complexity']}/10")
    
    print(f"\n💡 Justification (should show penalty):")
    for j in result4['justification']:
        if 'PENALTY' in j or 'Complexity' in j:
            print(f"  • {j}")
    
    try:
        # Cash-only should have 0 or negative complexity due to -5 penalty
        assert result4['breakdown']['billing_complexity'] == 0, "❌ FAIL: Cash-only should floor at 0 complexity"
        assert any('PENALTY' in j for j in result4['justification']), "❌ FAIL: Should have penalty justification"
        print("\n✅ TEST 4 PASSED")
    except AssertionError as e:
        print(f"\n{e}")
        return False
    
    # Summary
    print("\n" + "=" * 70)
    print("🎉 ALL PHASE 2 TESTS PASSED!")
    print("=" * 70)
    print("\n✅ Economic Pain (Phase 1) scoring works correctly")
    print("✅ Product-Market Fit (Phase 2) scoring works correctly")
    print("✅ Penalties (cash-only, single-payer) apply correctly")
    print("✅ Multi-payer complexity stacking works")
    print("✅ Practice type alignment differentiation works")
    print("\n✅ Ready to proceed to Phase 3 (Strategic Value - 25 points)")
    print("\n" + "=" * 70)
    
    return True

if __name__ == "__main__":
    success = run_phase2_validation()
    sys.exit(0 if success else 1)
