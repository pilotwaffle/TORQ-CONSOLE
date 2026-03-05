# TORQ Console Deployment Architecture

**Last Updated:** 2026-03-04
**Architecture:** Vercel Frontend + Railway Backend
**Status:** ✅ Production Active

---

## Overview

TORQ Console uses a **split deployment architecture**:
- **Frontend (Vercel)**: `https://torq-console.vercel.app/` - React/Vite UI
- **Backend (Railway)**: FastAPI Python service - AI agents & APIs
- **Database (Supabase)**: `npukynbaglmcdvzyklqa.supabase.co` - Learning events & telemetry

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Vercel (torq-console.vercel.app)                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Frontend: React/Vite UI (frontend/dist)                 │  │
│  │  - Static assets served by Vercel CDN                    │  │
│  │  - Rewrites /api/* requests to Railway backend           │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ API Calls (/api/*, /health)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Railway Backend                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI App (torq_console.ui.railway_app)              │  │
│  │  - /api/chat - Agent chat with learning hook             │  │
│  │  - /api/telemetry/* - Telemetry ingestion                │  │
│  │  - /api/learning/* - Learning policy management          │  │
│  │  - /api/debug/deploy - Deploy identity endpoint          │  │
│  │  - /health - Health check                                │  │
│  │  - /api/traces/* - Trace explorer                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Telemetry & Learning Data
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Supabase (npukynbaglmcdvzyklqa.supabase.co)                    │
│  Dashboard: https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Telemetry Tables:                                       │  │
│  │  - telemetry_traces - Trace metadata                     │  │
│  │  - telemetry_spans - Span timing & LLM usage             │  │
│  │  Learning Tables:                                         │  │
│  │  - learning_events - RL training data with embeddings    │  │
│  │  - learning_policies - Policy version management         │  │
│  │  Features:                                               │  │
│  │  - pgvector extension for similarity search              │  │
│  │  - Row Level Security (RLS) enabled                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuration Files

### Vercel Configuration (`vercel.json`)

```json
{
  "name": "torq-console",
  "buildCommand": "cd frontend && test -f src/components/ui/Badge.tsx && npm install && npx vite build",
  "outputDirectory": "frontend/dist",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "/api/index.py"
    },
    {
      "source": "/health",
      "destination": "/api/index.py"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

**Key Points:**
- Builds from `frontend/` directory using Vite
- Rewrites `/api/*` requests to backend (proxies to Railway)
- Static files served from `frontend/dist`

### Railway Configuration (`railway.json`)

```json
{
  "deploy": {
    "startCommand": "python -m torq_console.ui.start_railway",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ALWAYS",
    "numReplicas": 1
  }
}
```

**Key Points:**
- Runs FastAPI via `uvicorn torq_console.ui.railway_app:app`
- Health check on `/health` endpoint
- Auto-restart on failure

---

## Active Endpoints (Railway Backend)

Based on Railway logs, these endpoints are actively being called:

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/health` | GET | Health check | ✅ Active |
| `/api/debug/deploy` | GET | Deploy identity (git_sha, version) | ✅ Active |
| `/api/learning/status` | GET | Learning system status | ✅ Active |
| `/api/telemetry/health` | GET | Telemetry diagnostics | ✅ Active |
| `/api/traces` | GET | List telemetry traces | ✅ Active |

### Recent Log Activity (March 2026)

```
INFO: 100.64.0.19:52906 - "GET /api/debug/deploy HTTP/1.1" 200 OK
INFO: 100.64.0.7:23322 - "GET /api/learning/status HTTP/1.1" 200 OK
INFO: 100.64.0.4:54666 - "GET /api/telemetry/health HTTP/1.1" 200 OK
INFO: 100.64.0.13:53860 - "GET /api/traces?limit=5&path=traces HTTP/1.1" 200 OK
```

---

## Supabase Database Schema

### Project Reference
- **Project URL**: `https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa`
- **API URL**: `https://npukynbaglmcdvzyklqa.supabase.co`
- **Region**: (check dashboard)

### Tables

#### Telemetry Tables

**`telemetry_traces`** - Request/response metadata
| Column | Type | Description |
|--------|------|-------------|
| `trace_id` | TEXT | Unique trace identifier |
| `session_id` | TEXT | User session ID |
| `user_id` | TEXT | User identifier |
| `meta` | JSONB | Trace metadata |
| `started_at` | TIMESTAMPTZ | Trace start time |
| `ended_at` | TIMESTAMPTZ | Trace end time |
| `error_code` | TEXT | Error code if failed |
| `error_message` | TEXT | Error message if failed |

**`telemetry_spans`** - Individual operation timing
| Column | Type | Description |
|--------|------|-------------|
| `span_id` | TEXT | Unique span identifier |
| `trace_id` | TEXT | Parent trace ID |
| `parent_span_id` | TEXT | Parent span (for nested ops) |
| `kind` | TEXT | Span type (internal/llm/tool) |
| `name` | TEXT | Operation name |
| `duration_ms` | INTEGER | Duration in milliseconds |
| `start_ms` | BIGINT | Start timestamp (ms) |
| `end_ms` | BIGINT | End timestamp (ms) |
| `attributes` | JSONB | Span attributes |
| `provider` | TEXT | LLM provider (anthropic/openai) |
| `model` | TEXT | Model name (claude-sonnet-4-6) |
| `tokens_in` | INTEGER | Input tokens |
| `tokens_out` | INTEGER | Output tokens |
| `tokens_total` | INTEGER | Total tokens |
| `error_code` | TEXT | Error code if failed |
| `error_message` | TEXT | Error message if failed |

#### Learning Tables

**`learning_events`** - RL training data with vector embeddings
| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `event_id` | TEXT UNIQUE | Unique event identifier |
| `created_at` | TIMESTAMPTZ | Event timestamp |
| `query` | TEXT | User query |
| `query_embedding` | VECTOR(1536) | OpenAI embedding for similarity |
| `mode` | TEXT | Agent mode used |
| `success` | BOOLEAN | Whether outcome was successful |
| `reward` | DECIMAL(5,4) | Calculated reward (0.0-1.0) |
| `execution_time` | DECIMAL(8,3) | Response time |
| `outcome` | TEXT | Outcome description |
| `tools_used` | TEXT[] | Tools used in response |
| `metadata` | JSONB | Additional metadata |

**`learning_policies`** - Policy version management
| Column | Type | Description |
|--------|------|-------------|
| `policy_id` | TEXT | Policy identifier |
| `routing_data` | JSONB | Routing configuration |
| `status` | TEXT | Policy status |
| `approved_at` | TIMESTAMPTZ | Approval timestamp |
| `created_by` | TEXT | Admin who approved |

### Supabase API Endpoints

```bash
# Read traces
GET https://npukynbaglmcdvzyklqa.supabase.co/rest/v1/telemetry_traces
Headers: apikey=<SUPABASE_KEY>, Authorization: Bearer <SUPABASE_KEY>

# Read spans
GET https://npukynbaglmcdvzyklqa.supabase.co/rest/v1/telemetry_spans
Headers: apikey=<SUPABASE_KEY>, Authorization: Bearer <SUPABASE_KEY>

# Write learning event
POST https://npukynbaglmcdvzyklqa.supabase.co/rest/v1/learning_events
Headers: apikey=<SUPABASE_KEY>, Authorization: Bearer <SUPABASE_KEY>

# Vector similarity search
POST https://npukynbaglmcdvzyklqa.supabase.co/rest/v1/rpc/match_learning_events
```

### Indexes

```sql
-- Telemetry indexes
idx_telemetry_traces_trace_id
idx_telemetry_traces_session_id
idx_telemetry_spans_trace_id
idx_telemetry_spans_span_id
idx_telemetry_spans_parent_span_id
idx_telemetry_spans_start_ms

-- Learning indexes (ivfflat for vector)
idx_learning_events_query_embedding (ivfflat)
idx_learning_events_mode
idx_learning_events_success
idx_learning_events_created_at
```

### Row Level Security (RLS)

- **Enabled** on all tables
- **Service role** has full access for Railway backend
- **Policies**:
  - `"Service role full access"` - Allows `auth.role() = 'service_role'`

### Migrations

Located in `E:\TORQ-CONSOLE\supabase\migrations\`:
- `99_canonical_telemetry_schema.sql` - Telemetry schema
- `03_schema_fix.sql` - Schema fixes
- `06_complete_schema_fix.sql` - Complete fix

Schema file: `E:\TORQ-CONSOLE\supabase_learning_schema.sql`

---

## Environment Variables

### Vercel Environment
```bash
TORQ_CONSOLE_PRODUCTION=true
TORQ_DISABLE_LOCAL_LLM=true
TORQ_DISABLE_GPU=true
PYTHON_VERSION=3.11
```

### Railway Environment (required)
```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-***

# Supabase (Project: npukynbaglmcdvzyklqa)
SUPABASE_URL=https://npukynbaglmcdvzyklqa.supabase.co
SUPABASE_SERVICE_ROLE_KEY=***  # or SUPABASE_ANON_KEY

# Security
TORQ_PROXY_SECRET=***          # Shared secret with Vercel
TORQ_ADMIN_TOKEN=***           # Admin operations

# Optional
TORQ_TELEMETRY_ENABLED=true
TORQ_TELEMETRY_STRICT=false    # Best-effort mode
TORQ_LEARNING_POLICY_VERSION=1.0.0
```

---

## Deployment Workflow

### Deploying Changes

1. **Frontend Changes** (React/Vite)
   ```bash
   # Commit to control-plane-v1-clean branch
   git add frontend/
   git commit -m "feat: UI update"
   git push origin control-plane-v1-clean

   # Vercel auto-deploys from GitHub
   # Visit: https://vercel.com/pilotwaffles-projects/torq-console
   ```

2. **Backend Changes** (Python/FastAPI)
   ```bash
   # Commit to control-plane-v1-clean branch
   git add torq_console/
   git commit -m "feat: API update"
   git push origin control-plane-v1-clean

   # Railway auto-deploys from GitHub
   # Visit: https://railway.com/project/...
   ```

3. **Full Stack Changes**
   ```bash
   # Both frontend and backend
   git add frontend/ torq_console/
   git commit -m "feat: Full stack update"
   git push origin control-plane-v1-clean

   # Vercel and Railway deploy independently
   ```

---

## URLs & Links

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | https://torq-console.vercel.app/ | Main UI |
| **Vercel Dashboard** | https://vercel.com/pilotwaffles-projects/torq-console | Deployment settings |
| **Railway Service** | https://railway.com/project/.../service/... | Backend logs & config |
| **Supabase Dashboard** | https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa | Database & SQL |
| **GitHub Repo** | https://github.com/pilotwaffle/TORQ-CONSOLE | Source code |
| **Active Branch** | control-plane-v1-clean | Production branch |

---

## Health Check Commands

### Check Frontend
```bash
curl https://torq-console.vercel.app/
```

### Check Backend (Railway)
```bash
curl https://<your-railway-public-domain>/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "torq-console-railway",
  "git_sha": "fe821df71772",
  "app_version": "1.0.10-standalone",
  "supabase_configured": true,
  "anthropic_configured": true
}
```

### Check Deploy Identity
```bash
curl https://<your-railway-public-domain>/api/debug/deploy
```

Expected response:
```json
{
  "_schema": "torq-deploy-v1",
  "running_file": "torq_console/ui/railway_app.py",
  "git_sha": "fe821df71772",
  "app_version": "1.0.10-standalone",
  "platform": "railway",
  "anthropic_configured": true,
  "supabase_configured": true
}
```

---

## Troubleshooting

### Frontend Issues
1. Check Vercel deployment logs
2. Verify `frontend/dist` was built correctly
3. Check browser console for errors

### Backend Issues
1. Check Railway logs for errors
2. Verify environment variables are set
3. Check `/health` endpoint response
4. Review `/api/debug/deploy` for version info

### API Connection Issues
1. Verify `VITE_API_BASE` is set correctly (or empty for relative URLs)
2. Check Railway service is running
3. Verify CORS settings on Railway backend
4. Check `TORQ_PROXY_SECRET` matches between platforms

---

## Chrome Bridge Integration

The **Chrome Bridge** feature (commit `6262c384`) is available but:
- **Not deployed** to Vercel/Railway yet
- Requires local installation for browser automation
- See `CHROME_BRIDGE_README.md` for setup

---

## Additional Resources

- **API Contracts**: `torq_console/ui/api_contracts.py`
- **Railway App**: `torq_console/ui/railway_app.py`
- **Frontend API Service**: `frontend/src/dashboard/services/torqApi.ts`
- **Vercel Config**: `vercel.json`
- **Railway Config**: `railway.json`

---

*Generated: 2026-03-04*
*Architecture Version: 1.0.0*
