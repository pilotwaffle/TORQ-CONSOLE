# Prince Flowers Agent - Chat Endpoint Configuration

**Date:** 2026-03-05
**Status:** 🔄 Configuration Update Deployed - Awaiting Vercel Env Var

---

## Problem Identified

The `/api/chat` endpoint was returning `403: Invalid proxy secret` because:

1. **Railway** requires `TORQ_PROXY_SHARED_SECRET` for protected endpoints (`/api/chat`, `/api/learning`, `/api/telemetry`)
2. **Vercel frontend** was calling `/api/chat` without the required `x-torq-proxy-secret` header
3. No API proxy was configured between Vercel and Railway

---

## Solution Implemented

### 1. Updated Vercel Configuration (`frontend/vercel.json`)

Added API route proxying to Railway with authentication header:

```json
{
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "https://web-production-74ed0.up.railway.app/api/$1",
      "headers": {
        "x-torq-proxy-secret": "${TORQ_PROXY_SHARED_SECRET}"
      }
    }
  ]
}
```

### 2. Deployed to GitHub

- Commit: `b7af3bf7` - "feat: add Vercel API proxy to Railway with proxy secret auth"
- Pushed to `main` branch

---

## Action Required: Configure Vercel Environment Variable

**You must add the `TORQ_PROXY_SHARED_SECRET` to Vercel:**

### Option A: Via Vercel Dashboard
1. Go to: https://vercel.com/pilotwaffle/torq-console/settings/environment-variables
2. Click "Add New"
3. **Key:** `TORQ_PROXY_SHARED_SECRET`
4. **Value:** [Same value as set on Railway]
5. **Environments:** Production (and Preview/Development if needed)
6. Click "Save"

### Option B: Via Vercel CLI
```bash
vercel env add TORQ_PROXY_SHARED_SECRET production
# Paste the secret value when prompted
```

---

## Verification Steps

After adding the environment variable:

1. **Wait for Vercel redeployment** (~1-2 minutes)

2. **Test the chat endpoint through Vercel:**
   ```bash
   curl -X POST https://torq-console.vercel.app/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello Prince Flowers!", "session_id": "test"}'
   ```

3. **Expected response:**
   ```json
   {
     "response": "[AI response from Prince Flowers]",
     "session_id": "test",
     "trace_id": "chat-...",
     "agent": "prince_flowers",
     "backend": "railway",
     "learning_recorded": true,
     "duration_ms": 1234
   }
   ```

---

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Railway `/api/chat`** | ✅ Working | Protected endpoint, requires proxy secret |
| **Vercel Proxy Config** | ✅ Deployed | Routes `/api/*` to Railway with auth header |
| **Vercel Env Var** | ⚠️ PENDING | `TORQ_PROXY_SHARED_SECRET` needs to be set |
| **Prince Flowers Agent** | ⚠️ BLOCKED | Waiting for Vercel env var |

---

## How It Works

```
User → Vercel Frontend → Vercel API Proxy → Railway Backend
                              ↓
                         Adds header:
                         x-torq-proxy-secret:
                         [from env var]
```

---

## Security Notes

1. **Proxy Secret**: Shared secret between Vercel and Railway
2. **Protected Endpoints**:
   - `/api/chat` - Prince Flowers agent chat
   - `/api/learning/*` - Learning system
   - `/api/telemetry` - Telemetry ingestion
3. **Public Endpoints** (no secret required):
   - `/health` - Health check
   - `/api/knowledge/*` - Knowledge Plane

---

## Next Steps

1. ✅ Vercel proxy configuration deployed
2. ⏳ **ACTION REQUIRED**: Add `TORQ_PROXY_SHARED_SECRET` to Vercel environment variables
3. ⏳ Wait for Vercel redeployment
4. ⏳ Test chat endpoint through Vercel

Once complete, the Prince Flowers agent will be fully operational through the Vercel frontend!
