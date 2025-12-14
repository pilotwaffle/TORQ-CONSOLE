"""
TORQ Console Telemetry Package.

Comprehensive telemetry system for monitoring agent runs, performance metrics,
and distributed tracing across the TORQ Console ecosystem.
"""

from .event import (
    TorqEvent,
    TorqEventType,
    AgentRunEvent,
    ToolExecutionEvent,
    ModelInteractionEvent,
    MemoryOperationEvent,
    RoutingDecisionEvent,
    SystemEvent,
    EventSeverity,
    create_agent_run_event,
    create_tool_execution_event,
    create_model_interaction_event,
    create_memory_operation_event,
    create_routing_decision_event,
    create_system_event
)

from .trace import (
    TorqTrace,
    TraceContext,
    TraceSpan,
    SpanKind,
    SpanStatus,
    TraceManager,
    get_trace_manager,
    trace_agent_run,
    trace_tool_execution,
    trace_model_interaction,
    trace_memory_operation,
    trace_routing_decision
)

from .collector import (
    TelemetryCollector,
    TelemetryConfig,
    get_telemetry_collector
)

from .compliance import (
    SchemaComplianceChecker,
    ComplianceReport,
    check_schema_compliance,
    validate_event_schema
)

__all__ = [
    # Event module
    'TorqEvent',
    'TorqEventType',
    'AgentRunEvent',
    'ToolExecutionEvent',
    'ModelInteractionEvent',
    'MemoryOperationEvent',
    'RoutingDecisionEvent',
    'SystemEvent',
    'EventSeverity',
    'create_agent_run_event',
    'create_tool_execution_event',
    'create_model_interaction_event',
    'create_memory_operation_event',
    'create_routing_decision_event',
    'create_system_event',

    # Trace module
    'TorqTrace',
    'TraceContext',
    'TraceSpan',
    'SpanKind',
    'SpanStatus',
    'TraceManager',
    'get_trace_manager',
    'trace_agent_run',
    'trace_tool_execution',
    'trace_model_interaction',
    'trace_memory_operation',
    'trace_routing_decision',

    # Collector module
    'TelemetryCollector',
    'TelemetryConfig',
    'get_telemetry_collector',

    # Compliance module
    'SchemaComplianceChecker',
    'ComplianceReport',
    'check_schema_compliance',
    'validate_event_schema'
]

__version__ = "1.0.0"