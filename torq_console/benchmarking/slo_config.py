"""
SLO Configuration Management for TORQ Console

Manages Service Level Objectives configuration, parsing, and validation.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

import yaml
from pydantic import BaseModel, Field, validator


class SLOCategory(BaseModel):
    """Individual SLO category configuration."""

    description: str
    p95_ttfuo_ms: Optional[int] = Field(None, description="95th percentile Time to First Useful Output in ms")
    p99_ttfuo_ms: Optional[int] = Field(None, description="99th percentile Time to First Useful Output in ms")
    p90_response_ms: Optional[int] = Field(None, description="90th percentile response time in ms")
    p95_e2e_ms: Optional[int] = Field(None, description="95th percentile End-to-End execution time in ms")
    p99_e2e_ms: Optional[int] = Field(None, description="99th percentile End-to-End execution time in ms")
    tokens_per_sec: Optional[float] = Field(None, description="Minimum tokens per second")
    success_rate: float = Field(0.95, description="Required success rate (0.0-1.0)")
    max_memory_mb: int = Field(1024, description="Maximum memory usage in MB")
    sample_size: int = Field(100, description="Minimum sample size for validity")

    @validator('success_rate')
    def validate_success_rate(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Success rate must be between 0.0 and 1.0')
        return v

    def get_primary_metric(self) -> str:
        """Get the primary performance metric for this category."""
        if self.p95_ttfuo_ms is not None:
            return "p95_ttfuo_ms"
        elif self.p95_e2e_ms is not None:
            return "p95_e2e_ms"
        else:
            return "p90_response_ms"

    def get_primary_target(self) -> Union[int, float]:
        """Get the primary performance target value."""
        metric = self.get_primary_metric()
        return getattr(self, metric)


class ThresholdConfig(BaseModel):
    """Performance thresholds and alerting configuration."""

    degradation_warning: float = 10.0  # % degradation for warning
    degradation_critical: float = 25.0  # % degradation for critical
    max_cost_per_success: float = 0.10  # Maximum cost per successful operation ($)
    cost_increase_warning: float = 20.0  # % cost increase for warning
    regression_window: int = 7  # Days for regression detection
    min_samples_for_regression: int = 30


class BenchmarkConfig(BaseModel):
    """Benchmark execution configuration."""

    default_duration: int = 300  # seconds
    warmup_iterations: int = 5
    max_iterations: int = 1000
    timeout_ms: int = 120000  # 2 minutes
    concurrent_users: int = 1
    max_concurrent_users: int = 10
    output_format: str = "json"
    include_percentiles: List[int] = [50, 90, 95, 99]
    include_detailed_breakdown: bool = True

    @validator('output_format')
    def validate_output_format(cls, v):
        if v not in ['json', 'table', 'csv']:
            raise ValueError('Output format must be one of: json, table, csv')
        return v

    @validator('include_percentiles')
    def validate_percentiles(cls, v):
        for p in v:
            if not 0 <= p <= 100:
                raise ValueError('Percentiles must be between 0 and 100')
        return sorted(v)


class EnvironmentConfig(BaseModel):
    """Environment-specific SLO adjustments."""

    slack_factor: float = 1.0
    sample_size_multiplier: float = 1.0

    @validator('slack_factor')
    def validate_slack_factor(cls, v):
        if v < 1.0:
            raise ValueError('Slack factor must be >= 1.0')
        return v


class SLOConfig(BaseModel):
    """Complete SLO configuration."""

    version: str
    description: str
    last_updated: str
    categories: Dict[str, SLOCategory] = Field(default_factory=dict)
    thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)
    benchmark: BenchmarkConfig = Field(default_factory=BenchmarkConfig)
    environments: Dict[str, EnvironmentConfig] = Field(
        default_factory=lambda: {
            "development": EnvironmentConfig(slack_factor=2.0, sample_size_multiplier=0.5),
            "staging": EnvironmentConfig(slack_factor=1.5, sample_size_multiplier=0.8),
            "production": EnvironmentConfig(slack_factor=1.0, sample_size_multiplier=1.0)
        }
    )

    @classmethod
    def load_from_file(cls, config_path: Union[str, Path]) -> 'SLOConfig':
        """Load SLO configuration from YAML file."""
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"SLO configuration file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)

    @classmethod
    def load_default(cls) -> 'SLOConfig':
        """Load default SLO configuration."""
        # Look for slo.yml in current directory, then package directory
        current_dir = Path.cwd()
        package_dir = Path(__file__).parent.parent.parent

        for search_dir in [current_dir, package_dir]:
            config_path = search_dir / "slo.yml"
            if config_path.exists():
                return cls.load_from_file(config_path)

        raise FileNotFoundError("No SLO configuration file found. Expected 'slo.yml' in current directory or package root.")

    def get_category(self, category_name: str, environment: str = "production") -> SLOCategory:
        """Get SLO category with environment adjustments applied."""
        if category_name not in self.categories:
            raise ValueError(f"Unknown SLO category: {category_name}")

        base_category = self.categories[category_name]
        env_config = self.environments.get(environment, self.environments["production"])

        # Apply environment adjustments
        adjusted_category = base_category.copy()

        # Apply slack factor to timing metrics
        slack_factor = env_config.slack_factor

        if adjusted_category.p95_ttfuo_ms is not None:
            adjusted_category.p95_ttfuo_ms = int(adjusted_category.p95_ttfuo_ms * slack_factor)
        if adjusted_category.p99_ttfuo_ms is not None:
            adjusted_category.p99_ttfuo_ms = int(adjusted_category.p99_ttfuo_ms * slack_factor)
        if adjusted_category.p90_response_ms is not None:
            adjusted_category.p90_response_ms = int(adjusted_category.p90_response_ms * slack_factor)
        if adjusted_category.p95_e2e_ms is not None:
            adjusted_category.p95_e2e_ms = int(adjusted_category.p95_e2e_ms * slack_factor)
        if adjusted_category.p99_e2e_ms is not None:
            adjusted_category.p99_e2e_ms = int(adjusted_category.p99_e2e_ms * slack_factor)

        # Apply sample size multiplier
        adjusted_category.sample_size = int(adjusted_category.sample_size * env_config.sample_size_multiplier)

        return adjusted_category

    def validate_slo(self, category_name: str, metric_value: Union[int, float],
                     metric_name: Optional[str] = None, environment: str = "production") -> bool:
        """Validate if a metric meets SLO requirements."""
        category = self.get_category(category_name, environment)

        if metric_name is None:
            metric_name = category.get_primary_metric()

        target_value = getattr(category, metric_name, None)
        if target_value is None:
            return True  # No target defined, always passes

        # For timing metrics, lower is better
        if metric_name.endswith('_ms'):
            return metric_value <= target_value
        # For rate metrics, higher is better
        else:
            return metric_value >= target_value

    def get_degradation_level(self, category_name: str, metric_value: Union[int, float],
                            metric_name: Optional[str] = None, environment: str = "production") -> str:
        """Get degradation level (ok, warning, critical) for a metric."""
        category = self.get_category(category_name, environment)

        if metric_name is None:
            metric_name = category.get_primary_metric()

        target_value = getattr(category, metric_name, None)
        if target_value is None:
            return "ok"

        # Calculate degradation percentage
        if metric_name.endswith('_ms'):
            # For timing metrics
            degradation = ((metric_value - target_value) / target_value) * 100
        else:
            # For rate metrics
            degradation = ((target_value - metric_value) / target_value) * 100

        if degradation >= self.thresholds.degradation_critical:
            return "critical"
        elif degradation >= self.thresholds.degradation_warning:
            return "warning"
        else:
            return "ok"

    def list_categories(self) -> List[str]:
        """List all available SLO categories."""
        return list(self.categories.keys())

    def save_to_file(self, config_path: Union[str, Path]) -> None:
        """Save SLO configuration to YAML file."""
        config_path = Path(config_path)

        # Update last_updated timestamp
        self.last_updated = datetime.now().isoformat()

        config_data = {
            "version": self.version,
            "description": self.description,
            "last_updated": self.last_updated,
            "categories": {name: category.dict() for name, category in self.categories.items()},
            "thresholds": self.thresholds.dict(),
            "benchmark": self.benchmark.dict(),
            "environments": {name: env.dict() for name, env in self.environments.items()}
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)