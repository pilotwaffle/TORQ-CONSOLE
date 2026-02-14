"""
TORQ Console Observability Dashboard

Real-time monitoring and metrics collection for system health and performance.
"""

from .collector import MetricsCollector
from .dashboard import Dashboard
from .exporter import MetricsExporter

__all__ = [
    'MetricsCollector',
    'Dashboard',
    'MetricsExporter'
]

__version__ = '1.0.0'
