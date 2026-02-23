# TORQ Console - Railway Deployment Guide

## Overview

Railway runs the full TORQ Console backend including:
- Prince Flowers agent with learning hook
- Query router with Q-values
- Experience replay engine
- All telemetry + learning endpoints

## Prerequisites

1. Railway account (https://railway.app)
2. Supabase project with all migrations applied
3. GitHub repo connected to Railway

## Step 1: Create Railway Project

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select: `pilotwaffle/TORQ-CONSOLE`
4. Branch: `main`
5. Click "Deploy"

## Step 2: Configure the Service

After initial deploy, click into your service and configure:

### Environment Variables (Settings → Environment Variables)

```bash
# Supabase (required for telemetry + learning)
SUPABASE_URL=https://npukynbaglmcdvzyklqa.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5wdWt5bmJhZ2xtY2R2enlrbGFhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTU2MDUzNCwiZXhwIjoyMDg3MTM2NTM0fQ.-O3TTF2rr9_kUfOk9oD5Q_Fe494wtPxHOJsga5oT7Pk

# LLM Keys (required for agent)
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here

# Learning System (optional, recommended)
TORQ_ADMIN_TOKEN=your_secure_random_string

# Proxy Secret (for Vercel → Railway)
TORQ_PROXY_SHARED_SECRET=your_shared_secret_here

# Production mode
TORQ_CONSOLE_PRODUCTION=true
TORQ_DISABLE_LOCAL_LLM=true
TORQ_DISABLE_GPU=true
```

### Root Directory

Set to: `/` (repo root)

### Build Command

```bash
python -m pip install -r requirements-railway.txt
```

### Start Command

```bash
uvicorn torq_console.ui.railway_app:app --host 0.0.0.0 --port ${PORT}
```

## Step 3: Get Your Railway URL

After deployment, Railway will give you a URL like:
```
https://torq-console-production.up.railway.app
```

Copy this — you'll need it for Vercel environment variables.

## Step 4: Configure Vercel to Proxy to Railway

In Vercel Dashboard → Project → Settings → Environment Variables:

```bash
TORQ_BACKEND_URL=https://torq-console-production.up.railway.app
TORQ_PROXY_SHARED_SECRET=same_value_as_railway
TORQ_PROXY_TIMEOUT_MS=30000
```

Then redeploy Vercel.

## Step 5: Verify the Connection

Test from your terminal:

```bash
# Test Railway health
curl https://torq-console-production.up.railway.app/health

# Test Vercel proxy
curl -X POST https://torq-console.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello from Vercel!"}'
```

## Step 6: Add Proxy Secret Middleware to Railway

Create a new file `torq_console/api/middleware.py`:

```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class ProxySecretMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Require proxy secret for sensitive endpoints
        if request.url.path in ["/api/chat", "/api/learning", "/api/telemetry"]:
            secret = request.headers.get("x-torq-proxy-secret")
            expected = os.environ.get("TORQ_PROXY_SHARED_SECRET")

            if not secret or secret != expected:
                raise HTTPException(status_code=403, detail="Forbidden: Invalid proxy secret")

        response = await call_next(request)
        return response
```

Then add to `torq_console/ui/railway_app.py`:

```python
app.add_middleware(ProxySecretMiddleware)
```

## What This Enables

✅ Vercel serves the fast frontend
✅ Railway runs the full agent with learning
✅ Every chat triggers the learning hook
✅ Telemetry + learning events write to Supabase
✅ Q-values update via experience replay
✅ Policy versioning works via Supabase

## Troubleshooting

### Railway service not starting
- Check logs in Railway dashboard
- Verify PYTHONPATH in Dockerfile
- Check that all requirements install

### Vercel proxy failing
- Verify TORQ_BACKEND_URL is correct (no trailing slash)
- Check Railway service is running
- Look for CORS errors in browser console

### Learning events not appearing
- Verify SUPABASE_SERVICE_ROLE_KEY is set (not anon key)
- Check that migrations 01-10 have been run
- Check Railway logs for errors during learning hook execution
