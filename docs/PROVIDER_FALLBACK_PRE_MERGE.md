# Provider Fallback System - Pre-Merge Checklist

**Date**: 2026-02-17
**Status**: ✅ Implementation Complete - Awaiting Integration

---

## Production Review Summary

Your design has been stress-tested for the two critical failure modes:

| Failure Mode | Risk Level | Mitigation | Status |
|--------------|------------|------------|--------|
| Accidental fallback on policy blocks | HIGH | Provider adapters normalize policy → AI_ERROR | ⚠️ Requires audit |
| Retry storms on 429 | MEDIUM | Bounded delay (250ms) on 429 | ✅ Implemented |

---

## Three Critical Fixes Implemented

### Fix 1: Bounded Delay for 429 ✅

**File**: [`torq_console/llm/provider_fallback.py:13`](torq_console/llm/provider_fallback.py#L13)

```python
# Constants for fallback behavior
RATE_LIMIT_DELAY_MS = 250  # Small bounded delay for 429 to prevent cascade
```

**Applied in**: ProviderError exception handler

```python
except ProviderError as e:
    # Record attempt...
    meta.provider_attempts.append(attempt.to_dict())

    # Small bounded delay for 429 to prevent cascade across providers
    if attempt.error_code == "429":
        time.sleep(RATE_LIMIT_DELAY_MS / 1000.0)

    # Continue to next provider
```

**Effect**:
- Prevents instantaneous cascade across providers under load
- No exponential backoff complexity (yet)
- Small, bounded delay (250ms) won't impact latency significantly

---

### Fix 2: Prompt Immutability Safeguard ✅

**File**: [`torq_console/llm/provider_fallback.py:265-293`](torq_console/llm/provider_fallback.py#L265-L293)

```python
def generate_with_fallback(self, prompt: str, ...):
    """
    Important:
        - `prompt` is NEVER mutated inside this method
        - All providers receive the same base_prompt
        - Only tool results are injected (not accumulated)
    """
    # Store original prompt (NEVER mutate this variable)
    base_prompt = prompt

    # Single pass through provider chain
    for provider_name in provider_chain:
        # Use base_prompt for every provider (no accumulation)
        # IMPORTANT: Never use the parameter `prompt` here - it must remain immutable
        current_prompt = base_prompt

        # Generate response
        response = provider.generate_response(
            prompt=current_prompt,  # Always use fresh copy from base_prompt
            timeout=timeout,
        )
```

**Effect**:
- Guarantees every provider gets identical input
- Prevents cumulative mutations across fallback attempts
- Maintains determinism across provider chain

---

### Fix 3: Provider Adapter Normalization Requirements ⚠️

**File**: [`docs/PROVIDER_ADAPTER_NORMALIZATION.md`](docs/PROVIDER_ADAPTER_NORMALIZATION.md)

**Requirement**: All provider adapters MUST normalize errors correctly:

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

# In provider adapter
except APIError as e:
    message = str(e).lower()

    # Check for content policy FIRST
    if any(kw in message for kw in CONTENT_POLICY_KEYWORDS):
        raise AIResponseError(
            f"Content policy violation: {e}",
            error_category="ai_error"  # Terminal - no fallback
        )

    # Then map other errors
    if e.status_code == 429:
        raise ProviderError(f"Rate limited: {e}", code="429")  # Retryable
```

**Audit Required**:

| Provider | Status | Action |
|----------|--------|--------|
| ClaudeProvider | ⚠️ Needs audit | Verify policy → AI_ERROR |
| OpenAIProvider | ⚠️ Needs audit | Verify moderation → AI_ERROR |
| DeepSeekProvider | ⚠️ Needs audit | Verify safety → AI_ERROR |
| OllamaProvider | ✅ N/A | Local provider, no policy |

**Consequence of Misclassification**:
- Policy block classified as `PROVIDER_ERROR` → Falls back through entire chain
- Wastes API quota on all providers
- May trigger rate limiting cascade
- Circumvents safety filters (UNACCEPTABLE)

---

## Additional Safeguards

### Latency Recording on All Paths ✅

Every attempt records `latency_ms`, even failed ones:

```python
except AITimeoutError as e:
    # Still record latency even though it timed out
    attempt.latency_ms = int((time.time() - t0) * 1000)
    attempt.error_category = ErrorCategory.TIMEOUT

except ProviderError as e:
    # Record latency up to failure point
    attempt.latency_ms = int((time.time() - t0) * 1000)
    attempt.error_category = ErrorCategory.PROVIDER_ERROR
```

**Benefit**: Accurate SLA analytics (know which providers are slow before failing)

---

## Invariants Enforced

1. ✅ `provider_attempts` length >= 1 **always**
2. ✅ `fallback_used = (len(attempts) > 1)`
3. ✅ `prompt` parameter never mutated
4. ✅ All providers receive same `base_prompt`
5. ✅ `latency_ms` recorded for ALL attempts (success and failure)
6. ✅ `fallback_reason` deterministic (first failure or `all_failed:` prefix)
7. ✅ 429 → 250ms delay before next provider
8. ✅ AI_ERROR → stops immediately (no fallback)

---

## Pre-Merge Validation Checklist

### Code Review

- [x] Single-pass logic (no recursion)
- [x] Meta-first (all attempts recorded)
- [x] Category-preserving (timeouts stay timeouts)
- [x] Non-masking (final error reflects actual failure)
- [x] Thread-safe (no mutable instance state)
- [x] Prompt immutability safeguard
- [x] 429 bounded delay implemented
- [x] Latency recording on all paths

### Documentation

- [x] Provider fallback design documented
- [x] Integration guide created
- [x] Provider adapter normalization requirements documented
- [x] Pre-merge checklist created

### Testing

- [ ] Unit tests with mock providers (template provided)
- [ ] Integration tests with real providers
- [ ] Content policy fallback test (verify stops immediately)
- [ ] 429 delay test (verify bounded delay)
- [ ] Prompt immutability test (verify no accumulation)

### Provider Adapter Audit

- [ ] ClaudeProvider: Map policy blocks to AI_ERROR
- [ ] OpenAIProvider: Map moderation blocks to AI_ERROR
- [ ] DeepSeekProvider: Map safety blocks to AI_ERROR
- [ ] All providers: Map 401, 403, 429, 5xx to PROVIDER_ERROR

---

## Merge Strategy

### Phase 1: Behind Feature Flag (Recommended)

```bash
# .env
TORQ_FALLBACK_ENABLED=false  # Start disabled
```

**Benefits**:
- Zero risk to existing users
- Can enable selectively for testing
- Instant rollback if issues found

### Phase 2: Enable for DIRECT Mode Only

```python
# In LLMManager
if mode == ExecutionMode.DIRECT and fallback_enabled:
    return fallback_executor.generate_with_fallback(...)
else:
    return _generate_single_provider(...)
```

**Benefits**:
- Tests fallback on low-complexity queries first
- Research mode still uses single provider (more complex)
- Can validate behavior incrementally

### Phase 3: Enable for RESEARCH Mode

After validation in DIRECT mode.

### Phase 4: Enable for All Modes

Production rollout.

---

## What Happens After Merge

### Immediate Benefits

1. **Reliability**: Automatic failover on provider outages
2. **Observability**: Complete attempt history in metadata
3. **Cost Tracking**: See spend on failed attempts
4. **Debugging**: Know exactly why each provider failed

### Next Evolution (Future)

1. **Circuit Breaker**: Temporarily disable failing providers
2. **Adaptive Routing**: Route based on historical latency
3. **Telemetry Persistence**: JSONL logs for analytics
4. **SLA Monitoring**: Dashboards for provider performance

---

## Final Assessment

### Architecture: ✅ Production-Grade

| Property | Status | Notes |
|----------|--------|-------|
| Deterministic | ✅ Yes | Single-pass, no recursion |
| Observable | ✅ Yes | All attempts recorded |
| Type-safe | ✅ Yes | Typed exception hierarchy |
| Thread-safe | ✅ Yes | No mutable instance state |
| Backward-compatible | ✅ Yes | Feature flag + per-call disable |
| Policy-aware | ⚠️ Needs audit | Provider adapters must normalize correctly |

### Risk Level: MEDIUM

**Acceptable Risk**:
- 429 cascade prevented (bounded delay)
- Prompt accumulation prevented (immutability safeguard)
- Recursion prevented (single-pass design)

**Requires Audit**:
- Provider adapter error classification
- Content policy detection logic

**Recommendation**: Merge behind feature flag, audit provider adapters, then enable incrementally.

---

## Approval Sign-Off

| Checklist | Approved By | Date |
|-----------|-------------|------|
| Code review (fallback logic) | | |
| Code review (429 delay) | | |
| Code review (prompt immutability) | | |
| Provider adapter audit (Claude) | | |
| Provider adapter audit (OpenAI) | | |
| Provider adapter audit (DeepSeek) | | |
| Integration testing | | |
| Production readiness | | |

---

**Ready for integration once provider adapter audit is complete.**

The fallback system is architecturally sound. The remaining work is verifying that provider adapters correctly classify policy blocks as terminal (AI_ERROR) rather than retryable (PROVIDER_ERROR).
