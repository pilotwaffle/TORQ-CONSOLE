# TORQ Multi-Agent System - Implementation Status & Next Steps

**Date:** 2026-03-05
**Status:** ✅ Backend Fully Operational | ⚠️ Frontend API Proxy Blocked

---

## What's Working ✅

### Backend (Railway) - FULLY OPERATIONAL

All endpoints working via direct Railway access:

| Endpoint | Method | Description | Test |
|----------|--------|-------------|------|
| `/api/chat/health` | GET | Health check | ✅ Working |
| `/api/chat/agents` | GET | List agents with metadata | ✅ Working |
| `/api/chat/agents/{id}` | GET | Agent details | ✅ Working |
| `/api/chat` | POST | **Unified chat endpoint** | ✅ Working |
| `/api/agent/registry` | GET | Original registry endpoint | ✅ Working |
| `/api/agent/orchestrate` | POST | Multi-agent orchestration | ✅ Working |

**Direct Railway URL:** `https://web-production-74ed0.up.railway.app`

### New Unified Chat API Contract

```bash
POST https://web-production-74ed0.up.railway.app/api/chat
Content-Type: application/json

{
  "message": "What is quantum computing?",
  "session_id": "session-123",
  "agent_id": "research_agent",     // Optional - if null, auto-route
  "mode": "auto"                    // auto|single|sequential|parallel|consensus|hierarchical
}
```

**Rules:**
- `agent_id` provided → Use that specific agent
- `agent_id` null → Auto-route based on query analysis
- `mode` "auto" → System chooses best approach
- `mode` multi-agent → Orchestrate multiple agents

### Agent Registry with UI Metadata

```json
{
  "agent_id": "research_agent",
  "agent_name": "Research Agent",
  "agent_type": "core",
  "capabilities": ["research", "analysis"],
  "status": "active",
  "speed": "deep",
  "best_for": ["Research", "Analysis", "Information gathering"],
  "tools": ["Web Search", "Document Analysis", "Data Extraction"]
}
```

---

## What's Not Working ⚠️

### Vercel → Railway API Proxy

**Problem:** Vercel's `vercel.json` rewrites don't forward to external URLs (Railway) as expected.

**Attempted Solutions:**
1. ✗ `routes` with `headers` - Environment variable expansion doesn't work
2. ✗ `rewrites` to external URL - Vercel doesn't support external destinations
3. ✗ Edge Functions - Vite SPA doesn't recognize the api/ folder

**Current State:** Frontend cannot access backend API through Vercel proxy.

---

## Solutions (In Order of Preference)

### Option 1: Make Endpoints Public (Simplest - Recommended)

Remove proxy authentication from agent endpoints:

**In `railway_app.py`:**
```python
# Already done for /api/chat/*
PROTECTED_PATHS = {"/api/learning", "/api/telemetry"}
```

**For Vercel:** Use rewrites that point to a backend service configured in Vercel project settings.

**Steps:**
1. In Vercel Dashboard → torq-console project → Settings → Environment Variables
2. Add `RAILWAY_BACKEND_URL` = `https://web-production-74ed0.up.railway.app`
3. Use serverless function or Edge Config to proxy

### Option 2: Vercel Edge Config (Production Approach)

Create `vercel.json` with edge config:

```json
{
  "buildCommand": "npx vite build",
  "outputDirectory": "dist",
  "edge": {
    "routes": [
      {
        "src": "/api/(.*)",
        "dest": "https://web-production-74ed0.up.railway.app/api/$1",
        "headers": {
          "Access-Control-Allow-Origin": "*"
        }
      }
    ]
  }
}
```

Note: Edge config format varies - verify in Vercel docs.

### Option 3: Frontend Calls Railway Directly (Current Workaround)

Update frontend service to call Railway directly:

```typescript
// In agentRegistryService.ts
private baseUrl = 'https://web-production-74ed0.up.railway.app/api/agent';
```

**Pros:** Works immediately
**Cons:** CORS issues possible, couples frontend to Railway URL

### Option 4: Use Railway Custom Domain

1. Set up custom domain on Railway (e.g., `api.torq.console`)
2. Update frontend to use `https://api.torq.console`
3. No proxy needed

---

## How Users Can Use Agents RIGHT NOW

### Direct API (Working)

```bash
# Chat with auto-routing
curl -X POST https://web-production-74ed0.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum computing",
    "session_id": "test-123",
    "mode": "auto"
  }'

# Chat with specific agent
curl -X POST https://web-production-74ed0.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Debug this code",
    "session_id": "test-123",
    "agent_id": "workflow_agent",
    "mode": "single"
  }'

# Multi-agent orchestration
curl -X POST https://web-production-74ed0.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze Tesla from multiple perspectives",
    "session_id": "test-123",
    "mode": "parallel"
  }'

# List agents
curl https://web-production-74ed0.up.railway.app/api/chat/agents
```

### Web UI (Partial)

**URL:** https://torq-console.vercel.app

**Current State:**
- Sidebar shows hardcoded agents
- Chat works but doesn't reach backend
- Need to implement direct Railway calls

---

## Files Changed/Added

| File | Status | Description |
|------|--------|-------------|
| `railway_orchestration_v2.py` | ✅ Created | Unified chat API with improved contract |
| `railway_app.py` | ✅ Updated | Added v2 router, removed /api/chat from protected paths |
| `frontend/vercel.json` | ⚠️ Updated | Attempted proxy config (not working) |
| `frontend/api/chat.ts` | ✗ Created | Edge function (not used by Vite) |

---

## Next Steps for Full Integration

1. **Fix Vercel Proxy** - Choose one of the 4 options above
2. **Update Frontend Service** - Use Railway direct URL as fallback
3. **Add Agent Mode Selector** - UI control for mode selection
4. **Display Agent Metadata** - Show speed, best_for, tools in UI

---

## Quick Test Commands

```bash
# Test Railway direct (should work)
curl https://web-production-74ed0.up.railway.app/api/chat/health

# Test Vercel proxy (currently broken)
curl https://torq-console.vercel.app/api/chat/health

# Test unified chat
curl -X POST https://web-production-74ed0.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test", "mode": "auto"}'
```

---

## Summary

| Component | Status |
|-----------|--------|
| **Unified Chat API** | ✅ Working on Railway |
| **Agent Registry** | ✅ Working with metadata |
| **Orchestration** | ✅ All modes working |
| **Vercel Proxy** | ❌ Blocked - needs solution |
| **Frontend Integration** | ⚠️ Partial - needs Railway direct calls |

**Bottom Line:** The Multi-Agent Orchestration System is **fully functional via direct Railway API calls**. The Vercel proxy issue is a deployment configuration problem that requires one of the 4 solutions above.
