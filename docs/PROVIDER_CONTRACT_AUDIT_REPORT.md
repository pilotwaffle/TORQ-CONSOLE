# Provider Contract Audit Report

**Date**: 2026-02-17
**Auditor**: Claude Code (Platform Engineering Review)
**Status**: ❌ **CRITICAL ISSUES FOUND - NOT SAFE TO ENABLE**
**Scope**: Contract compliance for provider fallback integration

---

## Executive Summary

This audit validates that all LLM providers comply with the [Provider Fallback Contract](./PROVIDER_FALLBACK.md) before enabling `TORQ_FALLBACK_ENABLED=true` in production.

**Overall Result**: ❌ **CRITICAL VIOLATIONS DETECTED**

### Critical Findings

1. ❌ **OpenAI Provider Missing**: Provider chains reference "openai" but no OpenAI provider exists
2. ❌ **OllamaProvider Contract Violations**: Returns error strings instead of raising exceptions
3. ✅ **ClaudeProvider**: Contract compliant
4. ✅ **DeepSeekProvider**: Contract compliant
5. ⚠️ **GLMProvider**: Partial compliance (raises generic exceptions)

---

## Audit Criteria

Each provider is evaluated against the [Provider Fallback Contract](./PROVIDER_FALLBACK.md):

### Required Behaviors

1. **No Error Strings Returned**: Providers must raise typed exceptions, never return error strings/dicts
2. **Typed Exception Hierarchy**:
   - `AIResponseError` for content policy violations (non-retryable)
   - `AITimeoutError` for timeouts (retryable)
   - `ProviderError` for infrastructure issues (429, 5xx, network) (retryable)
3. **Error Code Mapping**: 429 → `code="429"`, 5xx → `code="500"`, etc.
4. **No Internal Retries**: Fallback layer handles all retries
5. **Policy Violation Detection**: Content safety errors must raise `AIResponseError` (terminal)

---

## Provider Audit Results

### 1. ClaudeProvider ✅ CONTRACT COMPLIANT

**File**: [torq_console/llm/providers/claude.py](../torq_console/llm/providers/claude.py)

#### Contract Compliance

| Requirement | Status | Evidence |
|------------|--------|----------|
| No error strings returned | ✅ PASS | Only returns `response.content[0].text` on success (line 112) |
| Timeouts → AITimeoutError | ✅ PASS | Lines 114-116: Catches `asyncio.TimeoutError`, raises `AITimeoutError` |
| Rate limits (429) → ProviderError | ✅ PASS | Lines 129-131: Raises `ProviderError` with `code="429"` |
| Server errors (5xx) → ProviderError | ✅ PASS | Lines 132-134: Raises `ProviderError` with status code |
| Policy violations → AIResponseError | ✅ PASS | Lines 19-43: `_is_policy_violation()` detector, lines 119-124: Raises `AIResponseError` |
| No internal retries | ✅ PASS | Single API call, no retry loop |
| Typed exception imports | ✅ PASS | Line 16: Imports `AIResponseError, AITimeoutError, ProviderError` |

#### Exception Classification

```
Success → Returns str (response.content[0].text)
Timeout → AITimeoutError (retryable)
429 → ProviderError(code="429") (retryable)
5xx → ProviderError(code="500") (retryable)
Policy violation → AIResponseError (non-retryable)
Other → ProviderError (retryable)
```

**Verdict**: ✅ **Safe for fallback integration**

---

### 2. DeepSeekProvider ✅ CONTRACT COMPLIANT

**File**: [torq_console/llm/providers/deepseek.py](../torq_console/llm/providers/deepseek.py)

#### Contract Compliance

| Requirement | Status | Evidence |
|------------|--------|----------|
| No error strings returned | ✅ PASS | Only returns `response_data` on success (line 150) |
| Timeouts → AITimeoutError | ✅ PASS | Lines 183-185: Catches `asyncio.TimeoutError`, raises `AITimeoutError` |
| Rate limits (429) → ProviderError | ✅ PASS | Lines 124-125, 168-170: Raises `ProviderError` with `code="429"` |
| Server errors (5xx) → ProviderError | ✅ PASS | Lines 171-173: Raises `ProviderError` with status code |
| Policy violations → AIResponseError | ✅ PASS | Lines 23-43: `_is_policy_violation()` detector, lines 160-165: Raises `AIResponseError` |
| No internal retries | ✅ PASS | Line 115: Comment confirms "Internal retry logic removed - fallback layer handles retries" |
| Typed exception imports | ✅ PASS | Line 20: Imports `AIResponseError, AITimeoutError, ProviderError` |

#### Exception Classification

```
Success → Returns dict (response_data)
Timeout → AITimeoutError (retryable)
429 → ProviderError(code="429") (retryable)
5xx → ProviderError(code="500") (retryable)
Network error → ProviderError(code="network_error") (retryable)
Policy violation → AIResponseError (non-retryable)
Adapter exception → ProviderError(code="adapter_error") (retryable)
```

**Verdict**: ✅ **Safe for fallback integration**

---

### 3. OllamaProvider ❌ CONTRACT VIOLATIONS

**File**: [torq_console/llm/providers/ollama.py](../torq_console/llm/providers/ollama.py)

#### Contract Compliance

| Requirement | Status | Evidence |
|------------|--------|----------|
| No error strings returned | ❌ **FAIL** | Lines 167-174: Returns error string in dict instead of raising exception |
| Timeouts → AITimeoutError | ❌ **FAIL** | No timeout exception handling |
| Rate limits (429) → ProviderError | ❌ **FAIL** | No 429 detection |
| Server errors (5xx) → ProviderError | ❌ **FAIL** | Lines 88-89, 91-94: Raises generic `Exception` not `ProviderError` |
| Policy violations → AIResponseError | ❌ **FAIL** | No policy violation detection |
| No internal retries | ✅ PASS | No retry loop |
| Typed exception imports | ❌ **FAIL** | No imports of `AIResponseError, AITimeoutError, ProviderError` |

#### Critical Violation Details

**Lines 165-174: Returns error string instead of raising exception**

```python
except Exception as e:
    self.logger.error(f"Ollama completion error: {e}")
    # Return a graceful error response instead of raising
    return {
        'content': f"I apologize, but I encountered an error while processing your request: {e}",
        'model': model,
        'usage': {},
        'finish_reason': 'error',
        'error': str(e)
    }
```

**This is a contract violation** because:
1. The fallback system expects providers to raise exceptions, not return error dicts
2. The error contains "I apologize" boilerplate that will trigger the contract violation detector in [provider_fallback.py:336-338](../torq_console/llm/provider_fallback.py#L336-L338)
3. This will cause the fallback system to raise `ProviderError(code="contract_violation")`

**Lines 88-94: Raises generic Exception**

```python
else:
    error_msg = response_data.get('error', f'HTTP {response.status}')
    raise Exception(f"Ollama API error: {error_msg}")

# ...

except aiohttp.ClientError as e:
    raise Exception(f"Network error: {e}")
except Exception as e:
    raise Exception(f"Ollama request failed: {e}")
```

**This is a contract violation** because:
1. Must raise `ProviderError` for infrastructure issues
2. Generic `Exception` doesn't provide error codes for dashboards

**Exception Classification (Current - Broken)**

```
Success → Returns dict (response_data)
Any error → Returns dict with 'content': "I apologize..." ❌ CONTRACT VIOLATION
```

**Verdict**: ❌ **NOT SAFE for fallback integration**

**Required Fixes**:

1. Remove error return in lines 167-174, raise exceptions instead
2. Import typed exceptions: `from torq_console.generation_meta import AIResponseError, AITimeoutError, ProviderError`
3. Map HTTP errors to `ProviderError` with codes
4. Add timeout detection and `AITimeoutError`
5. Add policy violation detection (if applicable for local models)

---

### 4. GLMProvider ⚠️ PARTIAL COMPLIANCE

**File**: [torq_console/llm/providers/glm.py](../torq_console/llm/providers/glm.py)

#### Contract Compliance

| Requirement | Status | Evidence |
|------------|--------|----------|
| No error strings returned | ⚠️ PARTIAL | Raises exception but generic `ValueError` for missing API key |
| Timeouts → AITimeoutError | ❌ UNKNOWN | Need to inspect full implementation |
| Rate limits (429) → ProviderError | ❌ UNKNOWN | Need to inspect full implementation |
| Server errors (5xx) → ProviderError | ❌ UNKNOWN | Need to inspect full implementation |
| Policy violations → AIResponseError | ❌ UNKNOWN | Need to inspect full implementation |
| No internal retries | ❌ UNKNOWN | Need to inspect full implementation |
| Typed exception imports | ❌ FAIL | No imports of `AIResponseError, AITimeoutError, ProviderError` |

**Verdict**: ⚠️ **Requires full audit before production use**

---

### 5. OpenAIProvider ❌ DOES NOT EXIST

**Finding**: The provider chains in [provider_fallback.py](../torq_console/llm/provider_fallback.py) reference "openai" as a fallback provider:

```python
direct_chain: List[str] = field(default_factory=lambda: ["deepseek", "openai", "claude", "ollama"])
research_chain: List[str] = field(default_factory=lambda: ["claude", "openai", "deepseek", "ollama"])
code_generation_chain: List[str] = field(default_factory=lambda: ["claude", "openai", "deepseek"])
```

**However**:
- No `openai.py` file exists in [torq_console/llm/providers/](../torq_console/llm/providers/)
- No OpenAI provider is imported in [manager.py](../torq_console/llm/manager.py)
- No OpenAI provider is initialized in `LLMManager.__init__()`

**Impact**:

When fallback is enabled and the chain reaches "openai":
1. `self.llm_manager.get_provider("openai")` returns `None`
2. [provider_fallback.py:300](../torq_console/llm/provider_fallback.py#L300) raises `ProviderError("Provider 'openai' not found")`
3. This causes **unnecessary fallback attempts** to a non-existent provider
4. Each attempt to "openai" adds 250ms delay (contract violation delay)

**Recommendation**:

Remove "openai" from all provider chains until an OpenAI provider is implemented:

```python
# Update defaults in provider_fallback.py
direct_chain: List[str] = field(default_factory=lambda: ["deepseek", "claude", "ollama"])
research_chain: List[str] = field(default_factory=lambda: ["claude", "deepseek", "ollama"])
code_generation_chain: List[str] = field(default_factory=lambda: ["claude", "deepseek"])
```

---

## Production Readiness Matrix

| Provider | Contract Compliant | Safe for Fallback | Action Required |
|----------|-------------------|-------------------|-----------------|
| ClaudeProvider | ✅ Yes | ✅ Yes | None |
| DeepSeekProvider | ✅ Yes | ✅ Yes | None |
| OllamaProvider | ❌ No | ❌ No | **Must fix before enabling** |
| GLMProvider | ⚠️ Unknown | ❌ No | Full audit required |
| OpenAIProvider | ❌ N/A | ❌ No | **Remove from chains or implement** |

---

## Vercel Environment Status

As of 2026-02-17 02:48:49 UTC:

```json
{
  "status": "healthy",
  "anthropic_configured": true,  // ✅ ClaudeProvider ready
  "openai_configured": true,      // ⚠️ No OpenAIProvider exists
  "version": "0.80.0"
}
```

**Implications**:
- ✅ ClaudeProvider is fully operational
- ❌ `openai_configured: true` is misleading (no provider to use the key)
- ⚠️ If fallback chains contain "openai", they will fail with "Provider not found"

---

## Recommendations

### Immediate Actions (Before Enabling Fallback)

1. **Fix OllamaProvider** (Required)
   - Remove error string returns (lines 167-174)
   - Import and use typed exceptions
   - Map errors to `ProviderError`, `AITimeoutError`, `AIResponseError`
   - See [ClaudeProvider](../torq_console/llm/providers/claude.py) as reference

2. **Remove "openai" from Provider Chains** (Required)
   - Update [provider_fallback.py](../torq_console/llm/provider_fallback.py) lines 155, 158, 161
   - Remove "openai" from all default chains
   - Or implement OpenAI provider (if needed)

3. **Audit GLMProvider** (Recommended)
   - Full contract compliance review
   - Add typed exception imports
   - Verify error handling paths

### Environment Variable Updates

**Before enabling fallback in Vercel**:

```bash
# Update provider chains to remove "openai"
TORQ_DIRECT_CHAIN=deepseek,claude,ollama
TORQ_RESEARCH_CHAIN=claude,deepseek,ollama
TORQ_CODE_CHAIN=claude,deepseek
```

---

## Conclusion

**Current Status**: ❌ **NOT SAFE TO ENABLE**

**Blockers**:
1. OllamaProvider has critical contract violations
2. Provider chains reference non-existent "openai" provider
3. GLMProvider requires full audit

**Path to Enable**:
1. Fix OllamaProvider contract violations
2. Remove "openai" from provider chains (or implement provider)
3. Audit GLMProvider (or exclude from chains)
4. Run E2E smoke tests with fixed providers
5. Enable `TORQ_FALLBACK_ENABLED=true` in Vercel

**Estimated Effort**: 2-3 hours to fix OllamaProvider + update chains

---

## Appendix: Contract Violation Detection

The fallback system includes contract violation detection in [provider_fallback.py:312-372](../torq_console/llm/provider_fallback.py#L312-L372):

**String Return Detection** (lines 315-353):
```python
if isinstance(response, str):
    # Check for error prefixes
    adapter_error_prefixes = [
        "error:",
        "i apologize, but i encountered an error",
        # ...
    ]
    if any(prefix in response_lower for prefix in adapter_error_prefixes):
        raise ProviderError("Provider adapter contract violation", code="contract_violation")
```

**Dict Return Detection** (lines 355-372):
```python
elif isinstance(response, dict):
    # ANY dict return is a contract violation
    raise ProviderError("Provider adapter contract violation: returned dict", code="contract_violation")
```

**OllamaProvider will trigger both detectors**:
1. Returns dict with `'content': "I apologize..."` → String detector
2. Returns dict instead of str → Dict detector

This will cause unnecessary 250ms delays and incorrect error categorization.

---

**Next Step**: Fix OllamaProvider contract violations before enabling fallback.
