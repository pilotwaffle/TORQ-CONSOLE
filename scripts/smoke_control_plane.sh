#!/usr/bin/env bash
# TORQ Console - Control Plane Smoke Test Suite
# Purpose: Validate deployment health after every deploy
# Usage: ./scripts/smoke_control_plane.sh
# Exit code: 0 = all pass, 1 = any fail

set -o pipefail

# Configuration
VERCEL_URL="${VERCEL_URL:-https://torq-console.vercel.app}"
RAILWAY_URL="${RAILWAY_URL:-https://web-production-74ed0.up.railway.app}"
EXPECTED_SHA="${EXPECTED_SHA:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; ((TESTS_PASSED++)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; ((TESTS_FAILED++)); }

# Fetch with timeout (default 10s)
fetch() {
  local url="$1"
  local timeout="${2:-10}"
  curl -s --max-time "$timeout" "$url"
}

# Extract JSON field (works without jq)
extract_field() {
  local json="$1"
  local field="$2"
  # Simple extraction: find "field":"value" pattern and extract value
  echo "$json" | grep -o "\"$field\":\"[^\"]*\"" | cut -d'"' -f4 || echo ""
}

# Check JSON contains key
json_has_key() {
  local json="$1"
  local key="$2"
  echo "$json" | grep -q "\"$key\""
}

# Check JSON has true value for key
json_is_true() {
  local json="$1"
  local key="$2"
  echo "$json" | grep -q "\"$key\"[[:space:]]*:[[:space:]]*true"
}

# Check JSON has specific string value
json_equals() {
  local json="$1"
  local key="$2"
  local value="$3"
  echo "$json" | grep -q "\"$key\"[[:space:]]*:[[:space:]]*\"$value\""
}

# Check array length > 0
json_array_length() {
  local json="$1"
  local count=$(echo "$json" | grep -o '"count":[0-9]*' | cut -d':' -f2)
  [[ "$count" -gt 0 ]]
}

echo "=========================================="
echo "TORQ Console - Control Plane Smoke Test"
echo "=========================================="
echo "Vercel: $VERCEL_URL"
echo "Railway: $RAILWAY_URL"
echo "Expected SHA: ${EXPECTED_SHA:-<not specified>}"
echo "=========================================="
echo ""

# =========================================================================
# Test 1: Vercel Health
# =========================================================================
log_info "Test 1: Vercel /health"
HEALTH=$(fetch "$VERCEL_URL/health" 15)
if json_equals "$HEALTH" "status" "healthy"; then
  log_pass "Vercel /health returns healthy"
else
  log_fail "Vercel /health not healthy: $HEALTH"
fi
echo ""

# =========================================================================
# Test 2: Railway Health
# =========================================================================
log_info "Test 2: Railway /health"
HEALTH=$(fetch "$RAILWAY_URL/health" 15)
if json_equals "$HEALTH" "status" "healthy"; then
  log_pass "Railway /health returns healthy"
else
  log_fail "Railway /health not healthy: $HEALTH"
fi
echo ""

# =========================================================================
# Test 3: Vercel Deploy Identity
# =========================================================================
log_info "Test 3: Vercel /api/debug/deploy identity"
DEPLOY=$(fetch "$VERCEL_URL/api/debug/deploy" 5)
GIT_SHA=$(echo "$DEPLOY" | extract_field "git_sha")

if [[ -n "$GIT_SHA" && "$GIT_SHA" != "unknown" ]]; then
  log_pass "Vercel has git_sha: $GIT_SHA"
else
  log_fail "Vercel missing git_sha or 'unknown'"
fi

# SHA mismatch check (FAIL HARD if specified)
if [[ -n "$EXPECTED_SHA" && "$GIT_SHA" != "$EXPECTED_SHA" ]]; then
  log_fail "SHA MISMATCH: expected $EXPECTED_SHA, got $GIT_SHA"
  echo ""
  echo "=========================================="
  echo -e "${RED}CRITICAL: Deploy SHA mismatch!${NC}"
  echo "=========================================="
  exit 1
elif [[ -n "$EXPECTED_SHA" ]]; then
  log_pass "SHA matches expected: $EXPECTED_SHA"
fi
echo ""

# =========================================================================
# Test 4: Railway Deploy Identity (torq-deploy-v1 contract)
# =========================================================================
log_info "Test 4: Railway /api/debug/deploy identity (torq-deploy-v1)"
DEPLOY=$(fetch "$RAILWAY_URL/api/debug/deploy" 5)
GIT_SHA=$(echo "$DEPLOY" | extract_field "git_sha")
SCHEMA=$(echo "$DEPLOY" | extract_field "_schema")

if [[ "$SCHEMA" == "torq-deploy-v1" ]]; then
  log_pass "Railway uses torq-deploy-v1 schema"
else
  log_fail "Railway schema not torq-deploy-v1: $SCHEMA"
fi

if [[ -n "$GIT_SHA" && "$GIT_SHA" != "unknown" ]]; then
  log_pass "Railway has git_sha: $GIT_SHA"
else
  log_fail "Railway missing git_sha or 'unknown'"
fi

# SHA mismatch check
if [[ -n "$EXPECTED_SHA" && "$GIT_SHA" != "$EXPECTED_SHA" ]]; then
  log_fail "SHA MISMATCH: expected $EXPECTED_SHA, got $GIT_SHA"
  echo ""
  echo "=========================================="
  echo -e "${RED}CRITICAL: Deploy SHA mismatch!${NC}"
  echo "=========================================="
  exit 1
elif [[ -n "$EXPECTED_SHA" ]]; then
  log_pass "SHA matches expected: $EXPECTED_SHA"
fi
echo ""

# =========================================================================
# Test 5: Vercel Proxy - Learning Status
# =========================================================================
log_info "Test 5: Vercel /api/learning/status (proxy to Railway)"
LEARNING=$(fetch "$VERCEL_URL/api/learning/status" 10)

# Check it's not a 404 error
if echo "$LEARNING" | grep -q "404"; then
  log_fail "Returns 404 - proxy not configured"
elif json_is_true "$LEARNING" "configured"; then
  log_pass "Learning status returns configured=true"
else
  log_fail "Learning not configured or error: $LEARNING"
fi
echo ""

# =========================================================================
# Test 6: Vercel Proxy - Telemetry Health
# =========================================================================
log_info "Test 6: Vercel /api/telemetry/health (proxy to Railway)"
TELEMETRY=$(fetch "$VERCEL_URL/api/telemetry/health" 10)

# Check it's not an error response
if echo "$TELEMETRY" | grep -q "Backend error"; then
  log_fail "Backend error from proxy"
elif json_is_true "$TELEMETRY" "configured"; then
  log_pass "Telemetry health returns configured=true"
else
  log_fail "Telemetry not configured or error: $TELEMETRY"
fi
echo ""

# =========================================================================
# Test 7: Vercel Proxy - Traces List
# =========================================================================
log_info "Test 7: Vercel /api/traces?limit=5 (proxy to Railway)"
TRACES=$(fetch "$VERCEL_URL/api/traces?limit=5" 10)

# Check it returns an array with count > 0
if json_array_length "$TRACES"; then
  COUNT=$(echo "$TRACES" | grep -o '"count":[0-9]*' | cut -d':' -f2)
  log_pass "Traces API returns $COUNT traces"
else
  log_fail "Traces API returns no data or error: $TRACES"
fi
echo ""

# =========================================================================
# Summary
# =========================================================================
echo "=========================================="
echo "Smoke Test Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
  echo -e "${GREEN}All tests passed!${NC}"
  echo "=========================================="
  exit 0
else
  echo -e "${RED}Some tests failed!${NC}"
  echo "=========================================="
  exit 1
fi
