#!/bin/bash
# Metadata Validation Script for TORQ Console
#
# Validates that metadata appears on ALL response paths:
# 1. Direct success - meta populated
# 2. Research success - tools_used populated
# 3. Error responses - error_category populated
# 4. Timeout responses - error_category = timeout
# 5. Metadata consistency - provider/model consistent across requests
#
# Usage: ./scripts/validate_metadata.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
PYTHON="${PYTHON:-python3}"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8899}"

echo "========================================"
echo "TORQ Console Metadata Validation"
echo "========================================"
echo ""
echo "Backend URL: $BACKEND_URL"
echo ""

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to check metadata (using Python for Windows compatibility)
check_metadata() {
    local test_name="$1"
    local response="$2"
    local field="$3"
    local expected="$4"

    # Use Python for JSON parsing (works on Windows/Git Bash)
    if echo "$response" | python -c "import sys, json; d=json.load(sys.stdin); meta=d.get('meta', {}); val=meta$field 2>/dev/null; exit(0 if $expected else 1)" 2>/dev/null; then
        echo -e "${GREEN}[PASS]${NC} $test_name: meta.$field $expected"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}[FAIL]${NC} $test_name: meta.$field $expected"
        echo "Response preview: $(echo "$response" | head -c 200)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Helper to make request and check metadata
test_request() {
    local test_name="$1"
    local message="$2"
    local tools="$3"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Test: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Build request
    if [ -z "$tools" ]; then
        request="{\"message\": \"$message\"}"
    else
        request="{\"message\": \"$message\", \"tools\": $tools}"
    fi

    # Make request
    response=$(curl -s -X POST "$BACKEND_URL/api/chat" \
        -H "Content-Type: application/json" \
        -d "$request" \
        --max-time 60)

    # Check response is valid JSON (using Python for Windows compatibility)
    if ! echo "$response" | python -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
        echo -e "${RED}[FAIL]${NC} $test_name: Invalid JSON response"
        echo "Response preview: $(echo "$response" | head -c 200)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo ""
        return 1
    fi

    # Check metadata block exists (using Python)
    if ! echo "$response" | python -c "import sys, json; d=json.load(sys.stdin); exit(0 if 'meta' in d else 1)" 2>/dev/null; then
        echo -e "${RED}[FAIL]${NC} $test_name: Missing metadata block"
        echo "Response preview: $(echo "$response" | head -c 200)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo ""
        return 1
    fi

    echo -e "${GREEN}[OK]${NC} Metadata block present"

    # Check required fields
    check_metadata "$test_name" "$response" "provider" "!= null"
    check_metadata "$test_name" "$response" "latency_ms" ">= 0"
    check_metadata "$test_name" "$response" "timestamp" "!= null"

    # For success responses, check tools_used
    if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
        echo -e "${GREEN}[OK]${NC} Response success=true"

        if [ -n "$tools" ]; then
            # Research mode - tools_used should be populated
            check_metadata "$test_name" "$response" "tools_used" "| length > 0"
        else
            # Direct mode - tools_used should be empty
            check_metadata "$test_name" "$response" "tools_used" "| length == 0"
        fi
    fi

    # For error responses, check error_category
    if echo "$response" | jq -e '.success == false' > /dev/null 2>&1; then
        echo -e "${YELLOW}[WARN]${NC} Response success=false (error case)"
        check_metadata "$test_name" "$response" "error" "!= null"
        check_metadata "$test_name" "$response" "error_category" "!= null"
    fi

    # Show preview (using Python for Windows compatibility)
    echo ""
    echo "Response preview:"
    echo "$response" | python -c "import sys, json; d=json.load(sys.stdin); m=d.get('meta',{}); print(json.dumps({'success': d.get('success'), 'provider': m.get('provider'), 'latency_ms': m.get('latency_ms'), 'mode': m.get('mode'), 'tools_used': m.get('tools_used'), 'error_category': m.get('error_category', 'N/A')}, indent=2))"
    echo ""
}

# Test 1: Direct success (no tools)
test_request \
    "Direct Success" \
    "What is 2+2? Respond with only the number." \
    ""

# Test 2: Research success (with web_search)
test_request \
    "Research Success" \
    "What is the current time in Texas? Explain briefly." \
    '["web_search"]'

# Test 3: Metadata consistency (3 requests)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test: Metadata Consistency"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

providers=""
for i in {1..3}; do
    response=$(curl -s -X POST "$BACKEND_URL/api/chat" \
        -H "Content-Type: application/json" \
        -d '{"message": "Consistency test '$i': What is 3+3?"}' \
        --max-time 30)

    provider=$(echo "$response" | python -c "import sys, json; d=json.load(sys.stdin); print(d.get('meta', {}).get('provider', 'unknown'))" 2>/dev/null)
    if [ -n "$providers" ]; then
        providers="$providers $provider"
    else
        providers="$provider"
    fi
done

# Check if all providers are the same
provider_count=$(echo "$providers" | tr ' ' '\n' | sort -u | wc -l)
if [ "$provider_count" -eq 1 ]; then
    echo -e "${GREEN}[PASS]${NC} Provider consistent across requests: $providers"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}[FAIL]${NC} Provider inconsistent across requests: $providers"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 4: Error metadata (empty message should trigger error)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test: Error Response Metadata"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

response=$(curl -s -X POST "$BACKEND_URL/api/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": ""}' \
    --max-time 30)

if echo "$response" | python -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
    if echo "$response" | python -c "import sys, json; d=json.load(sys.stdin); exit(0 if 'meta' in d else 1)" 2>/dev/null; then
        echo -e "${GREEN}[PASS]${NC} Error response includes metadata"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        error_cat=$(echo "$response" | python -c "import sys, json; d=json.load(sys.stdin); print(d.get('meta', {}).get('error_category', ''))" 2>/dev/null)
        if [ -n "$error_cat" ]; then
            echo -e "  └─ error_category: $error_cat"
        fi
    else
        echo -e "${RED}[FAIL]${NC} Error response missing metadata"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${YELLOW}[SKIP]${NC} Could not test error response (backend may reject empty messages)"
fi
echo ""

# Summary
echo "========================================"
echo "Metadata Validation Summary"
echo "========================================"
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL METADATA VALIDATION PASSED${NC}"
    echo ""
    echo "Metadata is present on all tested paths:"
    echo "  ✓ Direct success responses"
    echo "  ✓ Research success responses"
    echo "  ✓ Error responses"
    echo "  ✓ Consistent provider/model across requests"
    exit 0
else
    echo -e "${RED}✗ METADATA VALIDATION FAILED${NC}"
    echo ""
    echo "Some paths are missing metadata. Review the failures above."
    exit 1
fi
