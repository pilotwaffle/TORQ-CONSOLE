#!/bin/bash

# Workflow Builder UI - API Verification Script
# Tests the Task Graph Engine API endpoints

API_BASE="${API_BASE:-http://localhost:8899}"

echo "=================================="
echo "Workflow Builder UI - API Verification"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_endpoint() {
  local name="$1"
  local endpoint="$2"
  local expected_field="$3"

  echo -n "Testing $name... "

  response=$(curl -s "$API_BASE$endpoint" -w "\n%{http_code}")
  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | sed '$d')

  if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
    if [ -n "$expected_field" ]; then
      if echo "$body" | grep -q "$expected_field"; then
        echo -e "${GREEN}PASS${NC}"
        echo "  └─ Found: $expected_field"
      else
        echo -e "${YELLOW}WARN${NC}"
        echo "  └─ Expected field not found: $expected_field"
      fi
    else
      echo -e "${GREEN}PASS${NC} (HTTP $http_code)"
    fi
    return 0
  else
    echo -e "${RED}FAIL${NC} (HTTP $http_code)"
    return 1
  fi
}

# Test 1: Health Check
test_endpoint "Health Check" "/health" "healthy"

# Test 2: List Workflows
test_endpoint "List Workflows" "/api/tasks/graphs" "graph_id"

# Test 3: Get Templates
test_endpoint "Get Templates" "/api/tasks/examples" "examples"

# Test 4: List Executions
test_endpoint "List Executions" "/api/tasks/executions" "execution_id"

echo ""
echo "=================================="
echo "API Verification Complete"
echo "=================================="
echo ""
echo "If all tests passed, the Workflow Builder UI should work correctly."
echo ""
echo "Next steps:"
echo "1. Start frontend: cd frontend && npm run dev"
echo "2. Navigate to http://localhost:3000/workflows"
echo "3. Follow the QA Test Plan in WORKFLOW_BUILDER_QA_TEST_PLAN.md"
