#!/bin/bash
# Test Enhanced Prince API with curl commands

API_URL="http://localhost:8000"

echo "=================================="
echo "ENHANCED PRINCE API - CURL TESTS"
echo "=================================="
echo ""

# Check if server is running
echo "1. Health Check"
echo "-----------------------------------"
curl -s "$API_URL/health" | python3 -m json.tool
echo ""
echo ""

# Test Type A: Research query (should search immediately)
echo "2. Type A Test: Search Query (CRITICAL)"
echo "-----------------------------------"
echo "Query: 'Search the latest AI news 11/08/25'"
echo "Expected: IMMEDIATE_ACTION with WebSearch"
echo ""
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Search the latest AI news 11/08/25",
    "user_id": "test_user",
    "session_id": "test_session"
  }' | python3 -m json.tool
echo ""
echo ""

# Test Type A: Research query with "research" keyword
echo "3. Type A Test: Research Query (CRITICAL)"
echo "-----------------------------------"
echo "Query: 'Research new updates coming to GLM-4.6'"
echo "Expected: IMMEDIATE_ACTION with WebSearch"
echo ""
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Research new updates coming to GLM-4.6",
    "user_id": "test_user",
    "session_id": "test_session"
  }' | python3 -m json.tool
echo ""
echo ""

# Test Type A: Simple search
echo "4. Type A Test: Simple Search"
echo "-----------------------------------"
echo "Query: 'search for top AI tools'"
echo "Expected: IMMEDIATE_ACTION with WebSearch"
echo ""
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search for top AI tools",
    "user_id": "test_user",
    "session_id": "test_session"
  }' | python3 -m json.tool
echo ""
echo ""

# Test Type B: Build query (should ask questions)
echo "5. Type B Test: Build Query"
echo "-----------------------------------"
echo "Query: 'build a todo app'"
echo "Expected: ASK_CLARIFICATION with questions"
echo ""
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "build a todo app",
    "user_id": "test_user",
    "session_id": "test_session"
  }' | python3 -m json.tool
echo ""
echo ""

# Test memory snapshot
echo "6. Memory Snapshot"
echo "-----------------------------------"
curl -s "$API_URL/memory/snapshot" | python3 -m json.tool
echo ""
echo ""

echo "=================================="
echo "TESTS COMPLETE"
echo "=================================="
