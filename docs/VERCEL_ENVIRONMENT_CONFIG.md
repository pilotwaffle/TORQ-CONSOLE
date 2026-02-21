# Vercel Production Environment Configuration

**Date**: 2026-02-17
**Purpose**: Define exactly which environment variables go into Vercel vs local development

---

## Vercel Production Variables (Required)

### Provider Fallback Configuration

```bash
# Feature Flag - Start with FALSE, enable after smoke tests
TORQ_FALLBACK_ENABLED=false

# Provider Chains - No "openai" (provider doesn't exist)
TORQ_DIRECT_CHAIN=deepseek,claude,ollama
TORQ_RESEARCH_CHAIN=claude,deepseek,ollama
TORQ_CODE_CHAIN=claude,deepseek
```

### AI Provider API Keys (Sensitive)

```bash
# At least one of these is required
ANTHROPIC_API_KEY=<your_key>  # For Claude
DEEPSEEK_API_KEY=<your_key>   # For DeepSeek
# OPENAI_API_KEY=<your_key>   # Optional - no OpenAI provider exists yet
```

### Ollama Configuration (Optional - Only if you have a remote endpoint)

```bash
# ONLY add this if you have a remotely accessible Ollama instance
# If Ollama is local-only (localhost:11434), it will fail in Vercel
# OLLAMA_BASE_URL=https://your-ollama-endpoint.com
```

### Production Settings (Already in vercel.json)

```bash
TORQ_CONSOLE_PRODUCTION=true
TORQ_DISABLE_LOCAL_LLM=true
TORQ_DISABLE_GPU=true
PYTHON_VERSION=3.11
```

---

## Local Development Variables (.env)

Keep ALL variables in `.env.example` for local development, but add these new ones:

### Provider Fallback (Local Testing)

```bash
# Enable fallback for local testing
TORQ_FALLBACK_ENABLED=true

# Local chains (can include Ollama since it's localhost)
TORQ_DIRECT_CHAIN=deepseek,claude,ollama
TORQ_RESEARCH_CHAIN=claude,deepseek,ollama
TORQ_CODE_CHAIN=claude,deepseek
```

### All Other Variables (.env.example)

Keep everything from `.env.example`:
- ✅ Financial APIs (ALPHA_VANTAGE, FRED)
- ✅ News APIs (NEWS_API)
- ✅ Search APIs (GOOGLE_SEARCH, BRAVE_SEARCH)
- ✅ AI Provider Keys (OPENAI, ANTHROPIC, DEEPSEEK, XAI)
- ✅ Twitter/X API
- ✅ TBS Configuration
- ✅ Service Configuration
- ✅ Debug Settings
- ✅ MCP Server
- ✅ Security Settings
- ✅ GPU Acceleration (local only)
- ✅ Codebase Indexer

---

## Vercel vs Local: What Goes Where

### Vercel Production (Minimal)

**Required**:
- `TORQ_FALLBACK_ENABLED=false` (start disabled)
- `TORQ_DIRECT_CHAIN=deepseek,claude,ollama`
- `TORQ_RESEARCH_CHAIN=claude,deepseek,ollama`
- `TORQ_CODE_CHAIN=claude,deepseek`
- At least one AI provider key (ANTHROPIC_API_KEY or DEEPSEEK_API_KEY)

**Optional**:
- `OLLAMA_BASE_URL` (only if you have remote Ollama)
- `OPENAI_API_KEY` (only if you implement OpenAI provider)

**Already in vercel.json** (don't add these manually):
- `TORQ_CONSOLE_PRODUCTION=true`
- `TORQ_DISABLE_LOCAL_LLM=true`
- `TORQ_DISABLE_GPU=true`
- `PYTHON_VERSION=3.11`

### Local Development (.env)

**Everything from .env.example PLUS**:
- `TORQ_FALLBACK_ENABLED=true` (for local testing)
- `TORQ_DIRECT_CHAIN=deepseek,claude,ollama`
- `TORQ_RESEARCH_CHAIN=claude,deepseek,ollama`
- `TORQ_CODE_CHAIN=claude,deepseek`

---

## Critical Differences

### Ollama in Vercel

❌ **Problem**: Ollama on `localhost:11434` is NOT accessible from Vercel serverless functions

✅ **Solutions**:
1. **Best**: Remove `ollama` from production chains:
   ```bash
   TORQ_DIRECT_CHAIN=deepseek,claude
   TORQ_RESEARCH_CHAIN=claude,deepseek
   TORQ_CODE_CHAIN=claude,deepseek
   ```

2. **Alternative**: Deploy Ollama to a remote server:
   ```bash
   OLLAMA_BASE_URL=https://your-ollama-instance.com
   ```

3. **Accept failures**: Keep `ollama` in chains - it will always fail in production but fallback handles it

### OpenAI in Vercel

❌ **Problem**: `OPENAI_API_KEY` exists but no OpenAI provider implementation

✅ **Solutions**:
1. **Don't add** `OPENAI_API_KEY` to Vercel (until provider is implemented)
2. **Don't include** `openai` in any chains (already removed)

---

## Vercel Setup Instructions

### Step 1: Go to Vercel Dashboard

Navigate to: https://vercel.com/pilotwaffles-projects/torq-console/settings/environment-variables

### Step 2: Add Required Variables

Click "Add New" and add each variable:

#### Fallback Configuration (3 variables)

| Key | Value | Sensitive | Environment |
|-----|-------|-----------|-------------|
| `TORQ_FALLBACK_ENABLED` | `false` | No | Production, Preview |
| `TORQ_DIRECT_CHAIN` | `deepseek,claude,ollama` | No | Production, Preview |
| `TORQ_RESEARCH_CHAIN` | `claude,deepseek,ollama` | No | Production, Preview |
| `TORQ_CODE_CHAIN` | `claude,deepseek` | No | Production, Preview |

#### AI Provider Keys (Sensitive - Add at least one)

| Key | Value | Sensitive | Environment |
|-----|-------|-----------|-------------|
| `ANTHROPIC_API_KEY* | `<your_key>` | **Yes** | Production, Preview |
| `DEEPSEEK_API_KEY* | `<your_key>` | **Yes** | Production, Preview |

* Mark these as "Sensitive" in Vercel

### Step 3: Save and Redeploy

After adding variables:
1. Click "Save"
2. Vercel will auto-redeploy
3. Wait for deployment to complete

---

## .env.example Update Needed

Add these lines to `.env.example` (for reference):

```bash
# =============================================================================
# PROVIDER FALLBACK CONFIGURATION
# =============================================================================

# Enable/disable provider fallback (retry with different providers on failure)
TORQ_FALLBACK_ENABLED=true

# Provider chains for different execution modes (comma-separated, no spaces)
TORQ_DIRECT_CHAIN=deepseek,claude,ollama
TORQ_RESEARCH_CHAIN=claude,deepseek,ollama
TORQ_CODE_CHAIN=claude,deepseek

# Note: For Vercel production, remove "ollama" if you don't have a remote endpoint
# TORQ_DIRECT_CHAIN=deepseek,claude
# TORQ_RESEARCH_CHAIN=claude,deepseek
# TORQ_CODE_CHAIN=claude,deepseek
```

---

## Pre-Deploy Checklist

Before enabling `TORQ_FALLBACK_ENABLED=true` in Vercel:

- [ ] Tests pass locally (`pytest tests/test_provider_fallback.py -v`)
- [ ] Vercel environment variables configured
- [ ] API keys added (ANTHROPIC_API_KEY, DEEPSEEK_API_KEY)
- [ ] Chains configured (no "openai")
- [ ] Smoke tests passed on deployed app
- [ ] Ollama removed from chains OR remote endpoint configured

---

## Rollback Plan

If fallback causes issues:

1. **Immediate rollback**:
   - Go to Vercel environment variables
   - Set `TORQ_FALLBACK_ENABLED=false`
   - Save (will auto-redeploy)

2. **Investigate**:
   - Check `/api/diag` endpoint for provider attempts
   - Review Vercel logs for errors
   - Identify failing provider

3. **Fix and retry**:
   - Remove problematic provider from chains
   - Add missing API keys
   - Re-enable fallback

---

## Summary

### What to Add to Vercel Now

**Add these 5 variables to Vercel**:

1. `TORQ_FALLBACK_ENABLED=false` (start disabled)
2. `TORQ_DIRECT_CHAIN=deepseek,claude,ollama`
3. `TORQ_RESEARCH_CHAIN=claude,deepseek,ollama`
4. `TORQ_CODE_CHAIN=claude,deepseek`
5. `ANTHROPIC_API_KEY=<your_key>` or `DEEPSEEK_API_KEY=<your_key>` (at least one)

### What to Keep Local

Keep everything else in `.env`:
- Financial APIs
- News APIs
- Search APIs
- Twitter/X API
- TBS config
- Debug settings
- MCP config
- GPU/LLM config
- Codebase indexer

---

**Status**: Ready for Vercel configuration
**Next**: Add environment variables to Vercel dashboard, then smoke test
