"""
TORQ Console Benchmarking Module

Performance benchmarking and SLO enforcement system for TORQ Console.
Provides comprehensive performance testing, regression detection, and SLO monitoring.
"""

from .slo_config import SLOConfig, SLOCategory
from .runner import BenchmarkRunner, BenchmarkResult
from .storage import BenchmarkStorage
from .reporting import BenchmarkReporter
from .cli import create_benchmark_commands

__version__ = "1.0.0"
__all__ = [
    "SLOConfig",
    "SLOCategory",
    "BenchmarkRunner",
    "BenchmarkResult",
    "BenchmarkStorage",
    "BenchmarkReporter",
    "create_benchmark_commands"
]