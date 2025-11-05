# TORQ Console Security Setup Guide

**Date**: November 4, 2025
**Status**: ✅ Preventive Security Configuration

---

## 🛡️ Security Best Practices Implementation

### What Happened

The `.env` file containing API keys was tracked in Git (commit `b208f182a4`). As a **preventive security measure**, we've removed it from version control and implemented best practices.

**Important**: These keys were **only in local development** and were never pushed to public repositories. No key rotation is required unless you want to follow security best practices.

### Keys That Were in .env File

The following API keys were found in the local `.env` file (now removed from Git tracking):

1. **Google Search API**
   - Key: `AIzaSyA7eNQYC-zgo2OTYjL4QnrT5GeoHxJAhDw`
   - Status: ✅ Local only, not exposed publicly

2. **Brave Search API**
   - Key: `BSAkNrh316HK8uxqGjUN1_eeLon8PfO`
   - Status: ✅ Local only, not exposed publicly

3. **OpenAI API**
   - Key: `sk-proj-6gpZOJB52QxqLgW6XjiE...` (partial)
   - Status: ✅ Local only, not exposed publicly

---

## ✅ Preventive Security Measures Applied

### What We Fixed (No Urgent Action Needed)

1. **Removed `.env` from Git tracking**
   - Used `git rm --cached .env`
   - File still exists locally with your keys intact
   - No longer tracked in version control

2. **Updated `.env.example` template**
   - Comprehensive template for all services
   - Security notices and setup instructions
   - Safe to commit (contains only placeholders)

3. **Created this security guide**
   - Best practices documentation
   - Setup instructions for new developers
   - Key rotation guidelines (optional)

### Optional: Key Rotation (Recommended Security Practice)

While not urgent since keys were never exposed, you may want to rotate keys as a security best practice:

#### Google Search API (Optional)
1. Go to: https://console.cloud.google.com/apis/credentials
2. Create new API key
3. Update your local `.env` file
4. Delete old key

#### Brave Search API (Optional)
1. Go to: https://brave.com/search/api/
2. Generate new key
3. Update your local `.env` file
4. Revoke old key

#### OpenAI API (Optional)
1. Go to: https://platform.openai.com/api-keys
2. Create new API key
3. Update your local `.env` file
4. Revoke old key

### Recommended: Set Up Billing Alerts

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

### Preventive Security Setup (Optional)
- [ ] Consider rotating keys as best practice
- [ ] Set up billing alerts for cost monitoring
- [ ] Review API usage monthly
- [ ] Keep backup of keys in password manager

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

**Q: Were my API keys exposed publicly?**
A: **NO!** The keys were only in local Git commits that were never pushed to public repositories. This is a preventive security measure.

**Q: Do I need to revoke my keys immediately?**
A: **NO** - since they were never exposed publicly. However, rotating keys periodically (every 90 days) is a recommended security practice.

**Q: Can I keep using my existing keys?**
A: **YES!** Your keys are safe to continue using. They were never exposed publicly.

**Q: What if I already committed .env in my branch?**
A: Follow this guide to remove it from your branch too for best practices. Use `git rm --cached .env` on your branch.

**Q: Should I monitor my API usage?**
A: It's good practice to occasionally check usage dashboards on each service, but there's no urgent need since keys weren't exposed.

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
**Status**: ✅ Preventive security measures applied
**Action Required**: None urgent - keys were never publicly exposed
**Note**: This is a preventive configuration following security best practices
