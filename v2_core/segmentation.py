"""
Segmentation Module - v2 Clean Implementation

This module implements strict, mutually exclusive segmentation for healthcare clinics.

Segments:
- A: Specialty/Behavioral (Home Health, Hospice, Behavioral Health)
- B: FQHC/HRSA (Federally Qualified Health Centers, Rural Health Clinics)
- C: Health Systems/Hospitals (Large multi-specialty groups, hospital-affiliated)
- D: Other (Everything else)

Priority: B > A > C > D (to prevent double-counting)
"""

from typing import Dict, Any, Optional, List
import re


# ============================================================================
# TAXONOMY CODE PATTERNS
# ============================================================================

# Segment B: FQHC/HRSA
SEGMENT_B_TAXONOMY_CODES = {
    "261QF0400X",  # Federally Qualified Health Center (FQHC)
    "261QR1300X",  # Rural Health Clinic
}

# Segment A: Specialty/Behavioral
SEGMENT_A_TAXONOMY_PATTERNS = [
    # Home Health
    r"^251G",  # Home Health Agency
    r"^251E",  # Home Infusion
    # Hospice & Palliative
    r"^251F",  # Hospice
    r"H0002X$",  # Hospice and Palliative Medicine (any specialty)
    # Behavioral Health
    r"^2084",  # Psychiatry & Neurology
    r"^101Y",  # Counselor
    r"^103T",  # Psychologist
    r"^106H",  # Marriage & Family Therapist
    r"^261QM",  # Mental Health Clinic
    r"^261QS",  # Substance Abuse Clinic
]

# Segment C: Health Systems/Hospitals
SEGMENT_C_TAXONOMY_PATTERNS = [
    r"^282N",  # General Acute Care Hospital
    r"^281P",  # Chronic Disease Hospital
    r"^283",   # Hospital Units (Psychiatric, Rehabilitation, etc.)
]

SEGMENT_C_TAXONOMY_CODES = {
    "208M00000X",  # Hospitalist
}

# Keywords for text-based matching
SEGMENT_B_KEYWORDS = {
    "fqhc",
    "federally qualified",
    "rural health clinic",
    "hrsa",
    "community health center",
}

SEGMENT_A_KEYWORDS = {
    "behavioral health",
    "mental health",
    "substance abuse",
    "psychiatry",
    "psychiatric",
    "home health",
    "hospice",
    "palliative",
}

SEGMENT_C_KEYWORDS = {
    "hospital",
    "health system",
    "medical center",
    "health network",
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_text(value: Any) -> str:
    """Normalize text to lowercase and strip whitespace."""
    if value is None or (isinstance(value, float) and value != value):  # NaN check
        return ""
    return str(value).strip().lower()


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int."""
    try:
        if value is None or (isinstance(value, float) and value != value):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    try:
        if value is None or (isinstance(value, float) and value != value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def extract_taxonomy_codes(taxonomy_field: Any) -> List[str]:
    """
    Extract taxonomy codes from a field that may contain:
    - Single code: "251G00000X"
    - Multiple codes separated by semicolons: "251G00000X;261QF0400X"
    - Empty/null values
    
    Returns a list of taxonomy codes.
    """
    taxonomy_str = normalize_text(taxonomy_field)
    if not taxonomy_str:
        return []
    
    # Split by semicolon and clean up
    codes = [code.strip().upper() for code in taxonomy_str.split(";")]
    return [code for code in codes if code and len(code) == 10]  # NUCC codes are 10 chars


def matches_taxonomy_pattern(taxonomy_codes: List[str], patterns: List[str]) -> bool:
    """Check if any taxonomy code matches any of the given regex patterns."""
    for code in taxonomy_codes:
        for pattern in patterns:
            if re.match(pattern, code):
                return True
    return False


def contains_keywords(text: str, keywords: set) -> bool:
    """Check if text contains any of the keywords."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)


# ============================================================================
# MAIN SEGMENTATION FUNCTION
# ============================================================================

def classify_segment(clinic_data: Dict[str, Any]) -> str:
    """
    Classify a clinic into one of four segments: A, B, C, or D.
    
    Priority: B > A > C > D
    
    Args:
        clinic_data: Dictionary containing clinic information with keys:
            - fqhc_flag: int (1 if FQHC, 0 otherwise)
            - taxonomy: str (semicolon-separated taxonomy codes)
            - segment_label: str (existing segment label, if any)
            - org_name: str (organization name)
            - npi_count: int (number of providers)
            - site_count: int (number of sites)
    
    Returns:
        Segment letter: "A", "B", "C", or "D"
    """
    
    # Extract data
    fqhc_flag = safe_int(clinic_data.get("fqhc_flag", 0))
    taxonomy_codes = extract_taxonomy_codes(clinic_data.get("taxonomy", ""))
    segment_label = normalize_text(clinic_data.get("segment_label", ""))
    org_name = normalize_text(clinic_data.get("org_name", ""))
    npi_count = safe_int(clinic_data.get("npi_count", 0))
    site_count = safe_int(clinic_data.get("site_count", 0))
    
    # ========================================================================
    # PRIORITY 0: HOSPITAL OVERRIDE (Prevent hospitals from being FQHCs)
    # ========================================================================
    # CRITICAL FIX: Some organizations have fqhc_flag = 1 incorrectly
    # Hospitals/Medical Centers should NEVER be Segment B, even with bad flags

    HOSPITAL_OVERRIDE_KEYWORDS = {
        "hospital",
        "medical center",
        "health system",
        "hospital district"
    }
    if contains_keywords(org_name, HOSPITAL_OVERRIDE_KEYWORDS):
        # Skip FQHC checks, will be classified as Segment C later
        pass
    else:
        # ====================================================================
        # PRIORITY 1: SEGMENT B (FQHC/HRSA)
        # ====================================================================

        # Check FQHC flag
        if fqhc_flag >= 1:
            return "B"

        # Check taxonomy codes
        for code in taxonomy_codes:
            if code in SEGMENT_B_TAXONOMY_CODES:
                return "B"

        # Check keywords in segment_label or org_name
        if contains_keywords(segment_label, SEGMENT_B_KEYWORDS):
            return "B"
        if contains_keywords(org_name, SEGMENT_B_KEYWORDS):
            return "B"
    
    # ========================================================================
    # PRIORITY 2: SEGMENT A (SPECIALTY/BEHAVIORAL)
    # ========================================================================
    
    # Check taxonomy patterns
    if matches_taxonomy_pattern(taxonomy_codes, SEGMENT_A_TAXONOMY_PATTERNS):
        return "A"
    
    # Check keywords in segment_label or org_name
    if contains_keywords(segment_label, SEGMENT_A_KEYWORDS):
        return "A"
    if contains_keywords(org_name, SEGMENT_A_KEYWORDS):
        return "A"
    
    # ========================================================================
    # PRIORITY 3: SEGMENT C (HEALTH SYSTEMS/HOSPITALS)
    # ========================================================================
    
    # Check large provider count
    if npi_count >= 100:
        return "C"
    
    # Check large site count
    if site_count >= 10:
        return "C"
    
    # Check taxonomy patterns
    if matches_taxonomy_pattern(taxonomy_codes, SEGMENT_C_TAXONOMY_PATTERNS):
        return "C"
    
    # Check specific taxonomy codes
    for code in taxonomy_codes:
        if code in SEGMENT_C_TAXONOMY_CODES:
            return "C"
    
    # Check keywords in segment_label or org_name
    if contains_keywords(segment_label, SEGMENT_C_KEYWORDS):
        return "C"
    if contains_keywords(org_name, SEGMENT_C_KEYWORDS):
        return "C"
    
    # ========================================================================
    # DEFAULT: SEGMENT D (OTHER)
    # ========================================================================
    
    return "D"


def get_segment_description(segment: str) -> str:
    """Get a human-readable description of a segment."""
    descriptions = {
        "A": "Specialty/Behavioral (Home Health, Hospice, Behavioral Health)",
        "B": "FQHC/HRSA (Federally Qualified Health Centers, Rural Health Clinics)",
        "C": "Health Systems/Hospitals (Large multi-specialty groups, hospital-affiliated)",
        "D": "Other (General practices, small clinics, specialty not in A/B/C)",
    }
    return descriptions.get(segment, "Unknown")


# ============================================================================
# BATCH PROCESSING
# ============================================================================

def classify_segments_batch(clinics: List[Dict[str, Any]]) -> List[str]:
    """
    Classify multiple clinics at once.
    
    Args:
        clinics: List of clinic dictionaries
    
    Returns:
        List of segment letters in the same order as input
    """
    return [classify_segment(clinic) for clinic in clinics]
