# Enhanced Prince Flowers - API Testing Guide

## Quick Start: Test Enhanced Prince with REST API

This guide shows you how to test Enhanced Prince Flowers using a REST API endpoint, which can be:
1. Tested directly with `curl` commands
2. Configured as a backend in Maxim.ai workflows
3. Integrated into your own testing pipelines

---

## Step 1: Start the API Server

```bash
# 1. Set your API key (Anthropic Claude recommended)
export ANTHROPIC_API_KEY="your-api-key-here"

# Or use OpenAI
export OPENAI_API_KEY="your-api-key-here"

# 2. Install dependencies (if needed)
pip install fastapi uvicorn

# 3. Start the server
python enhanced_prince_api.py
```

**Expected Output:**
```
================================================================================
ENHANCED PRINCE FLOWERS - REST API SERVER
================================================================================
✅ API key configured
✅ Enhanced Prince initialized
✅ Agent memory initialized

🚀 Server ready!
   • Endpoint: http://localhost:8000/chat
   • Docs: http://localhost:8000/docs
   • Health: http://localhost:8000/health

================================================================================
```

---

## Step 2: Test with Curl Commands

### Quick Test Script

```bash
# Run all tests at once
./test_prince_api.sh
```

### Manual Testing

#### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "enhanced_prince_available": true,
  "agent_memory_available": true,
  "api_key_configured": true
}
```

#### Test 2: Type A Query (Research - CRITICAL TEST)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Search the latest AI news 11/08/25"
  }'
```

**Expected Response:**
```json
{
  "response": "Based on my search, here are the latest AI news stories from November 8, 2025: ...",
  "action_taken": "IMMEDIATE_ACTION",
  "interaction_id": "interaction_1",
  "debug_info": {
    "query_length": 35,
    "response_length": 500,
    "session_id": "default",
    "user_id": "test_user"
  }
}
```

**❌ WRONG Response (if bug still exists):**
```json
{
  "response": "I'll create a TypeScript application to search AI news...",
  "action_taken": "IMMEDIATE_ACTION (ERROR: generated code)",
  ...
}
```

#### Test 3: Type A Query - Research Keyword (CRITICAL TEST)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Research new updates coming to GLM-4.6"
  }'
```

**Expected:** `"action_taken": "IMMEDIATE_ACTION"` (with WebSearch results)
**Wrong:** `"action_taken": "IMMEDIATE_ACTION (ERROR: generated code)"`

#### Test 4: Type B Query (Build - Should Ask Questions)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "build a todo app"
  }'
```

**Expected Response:**
```json
{
  "response": "I'll help build that. Quick questions:\n1. What data do you need to store?\n2. Web or mobile?\n3. Framework preference?\n\nThen I'll implement it.",
  "action_taken": "ASK_CLARIFICATION",
  ...
}
```

#### Test 5: Submit Feedback
```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "interaction_id": "interaction_1",
    "score": 0.9,
    "comment": "Excellent response!"
  }'
```

#### Test 6: Memory Snapshot
```bash
curl http://localhost:8000/memory/snapshot
```

---

## Step 3: Configure in Maxim.ai

### Option A: Use Local Endpoint

1. **Start the API server** (as shown above)
2. **Make it accessible** to Maxim.ai:
   ```bash
   # If running locally, use ngrok or similar to expose localhost:8000
   ngrok http 8000

   # Copy the ngrok URL (e.g., https://abc123.ngrok.io)
   ```

3. **Configure in Maxim.ai workflow:**
   - Go to your workspace: https://app.getmaxim.ai/workspace/cmhqimzv9007c11ofecpe69n1/home
   - Create or edit a workflow
   - Set endpoint URL: `https://abc123.ngrok.io/chat`
   - Set method: `POST`
   - Set request body format:
     ```json
     {
       "query": "{{input.query}}",
       "user_id": "{{user.id}}",
       "session_id": "{{session.id}}"
     }
     ```

### Option B: Deploy to Production

Deploy the API server to:
- **Heroku**: `heroku create && git push heroku main`
- **AWS Lambda**: Use AWS SAM or Serverless framework
- **Google Cloud Run**: `gcloud run deploy`
- **DigitalOcean App Platform**: Connect your repo

Then use the production URL in Maxim.ai.

---

## Step 4: Run Maxim.ai Test Suite

Once your endpoint is configured in Maxim.ai:

### Option 1: Use the Endpoint Tester Script

```bash
# Update test_prince_maxim_endpoint.py with your endpoint URL
python test_prince_maxim_endpoint.py
```

### Option 2: Import Test Suite YAML

1. Go to Maxim.ai workspace
2. Import `maxim_ai_test_suite.yaml`
3. Configure it to use your endpoint
4. Run the test suite

### Option 3: Use SDK Integration

```bash
python maxim_integration.py
```

---

## Test Results Interpretation

### ✅ PASSING Tests

**Type A (Research) Tests:**
```json
{
  "action_taken": "IMMEDIATE_ACTION",
  "response": "Based on my search, here are the results..."
}
```
- ✅ Used WebSearch
- ✅ Did NOT generate code
- ✅ Returned actual search results

**Type B (Build) Tests:**
```json
{
  "action_taken": "ASK_CLARIFICATION",
  "response": "I'll help build that. Quick questions: ..."
}
```
- ✅ Asked clarifying questions
- ✅ Did NOT immediately generate code

### ❌ FAILING Tests

**Type A Failure (Critical):**
```json
{
  "action_taken": "IMMEDIATE_ACTION (ERROR: generated code)",
  "response": "I'll create a TypeScript application..."
}
```
- ❌ Generated code instead of searching
- ❌ Wrong behavior for research query

**Type B Failure:**
```json
{
  "action_taken": "ASK_CLARIFICATION (ERROR: code without questions)",
  "response": "Here's your todo app: ```typescript..."
}
```
- ❌ Generated code without asking questions
- ❌ Rushed to implementation

---

## Critical Test Cases

These are the EXACT queries that failed in your feedback:

| Test | Query | Expected | Historical Behavior |
|------|-------|----------|---------------------|
| 1 | "search for top 3 posts on x.com" | ✅ Search results | ✅ Worked correctly |
| 2 | "Search the latest AI news 11/08/25" | ✅ Search results | ❌ Generated TypeScript |
| 3 | "Research new updates coming to GLM-4.6" | ✅ Search results | ❌ Generated TypeScript |
| 4 | "No that's not right" (after wrong response) | ✅ Change approach | ❌ Generated MORE TypeScript |

**All 4 tests MUST pass** for the fix to be considered successful.

---

## Debugging

### Server Logs

The API server prints detailed logs:
```
[INFO] Received query: "Search the latest AI news"
[INFO] Enhanced Prince analyzing request...
[INFO] Action decision: IMMEDIATE_ACTION
[INFO] Using WebSearch tool...
[INFO] Response generated: 450 characters
```

Watch for:
- ✅ "Action decision: IMMEDIATE_ACTION" for research queries
- ✅ "Using WebSearch tool" for research queries
- ❌ "Generating code" for research queries (wrong!)
- ❌ "Action decision: ASK_CLARIFICATION" for simple research (wrong!)

### Interactive Testing

Visit the auto-generated API docs:
```
http://localhost:8000/docs
```

This provides an interactive UI to test all endpoints.

---

## Next Steps

1. **Start the server**: `python enhanced_prince_api.py`
2. **Run curl tests**: `./test_prince_api.sh`
3. **Check critical tests**: Verify all 4 critical queries pass
4. **If passing**: Deploy to production and configure in Maxim.ai
5. **If failing**: Report results - may need to implement Phases 2-5 of the fix plan

---

## URLs for Your Workspace

- **Workspace**: https://app.getmaxim.ai/workspace/cmhqimzv9007c11ofecpe69n1/home
- **Original Endpoint**: https://app.getmaxim.ai/workspace/cmhqimzv9007c11ofecpe69n1/workflow/endpoint/cmhqirw9e00aq11ofctjq7rp7
- **Local API**: http://localhost:8000/chat (when server running)

---

## Files Created

- `enhanced_prince_api.py` - FastAPI server for Enhanced Prince
- `test_prince_api.sh` - Curl test script
- `ENHANCED_PRINCE_API_TESTING.md` - This guide
- `test_prince_maxim_endpoint.py` - Maxim.ai endpoint tester
- `maxim_integration.py` - SDK integration
- `maxim_ai_test_suite.yaml` - Test scenarios

---

**Ready to test!** 🚀

Start the server and run the tests to verify Enhanced Prince's behavior.
