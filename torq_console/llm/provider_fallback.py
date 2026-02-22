"""
Provider Fallback System for TORQ Console

Implements deterministic, single-pass provider fallback with:
- Full observability (every attempt recorded)
- Category preservation (timeouts vs provider errors)
- Non-masking behavior (final error reflects actual failure)
- No recursion (single pass through provider chain)
- Bounded delay on 429 (prevents cascade across providers)

Design Principles:
1. meta.provider_attempts always populated (length >= 1)
2. meta.fallback_used = (len(attempts) > 1)
3. Success on any provider → return immediately
4. All providers fail → raise with complete attempt history
5. Rate limits (429) → small delay before next provider (prevents cascade)
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

from torq_console.generation_meta import GenerationMeta, ExecutionMode
from torq_console.ui.web_ai_fix import AIResponseError, AITimeoutError, ProviderError

# Constants for fallback behavior
RATE_LIMIT_DELAY_MS = 250  # Small bounded delay for 429 to prevent cascade


class AttemptStatus(str, Enum):
    """Status of a provider attempt."""
    SUCCESS = "success"
    FAILED = "failed"


class ErrorCategory(str, Enum):
    """Error categories for fallback decisions."""
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"
    AI_ERROR = "ai_error"
    EXCEPTION = "exception"


class RetryableError(str, Enum):
    """
    Error categories that are retryable (try next provider).

    Non-retryable: User/prompt issues that won't change across providers.
    """
    # Retry these (infrastructure/provider issues)
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"
    EXCEPTION = "exception"

    # Don't retry these (user/prompt issues)
    AI_ERROR = "ai_error"


@dataclass
class ProviderAttempt:
    """
    Single provider attempt record.

    This captures everything needed for:
    - Observability (what happened with each provider?)
    - Debugging (why did provider X fail?)
    - Analytics (which providers are failing most?)
    - Cost tracking (how much did we spend on failed attempts?)
    """

    # Provider identification
    provider: str
    model: str = "unknown"

    # Attempt outcome
    status: AttemptStatus = AttemptStatus.FAILED
    error_category: Optional[ErrorCategory] = None
    error_code: Optional[str] = None  # e.g., "429", "401", "rate_limited"

    # Performance metrics
    latency_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Token usage (if attempt succeeded)
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    tokens_total: Optional[int] = None

    # Cost estimation
    cost_usd_est: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "provider": self.provider,
            "model": self.model,
            "status": self.status.value if isinstance(self.status, AttemptStatus) else self.status,
            "error_category": self.error_category.value if self.error_category else None,
            "error_code": self.error_code,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "tokens_total": self.tokens_total,
            "cost_usd_est": self.cost_usd_est,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderAttempt":
        """Create from dictionary (for deserialization)."""
        status = data.get("status", "failed")
        if isinstance(status, str):
            try:
                status = AttemptStatus(status)
            except ValueError:
                status = AttemptStatus.FAILED

        error_cat = data.get("error_category")
        if isinstance(error_cat, str):
            try:
                error_cat = ErrorCategory(error_cat)
            except ValueError:
                error_cat = None

        return cls(
            provider=data.get("provider", "unknown"),
            model=data.get("model", "unknown"),
            status=status,
            error_category=error_cat,
            error_code=data.get("error_code"),
            latency_ms=data.get("latency_ms", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            tokens_in=data.get("tokens_in"),
            tokens_out=data.get("tokens_out"),
            tokens_total=data.get("tokens_total"),
            cost_usd_est=data.get("cost_usd_est"),
        )


@dataclass
class ProviderChainConfig:
    """
    Provider fallback chain configuration.

    Chains are mode-aware because different modes have different priorities:
    - DIRECT mode: Speed and cost matter (cheapest/fastest first)
    - RESEARCH mode: Quality matters (best synthesis first)
    """

    # Direct mode: fast + cheap first (for quick answers)
    direct_chain: List[str] = field(default_factory=lambda: ["deepseek", "claude", "ollama"])

    # Research mode: quality first (for web search + synthesis)
    research_chain: List[str] = field(default_factory=lambda: ["claude", "deepseek", "ollama"])

    # Code generation: reliability first
    code_generation_chain: List[str] = field(default_factory=lambda: ["claude", "deepseek"])

    # Default chain (fallback if mode not specified)
    default_chain: List[str] = field(default_factory=lambda: ["deepseek", "claude"])

    def get_chain_for_mode(self, mode: ExecutionMode) -> List[str]:
        """Get provider chain for a specific execution mode."""
        if mode == ExecutionMode.DIRECT:
            return self.direct_chain
        elif mode == ExecutionMode.RESEARCH:
            return self.research_chain
        elif mode == ExecutionMode.CODE_GENERATION:
            return self.code_generation_chain
        else:
            return self.default_chain


class ProviderFallbackExecutor:
    """
    Executes provider fallback chain with deterministic, single-pass logic.

    Key Properties:
    - Single-pass: No recursion, no nested retries
    - Meta-first: Every attempt recorded in metadata
    - Category-preserving: Timeouts stay timeouts, provider errors stay provider errors
    - Non-masking: Final error reflects why ALL providers failed

    Usage:
        executor = ProviderFallbackExecutor(llm_manager)
        result = executor.generate_with_fallback(
            prompt="What is 2+2?",
            mode=ExecutionMode.DIRECT,
            tools=[],
            meta=GenerationMeta()
        )
    """

    def __init__(self, llm_manager, chain_config: Optional[ProviderChainConfig] = None):
        """
        Initialize fallback executor.

        Args:
            llm_manager: LLMManager instance with get_provider() method
            chain_config: Optional provider chain configuration
        """
        self.llm_manager = llm_manager
        self.chain_config = chain_config or ProviderChainConfig()
        self.logger = logging.getLogger(__name__)

    def should_retry(self, error_category: Optional[ErrorCategory]) -> bool:
        """
        Determine if an error category should trigger fallback.

        Retryable (infrastructure/provider issues):
        - timeout: Provider took too long
        - provider_error: 429, 5xx, connection, DNS, auth, quota
        - exception: Provider adapter crash

        Non-retryable (user/prompt issues):
        - ai_error: Invalid request shape, content policy

        Args:
            error_category: The error category from the failed attempt

        Returns:
            True if we should try the next provider, False if we should fail immediately
        """
        if error_category is None:
            return False

        # Don't retry on user/prompt issues
        if error_category == ErrorCategory.AI_ERROR:
            return False

        # Retry everything else (timeout, provider_error, exception)
        return error_category in [
            ErrorCategory.TIMEOUT,
            ErrorCategory.PROVIDER_ERROR,
            ErrorCategory.EXCEPTION,
        ]

    async def generate_with_fallback(
        self,
        prompt: str,
        mode: ExecutionMode,
        tools: List[str],
        meta: GenerationMeta,
        timeout: int = 60,
    ) -> str:
        """
        Generate response with provider fallback.

        Args:
            prompt: The user's prompt (never mutated internally)
            mode: Execution mode (DIRECT, RESEARCH, CODE_GENERATION, etc.)
            tools: List of tools to use (e.g., ["web_search"])
            meta: GenerationMeta object (will be populated with attempt history)
            timeout: Per-provider timeout in seconds

        Returns:
            Response text from first successful provider

        Raises:
            AITimeoutError: All providers timed out
            ProviderError: All providers failed with provider errors
            AIResponseError: Non-retryable error (user/prompt issue)
            Exception: Unexpected error

        Important:
            - `prompt` is NEVER mutated inside this method
            - All providers receive the same base_prompt
            - Only tool results are injected (not accumulated)
        """
        # Store original prompt (NEVER mutate this variable)
        base_prompt = prompt

        # Get provider chain for this mode
        provider_chain = self.chain_config.get_chain_for_mode(mode)

        # Initialize attempt tracking (before sanitization so missing providers are recorded)
        meta.provider_attempts = []  # type: ignore
        last_error = None

        # Sanitize provider chain: drop providers that are not registered
        sanitized_chain = []
        for name in provider_chain:
            try:
                provider = self.llm_manager.get_provider(name)
                if provider is not None:
                    sanitized_chain.append(name)
                else:
                    # Record attempt as missing provider (observable), then skip
                    attempt = ProviderAttempt(provider=name)
                    attempt.status = AttemptStatus.FAILED
                    attempt.error_category = ErrorCategory.PROVIDER_ERROR
                    attempt.error_code = "provider_not_found"
                    meta.provider_attempts.append(attempt.to_dict())  # type: ignore
                    self.logger.warning(f"Provider '{name}' not found in manager, skipping")
            except Exception as e:
                # Record attempt as missing provider (observable), then skip
                attempt = ProviderAttempt(provider=name)
                attempt.status = AttemptStatus.FAILED
                attempt.error_category = ErrorCategory.PROVIDER_ERROR
                attempt.error_code = "provider_not_found"
                meta.provider_attempts.append(attempt.to_dict())  # type: ignore
                self.logger.warning(f"Provider '{name}' not accessible, skipping: {e}")

        provider_chain = sanitized_chain

        # Single pass through provider chain
        for provider_name in provider_chain:
            # Create attempt record
            attempt = ProviderAttempt(
                provider=provider_name,
                status=AttemptStatus.FAILED,
                timestamp=datetime.now().isoformat(),
            )

            t0 = time.time()

            try:
                # Get provider instance
                provider = self.llm_manager.get_provider(provider_name)

                if provider is None:
                    raise ProviderError(f"Provider '{provider_name}' not found")

                # Use base_prompt for every provider (no accumulation)
                # IMPORTANT: Never use the parameter `prompt` here - it must remain immutable
                current_prompt = base_prompt

                # Generate response (async call)
                response = await provider.generate_response(
                    prompt=current_prompt,  # Always use fresh copy from base_prompt
                    timeout=timeout,
                )

                # CONTRACT VIOLATION DETECTION
                # Providers must raise typed exceptions, not return error strings/dicts
                # If we detect an error string/dict, convert to ProviderError and retry
                if isinstance(response, str):
                    # Check if it looks like an adapter error (not normal LLM conversation)
                    response_lower = response.lower()
                    response_stripped = response_lower.strip()

                    # ADAPTER ERROR PREFIXES: Prefixes only provider adapters should emit
                    # These strings indicate legacy adapter error paths (forbidden by contract).
                    # Normal LLM output should NEVER start with these prefixes.
                    # If you add a new adapter, add its legacy error prefixes here temporarily during migration.
                    adapter_error_prefixes = [
                        "error:",                    # "Error: API key not found"
                        "error ",                    # "Error querying Claude:"
                        "failed:",                   # "Failed after 3 retries"
                        "i apologize, but i encountered an error",  # Full boilerplate
                        "i apologize, but i encountered an exception",  # Full boilerplate
                        "unable to process",         # "Unable to process your request"
                        "encountered an error while processing",  # Boilerplate
                    ]

                    # Combined check: apology words + TECHNICAL error keywords only
                    # This catches "I'm sorry, there was an error" but NOT "Sorry, I can't help"
                    if (any(response_stripped.startswith(prefix) for prefix in adapter_error_prefixes) or
                        (any(word in response_stripped for word in ["sorry", "apologize"]) and
                         any(kw in response_stripped for kw in ["error", "exception", "traceback"]))):
                        # Provider violated contract by returning error string
                        preview = response[:120]
                        error_msg = f"Provider '{provider_name}' returned error string instead of raising exception: {preview}"
                        self.logger.warning(error_msg)

                        # Create ProviderError with detailed metadata for dashboard detection
                        violation_error = ProviderError(
                            "Provider adapter contract violation: returned error string",
                            code="contract_violation"
                        )
                        # Attach metadata for debugging (dashboards can parse these fields)
                        setattr(violation_error, 'violation_type', 'adapter_returned_error_string')
                        setattr(violation_error, 'provider_message_preview', preview)

                        raise violation_error

                elif isinstance(response, dict):
                    # ANY dict return is a contract violation
                    # Providers must return str or raise exceptions
                    # This prevents interface drift where adapters start returning structured outputs
                    preview = str(response)[:120]
                    error_msg = f"Provider '{provider_name}' returned dict instead of raising exception: {preview}"
                    self.logger.warning(error_msg)

                    # Create ProviderError with detailed metadata for dashboard detection
                    violation_error = ProviderError(
                        "Provider adapter contract violation: returned dict",
                        code="contract_violation"
                    )
                    # Attach metadata for debugging (dashboards can parse these fields)
                    setattr(violation_error, 'violation_type', 'adapter_returned_dict')
                    setattr(violation_error, 'provider_message_preview', preview)

                    raise violation_error

                # Calculate latency
                latency_ms = int((time.time() - t0) * 1000)
                attempt.latency_ms = latency_ms

                # Record success
                attempt.status = AttemptStatus.SUCCESS
                attempt.error_category = None
                attempt.error_code = None

                # Try to extract model name
                if hasattr(provider, 'model'):
                    attempt.model = provider.model

                # Try to extract token usage (if provider supports it)
                if hasattr(response, 'usage') or hasattr(response, 'tokens_in'):
                    # Adjust based on your provider's response structure
                    pass

                # Add to attempt history
                meta.provider_attempts.append(attempt.to_dict())  # type: ignore

                # Update metadata with winning provider
                meta.provider = provider_name
                meta.model = attempt.model
                meta.latency_ms = latency_ms
                meta.fallback_used = len(meta.provider_attempts) > 1  # type: ignore
                meta.error = None
                meta.error_category = None

                # Return immediately on first success
                return response

            except AITimeoutError as e:
                # Provider timeout - retryable
                attempt.latency_ms = int((time.time() - t0) * 1000)
                attempt.error_category = ErrorCategory.TIMEOUT
                attempt.error_code = getattr(e, 'code', None)

                meta.provider_attempts.append(attempt.to_dict())  # type: ignore
                last_error = e

                # Continue to next provider
                continue

            except ProviderError as e:
                # Provider error - retryable (429, 5xx, connection, etc.)
                attempt.latency_ms = int((time.time() - t0) * 1000)
                attempt.error_category = ErrorCategory.PROVIDER_ERROR
                attempt.error_code = getattr(e, 'code', None)

                meta.provider_attempts.append(attempt.to_dict())  # type: ignore
                last_error = e

                # Small bounded delay for 429 to prevent cascade across providers
                if attempt.error_code == "429":
                    time.sleep(RATE_LIMIT_DELAY_MS / 1000.0)

                # Continue to next provider
                continue

            except AIResponseError as e:
                # AI/prompt error - NOT retryable (fail fast)
                attempt.latency_ms = int((time.time() - t0) * 1000)
                attempt.error_category = ErrorCategory.AI_ERROR
                attempt.error_code = getattr(e, 'code', None)

                meta.provider_attempts.append(attempt.to_dict())  # type: ignore

                # Don't retry - this is a user/prompt issue
                meta.fallback_used = len(meta.provider_attempts) > 1  # type: ignore
                raise

            except Exception as e:
                # Unexpected exception - retryable
                attempt.latency_ms = int((time.time() - t0) * 1000)
                attempt.error_category = ErrorCategory.EXCEPTION
                attempt.error_code = type(e).__name__

                meta.provider_attempts.append(attempt.to_dict())  # type: ignore
                last_error = ProviderError(f"Provider adapter exception: {e}", cause=e)

                # Continue to next provider
                continue

        # All providers failed
        meta.fallback_used = len(meta.provider_attempts) > 1  # type: ignore

        # Raise the last error with full context
        if last_error is not None:
            raise ProviderError(
                f"All providers in chain failed. Last error: {last_error}",
                cause=last_error
            ) from last_error
        else:
            raise ProviderError("All providers in chain failed (unknown error)")
