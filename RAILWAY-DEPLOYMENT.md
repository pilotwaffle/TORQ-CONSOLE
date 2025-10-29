# TORQ Console - Railway Deployment Guide

## 🚀 Quick Deploy Steps

### 1. Prerequisites
- ✅ Railway CLI installed (`npx @railway/cli`)
- ✅ GitHub repository: `pilotwaffle/TORQ-CONSOLE`
- ✅ Railway account: https://railway.app

### 2. Connect GitHub Repository to Railway

**Option A: Via Railway Dashboard (Recommended)**
1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `pilotwaffle/TORQ-CONSOLE`
5. Railway will auto-detect Python and start building

**Option B: Via CLI**
```bash
cd E:\TORQ-CONSOLE
npx @railway/cli login
npx @railway/cli init
npx @railway/cli up
```

### 3. Configure Environment Variables

In Railway Dashboard → Your Project → Variables, add:

**Required:**
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
# OR
OPENAI_API_KEY=sk-...
```

**Optional:**
```bash
PORT=8899  # Railway auto-assigns, but can override
LOG_LEVEL=INFO
SOCKET_IO_ENABLED=true
CONTEXT_PARSING_ENABLED=true
```

### 4. Deployment Files Created

✅ **Procfile** - Tells Railway how to start the app
```
web: uvicorn torq_console.ui.web:app --host 0.0.0.0 --port $PORT
```

✅ **railway.toml** - Railway-specific configuration
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn torq_console.ui.web:app --host 0.0.0.0 --port $PORT"
```

✅ **runtime.txt** - Python version
```
python-3.11
```

✅ **.env.example** - Environment variable template

### 5. Verify Deployment

Once deployed, Railway will provide a URL like:
```
https://torq-console-production.up.railway.app
```

Test the deployment:
```bash
curl https://your-app.up.railway.app/health
```

### 6. View Logs

**Via Dashboard:**
- Railway Dashboard → Your Project → Deployments → View Logs

**Via CLI:**
```bash
cd E:\TORQ-CONSOLE
npx @railway/cli logs
```

### 7. Redeploy After Changes

**Automatic (GitHub Integration):**
- Push to GitHub main branch
- Railway auto-deploys

**Manual (CLI):**
```bash
cd E:\TORQ-CONSOLE
npx @railway/cli up
```

## 🔧 Troubleshooting

### Build Fails

**Check Python Dependencies:**
```bash
# Ensure pyproject.toml has all dependencies
pip install -e .
```

**View Build Logs:**
```bash
npx @railway/cli logs --build
```

### App Crashes on Startup

**Common Issues:**
1. Missing API keys → Check environment variables
2. Port binding → Railway auto-assigns `$PORT`, ensure app uses it
3. Missing dependencies → Check `pyproject.toml`

**Check Runtime Logs:**
```bash
npx @railway/cli logs --runtime
```

### WebSocket Issues

Railway supports WebSockets by default. Ensure:
```python
# In your FastAPI app
app = FastAPI()
app.mount("/socket.io", socket_app)  # Socket.IO works on Railway
```

### Environment Variables Not Loading

**Check Railway Dashboard:**
1. Project → Variables
2. Ensure variables are saved
3. Redeploy after adding variables

## 📊 Railway Features for TORQ Console

### ✅ Supported Features
- Python 3.11+ runtime
- FastAPI/Uvicorn server
- WebSocket (Socket.IO) support
- Persistent environment variables
- Auto-scaling
- Custom domains
- SSL certificates (automatic)
- Logs and monitoring

### ⚠️ Limitations
- No persistent file storage (use database or external storage)
- 500MB memory limit (free tier)
- Can't access local git repositories (push to GitHub)

## 🌐 Custom Domain Setup

1. Railway Dashboard → Project → Settings → Domains
2. Add custom domain (e.g., `torq.yourdomain.com`)
3. Update DNS with provided CNAME record
4. SSL automatically provisioned

## 💰 Pricing

**Free Tier:**
- $5 free credits per month
- 500MB RAM
- Shared CPU
- Perfect for development/testing

**Pro Tier ($20/month):**
- $20 credits included
- Up to 8GB RAM
- Dedicated resources
- Priority support

## 🔒 Security Best Practices

1. **Never commit API keys** - Use environment variables
2. **Enable CORS** - Restrict origins in production
3. **Use HTTPS** - Railway provides this automatically
4. **Rotate secrets** - Update SESSION_SECRET regularly

## 📚 Additional Resources

- Railway Docs: https://docs.railway.app
- TORQ Console Docs: See README.md
- Railway CLI Docs: https://docs.railway.app/develop/cli

## 🎉 Success Checklist

- [x] GitHub repository connected to Railway
- [x] Environment variables configured
- [x] Deployment successful (green checkmark in Railway)
- [x] App accessible via Railway URL
- [x] Logs showing no errors
- [x] WebSocket connections working
- [x] API keys configured and working

---

## ✅ DEPLOYMENT SUCCESSFUL!

**Status:** PRODUCTION READY 🚀

**Live URL:** https://web-production-1f870.up.railway.app/

**Deployment Details:**
- Project: intelligent-alignment
- Service: web
- Region: us-east4
- Python: 3.11
- Build Time: ~2.5 minutes
- Image Size: ~1GB (CPU-only PyTorch)
- Latest Commit: 1d178f9 (healthcheck enabled)

**Verified Endpoints:**
- `GET /` → 200 OK - {"name":"TORQ CONSOLE Web UI","version":"0.80.0","status":"running"}
- `GET /api/health` → 200 OK - {"status":"healthy","service":"torq-console-web-ui"}
- `GET /api/console/info` → 200 OK - Console information

**Environment Variables Set:**
- OPENAI_API_KEY ✅ Configured
- RAILWAY_PUBLIC_DOMAIN ✅ web-production-1f870.up.railway.app

**Issues Resolved:**
1. ✅ Missing dependencies (aiohttp, numpy, scikit-learn, sentence-transformers)
2. ✅ Pip hash verification errors (CUDA libraries)
3. ✅ Build timeout (optimized with CPU-only PyTorch)
4. ✅ Healthcheck failures (re-enabled and passing)
5. ✅ ASGI app loading error (standalone FastAPI app created)
6. ✅ API key configuration complete

TORQ Console is now live and accessible worldwide via Railway!
