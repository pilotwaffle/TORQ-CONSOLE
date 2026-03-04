#!/bin/bash
# TORQ Console Railway Deployment Verification Script
#
# Usage: ./verify_railway_deploy.sh [railway_url] [vercel_url]
#
# This script validates that Railway is running the expected code with:
# 1. Correct git_sha (matches expected commit)
# 2. torq-deploy-v1 contract structure
# 3. New telemetry health fields (key_type_detected, key_source, access_test)
# 4. Supabase project ref matches expected value
# 5. Vercel proxy relay works (end-to-end validation)
#
# Exit codes:
# 0 - All checks passed
# 1 - Critical failure (deploy endpoint missing)
# 2 - Git SHA mismatch
# 3 - Contract violation
# 4 - Telemetry health failed
# 5 - Vercel proxy relay failed

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Expected values - update these when deploying new commits
EXPECTED_SHA="efdf084a"              # control-plane-v1-clean build metadata commit
EXPECTED_PROJECT_REF="npukynbaglmcdvzyklqa"
EXPECTED_SCHEMA="torq-deploy-v1"
EXPECTED_KEY_TYPE="service_role"
EXPECTED_KEY_SOURCE="SUPABASE_SERVICE_ROLE_KEY"

# URLs
RAILWAY_URL="${1:-https://web-production-74ed0.up.railway.app}"
VERCEL_URL="${2:-https://torq-console.vercel.app}"

EXIT_CODE=0

header() {
    echo ""
    echo "==================================================================="
    echo -e "${CYAN}$1${NC}"
    echo "==================================================================="
}

pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

fail() {
    echo -e "${RED}❌ $1${NC}"
    EXIT_CODE=$2
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

header "TORQ Console Deployment Verification"
echo "Railway: $RAILWAY_URL"
echo "Vercel:  $VERCEL_URL"
echo ""

# =============================================================================
# Test 1: Health Check (basic liveness)
# =============================================================================
header "Test 1: Health Check (/health)"

HEALTH=$(curl -s --max-time 10 "$RAILWAY_URL/health" 2>/dev/null) || {
    fail "Health check endpoint unreachable" 1
    echo ""
    exit 1
}

echo "$HEALTH" | head -20

# Check for schema version
if echo "$HEALTH" | grep -q "\"_schema\":\"$EXPECTED_SCHEMA\""; then
    pass "Health check returns torq-deploy-v1 schema"
else
    fail "Missing or incorrect _schema in health response" 3
fi

# Check git_sha
GIT_SHA=$(echo "$HEALTH" | jq -r '.git_sha // empty' 2>/dev/null)
if [ -n "$GIT_SHA" ]; then
    if [[ "$GIT_SHA" == *"$EXPECTED_SHA"* ]]; then
        pass "Git SHA matches: $GIT_SHA"
    else
        warn "Git SHA: $GIT_SHA (expected prefix: $EXPECTED_SHA)"
        EXIT_CODE=2
    fi
else
    warn "Could not extract git_sha from health endpoint"
fi
echo ""

# =============================================================================
# Test 2: Deploy Info (detailed contract validation)
# =============================================================================
header "Test 2: Deploy Info (/api/debug/deploy)"

DEPLOY=$(curl -s --max-time 10 "$RAILWAY_URL/api/debug/deploy" 2>/dev/null) || {
    fail "Deploy endpoint unreachable" 1
    echo ""
    exit 1
}

echo "$DEPLOY" | jq '.' 2>/dev/null || echo "$DEPLOY"
echo ""

# Validate contract structure
DEPLOY_SCHEMA=$(echo "$DEPLOY" | jq -r '._schema // empty' 2>/dev/null)
if [ "$DEPLOY_SCHEMA" = "$EXPECTED_SCHEMA" ]; then
    pass "Deploy endpoint schema: $DEPLOY_SCHEMA"
else
    fail "Deploy endpoint schema mismatch: ${DEPLOY_SCHEMA:-missing}" 3
fi

# Validate git_sha from deploy endpoint
DEPLOY_GIT_SHA=$(echo "$DEPLOY" | jq -r '.git_sha // empty' 2>/dev/null)
if [ -n "$DEPLOY_GIT_SHA" ]; then
    if [[ "$DEPLOY_GIT_SHA" == *"$EXPECTED_SHA"* ]]; then
        pass "Deploy git_sha matches: $DEPLOY_GIT_SHA"
    else
        fail "Deploy git_sha mismatch: $DEPLOY_GIT_SHA (expected: $EXPECTED_SHA)" 2
    fi
else
    fail "Could not extract git_sha from deploy endpoint" 2
fi

# Validate running file points to correct module
RUNNING_FILE=$(echo "$DEPLOY" | jq -r '.running_file // empty' 2>/dev/null)
if [[ "$RUNNING_FILE" == *"railway_app"* ]]; then
    pass "Running correct module: $RUNNING_FILE"
else
    warn "Unexpected running_file: ${RUNNING_FILE:-missing}"
fi

# Validate platform
PLATFORM=$(echo "$DEPLOY" | jq -r '.platform // empty' 2>/dev/null)
if [ "$PLATFORM" = "railway" ]; then
    pass "Platform detected: railway"
else
    warn "Unexpected platform: ${PLATFORM:-missing}"
fi
echo ""

# =============================================================================
# Test 3: Telemetry Health (key_type_detected validation)
# =============================================================================
header "Test 3: Telemetry Health (/api/telemetry/health)"

TELEMETRY=$(curl -s --max-time 10 "$RAILWAY_URL/api/telemetry/health" 2>/dev/null) || {
    fail "Telemetry health endpoint unreachable" 4
    echo ""
    exit 1
}

echo "$TELEMETRY" | jq '.' 2>/dev/null || echo "$TELEMETRY"
echo ""

# Extract fields
PROJECT_REF=$(echo "$TELEMETRY" | jq -r '.supabase_project_ref // empty' 2>/dev/null)
KEY_TYPE=$(echo "$TELEMETRY" | jq -r '.key_type_detected // empty' 2>/dev/null)
KEY_SOURCE=$(echo "$TELEMETRY" | jq -r '.key_source // empty' 2>/dev/null)
ACCESS_STATUS=$(echo "$TELEMETRY" | jq -r '.access_test.status // empty' 2>/dev/null)
HTTP_STATUS=$(echo "$TELEMETRY" | jq -r '.access_test.http_status // empty' 2>/dev/null)
TABLES=$(echo "$TELEMETRY" | jq -r '.tables[] // empty' 2>/dev/null)

# Check if new fields exist (this confirms new code is running)
if [ -z "$KEY_TYPE" ]; then
    fail "key_type_detected field missing - running old code!" 4
else
    info "key_type_detected present: $KEY_TYPE"
fi

if [ -z "$KEY_SOURCE" ]; then
    fail "key_source field missing - running old code!" 4
else
    info "key_source present: $KEY_SOURCE"
fi

if [ -z "$ACCESS_STATUS" ]; then
    fail "access_test field missing - running old code!" 4
else
    info "access_test present: $ACCESS_STATUS"
fi

# Validate values
if [ "$PROJECT_REF" = "$EXPECTED_PROJECT_REF" ]; then
    pass "Supabase project ref: $PROJECT_REF"
else
    fail "Supabase project ref mismatch: ${PROJECT_REF:-missing} (expected: $EXPECTED_PROJECT_REF)" 4
fi

if [ "$KEY_TYPE" = "$EXPECTED_KEY_TYPE" ]; then
    pass "key_type_detected: $KEY_TYPE"
else
    warn "key_type_detected: ${KEY_TYPE:-missing} (expected: $EXPECTED_KEY_TYPE)"
fi

if [ "$KEY_SOURCE" = "$EXPECTED_KEY_SOURCE" ]; then
    pass "key_source: $KEY_SOURCE"
else
    warn "key_source: ${KEY_SOURCE:-missing} (expected: $EXPECTED_KEY_SOURCE)"
fi

if [ "$ACCESS_STATUS" = "healthy" ] && [ "$HTTP_STATUS" = "200" ]; then
    pass "access_test: $ACCESS_STATUS (HTTP $HTTP_STATUS)"
else
    fail "access_test: ${ACCESS_STATUS:-missing} (HTTP ${HTTP_STATUS:-missing})" 4
fi

# Check tables
if echo "$TABLES" | grep -q "telemetry_traces"; then
    pass "telemetry_traces table configured"
else
    warn "telemetry_traces not in tables list"
fi

if echo "$TABLES" | grep -q "telemetry_spans"; then
    pass "telemetry_spans table configured"
else
    warn "telemetry_spans not in tables list"
fi
echo ""

# =============================================================================
# Test 4: Vercel Proxy Relay (end-to-end validation)
# =============================================================================
header "Test 4: Vercel Proxy Relay (via Vercel → Railway)"

VERCEL_HEALTH=$(curl -s --max-time 10 "$VERCEL_URL/api/telemetry/health" 2>/dev/null) || {
    warn "Vercel proxy unreachable (may not be configured yet)"
    echo "Skipping Vercel validation..."
    echo ""
else
    echo "$VERCEL_HEALTH" | jq '.' 2>/dev/null | head -30

    VERCEL_KEY_TYPE=$(echo "$VERCEL_HEALTH" | jq -r '.key_type_detected // empty' 2>/dev/null)
    VERCEL_PROJECT_REF=$(echo "$VERCEL_HEALTH" | jq -r '.supabase_project_ref // empty' 2>/dev/null)

    if [ -n "$VERCEL_KEY_TYPE" ]; then
        pass "Vercel proxy relays key_type_detected: $VERCEL_KEY_TYPE"
    else
        warn "Vercel proxy not relaying telemetry health (rewrite config?)" 5
    fi

    if [ "$VERCEL_PROJECT_REF" = "$EXPECTED_PROJECT_REF" ]; then
        pass "Vercel proxy relays correct project ref"
    else
        warn "Vercel project ref: ${VERCEL_PROJECT_REF:-missing}"
    fi
    echo ""
fi

# =============================================================================
# Summary
# =============================================================================
header "Verification Summary"

if [ $EXIT_CODE -eq 0 ]; then
    pass "All checks passed!"
    echo ""
    echo "Railway deployment is running:"
    echo "  - Branch: control-plane-v1-clean"
    echo "  - Commit: $DEPLOY_GIT_SHA"
    echo "  - Schema: $EXPECTED_SCHEMA"
    echo "  - Telemetry diagnostics: ACTIVE"
    echo "  - Supabase project: $EXPECTED_PROJECT_REF"
    echo ""
    echo "✅ Ready for production traffic"
else
    warn "Some checks failed - review output above"
    echo ""
    echo "Common issues:"
    echo "  - Old code still running: Trigger new deployment in Railway"
    echo "  - Git SHA mismatch: Railway hasn't picked up latest commit"
    echo "  - Missing fields: Old branch still deployed"
    echo ""
    echo "Fix: In Railway dashboard, change watched branch to control-plane-v1-clean"
fi

echo ""
exit $EXIT_CODE
