# Provider Adapter Normalization Requirements

**Date**: 2026-02-17
**Status**: Required for Provider Fallback System

---

## Critical Requirement: Error Classification Normalization

The provider fallback system relies on **accurate error classification** from provider adapters. If a provider adapter misclassifies a content policy block as `PROVIDER_ERROR`, the fallback system may accidentally retry across providers, attempting to circumvent safety filters.

---

## Provider Adapter Contract

All provider adapters MUST normalize errors as follows:

### HTTP Status Code Mapping

| HTTP Code | Typical Meaning | Error Category | Retryable | Notes |
|-----------|----------------|----------------|-----------|-------|
| 400 | Bad Request | `AI_ERROR` | ❌ No | **IF** message contains "policy", "safety", "content" |
| 400 | Bad Request | `PROVIDER_ERROR` | ✅ Yes | For malformed JSON, invalid params (not policy) |
| 401 | Unauthorized | `PROVIDER_ERROR` | ✅ Yes | Invalid API key |
| 403 | Forbidden | `PROVIDER_ERROR` | ✅ Yes | Quota, permissions |
| 404 | Not Found | `PROVIDER_ERROR` | ✅ Yes | Model not found |
| 429 | Rate Limited | `PROVIDER_ERROR` | ✅ Yes | With bounded delay |
| 500-504 | Server Error | `PROVIDER_ERROR` | ✅ Yes | Service issues |

### Content Policy Detection

**Rule**: If the error response contains ANY of these keywords, classify as `AI_ERROR` (terminal):

```python
CONTENT_POLICY_KEYWORDS = [
    "content policy",
    "safety guidelines",
    "policy violation",
    "inappropriate content",
    "safety filter",
    "against our policies",
    "violates content policy",
]
```

**Implementation Pattern**:

```python
class ClaudeProvider:
    def generate_response(self, prompt, timeout):
        try:
            response = self.api.messages.create(...)
            return response.content
        except APIError as e:
            # Extract status code and message
            status_code = e.status_code
            message = str(e).lower()

            # Check for content policy first
            if any(kw in message for kw in CONTENT_POLICY_KEYWORDS):
                raise AIResponseError(
                    f"Content policy violation: {e}",
                    error_category="ai_error"
                )

            # Map other errors to appropriate category
            if status_code == 429:
                raise ProviderError(f"Rate limited: {e}", code="429")
            elif status_code >= 500:
                raise ProviderError(f"Server error: {e}", code=str(status_code))
            else:
                raise ProviderError(f"Provider error: {e}", code=str(status_code))
```

---

## Provider-Specific Guidance

### Claude (Anthropic)

```python
# Claude error responses to watch for:
- "content policy" → AI_ERROR
- "safety guidelines" → AI_ERROR
- 400 with policy message → AI_ERROR
- 401 → PROVIDER_ERROR
- 429 → PROVIDER_ERROR (with delay)
- 5xx → PROVIDER_ERROR
```

### OpenAI

```python
# OpenAI error responses to watch for:
- "content policy" → AI_ERROR
- "safety" → AI_ERROR
- "moderation" → AI_ERROR
- 400 (policy) → AI_ERROR
- 400 (malformed) → PROVIDER_ERROR
- 401 → PROVIDER_ERROR
- 429 → PROVIDER_ERROR (with delay)
- 5xx → PROVIDER_ERROR
```

### DeepSeek

```python
# DeepSeek error responses to watch for:
- Content safety violations → AI_ERROR
- Policy violations → AI_ERROR
- 401 → PROVIDER_ERROR
- 429 → PROVIDER_ERROR (with delay)
- 5xx → PROVIDER_ERROR
```

---

## Validation Checklist

Before enabling provider fallback, verify each adapter:

- [ ] **ClaudeProvider**: Content policy → `AI_ERROR`
- [ ] **OpenAIProvider**: Content policy → `AI_ERROR`
- [ ] **DeepSeekProvider**: Content safety → `AI_ERROR`
- [ ] **OllamaProvider**: (No policy filtering, all errors retryable)
- [ ] **All adapters**: 401, 403, 429, 5xx → `PROVIDER_ERROR`
- [ ] **All adapters**: Timeouts → `AITimeoutError` with `error_category="timeout"`

---

## Testing Procedure

### Test 1: Content Policy Stops Fallback

```python
def test_content_policy_does_not_trigger_fallback():
    """Ensure policy blocks are terminal (no fallback)."""
    # Mock provider to return content policy error
    provider1 = Mock()
    provider1.generate_response.side_effect = AIResponseError(
        "Content policy violation",
        error_category="ai_error"
    )

    provider2 = Mock()  # Should never be called
    provider2.generate_response.return_value = "Should not see this"

    # Execute fallback
    with pytest.raises(AIResponseError):
        executor.generate_with_fallback(...)

    # Verify only first provider was attempted
    assert len(meta.provider_attempts) == 1
    assert meta.fallback_used is False
```

### Test 2: 429 Triggers Fallback With Delay

```python
def test_429_triggers_fallback_with_delay():
    """Ensure 429 triggers fallback with bounded delay."""
    import time

    provider1 = Mock()
    provider1.generate_response.side_effect = ProviderError("Rate limited", code="429")

    provider2 = Mock()
    provider2.generate_response.return_value = "Success"

    t0 = time.time()
    response = executor.generate_with_fallback(...)
    elapsed_ms = int((time.time() - t0) * 1000)

    # Should have delayed before trying provider2
    assert elapsed_ms >= RATE_LIMIT_DELAY_MS
    assert meta.fallback_reason == "provider_error:429"
```

---

## Consequences of Misclassification

### If Policy Block Misclassified as PROVIDER_ERROR

**What Happens**:
1. Provider A returns content policy error
2. Fallback system treats it as retryable
3. Attempts same prompt on Provider B
4. Provider B also rejects it (same policy)
5. Continues through entire chain
6. Wastes API quota on all providers
7. May trigger rate limiting cascade

**Correct Behavior**:
1. Provider A returns content policy error
2. Fallback system detects `ai_error` category
3. Stops immediately (no fallback)
4. Returns error to user with explanation
5. Preserves API quota

---

## Implementation Status

| Provider | Policy Detection | Status |
|----------|-----------------|--------|
| ClaudeProvider | Needs audit | ⏳ Pending |
| OpenAIProvider | Needs audit | ⏳ Pending |
| DeepSeekProvider | Needs audit | ⏳ Pending |
| OllamaProvider | N/A (local) | ✅ N/A |

---

**This normalization is REQUIRED before enabling provider fallback in production.**
