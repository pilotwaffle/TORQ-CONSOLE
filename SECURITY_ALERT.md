# 🚨 SECURITY ALERT - API Keys Exposed

## CRITICAL ACTIONS REQUIRED IMMEDIATELY

### API Keys That Need to be Revoked and Rotated

The following API keys were found exposed and must be revoked/rotated:

1. **OpenAI API Key**
   - Current: `sk-proj-6gpZ...wUA` (EXPOSED)
   - Action: Go to https://platform.openai.com/api-keys
   - Steps:
     1. Delete the exposed key
     2. Generate a new key
     3. Update `.env` file
     4. Never commit to Git

2. **X.AI API Key** (provided in chat)
   - Current: `xai-zQnQ...LuE` (EXPOSED)
   - Action: Go to https://console.x.ai/team/api-keys
   - Steps:
     1. Revoke the exposed key immediately
     2. Generate a new key
     3. Add to `.env` securely

3. **Google Search API Key**
   - Current: `AIzaSyA7...hDw` (EXPOSED)
   - Action: Go to https://console.cloud.google.com/apis/credentials

4. **Brave Search API Key**
   - Current: `BSAkNrh3...PfO` (EXPOSED)
   - Action: Go to https://brave.com/search/api/

5. **DeepSeek API Key**
   - Current: `sk-f746...93a` (EXPOSED)
   - Action: Contact DeepSeek support or regenerate

## Why This Matters

Exposed API keys can be used by anyone to:
- ❌ Consume your API quota
- ❌ Generate charges on your account
- ❌ Access your data
- ❌ Perform unauthorized actions
- ❌ Get you banned from the service

## How to Fix This

### Step 1: Revoke All Exposed Keys (NOW)

Visit each service and revoke the exposed keys:

| Service | URL | Priority |
|---------|-----|----------|
| OpenAI | https://platform.openai.com/api-keys | CRITICAL |
| X.AI | https://console.x.ai/team/api-keys | CRITICAL |
| Google Cloud | https://console.cloud.google.com/apis/credentials | HIGH |
| Brave Search | https://brave.com/search/api/ | MEDIUM |
| DeepSeek | Contact support | MEDIUM |

### Step 2: Generate New Keys

After revoking, generate new keys from the same dashboards.

### Step 3: Update .env Securely

```bash
# DO NOT commit .env to Git!
# Add to .gitignore if not already there

# X.AI/Grok API Configuration
XAI_API_KEY=your_new_xai_key_here
XAI_API_BASE_URL=https://api.x.ai/v1

# OpenAI API Configuration (NEW KEY)
OPENAI_API_KEY=your_new_openai_key_here

# Google Search API (NEW KEY)
GOOGLE_SEARCH_API_KEY=your_new_google_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id

# Brave Search API (NEW KEY)
BRAVE_SEARCH_API_KEY=your_new_brave_key_here

# DeepSeek API (NEW KEY)
DEEPSEEK_API_KEY=your_new_deepseek_key_here
```

### Step 4: Verify .env is in .gitignore

```bash
# Check if .env is ignored
cd TORQ-CONSOLE
cat .gitignore | grep -E "^\.env$|^\.env\..*$"

# If not found, add it:
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
echo "!.env.example" >> .gitignore
```

### Step 5: Remove from Git History (if committed)

If you've committed `.env` to Git:

```bash
# WARNING: This rewrites Git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (coordinate with team first!)
git push origin --force --all
```

## Best Practices Going Forward

### 1. Use .env.example Template

Create `.env.example` with placeholder values:

```bash
# .env.example - Safe to commit to Git
OPENAI_API_KEY=your_openai_key_here
XAI_API_KEY=your_xai_key_here
GOOGLE_SEARCH_API_KEY=your_google_key_here
# ... etc
```

### 2. Never Share Keys Publicly

- ❌ Don't paste in chat/forums
- ❌ Don't commit to Git
- ❌ Don't include in screenshots
- ✅ Use environment variables
- ✅ Use secret management tools
- ✅ Rotate keys regularly

### 3. Use Secret Management Tools

For production:
- **GitHub Secrets**: For GitHub Actions
- **Azure Key Vault**: For Azure deployments
- **AWS Secrets Manager**: For AWS
- **1Password/Bitwarden**: For team sharing

### 4. Monitor API Usage

Set up billing alerts:
- OpenAI: https://platform.openai.com/account/billing/overview
- X.AI: Check console for usage tracking
- Google Cloud: Set up billing alerts

### 5. Implement IP Restrictions

Where possible, restrict API keys to specific IP addresses.

## X.AI/Grok API Setup (Secure Method)

### Get Your Key Securely

1. Go to https://console.x.ai/
2. Sign in with your X/Twitter account
3. Navigate to "API Keys"
4. Click "Create New Key"
5. **Copy immediately** - shown only once
6. Save to `.env` file (NOT to Git!)

### Add to .env

```bash
# X.AI/Grok API Configuration
XAI_API_KEY=xai-your-actual-key-here-keep-secret
XAI_MODEL=grok-beta
XAI_API_BASE_URL=https://api.x.ai/v1
```

### Test Your Configuration

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Test X.AI key is loaded (DO NOT PRINT THE KEY!)
xai_key = os.getenv('XAI_API_KEY')
if xai_key:
    print(f"✓ X.AI key loaded: {xai_key[:10]}...{xai_key[-4:]}")
else:
    print("✗ X.AI key not found")
```

## Checklist

- [ ] Revoke exposed OpenAI key
- [ ] Revoke exposed X.AI key
- [ ] Revoke exposed Google Search key
- [ ] Revoke exposed Brave Search key
- [ ] Revoke exposed DeepSeek key
- [ ] Generate new keys for all services
- [ ] Update `.env` with new keys
- [ ] Verify `.env` is in `.gitignore`
- [ ] Remove `.env` from Git history (if needed)
- [ ] Set up billing alerts
- [ ] Enable IP restrictions where possible
- [ ] Create `.env.example` template
- [ ] Test new configuration
- [ ] Document key rotation date

## Emergency Contacts

If unauthorized usage detected:

- **OpenAI**: support@openai.com
- **X.AI**: support@x.ai
- **Google Cloud**: https://cloud.google.com/support
- **Brave**: Contact via API dashboard

## Prevention

This happened because `.env` was either:
1. Committed to Git
2. Shared in public chat
3. Included in screenshots

**Solution**: Always treat API keys like passwords - keep them secret!

---

**Status**: 🚨 URGENT - Take action immediately
**Priority**: CRITICAL
**Estimated Time**: 15-30 minutes to complete all steps
