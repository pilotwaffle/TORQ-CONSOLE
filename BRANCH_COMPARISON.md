# TORQ Console Branch Comparison
**Which branch should each service use?**

---

## Executive Summary

| Service | Current Branch | Should Use | Reason |
|---------|---------------|------------|--------|
| **Railway Backend** | `main` | **`control-plane-v1-clean`** | Has working Knowledge Plane + multi-agent endpoints |
| **Vercel Frontend** | `main` | **`main`** | Has full WebUI and streaming features |
| **Supabase** | N/A | **Either** | Database schema is the same |

**IMPORTANT:** Railway is now using `railway_app:app` (standalone) instead of `torq_console.ui.railway_app:app` (broken).

---

## Branch Analysis

### `main` Branch
**Latest commit:** `99072c65` - feat(vercel): add deploy fingerprint and explicit fallback telemetry

**Purpose:** Production-ready with full WebUI and streaming

**Key Features:**
- ✅ Full WebUI with static file serving
- ✅ SSE streaming endpoints
- ✅ Railway proxy with fallback
- ✅ Proper `railway.json` with `pip install -e .`
- ✅ Socket.io disabled on Vercel
- ✅ Real-time streaming updates
- ✅ Latest telemetry and deploy fingerprint features

**railway.json:**
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -e ."
  },
  "deploy": {
    "startCommand": "python -m uvicorn torq_console.ui.railway_app:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "numReplicas": 1
  }
}
```

### `control-plane-v1-clean` Branch
**Latest commit:** `045d15be` - chore: update build metadata [skip ci]

**Purpose:** Development/testing branch with experimental features

**Key Features:**
- ✅ Multi-agent orchestration endpoints (added in this branch)
- ✅ Cognitive loop endpoints
- ✅ Knowledge plane integration
- ✅ Supabase migration SQL
- ✅ Infrastructure documentation
- ⚠️ Missing `buildCommand` in railway.json
- ⚠️ Different `railway_app.py` (API-only, no WebUI)

**railway.json:**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn torq_console.ui.railway_app:app --host 0.0.0.0 --port $PORT --log-level warning",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 90,
    "restartPolicyType": "ON_FAILURE",
    "numReplicas": 1
  }
}
```

---

## Key Differences

### 1. Railway Backend

| Aspect | `main` | `control-plane-v1-clean` |
|--------|--------|------------------------|
| **railway_app.py** | Full WebUI + API | API only (no WebUI) |
| **buildCommand** | `pip install -e .` | Missing (causes issues) |
| **Multi-agent endpoints** | ❌ No | ✅ Yes |
| **Cognitive loop** | ❌ No | ✅ Yes |
| **Knowledge search** | ❌ No | ✅ Yes |

**Recommendation:** Use **`main`** for Railway
- The control-plane-v1-clean branch has multi-agent features BUT:
  - Missing `buildCommand` causes deployment failures
  - The branch is meant for development, not production
  - Multi-agent features should be merged to main first

### 2. Vercel Frontend

| Aspect | `main` | `control-plane-v1-clean` |
|--------|--------|------------------------|
| **WebUI** | ✅ Full | ❌ API-only backend |
| **SSE Streaming** | ✅ Yes | ❌ No |
| **Railway Proxy** | ✅ Yes | ❌ No |

**Recommendation:** Use **`main`** for Vercel
- control-plane-v1-clean is backend-only
- main has the complete frontend

### 3. Supabase

| Aspect | `main` | `control-plane-v1-clean` |
|--------|--------|------------------------|
| **Schema** | Same | Same |
| **Tables** | Existing + `thoughts` | Migration SQL for 12 tables |

**Recommendation:** Merge the Supabase migration from control-plane-v1-clean to main, then use main

---

## Why Railway Isn't Deploying

The Railway service is configured to watch `main` (or is connected via GitHub integration to main).

**Problem:** The multi-agent endpoints are in `control-plane-v1-clean`, but Railway is watching `main`.

**Solution:** Either:

### Option A: Merge control-plane-v1-clean to main (Recommended)
```bash
git checkout main
git merge control-plane-v1-clean
git push origin main
```
This brings all new features to the production branch.

### Option B: Configure Railway to watch control-plane-v1-clean
In Railway dashboard:
1. Service → Settings → General
2. Change "Root Directory" or branch configuration
3. But this is NOT recommended because:
   - control-plane-v1-clean has missing `buildCommand`
   - It's a development branch, not production-ready

---

## Action Plan

### Immediate (Recommended)

1. **Merge multi-agent features to main:**
   ```bash
   git checkout main
   git merge control-plane-v1-clean
   # Resolve conflicts if any
   git push origin main
   ```

2. **Verify railway.json in main is correct:**
   - Has `buildCommand: "pip install -e ."`
   - Has correct `startCommand`

3. **Railway will auto-deploy from main** once merged

### Alternative (If you want to keep them separate)

1. **Fix control-plane-v1-clean:**
   - Add `"buildCommand": "pip install -e ."` to railway.json
   - Ensure the merged code works correctly

2. **Configure Railway to watch control-plane-v1-clean**
   - Service → Settings → General
   - Disconnect GitHub repo
   - Reconnect and select control-plane-v1-clean branch

---

## Conclusion

| Service | Use Branch |
|---------|-----------|
| **Railway** | `main` (after merging multi-agent features) |
| **Vercel** | `main` |
| **Supabase** | Either (schema is same) |

**The control-plane-v1-clean branch contains new features (multi-agent, cognitive loop, knowledge plane) that should be merged into main for production deployment.**
