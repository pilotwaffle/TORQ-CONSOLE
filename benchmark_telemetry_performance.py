"""
TORQ Console Telemetry Performance Benchmarks.

Comprehensive performance testing to ensure minimal impact on system performance.
Meets requirement for minimal performance impact from telemetry system.
"""

import asyncio
import time
import json
import statistics
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple
import argparse
import sys
import os

# Add torq_console to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'torq_console'))

from torq_console.core.telemetry.collector import TelemetryCollector, TelemetryConfig
from torq_console.core.telemetry.event import (
    create_agent_run_event, create_tool_execution_event, create_model_interaction_event,
    create_memory_operation_event, AgentStatus, ToolType, ModelProvider, MemoryOperationType
)
from torq_console.core.telemetry.trace import TraceManager, trace_agent_run
from torq_console.core.telemetry.compliance import check_schema_compliance
from torq_console.core.telemetry.integration import TelemetryIntegration


class TelemetryBenchmark:
    """Comprehensive telemetry performance benchmarking."""

    def __init__(self):
        self.results = {}
        self.temp_dir = tempfile.mkdtemp()

    def __del__(self):
        """Cleanup temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    async def benchmark_event_creation(self, num_events: int = 10000) -> Dict[str, Any]:
        """Benchmark event creation performance."""
        print(f"📊 Benchmarking event creation with {num_events} events...")

        times = []
        session_id = "benchmark_session"

        for i in range(num_events):
            start_time = time.perf_counter()

            # Create different event types
            event_type = i % 4
            if event_type == 0:
                event = create_agent_run_event(
                    session_id=session_id,
                    agent_name=f"agent_{i}",
                    agent_type="benchmark_type",
                    status=AgentStatus.COMPLETED,
                    user_query=f"Benchmark query {i}",
                    input_tokens=100 + i,
                    output_tokens=200 + i,
                    total_tokens=300 + i
                )
            elif event_type == 1:
                event = create_tool_execution_event(
                    session_id=session_id,
                    tool_name=f"tool_{i}",
                    tool_type=ToolType.READ,
                    status="completed",
                    execution_time_ms=50 + (i % 100)
                )
            elif event_type == 2:
                event = create_model_interaction_event(
                    session_id=session_id,
                    model_provider=ModelProvider.ANTHROPIC,
                    model_name="claude-3-5-sonnet",
                    prompt_tokens=100 + (i % 200),
                    response_time_ms=1000 + (i % 2000),
                    completion_tokens=150 + (i % 300),
                    total_tokens=250 + (i % 500)
                )
            else:
                event = create_memory_operation_event(
                    session_id=session_id,
                    memory_type="episodic",
                    memory_backend="sqlite",
                    operation_type=MemoryOperationType.WRITE,
                    operation_time_ms=10 + (i % 50),
                    data_size_bytes=1024 + (i % 4096)
                )

            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)  # Convert to ms

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = statistics.quantiles(times, n=20)[18] if len(times) > 20 else max(times)
        p99_time = statistics.quantiles(times, n=100)[98] if len(times) > 100 else max(times)
        max_time = max(times)
        min_time = min(times)

        result = {
            'total_events': num_events,
            'avg_time_ms': avg_time,
            'median_time_ms': median_time,
            'p95_time_ms': p95_time,
            'p99_time_ms': p99_time,
            'max_time_ms': max_time,
            'min_time_ms': min_time,
            'events_per_second': 1000 / avg_time if avg_time > 0 else float('inf')
        }

        print(f"✅ Event Creation Results:")
        print(f"   Average: {avg_time:.3f}ms per event")
        print(f"   Median:  {median_time:.3f}ms per event")
        print(f"   P95:     {p95_time:.3f}ms per event")
        print(f"   P99:     {p99_time:.3f}ms per event")
        print(f"   Rate:    {result['events_per_second']:.0f} events/second")

        self.results['event_creation'] = result
        return result

    async def benchmark_serialization(self, num_events: int = 1000) -> Dict[str, Any]:
        """Benchmark event serialization performance."""
        print(f"📊 Benchmarking event serialization with {num_events} events...")

        # Create test events
        events = []
        for i in range(num_events):
            events.append(create_agent_run_event(
                session_id="serialization_test",
                agent_name=f"agent_{i}",
                agent_type="test_type",
                status=AgentStatus.COMPLETED,
                user_query=f"Serialization test {i}",
                total_tokens=500 + i
            ))

        # Benchmark to_dict serialization
        dict_times = []
        for event in events:
            start_time = time.perf_counter()
            event_dict = event.to_dict()
            end_time = time.perf_counter()
            dict_times.append((end_time - start_time) * 1000)

        # Benchmark JSON serialization
        json_times = []
        for event in events:
            start_time = time.perf_counter()
            json_str = event.to_json()
            end_time = time.perf_counter()
            json_times.append((end_time - start_time) * 1000)

        # Calculate statistics
        result = {
            'total_events': num_events,
            'avg_dict_time_ms': statistics.mean(dict_times),
            'avg_json_time_ms': statistics.mean(json_times),
            'dict_events_per_second': 1000 / statistics.mean(dict_times),
            'json_events_per_second': 1000 / statistics.mean(json_times),
            'total_dict_time_ms': sum(dict_times),
            'total_json_time_ms': sum(json_times)
        }

        print(f"✅ Serialization Results:")
        print(f"   Dict serialization:   {result['avg_dict_time_ms']:.3f}ms avg ({result['dict_events_per_second']:.0f} events/sec)")
        print(f"   JSON serialization:   {result['avg_json_time_ms']:.3f}ms avg ({result['json_events_per_second']:.0f} events/sec)")

        self.results['serialization'] = result
        return result

    async def benchmark_collection_throughput(self, num_events: int = 10000) -> Dict[str, Any]:
        """Benchmark telemetry collection throughput."""
        print(f"📊 Benchmarking collection throughput with {num_events} events...")

        # Setup collector with temporary storage
        db_path = Path(self.temp_dir) / "throughput_benchmark.db"
        config = TelemetryConfig(
            enabled=True,
            storage_type="sqlite",
            storage_path=db_path,
            batch_size=100,
            flush_interval_seconds=10.0,  # Long interval to avoid flush overhead
            max_queue_size=20000
        )

        collector = TelemetryCollector(config)
        await collector.start()

        # Generate events
        events = []
        for i in range(num_events):
            if i % 4 == 0:
                events.append(create_agent_run_event(
                    session_id="throughput_test",
                    agent_name=f"agent_{i}",
                    agent_type="throughput_type",
                    status=AgentStatus.STARTED
                ))
            elif i % 4 == 1:
                events.append(create_tool_execution_event(
                    session_id="throughput_test",
                    tool_name=f"tool_{i}",
                    tool_type=ToolType.EXECUTE,
                    status="completed"
                ))
            elif i % 4 == 2:
                events.append(create_model_interaction_event(
                    session_id="throughput_test",
                    model_provider=ModelProvider.OPENAI,
                    model_name="gpt-4",
                    prompt_tokens=100,
                    response_time_ms=1000
                ))
            else:
                events.append(create_memory_operation_event(
                    session_id="throughput_test",
                    memory_type="short_term",
                    memory_backend="memory",
                    operation_type=MemoryOperationType.READ,
                    operation_time_ms=5
                ))

        # Benchmark collection
        start_time = time.perf_counter()
        success = await collector.collect_events(events)
        collection_time = time.perf_counter() - start_time

        # Wait for processing
        await asyncio.sleep(1.0)

        # Get statistics
        stats = await collector.get_statistics()
        await collector.stop()

        result = {
            'total_events': num_events,
            'collection_time_seconds': collection_time,
            'avg_collection_time_ms': (collection_time / num_events) * 1000,
            'events_per_second': num_events / collection_time if collection_time > 0 else 0,
            'success_rate': 1.0 if success else 0.0,
            'events_collected': stats.get('events_collected', 0),
            'events_dropped': stats.get('events_dropped', 0),
            'drop_rate': stats.get('events_dropped', 0) / num_events if num_events > 0 else 0
        }

        print(f"✅ Collection Throughput Results:")
        print(f"   Collection time: {collection_time:.3f}s")
        print(f"   Average time per event: {result['avg_collection_time_ms']:.3f}ms")
        print(f"   Throughput: {result['events_per_second']:.0f} events/second")
        print(f"   Success rate: {result['success_rate']:.1%}")
        print(f"   Drop rate: {result['drop_rate']:.1%}")

        self.results['collection_throughput'] = result
        return result

    async def benchmark_distributed_tracing(self, num_traces: int = 1000) -> Dict[str, Any]:
        """Benchmark distributed tracing performance."""
        print(f"📊 Benchmarking distributed tracing with {num_traces} traces...")

        trace_manager = TraceManager()

        # Benchmark trace creation
        trace_creation_times = []
        spans_created = []

        for i in range(num_traces):
            start_time = time.perf_counter()

            # Create trace
            trace = trace_manager.create_trace(
                name=f"benchmark_trace_{i}",
                attributes={"benchmark_id": i}
            )

            # Create main span
            main_span = trace_manager.create_span(
                trace_id=trace.trace_id,
                name="agent_execution",
                kind="internal"
            )

            # Create child spans
            child_span1 = trace_manager.create_span(
                trace_id=trace.trace_id,
                name="tool_execution",
                parent_span_id=main_span.span_id
            )

            child_span2 = trace_manager.create_span(
                trace_id=trace.trace_id,
                name="model_interaction",
                parent_span_id=main_span.span_id
            )

            # Finish spans
            trace_manager.finish_span(child_span1.span_id)
            trace_manager.finish_span(child_span2.span_id)
            trace_manager.finish_span(main_span.span_id)
            trace_manager.finish_trace(trace.trace_id)

            end_time = time.perf_counter()
            trace_creation_times.append((end_time - start_time) * 1000)
            spans_created.extend([main_span, child_span1, child_span2])

        # Calculate statistics
        result = {
            'total_traces': num_traces,
            'total_spans': len(spans_created),
            'avg_trace_time_ms': statistics.mean(trace_creation_times),
            'spans_per_trace': len(spans_created) / num_traces,
            'traces_per_second': 1000 / statistics.mean(trace_creation_times),
            'max_spans_per_trace': 4  # main + 2 children + trace metadata
        }

        print(f"✅ Distributed Tracing Results:")
        print(f"   Average trace time: {result['avg_trace_time_ms']:.3f}ms")
        print(f"   Traces per second: {result['traces_per_second']:.0f}")
        print(f"   Spans per trace: {result['spans_per_trace']:.1f}")

        self.results['distributed_tracing'] = result
        return result

    async def benchmark_schema_compliance(self, num_events: int = 1000) -> Dict[str, Any]:
        """Benchmark schema compliance checking."""
        print(f"📊 Benchmarking schema compliance checking with {num_events} events...")

        from torq_console.core.telemetry.compliance import get_schema_compliance_checker

        checker = get_schema_compliance_checker()

        # Create test events
        events = []
        for i in range(num_events):
            # Mix of compliant and slightly non-compliant events
            if i % 10 == 0:
                # Create event with missing recommended fields
                event = create_agent_run_event(
                    session_id="compliance_test",
                    agent_name=f"agent_{i}",
                    agent_type="test_type",
                    status=AgentStatus.STARTED
                    # Missing recommended fields like user_query, confidence_score
                )
            else:
                # Create fully compliant event
                event = create_agent_run_event(
                    session_id="compliance_test",
                    agent_name=f"agent_{i}",
                    agent_type="test_type",
                    status=AgentStatus.COMPLETED,
                    user_query=f"Compliance test {i}",
                    confidence_score=0.95,
                    input_tokens=100,
                    output_tokens=200,
                    total_tokens=300,
                    success=True
                )
            events.append(event)

        # Benchmark validation
        validation_times = []
        compliant_count = 0

        for event in events:
            start_time = time.perf_counter()
            result = checker.validate_event(event)
            end_time = time.perf_counter()

            validation_times.append((end_time - start_time) * 1000)
            if result.is_compliant:
                compliant_count += 1

        # Calculate statistics
        result = {
            'total_events': num_events,
            'compliant_events': compliant_count,
            'compliance_rate': compliant_count / num_events,
            'avg_validation_time_ms': statistics.mean(validation_times),
            'validations_per_second': 1000 / statistics.mean(validation_times),
            'total_validation_time_ms': sum(validation_times)
        }

        print(f"✅ Schema Compliance Results:")
        print(f"   Compliance rate: {result['compliance_rate']:.1%}")
        print(f"   Average validation time: {result['avg_validation_time_ms']:.3f}ms")
        print(f"   Validations per second: {result['validations_per_second']:.0f}")

        self.results['schema_compliance'] = result
        return result

    async def benchmark_end_to_end_latency(self, num_operations: int = 100) -> Dict[str, Any]:
        """Benchmark end-to-end latency with full telemetry integration."""
        print(f"📊 Benchmarking end-to-end latency with {num_operations} operations...")

        # Setup full telemetry integration
        db_path = Path(self.temp_dir) / "e2e_benchmark.db"
        config = TelemetryConfig(
            enabled=True,
            storage_type="sqlite",
            storage_path=db_path,
            batch_size=10,
            flush_interval_seconds=1.0
        )

        integration = TelemetryIntegration(config)
        await integration.initialize()

        # Benchmark end-to-end operations
        latencies = []

        for i in range(num_operations):
            start_time = time.perf_counter()

            # Simulate complete agent operation
            run_id = await integration.start_agent_run(
                agent_name=f"e2e_agent_{i}",
                agent_type="benchmark",
                user_query=f"End-to-end test {i}"
            )

            # Simulate tool usage
            await integration.record_tool_execution(
                tool_name="file_operation",
                tool_type=ToolType.READ,
                status="completed",
                execution_time_ms=25,
                run_id=run_id
            )

            # Simulate model interaction
            await integration.record_model_interaction(
                model_provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-5-sonnet",
                prompt_tokens=50,
                response_time_ms=800,
                total_tokens=75,
                run_id=run_id
            )

            # Complete the run
            await integration.complete_agent_run(
                success=True,
                tools_used=["file_operation"],
                input_tokens=50,
                output_tokens=25
            )

            end_time = time.perf_counter()
            latencies.append((end_time - start_time) * 1000)

        # Wait for processing
        await asyncio.sleep(2.0)

        # Get final statistics
        final_stats = await integration.get_session_statistics()
        await integration.shutdown()

        result = {
            'total_operations': num_operations,
            'avg_latency_ms': statistics.mean(latencies),
            'median_latency_ms': statistics.median(latencies),
            'p95_latency_ms': statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies),
            'operations_per_second': num_operations / (sum(latencies) / 1000),
            'final_stats': final_stats
        }

        print(f"✅ End-to-End Latency Results:")
        print(f"   Average latency: {result['avg_latency_ms']:.1f}ms")
        print(f"   Median latency:  {result['median_latency_ms']:.1f}ms")
        print(f"   P95 latency:     {result['p95_latency_ms']:.1f}ms")
        print(f"   Operations/sec:  {result['operations_per_second']:.1f}")

        self.results['end_to_end_latency'] = result
        return result

    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmarks and return comprehensive results."""
        print("🚀 Starting TORQ Console Telemetry Performance Benchmarks")
        print("=" * 60)

        start_time = time.perf_counter()

        # Run all benchmarks
        await self.benchmark_event_creation()
        await self.benchmark_serialization()
        await self.benchmark_collection_throughput()
        await self.benchmark_distributed_tracing()
        await self.benchmark_schema_compliance()
        await self.benchmark_end_to_end_latency()

        total_time = time.perf_counter() - start_time

        # Generate summary
        summary = {
            'benchmark_duration_seconds': total_time,
            'results': self.results,
            'performance_assessment': self._assess_performance()
        }

        print("\n" + "=" * 60)
        print("📋 PERFORMANCE ASSESSMENT")
        print("=" * 60)

        assessment = summary['performance_assessment']
        for category, result in assessment.items():
            status = result['status']
            message = result['message']
            status_icon = "✅" if status == "PASS" else "⚠️" if status == "WARN" else "❌"
            print(f"{status_icon} {category}: {message}")

        print(f"\n⏱️  Total benchmark time: {total_time:.2f} seconds")

        return summary

    def _assess_performance(self) -> Dict[str, Dict[str, str]]:
        """Assess performance against requirements."""
        assessment = {}

        # Event creation assessment
        if 'event_creation' in self.results:
            avg_time = self.results['event_creation']['avg_time_ms']
            if avg_time < 0.1:
                assessment['Event Creation'] = {
                    'status': 'PASS',
                    'message': f'Excellent performance ({avg_time:.3f}ms per event)'
                }
            elif avg_time < 1.0:
                assessment['Event Creation'] = {
                    'status': 'PASS',
                    'message': f'Good performance ({avg_time:.3f}ms per event)'
                }
            else:
                assessment['Event Creation'] = {
                    'status': 'WARN',
                    'message': f'Suboptimal performance ({avg_time:.3f}ms per event)'
                }

        # Collection throughput assessment
        if 'collection_throughput' in self.results:
            throughput = self.results['collection_throughput']['events_per_second']
            if throughput > 10000:
                assessment['Collection Throughput'] = {
                    'status': 'PASS',
                    'message': f'Excellent throughput ({throughput:.0f} events/sec)'
                }
            elif throughput > 5000:
                assessment['Collection Throughput'] = {
                    'status': 'PASS',
                    'message': f'Good throughput ({throughput:.0f} events/sec)'
                }
            else:
                assessment['Collection Throughput'] = {
                    'status': 'WARN',
                    'message': f'Low throughput ({throughput:.0f} events/sec)'
                }

        # End-to-end latency assessment
        if 'end_to_end_latency' in self.results:
            avg_latency = self.results['end_to_end_latency']['avg_latency_ms']
            if avg_latency < 50:
                assessment['End-to-End Latency'] = {
                    'status': 'PASS',
                    'message': f'Excellent latency ({avg_latency:.1f}ms average)'
                }
            elif avg_latency < 100:
                assessment['End-to-End Latency'] = {
                    'status': 'PASS',
                    'message': f'Good latency ({avg_latency:.1f}ms average)'
                }
            else:
                assessment['End-to-End Latency'] = {
                    'status': 'WARN',
                    'message': f'High latency ({avg_latency:.1f}ms average)'
                }

        # Schema compliance assessment
        if 'schema_compliance' in self.results:
            compliance_rate = self.results['schema_compliance']['compliance_rate']
            if compliance_rate >= 0.95:
                assessment['Schema Compliance'] = {
                    'status': 'PASS',
                    'message': f'Meets ≥95% requirement ({compliance_rate:.1%} compliance)'
                }
            else:
                assessment['Schema Compliance'] = {
                    'status': 'FAIL',
                    'message': f'Below 95% requirement ({compliance_rate:.1%} compliance)'
                }

        return assessment

    def save_results(self, filename: str = "telemetry_benchmark_results.json"):
        """Save benchmark results to file."""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"💾 Results saved to {filename}")


async def main():
    """Main function to run benchmarks."""
    parser = argparse.ArgumentParser(description="TORQ Console Telemetry Performance Benchmarks")
    parser.add_argument("--output", "-o", default="telemetry_benchmark_results.json",
                       help="Output file for results")
    parser.add_argument("--benchmarks", nargs="+",
                       choices=["event_creation", "serialization", "collection", "tracing", "compliance", "e2e"],
                       help="Specific benchmarks to run")
    parser.add_argument("--events", type=int, default=10000,
                       help="Number of events for throughput benchmarks")
    parser.add_argument("--traces", type=int, default=1000,
                       help="Number of traces for tracing benchmarks")

    args = parser.parse_args()

    benchmark = TelemetryBenchmark()

    try:
        if args.benchmarks:
            # Run specific benchmarks
            print(f"🚀 Running specified benchmarks: {', '.join(args.benchmarks)}")
            print("=" * 60)

            if "event_creation" in args.benchmarks:
                await benchmark.benchmark_event_creation(args.events)
            if "serialization" in args.benchmarks:
                await benchmark.benchmark_serialization(args.events // 10)
            if "collection" in args.benchmarks:
                await benchmark.benchmark_collection_throughput(args.events)
            if "tracing" in args.benchmarks:
                await benchmark.benchmark_distributed_tracing(args.traces)
            if "compliance" in args.benchmarks:
                await benchmark.benchmark_schema_compliance(args.events // 10)
            if "e2e" in args.benchmarks:
                await benchmark.benchmark_end_to_end_latency(100)

            # Show assessment for run benchmarks
            assessment = benchmark._assess_performance()
            print("\n📋 PERFORMANCE ASSESSMENT")
            print("=" * 60)
            for category, result in assessment.items():
                status = result['status']
                message = result['message']
                status_icon = "✅" if status == "PASS" else "⚠️" if status == "WARN" else "❌"
                print(f"{status_icon} {category}: {message}")

        else:
            # Run all benchmarks
            await benchmark.run_all_benchmarks()

        # Save results
        benchmark.save_results(args.output)

    except KeyboardInterrupt:
        print("\n❌ Benchmarks interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running benchmarks: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())