#!/bin/bash
#
# TORQ Console - Post-Layer-11 UI Verification Script
#
# Executes the complete E2E test suite across local and browser environments.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_DIR="$(dirname "$0")/../frontend"
LOCAL_URL="${BASE_URL:-http://localhost:5173}"
BROWSER_URL="${BROWSER_URL:-https://torq-console.vercel.app}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TORQ Console - Post-Layer-11 UI Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Change to frontend directory
cd "$FRONTEND_DIR"

# ============================================================================
# Phase 1: Pre-flight Checks
# ============================================================================

echo -e "${YELLOW}Phase 1: Pre-flight Checks${NC}"

# Check if Playwright is installed
if ! command -v npx &> /dev/null; then
    echo -e "${RED}Error: npx not found. Please install Node.js.${NC}"
    exit 1
fi

# Check if browsers are installed
if [ ! -d "$FRONTEND_DIR/node_modules/playwright-core" ]; then
    echo -e "${YELLOW}Installing Playwright browsers...${NC}"
    npx playwright install --with-deps
fi

# Check if local dev server is needed
if [[ "$LOCAL_URL" == *"localhost"* ]] || [[ "$LOCAL_URL" == *"127.0.0.1"* ]]; then
    echo -e "${YELLOW}Local URL detected: $LOCAL_URL${NC}"
    echo -e "${YELLOW}Make sure dev server is running: npm run dev${NC}"

    # Try to ping the server
    if command -v curl &> /dev/null; then
        if ! curl -s "$LOCAL_URL" > /dev/null 2>&1; then
            echo -e "${RED}Error: Local server not responding at $LOCAL_URL${NC}"
            echo -e "${YELLOW}Start the server with: npm run dev${NC}"
            read -p "Press Enter to continue anyway (tests will fail)..."
        fi
    fi
fi

echo -e "${GREEN}✓ Pre-flight checks complete${NC}"
echo ""

# ============================================================================
# Phase 2: Smoke Tests (Critical)
# ============================================================================

echo -e "${YELLOW}Phase 2: Smoke Tests${NC}"
echo "Testing basic app functionality..."

if npx playwright test tests/e2e/smoke --reporter=line; then
    echo -e "${GREEN}✓ Smoke tests passed${NC}"
    SMOKE_PASS=1
else
    echo -e "${RED}✗ Smoke tests failed${NC}"
    SMOKE_PASS=0
fi

echo ""

# ============================================================================
# Phase 3: Workflow Tests (High Priority)
# ============================================================================

echo -e "${YELLOW}Phase 3: Workflow Tests${NC}"
echo "Testing operator workflows..."

if npx playwright test tests/e2e/workflows --reporter=line; then
    echo -e "${GREEN}✓ Workflow tests passed${NC}"
    WORKFLOW_PASS=1
else
    echo -e "${RED}✗ Workflow tests failed${NC}"
    WORKFLOW_PASS=0
fi

echo ""

# ============================================================================
# Phase 4: Distributed Fabric Tests (Layer 11)
# ============================================================================

echo -e "${YELLOW}Phase 4: Distributed Fabric Tests${NC}"
echo "Testing Layer 11 fabric UI..."

if npx playwright test tests/e2e/distributed_fabric --reporter=line; then
    echo -e "${GREEN}✓ Fabric tests passed${NC}"
    FABRIC_PASS=1
else
    echo -e "${RED}✗ Fabric tests failed${NC}"
    FABRIC_PASS=0
fi

echo ""

# ============================================================================
# Phase 5: Regression Tests
# ============================================================================

echo -e "${YELLOW}Phase 5: Regression Tests${NC}"
echo "Testing UI controls and error states..."

if npx playwright test tests/e2e/regression --reporter=line; then
    echo -e "${GREEN}✓ Regression tests passed${NC}"
    REGRESSION_PASS=1
else
    echo -e "${RED}✗ Regression tests failed${NC}"
    REGRESSION_PASS=0
fi

echo ""

# ============================================================================
# Phase 6: Browser Deployment Tests (Optional)
# ============================================================================

echo -e "${YELLOW}Phase 6: Browser Deployment Tests${NC}"
echo "Testing against $BROWSER_URL"

read -p "Run browser deployment tests? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if BROWSER_URL="$BROWSER_URL" npx playwright test --project=browser-deployment --reporter=line; then
        echo -e "${GREEN}✓ Browser tests passed${NC}"
        BROWSER_PASS=1
    else
        echo -e "${RED}✗ Browser tests failed${NC}"
        BROWSER_PASS=0
    fi
else
    echo -e "${YELLOW}Skipped browser deployment tests${NC}"
    BROWSER_PASS=-1
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verification Summary${NC}"
echo -e "${BLUE}========================================${NC}"

TOTAL_TESTS=4
PASSED_TESTS=0

if [ $SMOKE_PASS -eq 1 ]; then
    echo -e "${GREEN}✓${NC} Smoke Tests"
    ((PASSED_TESTS++))
else
    echo -e "${RED}✗${NC} Smoke Tests"
fi

if [ $WORKFLOW_PASS -eq 1 ]; then
    echo -e "${GREEN}✓${NC} Workflow Tests"
    ((PASSED_TESTS++))
else
    echo -e "${RED}✗${NC} Workflow Tests"
fi

if [ $FABRIC_PASS -eq 1 ]; then
    echo -e "${GREEN}✓${NC} Fabric Tests"
    ((PASSED_TESTS++))
else
    echo -e "${RED}✗${NC} Fabric Tests"
fi

if [ $REGRESSION_PASS -eq 1 ]; then
    echo -e "${GREEN}✓${NC} Regression Tests"
    ((PASSED_TESTS++))
else
    echo -e "${RED}✗${NC} Regression Tests"
fi

if [ $BROWSER_PASS -eq 1 ]; then
    echo -e "${GREEN}✓${NC} Browser Tests"
    ((TOTAL_TESTS++))
    ((PASSED_TESTS++))
elif [ $BROWSER_PASS -eq 0 ]; then
    echo -e "${RED}✗${NC} Browser Tests"
    ((TOTAL_TESTS++))
fi

echo ""
echo -e "Tests Passed: ${GREEN}$PASSED_TESTS${NC} / ${BLUE}$TOTAL_TESTS${NC}"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}ALL TESTS PASSED${NC}"
    echo -e "${GREEN}UI verification complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}SOME TESTS FAILED${NC}"
    echo -e "${RED}Review the HTML report: npm run test:e2e:report${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
