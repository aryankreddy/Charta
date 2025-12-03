"""
Unit tests for the ICP scoring engine, specifically for the
`calculate_row_score` function and the "Therapy Relevance Gate" logic.
"""
import pytest
import pandas as pd
import sys
import os

# Add parent directory to path to allow module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from workers.pipeline.score_icp_production import calculate_row_score

@pytest.fixture
def base_clinic_data():
    """Provides a base dictionary for a clinic row with default values."""
    return {
        'total_revenue': 5_000_000,
        'services_count': 10000,
        'final_volume': 10000,
        'volume_source': 'CLAIMS',
        'undercoding_ratio': 0.6, # Represents good E&M performance (low pain)
        'psych_risk_ratio': 0.2,    # Represents significant therapy undercoding (high pain)
        'total_psych_codes': 0,     # Default to 0
        'is_aco_participant': 'false',
        'risk_compliance_flag': 'false',
        'oig_leie_flag': 'false',
        'npi_count': 10,
        'site_count': 1,
        'segment_label': 'Private Practice',
        'fqhc_flag': 0,
        'avg_mips_score': 75,
        'is_hpsa': 'false',
        'is_mua': 'false',
        'org_name': 'Test Clinic'
    }

def test_therapy_gate_closes_for_irrelevant_clinic(base_clinic_data):
    """
    Tests that a non-behavioral clinic with few psych codes has its
    therapy pain signal ignored and is scored on E&M undercoding instead.
    """
    # This clinic has a high potential therapy pain score (psych_risk_ratio=0.2)
    # but very few actual psych codes.
    cardiology_clinic = base_clinic_data.copy()
    cardiology_clinic.update({
        'segment_label': 'Private Practice',
        'org_name': 'Cardiology Associates',
        'total_psych_codes': 10, # Below the 50 threshold
        'undercoding_ratio': 0.6 # Good E&M performance = low E&M pain
    })
    
    row = pd.Series(cardiology_clinic)
    result = calculate_row_score(row)
    
    # The therapy pain signal should be gated (ignored)
    # The pain score should be based on the low E&M undercoding pain
    # score_undercoding_continuous(0.6) returns 10
    assert result['score_pain_total'] == 10
    assert "undercoding" in result['score_reasoning_pain'].lower()
    assert "therapy" not in result['score_reasoning_pain'].lower() or "secondary" in result['score_reasoning_pain'].lower()

def test_therapy_gate_opens_for_relevant_clinic(base_clinic_data):
    """
    Tests that a non-behavioral clinic with sufficient psych codes has its
    therapy pain signal correctly evaluated.
    """
    # This clinic is a general practice but has a significant number of therapy codes.
    # Its therapy pain should be higher than its E&M pain.
    general_practice_clinic = base_clinic_data.copy()
    general_practice_clinic.update({
        'segment_label': 'Private Practice',
        'org_name': 'Community Health Practice',
        'total_psych_codes': 100, # Above the 50 threshold
        'psych_risk_ratio': 0.2,  # High therapy pain signal
        'undercoding_ratio': 0.6    # Low E&M pain signal
    })

    row = pd.Series(general_practice_clinic)
    result = calculate_row_score(row)
    
    # The therapy pain score should be calculated and should dominate the E&M score
    # score_psych_risk_continuous(0.2) returns 40
    # score_undercoding_continuous(0.6) returns 10
    assert result['score_pain_total'] == 40
    assert "therapy coding dominates" in result['score_reasoning_pain']

def test_behavioral_track_unaffected_by_gate(base_clinic_data):
    """
    Tests that a clinic on the BEHAVIORAL track is always scored on therapy
    pain, regardless of the psych code volume.
    """
    # This is a dedicated behavioral clinic, so it should always be scored on therapy pain.
    behavioral_clinic = base_clinic_data.copy()
    behavioral_clinic.update({
        'segment_label': 'Behavioral Health',
        'org_name': 'Mindful Counseling Center',
        'total_psych_codes': 25, # Below the 50 threshold, but shouldn't matter
        'psych_risk_ratio': 0.25 # High therapy pain signal
    })

    row = pd.Series(behavioral_clinic)
    result = calculate_row_score(row)

    # Should be on the BEHAVIORAL track and scored on psych risk
    assert result['scoring_track'] == 'BEHAVIORAL'
    # score_psych_risk_continuous(0.25) is 40
    assert result['score_pain_total'] >= 35 # It should be high
    assert "therapy undercoding" in result['score_reasoning_pain']

def test_hospital_revenue_downgrade(base_clinic_data):
    """
    Tests that a clinic classified as a 'Hospital' is downgraded to
    'Ambulatory Center' if its revenue is below $10M.
    """
    low_revenue_hospital = base_clinic_data.copy()
    low_revenue_hospital.update({
        'segment_label': 'Hospital',
        'total_revenue': 5_000_000, # Below the $10M threshold
    })

    row = pd.Series(low_revenue_hospital)
    result = calculate_row_score(row)

    # The segment label should be downgraded
    assert result['segment_label'] == 'Ambulatory Center'

def test_hospital_revenue_no_downgrade(base_clinic_data):
    """
    Tests that a 'Hospital' with revenue >= $10M is NOT downgraded.
    """
    high_revenue_hospital = base_clinic_data.copy()
    high_revenue_hospital.update({
        'segment_label': 'Hospital',
        'total_revenue': 25_000_000, # Above the $10M threshold
    })

    row = pd.Series(high_revenue_hospital)
    result = calculate_row_score(row)

    # The segment label should remain 'Hospital'
    assert result['segment_label'] == 'Hospital'