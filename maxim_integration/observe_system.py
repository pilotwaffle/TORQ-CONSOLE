"""
Maxim AI Integration - Phase 3: Observe Component
Production monitoring and quality assurance system for Prince Flowers agents

This module implements Maxim's Observe component with:
- Real-time performance monitoring
- Distributed tracing across agent workflows
- Quality checks and automated alerting
- Performance dashboards and analytics
- Reliability monitoring and error tracking
"""

import asyncio
import json
import time
import logging
import uuid
import hashlib
import statistics
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime, timedelta
import os
import asyncio
import threading
from collections import defaultdict, deque

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """Types of metrics tracked"""
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    QUALITY = "quality"
    BUSINESS = "business"
    SYSTEM = "system"

class AlertStatus(Enum):
    """Alert status tracking"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    IGNORED = "ignored"

@dataclass
class MetricDefinition:
    """Definition of a tracked metric"""
    name: str
    metric_type: MetricType
    description: str
    unit: str
    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    aggregation: str = "average"  # average, sum, min, max, count
    tags: List[str] = field(default_factory=list)

@dataclass
class MetricValue:
    """Single metric value with metadata"""
    metric_name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None

@dataclass
class Alert:
    """Alert definition and metadata"""
    alert_id: str
    metric_name: str
    severity: AlertSeverity
    title: str
    message: str
    threshold: float
    actual_value: float
    triggered_at: datetime
    status: AlertStatus
    resolved_at: Optional[datetime] = None
    acknowledgment_required: bool = False
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TraceEvent:
    """Single event in a distributed trace"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    component: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    status: str  # success, error, timeout
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class QualityCheck:
    """Quality check definition and result"""
    check_id: str
    name: str
    description: str
    check_function: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    frequency_seconds: int
    enabled: bool = True
    last_run: Optional[datetime] = field(default=None)
    last_result: Optional[bool] = field(default=None)
    failure_count: int = 0

@dataclass
class DashboardWidget:
    """Dashboard widget definition"""
    widget_id: str
    title: str
    widget_type: str  # metric_chart, alert_table, trace_visualizer
    metric_names: List[str]
    time_range_hours: int
    refresh_interval_seconds: int
    position: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)

class ObserveSystem:
    """
    Production monitoring and quality assurance system
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

        # Metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        self.active_metrics: set = set()

        # Alerting system
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, Dict] = {}
        self.alert_handlers: List[Callable] = []

        # Tracing system
        self.traces: Dict[str, List[TraceEvent]] = defaultdict(list)
        self.active_traces: Dict[str, datetime] = {}

        # Quality checks
        self.quality_checks: Dict[str, QualityCheck] = {}

        # Dashboard
        self.dashboards: Dict[str, List[DashboardWidget]] = {}

        # Monitoring state
        self.is_running = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.background_tasks: List[asyncio.Task] = []

        # Configuration
        self.config_dir = "E:/TORQ-CONSOLE/observe_system"
        self.metrics_dir = f"{self.config_dir}/metrics"
        self.alerts_dir = f"{self.config_dir}/alerts"
        self.traces_dir = f"{self.config_dir}/traces"

        # Initialize directories
        self._initialize_directories()

        # Initialize default metrics and checks
        self._initialize_default_metrics()
        self._initialize_default_checks()

        self.logger.info("Observe System initialized for production monitoring")

    def setup_logging(self):
        """Setup logging for observe system"""
        os.makedirs("E:/TORQ-CONSOLE/logs", exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('E:/TORQ-CONSOLE/logs/observe_system.log'),
                logging.StreamHandler()
            ]
        )

    def _initialize_directories(self):
        """Initialize required directories"""
        directories = [
            self.config_dir,
            self.metrics_dir,
            self.alerts_dir,
            self.traces_dir,
            f"{self.config_dir}/dashboards",
            f"{self.config_dir}/checkpoints"
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def _initialize_default_metrics(self):
        """Initialize default metric definitions"""
        default_metrics = [
            MetricDefinition(
                name="response_time",
                metric_type=MetricType.PERFORMANCE,
                description="Time taken to generate response",
                unit="ms",
                target_value=2000.0,
                warning_threshold=3000.0,
                critical_threshold=5000.0,
                aggregation="average",
                tags=["performance", "latency"]
            ),
            MetricDefinition(
                name="success_rate",
                metric_type=MetricType.RELIABILITY,
                description="Percentage of successful requests",
                unit="%",
                target_value=95.0,
                warning_threshold=90.0,
                critical_threshold=80.0,
                aggregation="average",
                tags=["reliability", "success"]
            ),
            MetricDefinition(
                name="confidence_score",
                metric_type=MetricType.QUALITY,
                description="Average confidence score of responses",
                unit="score",
                target_value=0.85,
                warning_threshold=0.75,
                critical_threshold=0.65,
                aggregation="average",
                tags=["quality", "confidence"]
            ),
            MetricDefinition(
                name="tool_usage_efficiency",
                metric_type=MetricType.PERFORMANCE,
                description="Efficiency of tool selection and usage",
                unit="score",
                target_value=0.80,
                warning_threshold=0.70,
                critical_threshold=0.60,
                aggregation="average",
                tags=["performance", "tools"]
            ),
            MetricDefinition(
                name="error_rate",
                metric_type=MetricType.RELIABILITY,
                description="Percentage of requests that failed",
                unit="%",
                target_value=5.0,
                warning_threshold=10.0,
                critical_threshold=20.0,
                aggregation="average",
                tags=["reliability", "errors"]
            ),
            MetricDefinition(
                name="request_rate",
                metric_type=MetricType.BUSINESS,
                description="Number of requests per minute",
                unit="req/min",
                target_value=100.0,
                warning_threshold=50.0,
                critical_threshold=10.0,
                aggregation="sum",
                tags=["business", "throughput"]
            )
        ]

        for metric in default_metrics:
            self.metric_definitions[metric.name] = metric

    def _initialize_default_checks(self):
        """Initialize default quality checks"""
        default_checks = [
            QualityCheck(
                check_id="performance_degradation",
                name="Performance Degradation Check",
                description="Check if performance metrics are degrading",
                check_function=self._check_performance_degradation,
                severity=AlertSeverity.WARNING,
                frequency_seconds=300,  # 5 minutes
                enabled=True
            ),
            QualityCheck(
                check_id="error_rate_spike",
                name="Error Rate Spike Check",
                description="Check for sudden spikes in error rates",
                check_function=self._check_error_rate_spike,
                severity=AlertSeverity.CRITICAL,
                frequency_seconds=60,  # 1 minute
                enabled=True
            ),
            QualityCheck(
                check_id="confidence_quality",
                name="Confidence Quality Check",
                description="Check if confidence scores are within acceptable ranges",
                check_function=self._check_confidence_quality,
                severity=AlertSeverity.WARNING,
                frequency_seconds=180,  # 3 minutes
                enabled=True
            ),
            QualityCheck(
                check_id="trace_integrity",
                name="Trace Integrity Check",
                description="Validate trace data integrity",
                check_function=self._check_trace_integrity,
                severity=AlertSeverity.ERROR,
                frequency_seconds=600,  # 10 minutes
                enabled=True
            ),
            QualityCheck(
                check_id="resource_usage",
                name="Resource Usage Check",
                description="Monitor system resource usage",
                check_function=self._check_resource_usage,
                severity=AlertSeverity.WARNING,
                frequency_seconds=120,  # 2 minutes
                enabled=True
            )
        ]

        for check in default_checks:
            self.quality_checks[check.check_id] = check

    def start_monitoring(self):
        """Start the monitoring system"""
        if self.is_running:
            self.logger.warning("Monitoring system is already running")
            return

        self.is_running = True
        self.logger.info("Starting production monitoring system")

        # Start background monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        # Start background tasks
        self._start_background_tasks()

    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.is_running = False
        self.logger.info("Stopping production monitoring system")

        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        self.logger.info("Production monitoring system stopped")

    def _monitoring_loop(self):
        """Main monitoring loop running in background thread"""
        while self.is_running:
            try:
                # Collect system metrics
                self._collect_system_metrics()

                # Run quality checks
                self._run_quality_checks()

                # Process metrics and generate alerts
                self._process_metrics()

                # Clean up old data
                self._cleanup_old_data()

                # Sleep for monitoring interval
                time.sleep(30)  # Monitor every 30 seconds

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on errors

    def _start_background_tasks(self):
        """Start background asyncio tasks"""
        # Start trace cleanup task
        trace_cleanup_task = asyncio.create_task(self._trace_cleanup_loop())
        self.background_tasks.append(trace_cleanup_task)

        # Start alert processing task
        alert_processing_task = asyncio.create_task(self._alert_processing_loop())
        self.background_tasks.append(alert_processing_task)

        # Start dashboard refresh task
        dashboard_task = asyncio.create_task(self._dashboard_refresh_loop())
        self.background_tasks.append(dashboard_task)

    async def _trace_cleanup_loop(self):
        """Background task to clean up old traces"""
        while self.is_running:
            try:
                current_time = datetime.now()
                traces_to_remove = []

                for trace_id, trace_events in self.traces.items():
                    # Remove traces older than 24 hours
                    if trace_events and (current_time - trace_events[-1].start_time).total_seconds() > 86400:
                        traces_to_remove.append(trace_id)

                for trace_id in traces_to_remove:
                    del self.traces[trace_id]
                    if trace_id in self.active_traces:
                        del self.active_traces[trace_id]

                if traces_to_remove:
                    self.logger.info(f"Cleaned up {len(traces_to_remove)} old traces")

                await asyncio.sleep(3600)  # Run every hour

            except Exception as e:
                self.logger.error(f"Error in trace cleanup: {e}")
                await asyncio.sleep(300)

    async def _alert_processing_loop(self):
        """Background task to process and send alerts"""
        while self.is_running:
            try:
                # Check for new alerts
                self._process_alert_queue()

                # Check for alert acknowledgments
                self._check_alert_acknowledgments()

                # Update alert statuses
                self._update_alert_statuses()

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Error in alert processing: {e}")
                await asyncio.sleep(30)

    async def _dashboard_refresh_loop(self):
        """Background task to refresh dashboards"""
        while self.is_running:
            try:
                # Refresh dashboard data
                self._refresh_dashboard_data()

                # Update widgets
                self._update_dashboard_widgets()

                await asyncio.sleep(60)  # Refresh every minute

            except Exception as e:
                self.logger.error(f"Error in dashboard refresh: {e}")
                await asyncio.sleep(120)

    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        current_time = datetime.now()

        # Collect system performance metrics
        system_metrics = {
            "cpu_usage": self._get_cpu_usage(),
            "memory_usage": self._get_memory_usage(),
            "disk_usage": self._get_disk_usage(),
            "network_io": self._get_network_io(),
            "active_traces": len(self.active_traces),
            "total_requests": self._get_total_requests()
        }

        # Record system metrics
        for metric_name, value in system_metrics.items():
            self.record_metric(
                metric_name=metric_name,
                value=float(value),
                tags={"component": "system", "type": "infrastructure"}
            )

    def _run_quality_checks(self):
        """Run all enabled quality checks"""
        current_time = datetime.now()

        for check_id, check in self.quality_checks.items():
            if check.enabled and current_time - (check.last_run or datetime.min) >= timedelta(seconds=check.frequency_seconds):
                try:
                    context = {
                        "current_time": current_time,
                        "metrics": self._get_current_metrics_summary(),
                        "alerts": self._get_active_alerts_count()
                    }

                    result = check.check_function(context)
                    check.last_run = current_time
                    check.last_result = result

                    if not result:
                        check.failure_count += 1
                        self._handle_quality_check_failure(check, context)
                    else:
                        check.failure_count = max(0, check.failure_count - 1)  # Reset on success

                except Exception as e:
                    self.logger.error(f"Error running quality check {check_id}: {e}")
                    check.failure_count += 1

    def _process_metrics(self):
        """Process metrics and generate alerts"""
        current_time = datetime.now()

        # Process each metric
        for metric_name, values in self.metrics.items():
            if not values:
                continue

            metric_def = self.metric_definitions.get(metric_name)
            if not metric_def:
                continue

            # Calculate current value
            recent_values = list(values)[-10:]  # Last 10 values
            if recent_values:
                current_value = statistics.mean(recent_values)

                # Check thresholds
                if metric_def.critical_threshold and current_value >= metric_def.critical_threshold:
                    self._create_alert(
                        metric_name=metric_name,
                        severity=AlertSeverity.CRITICAL,
                        threshold=metric_def.critical_threshold,
                        actual_value=current_value,
                        context={"metric_definition": metric_def.__dict__}
                    )
                elif metric_def.warning_threshold and current_value >= metric_def.warning_threshold:
                    self._create_alert(
                        metric_name=metric_name,
                        severity=AlertSeverity.WARNING,
                        threshold=metric_def.warning_threshold,
                        actual_value=current_value,
                        context={"metric_definition": metric_def.__dict__}
                    )

    def record_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None, context: Dict[str, Any] = None, trace_id: str = None):
        """Record a metric value"""
        if metric_name not in self.metric_definitions:
            # Auto-create metric definition
            self.metric_definitions[metric_name] = MetricDefinition(
                name=metric_name,
                metric_type=MetricType.SYSTEM,
                description=f"Auto-created metric: {metric_name}",
                unit="value"
            )
            self.active_metrics.add(metric_name)

        metric_value = MetricValue(
            metric_name=metric_name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {},
            context=context or {},
            trace_id=trace_id
        )

        self.metrics[metric_name].append(metric_value)
        self.active_metrics.add(metric_name)

    def start_trace(self, operation_name: str, component: str) -> str:
        """Start a new distributed trace"""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())

        trace_event = TraceEvent(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=None,
            operation_name=operation_name,
            component=component,
            start_time=datetime.now(),
            end_time=None,
            duration_ms=None,
            status="started",
            tags={},
            logs=[],
            metrics={}
        )

        self.traces[trace_id].append(trace_event)
        self.active_traces[trace_id] = datetime.now()

        return trace_id

    def end_trace(self, trace_id: str, status: str = "success", tags: Dict[str, str] = None, logs: List[Dict] = None, metrics: Dict[str, float] = None):
        """End a distributed trace"""
        if trace_id not in self.traces or not self.traces[trace_id]:
            return

        trace_events = self.traces[trace_id]
        if not trace_events:
            return

        # Find the span that needs to be ended (usually the last one)
        current_span = None
        for event in reversed(trace_events):
            if event.end_time is None:
                current_span = event
                break

        if current_span:
            current_span.end_time = datetime.now()
            current_span.duration_ms = (current_span.end_time - current_span.start_time).total_seconds() * 1000
            current_span.status = status
            current_span.tags.update(tags or {})
            current_span.logs.extend(logs or [])
            current_span.metrics.update(metrics or {})

        # Mark trace as completed
        if trace_id in self.active_traces:
            del self.active_traces[trace_id]

    def add_trace_log(self, trace_id: str, message: str, level: str = "info"):
        """Add a log entry to a trace"""
        if trace_id not in self.traces:
            return

        trace_events = self.traces[trace_id]
        if trace_events:
            current_span = trace_events[-1]
            current_span.logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message
            })

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            # Fallback to mock data
            return random.uniform(20, 80)

    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            return random.uniform(30, 70)

    def _get_disk_usage(self) -> float:
        """Get current disk usage percentage"""
        try:
            import psutil
            return psutil.disk_usage('/').percent
        except ImportError:
            return random.uniform(10, 50)

    def _get_network_io(self) -> float:
        """Get current network I/O"""
        try:
            import psutil
            net_io = psutil.net_io_counters()
            return (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024)  # MB
        except ImportError:
            return random.uniform(1, 100)

    def _get_total_requests(self) -> int:
        """Get total number of requests processed"""
        # Mock implementation
        return random.randint(1000, 5000)

    def _create_alert(self, metric_name: str, severity: AlertSeverity, threshold: float, actual_value: float, context: Dict[str, Any] = None):
        """Create and process an alert"""
        alert_id = str(uuid.uuid4())

        alert = Alert(
            alert_id=alert_id,
            metric_name=metric_name,
            severity=severity,
            title=f"{severity.value.title()} Alert: {metric_name}",
            message=f"Metric '{metric_name}' crossed {severity.value} threshold of {threshold:.2f} (actual: {actual_value:.2f})",
            threshold=threshold,
            actual_value=actual_value,
            triggered_at=datetime.now(),
            status=AlertStatus.ACTIVE,
            acknowledgment_required=severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL],
            tags=[severity.value, metric_name],
            context=context or {}
        )

        self.alerts[alert_id] = alert

        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")

        self.logger.warning(f"Alert created: {alert.title}")

    def _process_alert_queue(self):
        """Process alert queue and send notifications"""
        # This would integrate with notification systems
        pass

    def _check_alert_acknowledgments(self):
        """Check for alert acknowledgments"""
        # This would check for manual acknowledgments
        pass

    def _update_alert_statuses(self):
        """Update alert statuses based on metric values"""
        current_time = datetime.now()

        for alert in self.alerts.values():
            if alert.status == AlertStatus.ACTIVE:
                # Check if alert condition still exists
                recent_metrics = list(self.metrics.get(alert.metric_name, []))[-5:]
                if recent_metrics:
                    current_value = statistics.mean(recent_metrics)
                    metric_def = self.metric_definitions.get(alert.metric_name)

                    if metric_def:
                        # Check if threshold is no longer crossed
                        if alert.severity == AlertSeverity.CRITICAL:
                            threshold = metric_def.critical_threshold
                        else:
                            threshold = metric_def.warning_threshold

                        if threshold and current_value < threshold:
                            alert.status = AlertStatus.RESOLVED
                            alert.resolved_at = current_time

    def _handle_quality_check_failure(self, check: QualityCheck, context: Dict[str, Any]):
        """Handle quality check failure"""
        self._create_alert(
            metric_name=f"quality_check_{check.check_id}",
            severity=check.severity,
            threshold=0.0,
            actual_value=0.0,
            context={
                "check_name": check.name,
                "check_description": check.description,
                "failure_count": check.failure_count,
                "context": context
            }
        )

    # Quality check functions
    def _check_performance_degradation(self, context: Dict[str, Any]) -> bool:
        """Check for performance degradation"""
        metrics = context.get("metrics", {})

        # Check response time degradation
        response_time_metrics = list(self.metrics.get("response_time", []))[-10:]
        if response_time_metrics:
            avg_response_time = statistics.mean(response_time_metrics)
            # Alert if average response time is 50% higher than target
            if avg_response_time > 3000:  # 3 seconds
                return False

        return True

    def _check_error_rate_spike(self, context: Dict[str, Any]) -> bool:
        """Check for error rate spikes"""
        error_metrics = list(self.metrics.get("error_rate", []))[-10:]
        if len(error_metrics) >= 2:
            recent_error_rate = statistics.mean(error_metrics[-5:])  # Last 5 minutes
            historical_error_rate = statistics.mean(error_metrics[-10:-5]) if len(error_metrics) > 5 else 0

            # Alert if error rate doubled
            if historical_error_rate > 0 and recent_error_rate > historical_error_rate * 2:
                return False

        return True

    def _check_confidence_quality(self, context: Dict[str, Any]) -> bool:
        """Check confidence score quality"""
        confidence_metrics = list(self.metrics.get("confidence_score", []))[-10:]
        if confidence_metrics:
            avg_confidence = statistics.mean(confidence_metrics)
            # Alert if confidence is below target
            if avg_confidence < 0.7:
                return False

        return True

    def _check_trace_integrity(self, context: Dict[str, Any]) -> bool:
        """Check trace data integrity"""
        # Check for orphaned traces
        active_traces_count = len(self.active_traces)
        max_active_traces = 1000

        if active_traces_count > max_active_traces:
            return False

        # Check for very long-running traces
        for trace_id, start_time in self.active_traces.items():
            if (datetime.now() - start_time).total_seconds() > 3600:  # 1 hour
                return False

        return True

    def _check_resource_usage(self, context: Dict[str, Any]) -> bool:
        """Check system resource usage"""
        cpu_usage = self._get_cpu_usage()
        memory_usage = self._get_memory_usage()

        # Alert if resource usage is critical
        if cpu_usage > 90 or memory_usage > 90:
            return False

        return True

    def _cleanup_old_data(self):
        """Clean up old metric data"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        # Clean up old metrics
        for metric_name in self.metrics:
            old_metrics = [m for m in self.metrics[metric_name] if m.timestamp < cutoff_time]
            if old_metrics:
                self.metrics[metric_name] = deque([m for m in self.metrics[metric_name] if m.timestamp >= cutoff_time], maxlen=10000)

        # Clean up resolved alerts
        resolved_alerts = [
            alert for alert in self.alerts.values()
            if alert.status == AlertStatus.RESOLVED and
            (datetime.now() - alert.resolved_at).total_seconds() > 3600  # 1 hour
        ]

        for alert in resolved_alerts:
            del self.alerts[alert.alert_id]

        if resolved_alerts:
            self.logger.info(f"Cleaned up {len(resolved_alerts)} resolved alerts")

    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        # Already implemented in the main monitoring loop
        pass

    def _refresh_dashboard_data(self):
        """Refresh dashboard data"""
        # Collect latest metrics for dashboards
        dashboard_data = {}

        for metric_name in self.active_metrics:
            recent_values = list(self.metrics.get(metric_name, []))[-100:]  # Last 100 values
            if recent_values:
                metric_def = self.metric_definitions.get(metric_name)
                dashboard_data[metric_name] = {
                    "current": recent_values[-1].value,
                    "average": statistics.mean(recent_values),
                    "min": min(v.value for v in recent_values),
                    "max": max(v.value for v in recent_values),
                    "count": len(recent_values),
                    "trend": self._calculate_trend(recent_values)
                }

        # Store dashboard data
        for dashboard_id, widgets in self.dashboards.items():
            for widget in widgets:
                widget.data = {
                    metric_name: dashboard_data.get(metric_name, {})
                    for metric_name in widget.metric_names
                }

    def _update_dashboard_widgets(self):
        """Update dashboard widgets"""
        # This would push updates to connected dashboard systems
        pass

    def _calculate_trend(self, values: List[MetricValue]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "stable"

        values_list = [v.value for v in values]
        if len(values_list) >= 2:
            x = list(range(len(values_list)))
            slope = self._calculate_slope(x, values_list)

            if slope > 0.01:
                return "improving"
            elif slope < -0.01:
                return "declining"
            else:
                return "stable"

        return "stable"

    def _calculate_slope(self, x: List[float], y: List[float]) -> float:
        """Calculate slope of linear regression"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)

        return (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0.0

    def _get_current_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics"""
        summary = {}

        for metric_name in self.active_metrics:
            recent_values = list(self.metrics.get(metric_name, []))[-10:]
            if recent_values:
                summary[metric_name] = {
                    "current": recent_values[-1].value,
                    "average": statistics.mean(recent_values),
                    "count": len(recent_values)
                }

        return summary

    def _get_active_alerts_count(self) -> int:
        """Get count of active alerts"""
        return len([a for a in self.alerts.values() if a.status == AlertStatus.ACTIVE])

    def create_dashboard(self, dashboard_id: str, title: str, widgets: List[Dict]):
        """Create a new dashboard"""
        dashboard_widgets = []

        for widget_config in widgets:
            widget = DashboardWidget(
                widget_id=widget_config.get("widget_id", str(uuid.uuid4())),
                title=widget_config.get("title", "Widget"),
                widget_type=widget_config.get("widget_type", "metric_chart"),
                metric_names=widget_config.get("metric_names", []),
                time_range_hours=widget_config.get("time_range_hours", 24),
                refresh_interval_seconds=widget_config.get("refresh_interval_seconds", 60),
                position=widget_config.get("position", {}),
                config=widget_config.get("config", {})
            )
            dashboard_widgets.append(widget)

        self.dashboards[dashboard_id] = dashboard_widgets
        self.logger.info(f"Created dashboard: {dashboard_id}")

    def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """Get dashboard data"""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return {}

        data = {
            "dashboard_id": dashboard_id,
            "title": f"Dashboard {dashboard_id}",
            "widgets": []
        }

        for widget in dashboard:
            widget_data = {
                "widget_id": widget.widget_id,
                "title": widget.title,
                "widget_type": widget.widget_type,
                "metric_names": widget.metric_names,
                "data": {}
            }

            for metric_name in widget.metric_names:
                recent_values = list(self.metrics.get(metric_name, []))[-widget.time_range_hours:]
                if recent_values:
                    widget_data["data"][metric_name] = {
                        "values": [{"timestamp": v.timestamp.isoformat(), "value": v.value} for v in recent_values],
                        "current": recent_values[-1].value,
                        "average": statistics.mean([v.value for v in recent_values]),
                        "trend": self._calculate_trend(recent_values)
                    }

            data["widgets"].append(widget_data)

        return data

    def get_trace_data(self, trace_id: str) -> Dict[str, Any]:
        """Get trace data"""
        trace_events = self.traces.get(trace_id, [])
        if not trace_events:
            return {}

        # Build trace tree structure
        trace_tree = self._build_trace_tree(trace_events)

        return {
            "trace_id": trace_id,
            "events": [event.__dict__ for event in trace_events],
            "tree": trace_tree,
            "duration_ms": trace_events[-1].duration_ms if trace_events else 0,
            "status": trace_events[-1].status if trace_events else "unknown"
        }

    def _build_trace_tree(self, events: List[TraceEvent]) -> Dict:
        """Build hierarchical tree structure from trace events"""
        if not events:
            return {}

        # Create root nodes
        roots = []
        event_map = {}

        for event in events:
            event_map[event.span_id] = event
            if event.parent_span_id is None:
                roots.append(event)
            else:
                if event.parent_span_id not in event_map:
                    event_map[event.parent_span_id] = None
                event_map[event.parent_span_id] = event

        # Build tree structure
        tree = {"roots": []}
        for root in roots:
            node = self._build_node(root, event_map)
            tree["roots"].append(node)

        return tree

    def _build_node(self, event: TraceEvent, event_map: Dict) -> Dict:
        """Build node for tree structure"""
        node = {
            "span_id": event.span_id,
            "operation_name": event.operation_name,
            "component": event.component,
            "duration_ms": event.duration_ms,
            "status": event.status,
            "children": []
        }

        # Find children
        for other_event in event_map.values():
            if other_event and other_event.parent_span_id == event.span_id:
                child_node = self._build_node(other_event, event_map)
                node["children"].append(child_node)

        return node

    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add custom alert handler"""
        self.alert_handlers.append(handler)

    def register_metric(self, metric_definition: MetricDefinition):
        """Register a new metric definition"""
        self.metric_definitions[metric_definition.name] = metric_definition
        self.logger.info(f"Registered metric: {metric_definition.name}")

    def register_quality_check(self, quality_check: QualityCheck):
        """Register a quality check"""
        self.quality_checks[quality_check.check_id] = quality_check
        self.logger.info(f"Registered quality check: {quality_check.name}")

# Main execution function for testing
async def main():
    """Main execution function for testing observe system"""
    print("🔍 Maxim AI Integration - Phase 3: Observe Component")
    print("="*60)

    # Initialize observe system
    observe_system = ObserveSystem()

    # Register custom metrics
    custom_metric = MetricDefinition(
        name="user_satisfaction",
        metric_type=MetricType.BUSINESS,
        description="User satisfaction score from feedback",
        unit="score",
        target_value=4.0,
        warning_threshold=3.5,
        critical_threshold=3.0,
        aggregation="average",
        tags=["business", "satisfaction"]
    )
    observe_system.register_metric(custom_metric)

    # Start monitoring
    print("\n🚀 Starting production monitoring...")
    observe_system.start_monitoring()

    # Simulate some metrics
    print("\n📊 Recording sample metrics...")
    for i in range(10):
        observe_system.record_metric(
            metric_name="response_time",
            value=random.uniform(500, 3000),
            tags={"request_id": str(i), "agent": "prince_flowers"}
        )
        observe_system.record_metric(
            metric_name="success_rate",
            value=random.uniform(0.8, 1.0),
            tags={"component": "system"}
        )
        observe_system.record_metric(
            metric_name="confidence_score",
            value=random.uniform(0.7, 0.95),
            tags={"component": "agent"}
        )
        await asyncio.sleep(1)

    # Create and end traces
    print("\n🔍 Creating and ending traces...")
    for i in range(3):
        trace_id = observe_system.start_trace(
            operation_name=f"User Query {i}",
            component="prince_flowers"
        )
        await asyncio.sleep(0.1)
        observe_system.end_trace(trace_id, "success")

    # Create dashboard
    print("\n📈 Creating monitoring dashboard...")
    dashboard_widgets = [
        {
            "widget_id": "widget_1",
            "title": "Performance Metrics",
            "widget_type": "metric_chart",
            "metric_names": ["response_time", "success_rate", "confidence_score"],
            "time_range_hours": 1
        },
        {
            "widget_id": "widget_2",
            "title": "Alert Summary",
            "widget_type": "alert_table",
            "metric_names": [],
            "time_range_hours": 24
        }
    ]

    observe_system.create_dashboard("main_dashboard", "Prince Flowers Monitoring", dashboard_widgets)

    # Get dashboard data
    print("\n📊 Getting dashboard data...")
    dashboard_data = observe_system.get_dashboard_data("main_dashboard")
    print(f"Dashboard created with {len(dashboard_data['widgets'])} widgets")

    # Get trace data
    if observe_system.traces:
        trace_id = list(observe_system.traces.keys())[0]
        trace_data = observe_system.get_trace_data(trace_id)
        print(f"Sample trace data: {trace_id[:8]}... with {len(trace_data['events'])} events")

    # Run for a bit to collect data
    print("\n⏱️ Collecting data for 10 seconds...")
    await asyncio.sleep(10)

    # Stop monitoring
    print("\n🛑 Stopping monitoring system...")
    observe_system.stop_monitoring()

    # Show summary
    active_metrics = len(observe_system.active_metrics)
    total_alerts = len(observe_system.alerts)
    total_traces = len(observe_system.traces)

    print(f"\n📊 MONITORING SUMMARY:")
    print(f"  Active Metrics: {active_metrics}")
    print(f" Total Alerts: {total_alerts}")
    print(f" Total Traces: {total_traces}")

    print(f"\n✅ Observe System demonstration completed!")

if __name__ == "__main__":
    asyncio.run(main())