# TORQ Console — Branch Alignment + Redeploy Runbook

## Status: Step 0 Complete ✓
- GitHub `control-plane-v1` SHA: `2a15fce0` ✓

---

## 1) Vercel — Switch Production Branch

### Manual Steps (Vercel Dashboard)

1. Open: https://vercel.com/pilotwaffles-projects/torq-console
2. Go to **Settings** → **Git**
3. Find **Production Branch**
4. Change `main` → `control-plane-v1`
5. Click **Save**
6. Go to **Deployments** → Click latest → **Redeploy**

### Verify After Redeploy
```bash
curl -s https://torq-console.vercel.app/api/debug/deploy | jq
```

Expected: Should show `git_ref: "control-plane-v1"` (not "main")

---

## 2) Railway — Switch Tracked Branch

### Manual Steps (Railway Dashboard)

1. Open: https://railway.com/project/c6e58b87-d5f8-4819-86cb-1f34635616f3
2. Click the service (torq-console-backend)
3. Go to **Settings** tab
4. Under **GitHub Repo**:
   - Confirm repo: `pilotwaffle/TORQ-CONSOLE`
   - Change branch: `api-railway-proxy` → `control-plane-v1`
5. Click **Save**
6. Go to **Deployments** → Click **Redeploy**

### Verify After Redeploy
```bash
curl -s https://web-production-74ed0.up.railway.app/api/debug/deploy | jq
```

Expected: `git_sha` starts with `2a15fce0`

---

## 3) Vercel Proxy — Confirm Rewrites

### Root vercel.json Analysis

Your current `E:\TORQ-CONSOLE\vercel.json`:
```json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "/api/index.py" }
  ]
}
```

**This is CORRECT**. The rewrite sends ALL `/api/*` requests to `/api/index.py`, which then proxies to Railway.

### The Issue
The `api/index.py` file **already had the proxy logic**, but was missing specific endpoints for `/api/telemetry/*` and `/api/learning/*`. I just added them.

### Why 404 Before
The old `api/index.py` only handled `/api/chat`. When Vercel proxied `/api/learning/status` to `/api/index.py`, that route didn't exist → 404.

### Why It Should Work Now
After Vercel redeploys with the updated `api/index.py`, the flow will be:
1. Request: `https://torq-console.vercel.app/api/learning/status`
2. Vercel rewrite: → `/api/index.py` (Vercel serverless)
3. `/api/index.py`: → `learning_status()` → `_proxy_to_railway("/api/learning/status")`
4. Railway backend handles the actual request

---

## 4) Final Validation Checklist

Run these after BOTH platforms have redeployed:

```bash
# 1. Vercel health
curl -s https://torq-console.vercel.app/health | jq

# 2. Railway health
curl -s https://web-production-74ed0.up.railway.app/health | jq

# 3. Railway deploy identity (CRITICAL - must show 2a15fce0)
curl -s https://web-production-74ed0.up.railway.app/api/debug/deploy | jq

# 4. Vercel proxy - learning
curl -s https://torq-console.vercel.app/api/learning/status | jq

# 5. Vercel proxy - telemetry
curl -s https://torq-console.vercel.app/api/telemetry/health | jq
```

### Success Condition
- Railway: `"git_sha": "2a15fce0..."`
- Vercel `/api/learning/status`: Returns JSON (not 404)
- Vercel `/api/telemetry/health`: Returns JSON (not 404)

---

## 5) Cleanup (After Success)

```bash
# Delete old branch locally
git branch -D api-railway-proxy

# Delete old branch remotely
git push origin --delete api-railway-proxy

# Then delete in GitHub UI if it still appears
```

---

## Deployment Guard Policy (Future)

### Railway Deploy Guard
```python
# In railway_app.py startup:
if os.getenv("RAILWAY_GIT_COMMIT_SHA", "")[:8] != get_expected_sha():
    logger.error("Deploy SHA mismatch - refusing to start")
    sys.exit(1)
```

### Vercel Deploy Guard
```json
// vercel.json build hook
{
  "github": {
    "silent": true
  },
  "install": "node ./verify-deploy-identity.js"
}
```

### CI Rewrite Guard
```yaml
# .github/workflows/deploy-guard.yml
name: "Deploy Guard"
on: [push]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - name: Check rewrites
        run: |
          curl https://torq-console.vercel.app/api/learning/status
          curl https://torq-console.vercel.app/api/telemetry/health
```

---

## Quick Reference Commands

### Check Deploy Identity
```bash
# Railway
curl -s https://web-production-74ed0.up.railway.app/api/debug/deploy | jq

# Vercel
curl -s https://torq-console.vercel.app/api/debug/deploy | jq
```

### Trigger Manual Redeploy
```bash
# Empty commit method (cleanest)
git commit --allow-empty -m "chore: trigger deploy"
git push origin control-plane-v1
```

### Check Local vs Deployed SHA
```bash
# Local SHA
git rev-parse --short HEAD

# Deployed SHA (Railway)
curl -s https://web-production-74ed0.up.railway.app/api/debug/deploy | jq -r '.git_sha'

# Deployed SHA (Vercel)
curl -s https://torq-console.vercel.app/api/debug/deploy | jq -r '.git_sha'
```

---

## Current State Summary

| Component | Branch | SHA | Status |
|-----------|--------|-----|--------|
| GitHub | `control-plane-v1` | `2a15fce0` | ✅ Correct |
| Local | `control-plane-v1` | `2a15fce0` | ✅ Correct |
| Railway | `api-railway-proxy` | `346ede4b` (OLD) | ⚠️ Needs branch switch |
| Vercel | `main` | `99072c65` (OLD) | ⚠️ Needs branch switch |

---

## What I Fixed in api/index.py

Added these proxy endpoints:
- `GET /api/telemetry/health` → proxies to Railway
- `POST /api/telemetry` → proxies to Railway
- `GET /api/learning/status` → proxies to Railway
- `GET /api/traces` → proxies to Railway
- `GET /api/traces/{id}` → proxies to Railway
- `GET /api/traces/{id}/spans` → proxies to Railway

All use the existing `_proxy_to_railway()` function with proper auth headers.
