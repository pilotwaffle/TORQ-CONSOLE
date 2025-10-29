# TORQ-CONSOLE - Complete Railway Deployment Guide

## ✅ What's Already Done

- ✅ Railway CLI installed and authenticated (Barry Flowers)
- ✅ Deployment files created and pushed to GitHub (commit a146af9)
- ✅ GitHub Actions CI workflow added (commit e837762)
- ✅ Missing dependencies fixed: aiohttp (commit 7059b66)
- ✅ ML dependencies added: numpy, scikit-learn, sentence-transformers (commit f369541)
- ✅ Repository: https://github.com/pilotwaffle/TORQ-CONSOLE
- ✅ GitHub connected to Railway - Auto-deployment enabled

## 🚀 Deploy Now - 3 Simple Steps

### Step 1: Create Railway Project from GitHub (2 minutes)

1. **Open Railway Dashboard**: https://railway.app/new
2. **Click**: "Deploy from GitHub repo"
3. **Select**: `pilotwaffle/TORQ-CONSOLE`
4. **Click**: "Deploy Now"

Railway will automatically:
- Detect Python project from `pyproject.toml`
- Use `railway.toml` configuration
- Install dependencies
- Start the server with `Procfile`

### Step 2: Add Environment Variables (1 minute)

Once the project is created:

1. Go to your project in Railway dashboard
2. Click **"Variables"** tab
3. Add these variables:

**Required (choose one):**
```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```
or
```
OPENAI_API_KEY=sk-YOUR-KEY-HERE
```

**Optional (recommended):**
```
LOG_LEVEL=INFO
SOCKET_IO_ENABLED=true
CONTEXT_PARSING_ENABLED=true
REAL_TIME_COLLABORATION=true
VOICE_ENABLED=false
```

4. Click **"Save"** - Railway will redeploy automatically

### Step 3: Get Your URL (30 seconds)

1. Go to **"Settings"** tab
2. Find **"Public Networking"** section
3. Click **"Generate Domain"**
4. Your TORQ-CONSOLE will be live at: `https://torq-console-production.up.railway.app`

---

## 🎯 Quick Verification

Test your deployment:

```bash
# Check health endpoint
curl https://your-app.up.railway.app/health

# Open in browser
start https://your-app.up.railway.app
```

---

## 📊 Deployment Configuration Reference

### Files Already Configured

**Procfile**
```
web: uvicorn torq_console.ui.web:app --host 0.0.0.0 --port $PORT
```

**railway.toml**
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn torq_console.ui.web:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[build.nixpacksPlan]
providers = ["python"]
```

**runtime.txt**
```
python-3.11
```

---

## 🔧 Troubleshooting

### Build Fails

**Check Build Logs:**
- Railway Dashboard → Your Project → Deployments → View Build Logs

**Common Issues:**
1. Python dependencies missing → Check `pyproject.toml`
2. Build timeout → Contact Railway support for larger resource allocation

### App Crashes on Start

**Check Runtime Logs:**
- Railway Dashboard → Your Project → Deployments → View Runtime Logs

**Common Issues:**
1. Missing API key → Add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
2. Port binding error → Should use `$PORT` (already configured)
3. Import errors → Ensure all dependencies in `pyproject.toml`

### Can't Access URL

**Check:**
1. Deployment status is "Active" (green checkmark)
2. Domain is generated in Settings → Public Networking
3. No errors in runtime logs

---

## 💡 Alternative: Use Existing Railway Project

If you want to deploy to one of your existing projects:

1. Go to Railway Dashboard
2. Select existing project (e.g., "illustrious-courtesy")
3. Click **"New Service"**
4. Select **"GitHub Repo"**
5. Choose `pilotwaffle/TORQ-CONSOLE`
6. Configure environment variables
7. Railway will deploy

---

## 🔗 Useful Railway Commands

```bash
# View all projects
npx @railway/cli list

# View logs (after linking)
npx @railway/cli logs

# Deploy directly from CLI
npx @railway/cli up

# Check deployment status
npx @railway/cli status

# Open dashboard
npx @railway/cli open
```

---

## 📈 Railway Resource Limits

**Free Tier:**
- $5 in free credits per month
- 500MB RAM per service
- 1GB storage
- Good for development/testing

**Hobby Tier ($5/month):**
- $5 in credits included (additional usage billed)
- Up to 8GB RAM
- Better for production workloads

**Note:** If you see "Resource limit reached", you may need to:
1. Delete unused projects
2. Upgrade to Hobby tier
3. Use an existing project's service

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Build completed successfully (green checkmark)
- [ ] Application is running (Deployments tab shows "Active")
- [ ] Public URL is accessible
- [ ] Environment variables are set
- [ ] Health endpoint responds: `/health`
- [ ] Main interface loads at root URL `/`
- [ ] WebSocket connections work (if enabled)
- [ ] No errors in runtime logs

---

## 🎉 You're Done!

Once deployed, TORQ-CONSOLE will be:
- ✅ Live at your Railway URL
- ✅ Auto-deploying from GitHub main branch
- ✅ Monitored with Railway's built-in logging
- ✅ Backed by Railway's infrastructure
- ✅ SSL-enabled by default

Share your deployment URL and start using TORQ-CONSOLE!

---

**Deployment Date:** 2025-10-29
**Latest Commit:** f369541 "Fix: Add numpy, scikit-learn, sentence-transformers dependencies"
**Repository:** https://github.com/pilotwaffle/TORQ-CONSOLE
**Configured By:** Claude Code + Railway CLI
**Current Status:** All dependencies fixed - Ready for Railway auto-deploy
