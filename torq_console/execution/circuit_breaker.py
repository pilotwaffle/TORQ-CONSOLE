"""
Circuit Breaker and Connector Health Monitoring

Phase 8 Hardening: Production-grade resilience for external connectors.

Implements the circuit breaker pattern to prevent cascading failures and
provide graceful degradation when connectors are unhealthy.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


logger = __import__("logging").getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class CircuitState(str, Enum):
    """States of the circuit breaker."""
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Circuit is tripped, requests fail fast
    HALF_OPEN = "half_open"  # Testing if connector has recovered


class HealthStatus(str, Enum):
    """Health status of a connector."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# ============================================================================
# Circuit Breaker Configuration
# ============================================================================

class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker behavior."""
    # Failure threshold
    failure_threshold: int = 5  # Open circuit after N failures
    success_threshold: int = 2  # Close circuit after N successes in half-open

    # Timeouts
    open_timeout_seconds: float = 60.0  # How long to stay open before half-open
    half_open_timeout_seconds: float = 30.0  # How long to wait in half-open

    # Rolling window
    window_size_seconds: float = 60.0  # Time window for counting failures

    # Health check
    health_check_interval_seconds: float = 30.0
    health_check_timeout_seconds: float = 5.0


# ============================================================================
# Circuit Breaker State
# ============================================================================

@dataclass
class CircuitBreakerState:
    """Runtime state of the circuit breaker."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)
    opened_at: Optional[float] = None

    # Failure window (for rolling count)
    failures_in_window: List[float] = field(default_factory=list)

    def record_failure(self) -> None:
        """Record a failure."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.failures_in_window.append(time.time())

    def record_success(self) -> None:
        """Record a success."""
        self.success_count += 1
        self.last_success_time = time.time()

    def get_recent_failures(self, window_seconds: float) -> int:
        """Get failures within the time window."""
        cutoff = time.time() - window_seconds
        return len([t for t in self.failures_in_window if t > cutoff])

    def clear_old_failures(self, window_seconds: float) -> None:
        """Clear failures outside the time window."""
        cutoff = time.time() - window_seconds
        self.failures_in_window = [t for t in self.failures_in_window if t > cutoff]


# ============================================================================
# Circuit Breaker
# ============================================================================

class CircuitBreaker:
    """
    Circuit breaker for protecting against failing connectors.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit tripped, requests fail fast immediately
    - HALF_OPEN: Testing if service has recovered

    Transitions:
    CLOSED -> OPEN: When failure threshold is reached
    OPEN -> HALF_OPEN: After open timeout expires
    HALF_OPEN -> CLOSED: When success threshold is reached
    HALF_OPEN -> OPEN: On any failure
    """

    def __init__(
        self,
        connector_id: str,
        connector_type: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        self.connector_id = connector_id
        self.connector_type = connector_type
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitBreakerState()
        self._lock = asyncio.Lock()

        self.logger = logger

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state.state

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self._state.state == CircuitState.OPEN

    @property
    def can_execute(self) -> bool:
        """Check if execution is allowed through circuit."""
        return self._state.state != CircuitState.OPEN

    async def execute(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitOpenError: If circuit is open
        """
        async with self._lock:
            # Check if circuit is open
            if self._state.state == CircuitState.OPEN:
                # Check if we should transition to half-open
                if self._should_transition_to_half_open():
                    self._transition_to_half_open()
                else:
                    raise CircuitOpenError(
                        f"Circuit is open for {self.connector_type} connector {self.connector_id}"
                    )

        # Execute the function
        try:
            result = await func(*args, **kwargs)

            # Record success
            async with self._lock:
                self._state.record_success()

                if self._state.state == CircuitState.HALF_OPEN:
                    if self._state.success_count >= self.config.success_threshold:
                        self._transition_to_closed()

            return result

        except Exception as e:
            # Record failure
            async with self._lock:
                self._state.record_failure()
                self._state.clear_old_failures(self.config.window_size_seconds)

                # Check if we should open the circuit
                if self._state.get_recent_failures(self.config.window_size_seconds) >= self.config.failure_threshold:
                    if self._state.state != CircuitState.OPEN:
                        self._transition_to_open()

            raise

    def _should_transition_to_half_open(self) -> bool:
        """Check if circuit should transition to half-open."""
        if self._state.state != CircuitState.OPEN:
            return False

        if self._state.opened_at is None:
            return False

        return (time.time() - self._state.opened_at) >= self.config.open_timeout_seconds

    def _transition_to_open(self) -> None:
        """Transition circuit to open state."""
        old_state = self._state.state
        self._state.state = CircuitState.OPEN
        self._state.opened_at = time.time()
        self._state.last_state_change = time.time()
        self._state.success_count = 0  # Reset success count

        self.logger.warning(
            f"Circuit opened for {self.connector_type} connector {self.connector_id} "
            f"({self._state.get_recent_failures(self.config.window_size_seconds)} failures)"
        )

    def _transition_to_half_open(self) -> None:
        """Transition circuit to half-open state."""
        self._state.state = CircuitState.HALF_OPEN
        self._state.last_state_change = time.time()

        self.logger.info(
            f"Circuit half-open for {self.connector_type} connector {self.connector_id}"
        )

    def _transition_to_closed(self) -> None:
        """Transition circuit to closed state."""
        self._state.state = CircuitState.CLOSED
        self._state.last_state_change = time.time()
        self._state.failure_count = 0
        self._state.failures_in_window.clear()

        self.logger.info(
            f"Circuit closed for {self.connector_type} connector {self.connector_id}"
        )

    def get_state_info(self) -> Dict[str, Any]:
        """Get circuit breaker state info."""
        return {
            "connector_id": self.connector_id,
            "connector_type": self.connector_type,
            "state": self._state.state,
            "failure_count": self._state.failure_count,
            "success_count": self._state.success_count,
            "recent_failures": self._state.get_recent_failures(self.config.window_size_seconds),
            "last_failure_time": self._state.last_failure_time,
            "last_success_time": self._state.last_success_time,
            "last_state_change": self._state.last_state_change,
            "opened_at": self._state.opened_at,
        }


class CircuitOpenError(Exception):
    """Raised when attempting to execute through an open circuit."""
    pass


# ============================================================================
# Health Monitor
# ============================================================================

class ConnectorHealthMonitor(BaseModel):
    """Health monitoring data for a connector."""
    connector_id: str
    connector_type: str

    # Health status
    status: HealthStatus = HealthStatus.UNKNOWN
    last_check: Optional[float] = None
    last_check_duration_ms: Optional[float] = None

    # Statistics
    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    consecutive_failures: int = 0

    # Response times
    avg_response_time_ms: float = 0.0
    min_response_time_ms: Optional[float] = None
    max_response_time_ms: Optional[float] = None

    # Circuit breaker
    circuit_state: CircuitState = CircuitState.CLOSED
    circuit_open_since: Optional[float] = None

    # Error tracking
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None

    # Timestamp
    updated_at: float = Field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        """Calculate success rate of health checks."""
        if self.total_checks == 0:
            return 0.0
        return self.successful_checks / self.total_checks

    @property
    def is_healthy(self) -> bool:
        """Check if connector is considered healthy."""
        return self.status == HealthStatus.HEALTHY


class HealthMonitor:
    """
    Monitors health of all connectors.

    Provides:
    - Regular health checks
    - Response time tracking
    - Error aggregation
    - Health status reporting
    """

    def __init__(self):
        self._health: Dict[str, ConnectorHealthMonitor] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None

        self.logger = logger

    async def start(self, check_interval: float = 30.0) -> None:
        """Start the health monitor."""
        if self._running:
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(check_interval))
        self.logger.info("Health monitor started")

    async def stop(self) -> None:
        """Stop the health monitor."""
        self._running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Health monitor stopped")

    async def _monitor_loop(self, check_interval: float) -> None:
        """Background loop for health checks."""
        while self._running:
            try:
                await self._check_all_connectors()
                await asyncio.sleep(check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {e}")

    async def _check_all_connectors(self) -> None:
        """Check health of all monitored connectors."""
        for connector_id, health in self._health.items():
            try:
                await self._check_connector_health(connector_id)
            except Exception as e:
                self.logger.error(f"Error checking connector {connector_id}: {e}")

    async def _check_connector_health(self, connector_id: str) -> None:
        """Check health of a specific connector."""
        health = self._health.get(connector_id)
        if not health:
            return

        circuit_breaker = self._circuit_breakers.get(connector_id)

        start_time = time.time()

        try:
            # If circuit is open, skip health check
            if circuit_breaker and circuit_breaker.is_open:
                health.status = HealthStatus.UNHEALTHY
                health.circuit_state = CircuitState.OPEN
                health.circuit_open_since = circuit_breaker._state.opened_at
                health.last_check = time.time()
                return

            # Perform health check
            # In production, this would call the connector's health_check method
            # For now, simulate based on circuit state
            if circuit_breaker:
                state_info = circuit_breaker.get_state_info()
                health.circuit_state = state_info["state"]
                health.circuit_open_since = state_info.get("opened_at")

                if state_info["state"] == CircuitState.CLOSED:
                    health.status = HealthStatus.HEALTHY
                else:
                    health.status = HealthStatus.UNHEALTHY

            duration_ms = (time.time() - start_time) * 1000

            # Update statistics
            health.total_checks += 1
            health.successful_checks += 1
            health.consecutive_failures = 0
            health.last_check = time.time()
            health.last_check_duration_ms = duration_ms

            # Update response times
            health.avg_response_time_ms = (
                (health.avg_response_time_ms * (health.total_checks - 1) + duration_ms)
                / health.total_checks
            )

            if health.min_response_time_ms is None or duration_ms < health.min_response_time_ms:
                health.min_response_time_ms = duration_ms

            if health.max_response_time_ms is None or duration_ms > health.max_response_time_ms:
                health.max_response_time_ms = duration_ms

        except Exception as e:
            health.total_checks += 1
            health.failed_checks += 1
            health.consecutive_failures += 1
            health.last_error = str(e)
            health.last_error_time = time.time()
            health.last_check = time.time()
            health.status = HealthStatus.UNHEALTHY

        health.updated_at = time.time()

    def register_connector(
        self,
        connector_id: str,
        connector_type: str,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    ) -> None:
        """Register a connector for monitoring."""
        # Create health monitor
        self._health[connector_id] = ConnectorHealthMonitor(
            connector_id=connector_id,
            connector_type=connector_type
        )

        # Create circuit breaker
        self._circuit_breakers[connector_id] = CircuitBreaker(
            connector_id=connector_id,
            connector_type=connector_type,
            config=circuit_breaker_config
        )

        self.logger.info(f"Registered connector for monitoring: {connector_id}")

    def unregister_connector(self, connector_id: str) -> None:
        """Unregister a connector from monitoring."""
        self._health.pop(connector_id, None)
        self._circuit_breakers.pop(connector_id, None)
        self.logger.info(f"Unregistered connector: {connector_id}")

    def get_health(self, connector_id: str) -> Optional[ConnectorHealthMonitor]:
        """Get health data for a connector."""
        return self._health.get(connector_id)

    def get_circuit_breaker(self, connector_id: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker for a connector."""
        return self._circuit_breakers.get(connector_id)

    def get_all_health(self) -> List[ConnectorHealthMonitor]:
        """Get health data for all connectors."""
        return list(self._health.values())

    def get_unhealthy_connectors(self) -> List[ConnectorHealthMonitor]:
        """Get list of unhealthy connectors."""
        return [
            h for h in self._health.values()
            if h.status != HealthStatus.HEALTHY
        ]

    def get_summary(self) -> Dict[str, Any]:
        """Get health monitor summary."""
        health_list = list(self._health.values())

        healthy = sum(1 for h in health_list if h.status == HealthStatus.HEALTHY)
        degraded = sum(1 for h in health_list if h.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for h in health_list if h.status == HealthStatus.UNHEALTHY)

        open_circuits = sum(
            1 for cb in self._circuit_breakers.values()
            if cb.state == CircuitState.OPEN
        )

        return {
            "total_connectors": len(health_list),
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "open_circuits": open_circuits,
            "is_running": self._running,
        }


# ============================================================================
# Singleton
# ============================================================================

_global_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = HealthMonitor()
    return _global_monitor


# Export
__all__ = [
    'CircuitState',
    'HealthStatus',
    'CircuitBreakerConfig',
    'CircuitBreakerState',
    'CircuitBreaker',
    'CircuitOpenError',
    'ConnectorHealthMonitor',
    'HealthMonitor',
    'get_health_monitor',
]
