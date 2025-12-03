#!/bin/bash

# organize_files.sh
# This script organizes the project by archiving temporary/debug/test files
# and creating a structured pipeline directory for core workers

set -e  # Exit on error

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
ARCHIVE_DIR="$PROJECT_ROOT/archive_slop"
PIPELINE_DIR="$PROJECT_ROOT/workers/pipeline"

echo "🗂️  Starting project organization..."
echo "Project root: $PROJECT_ROOT"

# Create directories
echo ""
echo "📁 Creating directories..."
mkdir -p "$ARCHIVE_DIR"
mkdir -p "$PIPELINE_DIR"

# Archive test, debug, and investigative scripts from scripts/
echo ""
echo "📦 Archiving temporary/debug/test files from scripts/..."

# Test files
[ -f "scripts/test990.py" ] && mv "scripts/test990.py" "$ARCHIVE_DIR/" && echo "  ✓ test990.py"
[ -f "scripts/test_icp_scoring.py" ] && mv "scripts/test_icp_scoring.py" "$ARCHIVE_DIR/" && echo "  ✓ test_icp_scoring.py"
[ -f "scripts/test_network_scoring.py" ] && mv "scripts/test_network_scoring.py" "$ARCHIVE_DIR/" && echo "  ✓ test_network_scoring.py"
[ -f "scripts/test_phase1_validation.py" ] && mv "scripts/test_phase1_validation.py" "$ARCHIVE_DIR/" && echo "  ✓ test_phase1_validation.py"
[ -f "scripts/test_phase2_validation.py" ] && mv "scripts/test_phase2_validation.py" "$ARCHIVE_DIR/" && echo "  ✓ test_phase2_validation.py"
[ -f "scripts/test_hospital_sas.py" ] && mv "scripts/test_hospital_sas.py" "$ARCHIVE_DIR/" && echo "  ✓ test_hospital_sas.py"
[ -f "scripts/test_hha_integration.py" ] && mv "scripts/test_hha_integration.py" "$ARCHIVE_DIR/" && echo "  ✓ test_hha_integration.py"
[ -f "scripts/test_ccn_npi_crosswalk.py" ] && mv "scripts/test_ccn_npi_crosswalk.py" "$ARCHIVE_DIR/" && echo "  ✓ test_ccn_npi_crosswalk.py"
[ -f "scripts/test_strategic_integration.py" ] && mv "scripts/test_strategic_integration.py" "$ARCHIVE_DIR/" && echo "  ✓ test_strategic_integration.py"
[ -f "scripts/test_hrsa_integration.py" ] && mv "scripts/test_hrsa_integration.py" "$ARCHIVE_DIR/" && echo "  ✓ test_hrsa_integration.py"

# Debug files
[ -f "scripts/debug_entities.py" ] && mv "scripts/debug_entities.py" "$ARCHIVE_DIR/" && echo "  ✓ debug_entities.py"
[ -f "scripts/debug_fqhc_match.py" ] && mv "scripts/debug_fqhc_match.py" "$ARCHIVE_DIR/" && echo "  ✓ debug_fqhc_match.py"
[ -f "scripts/debug_data_columns.py" ] && mv "scripts/debug_data_columns.py" "$ARCHIVE_DIR/" && echo "  ✓ debug_data_columns.py"
[ -f "scripts/debug_enriched_columns.py" ] && mv "scripts/debug_enriched_columns.py" "$ARCHIVE_DIR/" && echo "  ✓ debug_enriched_columns.py"

# Investigation/inspection files
[ -f "scripts/investigate_subsegments.py" ] && mv "scripts/investigate_subsegments.py" "$ARCHIVE_DIR/" && echo "  ✓ investigate_subsegments.py"
[ -f "scripts/investigate_subsegments_v2.py" ] && mv "scripts/investigate_subsegments_v2.py" "$ARCHIVE_DIR/" && echo "  ✓ investigate_subsegments_v2.py"
[ -f "scripts/investigate_hcris_structure.py" ] && mv "scripts/investigate_hcris_structure.py" "$ARCHIVE_DIR/" && echo "  ✓ investigate_hcris_structure.py"
[ -f "scripts/inspect_staging.py" ] && mv "scripts/inspect_staging.py" "$ARCHIVE_DIR/" && echo "  ✓ inspect_staging.py"
[ -f "scripts/inspect_seed.py" ] && mv "scripts/inspect_seed.py" "$ARCHIVE_DIR/" && echo "  ✓ inspect_seed.py"
[ -f "scripts/inspect_hospital_sas.py" ] && mv "scripts/inspect_hospital_sas.py" "$ARCHIVE_DIR/" && echo "  ✓ inspect_hospital_sas.py"
[ -f "scripts/inspect_hha_reports.py" ] && mv "scripts/inspect_hha_reports.py" "$ARCHIVE_DIR/" && echo "  ✓ inspect_hha_reports.py"
[ -f "scripts/inspect_hha_detailed.py" ] && mv "scripts/inspect_hha_detailed.py" "$ARCHIVE_DIR/" && echo "  ✓ inspect_hha_detailed.py"
[ -f "scripts/examine_g3_columns.py" ] && mv "scripts/examine_g3_columns.py" "$ARCHIVE_DIR/" && echo "  ✓ examine_g3_columns.py"

# Diagnostic files
[ -f "scripts/dev_smoke.py" ] && mv "scripts/dev_smoke.py" "$ARCHIVE_DIR/" && echo "  ✓ dev_smoke.py"
[ -f "scripts/diagnose_score_compression.py" ] && mv "scripts/diagnose_score_compression.py" "$ARCHIVE_DIR/" && echo "  ✓ diagnose_score_compression.py"
[ -f "scripts/diagnose_revenue_lift.py" ] && mv "scripts/diagnose_revenue_lift.py" "$ARCHIVE_DIR/" && echo "  ✓ diagnose_revenue_lift.py"
[ -f "scripts/data_diagnostic_tool.py" ] && mv "scripts/data_diagnostic_tool.py" "$ARCHIVE_DIR/" && echo "  ✓ data_diagnostic_tool.py"

# Verification/check files
[ -f "scripts/verify_data_depth.py" ] && mv "scripts/verify_data_depth.py" "$ARCHIVE_DIR/" && echo "  ✓ verify_data_depth.py"
[ -f "scripts/verify_data_assets.py" ] && mv "scripts/verify_data_assets.py" "$ARCHIVE_DIR/" && echo "  ✓ verify_data_assets.py"
[ -f "scripts/check_segment_counts.py" ] && mv "scripts/check_segment_counts.py" "$ARCHIVE_DIR/" && echo "  ✓ check_segment_counts.py"
[ -f "scripts/check_overlap.py" ] && mv "scripts/check_overlap.py" "$ARCHIVE_DIR/" && echo "  ✓ check_overlap.py"
[ -f "scripts/check_psych_data.py" ] && mv "scripts/check_psych_data.py" "$ARCHIVE_DIR/" && echo "  ✓ check_psych_data.py"
[ -f "scripts/check_address.py" ] && mv "scripts/check_address.py" "$ARCHIVE_DIR/" && echo "  ✓ check_address.py"

# Assessment/audit/analysis files
[ -f "scripts/assess_scoring_readiness.py" ] && mv "scripts/assess_scoring_readiness.py" "$ARCHIVE_DIR/" && echo "  ✓ assess_scoring_readiness.py"
[ -f "scripts/audit_scoring_results.py" ] && mv "scripts/audit_scoring_results.py" "$ARCHIVE_DIR/" && echo "  ✓ audit_scoring_results.py"
[ -f "scripts/audit_scoring_logic.py" ] && mv "scripts/audit_scoring_logic.py" "$ARCHIVE_DIR/" && echo "  ✓ audit_scoring_logic.py"
[ -f "scripts/audit_filtered_orgs.py" ] && mv "scripts/audit_filtered_orgs.py" "$ARCHIVE_DIR/" && echo "  ✓ audit_filtered_orgs.py"
[ -f "scripts/audit_excluded_giants.py" ] && mv "scripts/audit_excluded_giants.py" "$ARCHIVE_DIR/" && echo "  ✓ audit_excluded_giants.py"
[ -f "scripts/analyze_tier2_profile.py" ] && mv "scripts/analyze_tier2_profile.py" "$ARCHIVE_DIR/" && echo "  ✓ analyze_tier2_profile.py"
[ -f "scripts/analyze_current_data.py" ] && mv "scripts/analyze_current_data.py" "$ARCHIVE_DIR/" && echo "  ✓ analyze_current_data.py"

# Move core pipeline workers to workers/pipeline/
echo ""
echo "🔧 Organizing core pipeline files into workers/pipeline/..."

# Ingestion
[ -f "workers/ingest_bulk.py" ] && mv "workers/ingest_bulk.py" "$PIPELINE_DIR/" && echo "  ✓ ingest_bulk.py"
[ -f "workers/ingest_api.py" ] && mv "workers/ingest_api.py" "$PIPELINE_DIR/" && echo "  ✓ ingest_api.py"

# Enrichment/Merging
[ -f "workers/enrich_duckdb.py" ] && mv "workers/enrich_duckdb.py" "$PIPELINE_DIR/" && echo "  ✓ enrich_duckdb.py"
[ -f "workers/enrich_oig_leie.py" ] && mv "workers/enrich_oig_leie.py" "$PIPELINE_DIR/" && echo "  ✓ enrich_oig_leie.py"
[ -f "workers/enrich_features.py" ] && mv "workers/enrich_features.py" "$PIPELINE_DIR/" && echo "  ✓ enrich_features.py"

# Scoring
[ -f "workers/score_icp.py" ] && mv "workers/score_icp.py" "$PIPELINE_DIR/" && echo "  ✓ score_icp.py"
[ -f "workers/score_icp_v8.py" ] && mv "workers/score_icp_v8.py" "$PIPELINE_DIR/" && echo "  ✓ score_icp_v8.py"
[ -f "workers/score_icf.py" ] && mv "workers/score_icf.py" "$PIPELINE_DIR/" && echo "  ✓ score_icf.py"
[ -f "workers/score_leads.py" ] && mv "workers/score_leads.py" "$PIPELINE_DIR/" && echo "  ✓ score_leads.py"
[ -f "workers/score_orgs.py" ] && mv "workers/score_orgs.py" "$PIPELINE_DIR/" && echo "  ✓ score_orgs.py"
[ -f "workers/score_verified_orgs.py" ] && mv "workers/score_verified_orgs.py" "$PIPELINE_DIR/" && echo "  ✓ score_verified_orgs.py"

# Pipeline orchestration
[ -f "workers/pipeline_main.py" ] && mv "workers/pipeline_main.py" "$PIPELINE_DIR/" && echo "  ✓ pipeline_main.py"

# Create __init__.py in pipeline directory
touch "$PIPELINE_DIR/__init__.py"
echo "  ✓ Created __init__.py"

echo ""
echo "✅ Organization complete!"
echo ""
echo "Summary:"
echo "  - Archived files: archive_slop/"
echo "  - Pipeline files: workers/pipeline/"
echo ""
echo "Files remaining in workers/:"
echo "  - config.py, utils.py, taxonomy_utils.py (utilities)"
echo "  - scrape_*.py (scrapers)"
echo "  - mine_*.py (data mining scripts)"
echo "  - extract_*.py, patch_*.py (auxiliary scripts)"
