"""
Test Suite for Segmentation Module

Tests the 4-segment classification logic (A/B/C/D) with various scenarios
including pure segments, overlaps, edge cases, and missing data.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from v2_core.segmentation import (
    classify_segment,
    get_segment_description,
    extract_taxonomy_codes,
    matches_taxonomy_pattern,
    contains_keywords,
    SEGMENT_A_TAXONOMY_PATTERNS,
    SEGMENT_B_KEYWORDS,
)


class TestTaxonomyExtraction:
    """Test taxonomy code extraction and parsing."""
    
    def test_single_code(self):
        result = extract_taxonomy_codes("251G00000X")
        assert result == ["251G00000X"]
    
    def test_multiple_codes(self):
        result = extract_taxonomy_codes("251G00000X;261QF0400X;208M00000X")
        assert result == ["251G00000X", "261QF0400X", "208M00000X"]
    
    def test_empty_string(self):
        result = extract_taxonomy_codes("")
        assert result == []
    
    def test_none_value(self):
        result = extract_taxonomy_codes(None)
        assert result == []
    
    def test_whitespace_handling(self):
        result = extract_taxonomy_codes(" 251G00000X ; 261QF0400X ")
        assert result == ["251G00000X", "261QF0400X"]


class TestSegmentB:
    """Test Segment B (FQHC/HRSA) classification."""
    
    def test_fqhc_flag(self):
        """Clinic with FQHC flag should be Segment B."""
        clinic = {
            "fqhc_flag": 1,
            "taxonomy": "",
            "segment_label": "",
            "org_name": "Test Clinic",
            "npi_count": 5,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "B"
    
    def test_fqhc_taxonomy(self):
        """Clinic with FQHC taxonomy code should be Segment B."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "261QF0400X",
            "segment_label": "",
            "org_name": "Test Clinic",
            "npi_count": 5,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "B"
    
    def test_rural_health_taxonomy(self):
        """Clinic with Rural Health taxonomy should be Segment B."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "261QR1300X",
            "segment_label": "",
            "org_name": "Test Clinic",
            "npi_count": 5,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "B"
    
    def test_fqhc_keyword_in_name(self):
        """Clinic with 'FQHC' in name should be Segment B."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "",
            "segment_label": "",
            "org_name": "Community FQHC Health Center",
            "npi_count": 5,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "B"
    
    def test_rural_health_keyword(self):
        """Clinic with 'rural health clinic' in segment label should be Segment B."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "",
            "segment_label": "rural health clinic",
            "org_name": "Test Clinic",
            "npi_count": 5,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "B"


class TestSegmentA:
    """Test Segment A (Specialty/Behavioral) classification."""
    
    def test_home_health_taxonomy(self):
        """Clinic with Home Health taxonomy should be Segment A."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "251G00000X",
            "segment_label": "",
            "org_name": "Test Home Health",
            "npi_count": 5,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "A"
    
    def test_hospice_taxonomy(self):
        """Clinic with Hospice taxonomy should be Segment A."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "251F00000X",
            "segment_label": "",
            "org_name": "Test Hospice",
            "npi_count": 5,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "A"
    
    def test_behavioral_health_taxonomy(self):
        """Clinic with Behavioral Health taxonomy should be Segment A."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "2084P0804X",  # Psychiatry
            "segment_label": "",
            "org_name": "Test Mental Health",
            "npi_count": 5,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "A"
    
    def test_palliative_medicine_taxonomy(self):
        """Clinic with Palliative Medicine taxonomy should be Segment A."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "2080H0002X",  # Hospice and Palliative Medicine
            "segment_label": "",
            "org_name": "Test Palliative Care",
            "npi_count": 5,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "A"
    
    def test_home_health_keyword(self):
        """Clinic with 'home health' in name should be Segment A."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "",
            "segment_label": "",
            "org_name": "ABC Home Health Services",
            "npi_count": 5,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "A"
    
    def test_behavioral_health_keyword(self):
        """Clinic with 'behavioral health' in segment label should be Segment A."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "",
            "segment_label": "behavioral health clinic",
            "org_name": "Test Clinic",
            "npi_count": 5,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "A"


class TestSegmentC:
    """Test Segment C (Health Systems/Hospitals) classification."""
    
    def test_large_provider_count(self):
        """Clinic with 100+ providers should be Segment C."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "",
            "segment_label": "",
            "org_name": "Large Medical Group",
            "npi_count": 150,
            "site_count": 5,
        }
        assert classify_segment(clinic) == "C"
    
    def test_large_site_count(self):
        """Clinic with 10+ sites should be Segment C."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "",
            "segment_label": "",
            "org_name": "Multi-Site Health System",
            "npi_count": 50,
            "site_count": 15,
        }
        assert classify_segment(clinic) == "C"
    
    def test_hospital_taxonomy(self):
        """Clinic with Hospital taxonomy should be Segment C."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "282N00000X",  # General Acute Care Hospital
            "segment_label": "",
            "org_name": "Test Hospital",
            "npi_count": 50,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "C"
    
    def test_hospitalist_taxonomy(self):
        """Clinic with Hospitalist taxonomy should be Segment C."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "208M00000X",
            "segment_label": "",
            "org_name": "Hospitalist Group",
            "npi_count": 20,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "C"
    
    def test_hospital_keyword(self):
        """Clinic with 'hospital' in name should be Segment C."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "",
            "segment_label": "",
            "org_name": "Memorial Hospital",
            "npi_count": 50,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "C"
    
    def test_health_system_keyword(self):
        """Clinic with 'health system' in segment label should be Segment C."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "",
            "segment_label": "health system",
            "org_name": "Test Clinic",
            "npi_count": 50,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "C"


class TestSegmentD:
    """Test Segment D (Other) classification."""
    
    def test_small_primary_care(self):
        """Small primary care clinic should be Segment D."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "207Q00000X",  # Family Medicine
            "segment_label": "primary care",
            "org_name": "Family Practice Associates",
            "npi_count": 3,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "D"
    
    def test_specialty_not_in_abc(self):
        """Specialty clinic not in A/B/C should be Segment D."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "207V00000X",  # Obstetrics & Gynecology
            "segment_label": "obstetrics",
            "org_name": "Women's Health Clinic",
            "npi_count": 5,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "D"
    
    def test_missing_data(self):
        """Clinic with missing data should default to Segment D."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "",
            "segment_label": "",
            "org_name": "",
            "npi_count": 0,
            "site_count": 0,
        }
        assert classify_segment(clinic) == "D"


class TestPriorityLogic:
    """Test that priority logic B > A > C > D works correctly."""
    
    def test_fqhc_with_home_health(self):
        """FQHC with Home Health taxonomy should be Segment B (B > A)."""
        clinic = {
            "fqhc_flag": 1,
            "taxonomy": "251G00000X",  # Home Health
            "segment_label": "home health",
            "org_name": "FQHC Home Health",
            "npi_count": 5,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "B"
    
    def test_fqhc_with_hospital(self):
        """FQHC with Hospital taxonomy should be Segment B (B > C)."""
        clinic = {
            "fqhc_flag": 1,
            "taxonomy": "282N00000X",  # Hospital
            "segment_label": "",
            "org_name": "FQHC Hospital",
            "npi_count": 150,
            "site_count": 10,
        }
        assert classify_segment(clinic) == "B"
    
    def test_home_health_with_hospital(self):
        """Home Health with 100+ providers should be Segment A (A > C)."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "251G00000X",  # Home Health
            "segment_label": "home health",
            "org_name": "Large Home Health Network",
            "npi_count": 150,
            "site_count": 10,
        }
        assert classify_segment(clinic) == "A"
    
    def test_behavioral_with_large_size(self):
        """Behavioral Health with large size should be Segment A (A > C)."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "2084P0804X",  # Psychiatry
            "segment_label": "behavioral health",
            "org_name": "Mental Health Hospital",
            "npi_count": 200,
            "site_count": 15,
        }
        assert classify_segment(clinic) == "A"


class TestEdgeCases:
    """Test edge cases and unusual inputs."""
    
    def test_multiple_taxonomy_codes(self):
        """Clinic with multiple taxonomy codes should use first match."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "207Q00000X;251G00000X;282N00000X",  # Family Med, Home Health, Hospital
            "segment_label": "",
            "org_name": "Multi-Service Clinic",
            "npi_count": 10,
            "site_count": 1,
        }
        # Should be A because Home Health (251G) is checked before Hospital (282N)
        assert classify_segment(clinic) == "A"
    
    def test_case_insensitive_keywords(self):
        """Keywords should be case-insensitive."""
        clinic = {
            "fqhc_flag": 0,
            "taxonomy": "",
            "segment_label": "",
            "org_name": "HOME HEALTH SERVICES",
            "npi_count": 5,
            "site_count": 1,
        }
        assert classify_segment(clinic) == "A"
    
    def test_nan_values(self):
        """Handle NaN values gracefully."""
        import math
        clinic = {
            "fqhc_flag": math.nan,
            "taxonomy": math.nan,
            "segment_label": math.nan,
            "org_name": math.nan,
            "npi_count": math.nan,
            "site_count": math.nan,
        }
        assert classify_segment(clinic) == "D"
    
    def test_none_values(self):
        """Handle None values gracefully."""
        clinic = {
            "fqhc_flag": None,
            "taxonomy": None,
            "segment_label": None,
            "org_name": None,
            "npi_count": None,
            "site_count": None,
        }
        assert classify_segment(clinic) == "D"


class TestSegmentDescriptions:
    """Test segment description helper function."""
    
    def test_all_segments(self):
        """All segments should have descriptions."""
        assert "Specialty" in get_segment_description("A")
        assert "FQHC" in get_segment_description("B")
        assert "Hospital" in get_segment_description("C")
        assert "Other" in get_segment_description("D")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
