"""
Metrics Collector for TORQ Console

Collects and aggregates metrics from all system components.
"""

import time
import threading
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta


class MetricPoint:
    """A single metric data point."""

    def __init__(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, timestamp: Optional[datetime] = None):
        self.name = name
        self.value = value
        self.tags = tags or {}
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat()
        }


class MetricsCollector:
    """
    Collects metrics from all TORQ Console components.

    Tracks:
    - Performance metrics (response times, throughput)
    - System metrics (memory, CPU, disk usage)
    - Business metrics (queries, errors, success rates)
    - Custom metrics from plugins
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector.

        Args:
            max_history: Maximum number of metric points to keep in memory
        """
        self.max_history = max_history
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

        # System start time
        self.start_time = time.time()

    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Amount to increment by
            tags: Optional tags for the metric
        """
        with self._lock:
            self._counters[name] += value

            # Store as metric point
            metric = MetricPoint(name, value, tags)
            self._metrics[name].append(metric)

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge metric (current value).

        Args:
            name: Metric name
            value: Current value
            tags: Optional tags for the metric
        """
        with self._lock:
            self._gauges[name] = value

            metric = MetricPoint(name, value, tags)
            self._metrics[name].append(metric)

    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a value in a histogram (distribution tracking).

        Args:
            name: Metric name
            value: Value to record
            tags: Optional tags for the metric
        """
        with self._lock:
            self._histograms[name].append(value)

            metric = MetricPoint(name, value, tags)
            self._metrics[name].append(metric)

    def timing(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a timing metric.

        Args:
            name: Operation name
            duration_ms: Duration in milliseconds
            tags: Optional tags for the metric
        """
        self.record_histogram(f"{name}.duration", duration_ms, tags)
        self.increment(f"{name}.count", 1.0, tags)

    def get_metric(self, name: str) -> Optional[List[MetricPoint]]:
        """Get all data points for a metric."""
        if name in self._metrics:
            return list(self._metrics[name])
        return None

    def get_counter(self, name: str) -> int:
        """Get current counter value."""
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> Optional[float]:
        """Get current gauge value."""
        return self._gauges.get(name)

    def get_histogram_stats(self, name: str) -> Optional[Dict[str, float]]:
        """
        Get histogram statistics for a metric.

        Returns:
            Dictionary with min, max, avg, p50, p95, p99
        """
        if name not in self._histograms or not self._histograms[name]:
            return None

        values = self._histograms[name]
        if not values:
            return None

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "count": count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / count,
            "p50": sorted_values[int(count * 0.5)],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)]
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all collected metrics.

        Returns:
            Dictionary with counters, gauges, and histograms
        """
        with self._lock:
            return {
                "counters": self._counters.copy(),
                "gauges": self._gauges.copy(),
                "histograms": {name: self.get_histogram_stats(name) for name in self._histograms},
                "uptime_seconds": time.time() - self.start_time,
                "metric_count": sum(len(metrics) for metrics in self._metrics.values())
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
