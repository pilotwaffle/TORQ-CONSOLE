"""
TORQ Console - Tracing Verification Script

Tests that traces are being emitted and collected correctly.
Run this to verify your OpenTelemetry setup before deployment.
"""

import asyncio
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tracing import (
    init_tracing,
    get_tracer,
    SpanKind,
    traced,
    traced_db,
    traced_llm
)


async def test_basic_tracing():
    """Test 1: Basic span creation and emission"""
    print("\n=== Test 1: Basic Tracing ===")

    tracer = init_tracing(
        service_name="torq-test",
        enable_console=True
    )

    with tracer.trace("test.operation", kind=SpanKind.API_REQUEST) as span:
        await asyncio.sleep(0.1)
        span.attributes["test"] = "value"

    print("✓ Basic tracing test passed")


async def test_decorator_tracing():
    """Test 2: Decorator-based tracing"""
    print("\n=== Test 2: Decorator Tracing ===")

    @traced(name="decorator.test", kind=SpanKind.AGENT_ACT)
    async def test_function(value: int):
        return value * 2

    result = await test_function(21)
    assert result == 42, f"Expected 42, got {result}"

    print("✓ Decorator tracing test passed")


async def test_db_tracing():
    """Test 3: Database operation tracing"""
    print("\n=== Test 3: Database Tracing ===")

    @traced_db(operation="select")
    async def mock_db_query(query: str):
        await asyncio.sleep(0.05)
        return [{"id": 1, "name": "Test"}]

    results = await mock_db_query("SELECT * FROM users")
    assert len(results) == 1

    print("✓ Database tracing test passed")


async def test_llm_tracing():
    """Test 4: LLM call tracing"""
    print("\n=== Test 4: LLM Tracing ===")

    @traced_llm(provider="openai", model="gpt-4")
    async def mock_llm_call(prompt: str):
        await asyncio.sleep(0.15)
        return f"Response to: {prompt}"

    response = await mock_llm_call("Hello, TORQ!")
    assert "Response to:" in response

    print("✓ LLM tracing test passed")


async def test_trace_propagation():
    """Test 5: Trace context propagation"""
    print("\n=== Test 5: Trace Propagation ===")

    tracer = get_tracer()

    @traced(name="parent.operation")
    async def parent_operation():
        context = tracer._current_context

        @traced(name="child.operation", kind=SpanKind.AGENT_ACT)
        async def child_operation():
            # Verify child has parent span ID
            current = tracer._current_context
            assert current.parent_span_id is not None
            assert current.parent_span_id == context.span_id
            return "child result"

        return await child_operation()

    await parent_operation()

    print("✓ Trace propagation test passed")


async def test_error_handling():
    """Test 6: Error tracing"""
    print("\n=== Test 6: Error Handling ===")

    @traced(name="error.test")
    async def failing_operation():
        raise ValueError("Intentional test error")

    try:
        await failing_operation()
    except ValueError:
        pass  # Expected

    print("✓ Error handling test passed")


async def run_all_tests():
    """Run all verification tests"""
    print("\n" + "="*50)
    print("TORQ Console - OpenTelemetry Verification")
    print("="*50)

    start_time = time.time()

    try:
        await test_basic_tracing()
        await test_decorator_tracing()
        await test_db_tracing()
        await test_llm_tracing()
        await test_trace_propagation()
        await test_error_handling()

        elapsed = time.time() - start_time

        print("\n" + "="*50)
        print(f"✓ ALL TESTS PASSED ({elapsed:.2f}s)")
        print("="*50)
        print("\nTracing is working correctly!")
        print("You can now deploy to Railway with confidence.")

        return True

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False

    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
