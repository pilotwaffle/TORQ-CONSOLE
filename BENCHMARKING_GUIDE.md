# TORQ Console Performance Benchmarking & SLO Enforcement

Complete performance monitoring and Service Level Objective (SLO) enforcement system for TORQ Console.

## 🎯 Overview

The TORQ Console benchmarking system provides:
- **Performance Benchmarking**: Automated performance testing with detailed metrics
- **SLO Enforcement**: Service Level Objective validation and compliance tracking
- **Performance Storage**: Persistent storage and tracking of results over time
- **Regression Detection**: Automated detection of performance regressions
- **Release Tracking**: Performance tracking per release version
- **Rich Reporting**: Detailed performance reports with visualizations

## 🚀 Quick Start

### Installation

The benchmarking system is included in TORQ Console v0.80.0+:

```bash
# Install TORQ Console with benchmarking support
pip install torq-console

# Or install from source
git clone https://github.com/pilotwaffle/TORQ-CONSOLE.git
cd TORQ-CONSOLE
pip install -e .
```

### Basic Usage

```bash
# Run all benchmarks
torq-bench run

# Run a specific benchmark test
torq-bench run simple_response

# List recent results
torq-bench list

# Show SLO configuration
torq-bench slo

# Run with custom iterations and release tracking
torq-bench run --iterations 20 --release v1.2.3

# Export results to JSON
torq-bench run --format json --output results.json
```

### Integration with TORQ Console

```bash
# Access benchmarks through TORQ Console CLI
torq-console bench run
torq-console bench list
torq-console bench slo
```

## 📊 SLO Configuration

### Default SLOs

The system includes predefined SLOs for different operation categories:

#### Interactive Operations
- **p95_ttfuo_ms**: 2500ms (Time to First Useful Output)
- **p99_ttfuo_ms**: 5000ms
- **Success Rate**: 95%

#### Tool-Heavy Operations
- **p95_e2e_ms**: 30000ms (End-to-End execution)
- **p99_e2e_ms**: 60000ms
- **Success Rate**: 90%

#### Code Generation
- **p95_e2e_ms**: 15000ms
- **Tokens/sec**: 10 tokens/second
- **Success Rate**: 92%

#### Search Operations
- **p95_e2e_ms**: 12000ms
- **Success Rate**: 94%

### Custom SLO Configuration

Create a custom `slo.yml` file:

```yaml
version: "1.0"
description: "Custom SLO configuration"
categories:
  interactive:
    description: "User-facing interactive operations"
    p95_ttfuo_ms: 2000  # Faster target
    p99_ttfuo_ms: 4000
    success_rate: 0.98   # Higher success rate
    max_memory_mb: 1024
    sample_size: 100

  tool_heavy:
    description: "Complex operations with multiple tool calls"
    p95_e2e_ms: 25000    # Faster target
    p99_e2e_ms: 50000
    success_rate: 0.95    # Higher success rate
    max_memory_mb: 2048
    sample_size: 50

# Environment-specific adjustments
environments:
  development:
    slack_factor: 2.0      # Allow 2x slower in development
    sample_size_multiplier: 0.5

  production:
    slack_factor: 1.0      # No slack in production
    sample_size_multiplier: 1.0
```

Use custom configuration:

```bash
torq-bench --config custom-slo.yml run
```

## 🧪 Benchmark Tests

### Built-in Tests

The system includes default benchmark tests:

1. **simple_response** (interactive)
   - Tests basic response time
   - Expected: ~100ms response time
   - 5 tokens generated

2. **code_generation** (code_gen)
   - Tests code generation performance
   - Expected: ~1.5s execution time
   - 50 tokens generated

3. **tool_heavy_operation** (tool_heavy)
   - Tests complex multi-tool workflows
   - Expected: ~3s execution time
   - 200 tokens generated, 5 tool calls

4. **search_operation** (search)
   - Tests information retrieval performance
   - Expected: ~800ms execution time
   - 30 tokens generated

### Custom Benchmark Tests

Create custom benchmark tests:

```python
import asyncio
from torq_console.benchmarking.runner import BenchmarkRunner, BenchmarkTest

async def my_custom_test():
    """Custom benchmark test implementation."""
    start_time = time.time()

    # Your test logic here
    await asyncio.sleep(1.0)  # Simulate work

    end_time = time.time()

    return {
        "result": "Custom operation completed",
        "tokens_generated": 25,
        "processing_time": (end_time - start_time) * 1000
    }

# Create test definition
custom_test = BenchmarkTest(
    name="my_custom_test",
    category="interactive",
    description="Custom performance test",
    test_func=my_custom_test,
    timeout_ms=5000,
    expected_tokens=25,
    cost_per_token=0.00002
)

# Register and run
runner = BenchmarkRunner()
runner.register_test(custom_test)
result = await runner.run_benchmark("my_custom_test", iterations=10)
```

## 📈 Performance Reporting

### Console Reports

The system generates rich console reports with:

- **SLO Compliance Summary**: Overall compliance percentage and degradation levels
- **Comparison Tables**: Side-by-side comparison of multiple benchmark results
- **Detailed Metrics**: p50/p90/p95/p99 percentiles for all metrics
- **Performance Trends**: Historical performance data
- **Regression Analysis**: Automated performance regression detection

### JSON Reports

```bash
# Export detailed JSON report
torq-bench run --format json --output results.json

# Report structure:
{
  "metadata": {
    "generated_at": "2025-01-14T10:30:00",
    "slo_config_version": "1.0",
    "total_results": 4
  },
  "summary": {
    "overall_slo_compliance": 0.95,
    "total_tests": 4,
    "successful_tests": 4
  },
  "results": [...],
  "slo_analysis": {...},
  "performance_analysis": {...},
  "cost_analysis": {...}
}
```

### CSV Reports

```bash
# Export to CSV for spreadsheet analysis
torq-bench run --format csv --output results.csv
```

## 🔍 Performance Monitoring

### Continuous Monitoring

Set up automated benchmark runs:

```bash
# Daily benchmark with release tracking
torq-bench run --release $(git rev-parse --short HEAD) --format json --output daily-$(date +%Y%m%d).json

# Weekly performance trends
torq-bench trends --category interactive --days 7

# Regression detection
torq-bench regressions
```

### Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/benchmark.yml
name: Performance Benchmarks

on: [push, pull_request]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install TORQ Console
        run: pip install torq-console

      - name: Run Benchmarks
        run: |
          torq-bench run --release ${{ github.sha }} --format json --output benchmark-results.json

      - name: Check SLO Compliance
        run: |
          # Extract SLO compliance from results
          SLO_COMPLIANCE=$(cat benchmark-results.json | jq '.summary.overall_slo_compliance')

          # Fail if compliance < 90%
          if (( $(echo "$SLO_COMPLIANCE < 0.90" | bc -l) )); then
            echo "SLO compliance too low: $SLO_COMPLIANCE"
            exit 1
          fi

      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: benchmark-results.json
```

### Performance Storage

Results are stored in `.torq/benchmarks/`:

```
.torq/benchmarks/
├── benchmarks.db          # SQLite database for queries
├── results/               # Detailed JSON results
│   ├── run_001.json
│   ├── run_002.json
│   └── ...
└── releases/              # Per-release tracking
    ├── v1.0.0/
    ├── v1.1.0/
    └── ...
```

## 📊 Release Tracking

### Track Performance Per Release

```bash
# Run benchmarks for a specific release
torq-bench run --release v1.2.0

# Get release summary
torq-bench release v1.2.0

# Compare releases
torq-bench list --limit 50 | grep -E "(v1.1.0|v1.2.0)"
```

### Release Performance Report

```bash
# Generate comprehensive release report
torq-bench release v1.2.0

# Example output:
Release Summary: v1.2.0
================================
Total Runs: 12
Overall Success Rate: 96.5%
SLO Compliance Rate: 92.0%
Avg Cost/Success: $0.0042
Total Cost: $0.0834

Category Performance:
┌─────────────┬──────┬─────────────┬─────────┬──────────┬───────────┐
│ Category    │ Runs │ Success Rate│ SLO Comp │ Avg p95   │ Cost/Success│
├─────────────┼──────┼─────────────┼─────────┼──────────┼───────────┤
│ interactive │ 4    │ 98.5%       │ 100.0%  │ 2450ms   │ $0.0038    │
│ tool_heavy  │ 3    │ 95.2%       │ 85.7%   │ 28500ms  │ $0.0052    │
│ code_gen    │ 3    │ 96.8%       │ 90.3%   │ 14200ms  │ $0.0041    │
│ search      │ 2    │ 100.0%      │ 100.0%  │ 11500ms  │ $0.0029    │
└─────────────┴──────┴─────────────┴─────────┴──────────┴───────────┘
```

## 🚨 SLO Enforcement

### Automatic Enforcement

The system automatically enforces SLOs:

1. **Benchmark Validation**: Each run validates against SLO targets
2. **Exit Codes**: Non-zero exit code if SLOs are not met
3. **Degradation Detection**: Multi-level degradation warnings (ok/warning/critical)
4. **Regression Alerts**: Automatic detection of performance regressions

### Manual SLO Validation

```bash
# Validate specific metrics against SLOs
torq-bench validate interactive p95_ttfuo_ms 2400
torq-bench validate tool_heavy p95_e2e_ms 28000
torq-bench validate code_gen tokens_per_sec 15

# Output examples:
SLO Validation: interactive.p95_ttfuo_ms
Environment: production
Value:     2400
Target:    2500
Status:    PASS
Level:     OK
Degradation: -4.0%
```

### SLO Degradation Levels

- **OK**: Performance within acceptable limits
- **WARNING**: 10-25% degradation from SLO target
- **CRITICAL**: >25% degradation from SLO target

## 🔧 Configuration Options

### Environment Variables

```bash
# Custom storage location
export TORQ_BENCH_STORAGE_PATH=/custom/path/benchmarks

# Default environment
export TORQ_BENCH_ENVIRONMENT=staging

# Custom SLO config location
export TORQ_BENCH_SLO_CONFIG=/path/to/slo.yml
```

### Command Line Options

```bash
# Global options
torq-bench --config slo.yml --environment staging --storage-path ./benchmarks

# Run options
torq-bench run --iterations 20 --warmup 5 --release v1.2.3 --format json --output results.json

# List options
torq-bench list --category interactive --limit 50

# Trends options
torq-bench trends --category interactive --days 30
```

## 🛠 Advanced Usage

### Custom Test Categories

Define new benchmark categories in your SLO config:

```yaml
categories:
  api_calls:
    description: "External API performance tests"
    p95_e2e_ms: 5000
    success_rate: 0.99
    max_memory_mb: 512
    sample_size: 200
```

### Batch Benchmarking

Run benchmarks for multiple configurations:

```bash
#!/bin/bash
# benchmark-suite.sh

ENVIRONMENTS=("development" "staging" "production")
RELEASE=$(git rev-parse --short HEAD)

for env in "${ENVIRONMENTS[@]}"; do
    echo "Running benchmarks for $env environment..."

    torq-bench --environment $env run \
        --release $RELEASE \
        --format json \
        --output "benchmark-${env}-${RELEASE}.json"

    # Check SLO compliance
    if [ $? -ne 0 ]; then
        echo "SLO failures detected in $env environment"
        exit 1
    fi
done

echo "All benchmarks passed!"
```

### Performance Regression Testing

Automated regression detection in CI:

```bash
# Check for regressions compared to baseline
torq-bench regressions

# Exit with error if regressions found
if [ $? -ne 0 ]; then
    echo "Performance regressions detected!"
    exit 1
fi
```

## 📚 API Reference

### BenchmarkRunner

```python
from torq_console.benchmarking import BenchmarkRunner, create_default_tests

# Create runner
runner = BenchmarkRunner()

# Register default tests
for test in create_default_tests():
    runner.register_test(test)

# Run benchmark
result = await runner.run_benchmark(
    "simple_response",
    iterations=20,
    environment="production"
)
```

### BenchmarkReporter

```python
from torq_console.benchmarking import BenchmarkReporter

# Create reporter
reporter = BenchmarkReporter()

# Print full report
reporter.print_full_report(results)

# Generate JSON report
report_data = reporter.generate_json_report(results, output_path="report.json")

# Export CSV
reporter.export_csv_report(results, Path("results.csv"))
```

### BenchmarkStorage

```python
from torq_console.benchmarking import BenchmarkStorage

# Create storage
storage = BenchmarkStorage()

# Store result
storage.store_result(result, release_version="v1.2.3")

# Retrieve results
results = storage.list_results(category="interactive", limit=20)
result = storage.get_result("run_id")

# Get trends
trends = storage.get_trend_data("interactive", "p95_ttfuo_ms", days=30)

# Detect regressions
regressions = storage.detect_regressions("interactive", environment="production")
```

## 🐛 Troubleshooting

### Common Issues

1. **ImportError: No module named 'torq_console.benchmarking'**
   - Ensure you have TORQ Console v0.80.0+ installed
   - Install from source if needed

2. **SLO configuration not found**
   - Check that `slo.yml` exists in current directory or package root
   - Use `--config` to specify custom config path

3. **Benchmark storage errors**
   - Ensure write permissions to `.torq/benchmarks/` directory
   - Use `--storage-path` to specify custom location

4. **Memory errors during benchmarks**
   - Reduce number of concurrent users or iterations
   - Increase sample size multiplier for development environment

### Debug Mode

Enable debug logging:

```bash
# Enable verbose output
torq-bench --verbose run

# Check system status
torq-bench slo
```

### Performance Tuning

Adjust benchmark parameters for your system:

```yaml
# In slo.yml
benchmark:
  default_duration: 300      # Reduce for faster testing
  warmup_iterations: 2       # Fewer warmup iterations
  max_iterations: 100        # Fewer max iterations
  timeout_ms: 60000          # Longer timeout for slow systems
```

## 📖 Examples

### Example 1: Daily Performance Monitoring

```bash
#!/bin/bash
# daily-benchmark.sh

DATE=$(date +%Y%m%d)
RELEASE=$(git rev-parse --short HEAD)
REPORT_DIR="benchmark-reports/$DATE"

mkdir -p "$REPORT_DIR"

echo "Running daily benchmarks for release $RELEASE..."

# Run benchmarks and generate reports
torq-bench run \
    --release $RELEASE \
    --format json \
    --output "$REPORT_DIR/benchmark-$DATE.json"

# Generate trends report
torq-bench trends --category interactive --days 7 > "$REPORT_DIR/trends-$DATE.txt"

# Check for regressions
torq-bench regressions > "$REPORT_DIR/regressions-$DATE.txt"

# SLO compliance summary
torq-bench slo > "$REPORT_DIR/slo-$DATE.txt"

echo "Daily benchmark complete! Results saved to $REPORT_DIR"
```

### Example 2: CI/CD Integration

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  benchmark:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install torq-console

      - name: Run performance benchmarks
        run: |
          torq-bench run \
            --release ${{ github.sha }} \
            --format json \
            --output benchmark-results.json

      - name: Validate SLO compliance
        run: |
          python -c "
          import json
          with open('benchmark-results.json') as f:
              data = json.load(f)
          compliance = data['summary']['overall_slo_compliance']
          print(f'SLO Compliance: {compliance:.1%}')
          if compliance < 0.90:
              print('SLO compliance too low!')
              exit(1)
          "

      - name: Upload benchmark results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: benchmark-results-${{ github.sha }}
          path: |
            benchmark-results.json
            .torq/benchmarks/
```

### Example 3: Custom Benchmark Test

```python
# my_benchmarks.py
import asyncio
import time
from torq_console.benchmarking import BenchmarkRunner, BenchmarkTest

async def database_query_test():
    """Benchmark database query performance."""
    start_time = time.time()

    # Simulate database work
    await asyncio.sleep(0.5)

    # Simulate processing results
    result_count = 100
    await asyncio.sleep(0.2)

    return {
        "query_result_count": result_count,
        "processing_time": (time.time() - start_time) * 1000,
        "tokens_generated": result_count // 10  # 10 tokens per result
    }

async def api_call_test():
    """Benchmark external API call performance."""
    start_time = time.time()

    # Simulate API call
    await asyncio.sleep(1.0)

    return {
        "api_response_size": 2048,  # bytes
        "response_time": (time.time() - start_time) * 1000,
        "tokens_generated": 15
    }

def create_custom_tests():
    """Create custom benchmark tests."""
    return [
        BenchmarkTest(
            name="database_query",
            category="tool_heavy",
            description="Database query performance test",
            test_func=database_query_test,
            timeout_ms=5000,
            expected_tokens=10
        ),
        BenchmarkTest(
            name="api_call",
            category="interactive",
            description="External API call performance test",
            test_func=api_call_test,
            timeout_ms=10000,
            expected_tokens=15
        )
    ]

async def run_custom_benchmarks():
    """Run custom benchmark suite."""
    runner = BenchmarkRunner()

    # Register custom tests
    for test in create_custom_tests():
        runner.register_test(test)

    # Run all custom tests
    results = await runner.run_full_benchmark_suite(
        iterations_per_test=10,
        environment="production"
    )

    # Print results
    from torq_console.benchmarking import BenchmarkReporter
    reporter = BenchmarkReporter()
    reporter.print_full_report([r for cat_results in results.values() for r in cat_results])

if __name__ == "__main__":
    asyncio.run(run_custom_benchmarks())
```

## 🤝 Contributing

Contributions to the benchmarking system are welcome! Please:

1. Follow the existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for any API changes
4. Ensure SLO compliance for any performance-related changes

### Development Setup

```bash
# Clone repository
git clone https://github.com/pilotwaffle/TORQ-CONSOLE.git
cd TORQ-CONSOLE

# Install in development mode
pip install -e ".[dev,benchmarking]"

# Run tests
pytest tests/benchmarking/

# Run benchmarks locally
python -m torq_console.benchmarking run
```

## 📄 License

This benchmarking system is part of TORQ Console and is licensed under the MIT License.