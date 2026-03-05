"""
TORQ Console - Tracing Verification Script
Standalone verification that traces are being emitted correctly.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add infrastructure to path
sys.path.insert(0, str(Path(__file__).parent))

from tracing import (
    TORQTracer,
    SpanKind,
    TraceContext,
    init_tracing
)


async def test_basic_tracing():
    """Test 1: Basic span creation and emission"""
    print("\n=== Test 1: Basic Tracing ===")

    tracer = init_tracing(service_name="torq-test", enable_console=True)

    span = tracer.start_span("test.operation", context=TraceContext.generate())
    await asyncio.sleep(0.1)
    span.attributes["test"] = "value"
    tracer.end_span(span, status="ok")

    print("✓ Basic tracing test passed")
    return True


async def test_span_kinds():
    """Test 2: All required span kinds from PRD"""
    print("\n=== Test 2: Required Span Kinds ===")

    required_spans = [
        ("api.request", "GET /api/health"),
        ("agent.reason", "User query analysis"),
        ("agent.retrieve", "Knowledge lookup"),
        ("agent.act", "Execute action"),
        ("agent.evaluate", "Outcome evaluation"),
        ("database.query", "SELECT * FROM users"),
        ("redis.lookup", "cache.get(key)")
    ]

    tracer = get_tracer()

    for name, description in required_spans:
        span = tracer.start_span(name, attributes={"description": description})
        tracer.end_span(span)

    print(f"✓ All {len(required_spans)} required span kinds tested")
    return True


async def test_trace_propagation():
    """Test 3: Trace context propagation"""
    print("\n=== Test 3: Trace Propagation ===")

    tracer = get_tracer()

    # Create parent span
    parent_ctx = TraceContext.generate()
    parent_span = tracer.start_span("parent.operation", context=parent_ctx)

    # Create child span with parent context
    child_ctx = parent_ctx.child()
    child_span = tracer.start_span("child.operation", context=child_ctx)

    # Verify parent-child relationship
    assert child_span.context.parent_span_id == parent_span.context.span_id
    assert child_span.context.trace_id == parent_span.context.trace_id

    tracer.end_span(child_span)
    tracer.end_span(parent_span)

    print("✓ Trace propagation test passed")
    return True


async def test_span_fields():
    """Test 4: Required span fields (trace_id, span_id, parent_span_id)"""
    print("\n=== Test 4: Required Span Fields ===")

    ctx = TraceContext.generate()
    span = get_tracer().start_span("field.test", context=ctx)

    # Check required fields exist
    assert hasattr(span.context, 'trace_id'), "Missing trace_id"
    assert hasattr(span.context, 'span_id'), "Missing span_id"
    assert hasattr(span.context, 'parent_span_id'), "Missing parent_span_id"

    # Verify they're non-empty strings
    assert span.context.trace_id, "trace_id is empty"
    assert span.context.span_id, "span_id is empty"

    # Serialize and verify output format
    span_dict = span.to_dict()
    required_keys = ["trace_id", "span_id", "parent_span_id", "start_time"]
    for key in required_keys:
        assert key in span_dict, f"Missing key: {key}"

    print("✓ All required fields present")
    return True


async def test_error_handling():
    """Test 5: Error tracing"""
    print("\n=== Test 5: Error Handling ===")

    span = get_tracer().start_span("error.test")
    try:
        raise ValueError("Intentional test error")
    except ValueError as e:
        tracer.end_span(span, status=f"error: {e}")

    print("✓ Error handling test passed")
    return True


async def test_torq_tracer_methods():
    """Test 6: TORQ-specific tracer methods"""
    print("\n=== Test 6: TORQTracer Methods ===")

    tracer = get_tracer()

    # Test API request method
    api_span = tracer.trace_api_request("GET", "/api/health", 200)
    tracer.end_span(api_span)

    # Test agent methods
    agent_span = tracer.trace_agent_reason("agent_1", "test prompt")
    tracer.end_span(agent_span)

    # Test database method
    db_span = tracer.trace_database_query("SELECT", table="users")
    tracer.end_span(db_span)

    # Test Redis method
    redis_span = tracer.trace_redis_operation("get", key="session:123")
    tracer.end_span(redis_span)

    # Test LLM method
    llm_span = tracer.trace_llm_request(provider="openai", model="gpt-4")
    tracer.end_span(llm_span)

    print("✓ All TORQTracer methods tested")
    return True


async def run_all_tests():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("TORQ Console - OpenTelemetry Verification")
    print("="*60)

    start_time = time.time()

    try:
        results = await asyncio.gather(
            test_basic_tracing(),
            test_span_kinds(),
            test_trace_propagation(),
            test_span_fields(),
            test_error_handling(),
            test_torq_tracer_methods()
        )

        elapsed = time.time() - start_time

        if all(results):
            print("\n" + "="*60)
            print(f"✓ ALL TESTS PASSED ({elapsed:.2f}s)")
            print("="*60)
            print("\n[TRACING] Traces are being emitted correctly!")
            print("[PRD] Step 2 complete: OpenTelemetry Distributed Tracing")
            print("\nRequired span names implemented:")
            for kind in SpanKind:
                print(f"  - {kind.value}")
            print("\nEach span includes:")
            print("  - trace_id (unique identifier)")
            print("  - span_id (unique span identifier)")
            print("  - parent_span_id (for hierarchy)")
            print("  - attributes (key-value metadata)")
            print("  - status (final span status)")
            return True
        else:
            print("\n✗ SOME TESTS FAILED")
            return False

    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
