# LLM Dropdown Analysis Report

## Current Status: ⚠️ Issues Found

### Models Listed in Dropdown (8 total)

From `/torq_console/ui/templates/dashboard.html` (lines 1013-1021):

| # | Model Name | Model ID | Status | Notes |
|---|------------|----------|--------|-------|
| 1 | Claude Sonnet 4.5 (Latest) | `claude-sonnet-4-5-20250929` | ✅ **WORKING** | Requires `ANTHROPIC_API_KEY` |
| 2 | Claude 3.5 Sonnet | `claude-3-5-sonnet-20241022` | ✅ **WORKING** | Requires `ANTHROPIC_API_KEY` |
| 3 | Claude 3 Opus | `claude-3-opus-20240229` | ✅ **WORKING** | Requires `ANTHROPIC_API_KEY` |
| 4 | GPT-4 Turbo | `gpt-4-turbo-preview` | ❌ **NOT WORKING** | No OpenAI provider exists |
| 5 | GPT-4o | `gpt-4o` | ❌ **NOT WORKING** | No OpenAI provider exists |
| 6 | DeepSeek Chat | `deepseek-chat` | ✅ **WORKING** | Requires `DEEPSEEK_API_KEY` |
| 7 | Llama 3.1 405B | `llama-3.1-405b` | ⚠️ **MAYBE WORKING** | Via Ollama (if model installed) |
| 8 | Gemini Pro | `gemini-pro` | ❌ **NOT WORKING** | No Gemini provider exists |

---

## GLM-4.6: Missing from Dropdown ❌

### GLM-4.6 Integration Status

**Integration Exists:** ✅ YES
- **Files:**
  - `torq_console/llm/glm_client.py` (GLM client)
  - `torq_console/agents/glm_prince_flowers.py` (GLM agent)
  - `GLM_4_6_INTEGRATION.md` (documentation)
  - `test_glm_simple.py`, `test_glm_integration.py` (tests)

**Why It's Not in Dropdown:** ❌ Not registered as provider

**Problem:** GLM-4.6 is integrated as a **standalone agent** but NOT as a **provider** in the LLM Manager.

### What Exists:
- ✅ `GLMClient` class (`torq_console/llm/glm_client.py`)
- ✅ `GLMPrinceFlowersAgent` class (`torq_console/agents/glm_prince_flowers.py`)
- ✅ API integration (Z.AI OpenAI-compatible API)
- ✅ Test files proving it works

### What's Missing:
- ❌ `GLMProvider` class in `torq_console/llm/providers/`
- ❌ Registration in `LLMManager.__init__()`
- ❌ Entry in UI dropdown (`dashboard.html`)
- ❌ Provider alias in `LLMManager.provider_aliases`

---

## LLM Manager - Registered Providers

From `torq_console/llm/manager.py` (lines 43-52):

### Currently Registered:
1. ✅ **Claude** - `ClaudeProvider` (default provider)
   - Requires: `ANTHROPIC_API_KEY`
   - Models: Any Claude model ID

2. ✅ **DeepSeek** - `DeepSeekProvider` (search provider)
   - Requires: `DEEPSEEK_API_KEY`
   - Models: `deepseek-chat`, `deepseek-coder`

3. ✅ **Ollama** - `OllamaProvider` (local provider)
   - Requires: Ollama running on `localhost:11434`
   - Models: Any Ollama-installed model
   - Default: `deepseek-r1:7b`

4. ⚠️ **Llama.cpp** - `LlamaCppProvider` (optional)
   - Requires: `llama-cpp-python` installed + model file
   - Fast local inference with GPU support

### NOT Registered:
- ❌ **OpenAI** - No provider class exists
- ❌ **Gemini** - No provider class exists
- ❌ **GLM** - Client exists, but no provider class

---

## Working vs Non-Working Models

### ✅ Confirmed Working (4 providers)

**Claude Models** (if `ANTHROPIC_API_KEY` set):
- `claude-sonnet-4-5-20250929` ✅
- `claude-3-5-sonnet-20241022` ✅
- `claude-3-opus-20240229` ✅
- Any other valid Claude model ID

**DeepSeek Models** (if `DEEPSEEK_API_KEY` set):
- `deepseek-chat` ✅
- `deepseek-coder` ✅

**Ollama Models** (if Ollama running):
- `llama-3.1-405b` (if installed locally) ⚠️
- `deepseek-r1:7b` (default) ✅
- Any Ollama-installed model ✅

**Llama.cpp Models** (if configured):
- Local GGUF models ⚠️

### ❌ Listed But NOT Working (3 models)

**OpenAI Models** (no provider):
- `gpt-4-turbo-preview` ❌
- `gpt-4o` ❌

**Google Models** (no provider):
- `gemini-pro` ❌

### 🔍 Integrated But NOT Listed (1 model)

**Z.AI Models** (client exists, no provider):
- `glm-4.6` 🔍 (works via standalone agent only)

---

## Health Check Status

From `torq_console/ui/web.py` (lines 234-239):

```python
llm_providers = {
    "claude": "operational" if os.getenv('ANTHROPIC_API_KEY') else "not_configured",
    "deepseek": "operational" if os.getenv('DEEPSEEK_API_KEY') else "not_configured",
    "ollama": "operational",  # Assume available if local
    "llama_cpp": "operational"
}
```

**Status:**
- Claude: Checks for API key ✅
- DeepSeek: Checks for API key ✅
- Ollama: Always reports operational (optimistic) ⚠️
- Llama.cpp: Always reports operational (optimistic) ⚠️
- OpenAI: NOT checked (because no provider) ❌
- Gemini: NOT checked (because no provider) ❌
- GLM: NOT checked (because no provider) ❌

---

## Issues Summary

### Critical Issues 🔴

1. **Dropdown shows non-working models**
   - GPT-4 Turbo, GPT-4o, Gemini Pro are listed but have NO provider
   - Users will select these and get errors

2. **GLM-4.6 is hidden**
   - Fully integrated and working
   - But not accessible via dropdown
   - Only accessible via direct agent usage

### Minor Issues 🟡

3. **Ollama model assumption**
   - Dropdown shows "Llama 3.1 405B"
   - But this only works if user has Ollama + downloaded that specific model
   - Could fail silently

4. **Health check optimistic**
   - Ollama and Llama.cpp always report "operational"
   - Even if not actually running/configured

---

## Recommendations

### Immediate Fixes Needed:

1. **Remove non-working models from dropdown**
   - Remove: `gpt-4-turbo-preview`
   - Remove: `gpt-4o`
   - Remove: `gemini-pro`
   - OR: Create OpenAI and Gemini providers

2. **Add GLM-4.6 to dropdown**
   - Create `GLMProvider` class in `torq_console/llm/providers/glm.py`
   - Register in `LLMManager._init_glm()`
   - Add to dropdown: `<option value="glm-4.6">GLM-4.6 (Z.AI)</option>`
   - Add to health check

3. **Fix Ollama dropdown entry**
   - Change "Llama 3.1 405B" to generic "Ollama (Local)"
   - Or dynamically populate from installed models

4. **Improve health checks**
   - Actually check if Ollama is running (try API call)
   - Actually check if Llama.cpp model exists

---

## How to Add GLM-4.6 to Dropdown

### Step 1: Create GLM Provider

Create `/torq_console/llm/providers/glm.py`:

```python
"""GLM-4.6 Provider for TORQ Console."""
from typing import Optional, Dict, Any
from .base import LLMProvider
from ..glm_client import GLMClient

class GLMProvider(LLMProvider):
    """Z.AI GLM-4.6 provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "glm-4.6"):
        self.client = GLMClient(api_key=api_key, model=model)
        self.model = model

    def is_configured(self) -> bool:
        return self.client.api_key is not None

    async def generate(self, messages, **kwargs):
        return self.client.chat(messages, **kwargs)
```

### Step 2: Register in LLM Manager

Add to `torq_console/llm/manager.py`:

```python
# Line 15: Add import
from .providers.glm import GLMProvider

# Line 52: Add initialization
self._init_glm()

# Line 150+: Add init method
def _init_glm(self):
    """Initialize GLM provider."""
    try:
        api_key = os.getenv('GLM_API_KEY')
        provider = GLMProvider(api_key=api_key, model='glm-4.6')
        self.providers['glm'] = provider

        if provider.is_configured():
            self.logger.info("GLM provider configured successfully")
        else:
            self.logger.warning("GLM provider not configured (missing GLM_API_KEY)")
    except Exception as e:
        self.logger.error(f"Failed to initialize GLM provider: {e}")
```

### Step 3: Add to Dropdown

Edit `torq_console/ui/templates/dashboard.html` line 1018:

```html
<option value="glm-4.6">GLM-4.6 (Z.AI)</option>
```

### Step 4: Add to Health Check

Edit `torq_console/ui/web.py` line 237:

```python
llm_providers = {
    "claude": "operational" if os.getenv('ANTHROPIC_API_KEY') else "not_configured",
    "deepseek": "operational" if os.getenv('DEEPSEEK_API_KEY') else "not_configured",
    "glm": "operational" if os.getenv('GLM_API_KEY') else "not_configured",
    "ollama": "operational",
    "llama_cpp": "operational"
}
```

---

## Current Working Configuration

**If you want ONLY working models in dropdown right now:**

```html
<select x-model="selectedModel" @change="updateModel()"
        class="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm">
    <!-- Claude Models (requires ANTHROPIC_API_KEY) -->
    <option value="claude-sonnet-4-5-20250929">Claude Sonnet 4.5 (Latest)</option>
    <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
    <option value="claude-3-opus-20240229">Claude 3 Opus</option>

    <!-- DeepSeek Models (requires DEEPSEEK_API_KEY) -->
    <option value="deepseek-chat">DeepSeek Chat</option>

    <!-- Local Models (requires Ollama running) -->
    <option value="deepseek-r1:7b">DeepSeek R1 7B (Local)</option>
    <option value="llama-3.1-405b">Llama 3.1 405B (Local)</option>
</select>
```

**Plus GLM-4.6 after implementing provider:**
```html
    <!-- Z.AI Models (requires GLM_API_KEY) -->
    <option value="glm-4.6">GLM-4.6 (Z.AI)</option>
```

---

## Summary

### Currently Working: 4/8 Models ✅
- Claude Sonnet 4.5 ✅
- Claude 3.5 Sonnet ✅
- Claude 3 Opus ✅
- DeepSeek Chat ✅

### Listed But Broken: 3/8 Models ❌
- GPT-4 Turbo ❌
- GPT-4o ❌
- Gemini Pro ❌

### Unclear: 1/8 Models ⚠️
- Llama 3.1 405B (depends on Ollama + local model)

### Missing: 1 Model 🔍
- GLM-4.6 (integrated but not in dropdown)

### Recommendation:
**Remove broken models and add GLM-4.6 for a clean, working dropdown.**
