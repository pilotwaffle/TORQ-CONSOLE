# Railway Deployment Guide: control-plane-v1-clean

## Objective

Deploy TORQ Console with production-proof telemetry diagnostics including:
- `key_type_detected` field (detects service_role vs anon)
- `key_source` field (which env var provided the key)
- `access_test` field (read-only Supabase connectivity check)
- PGRST204 schema cache error handling

---

## Pre-Deployment Checklist

- [x] Duplicate SUPABASE_URL entries removed from `.env`
- [x] `railway.json` uses `$PORT` (not hardcoded 8080)
- [x] `torq_console/settings.py` added (runtime env reads)
- [x] `torq_console/telemetry/health.py` updated (access_test, PGRST204)
- [x] `verify_railway_deploy.py` added (deployment validation)
- [x] Branch `control-plane-v1-clean` pushed to GitHub

---

## Step 1: Configure Railway Service

### Navigate to Railway Project
```
https://railway.com/project/c6e58b87-d5f8-4819-86cb-1f34635616f3/service/2b12325d-6b35-445a-8b84-475c1e9bb27b
```

### Update Source Settings

1. **Settings** -> **Source**
2. **Repository**: `pilotwaffle/TORQ-CONSOLE`
3. **Branch**: `control-plane-v1-clean`
4. **Root Directory**: `/` (repo root)

### Verify Start Command

In **Settings** -> the start command should use `$PORT`:
```
python -m uvicorn torq_console.ui.railway_app:app --host 0.0.0.0 --port $PORT
```

Or via `railway.json` (already fixed):
```json
{
  "deploy": {
    "startCommand": "python -m uvicorn torq_console.ui.railway_app:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30
  }
}
```

---

## Step 2: Set Environment Variables

In **Variables** tab, set these **exact** keys:

### Required for Telemetry Health
```bash
SUPABASE_URL=https://npukynbaglmcdvzyklqa.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<your service role key>
SUPABASE_ANON_KEY=<your anon key>
```

### Required for LLM
```bash
ANTHROPIC_API_KEY=<your key>
OPENAI_API_KEY=<your key>
```

### Optional
```bash
TORQ_PROXY_SHARED_SECRET=<shared secret with Vercel>
TORQ_ADMIN_TOKEN=<for admin endpoints>
```

### Critical: Use Consistent Key Names

**Backend should use ONLY:**
- `SUPABASE_URL` (single source of truth)
- `SUPABASE_SERVICE_ROLE_KEY` (write access, backend)
- `SUPABASE_ANON_KEY` (optional, only if needed)

**Do NOT use:**
- `SUPABASE_KEY` (ambiguous, can conflict)
- Duplicate `SUPABASE_URL` entries (last wins, unpredictable)

---

## Step 3: Trigger Deployment

1. Click **Deploy New** or **Redeploy**
2. Wait for build to complete (5-10 minutes)
3. Railway will provide a deployment URL

---

## Step 4: Verify Deployment

### Run Verification Script

```bash
python verify_railway_deploy.py https://<your-railway-url>.up.railway.app
```

### Expected Output (All Pass)

All checks should show [PASS]:
- torq-deploy-v1 schema present
- Git SHA matches expected
- key_type_detected: service_role
- key_source: SUPABASE_SERVICE_ROLE_KEY
- access_test: healthy (HTTP 200)
- Supabase project ref: npukynbaglmcdvzyklqa

