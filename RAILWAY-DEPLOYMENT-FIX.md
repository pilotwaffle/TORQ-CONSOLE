# Railway Deployment Fix - TORQ-CONSOLE

## Problem Summary
Railway deployment was failing with hash verification errors for NVIDIA CUDA libraries:
```
ERROR: THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS FILE
nvidia_cublas_cu12: Expected sha256 8ac4e771... Got 780639d7b94...
```

## Root Cause
- Railway was using cached pip hashes from previous builds
- NVIDIA CUDA libraries are frequently updated with new checksums
- Pip's hash verification was enforcing old cached hashes
- 4GB+ of dependencies downloaded successfully but failed at verification step

## Solution Implemented

### Files Changed:
1. **`.nixpacks.toml`** (NEW) - Nixpacks build configuration
2. **`railway.toml`** - Updated with pip install flags
3. **`requirements.txt`** - Enhanced with explicit PyTorch/transformers
4. **`.railwayignore`** (NEW) - Optimized deployment size

### Changes Made:

#### 1. .nixpacks.toml
```toml
[phases.setup]
nixPkgs = ["python311", "pip"]

[phases.install]
cmds = [
    "pip install --upgrade pip",
    "pip install --no-cache-dir --no-deps -r requirements.txt"
]

[start]
cmd = "uvicorn torq_console.ui.web:app --host 0.0.0.0 --port $PORT"
```

**Key flags:**
- `--no-cache-dir` - Forces fresh download, ignores cached hashes
- `--no-deps` - Installs packages without dependency resolution conflicts

#### 2. railway.toml
```toml
[build]
builder = "NIXPACKS"

[build.nixpacksPlan]
providers = ["python"]

[build.nixpacksOptions]
pipInstallFlags = "--no-cache-dir --no-deps"

[deploy]
startCommand = "uvicorn torq_console.ui.web:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
healthcheckPath = "/"
healthcheckTimeout = 300
```

**Improvements:**
- Explicit pip install flags in nixpacksOptions
- 5-minute healthcheck timeout (ML libraries take time to load)
- Automatic restart on failure

#### 3. requirements.txt
Added explicit PyTorch and transformers dependencies:
```
torch>=2.0.0
transformers>=4.30.0
numpy>=1.24.0,<2.0.0
```

#### 4. .railwayignore
Excludes unnecessary files to optimize deployment:
- Test files
- Demo scripts
- Documentation (except README.md)
- Local development files
- Python cache

## Deployment Steps

### Option 1: Automatic Deployment (Recommended)
Railway will automatically detect the GitHub push and redeploy:

1. **Check deployment status in Railway dashboard:**
   - Project: "intelligent-alignment"
   - Service: "TORQ-CONSOLE"
   - Latest commit: bd775af (Railway deployment fix)

2. **Monitor build logs for:**
   - ✅ "Installing dependencies from requirements.txt"
   - ✅ "Successfully installed torch-2.x.x transformers-4.x.x"
   - ✅ "Starting uvicorn server"

### Option 2: Manual Railway CLI Commands

If Railway CLI is installed locally, run these commands:

```bash
# Navigate to project directory
cd E:\TORQ-CONSOLE

# Verify Railway authentication
railway whoami

# Check current project link
railway status

# Trigger manual deployment
railway up

# OR force a new deployment with cache clear
railway up --detach

# Monitor deployment logs
railway logs

# Check service status
railway status
```

### Option 3: Clear Build Cache via Railway Dashboard

If issues persist:

1. Go to Railway Dashboard: https://railway.app/project/32c42b8f-cbef-48dd-86ea-a9aebf3b0e66
2. Click on "TORQ-CONSOLE" service
3. Go to "Settings" tab
4. Scroll to "Danger Zone"
5. Click "Clear Build Cache"
6. Go to "Deployments" tab
7. Click "Redeploy" on the latest deployment

### Option 4: Create New Deployment via GitHub

Force a new deployment:

```bash
cd E:\TORQ-CONSOLE

# Create an empty commit to trigger deployment
git commit --allow-empty -m "chore: Trigger Railway redeployment"
git push origin main
```

## Expected Build Timeline

With 4GB+ of dependencies:
- **Download Phase:** 5-10 minutes (PyTorch, CUDA libraries, transformers)
- **Installation Phase:** 3-5 minutes (compilation and setup)
- **Startup Phase:** 1-2 minutes (ML model loading)
- **Total:** ~15-20 minutes

## Verification Steps

### 1. Check Deployment Status
```bash
railway status
```

Expected output:
```
Service: TORQ-CONSOLE
Status: DEPLOYED
URL: https://torq-console-production.up.railway.app
```

### 2. Test API Endpoint
```bash
curl https://your-deployment-url.railway.app/
```

Expected: FastAPI JSON response or HTML page

### 3. Check Health Endpoint
```bash
curl https://your-deployment-url.railway.app/health
```

Expected: `{"status": "ok"}`

### 4. View Logs
```bash
railway logs --tail 100
```

Look for:
- ✅ "Application startup complete"
- ✅ "Uvicorn running on 0.0.0.0:$PORT"
- ❌ No "ERROR: THESE PACKAGES DO NOT MATCH" messages

## Post-Deployment: Add Environment Variables

After successful deployment, add API keys:

### Via Railway Dashboard:
1. Go to Service Settings
2. Click "Variables" tab
3. Add environment variables:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-...
   BRAVE_API_KEY=...
   ```

### Via Railway CLI:
```bash
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set OPENAI_API_KEY=sk-...
railway variables set BRAVE_API_KEY=...
```

## Troubleshooting

### If deployment still fails:

#### 1. Check Nixpacks version
Railway might need to update to latest Nixpacks:
```bash
railway run nixpacks --version
```

#### 2. Try CPU-only PyTorch
If CUDA libraries continue to fail, edit `requirements.txt`:
```
# Replace:
torch>=2.0.0

# With CPU-only version:
torch>=2.0.0+cpu -f https://download.pytorch.org/whl/torch_stable.html
```

#### 3. Pin exact versions
If hash errors persist, pin exact working versions:
```
torch==2.1.2
transformers==4.36.2
sentence-transformers==2.2.2
```

#### 4. Split dependency installation
Modify `.nixpacks.toml` to install in stages:
```toml
[phases.install]
cmds = [
    "pip install --upgrade pip",
    "pip install --no-cache-dir torch>=2.0.0",
    "pip install --no-cache-dir transformers>=4.30.0",
    "pip install --no-cache-dir -r requirements.txt"
]
```

#### 5. Check Railway service logs
```bash
railway logs --tail 500
```

Look for specific error messages and stack traces.

## Success Indicators

Deployment is successful when you see:

```
✅ Build completed successfully
✅ Dependencies installed: 45 packages
✅ Starting application...
✅ INFO: Application startup complete
✅ INFO: Uvicorn running on http://0.0.0.0:8080
✅ Deployment live at: https://torq-console-production.up.railway.app
```

## Git Commit Reference

- **Commit:** bd775af
- **Message:** "fix: Railway deployment hash verification issue"
- **Files Changed:**
  - `.nixpacks.toml` (new)
  - `.railwayignore` (new)
  - `railway.toml` (modified)
  - `requirements.txt` (modified)

## Support Resources

- Railway Documentation: https://docs.railway.app
- Nixpacks Documentation: https://nixpacks.com
- Railway Discord: https://discord.gg/railway
- GitHub Issues: https://github.com/pilotwaffle/TORQ-CONSOLE/issues

## Next Steps

1. ✅ Changes committed and pushed (bd775af)
2. ⏳ Wait for Railway auto-deployment (15-20 minutes)
3. ⏳ Verify deployment success
4. ⏳ Add API key environment variables
5. ⏳ Test API endpoints
6. ⏳ Monitor application logs

---

**Last Updated:** 2025-10-29
**Commit:** bd775af
**Status:** Deployed to GitHub, awaiting Railway build
