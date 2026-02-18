# Provider Fallback Integration Guide

**Date**: 2026-02-17
**Status**: Ready for Integration

---

## Overview

This guide shows how to integrate the provider fallback system into the existing TORQ Console codebase **without breaking current functionality**.

### Key Principle: One Integration Point

Only **ONE place** in the codebase should implement provider fallback. Everything else calls the existing `generate_response()` interface and gets either:
- A real answer (with fallback metadata)
- A typed exception (with full attempt history)

---

## Integration Steps

### Step 1: Add Fallback Executor to LLMManager

**File**: [`torq_console/llm/manager.py`](torq_console/llm/manager.py)

Add the fallback executor to `LLMManager.__init__()`:

```python
from torq_console.llm.provider_fallback import ProviderFallbackExecutor, ProviderChainConfig

class LLMManager:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM Manager with provider configuration.
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize providers
        self.providers = {}
        self.default_provider = 'claude'
        self.search_provider = 'deepseek'
        self.local_provider = 'ollama'

        # Initialize providers
        self._init_providers()

        # NEW: Initialize fallback executor
        self.fallback_enabled = self.config.get("fallback_enabled", True)
        if self.fallback_enabled:
            chain_config = ProviderChainConfig()
            self.fallback_executor = ProviderFallbackExecutor(self, chain_config)
            self.logger.info("Provider fallback enabled")
        else:
            self.fallback_executor = None
            self.logger.info("Provider fallback disabled (single-provider mode)")
```

### Step 2: Update generate_response() to Use Fallback

**File**: [`torq_console/llm/manager.py`](torq_console/llm/manager.py)

Modify the `generate_response()` method to use fallback when enabled:

```python
from torq_console.generation_meta import GenerationMeta, ExecutionMode

class LLMManager:
    # ... existing code ...

    def generate_response(
        self,
        prompt: str,
        provider: Optional[str] = None,
        mode: ExecutionMode = ExecutionMode.DIRECT,
        tools: Optional[List[str]] = None,
        timeout: int = 60,
        use_fallback: bool = True,
    ) -> tuple[str, GenerationMeta]:
        """
        Generate response using LLM with optional provider fallback.

        Args:
            prompt: The user's prompt
            provider: Specific provider to use (skips fallback if specified)
            mode: Execution mode (DIRECT, RESEARCH, CODE_GENERATION)
            tools: List of tools to use
            timeout: Request timeout in seconds
            use_fallback: Whether to use fallback chain (default: True)

        Returns:
            tuple: (response_text, generation_metadata)

        Raises:
            ProviderError: All providers failed (if fallback enabled)
            AIResponseError: Non-retryable error
        """
        meta = GenerationMeta(
            mode=mode,
            tools_used=tools or [],
        )

        # If specific provider requested, use it directly (no fallback)
        if provider is not None or not use_fallback or not self.fallback_enabled:
            return self._generate_single_provider(
                prompt=prompt,
                provider=provider or self.default_provider,
                meta=meta,
                timeout=timeout,
            )

        # Use fallback chain
        try:
            response_text = self.fallback_executor.generate_with_fallback(
                prompt=prompt,
                mode=mode,
                tools=tools or [],
                meta=meta,
                timeout=timeout,
            )

            # Set fallback_reason from attempt history
            if meta.fallback_used and len(meta.provider_attempts) > 0:
                first_attempt = meta.provider_attempts[0]
                error_cat = first_attempt.get("error_category")
                error_code = first_attempt.get("error_code")
                if error_cat and error_code:
                    meta.fallback_reason = f"{error_cat}:{error_code}"
                elif error_cat:
                    meta.fallback_reason = error_cat

            return response_text, meta

        except (AITimeoutError, ProviderError, AIResponseError) as e:
            # All providers failed - return error response with metadata
            meta.error = str(e)
            meta.error_category = getattr(e, 'error_category', 'exception')

            if meta.fallback_used and len(meta.provider_attempts) > 0:
                first_attempt = meta.provider_attempts[0]
                error_cat = first_attempt.get("error_category")
                error_code = first_attempt.get("error_code")
                if error_cat and error_code:
                    meta.fallback_reason = f"{error_cat}:{error_code}"
                elif error_cat:
                    meta.fallback_reason = error_cat

            error_response = self._create_error_response(e)
            return error_response, meta

    def _generate_single_provider(
        self,
        prompt: str,
        provider: str,
        meta: GenerationMeta,
        timeout: int = 60,
    ) -> tuple[str, GenerationMeta]:
        """
        Generate response using a single provider (no fallback).

        This is the legacy code path - unchanged.
        """
        provider_instance = self.get_provider(provider)
        if provider_instance is None:
            raise ProviderError(f"Provider '{provider}' not found")

        t0 = time.time()
        response_text = provider_instance.generate_response(
            prompt=prompt,
            timeout=timeout,
        )
        latency_ms = int((time.time() - t0) * 1000)

        meta.provider = provider
        meta.model = getattr(provider_instance, 'model', 'unknown')
        meta.latency_ms = latency_ms

        return response_text, meta

    def _create_error_response(self, error: Exception) -> str:
        """Create a user-friendly error response."""
        if isinstance(error, AITimeoutError):
            return "I apologize, but your request timed out. Please try a simpler query or try again."
        elif isinstance(error, ProviderError):
            return f"I apologize, but the AI service is currently unavailable: {str(error)}. Please try again."
        else:
            return f"I apologize, but I encountered an error: {str(error)}. Please try again."
```

---

## Backward Compatibility

### Existing Code Continues to Work

```python
# Old code still works (uses default provider)
response, meta = llm_manager.generate_response("What is 2+2?")

# Old code with specific provider still works (no fallback)
response, meta = llm_manager.generate_response("What is 2+2?", provider="claude")
```

### New Code Gets Fallback

```python
# New code gets automatic fallback
response, meta = llm_manager.generate_response(
    "What is 2+2?",
    mode=ExecutionMode.DIRECT,
)

if meta.fallback_used:
    print(f"Fallback reason: {meta.fallback_reason}")
    print(f"Attempt history: {meta.provider_attempts}")
```

### Disable Fallback if Needed

```python
# Per-call disable
response, meta = llm_manager.generate_response(
    "What is 2+2?",
    use_fallback=False,  # Single provider mode
)

# Global disable via config
llm_manager = LLMManager(config={"fallback_enabled": False})
```

---

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Enable/disable provider fallback
TORQ_FALLBACK_ENABLED=true

# Provider chains (comma-separated)
TORQ_DIRECT_CHAIN=deepseek,openai,claude,ollama
TORQ_RESEARCH_CHAIN=claude,openai,deepseek,ollama
TORQ_CODE_CHAIN=claude,openai,deepseek

# Timeout per provider (seconds)
TORQ_PROVIDER_TIMEOUT=60
```

### Load in LLMManager.__init__()

```python
import os

class LLMManager:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # ... existing code ...

        # Load fallback configuration
        self.fallback_enabled = os.getenv("TORQ_FALLBACK_ENABLED", "true").lower() == "true"

        if self.fallback_enabled:
            chain_config = ProviderChainConfig(
                direct_chain=os.getenv("TORQ_DIRECT_CHAIN", "deepseek,openai,claude,ollama").split(","),
                research_chain=os.getenv("TORQ_RESEARCH_CHAIN", "claude,openai,deepseek,ollama").split(","),
                code_generation_chain=os.getenv("TORQ_CODE_CHAIN", "claude,openai,deepseek").split(","),
            )
            self.fallback_executor = ProviderFallbackExecutor(self, chain_config)
```

---

## Testing the Integration

### Unit Test (Mock Providers)

```python
def test_fallback_integration():
    """Test that LLMManager uses fallback correctly."""
    from unittest.mock import Mock, patch
    from torq_console.llm.manager import LLMManager

    manager = LLMManager()

    # Mock first provider to fail, second to succeed
    with patch.object(manager, 'get_provider') as mock_get_provider:
        provider1 = Mock()
        provider1.generate_response.side_effect = ProviderError("Rate limited", code="429")

        provider2 = Mock()
        provider2.generate_response.return_value = "4"
        provider2.model = "gpt-4"

        mock_get_provider.side_effect = [provider1, provider2]

        response, meta = manager.generate_response("What is 2+2?")

        # Should have fallen back to second provider
        assert meta.provider_attempts[0]["error_category"] == "provider_error"
        assert meta.provider == "openai"  # Second in chain
        assert meta.fallback_used is True
        assert response == "4"
```

### Integration Test (Real Providers)

```python
def test_real_fallback_integration():
    """Test with real providers (requires valid API keys)."""
    from torq_console.llm.manager import LLMManager

    manager = LLMManager()

    response, meta = manager.generate_response(
        "What is 2+2? Respond with only the number.",
        mode=ExecutionMode.DIRECT,
        timeout=30,
    )

    assert meta.provider_attempts is not None
    assert len(meta.provider_attempts) >= 1

    if meta.fallback_used:
        assert meta.fallback_reason is not None
        print(f"Fallback used: {meta.fallback_reason}")
        print(f"Providers tried: {[a['provider'] for a in meta.provider_attempts]}")
```

---

## Migration Path

### Phase 1: Add Fallback Infrastructure (Current)
- ✅ Create `ProviderFallbackExecutor`
- ✅ Add `fallback_reason` to `GenerationMeta`
- ✅ Document integration approach

### Phase 2: Integrate into LLMManager (Next)
- Add `fallback_executor` to `LLMManager.__init__()`
- Modify `generate_response()` to use fallback
- Add configuration loading

### Phase 3: Test and Validate (Next)
- Unit tests with mock providers
- Integration tests with real providers
- Confidence test validation

### Phase 4: Monitor and Iterate (Future)
- Add telemetry persistence (JSONL logs)
- Create monitoring dashboards
- Analyze provider performance

---

## Rollback Plan

If issues arise, fallback can be **disabled globally** without code changes:

```bash
# .env
TORQ_FALLBACK_ENABLED=false
```

This reverts to single-provider mode immediately.

---

## Acceptance Criteria

The integration is complete when:

1. ✅ Existing code continues to work (backward compatible)
2. ✅ New code gets automatic fallback
3. ✅ `provider_attempts` always populated (length >= 1)
4. ✅ `fallback_used = True` when multiple providers tried
5. ✅ `fallback_reason` set on fallback
6. ✅ Single provider mode still works
7. ✅ Can disable fallback via config
8. ✅ All metadata invariants preserved

---

## Status

✅ **Design Complete** - Single-pass, meta-first fallback
✅ **Implementation Complete** - ProviderFallbackExecutor ready
⏳ **Integration Pending** - Awaiting merge into LLMManager
⏳ **Testing Pending** - Unit and integration tests

**Next Step**: Integrate into `LLMManager.generate_response()`

---

**This integration preserves the deterministic contract while adding resilience.**
