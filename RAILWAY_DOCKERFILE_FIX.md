# Railway Dockerfile Fix Summary

**Date:** 2026-03-05
**Status:** 🔄 FIX PUSHED - Waiting for Railway Deployment

---

## Problem

Railway deployment was failing with:
```
Error: Invalid value for '--port': '$PORT' is not a valid integer.
```

**Root Causes:**
1. Dockerfile was using broken entry point: `torq_console.ui.start_railway`
2. `$PORT` environment variable wasn't being expanded (shell vs direct CMD)
3. Dockerfile had `$PYTHONPATH` with undefined variable during build

## Changes Made

### 1. Fixed Dockerfile (`E:\TORQ-CONSOLE\Dockerfile`)

**Before:**
```dockerfile
# Line 42 - Undefined variable during build
ENV PYTHONPATH=/app:$PYTHONPATH

# Line 70 - Wrong entry point
CMD ["python", "-m", "torq_console.ui.start_railway"]
```

**After:**
```dockerfile
# Line 42 - Fixed with default value
ENV PYTHONPATH=/app

# Line 70-71 - Use railway_app.py with shell expansion for PORT
CMD ["sh", "-c", "uvicorn railway_app:app --host 0.0.0.0 --port ${PORT} --log-level warning"]
```

### 2. Commit Details
```
83f81f98 fix: use railway_app.py in Dockerfile with proper PORT env var expansion
86820d54 chore: update build metadata [skip ci]
```

---

## Current Status

### Railway Deployment
| Service | Status |
|---------|--------|
| **Current SHA** | `5b9a06ae` (OLD - still deploying) |
| **Expected SHA** | `83f81f98` (NEW - fix pushed) |
| **Health Endpoint** | https://web-production-74ed0.up.railway.app/health |

### Vercel Deployment
| Service | Status |
|---------|--------|
| **Frontend** | ✅ Working (HTTP 200) |
| **URL** | https://torq-console.vercel.app |

---

## Next Steps

1. **Monitor Railway Dashboard** - Watch for new build with SHA `83f81f98`
2. **Verify health endpoint** returns new git_sha after deployment
3. **Test Knowledge Plane endpoints**:
   - `/api/knowledge/health`
   - `/api/knowledge/store`
   - `/api/knowledge/search`

---

## Configuration Files Summary

| File | Builder | Start Command |
|------|---------|---------------|
| `railway.json` | NIXPACKS | `uvicorn railway_app:app...` |
| `.nixpacks.toml` | Nixpacks | `uvicorn railway_app:app...` |
| `Dockerfile` | Docker | `uvicorn railway_app:app...` (NEW) |
| `railway.toml` | Docker (auto) | Uses Dockerfile |

All config files now point to the working `railway_app.py` standalone application.

---

**Railway should auto-deploy commit `83f81f98` shortly.**
