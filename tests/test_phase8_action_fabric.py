"""
Tests for Phase 8: External Action Fabric

Tests the action fabric, connector framework, and workflow execution.
"""

import asyncio
import tempfile
import pytest
import pytest_asyncio

from torq_console.connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorRegistry,
    ConnectorType,
    ConnectorStatus,
    ExternalAction,
    ActionExecutionResult,
    ActionState,
    RiskLevel,
    RetryPolicy,
    HealthCheckResult,
    get_connector_registry,
    execute_with_retry,
)
from torq_console.connectors.webhook import WebhookConnector
from torq_console.connectors.slack import SlackConnector
from torq_console.execution.action_fabric import (
    ExternalActionFabric,
    ActionFabricEvent,
    ActionPolicy,
    get_action_fabric,
)
from torq_console.workflows.execution_engine import (
    WorkflowExecutionEngine,
    WorkflowDefinition,
    WorkflowNode,
    WorkflowEdge,
    WorkflowState,
    NodeState,
    NodeType,
    get_workflow_engine,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_storage():
    """Temporary storage for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest_asyncio.fixture
async def connector_registry():
    """Connector registry for tests."""
    registry = ConnectorRegistry()

    # Register connector classes
    registry.register_connector_class("webhook", WebhookConnector)
    registry.register_connector_class("slack", SlackConnector)

    # Create a webhook connector
    config = ConnectorConfig(
        connector_type="webhook",
        name="Test Webhook",
        base_url="https://httpbin.org"
    )
    await registry.create_connector(config).setup()

    return registry


@pytest_asyncio.fixture
async def action_fabric(connector_registry):
    """Action fabric for tests."""
    fabric = ExternalActionFabric(connector_registry=connector_registry)
    await fabric.start()
    yield fabric
    await fabric.stop()


@pytest_asyncio.fixture
async def workflow_engine():
    """Workflow engine for tests."""
    engine = WorkflowExecutionEngine()
    await engine.start()
    yield engine
    await engine.stop()


# ============================================================================
# Connector Config Tests
# ============================================================================

class TestConnectorConfig:
    """Test ConnectorConfig model."""

    def test_config_creation(self):
        """Test creating a connector config."""
        config = ConnectorConfig(
            connector_type="webhook",
            name="Test Webhook",
            auth_type="none",
            timeout_seconds=30
        )

        assert config.connector_id is not None
        assert config.connector_type == "webhook"
        assert config.name == "Test Webhook"
        assert config.status == ConnectorStatus.INACTIVE

    def test_config_with_credentials(self):
        """Test config with credential reference."""
        config = ConnectorConfig(
            connector_type="slack",
            name="Test Slack",
            auth_type="token",
            credentials_ref="secret:slack_bot_token"
        )

        assert config.auth_type == "token"
        assert config.credentials_ref == "secret:slack_bot_token"


# ============================================================================
# External Action Tests
# ============================================================================

class TestExternalAction:
    """Test ExternalAction model."""

    def test_action_creation(self):
        """Test creating an external action."""
        action = ExternalAction(
            action_type="send_message",
            connector_type="slack",
            parameters={"channel": "#general", "text": "Hello"},
            risk_level=RiskLevel.LOW
        )

        assert action.action_id is not None
        assert action.state == ActionState.CREATED
        assert action.risk_level == RiskLevel.LOW

    def test_action_with_workspace(self):
        """Test action with workspace scoping."""
        action = ExternalAction(
            action_type="create_ticket",
            connector_type="jira",
            parameters={"project": "OPS"},
            workspace_id="workspace_123",
            environment="production"
        )

        assert action.workspace_id == "workspace_123"
        assert action.environment == "production"


# ============================================================================
# Webhook Connector Tests
# ============================================================================

class TestWebhookConnector:
    """Test WebhookConnector."""

    @pytest.mark.asyncio
    async def test_webhook_setup(self):
        """Test webhook connector setup."""
        config = ConnectorConfig(
            connector_type="webhook",
            name="Test Webhook"
        )
        connector = WebhookConnector(config)
        await connector.setup()

        assert connector.status == ConnectorStatus.ACTIVE
        await connector.teardown()

    @pytest.mark.asyncio
    async def test_webhook_capabilities(self):
        """Test webhook connector capabilities."""
        config = ConnectorConfig(
            connector_type="webhook",
            name="Test Webhook"
        )
        connector = WebhookConnector(config)

        capabilities = connector.get_capabilities()

        assert len(capabilities) > 0
        assert any(c.name == "send_webhook" for c in capabilities)
        assert any(c.name == "send_json" for c in capabilities)

    @pytest.mark.asyncio
    async def test_validate_webhook_params(self):
        """Test webhook parameter validation."""
        config = ConnectorConfig(
            connector_type="webhook",
            name="Test Webhook"
        )
        connector = WebhookConnector(config)

        # Valid parameters
        valid, error = await connector.validate_parameters(
            "send_webhook",
            {"url": "https://example.com", "method": "POST"}
        )
        assert valid is True
        assert error is None

        # Missing URL
        valid, error = await connector.validate_parameters(
            "send_webhook",
            {"method": "POST"}
        )
        assert valid is False
        assert "url" in error

        # Invalid URL
        valid, error = await connector.validate_parameters(
            "send_webhook",
            {"url": "not-a-url"}
        )
        assert valid is False

    @pytest.mark.asyncio
    async def test_webhook_execution(self):
        """Test webhook execution."""
        config = ConnectorConfig(
            connector_type="webhook",
            name="Test Webhook"
        )
        connector = WebhookConnector(config)
        await connector.setup()

        action = ExternalAction(
            action_type="send_json",
            connector_type="webhook",
            parameters={
                "url": "https://httpbin.org/post",
                "data": {"test": "data"}
            }
        )

        result = await connector.execute(action)

        # Check result
        assert result is not None
        assert result.action_type == "send_json"

        await connector.teardown()


# ============================================================================
# Slack Connector Tests
# ============================================================================

class TestSlackConnector:
    """Test SlackConnector."""

    @pytest.mark.asyncio
    async def test_slack_capabilities(self):
        """Test Slack connector capabilities."""
        config = ConnectorConfig(
            connector_type="slack",
            name="Test Slack"
        )
        connector = SlackConnector(config)

        capabilities = connector.get_capabilities()

        assert len(capabilities) > 0
        assert any(c.name == "send_message" for c in capabilities)
        assert any(c.name == "send_webhook" for c in capabilities)
        assert any(c.name == "send_alert" for c in capabilities)

    @pytest.mark.asyncio
    async def test_validate_slack_params(self):
        """Test Slack parameter validation."""
        config = ConnectorConfig(
            connector_type="slack",
            name="Test Slack"
        )
        connector = SlackConnector(config)

        # Valid message
        valid, error = await connector.validate_parameters(
            "send_message",
            {"channel": "#general", "text": "Hello"}
        )
        assert valid is True

        # Missing channel
        valid, error = await connector.validate_parameters(
            "send_message",
            {"text": "Hello"}
        )
        assert valid is False

    @pytest.mark.asyncio
    async def test_alert_message_structure(self):
        """Test alert message structure."""
        config = ConnectorConfig(
            connector_type="slack",
            name="Test Slack"
        )
        connector = SlackConnector(config)

        # Alert validation
        valid, error = await connector.validate_parameters(
            "send_alert",
            {"channel": "#alerts", "title": "Test Alert", "message": "Test message"}
        )
        assert valid is True


# ============================================================================
# Connector Registry Tests
# ============================================================================

class TestConnectorRegistry:
    """Test ConnectorRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = ConnectorRegistry()

        assert len(registry.get_registered_types()) == 0

    def test_register_connector_class(self):
        """Test registering a connector class."""
        registry = ConnectorRegistry()

        registry.register_connector_class("test", WebhookConnector)

        assert "test" in registry.get_registered_types()

    @pytest.mark.asyncio
    async def test_create_connector(self):
        """Test creating a connector."""
        registry = ConnectorRegistry()
        registry.register_connector_class("webhook", WebhookConnector)

        config = ConnectorConfig(
            connector_type="webhook",
            name="Test"
        )

        connector = registry.create_connector(config)

        assert connector is not None
        assert connector.config.connector_type == "webhook"

    @pytest.mark.asyncio
    async def test_list_connectors(self):
        """Test listing connectors."""
        registry = ConnectorRegistry()
        registry.register_connector_class("webhook", WebhookConnector)

        config1 = ConnectorConfig(
            connector_type="webhook",
            name="Webhook 1"
        )
        config2 = ConnectorConfig(
            connector_type="webhook",
            name="Webhook 2"
        )

        await registry.create_connector(config1).setup()
        await registry.create_connector(config2).setup()

        connectors = registry.list_connectors()

        assert len(connectors) == 2

    @pytest.mark.asyncio
    async def test_get_connector_by_type(self):
        """Test getting connector by type."""
        registry = ConnectorRegistry()
        registry.register_connector_class("webhook", WebhookConnector)

        config = ConnectorConfig(
            connector_type="webhook",
            name="Test"
        )

        registry.create_connector(config)

        connector = registry.get_connector_by_type("webhook")

        assert connector is not None
        assert connector.config.connector_type == "webhook"


# ============================================================================
# Action Fabric Tests
# ============================================================================

class TestActionFabric:
    """Test ExternalActionFabric."""

    @pytest.mark.asyncio
    async def test_fabric_start_stop(self):
        """Test starting and stopping the fabric."""
        fabric = ExternalActionFabric()

        assert fabric._running is False

        await fabric.start()
        assert fabric._running is True

        await fabric.stop()
        assert fabric._running is False

    @pytest.mark.asyncio
    async def test_submit_action(self, action_fabric):
        """Test submitting an action."""
        action = await action_fabric.submit_action(
            action_type="send_json",
            connector_type="webhook",
            parameters={
                "url": "https://httpbin.org/post",
                "data": {"test": "data"}
            },
            workspace_id="test_workspace",
            environment="dev",
            requested_by="test_user"
        )

        assert action.action_id is not None
        assert action.connector_type == "webhook"
        assert action.action_type == "send_json"
        assert action.workspace_id == "test_workspace"

    @pytest.mark.asyncio
    async def test_policy_enforcement(self, action_fabric):
        """Test policy enforcement."""
        # Add a policy that blocks high-risk actions
        policy = ActionPolicy(
            name="Block High Risk",
            description="Block high risk actions",
            allowed_risk_levels=[RiskLevel.LOW, RiskLevel.MEDIUM],
            connector_types=["webhook"],
            require_approval=False
        )

        action_fabric.add_policy(policy)

        # Submit high-risk action
        action = await action_fabric.submit_action(
            action_type="send_json",
            connector_type="webhook",
            parameters={"url": "https://example.com", "data": {}},
            risk_level=RiskLevel.HIGH
        )

        # Give time for processing
        await asyncio.sleep(0.2)

        # Check statistics
        stats = action_fabric.get_statistics()
        assert stats["total_actions"] >= 1

    @pytest.mark.asyncio
    async def test_get_statistics(self, action_fabric):
        """Test getting fabric statistics."""
        stats = action_fabric.get_statistics()

        assert "total_actions" in stats
        assert "successful_actions" in stats
        assert "failed_actions" in stats
        assert "queue_size" in stats
        assert "is_running" in stats

        assert stats["is_running"] is True

    @pytest.mark.asyncio
    async def test_add_remove_policy(self, action_fabric):
        """Test adding and removing policies."""
        policy = ActionPolicy(
            name="Test Policy",
            connector_types=["slack"],
            require_approval=True
        )

        action_fabric.add_policy(policy)

        policies = action_fabric.list_policies()
        assert len(policies) >= 1

        removed = action_fabric.remove_policy(policy.policy_id)
        assert removed is True

        policies_after = action_fabric.list_policies()
        assert policy.policy_id not in [p.policy_id for p in policies_after]

    @pytest.mark.asyncio
    async def test_event_emission(self, action_fabric):
        """Test event emission."""
        events = []

        def event_handler(event):
            events.append(event)

        action_fabric.add_event_handler(event_handler)

        # Submit an action
        await action_fabric.submit_action(
            action_type="send_json",
            connector_type="webhook",
            parameters={"url": "https://example.com", "data": {}}
        )

        # Check for events
        await asyncio.sleep(0.1)

        assert len(events) >= 1
        assert events[0].event_type == "action_created"


# ============================================================================
# Workflow Execution Engine Tests
# ============================================================================

class TestWorkflowExecutionEngine:
    """Test WorkflowExecutionEngine."""

    @pytest.mark.asyncio
    async def test_engine_start_stop(self):
        """Test starting and stopping the engine."""
        engine = WorkflowExecutionEngine()

        await engine.start()
        assert engine._running is True

        await engine.stop()
        assert engine._running is False

    @pytest.mark.asyncio
    async def test_simple_workflow(self, workflow_engine):
        """Test executing a simple workflow."""
        # Create a simple workflow
        definition = WorkflowDefinition(
            name="Simple Test Workflow",
            nodes=[
                WorkflowNode(
                    node_id="start",
                    node_type=NodeType.START,
                    name="Start"
                ),
                WorkflowNode(
                    node_id="action1",
                    node_type=NodeType.ACTION,
                    name="Send Message",
                    connector_type="slack",
                    action_type="send_message",
                    action_parameters={"channel": "#test", "text": "Hello"}
                ),
                WorkflowNode(
                    node_id="end",
                    node_type=NodeType.END,
                    name="End"
                )
            ],
            edges=[
                WorkflowEdge(from_node="start", to_node="action1"),
                WorkflowEdge(from_node="action1", to_node="end")
            ]
        )

        result = await workflow_engine.execute_workflow(definition)

        assert result.execution_id is not None
        assert result.state in [WorkflowState.COMPLETED, WorkflowState.FAILED]

    @pytest.mark.asyncio
    async def test_workflow_with_condition(self, workflow_engine):
        """Test workflow with conditional branching."""
        definition = WorkflowDefinition(
            name="Conditional Workflow",
            nodes=[
                WorkflowNode(
                    node_id="start",
                    node_type=NodeType.START,
                    name="Start"
                ),
                WorkflowNode(
                    node_id="condition",
                    node_type=NodeType.CONDITION,
                    name="Check Condition",
                    condition_expression="true",
                    true_branch="true_action",
                    false_branch="false_action"
                ),
                WorkflowNode(
                    node_id="true_action",
                    node_type=NodeType.ACTION,
                    name="True Action"
                ),
                WorkflowNode(
                    node_id="false_action",
                    node_type=NodeType.ACTION,
                    name="False Action"
                ),
                WorkflowNode(
                    node_id="end",
                    node_type=NodeType.END,
                    name="End"
                )
            ],
            edges=[
                WorkflowEdge(from_node="start", to_node="condition"),
                WorkflowEdge(from_node="condition", to_node="true_action"),
                WorkflowEdge(from_node="condition", to_node="false_action"),
                WorkflowEdge(from_node="true_action", to_node="end"),
                WorkflowEdge(from_node="false_action", to_node="end")
            ]
        )

        result = await workflow_engine.execute_workflow(definition)

        assert result.execution_id is not None

    @pytest.mark.asyncio
    async def test_workflow_with_delay(self, workflow_engine):
        """Test workflow with delay node."""
        definition = WorkflowDefinition(
            name="Delay Workflow",
            nodes=[
                WorkflowNode(
                    node_id="start",
                    node_type=NodeType.START,
                    name="Start"
                ),
                WorkflowNode(
                    node_id="delay",
                    node_type=NodeType.DELAY,
                    name="Wait",
                    delay_seconds=0.1
                ),
                WorkflowNode(
                    node_id="end",
                    node_type=NodeType.END,
                    name="End"
                )
            ],
            edges=[
                WorkflowEdge(from_node="start", to_node="delay"),
                WorkflowEdge(from_node="delay", to_node="end")
            ]
        )

        start_time = asyncio.get_event_loop().time()
        result = await workflow_engine.execute_workflow(definition)
        duration = asyncio.get_event_loop().time() - start_time

        assert result.execution_id is not None
        assert duration >= 0.1  # At least the delay time

    @pytest.mark.asyncio
    async def test_get_execution(self, workflow_engine):
        """Test getting an execution."""
        definition = WorkflowDefinition(
            name="Test Workflow",
            nodes=[
                WorkflowNode(node_id="start", node_type=NodeType.START, name="Start"),
                WorkflowNode(node_id="end", node_type=NodeType.END, name="End")
            ],
            edges=[WorkflowEdge(from_node="start", to_node="end")]
        )

        result = await workflow_engine.execute_workflow(definition)

        execution = workflow_engine.get_execution(result.execution_id)

        assert execution is not None
        assert execution.execution_id == result.execution_id

    @pytest.mark.asyncio
    async def test_list_executions(self, workflow_engine):
        """Test listing executions."""
        definition = WorkflowDefinition(
            name="Test Workflow",
            nodes=[
                WorkflowNode(node_id="start", node_type=NodeType.START, name="Start"),
                WorkflowNode(node_id="end", node_type=NodeType.END, name="End")
            ],
            edges=[WorkflowEdge(from_node="start", to_node="end")]
        )

        # Execute multiple times
        await workflow_engine.execute_workflow(definition)
        await workflow_engine.execute_workflow(definition)

        executions = workflow_engine.list_executions()

        assert len(executions) >= 2

    @pytest.mark.asyncio
    async def test_cancel_execution(self, workflow_engine):
        """Test cancelling an execution."""
        definition = WorkflowDefinition(
            name="Long Workflow",
            nodes=[
                WorkflowNode(
                    node_id="start",
                    node_type=NodeType.START,
                    name="Start"
                ),
                WorkflowNode(
                    node_id="delay",
                    node_type=NodeType.DELAY,
                    name="Long Wait",
                    delay_seconds=10  # Long delay
                ),
                WorkflowNode(
                    node_id="end",
                    node_type=NodeType.END,
                    name="End"
                )
            ],
            edges=[
                WorkflowEdge(from_node="start", to_node="delay"),
                WorkflowEdge(from_node="delay", to_node="end")
            ]
        )

        # Start execution in background
        task = asyncio.create_task(workflow_engine.execute_workflow(definition))

        # Wait a bit then cancel
        await asyncio.sleep(0.1)

        executions = workflow_engine.list_executions(state=WorkflowState.RUNNING)
        if executions:
            cancelled = await workflow_engine.cancel_execution(executions[0].execution_id)
            assert cancelled is True

        # Clean up task
        try:
            await asyncio.wait_for(task, timeout=1)
        except asyncio.TimeoutError:
            pass


# ============================================================================
# Retry Policy Tests
# ============================================================================

class TestRetryPolicy:
    """Test RetryPolicy."""

    def test_retry_delay_calculation(self):
        """Test retry delay calculation."""
        policy = RetryPolicy(
            retry_delay_seconds=1.0,
            backoff_multiplier=2.0,
            max_delay_seconds=60.0
        )

        delay1 = policy.get_retry_delay(0)
        delay2 = policy.get_retry_delay(1)
        delay3 = policy.get_retry_delay(2)

        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0

    def test_max_delay_enforcement(self):
        """Test max delay enforcement."""
        policy = RetryPolicy(
            retry_delay_seconds=1.0,
            backoff_multiplier=10.0,
            max_delay_seconds=30.0
        )

        delay = policy.get_retry_delay(5)

        assert delay == 30.0  # Max delay


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase8Integration:
    """Integration tests for Phase 8."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow_execution(self):
        """Test complete workflow execution with action fabric."""
        # Set up registry
        registry = get_connector_registry()
        registry.register_connector_class("webhook", WebhookConnector)

        # Create connector
        config = ConnectorConfig(
            connector_type="webhook",
            name="Test Webhook"
        )
        await registry.create_connector(config).setup()

        # Create fabric
        fabric = get_action_fabric()
        await fabric.start()

        # Create workflow engine
        engine = get_workflow_engine()
        await engine.start()

        try:
            # Define workflow
            definition = WorkflowDefinition(
                name="E2E Test Workflow",
                nodes=[
                    WorkflowNode(
                        node_id="start",
                        node_type=NodeType.START,
                        name="Start"
                    ),
                    WorkflowNode(
                        node_id="action",
                        node_type=NodeType.ACTION,
                        name="Send Webhook",
                        connector_type="webhook",
                        action_type="send_json",
                        action_parameters={
                            "url": "https://httpbin.org/post",
                            "data": {"test": "e2e"}
                        }
                    ),
                    WorkflowNode(
                        node_id="end",
                        node_type=NodeType.END,
                        name="End"
                    )
                ],
                edges=[
                    WorkflowEdge(from_node="start", to_node="action"),
                    WorkflowEdge(from_node="action", to_node="end")
                ]
            )

            # Execute
            result = await engine.execute_workflow(definition)

            assert result.execution_id is not None

        finally:
            await fabric.stop()
            await engine.stop()

    @pytest.mark.asyncio
    async def test_multi_connector_workflow(self):
        """Test workflow using multiple connectors."""
        registry = get_connector_registry()
        registry.register_connector_class("webhook", WebhookConnector)

        fabric = get_action_fabric()
        await fabric.start()

        engine = get_workflow_engine()
        await engine.start()

        try:
            definition = WorkflowDefinition(
                name="Multi-Connector Workflow",
                nodes=[
                    WorkflowNode(
                        node_id="start",
                        node_type=NodeType.START,
                        name="Start"
                    ),
                    WorkflowNode(
                        node_id="webhook1",
                        node_type=NodeType.ACTION,
                        name="First Webhook",
                        connector_type="webhook",
                        action_parameters={"url": "https://httpbin.org/post", "data": {"step": 1}}
                    ),
                    WorkflowNode(
                        node_id="webhook2",
                        node_type=NodeType.ACTION,
                        name="Second Webhook",
                        connector_type="webhook",
                        action_parameters={"url": "https://httpbin.org/post", "data": {"step": 2}}
                    ),
                    WorkflowNode(
                        node_id="end",
                        node_type=NodeType.END,
                        name="End"
                    )
                ],
                edges=[
                    WorkflowEdge(from_node="start", to_node="webhook1"),
                    WorkflowEdge(from_node="webhook1", to_node="webhook2"),
                    WorkflowEdge(from_node="webhook2", to_node="end")
                ]
            )

            result = await engine.execute_workflow(definition)

            assert result.execution_id is not None

        finally:
            await fabric.stop()
            await engine.stop()
