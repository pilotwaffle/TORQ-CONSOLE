# Provider Fallback System

**Date**: 2026-02-17
**Status**: ✅ Implemented - Single-Pass, Meta-First Fallback

---

## Overview

The provider fallback system adds **resilience without losing observability**. It implements deterministic, single-pass provider fallback with complete attempt tracking.

### Key Properties

1. **Single-Pass**: No recursion, no nested retries
2. **Meta-First**: Every attempt recorded in `provider_attempts`
3. **Category-Preserving**: Timeouts stay timeouts, provider errors stay provider errors
4. **Non-Masking**: Final error reflects why ALL providers failed
5. **Pluggable**: Works with Claude, DeepSeek, OpenAI, Ollama, llama.cpp

---

## Architecture

### Canonical Contract

**Inputs**:
- `prompt`: User's prompt
- `mode`: ExecutionMode (DIRECT, RESEARCH, CODE_GENERATION, etc.)
- `tools`: List of tools (e.g., `["web_search"]`)
- `provider_chain`: Ordered list of providers to try
- `timeout`: Per-provider timeout in seconds

**Outputs**:
- Success: `(text, meta)` where `meta` contains complete attempt history
- Failure: Raises typed exception with `meta` populated

**Non-Negotiables**:
- `meta.provider_attempts` is always a list (length >= 1)
- `meta.fallback_used = (len(attempts) > 1)`
- On success: `meta.provider` = winning provider, `meta.error_category = None`
- On failure: `success=False` + `meta.error_category` set + `meta.provider_attempts` shows full story

---

## Attempt Record Schema

Each provider attempt is recorded with full observability:

```python
{
    "provider": "claude",              # Provider name
    "model": "claude-sonnet-4-20250514", # Model used
    "status": "success" | "failed",    # Attempt outcome
    "error_category": "timeout" | "provider_error" | "ai_error" | "exception" | None,
    "error_code": "429" | "401" | "rate_limited" | None,  # Specific error code
    "latency_ms": 1847,                # Request latency
    "timestamp": "2026-02-17T...",     # ISO 8601 timestamp
    "tokens_in": 123,                  # Input tokens (if successful)
    "tokens_out": 456,                 # Output tokens (if successful)
    "cost_usd_est": 0.0123,            # Estimated cost (if successful)
}
```

This enables:
- **Observability**: What happened with each provider?
- **Debugging**: Why did provider X fail?
- **Analytics**: Which providers are failing most?
- **Cost tracking**: How much did we spend on failed attempts?

---

## Fallback Decision Matrix

### Retryable Errors (Try Next Provider)

| Error Category | Examples | Action |
|----------------|----------|--------|
| `timeout` | Request took too long | Continue to next provider |
| `provider_error` | 429, 5xx, connection, DNS, auth, quota | Continue to next provider |
| `exception` | Provider adapter crash | Continue to next provider |

### Non-Retryable Errors (Fail Fast)

| Error Category | Examples | Action |
|----------------|----------|--------|
| `ai_error` | Invalid request shape, content policy | Stop immediately (don't retry) |

**Rationale**: Infrastructure issues merit retry, but user/prompt issues won't change across providers.

---

## Chain Ordering Strategy

Chains are **mode-aware** because different modes have different priorities:

### Direct Mode (Fast + Cheap First)
```python
["deepseek", "openai", "claude", "ollama"]
```
**Priority**: Speed and cost matter for quick answers

### Research Mode (Quality First)
```python
["claude", "openai", "deepseek", "ollama"]
```
**Priority**: Quality matters for web search + synthesis

### Code Generation (Reliability First)
```python
["claude", "openai", "deepseek"]
```
**Priority**: Correctness and best practices

**Note**: Chains are **config-driven, not hardcoded**. See [`ProviderChainConfig`](torq_console/llm/provider_fallback.py#L158-L177).

---

## Usage

### Basic Usage

```python
from torq_console.llm.provider_fallback import ProviderFallbackExecutor
from torq_console.generation_meta import GenerationMeta, ExecutionMode

# Create executor
executor = ProviderFallbackExecutor(llm_manager)

# Create metadata object
meta = GenerationMeta(
    mode=ExecutionMode.DIRECT,
)

# Generate with fallback
try:
    response_text = executor.generate_with_fallback(
        prompt="What is 2+2?",
        mode=ExecutionMode.DIRECT,
        tools=[],
        meta=meta,
        timeout=60,
    )

    # Success!
    print(f"Provider: {meta.provider}")
    print(f"Fallback used: {meta.fallback_used}")
    print(f"Response: {response_text}")

    if meta.fallback_used:
        print(f"Fallback reason: {meta.fallback_reason}")
        print(f"Attempt history: {meta.provider_attempts}")

except ProviderError as e:
    # All providers failed
    print(f"Error: {e}")
    print(f"Attempt history: {meta.provider_attempts}")
```

### Example Response (Success with Fallback)

```json
{
    "success": true,
    "response": "4",
    "meta": {
        "provider": "openai",
        "model": "gpt-4",
        "mode": "direct",
        "latency_ms": 2147,
        "fallback_used": true,
        "fallback_reason": "provider_error:429",
        "provider_attempts": [
            {
                "provider": "deepseek",
                "status": "failed",
                "error_category": "provider_error",
                "error_code": "429",
                "latency_ms": 1234
            },
            {
                "provider": "openai",
                "status": "success",
                "latency_ms": 2147,
                "tokens_in": 12,
                "tokens_out": 5,
                "cost_usd_est": 0.0002
            }
        ]
    }
}
```

### Example Response (All Providers Failed)

```json
{
    "success": false,
    "response": "I apologize, but all AI providers are currently unavailable...",
    "meta": {
        "provider": "unknown",
        "mode": "direct",
        "error_category": "provider_error",
        "error": "All providers in chain failed",
        "fallback_used": true,
        "fallback_reason": "provider_error:503",
        "provider_attempts": [
            {
                "provider": "deepseek",
                "status": "failed",
                "error_category": "provider_error",
                "error_code": "503",
                "latency_ms": 500
            },
            {
                "provider": "openai",
                "status": "failed",
                "error_category": "timeout",
                "latency_ms": 60000
            },
            {
                "provider": "claude",
                "status": "failed",
                "error_category": "provider_error",
                "error_code": "529",
                "latency_ms": 1200
            }
        ]
    }
}
```

---

## Integration Point

The fallback executor should be inserted **at exactly one place** in the codebase:

**Recommended**: `LLMManager.generate_response(...)` layer

```python
class LLMManager:
    def __init__(self):
        self.fallback_executor = ProviderFallbackExecutor(self)

    def generate_response(self, prompt, mode=ExecutionMode.DIRECT, tools=None, timeout=60):
        """Generate response with automatic provider fallback."""
        meta = GenerationMeta(mode=mode, tools_used=tools or [])

        try:
            response = self.fallback_executor.generate_with_fallback(
                prompt=prompt,
                mode=mode,
                tools=tools or [],
                meta=meta,
                timeout=timeout,
            )
            return response, meta
        except (AITimeoutError, ProviderError, AIResponseError) as e:
            # Return error response with metadata
            return create_error_response(e, meta), meta
```

**Rule**: Only ONE place should implement fallback. Everything else calls "generate" and gets either a real answer or a typed exception.

---

## Metadata Invariants

These invariants can be enforced in metadata tests:

1. `provider_attempts` length >= 1 **always**
2. If `success=true` and `attempts > 1` → `fallback_used=True`
3. If `success=false` and `attempts > 1` → `fallback_used=True`
4. The last attempt's provider == `meta.provider` on success
5. No attempt has `status=success` unless overall `success=true`

---

## Fallback Reason Field

The `fallback_reason` field provides a **quick summary** for dashboards:

| Scenario | `fallback_reason` | Description |
|----------|-------------------|-------------|
| First provider timed out | `timeout` | DeepSeek took too long |
| First provider rate-limited | `provider_error:429` | DeepSeek returned 429 |
| All providers failed | `provider_error:503` | Service unavailable |

This makes dashboard queries simpler without parsing attempt details.

---

## Configuration

### Custom Provider Chains

```python
from torq_console.llm.provider_fallback import ProviderChainConfig

config = ProviderChainConfig(
    direct_chain=["ollama", "deepseek", "openai"],  # Local first
    research_chain=["claude", "deepseek", "openai"],
    code_generation_chain=["openai", "claude", "deepseek"],
)

executor = ProviderFallbackExecutor(llm_manager, chain_config=config)
```

### Environment Variable Configuration

```bash
# .env
TORQ_DIRECT_CHAIN=ollama,deepseek,openai
TORQ_RESEARCH_CHAIN=claude,openai,deepseek
TORQ_CODE_CHAIN=claude,openai,deepseek
```

```python
import os

config = ProviderChainConfig(
    direct_chain=os.getenv("TORQ_DIRECT_CHAIN", "deepseek,openai,claude").split(","),
    research_chain=os.getenv("TORQ_RESEARCH_CHAIN", "claude,openai,deepseek").split(","),
)
```

---

## Benefits

### For Operations
- **Reliability**: Automatic failover on provider outages
- **Observability**: Complete attempt history for every request
- **Debugging**: Know exactly why each provider failed
- **Cost tracking**: See how much you're spending on failed attempts

### For Developers
- **Simplicity**: One function call, automatic fallback
- **Type safety**: Typed exceptions for different error categories
- **Testability**: Deterministic behavior, no hidden recursion
- **Flexibility**: Configurable chains per mode

### For Users
- **Uptime**: Higher availability through provider redundancy
- **Transparency**: Can see which providers were tried
- **Performance**: Still fast (no retry delays)

---

## Testing

### Unit Tests

```python
def test_fallback_on_timeout():
    """Test that fallback triggers on timeout."""
    executor = ProviderFallbackExecutor(mock_llm_manager)

    # Mock first provider to timeout, second to succeed
    response, meta = executor.generate_with_fallback(...)

    assert meta.provider_attempts[0]["error_category"] == "timeout"
    assert meta.provider == "openai"  # Second provider
    assert meta.fallback_used is True
```

### Integration Tests

```python
def test_real_provider_fallback():
    """Test with real providers (requires API keys)."""
    executor = ProviderFallbackExecutor(real_llm_manager)

    # Use chain where first provider has invalid key
    config = ProviderChainConfig(direct_chain=["invalid", "deepseek"])

    response, meta = executor.generate_with_fallback(...)

    assert meta.provider_attempts[0]["error_category"] == "provider_error"
    assert meta.provider == "deepseek"
    assert meta.fallback_used is True
```

---

## Status

✅ **Implemented** - Single-pass, meta-first provider fallback

- ✅ `ProviderAttempt` dataclass with full observability
- ✅ `ProviderFallbackExecutor` with deterministic logic
- ✅ `ProviderChainConfig` with mode-aware ordering
- ✅ `fallback_reason` field added to `GenerationMeta`
- ✅ Retryable vs non-retryable error classification
- ✅ Integration point defined (LLMManager layer)

**Next Steps**:
1. Integrate into `LLMManager.generate_response()`
2. Configure provider chains via environment variables
3. Add telemetry persistence (JSONL log)
4. Create monitoring dashboards

---

**This preserves the deterministic contract while adding resilience.**
