"""
Test suite for the feature enrichment pipeline, specifically the `assign_segment` function.
"""

import pytest
import pandas as pd
from workers.pipeline.enrich_features import assign_segment

# Test cases for the `assign_segment` function

def test_fqhc_segment():
    """Test that a clinic with an FQHC flag is correctly identified."""
    row = pd.Series({"fqhc_flag": 1})
    assert assign_segment(row) == "FQHC"

def test_hospital_by_taxonomy():
    """Test that a hospital is identified by its taxonomy code."""
    row = pd.Series({"taxonomy": "282N00000X", "fqhc_flag": 0})
    assert assign_segment(row) == "Hospital"

def test_hospital_by_name():
    """Test that a hospital is identified by keywords in its name."""
    row = pd.Series({"org_name": "GENERAL HOSPITAL", "fqhc_flag": 0, "taxonomy": ""})
    assert assign_segment(row) == "Hospital"

def test_urgent_care_by_taxonomy():
    """Test that an urgent care center is identified by its taxonomy code."""
    row = pd.Series({"taxonomy": "261QU0200X", "fqhc_flag": 0})
    assert assign_segment(row) == "Urgent Care"

def test_private_practice_by_taxonomy():
    """Test that a private practice is identified by its taxonomy code."""
    row = pd.Series({"taxonomy": "207Q00000X", "fqhc_flag": 0}) # Family Medicine
    assert assign_segment(row) == "Private Practice"

def test_behavioral_health_by_taxonomy():
    """Test that a behavioral health clinic is identified by its taxonomy code."""
    row = pd.Series({"taxonomy": "101Y00000X", "fqhc_flag": 0}) # Counseling
    assert assign_segment(row) == "Behavioral Health"

def test_home_health_by_taxonomy():
    """Test that a home health agency is identified by its taxonomy code."""
    row = pd.Series({"taxonomy": "251E00000X", "fqhc_flag": 0})
    assert assign_segment(row) == "Home Health"

def test_ambulatory_clinic_by_taxonomy():
    """Test that an ambulatory clinic is identified by its taxonomy code."""
    row = pd.Series({"taxonomy": "261Z00000X", "fqhc_flag": 0}) # Physical Therapy
    assert assign_segment(row) == "Ambulatory Clinic"

def test_name_fallback_urgent_care():
    """Test the name-based fallback for urgent care."""
    row = pd.Series({"org_name": "Community Urgent Care", "fqhc_flag": 0, "taxonomy": ""})
    assert assign_segment(row) == "Urgent Care"

def test_default_to_multispecialty():
    """Test that a clinic with no other indicators defaults to Multi-specialty."""
    row = pd.Series({"org_name": "The Clinic", "fqhc_flag": 0, "taxonomy": ""})
    assert assign_segment(row) == "Multi-specialty"

def test_taxonomy_priority_over_name():
    """Test that taxonomy code takes priority over name-based keywords."""
    row = pd.Series({"org_name": "Mental Health Hospital", "taxonomy": "282N00000X", "fqhc_flag": 0})
    assert assign_segment(row) == "Hospital"

def test_fqhc_priority():
    """Test that the FQHC flag takes priority over all other rules."""
    row = pd.Series({"org_name": "General Hospital", "taxonomy": "282N00000X", "fqhc_flag": 1})
    assert assign_segment(row) == "FQHC"
