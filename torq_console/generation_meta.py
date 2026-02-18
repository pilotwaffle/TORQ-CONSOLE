"""
Generation Metadata for TORQ Console AI responses.

This module provides the GenerationMeta dataclass for consistent metadata tracking
across all AI providers, tools, and execution modes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ExecutionMode(str, Enum):
    """Execution mode for the AI request."""
    DIRECT = "direct"          # Direct LLM call, no tools
    RESEARCH = "research"      # Research with web search
    CODE_GENERATION = "code_generation"  # Code generation
    COMPOSITION = "composition"  # Multi-step composition
    HIERARCHICAL = "hierarchical"  # Hierarchical planning


@dataclass
class GenerationMeta:
    """
    Metadata for AI generation responses.

    This provides visibility into:
    - Which provider/model was used
    - How long the request took
    - Token usage and cost estimates
    - Which tools were executed
    - Whether caching was involved
    - Request identification for tracing

    All fields are optional to accommodate different execution paths and error scenarios.
    """

    # Provider information
    provider: str = field(default="unknown")
    model: str = field(default="unknown")
    mode: ExecutionMode = field(default=ExecutionMode.DIRECT)

    # Timing information
    latency_ms: int = field(default=0)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Token usage
    tokens_in: Optional[int] = field(default=None)
    tokens_out: Optional[int] = field(default=None)
    tokens_total: Optional[int] = field(default=None)

    # Cost estimation (USD)
    cost_usd_est: Optional[float] = field(default=None)

    # Tools and execution
    tools_used: List[str] = field(default_factory=list)
    tool_results: int = field(default=0)  # Number of tool executions
    cache_hit: bool = field(default=False)

    # Request identification
    request_id: Optional[str] = field(default=None)

    # Provider fallback tracking
    provider_attempts: List[Dict[str, Any]] = field(default_factory=list)  # Full attempt records
    fallback_used: bool = field(default=False)
    fallback_reason: Optional[str] = None  # e.g., "provider_error:429", "timeout"

    # Error information
    error: Optional[str] = field(default=None)
    error_category: Optional[str] = field(default=None)  # "timeout", "rate_limit", "provider_error"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "provider": self.provider,
            "model": self.model,
            "mode": self.mode.value if isinstance(self.mode, ExecutionMode) else self.mode,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "tokens_total": self.tokens_total,
            "cost_usd_est": self.cost_usd_est,
            "tools_used": self.tools_used,
            "tool_results": self.tool_results,
            "cache_hit": self.cache_hit,
            "request_id": self.request_id,
            "provider_attempts": self.provider_attempts,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "error": self.error,
            "error_category": self.error_category,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GenerationMeta":
        """Create from dictionary (for deserialization)."""
        mode = data.get("mode", "direct")
        if isinstance(mode, str):
            try:
                mode = ExecutionMode(mode)
            except ValueError:
                mode = ExecutionMode.DIRECT

        return cls(
            provider=data.get("provider", "unknown"),
            model=data.get("model", "unknown"),
            mode=mode,
            latency_ms=data.get("latency_ms", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            tokens_in=data.get("tokens_in"),
            tokens_out=data.get("tokens_out"),
            tokens_total=data.get("tokens_total"),
            cost_usd_est=data.get("cost_usd_est"),
            tools_used=data.get("tools_used", []),
            tool_results=data.get("tool_results", 0),
            cache_hit=data.get("cache_hit", False),
            request_id=data.get("request_id"),
            provider_attempts=data.get("provider_attempts", []),
            fallback_used=data.get("fallback_used", False),
            fallback_reason=data.get("fallback_reason"),
            error=data.get("error"),
            error_category=data.get("error_category"),
        )


@dataclass
class GenerationResult:
    """
    Complete result from AI generation.

    This couples the response text with its metadata, making it impossible
    to return a response without providing context about how it was generated.
    """

    response: str
    meta: GenerationMeta
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "response": self.response,
            "meta": self.meta.to_dict(),
            "success": self.success,
        }

    def to_api_response(self) -> Dict[str, Any]:
        """
        Convert to API response format for /api/chat.

        This is the format returned to clients, including all keys
        they expect (success, response, timestamp, etc.) plus the new meta block.
        """
        result = {
            "success": self.success,
            "response": self.response,
            "meta": self.meta.to_dict(),
            "timestamp": self.meta.timestamp,
            "agent": "TORQ Console Enhanced AI",
            "enhanced_mode": True,  # If we have metadata, we're in enhanced mode
        }

        if self.meta.error:
            result["error"] = self.meta.error
            result["error_category"] = self.meta.error_category

        return result


def create_error_meta(
    error: str,
    provider: str = "unknown",
    error_category: str = "unknown",
    latency_ms: int = 0,
) -> GenerationMeta:
    """Create metadata for error responses."""
    return GenerationMeta(
        provider=provider,
        error=error,
        error_category=error_category,
        latency_ms=latency_ms,
    )


def estimate_cost(
    provider: str,
    model: str,
    tokens_in: int,
    tokens_out: int
) -> Optional[float]:
    """
    Estimate cost in USD for a generation.

    Args:
        provider: Provider name (deepseek, claude, openai, etc.)
        model: Model name
        tokens_in: Input tokens
        tokens_out: Output tokens

    Returns:
        Estimated cost in USD, or None if unknown
    """
    # Rough pricing as of 2025 (update as needed)
    pricing = {
        # DeepSeek
        ("deepseek", "deepseek-chat"): (0.14, 0.28),  # per million tokens
        ("deepseek", "deepseek-coder"): (0.14, 0.28),

        # Claude (Anthropic)
        ("claude", "claude-3-5-sonnet-20241022"): (3.0, 15.0),
        ("claude", "claude-sonnet-4-20250514"): (3.0, 15.0),
        ("claude", "claude-opus-4-20250514"): (15.0, 75.0),

        # OpenAI
        ("openai", "gpt-4"): (30.0, 60.0),
        ("openai", "gpt-4-turbo"): (10.0, 30.0),
        ("openai", "gpt-3.5-turbo"): (0.5, 1.5),
    }

    key = (provider.lower(), model.lower())
    if key in pricing:
        price_in, price_out = pricing[key]
        cost = (tokens_in / 1_000_000) * price_in + (tokens_out / 1_000_000) * price_out
        return round(cost, 6)
    else:
        return None
