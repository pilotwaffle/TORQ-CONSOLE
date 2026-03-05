"""
Configuration management for the TORQ Agent Cognitive Loop.

Provides configuration loading and management with support for environment variables
and runtime overrides.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from .models import CognitiveLoopConfig


class CognitiveLoopConfigManager:
    """Manages cognitive loop configuration with multiple sources."""

    DEFAULT_CONFIG = {
        "max_loop_latency_seconds": 2.0,
        "min_tool_success_rate": 0.95,
        "min_evaluation_confidence": 0.80,
        "max_retries": 3,
        "retry_delay_seconds": 0.5,
        "enable_fallback": True,
        "knowledge_enabled": True,
        "max_knowledge_contexts": 5,
        "knowledge_similarity_threshold": 0.75,
        "max_plan_steps": 10,
        "enable_parallel_execution": True,
        "tool_timeout_seconds": 30.0,
        "enable_tool_caching": True,
        "learning_enabled": True,
        "min_confidence_for_learning": 0.70,
        "telemetry_enabled": True,
        "emit_detailed_spans": True,
        "learning_storage_path": ".torq/cognitive_learning",
    }

    ENV_PREFIX = "TORQ_COGNITIVE_"
    ENV_MAPPING = {
        "TORQ_COGNITIVE_MAX_LATENCY": "max_loop_latency_seconds",
        "TORQ_COGNITIVE_MIN_SUCCESS_RATE": "min_tool_success_rate",
        "TORQ_COGNITIVE_MIN_CONFIDENCE": "min_evaluation_confidence",
        "TORQ_COGNITIVE_MAX_RETRIES": "max_retries",
        "TORQ_COGNITIVE_RETRY_DELAY": "retry_delay_seconds",
        "TORQ_COGNITIVE_ENABLE_FALLBACK": "enable_fallback",
        "TORQ_COGNITIVE_KNOWLEDGE_ENABLED": "knowledge_enabled",
        "TORQ_COGNITIVE_MAX_KNOWLEDGE": "max_knowledge_contexts",
        "TORQ_COGNITIVE_KNOWLEDGE_THRESHOLD": "knowledge_similarity_threshold",
        "TORQ_COGNITIVE_MAX_STEPS": "max_plan_steps",
        "TORQ_COGNITIVE_PARALLEL": "enable_parallel_execution",
        "TORQ_COGNITIVE_TOOL_TIMEOUT": "tool_timeout_seconds",
        "TORQ_COGNITIVE_TOOL_CACHE": "enable_tool_caching",
        "TORQ_COGNITIVE_LEARNING": "learning_enabled",
        "TORQ_COGNITIVE_MIN_LEARNING_CONFIDENCE": "min_confidence_for_learning",
        "TORQ_COGNITIVE_TELEMETRY": "telemetry_enabled",
        "TORQ_COGNITIVE_DETAILED_SPANS": "emit_detailed_spans",
        "TORQ_COGNITIVE_STORAGE": "learning_storage_path",
    }

    def __init__(self):
        self._config_cache: Optional[CognitiveLoopConfig] = None
        self._config_path: Optional[Path] = None

    def load_from_file(self, path: Path | str) -> CognitiveLoopConfig:
        """Load configuration from a JSON or YAML file."""
        import json

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r") as f:
            if path.suffix in (".yaml", ".yml"):
                import yaml
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        self._config_cache = CognitiveLoopConfig.from_dict(data)
        self._config_path = path
        return self._config_cache

    def load_from_env(self) -> CognitiveLoopConfig:
        """Load configuration from environment variables."""
        config_dict = self.DEFAULT_CONFIG.copy()

        for env_var, config_key in self.ENV_MAPPING.items():
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion
                if config_key.endswith(("_enabled", "_fallback", "_parallel", "_cache")):
                    config_dict[config_key] = value.lower() in ("true", "1", "yes")
                elif config_key.endswith(("_seconds", "_latency", "_timeout", "_rate", "_threshold")):
                    config_dict[config_key] = float(value)
                else:
                    config_dict[config_key] = int(value)

        self._config_cache = CognitiveLoopConfig(**config_dict)
        return self._config_cache

    def get_config(
        self,
        overrides: Optional[Dict[str, Any]] = None,
        use_env: bool = True
    ) -> CognitiveLoopConfig:
        """Get the current configuration with optional overrides."""
        if self._config_cache is None:
            if use_env:
                self.load_from_env()
            else:
                self._config_cache = CognitiveLoopConfig()

        config = self._config_cache

        if overrides:
            # Create a new config with overrides applied
            config_dict = {
                k: getattr(config, k) for k in config.__annotations__
            }
            config_dict.update(overrides)
            config = CognitiveLoopConfig(**config_dict)

        return config

    def set_config(self, config: CognitiveLoopConfig):
        """Set the current configuration."""
        self._config_cache = config

    def reset(self):
        """Reset to default configuration."""
        self._config_cache = None
        self._config_path = None


# Global configuration manager instance
_config_manager: Optional[CognitiveLoopConfigManager] = None


def get_config_manager() -> CognitiveLoopConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = CognitiveLoopConfigManager()
    return _config_manager


def get_cognitive_config(
    overrides: Optional[Dict[str, Any]] = None,
    use_env: bool = True
) -> CognitiveLoopConfig:
    """Get the current cognitive loop configuration."""
    return get_config_manager().get_config(overrides=overrides, use_env=use_env)


def set_cognitive_config(config: CognitiveLoopConfig):
    """Set the cognitive loop configuration."""
    get_config_manager().set_config(config)


def load_cognitive_config_from_file(path: Path | str) -> CognitiveLoopConfig:
    """Load cognitive loop configuration from a file."""
    return get_config_manager().load_from_file(path)
