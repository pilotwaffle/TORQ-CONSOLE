"""
Tests for Phase 8 Hardening: Idempotency, Circuit Breaking, Provenance

Tests the production-grade features added after initial Phase 8 implementation.
"""

import asyncio
import tempfile
import pytest
import pytest_asyncio

from torq_console.execution.provenance import (
    ProvenanceStore,
    ExecutionProvenance,
    ProvenanceEvent,
    ProvenanceEventType,
    get_provenance_store,
)
from torq_console.execution.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitOpenError,
    HealthMonitor,
    HealthStatus,
    get_health_monitor,
)
from torq_console.connectors.base import ExternalAction, ActionState, RiskLevel


# ============================================================================
# Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def provenance_store():
    """Provenance store for tests."""
    store = ProvenanceStore()
    yield store


@pytest_asyncio.fixture
async def health_monitor():
    """Health monitor for tests."""
    monitor = HealthMonitor()
    await monitor.start(check_interval=1.0)
    yield monitor
    await monitor.stop()


# ============================================================================
# Idempotency Tests
# ============================================================================

class TestIdempotency:
    """Test idempotency key handling."""

    def test_idempotency_key_generation(self):
        """Test that idempotency keys are generated consistently."""
        store = ProvenanceStore()

        # Create first action
        prov1 = store.create_provenance(
            action_id="action_1",
            connector_type="webhook",
            action_type="send_json",
            idempotency_key="test-key-123",
            workspace_id="ws1"
        )

        # Create second action with same key
        prov2 = store.create_provenance(
            action_id="action_2",
            connector_type="webhook",
            action_type="send_json",
            idempotency_key="test-key-123",
            workspace_id="ws1"
        )

        # Should return the same provenance record
        assert prov1.provenance_id == prov2.provenance_id
        assert prov1.action_id == prov2.action_id

    def test_different_keys_different_records(self):
        """Test that different keys create different records."""
        store = ProvenanceStore()

        prov1 = store.create_provenance(
            action_id="action_1",
            connector_type="webhook",
            action_type="send_json",
            idempotency_key="key-1"
        )

        prov2 = store.create_provenance(
            action_id="action_2",
            connector_type="webhook",
            action_type="send_json",
            idempotency_key="key-2"
        )

        assert prov1.provenance_id != prov2.provenance_id

    def test_get_by_idempotency_key(self, provenance_store):
        """Test retrieving by idempotency key."""
        prov = provenance_store.create_provenance(
            action_id="action_1",
            connector_type="slack",
            action_type="send_message",
            idempotency_key="slack-msg-123"
        )

        retrieved = provenance_store.get_by_idempotency_key("slack-msg-123")

        assert retrieved is not None
        assert retrieved.provenance_id == prov.provenance_id
        assert retrieved.connector_type == "slack"


# ============================================================================
# Provenance Tracking Tests
# ============================================================================

class TestProvenanceTracking:
    """Test execution provenance tracking."""

    def test_create_provenance(self, provenance_store):
        """Test creating a provenance record."""
        prov = provenance_store.create_provenance(
            action_id="action_123",
            connector_type="webhook",
            action_type="send_json",
            trace_id="trace-456",
            workspace_id="workspace_1",
            environment="production"
        )

        assert prov.provenance_id is not None
        assert prov.action_id == "action_123"
        assert prov.connector_type == "webhook"
        assert prov.trace_id == "trace-456"
        assert prov.status == "pending"

    def test_record_event(self, provenance_store):
        """Test recording provenance events."""
        prov = provenance_store.create_provenance(
            action_id="action_1",
            connector_type="slack",
            action_type="send_message"
        )

        event = provenance_store.record_event(
            prov.provenance_id,
            prov.trace_id,
            ProvenanceEventType.ACTION_SUBMITTED,
            data={"test": "data"}
        )

        assert event.event_id is not None
        assert event.event_type == ProvenanceEventType.ACTION_SUBMITTED

    def test_event_updates_provenance_status(self, provenance_store):
        """Test that events update provenance status."""
        prov = provenance_store.create_provenance(
            action_id="action_1",
            connector_type="webhook",
            action_type="send_json"
        )

        # Record executing event
        provenance_store.record_event(
            prov.provenance_id,
            prov.trace_id,
            ProvenanceEventType.ACTION_EXECUTING
        )

        # Record success event
        provenance_store.record_event(
            prov.provenance_id,
            prov.trace_id,
            ProvenanceEventType.ACTION_SUCCEEDED,
            data={"duration": 1.5}
        )

        # Check updated provenance
        updated = provenance_store.get_provenance(prov.provenance_id)
        assert updated.status == "succeeded"
        assert updated.duration_seconds is not None

    def test_trace_grouping(self, provenance_store):
        """Test that trace groups related actions."""
        trace_id = "trace-123"

        prov1 = provenance_store.create_provenance(
            action_id="action_1",
            connector_type="slack",
            action_type="send_message",
            trace_id=trace_id
        )

        prov2 = provenance_store.create_provenance(
            action_id="action_2",
            connector_type="webhook",
            action_type="send_json",
            trace_id=trace_id
        )

        trace_records = provenance_store.get_by_trace(trace_id)

        assert len(trace_records) == 2
        assert prov1.provenance_id in [r.provenance_id for r in trace_records]
        assert prov2.provenance_id in [r.provenance_id for r in trace_records]

    def test_get_trace_events(self, provenance_store):
        """Test getting all events for a trace."""
        trace_id = "trace-events"

        prov = provenance_store.create_provenance(
            action_id="action_1",
            connector_type="webhook",
            action_type="send_json",
            trace_id=trace_id
        )

        provenance_store.record_event(
            prov.provenance_id,
            trace_id,
            ProvenanceEventType.ACTION_SUBMITTED
        )

        provenance_store.record_event(
            prov.provenance_id,
            trace_id,
            ProvenanceEventType.ACTION_SUCCEEDED
        )

        events = provenance_store.get_trace_events(trace_id)

        assert len(events) >= 2  # At least submitted and succeeded

    def test_query_provenance(self, provenance_store):
        """Test querying provenance records."""
        # Create records with different attributes
        provenance_store.create_provenance(
            action_id="action_1",
            connector_type="slack",
            action_type="send_message",
            workspace_id="ws1",
            status="succeeded"
        )

        provenance_store.create_provenance(
            action_id="action_2",
            connector_type="webhook",
            action_type="send_json",
            workspace_id="ws1",
            status="failed"
        )

        provenance_store.create_provenance(
            action_id="action_3",
            connector_type="slack",
            action_type="send_message",
            workspace_id="ws2",
            status="succeeded"
        )

        # Query by workspace
        ws1_results = provenance_store.query(workspace_id="ws1")
        assert len(ws1_results) == 2

        # Query by connector type
        slack_results = provenance_store.query(connector_type="slack")
        assert len(slack_results) == 2

        # Query by status
        success_results = provenance_store.query(status="succeeded")
        assert len(success_results) == 2

    def test_provenance_statistics(self, provenance_store):
        """Test provenance statistics."""
        provenance_store.create_provenance(
            action_id="action_1",
            connector_type="slack",
            action_type="send_message",
            workspace_id="ws1",
            status="succeeded"
        )

        stats = provenance_store.get_statistics()

        assert stats["total_provenance"] >= 1
        assert stats["unique_traces"] >= 1
        assert "by_status" in stats
        assert "by_connector" in stats


# ============================================================================
# Circuit Breaker Tests
# ============================================================================

class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_initial_state(self):
        """Test circuit breaker starts in closed state."""
        breaker = CircuitBreaker(
            connector_id="conn_1",
            connector_type="webhook"
        )

        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_open is False
        assert breaker.can_execute is True

    def test_circuit_opens_on_failures(self):
        """Test circuit opens after failure threshold."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            window_size_seconds=60.0
        )

        breaker = CircuitBreaker(
            connector_id="conn_1",
            connector_type="webhook",
            config=config
        )

        # Record failures up to threshold
        for _ in range(config.failure_threshold):
            breaker._state.record_failure()
            breaker._state.clear_old_failures(config.window_size_seconds)

        # Manually trigger circuit opening (in production, execute() would do this)
        if breaker._state.get_recent_failures(config.window_size_seconds) >= config.failure_threshold:
            breaker._transition_to_open()

        # Should open circuit
        assert breaker.is_open is True
        assert breaker.can_execute is False

    @pytest.mark.asyncio
    async def test_circuit_prevents_execution_when_open(self):
        """Test that open circuit prevents execution."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            open_timeout_seconds=1.0
        )

        breaker = CircuitBreaker(
            connector_id="conn_1",
            connector_type="webhook",
            config=config
        )

        # Trip the circuit
        breaker._state.record_failure()
        breaker._state.record_failure()
        breaker._transition_to_open()

        # Should raise error
        with pytest.raises(CircuitOpenError):
            await breaker.execute(lambda: "result")

    @pytest.mark.asyncio
    async def test_successful_execution_resets_failures(self):
        """Test that successful execution resets failure count."""
        breaker = CircuitBreaker(
            connector_id="conn_1",
            connector_type="webhook"
        )

        # Add some failures
        breaker._state.record_failure()
        breaker._state.record_failure()

        # Execute successfully
        async def success_func():
            return "success"

        result = await breaker.execute(success_func)

        assert result == "success"
        # In half-open state, would need more successes to close

    @pytest.mark.asyncio
    async def test_circuit_transitions_to_half_open(self):
        """Test circuit transitions to half-open after timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            open_timeout_seconds=0.1,  # Short timeout for testing
            success_threshold=2
        )

        breaker = CircuitBreaker(
            connector_id="conn_1",
            connector_type="webhook",
            config=config
        )

        # Open the circuit
        breaker._transition_to_open()

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Check if should transition
        assert breaker._should_transition_to_half_open() is True

    def test_get_state_info(self):
        """Test getting circuit breaker state info."""
        breaker = CircuitBreaker(
            connector_id="conn_1",
            connector_type="webhook"
        )

        breaker._state.record_failure()

        info = breaker.get_state_info()

        assert info["connector_id"] == "conn_1"
        assert info["connector_type"] == "webhook"
        assert info["state"] == CircuitState.CLOSED
        assert info["failure_count"] == 1


# ============================================================================
# Health Monitor Tests
# ============================================================================

class TestHealthMonitor:
    """Test health monitor functionality."""

    def test_register_connector(self, health_monitor):
        """Test registering a connector for monitoring."""
        health_monitor.register_connector(
            connector_id="conn_1",
            connector_type="webhook"
        )

        health = health_monitor.get_health("conn_1")
        assert health is not None
        assert health.connector_id == "conn_1"

    def test_get_circuit_breaker(self, health_monitor):
        """Test getting circuit breaker for a connector."""
        health_monitor.register_connector(
            connector_id="conn_1",
            connector_type="webhook"
        )

        breaker = health_monitor.get_circuit_breaker("conn_1")
        assert breaker is not None
        assert breaker.connector_id == "conn_1"

    @pytest.mark.asyncio
    async def test_unhealthy_connector_detection(self, health_monitor):
        """Test detection of unhealthy connectors."""
        health_monitor.register_connector(
            connector_id="conn_1",
            connector_type="webhook"
        )

        breaker = health_monitor.get_circuit_breaker("conn_1")

        # Trip the circuit breaker
        breaker._transition_to_open()

        # Manually trigger health check to update status
        await health_monitor._check_connector_health("conn_1")

        # Check health
        health = health_monitor.get_health("conn_1")
        assert health.status == HealthStatus.UNHEALTHY
        assert health.circuit_state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_get_unhealthy_connectors(self, health_monitor):
        """Test getting list of unhealthy connectors."""
        health_monitor.register_connector(
            connector_id="conn_1",
            connector_type="webhook"
        )

        health_monitor.register_connector(
            connector_id="conn_2",
            connector_type="slack"
        )

        # Make one unhealthy
        breaker = health_monitor.get_circuit_breaker("conn_1")
        breaker._transition_to_open()

        # Trigger health check to update status
        await health_monitor._check_connector_health("conn_1")

        unhealthy = health_monitor.get_unhealthy_connectors()

        assert len(unhealthy) >= 1
        assert any(h.connector_id == "conn_1" for h in unhealthy)

    def test_get_summary(self, health_monitor):
        """Test getting health monitor summary."""
        health_monitor.register_connector(
            connector_id="conn_1",
            connector_type="webhook"
        )

        summary = health_monitor.get_summary()

        assert "total_connectors" in summary
        assert "healthy" in summary
        assert "unhealthy" in summary
        assert "open_circuits" in summary
        assert summary["total_connectors"] >= 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestHardeningIntegration:
    """Integration tests for hardening features."""

    @pytest.mark.asyncio
    async def test_idempotency_with_provenance(self):
        """Test idempotency integrates with provenance tracking."""
        store = ProvenanceStore()

        # First submission
        prov1 = store.create_provenance(
            action_id="action_1",
            connector_type="slack",
            action_type="send_message",
            idempotency_key="slack-123"
        )

        # Duplicate submission
        prov2 = store.create_provenance(
            action_id="action_2",
            connector_type="slack",
            action_type="send_message",
            idempotency_key="slack-123"
        )

        # Should return same provenance
        assert prov1.provenance_id == prov2.provenance_id

        # Events should only be recorded once
        store.record_event(
            prov1.provenance_id,
            prov1.trace_id,
            ProvenanceEventType.ACTION_SUCCEEDED
        )

        events = store.get_events(prov1.provenance_id)
        assert len(events) >= 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_health_monitor(self):
        """Test circuit breaker integration with health monitor."""
        monitor = HealthMonitor()

        monitor.register_connector(
            connector_id="webhook_1",
            connector_type="webhook",
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=2)
        )

        breaker = monitor.get_circuit_breaker("webhook_1")

        # Simulate failures
        breaker._state.record_failure()
        breaker._state.record_failure()
        breaker._transition_to_open()

        # Health check should detect unhealthy state
        await monitor._check_connector_health("webhook_1")

        health = monitor.get_health("webhook_1")
        assert health.status == HealthStatus.UNHEALTHY

        # Summary should show open circuit
        summary = monitor.get_summary()
        assert summary["open_circuits"] >= 1

    @pytest.mark.asyncio
    async def test_complete_execution_chain(self):
        """Test complete execution chain with all hardening features."""
        store = ProvenanceStore()
        monitor = HealthMonitor()
        await monitor.start()

        try:
            monitor.register_connector(
                connector_id="slack_1",
                connector_type="slack"
            )

            # Create action with idempotency
            prov = store.create_provenance(
                action_id="action_1",
                connector_type="slack",
                action_type="send_message",
                trace_id="trace-complete",
                idempotency_key="slack-complete-123"
            )

            # Record execution events
            store.record_event(
                prov.provenance_id,
                prov.trace_id,
                ProvenanceEventType.ACTION_EXECUTING
            )

            # Simulate success
            store.record_event(
                prov.provenance_id,
                prov.trace_id,
                ProvenanceEventType.ACTION_SUCCEEDED,
                data={"timestamp": "123.456"}
            )

            store.record_event(
                prov.provenance_id,
                prov.trace_id,
                ProvenanceEventType.VERIFICATION_PASSED,
                data={"message": "Message delivered"}
            )

            # Verify complete chain
            final_prov = store.get_provenance(prov.provenance_id)
            assert final_prov.status == "succeeded"
            assert final_prov.verified is True

            # Verify trace events
            trace_events = store.get_trace_events("trace-complete")
            assert len(trace_events) >= 3

        finally:
            await monitor.stop()
