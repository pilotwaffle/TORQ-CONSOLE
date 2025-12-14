"""
Performance tracking utilities for TORQ Prince Flowers agent.

This module provides performance monitoring and metrics collection
capabilities for the agent system.
"""

import logging
import psutil
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque


class PerformanceTracker:
    """Performance tracking and monitoring system."""

    def __init__(self):
        """Initialize the performance tracker."""
        self.logger = logging.getLogger("PerformanceTracker")
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 metrics
        self.response_times = deque(maxlen=100)
        self.start_time = time.time()

    def record_metric(self, metric_name: str, value: float, metadata: Dict[str, Any] = None):
        """Record a performance metric."""
        try:
            metric = {
                "timestamp": datetime.now(),
                "name": metric_name,
                "value": value,
                "metadata": metadata or {}
            }

            self.metrics_history.append(metric)

            if metric_name == "response_time":
                self.response_times.append(value)

        except Exception as e:
            self.logger.error(f"Error recording metric: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        try:
            current_time = time.time()
            uptime = current_time - self.start_time

            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            memory_mb = memory_info.used / (1024 * 1024)

            # Response time metrics
            avg_response_time = 0
            if self.response_times:
                avg_response_time = sum(self.response_times) / len(self.response_times)

            return {
                "uptime_seconds": uptime,
                "cpu_usage_percent": cpu_percent,
                "memory_usage_mb": memory_mb,
                "avg_response_time": avg_response_time,
                "total_metrics": len(self.metrics_history),
                "last_updated": datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Error getting metrics: {e}")
            return {"error": str(e)}

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get detailed memory usage information."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()

            return {
                "process_memory_mb": memory_info.rss / (1024 * 1024),
                "system_memory_mb": system_memory.used / (1024 * 1024),
                "system_memory_percent": system_memory.percent,
                "available_memory_mb": system_memory.available / (1024 * 1024)
            }

        except Exception as e:
            return {"error": str(e)}