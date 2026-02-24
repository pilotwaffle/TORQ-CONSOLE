# Railway Redeploy Triggers

## Current Status
- **Vercel**: ✅ Watching `control-plane-v1` - Auto-deploys on push
- **Railway**: ⚠️ Still configured to watch `main` or needs manual trigger

## Solutions

### Option A: Configure Railway to watch `control-plane-v1` (Recommended)
1. Go to https://railway.com/project/c6e58b87-d5f8-4819-86cb-1f34635616f3
2. Select the `torq-console-backend` service
3. Go to Settings → GitHub
4. Change branch from `main` to `control-plane-v1`
5. Save → Railway will auto-redeploy on future pushes

### Option B: Manual Redeploy via Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Trigger redeploy
railway up --service torq-console-backend
```

### Option C: Manual Redeploy via Dashboard
1. Open https://railway.com/project/c6e58b87-d5f8-4819-86cb-1f34635616f3
2. Select the service
3. Click "Redeploy" button

### Option D: Trigger via Empty Commit (if Railway watching branch)
```bash
git commit --allow-empty -m "chore: trigger railway redeploy"
git push origin control-plane-v1
```

## Smoke Test with SHA Validation
Once Railway updates, run:
```bash
EXPECTED_SHA=$(git rev-parse --short HEAD) python scripts/smoke_control_plane.py
```

This will fail-fast if SHA mismatch detected.
