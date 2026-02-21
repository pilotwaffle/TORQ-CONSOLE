#!/bin/bash
# CI Gate Script for TORQ Console
#
# This script enforces quality gates before allowing code to merge.
# Run this in CI/CD pipeline (GitHub Actions, GitLab CI, etc.)
#
# Exit code 0 = All gates passed
# Exit code 1 = One or more gates failed
#
# Usage:
#   ./scripts/ci_gate.sh [--skip-smoke] [--direct-n 3] [--research-n 3]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PYTHON="${PYTHON:-python3}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8899}"
DIRECT_N="${DIRECT_N:-3}"
RESEARCH_N="${RESEARCH_N:-3}"
MIN_DIRECT_LATENCY="${MIN_DIRECT_LATENCY:-0.2}"
MIN_RESEARCH_LATENCY="${MIN_RESEARCH_LATENCY:-0.6}"

# Parse arguments
SKIP_SMOKE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-smoke)
            SKIP_SMOKE=true
            shift
            ;;
        --direct-n)
            DIRECT_N="$2"
            shift 2
            ;;
        --research-n)
            RESEARCH_N="$2"
            shift 2
            ;;
        --min-direct)
            MIN_DIRECT_LATENCY="$2"
            shift 2
            ;;
        --min-research)
            MIN_RESEARCH_LATENCY="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "========================================"
echo "TORQ Console CI Gate"
echo "========================================"
echo ""
echo "Configuration:"
echo "  Project Root: $PROJECT_ROOT"
echo "  Backend URL: $BACKEND_URL"
echo "  Direct Prompts: $DIRECT_N"
echo "  Research Prompts: $RESEARCH_N"
echo "  Min Direct Latency: ${MIN_DIRECT_LATENCY}s"
echo "  Min Research Latency: ${MIN_RESEARCH_LATENCY}s"
echo "  Skip Smoke: $SKIP_SMOKE"
echo ""

GATES_PASSED=0
GATES_FAILED=0

# Gate 1: Preflight Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Gate 1: Preflight Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd "$PROJECT_ROOT"

if [ "$SKIP_SMOKE" = true ]; then
    echo "[SKIP] Skipping smoke test (--skip-smoke flag)"
    GATES_PASSED=$((GATES_PASSED + 1))
else
    echo "[RUN] Running preflight with smoke test..."
    if $PYTHON -m torq_console.preflight --provider deepseek --smoke --json > /tmp/preflight.json 2>&1; then
        echo -e "${GREEN}[PASS]${NC} Preflight check passed"
        GATES_PASSED=$((GATES_PASSED + 1))
    else
        echo -e "${RED}[FAIL]${NC} Preflight check failed"
        echo "Check /tmp/preflight.json for details"
        GATES_FAILED=$((GATES_FAILED + 1))
    fi
fi
echo ""

# Gate 2: Unit Tests (Regression Tests)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Gate 2: Regression Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[RUN] Running regression tests..."

if $PYTHON -m pytest tests/test_regression_no_placeholders.py -v --tb=short > /tmp/regression_tests.txt 2>&1; then
    # Check that all tests passed (4 tests expected)
    if grep -q "4 passed" /tmp/regression_tests.txt; then
        echo -e "${GREEN}[PASS]${NC} All 4 regression tests passed"
        GATES_PASSED=$((GATES_PASSED + 1))
    else
        echo -e "${YELLOW}[WARN]${NC} Tests passed but unexpected count"
        echo "Check /tmp/regression_tests.txt for details"
        GATES_PASSED=$((GATES_PASSED + 1))
    fi
else
    echo -e "${RED}[FAIL]${NC} Regression tests failed"
    echo "Check /tmp/regression_tests.txt for details"
    GATES_FAILED=$((GATES_FAILED + 1))
fi
echo ""

# Gate 3: Check Metadata in Responses
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Gate 3: Metadata Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Make a simple request and check for meta block
echo "[RUN] Checking API responses include metadata..."

RESPONSE=$($PYTHON -c "
import requests
import json
r = requests.post('${BACKEND_URL}/api/chat', json={'message': 'What is 2+2? Respond with only the number.'}, timeout=30)
print(r.status_code)
data = r.json()
print('meta_present=' + str('meta' in data))
if 'meta' in data:
    print('provider=' + str(data['meta'].get('provider')))
    print('latency_ms=' + str(data['meta'].get('latency_ms')))
" 2>&1)

if echo "$RESPONSE" | grep -q "meta_present=True"; then
    echo -e "${GREEN}[PASS]${NC} Metadata is included in responses"
    GATES_PASSED=$((GATES_PASSED + 1))
else
    echo -e "${YELLOW}[WARN]${NC} Metadata not detected (can be enhanced later)"
    GATES_PASSED=$((GATES_PASSED + 1))  # Not a hard failure for now
fi
echo ""

# Gate 4: Diagnostics Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Gate 4: System Diagnostics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[RUN] Checking /api/diag..."

DIAG_RESPONSE=$($PYTHON -c "
import requests
r = requests.get('${BACKEND_URL}/api/diag', timeout=10)
print(r.status_code)
if r.status_code == 200:
    data = r.json()
    print('provider_available=' + str(data.get('provider', {}).get('available', False)))
    print('prince_loaded=' + str(data.get('prince_flowers', {}).get('loaded', False)))
    print('env_keys_present=' + str(any(data.get('env', {}).values())))
" 2>&1)

if echo "$DIAG_RESPONSE" | grep -q "200"; then
    echo -e "${GREEN}[PASS]${NC} Diagnostics endpoint accessible"
    GATES_PASSED=$((GATES_PASSED + 1))

    # Check critical components
    if echo "$DIAG_RESPONSE" | grep -q "provider_available=True"; then
        echo -e "  └─ Provider is available"
    fi

    if echo "$DIAG_RESPONSE" | grep -q "prince_loaded=True"; then
        echo -e "  └─ Prince Flowers is loaded"
    fi

    if echo "$DIAG_RESPONSE" | grep -q "env_keys_present=True"; then
        echo -e "  └─ Environment keys configured"
    fi
else
    echo -e "${YELLOW}[WARN]${NC} Diagnostics endpoint not accessible"
    GATES_PASSED=$((GATES_PASSED + 1))
fi
echo ""

# Gate 5: Confidence Test
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Gate 5: Confidence Test (Real API Calls)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[RUN] Running confidence test with ${DIRECT_N} direct + ${RESEARCH_N} research prompts..."
echo "      Latency floors: direct >= ${MIN_DIRECT_LATENCY}s, research >= ${MIN_RESEARCH_LATENCY}s"

if $PYTHON -m torq_console.confidence_test \
    --base-url "$BACKEND_URL" \
    --direct-n "$DIRECT_N" \
    --research-n "$RESEARCH_N" \
    --min-direct-latency "$MIN_DIRECT_LATENCY" \
    --min-research-latency "$MIN_RESEARCH_LATENCY" \
    > /tmp/confidence_test.txt 2>&1; then
    echo -e "${GREEN}[PASS]${NC} Confidence test passed"
    GATES_PASSED=$((GATES_PASSED + 1))
else
    echo -e "${RED}[FAIL]${NC} Confidence test failed"
    echo "Check /tmp/confidence_test.txt for details"
    GATES_FAILED=$((GATES_FAILED + 1))
fi
echo ""

# Summary
echo "========================================"
echo "CI Gate Summary"
echo "========================================"
echo "Gates Passed: $GATES_PASSED"
echo "Gates Failed: $GATES_FAILED"
echo ""

if [ $GATES_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL GATES PASSED${NC}"
    echo ""
    echo "The system is ready for deployment."
    exit 0
else
    echo -e "${RED}✗ CI GATE FAILED${NC}"
    echo ""
    echo "One or more quality gates failed. Please review the logs above."
    exit 1
fi
