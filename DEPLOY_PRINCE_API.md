# Deploy Enhanced Prince API - Public Endpoint for Maxim.ai

Since Maxim.ai doesn't support local APIs, you need to deploy Enhanced Prince API to a publicly accessible URL. This guide shows you how to deploy to **free hosting platforms**.

---

## 🚀 Option 1: Railway.app (Recommended - Easiest)

Railway offers 500 hours/month free tier and is the easiest deployment.

### Steps:

1. **Go to Railway**: https://railway.app
2. **Sign up** with GitHub
3. **Create New Project** → **Deploy from GitHub repo**
4. **Select this repository**: `pilotwaffle/TORQ-CONSOLE`
5. **Select branch**: `claude/create-agent-json-011CUtyHaWVGi61W7QuCa7pw`
6. **Add Environment Variables**:
   - Click "Variables" tab
   - Add: `ANTHROPIC_API_KEY` = `your-api-key-here`
7. **Wait for deployment** (~2-3 minutes)
8. **Get your URL**: Railway will generate a URL like `https://enhanced-prince-api-production.up.railway.app`

### Configure Start Command (if needed):

If Railway doesn't auto-detect the start command:
- Go to Settings → Start Command
- Set: `uvicorn enhanced_prince_api:app --host 0.0.0.0 --port $PORT`

### Your Endpoint URL:

```
https://your-app-name.up.railway.app/chat
```

---

## 🚀 Option 2: Render.com (Free Tier)

Render offers free tier for web services (sleeps after 15 min of inactivity).

### Steps:

1. **Go to Render**: https://render.com
2. **Sign up** with GitHub
3. **New** → **Web Service**
4. **Connect repository**: `pilotwaffle/TORQ-CONSOLE`
5. **Configure**:
   - **Name**: `enhanced-prince-api`
   - **Branch**: `claude/create-agent-json-011CUtyHaWVGi61W7QuCa7pw`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn enhanced_prince_api:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
6. **Add Environment Variable**:
   - Key: `ANTHROPIC_API_KEY`
   - Value: `your-api-key-here`
7. **Create Web Service**
8. **Wait for deployment** (~5 minutes for free tier)

### Your Endpoint URL:

```
https://enhanced-prince-api.onrender.com/chat
```

**Note**: Free tier sleeps after 15 minutes of inactivity. First request after sleep takes ~30 seconds to wake up.

---

## 🚀 Option 3: Fly.io (Free Allowances)

Fly.io offers free allowances: 3 shared-cpu-1x 256mb VMs.

### Steps:

1. **Install flyctl**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Sign up and login**:
   ```bash
   fly auth signup
   # or
   fly auth login
   ```

3. **Deploy from project directory**:
   ```bash
   cd /home/user/TORQ-CONSOLE

   # Initialize (creates fly.toml)
   fly launch --name enhanced-prince-api --region sjc --no-deploy

   # Set environment variable
   fly secrets set ANTHROPIC_API_KEY="your-api-key-here"

   # Deploy
   fly deploy
   ```

4. **Get your URL**: `https://enhanced-prince-api.fly.dev`

### Your Endpoint URL:

```
https://enhanced-prince-api.fly.dev/chat
```

---

## 🚀 Option 4: Vercel (Serverless)

Vercel can run FastAPI via serverless functions.

### Steps:

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Create `vercel.json`** (already in repo):
   ```json
   {
     "builds": [
       {
         "src": "enhanced_prince_api.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "enhanced_prince_api.py"
       }
     ]
   }
   ```

3. **Deploy**:
   ```bash
   cd /home/user/TORQ-CONSOLE
   vercel
   ```

4. **Set environment variable**:
   ```bash
   vercel env add ANTHROPIC_API_KEY
   # Enter your API key when prompted
   ```

5. **Deploy to production**:
   ```bash
   vercel --prod
   ```

### Your Endpoint URL:

```
https://your-project.vercel.app/chat
```

---

## 📋 After Deployment: Configure Maxim.ai

Once you have your public URL, configure it in Maxim.ai:

### Step 1: Test Your Endpoint

```bash
# Replace with your actual deployed URL
curl -X POST https://your-app-name.up.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Search the latest AI news 11/08/25"}'
```

**Expected Response:**
```json
{
  "response": "Based on my search, here are the latest AI news...",
  "action_taken": "IMMEDIATE_ACTION",
  "interaction_id": "interaction_1"
}
```

### Step 2: Configure in Maxim.ai

1. **Go to your workspace**: https://app.getmaxim.ai/workspace/cmhqimzv9007c11ofecpe69n1/home

2. **Create or Edit Workflow**:
   - Click on your workflow
   - Configure the AI endpoint

3. **Set Endpoint Configuration**:
   ```
   URL: https://your-deployed-url.com/chat
   Method: POST
   Headers:
     Content-Type: application/json

   Request Body:
   {
     "query": "{{input.query}}"
   }

   Response Path:
   response: $.response
   action: $.action_taken
   ```

### Step 3: Run Test Suite

Now you can use the test scripts against your public endpoint:

```bash
# Update test_prince_maxim_endpoint.py with your URL
ENDPOINT_URL="https://your-app-name.up.railway.app"

python test_prince_maxim_endpoint.py
```

Or import the YAML test suite in Maxim.ai and configure it to use your endpoint.

---

## 🔍 Verify Deployment

### Health Check

```bash
curl https://your-deployed-url.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "enhanced_prince_available": true,
  "agent_memory_available": true,
  "api_key_configured": true
}
```

### Critical Test

```bash
curl -X POST https://your-deployed-url.com/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Research new updates coming to GLM-4.6"}'
```

**✅ PASS if response contains:**
- `"action_taken": "IMMEDIATE_ACTION"`
- Search results (not code generation)

**❌ FAIL if response contains:**
- `"action_taken": "IMMEDIATE_ACTION (ERROR: generated code)"`
- TypeScript/JavaScript code

---

## 💰 Cost Comparison

| Platform | Free Tier | Limits | Best For |
|----------|-----------|--------|----------|
| **Railway** | 500 hrs/month | No sleep | ⭐ Best overall |
| **Render** | Unlimited | Sleeps after 15min | Light testing |
| **Fly.io** | 3 VMs free | 256MB RAM | Always-on |
| **Vercel** | Unlimited | 10s execution limit | Simple requests |

**Recommendation**: Use **Railway** for testing Enhanced Prince with Maxim.ai.

---

## 🐛 Troubleshooting

### Error: "enhanced_prince_available": false

**Cause**: Enhanced Prince failed to initialize

**Fix**:
1. Check server logs for errors
2. Verify `ANTHROPIC_API_KEY` is set correctly
3. Check that all dependencies installed

### Error: "api_key_configured": false

**Cause**: API key not set

**Fix**:
```bash
# Railway
railway variables --set ANTHROPIC_API_KEY="your-key"

# Render
# Go to Dashboard → Environment → Add Variable

# Fly.io
fly secrets set ANTHROPIC_API_KEY="your-key"
```

### Error: 503 Service Unavailable

**Cause**: App is sleeping (Render free tier)

**Fix**: Wait 30 seconds for app to wake up, or upgrade to paid tier

### Error: Timeout

**Cause**: LLM API call taking too long

**Fix**: Increase timeout in Maxim.ai workflow configuration (recommend 60s)

---

## 📝 Example: Full Railway Deployment

```bash
# 1. Go to Railway.app and sign in with GitHub
# 2. Click "New Project" → "Deploy from GitHub repo"
# 3. Select "pilotwaffle/TORQ-CONSOLE"
# 4. Select branch "claude/create-agent-json-011CUtyHaWVGi61W7QuCa7pw"
# 5. Click "Add variables" → Add ANTHROPIC_API_KEY
# 6. Wait for deployment
# 7. Click "Settings" → "Generate Domain"
# 8. Your endpoint: https://your-app.up.railway.app/chat

# Test it:
curl https://your-app.up.railway.app/health

# Use in Maxim.ai:
# Endpoint URL: https://your-app.up.railway.app/chat
# Method: POST
# Body: {"query": "Search the latest AI news"}
```

---

## ✅ Ready for Maxim.ai Testing

Once deployed:

1. ✅ Your Enhanced Prince API is publicly accessible
2. ✅ Maxim.ai can call your endpoint via HTTPS
3. ✅ You can run comprehensive test suites
4. ✅ You can track all interactions and learn from feedback

**Next**: Deploy using one of the options above, then configure the endpoint URL in your Maxim.ai workflow!

---

## 📄 Files for Deployment

- ✅ `enhanced_prince_api.py` - The API server
- ✅ `requirements.txt` - Already includes all dependencies
- ✅ `railway.json` - Railway configuration
- ✅ `render.yaml` - Render configuration
- ✅ `Procfile` - For Heroku-style platforms
- ✅ `test_prince_maxim_endpoint.py` - Test script to update with your URL

---

**Quick Deploy**: Click one of these buttons (once repo is public):

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

Or follow the manual steps above! 🚀
