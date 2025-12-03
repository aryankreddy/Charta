#!/bin/bash
# scripts/run_full_pipeline.sh
# Full pipeline orchestration with smart caching
#
# Usage:
#   ./scripts/run_full_pipeline.sh           # Run with 7-day cache
#   ./scripts/run_full_pipeline.sh --force   # Force re-run all miners

set -e  # Exit on error

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGING_DIR="$PROJECT_ROOT/data/curated/staging"
MAX_AGE_DAYS=7

echo "🚀 Charta Pipeline Orchestration"
echo "================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo "Staging dir: $STAGING_DIR"
echo ""

# Parse arguments
FORCE_RERUN=false
if [[ "$1" == "--force" ]]; then
    FORCE_RERUN=true
    echo "⚠️  FORCE MODE: Will re-run all miners regardless of cache"
    echo ""
fi

# Function to check file age
check_file_age() {
    local file=$1
    local max_days=$2

    if [[ ! -f "$file" ]]; then
        echo "MISSING"
        return 1
    fi

    if [[ "$FORCE_RERUN" == true ]]; then
        echo "FORCE"
        return 1
    fi

    # Get file age in days (macOS and Linux compatible)
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        local file_time=$(stat -f %m "$file")
    else
        # Linux
        local file_time=$(stat -c %Y "$file")
    fi

    local current_time=$(date +%s)
    local age_seconds=$((current_time - file_time))
    local age_days=$((age_seconds / 86400))

    if [[ $age_days -gt $max_days ]]; then
        echo "STALE (${age_days}d old)"
        return 1
    else
        echo "FRESH (${age_days}d old)"
        return 0
    fi
}

# Step 1: CPT Code Mining (Undercoding Metrics)
echo "📊 Step 1: CPT Code Mining"
echo "─────────────────────────────"
UNDERCODING_FILE="$STAGING_DIR/stg_undercoding_metrics.csv"
STATUS=$(check_file_age "$UNDERCODING_FILE" $MAX_AGE_DAYS) || NEEDS_RUN=true

if [[ "$NEEDS_RUN" == true ]]; then
    echo "Status: $STATUS"
    echo "Running: python workers/pipeline/mine_cpt_codes.py"
    python "$PROJECT_ROOT/workers/pipeline/mine_cpt_codes.py"
    echo "✅ CPT mining completed"
else
    echo "Status: $STATUS"
    echo "✅ Using cached undercoding metrics"
fi
echo ""
unset NEEDS_RUN

# Step 2: Psych Code Mining (Behavioral Health Signals)
echo "🧠 Step 2: Psych Code Mining"
echo "─────────────────────────────"
PSYCH_FILE="$STAGING_DIR/stg_psych_metrics.csv"
STATUS=$(check_file_age "$PSYCH_FILE" $MAX_AGE_DAYS) || NEEDS_RUN=true

if [[ "$NEEDS_RUN" == true ]]; then
    echo "Status: $STATUS"
    echo "Running: python workers/pipeline/mine_psych_codes.py"
    python "$PROJECT_ROOT/workers/pipeline/mine_psych_codes.py"
    echo "✅ Psych mining completed"
else
    echo "Status: $STATUS"
    echo "✅ Using cached psych metrics"
fi
echo ""
unset NEEDS_RUN

# Step 3: Full Pipeline (Data Integration + Scoring)
echo "⚙️  Step 3: Full Pipeline Execution"
echo "───────────────────────────────────"
echo "Running: python workers/pipeline/pipeline_main.py"
python "$PROJECT_ROOT/workers/pipeline/pipeline_main.py"
echo ""

echo "✅ Pipeline completed successfully!"
echo ""
echo "📋 Output files:"
echo "  - data/curated/clinics_enriched_scored.csv"
echo "  - data/curated/clinics_scored_final.csv"
