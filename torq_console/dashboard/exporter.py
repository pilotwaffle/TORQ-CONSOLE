"""
Metrics Exporter for TORQ Console

Exports collected metrics to various formats and endpoints.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .collector import MetricsCollector


class MetricsExporter:
    """Export metrics to various formats and destinations."""

    def __init__(self, collector: MetricsCollector):
        """
        Initialize metrics exporter.

        Args:
            collector: MetricsCollector instance to export from
        """
        self.collector = collector
        self.logger = logging.getLogger(__name__)

    def to_json(self, pretty: bool = True) -> str:
        """
        Export all metrics as JSON.

        Args:
            pretty: Whether to format JSON with indentation

        Returns:
            JSON string of all metrics
        """
        metrics = self.collector.get_all_metrics()

        if pretty:
            return json.dumps(metrics, indent=2, default=str)
        return json.dumps(metrics, default=str)

    def to_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            String in Prometheus exposition format
        """
        lines = []
        metrics = self.collector.get_all_metrics()

        # Export counters
        for name, value in metrics.get("counters", {}).items():
            lines.append(f"# HELP torq_{name} Counter metric for {name}")
            lines.append(f"# TYPE torq_{name} counter")
            lines.append(f"torq_{name} {value}")

        # Export gauges
        for name, value in metrics.get("gauges", {}).items():
            lines.append(f"# HELP torq_{name} Gauge metric for {name}")
            lines.append(f"# TYPE torq_{name} gauge")
            lines.append(f"torq_{name} {value}")

        # Export histogram stats
        for name, stats in metrics.get("histograms", {}).items():
            if stats:
                base = f"torq_{name}"
                lines.append(f"# HELP {base} Histogram stats for {name}")
                lines.append(f"# TYPE {base} summary")
                lines.append(f"{base}_count {stats['count']}")
                lines.append(f"{base}_sum {stats['count']}")  # Use count as sum for now
                lines.append(f"{base}_avg {stats['avg']}")
                lines.append(f"{base}_max {stats['max']}")

        return "\n".join(lines)

    def save_to_file(self, filepath: str, format_type: str = "json") -> bool:
        """
        Save metrics to a file.

        Args:
            filepath: Path to save metrics
            format_type: Either 'json' or 'prometheus'

        Returns:
            True if saved successfully
        """
        try:
            if format_type == "json":
                content = self.to_json()
            elif format_type == "prometheus":
                content = self.to_prometheus()
            else:
                self.logger.error(f"Unknown format type: {format_type}")
                return False

            with open(filepath, 'w') as f:
                f.write(content)

            self.logger.info(f"Saved metrics to {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")
            return False

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get metrics formatted for dashboard display.

        Returns:
            Dictionary with dashboard-ready data
        """
        metrics = self.collector.get_all_metrics()

        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": metrics.get("uptime_seconds", 0),
            "counters": [
                {
                    "name": name,
                    "value": value
                }
                for name, value in metrics.get("counters", {}).items()
            ],
            "gauges": [
                {
                    "name": name,
                    "value": value
                }
                for name, value in metrics.get("gauges", {}).items()
            ],
            "histograms": [
                {
                    "name": name,
                    "stats": stats
                }
                for name, stats in metrics.get("histograms", {}).items()
                if stats
            ],
            "summary": {
                "total_metrics": metrics.get("metric_count", 0),
                "total_counters": len(metrics.get("counters", {})),
                "total_gauges": len(metrics.get("gauges", {})),
                "total_histograms": len(metrics.get("histograms", {}))
            }
        }
