# TORQ Console Telemetry System Implementation Guide

## Overview

This document provides comprehensive guidance on the TORQ Console telemetry system implementation, which meets the requirements for structured event tracking, distributed tracing, and ≥95% schema compliance.

## Architecture

### Core Components

1. **Event Schema** (`core/telemetry/event.py`)
   - Canonical event schema for all telemetry data
   - Type-safe event classes with Pydantic validation
   - Support for all required event types: agent runs, tool executions, model interactions, memory operations, routing decisions

2. **Distributed Tracing** (`core/telemetry/trace.py`)
   - Complete trace lifecycle management
   - Span creation with parent-child relationships
   - Context propagation across service boundaries
   - Performance timing and attribution

3. **Telemetry Collection** (`core/telemetry/collector.py`)
   - High-performance async event collection
   - Multiple storage backends (SQLite, file, memory)
   - Batch processing with configurable flush intervals
   - PII filtering and data sanitization

4. **Schema Compliance** (`core/telemetry/compliance.py`)
   - Automated schema validation with ≥95% compliance requirement
   - Comprehensive compliance reporting
   - Field-level validation and type checking
   - Recommendations for improvement

5. **Integration Layer** (`core/telemetry/integration.py`)
   - Seamless integration with existing TORQ Console components
   - Automatic instrumentation with decorators
   - Performance-optimized with minimal impact
   - Context management for run tracking

## CLI Commands

### Trace Command

```bash
# Display trace information for a specific run
torq-console trace <run_id>

# Show detailed events and spans
torq-console trace abc-123-def-456 --events --spans

# Export trace data to JSON
torq-console trace abc-123-def-456 --format json --output trace.json
```

### Telemetry Command

```bash
# Show telemetry statistics
torq-console telemetry

# Filter by event type
torq-console telemetry --event-type agent_run

# Include compliance report
torq-console telemetry --compliance
```

## Integration Examples

### Basic Agent Run Tracking

```python
from torq_console.core.telemetry.integration import get_telemetry_integration

# Initialize telemetry
integration = get_telemetry_integration()
await integration.initialize()

# Start tracking an agent run
run_id = await integration.start_agent_run(
    agent_name="code_generation_agent",
    agent_type="marvin_agent",
    user_query="Generate a REST API endpoint"
)

# Record tool execution
await integration.record_tool_execution(
    tool_name="file_writer",
    tool_type=ToolType.WRITE,
    status="completed",
    execution_time_ms=150,
    run_id=run_id
)

# Record model interaction
await integration.record_model_interaction(
    model_provider=ModelProvider.ANTHROPIC,
    model_name="claude-3-5-sonnet",
    prompt_tokens=200,
    response_time_ms=1200,
    total_tokens=350,
    run_id=run_id
)

# Complete the run
await integration.complete_agent_run(
    success=True,
    tools_used=["file_writer"],
    input_tokens=200,
    output_tokens=150
)
```

### Distributed Tracing with Decorators

```python
from torq_console.core.telemetry.trace import trace_agent_run, trace_tool_execution

@trace_agent_run()
async def process_user_query(query: str):
    """Agent function with automatic tracing."""
    # Tool execution with tracing
    await execute_tool_with_tracing(query)
    return "Response generated"

@trace_tool_execution()
async def execute_tool_with_tracing(query: str):
    """Tool function with automatic tracing."""
    # Tool logic here
    return {"result": "success"}
```

### Method Instrumentation

```python
from torq_console.core.telemetry.integration import instrument_method

class TorqConsole:
    @instrument_method("console", "process_command")
    async def process_command(self, command: str):
        """Automatically instrumented method."""
        # Method implementation
        return result
```

## Event Schema Compliance

### Required Fields

Each event type has specific required fields that must be present for ≥95% schema compliance:

#### Agent Run Events
- `event_id`, `event_type`, `timestamp`, `session_id`
- `agent_name`, `agent_type`, `status`
- Recommended: `user_query`, `confidence_score`, `tools_used`, `total_tokens`

#### Tool Execution Events
- `event_id`, `event_type`, `timestamp`, `session_id`
- `tool_name`, `tool_type`, `status`
- Recommended: `execution_time_ms`, `success`

#### Model Interaction Events
- `event_id`, `event_type`, `timestamp`, `session_id`
- `model_provider`, `model_name`, `prompt_tokens`, `response_time_ms`
- Recommended: `total_tokens`, `completion_tokens`, `success`

#### Memory Operation Events
- `event_id`, `event_type`, `timestamp`, `session_id`
- `memory_type`, `memory_backend`, `operation_type`, `operation_time_ms`
- Recommended: `success`, `cache_hit`

#### Routing Decision Events
- `event_id`, `event_type`, `timestamp`, `session_id`
- `query`, `selected_agent`, `routing_strategy`, `confidence_score`
- Recommended: `routing_time_ms`, `candidate_agents`

### Validation

```python
from torq_console.core.telemetry.compliance import validate_event_schema

# Validate single event
result = await validate_event_schema(event)
print(f"Compliance: {result.is_compliant}")
print(f"Score: {result.compliance_score:.2%}")

# Batch validation
from torq_console.core.telemetry.compliance import check_schema_compliance
report = await check_schema_compliance(events)
print(f"Overall compliance: {report.overall_compliance_score:.2%}")
```

## Performance Considerations

### Minimal Impact Requirements

The telemetry system is designed for minimal performance impact:

1. **Event Creation**: <1ms per event on average
2. **Collection Throughput**: >10,000 events/second
3. **End-to-End Latency**: <50ms average overhead
4. **Memory Overhead**: <5% increase in memory usage

### Performance Tuning

```python
from torq_console.core.telemetry.collector import TelemetryConfig

# High-performance configuration
config = TelemetryConfig(
    enabled=True,
    batch_size=1000,              # Larger batches for better throughput
    flush_interval_seconds=5.0,    # Less frequent flushing
    sampling_rate=0.1,            # 10% sampling for high-traffic systems
    async_flush=True,             # Asynchronous processing
    max_flush_workers=4           # Parallel flush workers
)
```

### Benchmarking

Run performance benchmarks:

```bash
# Run all benchmarks
python benchmark_telemetry_performance.py

# Run specific benchmarks
python benchmark_telemetry_performance.py --benchmarks event_creation collection e2e

# Custom event count
python benchmark_telemetry_performance.py --events 50000
```

## Storage Configuration

### SQLite Storage (Default)

```python
config = TelemetryConfig(
    storage_type="sqlite",
    storage_path=Path("~/.torq_console/telemetry.db"),
    retention_days=30,
    compression=True
)
```

### File Storage

```python
config = TelemetryConfig(
    storage_type="file",
    storage_path=Path("~/.torq_console/telemetry.jsonl"),
    compression=True
)
```

### Memory Storage (Testing)

```python
config = TelemetryConfig(
    storage_type="memory",
    max_events_per_hour=10000
)
```

## Security and Privacy

### PII Filtering

The system automatically filters personally identifiable information:

```python
config = TelemetryConfig(
    pii_filtering=True,
    sanitize_fields=[
        'user_query', 'user_feedback', 'error_message', 'query'
    ]
)
```

### Data Retention

Configure automatic data cleanup:

```python
config = TelemetryConfig(
    retention_days=30,          # Delete events older than 30 days
    max_events_per_hour=10000   # Rate limit for high-volume systems
)
```

## Testing

### Schema Compliance Tests

```bash
# Run compliance tests
python test_telemetry_system.py --suite compliance --verbose

# Ensure ≥95% compliance
python test_telemetry_system.py --suite schema
```

### Performance Tests

```bash
# Run performance benchmarks
python benchmark_telemetry_performance.py

# Validate minimal impact requirements
python benchmark_telemetry_performance.py --benchmarks e2e
```

### Integration Tests

```bash
# Full integration testing
python test_telemetry_system.py --suite integration --verbose
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Reduce `batch_size` in configuration
   - Increase `flush_interval_seconds`
   - Enable `compression`

2. **Slow Performance**
   - Enable `sampling_rate` to reduce event volume
   - Use `async_flush=True`
   - Increase `max_flush_workers`

3. **Low Compliance**
   - Check event creation code for missing required fields
   - Run compliance checker for detailed reports
   - Add recommended fields to improve scores

### Debug Information

```python
# Get telemetry statistics
stats = await integration.get_session_statistics()
print(f"Events collected: {stats['events_collected']}")
print(f"Events dropped: {stats['events_dropped']}")
print(f"Queue size: {stats['queue_size']}")

# Get run summary
summary = await integration.get_run_summary(run_id)
print(f"Run duration: {summary['duration_ms']}ms")
print(f"Event count: {summary['event_count']}")
```

## Migration Guide

### Adding Telemetry to Existing Components

1. **Import integration layer**
   ```python
   from torq_console.core.telemetry.integration import get_telemetry_integration
   ```

2. **Initialize in constructor**
   ```python
   def __init__(self):
       self.telemetry = get_telemetry_integration()
   ```

3. **Add run tracking**
   ```python
   run_id = await self.telemetry.start_agent_run(
       agent_name=self.name,
       agent_type=self.type,
       user_query=query
   )
   ```

4. **Record operations**
   ```python
   await self.telemetry.record_tool_execution(
       tool_name=tool_name,
       tool_type=tool_type,
       status="completed"
   )
   ```

5. **Complete run**
   ```python
   await self.telemetry.complete_agent_run(
       success=True,
       tools_used=tools_used
   )
   ```

### Enabling Telemetry System-Wide

```python
# In main console initialization
from torq_console.core.telemetry.integration import get_telemetry_integration

async def initialize_console():
    # Initialize telemetry
    telemetry = get_telemetry_integration()
    await telemetry.initialize()

    # Use telemetry in console methods
    # ...

    # Shutdown on exit
    await telemetry.shutdown()
```

## Best Practices

1. **Always include required fields** for schema compliance
2. **Use appropriate event types** for accurate tracking
3. **Add context information** for better debugging
4. **Monitor compliance scores** regularly
5. **Configure sampling** for high-traffic systems
6. **Set appropriate retention policies** for storage management
7. **Test performance impact** before production deployment
8. **Use distributed tracing** for complex workflows
9. **Enable PII filtering** for privacy compliance
10. **Monitor storage growth** and set appropriate limits

## File Structure

```
torq_console/core/telemetry/
├── __init__.py              # Package exports
├── event.py                 # Canonical event schema
├── trace.py                 # Distributed tracing
├── collector.py             # Event collection and storage
├── compliance.py            # Schema compliance checking
└── integration.py           # Integration layer

tests/
├── test_telemetry_system.py # Comprehensive test suite
└── benchmark_telemetry_performance.py # Performance benchmarks
```

This telemetry system provides comprehensive observability for TORQ Console while maintaining the ≥95% schema compliance requirement and ensuring minimal performance impact on the system.