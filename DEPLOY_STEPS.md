# Railway Deployment: control-plane-v1-clean

## Next Steps

### Step 1: Railway - Set Branch Watcher

1. Open project: https://railway.com/project/c6e58b87-d5f8-4819-86cb-1f34635616f3
2. **Select service**: `torq-console-backend` (or your backend service name)
3. **Select environment**: `production`
4. Settings -> Source -> Branch: `control-plane-v1-clean`
5. Root Directory: `/` (repo root)

### Step 2: Railway - Environment Variables (Minimum Set)

In **Variables** tab, set these:

**Required:**
```
SUPABASE_URL=https://npukynbaglmcdvzyklqa.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<your service role key>
```

**Optional:**
```
SUPABASE_ANON_KEY=<your anon key>
```
Only set if a feature explicitly uses anon-scoped reads. For backend writes, service_role is sufficient.

**For LLM (if needed):**
```
ANTHROPIC_API_KEY=<your key>
OPENAI_API_KEY=<your key>
```

### Step 3: Deploy + Verify (Direct)

1. Click **Redeploy** in Railway
2. Wait for deployment to complete (5-10 min)
3. Get your Railway URL from dashboard (e.g., `https://<service>-<id>.up.railway.app`)
4. Run verification:
```bash
python verify_railway_deploy.py https://<railway-url>.up.railway.app
```

### Step 4: Verify End-to-End (Via Proxy)

```bash
python verify_railway_deploy.py https://torq-console.vercel.app --via-proxy
```

### Step 5: Paste Both JSON Outputs

Share the `/api/telemetry/health` JSON from **both** URLs:
- Railway direct: `https://<railway-url>.up.railway.app/api/telemetry/health`
- Vercel proxy: `https://torq-console.vercel.app/api/telemetry/health`

This confirms `key_type_detected` and catches proxy drift in one shot.

---

## Expected Output

All checks should show `[PASS]`:
- Git SHA: `92070874...` (confirms new code)
- `key_type_detected`: `service_role`
- `key_source`: `SUPABASE_SERVICE_ROLE_KEY`
- `access_test`: `healthy` (HTTP 200)
- Supabase project ref: `npukynbaglmcdvzyklqa`
