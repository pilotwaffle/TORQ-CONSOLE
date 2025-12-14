"""
Benchmark Runner for TORQ Console

Executes performance benchmarks and collects detailed metrics.
"""

import asyncio
import time
import psutil
import uuid
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager

import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from .slo_config import SLOConfig, SLOCategory
from .storage import BenchmarkResult, BenchmarkIteration, BenchmarkStorage


@dataclass
class BenchmarkTest:
    """Definition of a benchmark test."""

    name: str
    category: str
    description: str
    test_func: Callable  # Async function that executes the test
    warmup_func: Optional[Callable] = None
    setup_func: Optional[Callable] = None
    teardown_func: Optional[Callable] = None

    # Test parameters
    timeout_ms: int = 30000  # 30 seconds default
    expected_tokens: Optional[int] = None
    cost_per_token: float = 0.00002  # Default cost estimation

    # Metadata
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PerformanceMonitor:
    """Monitors system performance during benchmark execution."""

    def __init__(self):
        self.monitoring = False
        self.metrics = []
        self.start_time = None
        self.ttfuo_time = None  # Time to First Useful Output
        self.process = psutil.Process()

    def start_monitoring(self):
        """Start performance monitoring."""
        self.monitoring = True
        self.start_time = time.time()
        self.metrics = []
        self.ttfuo_time = None

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=1.0)

    def mark_ttfuo(self):
        """Mark Time to First Useful Output."""
        if self.start_time and not self.ttfuo_time:
            self.ttfuo_time = (time.time() - self.start_time) * 1000

    def _monitor_loop(self):
        """Monitoring loop running in separate thread."""
        while self.monitoring:
            try:
                # Collect system metrics
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024

                metric = {
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb,
                }

                self.metrics.append(metric)
                time.sleep(0.1)  # Sample every 100ms

            except Exception:
                break

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.metrics:
            return {}

        cpu_values = [m['cpu_percent'] for m in self.metrics]
        memory_values = [m['memory_mb'] for m in self.metrics]

        return {
            'peak_memory_mb': max(memory_values),
            'avg_memory_mb': sum(memory_values) / len(memory_values),
            'peak_cpu_percent': max(cpu_values),
            'avg_cpu_percent': sum(cpu_values) / len(cpu_values),
            'duration_ms': (time.time() - self.start_time) * 1000 if self.start_time else 0,
            'ttfuo_ms': self.ttfuo_time
        }


class BenchmarkRunner:
    """Executes benchmarks and manages test lifecycle."""

    def __init__(self, slo_config: Optional[SLOConfig] = None,
                 storage: Optional[BenchmarkStorage] = None,
                 console: Optional[Console] = None):
        """Initialize benchmark runner.

        Args:
            slo_config: SLO configuration. If None, loads default.
            storage: Storage backend. If None, creates default.
            console: Rich console for output. If None, creates new.
        """
        self.slo_config = slo_config or SLOConfig.load_default()
        self.storage = storage or BenchmarkStorage()
        self.console = console or Console()
        self.monitor = PerformanceMonitor()

        # Test registry
        self.tests: Dict[str, BenchmarkTest] = {}

    def register_test(self, test: BenchmarkTest) -> None:
        """Register a benchmark test."""
        self.tests[test.name] = test

    def get_test(self, test_name: str) -> Optional[BenchmarkTest]:
        """Get a registered test."""
        return self.tests.get(test_name)

    def list_tests(self, category: Optional[str] = None) -> List[str]:
        """List all registered tests, optionally filtered by category."""
        tests = self.tests.values()
        if category:
            tests = [t for t in tests if t.category == category]
        return [t.name for t in tests]

    async def run_single_iteration(self, test: BenchmarkTest,
                                  environment: str = "production") -> BenchmarkIteration:
        """Run a single iteration of a benchmark test."""
        iteration_id = str(uuid.uuid4())
        start_time = datetime.now()

        iteration = BenchmarkIteration(
            iteration_id=iteration_id,
            category=test.category,
            test_name=test.name,
            start_time=start_time,
            end_time=start_time,  # Will be updated
            duration_ms=0.0,
            success=False
        )

        try:
            # Setup
            if test.setup_func:
                await test.setup_func()

            # Start monitoring
            self.monitor.start_monitoring()

            # Execute test with timeout
            timeout_seconds = test.timeout_ms / 1000.0
            result = await asyncio.wait_for(test.test_func(), timeout=timeout_seconds)

            # Mark TTFUO if not already marked
            self.monitor.mark_ttfuo()

            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            # Update iteration with success
            iteration.end_time = end_time
            iteration.duration_ms = duration_ms
            iteration.success = True

            # Get performance metrics
            perf_summary = self.monitor.get_summary()
            iteration.memory_peak_mb = perf_summary.get('peak_memory_mb')
            iteration.ttfuo_ms = perf_summary.get('ttfuo_ms')
            iteration.e2e_ms = perf_summary.get('duration_ms')

            # Extract tokens from result if available
            if isinstance(result, dict):
                iteration.tokens_generated = result.get('tokens_generated')
                iteration.metadata = {k: v for k, v in result.items() if k != 'tokens_generated'}

                # Calculate tokens per second
                if iteration.tokens_generated and duration_ms > 0:
                    iteration.tokens_per_sec = iteration.tokens_generated / (duration_ms / 1000.0)

                # Estimate cost
                if iteration.tokens_generated:
                    iteration.cost_estimate = iteration.tokens_generated * test.cost_per_token

        except asyncio.TimeoutError:
            end_time = datetime.now()
            iteration.end_time = end_time
            iteration.duration_ms = (end_time - start_time).total_seconds() * 1000
            iteration.error = f"Test timed out after {test.timeout_ms}ms"

        except Exception as e:
            end_time = datetime.now()
            iteration.end_time = end_time
            iteration.duration_ms = (end_time - start_time).total_seconds() * 1000
            iteration.error = str(e)

        finally:
            # Stop monitoring
            self.monitor.stop_monitoring()

            # Teardown
            try:
                if test.teardown_func:
                    await test.teardown_func()
            except Exception as e:
                self.console.print(f"[yellow]Warning: Teardown failed for {test.name}: {e}[/yellow]")

        return iteration

    async def run_benchmark(self, test_name: str, iterations: int = 10,
                           warmup_iterations: int = 3, environment: str = "production",
                           concurrent_users: int = 1, **kwargs) -> BenchmarkResult:
        """Run a complete benchmark for a test."""
        test = self.get_test(test_name)
        if not test:
            raise ValueError(f"Test not found: {test_name}")

        run_id = str(uuid.uuid4())
        timestamp = datetime.now()

        self.console.print(f"[cyan]Running benchmark:[/cyan] {test_name}")
        self.console.print(f"[dim]Category:[/dim] {test.category}")
        self.console.print(f"[dim]Iterations:[/dim] {iterations} (+ {warmup_iterations} warmup)")
        self.console.print(f"[dim]Environment:[/dim] {environment}")

        result = BenchmarkResult(
            run_id=run_id,
            category=test.category,
            test_name=test.name,
            environment=environment,
            timestamp=timestamp,
            config={
                'iterations': iterations,
                'warmup_iterations': warmup_iterations,
                'concurrent_users': concurrent_users,
                **kwargs
            },
            system_info=self._get_system_info()
        )

        # Warmup iterations
        if warmup_iterations > 0:
            self.console.print(f"\n[yellow]Running {warmup_iterations} warmup iterations...[/yellow]")
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Warming up...", total=warmup_iterations)

                for i in range(warmup_iterations):
                    if test.warmup_func:
                        await test.warmup_func()
                    else:
                        # Use regular test function for warmup
                        await self.run_single_iteration(test, environment)

                    progress.advance(task)

        # Main benchmark iterations
        self.console.print(f"\n[green]Running {iterations} benchmark iterations...[/green]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task("Benchmarking...", total=iterations)

            for i in range(iterations):
                iteration = await self.run_single_iteration(test, environment)
                result.iterations.append(iteration)

                # Update progress
                progress.update(task, advance=1,
                              description=f"Iteration {i+1}/{iterations} "
                                        f"({'✓' if iteration.success else '✗'})")

        # Calculate statistics
        result.calculate_statistics()

        # Evaluate SLO compliance
        slo_category = self.slo_config.get_category(test.category, environment)
        primary_metric = slo_category.get_primary_metric()
        primary_value = getattr(result, 'p95_primary', result.p95_duration)

        if primary_value is not None:
            result.slo_met = self.slo_config.validate_slo(
                test.category, primary_value, primary_metric, environment
            )
            result.slo_degradation_level = self.slo_config.get_degradation_level(
                test.category, primary_value, primary_metric, environment
            )

        # Store result
        release_version = kwargs.get('release_version')
        self.storage.store_result(result, release_version)

        return result

    async def run_category_benchmark(self, category: str,
                                   iterations_per_test: int = 10,
                                   environment: str = "production",
                                   **kwargs) -> List[BenchmarkResult]:
        """Run benchmarks for all tests in a category."""
        tests = [t for t in self.tests.values() if t.category == category]
        if not tests:
            raise ValueError(f"No tests found for category: {category}")

        self.console.print(f"[cyan]Running {len(tests)} tests in category:[/cyan] {category}")

        results = []
        for test in tests:
            result = await self.run_benchmark(
                test.name, iterations=iterations_per_test,
                environment=environment, **kwargs
            )
            results.append(result)

        return results

    async def run_full_benchmark_suite(self, iterations_per_test: int = 10,
                                      environment: str = "production",
                                      **kwargs) -> Dict[str, List[BenchmarkResult]]:
        """Run the complete benchmark suite."""
        categories = set(test.category for test in self.tests.values())

        self.console.print(f"[cyan]Running full benchmark suite:[/cyan] {len(categories)} categories")

        results = {}
        for category in categories:
            try:
                category_results = await self.run_category_benchmark(
                    category, iterations_per_test, environment, **kwargs
                )
                results[category] = category_results
            except Exception as e:
                self.console.print(f"[red]Error running category {category}:[/red] {e}")
                results[category] = []

        return results

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmark context."""
        import platform

        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
            'torq_version': '0.70.0'  # Should be dynamic
        }


# Built-in benchmark tests for TORQ Console

async def test_simple_response():
    """Simple response time test."""
    await asyncio.sleep(0.1)  # Simulate work
    return {"response": "Hello World", "tokens_generated": 5}

async def test_code_generation():
    """Code generation performance test."""
    # Simulate code generation work
    await asyncio.sleep(1.5)
    return {
        "code": "def hello():\n    print('Hello World')",
        "tokens_generated": 50,
        "language": "python"
    }

async def test_tool_heavy_operation():
    """Complex operation with multiple tool calls."""
    # Simulate complex workflow
    await asyncio.sleep(3.0)
    return {
        "result": "Complex operation completed",
        "tool_calls": 5,
        "tokens_generated": 200
    }

async def test_search_operation():
    """Information search and retrieval test."""
    # Simulate search operation
    await asyncio.sleep(0.8)
    return {
        "search_results": ["result1", "result2", "result3"],
        "tokens_generated": 30
    }


def create_default_tests() -> List[BenchmarkTest]:
    """Create default benchmark tests for TORQ Console."""
    return [
        BenchmarkTest(
            name="simple_response",
            category="interactive",
            description="Simple interactive response test",
            test_func=test_simple_response,
            timeout_ms=5000,
            expected_tokens=5
        ),
        BenchmarkTest(
            name="code_generation",
            category="code_gen",
            description="Code generation performance test",
            test_func=test_code_generation,
            timeout_ms=20000,
            expected_tokens=50
        ),
        BenchmarkTest(
            name="tool_heavy_operation",
            category="tool_heavy",
            description="Complex operation with multiple tool calls",
            test_func=test_tool_heavy_operation,
            timeout_ms=45000,
            expected_tokens=200
        ),
        BenchmarkTest(
            name="search_operation",
            category="search",
            description="Information search and retrieval test",
            test_func=test_search_operation,
            timeout_ms=15000,
            expected_tokens=30
        )
    ]