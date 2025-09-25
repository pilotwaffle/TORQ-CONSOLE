#!/bin/bash

# TORQ Console API Integration Validator (Bash Version)
# Tests all three APIs: DeepSeek, Google Search, Brave Search

echo "🚀 TORQ Console API Integration Validation"
echo "=========================================="

# Load environment variables
DEEPSEEK_API_KEY="sk-1061efb8089744dcad1183fb2ef55960"
GOOGLE_API_KEY="AIzaSyA7eNQYC-zgo2OTYjL4QnrT5GeoHxJAhDw"
GOOGLE_ENGINE_ID="34dd471ccd5dd4572"
BRAVE_API_KEY="BSAkNrh316HK8uxqGjUN1_eeLon8PfO"

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo ""
echo "🔑 Testing API Key Configuration..."
echo "   - DeepSeek API Key: ${DEEPSEEK_API_KEY:0:15}..."
echo "   - Google API Key: ${GOOGLE_API_KEY:0:15}..."
echo "   - Brave API Key: ${BRAVE_API_KEY:0:15}..."

# Test 1: DeepSeek API
echo ""
echo "🧠 Testing DeepSeek API..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))

DEEPSEEK_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    -X POST "https://api.deepseek.com/chat/completions" \
    -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": "What is digital transformation? Answer in 20 words."
            }
        ],
        "max_tokens": 50
    }' \
    --max-time 30)

DEEPSEEK_STATUS=$(echo $DEEPSEEK_RESPONSE | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
DEEPSEEK_BODY=$(echo $DEEPSEEK_RESPONSE | sed 's/HTTPSTATUS:[0-9]*$//')

if [ "$DEEPSEEK_STATUS" = "200" ]; then
    echo "   ✅ DeepSeek API: SUCCESS (HTTP $DEEPSEEK_STATUS)"
    echo "   📝 Response preview: $(echo $DEEPSEEK_BODY | head -c 100)..."
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "   ❌ DeepSeek API: FAILED (HTTP $DEEPSEEK_STATUS)"
    echo "   📝 Error: $(echo $DEEPSEEK_BODY | head -c 200)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 2: Google Custom Search API
echo ""
echo "🔍 Testing Google Custom Search API..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))

GOOGLE_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    "https://www.googleapis.com/customsearch/v1?key=$GOOGLE_API_KEY&cx=$GOOGLE_ENGINE_ID&q=business+intelligence+2024&num=3" \
    --max-time 15)

GOOGLE_STATUS=$(echo $GOOGLE_RESPONSE | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
GOOGLE_BODY=$(echo $GOOGLE_RESPONSE | sed 's/HTTPSTATUS:[0-9]*$//')

if [ "$GOOGLE_STATUS" = "200" ]; then
    RESULTS_COUNT=$(echo $GOOGLE_BODY | grep -o '"title"' | wc -l)
    echo "   ✅ Google Search API: SUCCESS (HTTP $GOOGLE_STATUS)"
    echo "   📊 Results returned: $RESULTS_COUNT"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "   ❌ Google Search API: FAILED (HTTP $GOOGLE_STATUS)"
    echo "   📝 Error: $(echo $GOOGLE_BODY | head -c 200)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 3: Brave Search API
echo ""
echo "🦁 Testing Brave Search API..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))

BRAVE_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    -H "Accept: application/json" \
    -H "Accept-Encoding: gzip" \
    -H "X-Subscription-Token: $BRAVE_API_KEY" \
    "https://api.search.brave.com/res/v1/web/search?q=digital+transformation+strategy&count=3" \
    --max-time 15)

BRAVE_STATUS=$(echo $BRAVE_RESPONSE | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
BRAVE_BODY=$(echo $BRAVE_RESPONSE | sed 's/HTTPSTATUS:[0-9]*$//')

if [ "$BRAVE_STATUS" = "200" ]; then
    RESULTS_COUNT=$(echo $BRAVE_BODY | grep -o '"title"' | wc -l)
    echo "   ✅ Brave Search API: SUCCESS (HTTP $BRAVE_STATUS)"
    echo "   📊 Results returned: $RESULTS_COUNT"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "   ❌ Brave Search API: FAILED (HTTP $BRAVE_STATUS)"
    echo "   📝 Error: $(echo $BRAVE_BODY | head -c 200)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Calculate success rate
SUCCESS_RATE=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))

# Generate final report
echo ""
echo "==============================================="
echo "🏆 FINAL VALIDATION REPORT"
echo "==============================================="
echo "📊 Total Tests: $TOTAL_TESTS"
echo "✅ Passed: $PASSED_TESTS"
echo "❌ Failed: $FAILED_TESTS"
echo "📈 Success Rate: $SUCCESS_RATE%"
echo ""

# API Status Summary
echo "🔍 API STATUS SUMMARY:"
echo "   • DeepSeek API: $([ "$DEEPSEEK_STATUS" = "200" ] && echo "✅ OPERATIONAL" || echo "❌ FAILED")"
echo "   • Google Search API: $([ "$GOOGLE_STATUS" = "200" ] && echo "✅ OPERATIONAL" || echo "❌ FAILED")"
echo "   • Brave Search API: $([ "$BRAVE_STATUS" = "200" ] && echo "✅ OPERATIONAL" || echo "❌ FAILED")"

echo ""
echo "💡 RECOMMENDATIONS:"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo "   ✅ All APIs validated successfully - READY FOR PRODUCTION"
    echo "   🚀 Integration testing complete - No issues detected"
    echo "   📊 Monitor usage quotas: Google (100/day), Brave (2000/month)"
elif [ $PASSED_TESTS -gt $((TOTAL_TESTS / 2)) ]; then
    echo "   ⚠️  Partial success - Review failed API configurations"
    echo "   🔧 Check API keys and network connectivity for failed services"
    echo "   📋 Consider fallback mechanisms for failed APIs"
else
    echo "   ❌ Critical failures detected - NOT READY FOR DEPLOYMENT"
    echo "   🔧 Verify all API keys are correct and active"
    echo "   🌐 Check network connectivity and firewall settings"
fi

echo ""
echo "📄 Validation completed: $(date)"
echo "==============================================="

# Exit with appropriate code
if [ $SUCCESS_RATE -ge 75 ]; then
    exit 0
else
    exit 1
fi