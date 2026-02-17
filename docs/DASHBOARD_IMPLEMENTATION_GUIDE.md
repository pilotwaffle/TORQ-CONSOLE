# TORQ Console Dashboard — Phase 1 Implementation Guide

## What's Been Built

### 1. TorqDashboard.jsx (Main Artifact)
Complete React dashboard with:
- **Chat interface** connecting to verified `POST /api/agents/{id}/chat` endpoint
- **Routing transparency** — RoutingBadge on every assistant message showing agent, capabilities, mode, success
- **Agent selector** dropdown (Prince Flowers, Orchestrator, Query Router)
- **Mode selector** (single_agent, multi_agent, pipeline, parallel)
- **Session management** — create, switch, delete sessions
- **System status** — polls `GET /api/status` every 30s
- **Demo mode** — works offline with simulated responses when backend is unavailable
- **Streaming indicator** — pulsing dot in TopNav when processing
- **Welcome screen** with suggestion cards

### 2. Backend Patches (patches/ folder)

#### `railway_app_patch.py`
The critical Step 0 fix. Adds this to `railway_app.py`:
```python
from torq_console.api.routes import router as api_router
app.include_router(api_router, prefix="/api")
```
This makes the 7 REST endpoints from routes.py available on Vercel/Railway.

#### `vercel.json.patched`
- Adds `maxDuration: 60` for the API function
- **Removes hardcoded API keys** (move to Vercel dashboard)

### 3. TypeScript Source Files (src/ folder)
Production-grade individual components for integration into the existing frontend:
- `types/api.ts` — TypeScript interfaces matching Pydantic models
- `services/torqApi.ts` — API client for all verified endpoints
- `stores/dashboardStore.ts` — Zustand store extending agentStore pattern
- `components/chat/RoutingBadge.tsx` — Collapsible routing metadata badge
- `components/chat/StreamingIndicator.tsx` — Processing indicator

---

## Deployment Steps

### Step 0: Backend Fix (REQUIRED — blocks everything)

1. **Rotate API keys** — your Anthropic and OpenAI keys in vercel.json are exposed
   - Generate new keys at https://console.anthropic.com and https://platform.openai.com
   - Add them in Vercel Dashboard → Settings → Environment Variables
   - Remove them from vercel.json

2. **Patch railway_app.py:**
   ```powershell
   cd E:\TORQ-CONSOLE
   # Edit torq_console/ui/railway_app.py
   # After the line `app = web_ui.app`, add:
   
   try:
       from torq_console.api.routes import router as api_router
       app.include_router(api_router, prefix="/api")
       logger.info("API routes mounted at /api")
   except Exception as e:
       logger.warning(f"Could not mount API routes: {e}")
   ```

3. **Update vercel.json** — replace with the patched version (patches/vercel.json.patched)

4. **Test locally:**
   ```powershell
   cd E:\TORQ-CONSOLE
   python start_web.py
   # Visit http://127.0.0.1:8000/api/agents — should return JSON
   # Visit http://127.0.0.1:8000/api/status — should return system status
   ```

### Step 1: Frontend Integration

**Option A: Use as standalone artifact (fastest)**
- The TorqDashboard.jsx file works as-is in Claude.ai artifacts
- Preview it to verify the UI, then adapt for your frontend

**Option B: Integrate into existing frontend**
1. Copy `src/types/api.ts` → `frontend/src/types/api.ts`
2. Copy `src/services/torqApi.ts` → `frontend/src/services/torqApi.ts`
3. Copy `src/stores/dashboardStore.ts` → `frontend/src/stores/dashboardStore.ts`
4. Copy `src/components/chat/RoutingBadge.tsx` → `frontend/src/components/chat/RoutingBadge.tsx`
5. Copy `src/components/chat/StreamingIndicator.tsx` → `frontend/src/components/chat/StreamingIndicator.tsx`
6. Update `frontend/src/App.tsx` to use the new dashboard components
7. Update existing `ChatWindow.tsx` and `ChatMessage.tsx` to include RoutingBadge

### Step 2: Deploy

```powershell
cd E:\TORQ-CONSOLE
git add -A
git commit -m "Phase 1: Dashboard with routing transparency"
git push origin main
# Vercel auto-deploys from main
```

---

## API Reference (Verified from source code)

| Endpoint | Method | Request Body | Response |
|----------|--------|-------------|----------|
| `/api/agents` | GET | — | `AgentInfo[]` |
| `/api/agents/{id}` | GET | — | `AgentInfo` |
| `/api/agents/{id}/chat` | POST | `{ message, mode? }` | `{ response, agent_id, timestamp, metadata }` |
| `/api/sessions` | GET | — | `SessionInfo[]` |
| `/api/sessions` | POST | `{ agent_id, metadata? }` | `SessionInfo` |
| `/api/sessions/{id}` | GET | — | `SessionInfo` |
| `/api/status` | GET | — | `SystemStatus` |
| `/health` | GET | — | `{ status, service }` |

## Architecture Notes

- **No streaming yet** — `process_query()` returns complete response. Phase 1b will add "fake SSE" (routing event + final event)
- **Demo mode** — Dashboard works offline with simulated responses. Backend connection auto-detected on mount.
- **Default model** — `anthropic/claude-sonnet-4-20250514` via `get_orchestrator()` singleton
- **OrchestrationMode.PIPELINE and .PARALLEL** are stubs — they just call prince_flowers.chat() once
