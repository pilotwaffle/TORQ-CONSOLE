"""
Phase B: Configuration System and Feature Flags

Provides configurable parameters and feature flags for:
- Handoff optimization thresholds
- Performance tuning
- Feature enablement/disablement
- Environment-specific settings
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class HandoffConfig:
    """Configuration for handoff optimization."""
    # Context sizing
    max_context_length: int = 2000
    min_context_length: int = 500

    # Query complexity thresholds
    high_complexity_threshold: float = 0.7
    medium_complexity_threshold: float = 0.4

    # Quality scoring weights
    entity_weight: float = 0.5
    concept_weight: float = 0.3
    length_weight: float = 0.2

    # Performance thresholds
    slow_operation_threshold_ms: float = 100.0
    max_metrics_history: int = 1000

    # Compression
    min_compression_threshold: float = 0.8  # Fill at least 80% of target
    min_meaningful_remaining: int = 50  # Minimum chars for partial sentence

    @classmethod
    def from_env(cls) -> "HandoffConfig":
        """Load configuration from environment variables."""
        return cls(
            max_context_length=int(os.getenv("HANDOFF_MAX_CONTEXT", "2000")),
            min_context_length=int(os.getenv("HANDOFF_MIN_CONTEXT", "500")),
            high_complexity_threshold=float(os.getenv("HANDOFF_HIGH_COMPLEXITY", "0.7")),
            medium_complexity_threshold=float(os.getenv("HANDOFF_MED_COMPLEXITY", "0.4")),
            entity_weight=float(os.getenv("HANDOFF_ENTITY_WEIGHT", "0.5")),
            concept_weight=float(os.getenv("HANDOFF_CONCEPT_WEIGHT", "0.3")),
            length_weight=float(os.getenv("HANDOFF_LENGTH_WEIGHT", "0.2")),
            slow_operation_threshold_ms=float(os.getenv("HANDOFF_SLOW_MS", "100.0")),
            max_metrics_history=int(os.getenv("HANDOFF_MAX_METRICS", "1000")),
        )


@dataclass
class AgentConfig:
    """Configuration for agent system enhancements."""
    # Storage
    storage_dir: Path = field(default_factory=lambda: Path(".torq/agent_learning"))
    knowledge_file_name: str = "shared_knowledge.json"

    # Performance monitoring
    latency_threshold_seconds: float = 2.0
    quality_threshold: float = 0.7
    error_threshold: float = 0.1
    metrics_window_size: int = 1000

    # Knowledge sharing
    min_confidence_for_sharing: float = 0.8
    min_quality_for_sharing: float = 0.8

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load configuration from environment variables."""
        storage_dir = os.getenv("AGENT_STORAGE_DIR", ".torq/agent_learning")
        return cls(
            storage_dir=Path(storage_dir),
            latency_threshold_seconds=float(os.getenv("AGENT_LATENCY_THRESHOLD", "2.0")),
            quality_threshold=float(os.getenv("AGENT_QUALITY_THRESHOLD", "0.7")),
            error_threshold=float(os.getenv("AGENT_ERROR_THRESHOLD", "0.1")),
            metrics_window_size=int(os.getenv("AGENT_METRICS_WINDOW", "1000")),
            min_confidence_for_sharing=float(os.getenv("AGENT_MIN_CONFIDENCE", "0.8")),
            min_quality_for_sharing=float(os.getenv("AGENT_MIN_QUALITY", "0.8")),
        )


@dataclass
class FeatureFlags:
    """Feature flags for gradual rollout and A/B testing."""

    # Phase 1: Handoff optimization
    enable_handoff_optimizer: bool = True
    enable_semantic_compression: bool = True
    enable_adaptive_sizing: bool = True
    enable_metrics_collection: bool = True

    # Phase 3: Agent enhancements
    enable_cross_agent_learning: bool = True
    enable_performance_monitoring: bool = True
    enable_advanced_coordination: bool = True

    # Rollout percentage (0-100)
    handoff_optimizer_rollout_pct: int = 100
    agent_enhancements_rollout_pct: int = 100

    # Debug/development flags
    enable_debug_logging: bool = False
    enable_slow_operation_warnings: bool = True

    @classmethod
    def from_env(cls) -> "FeatureFlags":
        """Load feature flags from environment variables."""
        return cls(
            enable_handoff_optimizer=os.getenv("FEATURE_HANDOFF_OPT", "true").lower() == "true",
            enable_semantic_compression=os.getenv("FEATURE_SEMANTIC_COMPRESS", "true").lower() == "true",
            enable_adaptive_sizing=os.getenv("FEATURE_ADAPTIVE_SIZE", "true").lower() == "true",
            enable_metrics_collection=os.getenv("FEATURE_METRICS", "true").lower() == "true",
            enable_cross_agent_learning=os.getenv("FEATURE_CROSS_LEARNING", "true").lower() == "true",
            enable_performance_monitoring=os.getenv("FEATURE_PERF_MON", "true").lower() == "true",
            enable_advanced_coordination=os.getenv("FEATURE_ADV_COORD", "true").lower() == "true",
            handoff_optimizer_rollout_pct=int(os.getenv("ROLLOUT_HANDOFF_PCT", "100")),
            agent_enhancements_rollout_pct=int(os.getenv("ROLLOUT_AGENT_PCT", "100")),
            enable_debug_logging=os.getenv("DEBUG_LOGGING", "false").lower() == "true",
            enable_slow_operation_warnings=os.getenv("WARN_SLOW_OPS", "true").lower() == "true",
        )


# Global configuration instances
_handoff_config: Optional[HandoffConfig] = None
_agent_config: Optional[AgentConfig] = None
_feature_flags: Optional[FeatureFlags] = None


def get_handoff_config() -> HandoffConfig:
    """Get or create global handoff configuration."""
    global _handoff_config
    if _handoff_config is None:
        _handoff_config = HandoffConfig.from_env()
    return _handoff_config


def get_agent_config() -> AgentConfig:
    """Get or create global agent configuration."""
    global _agent_config
    if _agent_config is None:
        _agent_config = AgentConfig.from_env()
    return _agent_config


def get_feature_flags() -> FeatureFlags:
    """Get or create global feature flags."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags.from_env()
    return _feature_flags


def reload_config():
    """Reload all configuration from environment (for testing/hot reload)."""
    global _handoff_config, _agent_config, _feature_flags
    _handoff_config = None
    _agent_config = None
    _feature_flags = None
