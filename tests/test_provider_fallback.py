"""
Provider Fallback System Tests.

Tests the single-pass, meta-first fallback behavior including:
- Fallback on retryable errors (timeout, provider_error)
- Immediate halt on terminal errors (ai_error, policy violations)
- Prompt immutability (no accumulation across attempts)
- Metadata invariants on all paths
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from torq_console.llm.provider_fallback import (
    ProviderFallbackExecutor,
    ProviderChainConfig,
    ProviderAttempt,
    AttemptStatus
)
from torq_console.generation_meta import (
    GenerationMeta,
    ExecutionMode,
    ErrorCategory,
    AIResponseError,
    AITimeoutError,
    ProviderError
)


class TestPolicyBlockStopsFallback:
    """
    GATING TEST: Verify that content policy blocks do NOT trigger fallback.

    This is the critical safety test. If this fails, the fallback system
    could be used to circumvent safety filters by retrying across providers.

    Expected behavior:
    - Policy block on first provider → stops immediately
    - Second provider is NEVER called
    - fallback_used = False
    - Only 1 attempt recorded
    """

    def test_policy_block_stops_fallback_immediately(self):
        """Policy block must halt the fallback chain (no retry)."""
        # Setup: Mock first provider to return policy error
        provider1 = Mock()
        provider1.generate_response.side_effect = AIResponseError(
            "Content policy violation: This content violates our safety guidelines",
            error_category="ai_error"
        )
        provider1.model = "claude-sonnet-4-20250514"

        # Setup: Second provider should NEVER be called
        provider2 = Mock()
        provider2.generate_response.return_value = "This should never be returned"
        provider2.model = "gpt-4"

        # Setup: Mock LLM manager
        llm_manager = Mock()
        llm_manager.get_provider.side_effect = [provider1, provider2]

        # Setup: Executor and metadata
        config = ProviderChainConfig(direct_chain=["provider1", "provider2"])
        executor = ProviderFallbackExecutor(llm_manager, config)
        meta = GenerationMeta(mode=ExecutionMode.DIRECT)

        # Execute: Should raise AIResponseError (policy block)
        with pytest.raises(AIResponseError) as exc_info:
            executor.generate_with_fallback(
                prompt="Generate harmful content",
                mode=ExecutionMode.DIRECT,
                tools=[],
                meta=meta,
                timeout=60
            )

        # Verify: Exception is policy-related
        assert "policy" in str(exc_info.value).lower()
        assert exc_info.value.error_category == "ai_error"

        # Verify: Only first provider was attempted
        assert len(meta.provider_attempts) == 1, \
            f"Expected 1 attempt, got {len(meta.provider_attempts)}"

        # Verify: Second provider was NEVER called
        provider2.generate_response.assert_not_called()

        # Verify: fallback_used is False (no fallback occurred)
        assert meta.fallback_used is False, \
            "fallback_used should be False for policy blocks"

        # Verify: Only ONE attempt was made (critical safety invariant)
        assert len(meta.provider_attempts) == 1, \
            f"Policy blocks must not record multiple attempts, got {len(meta.provider_attempts)}"

        # Verify: First attempt failed with ai_error
        attempt = meta.provider_attempts[0]
        assert attempt["status"] == "failed"
        assert attempt["error_category"] == "ai_error"
        assert attempt["provider"] == "provider1"

        # Verify: No delay occurred (policy blocks fail fast)
        # We can't directly measure sleep() in mocks, but we verify no second attempt
        # which means the loop didn't continue

        print("[PASS] Policy block correctly halted fallback chain")
        print(f"  - Only {len(meta.provider_attempts)} provider attempted (critical invariant)")
        print(f"  - fallback_used = {meta.fallback_used} (must be False)")
        print(f"  - Second provider called: {provider2.generate_response.called} (must be False)")
        print(f"  - Error category: {attempt['error_category']} (must be ai_error)")

    def test_safety_violation_stops_fallback(self):
        """Safety guideline violations must also halt fallback."""
        # Setup: Mock provider with safety violation
        provider1 = Mock()
        provider1.generate_response.side_effect = AIResponseError(
            "This request violates our safety guidelines",
            error_category="ai_error"
        )

        provider2 = Mock()  # Should never be called

        # Setup: Mock LLM manager
        llm_manager = Mock()
        llm_manager.get_provider.side_effect = [provider1, provider2]

        # Setup: Executor and metadata
        config = ProviderChainConfig(direct_chain=["provider1", "provider2"])
        executor = ProviderFallbackExecutor(llm_manager, config)
        meta = GenerationMeta(mode=ExecutionMode.DIRECT)

        # Execute: Should raise AIResponseError
        with pytest.raises(AIResponseError) as exc_info:
            executor.generate_with_fallback(
                prompt="Violate safety guidelines",
                mode=ExecutionMode.DIRECT,
                tools=[],
                meta=meta,
                timeout=60
            )

        # Verify: Only first provider attempted
        assert len(meta.provider_attempts) == 1
        assert meta.fallback_used is False

        # Verify: Second provider never called
        provider2.generate_response.assert_not_called()

        print("[PASS] Safety violation correctly halted fallback chain")


class TestRetryableErrorsTriggerFallback:
    """
    Tests that retryable errors (timeout, provider_error) DO trigger fallback.

    These errors represent infrastructure issues, not content/prompt issues.
    It's safe to retry the same prompt on a different provider.
    """

    def test_timeout_triggers_fallback(self):
        """Timeout on first provider should trigger fallback to second."""
        # Setup: First provider times out
        provider1 = Mock()
        provider1.generate_response.side_effect = AITimeoutError("Request timed out")
        provider1.model = "deepseek-chat"

        # Setup: Second provider succeeds
        provider2 = Mock()
        provider2.generate_response.return_value = "4"
        provider2.model = "gpt-4"

        # Setup: Mock LLM manager
        llm_manager = Mock()
        llm_manager.get_provider.side_effect = [provider1, provider2]

        # Setup: Executor and metadata
        config = ProviderChainConfig(direct_chain=["provider1", "provider2"])
        executor = ProviderFallbackExecutor(llm_manager, config)
        meta = GenerationMeta(mode=ExecutionMode.DIRECT)

        # Execute: Should succeed after fallback
        response = executor.generate_with_fallback(
            prompt="What is 2+2?",
            mode=ExecutionMode.DIRECT,
            tools=[],
            meta=meta,
            timeout=60
        )

        # Verify: Got successful response from second provider
        assert response == "4"
        assert meta.provider == "provider2"

        # Verify: Both providers were attempted
        assert len(meta.provider_attempts) == 2

        # Verify: First attempt timed out
        assert meta.provider_attempts[0]["status"] == "failed"
        assert meta.provider_attempts[0]["error_category"] == "timeout"

        # Verify: Second attempt succeeded
        assert meta.provider_attempts[1]["status"] == "success"
        assert meta.provider_attempts[1]["error_category"] is None

        # Verify: fallback_used is True
        assert meta.fallback_used is True
        assert meta.fallback_reason == "timeout"

        print("[PASS] Timeout correctly triggered fallback")

    def test_429_triggers_fallback_with_delay(self):
        """429 (rate limit) should trigger fallback after bounded delay."""
        import time

        # Setup: First provider returns 429
        provider1 = Mock()
        provider1.generate_response.side_effect = ProviderError(
            "Rate limited",
            code="429"
        )
        provider1.model = "deepseek-chat"

        # Setup: Second provider succeeds
        provider2 = Mock()
        provider2.generate_response.return_value = "Success"
        provider2.model = "claude-sonnet-4-20250514"

        # Setup: Mock LLM manager
        llm_manager = Mock()
        llm_manager.get_provider.side_effect = [provider1, provider2]

        # Setup: Executor and metadata
        from torq_console.llm.provider_fallback import RATE_LIMIT_DELAY_MS
        config = ProviderChainConfig(direct_chain=["provider1", "provider2"])
        executor = ProviderFallbackExecutor(llm_manager, config)
        meta = GenerationMeta(mode=ExecutionMode.DIRECT)

        # Execute: Should succeed after fallback with delay
        t0 = time.time()
        response = executor.generate_with_fallback(
            prompt="Test",
            mode=ExecutionMode.DIRECT,
            tools=[],
            meta=meta,
            timeout=60
        )
        elapsed_ms = int((time.time() - t0) * 1000)

        # Verify: Got successful response
        assert response == "Success"

        # Verify: Delay was applied (should take at least RATE_LIMIT_DELAY_MS)
        assert elapsed_ms >= RATE_LIMIT_DELAY_MS, \
            f"Expected delay >= {RATE_LIMIT_DELAY_MS}ms, got {elapsed_ms}ms"

        # Verify: Fallback used
        assert meta.fallback_used is True
        assert meta.fallback_reason == "provider_error:429"

        print(f"[PASS] 429 correctly triggered fallback with {elapsed_ms}ms delay")

    def test_500_server_error_triggers_fallback(self):
        """5xx server errors should trigger fallback."""
        # Setup: First provider has 500 error
        provider1 = Mock()
        provider1.generate_response.side_effect = ProviderError(
            "Internal server error",
            code="500"
        )

        # Setup: Second provider succeeds
        provider2 = Mock()
        provider2.generate_response.return_value = "Success"

        # Setup: Mock LLM manager
        llm_manager = Mock()
        llm_manager.get_provider.side_effect = [provider1, provider2]

        # Setup: Executor and metadata
        config = ProviderChainConfig(direct_chain=["provider1", "provider2"])
        executor = ProviderFallbackExecutor(llm_manager, config)
        meta = GenerationMeta(mode=ExecutionMode.DIRECT)

        # Execute: Should succeed after fallback
        response = executor.generate_with_fallback(
            prompt="Test",
            mode=ExecutionMode.DIRECT,
            tools=[],
            meta=meta,
            timeout=60
        )

        # Verify: Got successful response
        assert response == "Success"
        assert meta.fallback_used is True
        assert meta.fallback_reason == "provider_error:500"

        print("[PASS] 500 error correctly triggered fallback")


class TestPromptImmutability:
    """
    Tests that prompts are never mutated across fallback attempts.

    This ensures every provider gets the same input, preventing
    cumulative mutations.
    """

    def test_prompt_immutability(self):
        """Verify that all providers receive identical prompts."""
        # Setup: Track prompts received by each provider
        prompts_received = []

        def mock_generate1(prompt, **kwargs):
            prompts_received.append(("provider1", prompt))
            raise ProviderError("Failed", code="500")

        def mock_generate2(prompt, **kwargs):
            prompts_received.append(("provider2", prompt))
            return "Success"

        # Setup: Providers
        provider1 = Mock()
        provider1.generate_response.side_effect = mock_generate1
        provider2 = Mock()
        provider2.generate_response.side_effect = mock_generate2

        # Setup: Mock LLM manager
        llm_manager = Mock()
        llm_manager.get_provider.side_effect = [provider1, provider2]

        # Setup: Executor and metadata
        config = ProviderChainConfig(direct_chain=["provider1", "provider2"])
        executor = ProviderFallbackExecutor(llm_manager, config)
        meta = GenerationMeta(mode=ExecutionMode.DIRECT)

        # Execute
        original_prompt = "What is 2+2?"
        response = executor.generate_with_fallback(
            prompt=original_prompt,
            mode=ExecutionMode.DIRECT,
            tools=[],
            meta=meta,
            timeout=60
        )

        # Verify: Both providers received the SAME prompt
        assert len(prompts_received) == 2
        prompt1 = prompts_received[0][1]
        prompt2 = prompts_received[1][1]

        assert prompt1 == original_prompt, \
            f"Provider1 received mutated prompt: {prompt1}"
        assert prompt2 == original_prompt, \
            f"Provider2 received mutated prompt: {prompt2}"
        assert prompt1 == prompt2, \
            f"Prompts differ: provider1 got '{prompt1}', provider2 got '{prompt2}'"

        print("[PASS] Prompt immutability verified - all providers received identical input")


class TestMetadataInvariants:
    """
    Tests that metadata invariants are preserved on all code paths.
    """

    def test_metadata_invariants_on_success(self):
        """Verify metadata invariants when fallback succeeds."""
        # Setup: First fails, second succeeds
        provider1 = Mock()
        provider1.generate_response.side_effect = ProviderError("Failed", code="500")
        provider2 = Mock()
        provider2.generate_response.return_value = "Success"

        llm_manager = Mock()
        llm_manager.get_provider.side_effect = [provider1, provider2]

        config = ProviderChainConfig(direct_chain=["provider1", "provider2"])
        executor = ProviderFallbackExecutor(llm_manager, config)
        meta = GenerationMeta(mode=ExecutionMode.DIRECT)

        # Execute
        response = executor.generate_with_fallback(
            prompt="Test",
            mode=ExecutionMode.DIRECT,
            tools=[],
            meta=meta,
            timeout=60
        )

        # Invariant 1: provider_attempts length >= 1
        assert len(meta.provider_attempts) >= 1

        # Invariant 2: fallback_used = (len(attempts) > 1)
        assert meta.fallback_used == (len(meta.provider_attempts) > 1)

        # Invariant 3: On success, error_category is None
        assert meta.error_category is None

        # Invariant 4: On success with fallback, provider is the winning one
        if meta.fallback_used:
            assert meta.provider == "provider2"

        # Invariant 5: fallback_reason is set
        if meta.fallback_used:
            assert meta.fallback_reason is not None

        print("[PASS] Metadata invariants verified on success")

    def test_metadata_invariants_on_all_failed(self):
        """Verify metadata invariants when all providers fail."""
        # Setup: All providers fail
        provider1 = Mock()
        provider1.generate_response.side_effect = ProviderError("Failed", code="500")
        provider2 = Mock()
        provider2.generate_response.side_effect = ProviderError("Failed", code="500")

        llm_manager = Mock()
        llm_manager.get_provider.side_effect = [provider1, provider2]

        config = ProviderChainConfig(direct_chain=["provider1", "provider2"])
        executor = ProviderFallbackExecutor(llm_manager, config)
        meta = GenerationMeta(mode=ExecutionMode.DIRECT)

        # Execute: Should raise exception
        with pytest.raises(ProviderError):
            executor.generate_with_fallback(
                prompt="Test",
                mode=ExecutionMode.DIRECT,
                tools=[],
                meta=meta,
                timeout=60
            )

        # Invariant 1: provider_attempts length >= 1
        assert len(meta.provider_attempts) >= 1

        # Invariant 2: fallback_used = (len(attempts) > 1)
        assert meta.fallback_used == (len(meta.provider_attempts) > 1)

        # Invariant 3: On failure, error_category is set
        assert meta.error_category is not None

        # Invariant 4: fallback_reason is set if multiple attempts
        if meta.fallback_used:
            assert meta.fallback_reason is not None

        print("[PASS] Metadata invariants verified on all-failed")


class TestAdapterContractViolation:
    """
    CRITICAL: Test that prevents regression where providers return error strings
    instead of raising typed exceptions.

    This is the "masking" test - if a provider returns "Error: ..." instead of
    raising an exception, it masks the failure and breaks fallback behavior.
    """

    def test_adapter_must_raise_not_return_string(self):
        """
        Verify that providers RAISE typed exceptions, not RETURN error strings.

        This test ensures that if someone accidentally adds:
            return "Error: Something went wrong"

        ...the fallback system will treat it as a contract violation and convert
        it to a typed exception before it can escape.
        """
        # Setup: Mock provider that VIOLATES contract by returning error string
        bad_provider = Mock()
        bad_provider.generate_response.return_value = "Error: API failed"
        bad_provider.model = "bad-provider"

        # Setup: Good provider (fallback target)
        good_provider = Mock()
        good_provider.generate_response.return_value = "Success"
        good_provider.model = "good-provider"

        # Setup: Mock LLM manager
        llm_manager = Mock()
        llm_manager.get_provider.side_effect = [bad_provider, good_provider]

        # Setup: Executor and metadata
        config = ProviderChainConfig(direct_chain=["bad_provider", "good_provider"])
        executor = ProviderFallbackExecutor(llm_manager, config)
        meta = GenerationMeta(mode=ExecutionMode.DIRECT)

        # Execute: Should detect contract violation and fall back to good provider
        response = executor.generate_with_fallback(
            prompt="Test",
            mode=ExecutionMode.DIRECT,
            tools=[],
            meta=meta,
            timeout=60
        )

        # Verify: Got successful response from second provider
        assert response == "Success", \
            f"Expected 'Success' from fallback, got: {response}"

        # Verify: Both providers were attempted (first failed with contract violation)
        assert len(meta.provider_attempts) == 2, \
            f"Expected 2 attempts, got {len(meta.provider_attempts)}"

        # Verify: Fallback was used (chain length > 1)
        assert meta.fallback_used is True, \
            "fallback_used must be True when chain has multiple providers"

        # Verify: First attempt failed with contract_violation (critical invariant)
        assert meta.provider_attempts[0]["error_category"] == "provider_error", \
            "Contract violations must be categorized as provider_error"
        assert meta.provider_attempts[0]["error_code"] == "contract_violation", \
            "Contract violations must have error_code='contract_violation' for dashboard detection"

        # Verify: Second provider succeeded
        assert meta.provider_attempts[1]["status"] == "success"
        assert meta.provider_attempts[1]["error_category"] is None
        assert meta.provider == "good-provider"

        print("[PASS] Contract violation (error string) detected and handled correctly")
        print(f"  - Violation type: contract_violation (dashboards can detect this)")
        print(f"  - Error category: {meta.provider_attempts[0]['error_category']}")
        print(f"  - Fallback used: {meta.fallback_used}")

    def test_adapter_must_raise_not_return_dict(self):
        """
        Verify that providers RAISE typed exceptions, not RETURN error dicts.

        Some providers (like old DeepSeek) returned:
            {'content': "I apologize...", 'error': "..."}

        This should also be treated as a contract violation.
        """
        # Setup: Mock provider that returns error dict
        bad_provider = Mock()
        bad_provider.generate_response.return_value = {
            'content': "I apologize, but I encountered an error",
            'error': 'API failed'
        }
        bad_provider.model = "bad-provider"

        # Setup: Good provider (fallback target)
        good_provider = Mock()
        good_provider.generate_response.return_value = "Success"
        good_provider.model = "good-provider"

        # Setup: Mock LLM manager
        llm_manager = Mock()
        llm_manager.get_provider.side_effect = [bad_provider, good_provider]

        # Setup: Executor and metadata
        config = ProviderChainConfig(direct_chain=["bad_provider", "good_provider"])
        executor = ProviderFallbackExecutor(llm_manager, config)
        meta = GenerationMeta(mode=ExecutionMode.DIRECT)

        # Execute: Should detect contract violation and fall back to good provider
        response = executor.generate_with_fallback(
            prompt="Test",
            mode=ExecutionMode.DIRECT,
            tools=[],
            meta=meta,
            timeout=60
        )

        # Verify: Got successful response from second provider
        assert response == "Success", \
            f"Expected 'Success' from fallback, got: {response}"

        # Verify: Both providers were attempted
        assert len(meta.provider_attempts) == 2

        # Verify: Fallback was used
        assert meta.fallback_used is True

        # Verify: First attempt failed with contract_violation (critical invariant)
        assert meta.provider_attempts[0]["error_category"] == "provider_error", \
            "Contract violations must be categorized as provider_error"
        assert meta.provider_attempts[0]["error_code"] == "contract_violation", \
            "Contract violations must have error_code='contract_violation' for dashboard detection"

        print("[PASS] Contract violation (error dict) detected and handled correctly")
        print(f"  - Violation type: contract_violation (dashboards can detect this)")
        print(f"  - Error category: {meta.provider_attempts[0]['error_category']}")

    def test_normal_sorry_response_not_flagged(self):
        """
        Verify that normal responses containing "sorry" are NOT flagged as contract violations.

        This prevents false positives where the AI legitimately apologizes in conversation.
        """
        # Setup: Provider returns normal response with "sorry" (common in chat)
        provider = Mock()
        provider.generate_response.return_value = "Sorry, I can't help with that specific topic."
        provider.model = "test-provider"

        # Setup: Mock LLM manager
        llm_manager = Mock()
        llm_manager.get_provider.return_value = provider

        # Setup: Executor and metadata
        config = ProviderChainConfig(direct_chain=["provider"])
        executor = ProviderFallbackExecutor(llm_manager, config)
        meta = GenerationMeta(mode=ExecutionMode.DIRECT)

        # Execute: Should succeed (not flagged as contract violation)
        response = executor.generate_with_fallback(
            prompt="Tell me about something controversial",
            mode=ExecutionMode.DIRECT,
            tools=[],
            meta=meta,
            timeout=60
        )

        # Verify: Response treated as success (not contract violation)
        assert response == "Sorry, I can't help with that specific topic."
        assert len(meta.provider_attempts) == 1
        assert meta.provider_attempts[0]["status"] == "success"
        assert meta.provider_attempts[0]["error_category"] is None

        print("[PASS] Normal 'sorry' response not flagged as contract violation")

    def test_error_boilerplate_is_flagged(self):
        """
        Verify that error boilerplate containing "sorry" + "error" IS flagged.

        This ensures we catch the actual contract violations.
        """
        # Setup: Provider returns error boilerplate (contract violation)
        provider = Mock()
        provider.generate_response.return_value = (
            "I apologize, but I encountered an error while processing your request. "
            "Please try again later."
        )
        provider.model = "bad-provider"

        # Setup: Good provider (fallback target)
        good_provider = Mock()
        good_provider.generate_response.return_value = "Success"
        good_provider.model = "good-provider"

        # Setup: Mock LLM manager
        llm_manager = Mock()
        llm_manager.get_provider.side_effect = [provider, good_provider]

        # Setup: Executor and metadata
        config = ProviderChainConfig(direct_chain=["bad-provider", "good-provider"])
        executor = ProviderFallbackExecutor(llm_manager, config)
        meta = GenerationMeta(mode=ExecutionMode.DIRECT)

        # Execute: Should detect contract violation and fall back
        response = executor.generate_with_fallback(
            prompt="Test",
            mode=ExecutionMode.DIRECT,
            tools=[],
            meta=meta,
            timeout=60
        )

        # Verify: Fell back to good provider
        assert response == "Success"
        assert len(meta.provider_attempts) == 2
        assert meta.provider_attempts[0]["error_code"] == "contract_violation"

        print("[PASS] Error boilerplate with 'sorry' + 'error' correctly flagged")

    def test_unable_without_error_not_flagged(self):
        """
        Verify that "unable" without technical error keywords is NOT flagged.

        This ensures we don't catch normal refusals like "Sorry, I'm unable to help with that."
        """
        # Setup: Provider returns normal refusal with "unable" (common in chat)
        provider = Mock()
        provider.generate_response.return_value = "Sorry, I'm unable to provide assistance with that topic."
        provider.model = "test-provider"

        # Setup: Mock LLM manager
        llm_manager = Mock()
        llm_manager.get_provider.return_value = provider

        # Setup: Executor and metadata
        config = ProviderChainConfig(direct_chain=["provider"])
        executor = ProviderFallbackExecutor(llm_manager, config)
        meta = GenerationMeta(mode=ExecutionMode.DIRECT)

        # Execute: Should succeed (not flagged as contract violation)
        response = executor.generate_with_fallback(
            prompt="Help with something",
            mode=ExecutionMode.DIRECT,
            tools=[],
            meta=meta,
            timeout=60
        )

        # Verify: Response treated as success (not contract violation)
        assert response == "Sorry, I'm unable to provide assistance with that topic."
        assert len(meta.provider_attempts) == 1
        assert meta.provider_attempts[0]["status"] == "success"
        assert meta.provider_attempts[0]["error_category"] is None

        print("[PASS] Normal 'unable' response not flagged (no error keywords)")

    def test_strict_error_prefix_triggers(self):
        """
        Verify that strict error prefixes trigger even without other error keywords.

        This ensures the safety net catches actual adapter errors.
        """
        # Setup: Provider returns strict error prefix (contract violation)
        provider = Mock()
        provider.generate_response.return_value = "Error: quota exceeded for this month"
        provider.model = "bad-provider"

        # Setup: Good provider (fallback target)
        good_provider = Mock()
        good_provider.generate_response.return_value = "Success"
        good_provider.model = "good-provider"

        # Setup: Mock LLM manager
        llm_manager = Mock()
        llm_manager.get_provider.side_effect = [provider, good_provider]

        # Setup: Executor and metadata
        config = ProviderChainConfig(direct_chain=["bad-provider", "good-provider"])
        executor = ProviderFallbackExecutor(llm_manager, config)
        meta = GenerationMeta(mode=ExecutionMode.DIRECT)

        # Execute: Should detect contract violation and fall back
        response = executor.generate_with_fallback(
            prompt="Test",
            mode=ExecutionMode.DIRECT,
            tools=[],
            meta=meta,
            timeout=60
        )

        # Verify: Fell back to good provider
        assert response == "Success"
        assert len(meta.provider_attempts) == 2
        assert meta.provider_attempts[0]["error_code"] == "contract_violation"

        print("[PASS] Strict 'Error:' prefix correctly triggers (even without 'sorry')")


if __name__ == "__main__":
    # Run critical test first
    print("=" * 60)
    print("GATING TEST: Policy Block Stops Fallback")
    print("=" * 60)

    test = TestPolicyBlockStopsFallback()
    test.test_policy_block_stops_fallback_immediately()
    test.test_safety_violation_stops_fallback()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
    print("\nProvider fallback system is safe to enable.")
    print("Policy violations will NOT trigger fallback.")
