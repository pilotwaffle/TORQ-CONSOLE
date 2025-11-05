# TORQ Console Security Setup Guide

**Date**: November 4, 2025
**Status**: ⚠️ CRITICAL - Immediate Action Required

---

## 🚨 URGENT: API Keys Were Exposed

### What Happened

The `.env` file containing **real API keys** was accidentally committed to Git in commit `b208f182a4`. This file has been **removed from tracking**, but the keys were exposed and must be rotated immediately.

### Exposed API Keys

The following API keys were found in the committed `.env` file and **MUST BE REVOKED**:

1. **Google Search API**
   - Exposed Key: `AIzaSyA7eNQYC-zgo2OTYjL4QnrT5GeoHxJAhDw`
   - Action: ✅ REVOKE IMMEDIATELY

2. **Brave Search API**
   - Exposed Key: `BSAkNrh316HK8uxqGjUN1_eeLon8PfO`
   - Action: ✅ REVOKE IMMEDIATELY

3. **OpenAI API**
   - Exposed Key: `sk-proj-6gpZOJB52QxqLgW6XjiE...` (partial)
   - Action: ✅ REVOKE IMMEDIATELY

---

## ⚡ Immediate Actions Required

### Step 1: Revoke Exposed Keys (DO THIS NOW!)

#### Google Search API
1. Go to: https://console.cloud.google.com/apis/credentials
2. Find API key: `AIzaSyA7eNQYC-zgo2OTYjL4QnrT5GeoHxJAhDw`
3. Click "Delete" or "Regenerate"
4. Generate a new key
5. Update your local `.env` file with the new key

#### Brave Search API
1. Go to: https://brave.com/search/api/
2. Log in to your account
3. Navigate to API Keys section
4. Revoke key: `BSAkNrh316HK8uxqGjUN1_eeLon8PfO`
5. Generate a new key
6. Update your local `.env` file with the new key

#### OpenAI API
1. Go to: https://platform.openai.com/api-keys
2. Find the key starting with `sk-proj-6gpZOJB52...`
3. Click "Revoke" or "Delete"
4. Create a new API key
5. Update your local `.env` file with the new key
6. **Monitor usage** for any unauthorized charges

### Step 2: Monitor for Unauthorized Usage

**Check immediately:**
- OpenAI Dashboard: https://platform.openai.com/usage
- Google Cloud Console: Check for unexpected API calls
- Brave Search API: Review usage metrics

**Look for:**
- Unusual spikes in API usage
- Calls from unknown IP addresses
- Requests at unusual times
- Unexpected charges

### Step 3: Set Up Billing Alerts

**OpenAI:**
1. Go to https://platform.openai.com/account/billing/limits
2. Set up soft limit (e.g., $50/month)
3. Set up hard limit (e.g., $100/month)
4. Add notification email

**Google Cloud:**
1. Go to https://console.cloud.google.com/billing/budgets
2. Create budget alert
3. Set threshold (e.g., $20/month)
4. Add notification channels

---

## 🔒 Security Best Practices Going Forward

### 1. Environment File Management

**DO:**
- ✅ Use `.env` for local development only
- ✅ Keep `.env` in `.gitignore` (already configured)
- ✅ Use `.env.example` as a template (committed to repo)
- ✅ Store production keys in secure vault (1Password, AWS Secrets Manager, etc.)
- ✅ Use different keys for dev/staging/production

**DON'T:**
- ❌ NEVER commit `.env` to Git
- ❌ NEVER share API keys in chat/email/Slack
- ❌ NEVER hardcode keys in source code
- ❌ NEVER use production keys in development
- ❌ NEVER share keys across multiple projects

### 2. API Key Rotation Schedule

**Recommended:**
- **Every 90 days**: Rotate all API keys
- **Immediately**: If key is exposed or compromised
- **Quarterly**: Review all API access and permissions

**Set Calendar Reminders:**
- January 1: Rotate all keys
- April 1: Rotate all keys
- July 1: Rotate all keys
- October 1: Rotate all keys

### 3. Git Security Checks

**Before Every Commit:**
```bash
# Check for secrets
git diff | grep -E "sk-|xai-|AIza|BSA"

# Check staged files
git diff --cached | grep -E "API_KEY|SECRET|PASSWORD"
```

**Add Pre-Commit Hook** (optional):
```bash
# Create .git/hooks/pre-commit
#!/bin/bash
if git diff --cached | grep -qE "sk-[a-zA-Z0-9]{20,}|xai-[a-zA-Z0-9]{20,}|AIza[a-zA-Z0-9]{20,}"; then
  echo "ERROR: Potential API key detected in staged changes!"
  echo "Please remove API keys before committing."
  exit 1
fi
```

### 4. Secure Storage Solutions

**For Local Development:**
- Use `.env` file (gitignored)
- Store backup in password manager (1Password, Bitwarden, etc.)

**For Production:**
- **Railway**: Use Environment Variables in dashboard
- **Vercel**: Use Environment Variables in project settings
- **AWS**: Use AWS Secrets Manager
- **Azure**: Use Azure Key Vault
- **GCP**: Use Secret Manager
- **Docker**: Use Docker Secrets

---

## 📋 Setting Up Your Environment

### Step 1: Copy Template

```bash
cd TORQ-CONSOLE
cp .env.example .env
```

### Step 2: Get API Keys

#### Required (at least one LLM provider):

**OpenAI API:**
1. Go to: https://platform.openai.com/signup
2. Create account or log in
3. Navigate to API Keys: https://platform.openai.com/api-keys
4. Click "Create new secret key"
5. Name it "TORQ-Console-Dev"
6. Copy the key (starts with `sk-proj-` or `sk-`)
7. Add to `.env`: `OPENAI_API_KEY=sk-...`

**Anthropic API (Claude):**
1. Go to: https://console.anthropic.com/
2. Create account or log in
3. Navigate to API Keys
4. Click "Create Key"
5. Name it "TORQ-Console-Dev"
6. Copy the key (starts with `sk-ant-`)
7. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

**DeepSeek API:**
1. Go to: https://platform.deepseek.com/
2. Create account or log in
3. Get API key
4. Add to `.env`: `DEEPSEEK_API_KEY=sk-...`

**Z.AI GLM API:**
1. Go to: https://open.bigmodel.cn/
2. Create account or log in
3. Get API key
4. Add to `.env`: `GLM_API_KEY=...`

**X.AI API (Grok):**
1. Go to: https://console.x.ai/
2. Create account or log in
3. Navigate to Team → API Keys
4. Create new key
5. Add to `.env`: `XAI_API_KEY=xai-...`

#### Optional (but recommended for search):

**Google Search API:**
1. Go to: https://console.cloud.google.com/
2. Create new project or select existing
3. Enable "Custom Search API"
4. Create credentials → API Key
5. Create Custom Search Engine: https://programmablesearchengine.google.com/
6. Get Engine ID
7. Add to `.env`:
   ```
   GOOGLE_SEARCH_API_KEY=AIza...
   GOOGLE_SEARCH_ENGINE_ID=...
   ```

**Brave Search API:**
1. Go to: https://brave.com/search/api/
2. Sign up (2,000 free queries/month)
3. Get API key
4. Add to `.env`: `BRAVE_SEARCH_API_KEY=BSA...`

### Step 3: Verify Configuration

```bash
# Check .env file exists and is NOT tracked
ls -la .env
git status | grep .env  # Should return nothing

# Verify .gitignore includes .env
cat .gitignore | grep "^\.env$"  # Should show .env

# Test with Python
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✓ API Key loaded' if os.getenv('OPENAI_API_KEY') else '✗ No key found')"
```

---

## 🛡️ Security Checklist

### Initial Setup
- [ ] Copied `.env.example` to `.env`
- [ ] Added at least one LLM API key
- [ ] Verified `.env` is in `.gitignore`
- [ ] Tested configuration loads correctly
- [ ] Stored backup of keys in password manager

### After Key Exposure
- [ ] Revoked all exposed keys immediately
- [ ] Generated new keys
- [ ] Updated `.env` with new keys
- [ ] Checked for unauthorized usage
- [ ] Set up billing alerts
- [ ] Monitored accounts for 48 hours

### Ongoing Security
- [ ] Rotate keys every 90 days
- [ ] Review API usage monthly
- [ ] Keep `.env` out of version control
- [ ] Never share keys in messages/emails
- [ ] Use different keys for dev/prod
- [ ] Monitor billing/usage regularly

---

## 🔍 What We Fixed

### Files Changed:
1. **`.env`** - Removed from Git tracking, replaced real keys with placeholders
2. **`.env.example`** - Updated with comprehensive template and instructions
3. **`.gitignore`** - Already includes `.env` (line 29)
4. **`SECURITY_SETUP.md`** - This guide

### Git Changes:
```bash
# Removed .env from tracking
git rm --cached .env

# Committed security fix
git commit -m "security: Remove exposed API keys from version control"
```

### What's Protected Now:
- ✅ `.env` file is no longer tracked by Git
- ✅ Real API keys replaced with placeholders
- ✅ `.env.example` provides secure template
- ✅ This guide documents rotation process
- ✅ `.gitignore` prevents future accidents

---

## ❓ FAQ

**Q: Can I use the exposed keys?**
A: **NO!** They were public and must be revoked. Anyone could have copied them.

**Q: What if I already committed .env in my branch?**
A: Follow this guide to remove it from your branch too. Use `git filter-branch` or `BFG Repo-Cleaner` to remove from history.

**Q: How do I know if someone used my keys?**
A: Check usage dashboards on each service. Look for unexpected spikes or calls from unknown IPs.

**Q: Should I use .env in production?**
A: NO! Use environment variables via your hosting platform (Railway, Vercel, AWS, etc.).

**Q: Can I share .env.example?**
A: YES! `.env.example` contains only placeholders and is safe to commit.

**Q: What if I accidentally commit a key?**
A: 1) Revoke it immediately, 2) Remove from Git history, 3) Generate new key, 4) Update `.env`

---

## 📞 Support

**Security Issues:**
- Email: security@torq-console.dev (if available)
- GitHub Issues: https://github.com/pilotwaffle/TORQ-CONSOLE/issues (for non-sensitive issues)

**API Provider Support:**
- OpenAI: https://help.openai.com/
- Anthropic: https://support.anthropic.com/
- Google Cloud: https://cloud.google.com/support
- Brave: https://brave.com/search/api/

---

**Last Updated**: November 4, 2025
**Status**: ✅ Security fixes applied, keys removed from Git
**Action Required**: REVOKE and ROTATE exposed keys immediately
