"""
Benchmark CLI Commands for TORQ Console

Provides Click-based command line interface for benchmarking and SLO management.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.table import Table

from .slo_config import SLOConfig
from .runner import BenchmarkRunner, create_default_tests
from .storage import BenchmarkStorage
from .reporting import BenchmarkReporter


console = Console()


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True),
              help='SLO configuration file path')
@click.option('--environment', '-e', default='production',
              type=click.Choice(['development', 'staging', 'production']),
              help='Environment for SLO evaluation')
@click.option('--storage-path', type=click.Path(),
              help='Custom storage path for benchmark results')
@click.pass_context
def bench(ctx, config, environment, storage_path):
    """TORQ Console Performance Benchmarking System.

    Run performance benchmarks, monitor SLO compliance, and track performance trends.
    """
    ctx.ensure_object(dict)

    # Load SLO configuration
    try:
        if config:
            slo_config = SLOConfig.load_from_file(config)
        else:
            slo_config = SLOConfig.load_default()
    except Exception as e:
        console.print(f"[red]Error loading SLO configuration:[/red] {e}")
        sys.exit(1)

    # Initialize components
    storage_path = Path(storage_path) if storage_path else None
    storage = BenchmarkStorage(storage_path)
    reporter = BenchmarkReporter(slo_config, storage, console)

    ctx.obj['slo_config'] = slo_config
    ctx.obj['environment'] = environment
    ctx.obj['storage'] = storage
    ctx.obj['reporter'] = reporter


@bench.command()
@click.argument('test_name', required=False)
@click.option('--iterations', '-n', default=10, type=int,
              help='Number of benchmark iterations (default: 10)')
@click.option('--warmup', '-w', default=3, type=int,
              help='Number of warmup iterations (default: 3)')
@click.option('--concurrent', default=1, type=int,
              help='Number of concurrent users (default: 1)')
@click.option('--release', '-r', type=str,
              help='Release version for tracking')
@click.option('--output', '-o', type=click.Path(),
              help='Output file for detailed results (JSON format)')
@click.option('--format', 'output_format', default='table',
              type=click.Choice(['table', 'json', 'csv']),
              help='Output format (default: table)')
@click.option('--no-report', is_flag=True,
              help='Skip detailed report generation')
@click.pass_context
def run(ctx, test_name, iterations, warmup, concurrent, release, output, output_format, no_report):
    """Run performance benchmarks.

    Examples:
      torq bench run                    # Run all tests
      torq bench run simple_response    # Run specific test
      torq bench run --iterations 20    # Run with more iterations
      torq bench run --release v1.2.3   # Tag with release version
    """
    slo_config = ctx.obj['slo_config']
    environment = ctx.obj['environment']
    storage = ctx.obj['storage']
    reporter = ctx.obj['reporter']

    async def run_benchmark():
        # Initialize benchmark runner
        runner = BenchmarkRunner(slo_config, storage, console)

        # Register default tests
        for test in create_default_tests():
            runner.register_test(test)

        results = []

        if test_name:
            # Run specific test
            if test_name not in runner.list_tests():
                console.print(f"[red]Test not found:[/red] {test_name}")
                console.print(f"Available tests: {', '.join(runner.list_tests())}")
                sys.exit(1)

            console.print(f"[cyan]Running benchmark:[/cyan] {test_name}")
            result = await runner.run_benchmark(
                test_name, iterations=iterations, warmup_iterations=warmup,
                concurrent_users=concurrent, environment=environment,
                release_version=release
            )
            results.append(result)

        else:
            # Run all tests
            console.print("[cyan]Running full benchmark suite[/cyan]")
            category_results = await runner.run_full_benchmark_suite(
                iterations_per_test=iterations, environment=environment,
                release_version=release
            )

            # Flatten results
            for category_results in category_results.values():
                results.extend(category_results)

        # Generate output
        if not no_report:
            if output_format == 'table':
                reporter.print_full_report(results)
            elif output_format == 'json':
                report_data = reporter.generate_json_report(results)
                if output:
                    Path(output).write_text(json.dumps(report_data, indent=2))
                    console.print(f"[green]JSON report saved to:[/green] {output}")
                else:
                    console.print_json(data=report_data)
            elif output_format == 'csv':
                if not output:
                    console.print("[red]Error: --output required for CSV format[/red]")
                    sys.exit(1)
                reporter.export_csv_report(results, Path(output))
                console.print(f"[green]CSV report saved to:[/green] {output}")

        # Exit with error code if any SLOs failed
        failed_slos = sum(1 for r in results if not r.slo_met)
        if failed_slos > 0:
            console.print(f"[red]Benchmark completed with {failed_slos} SLO failures[/red]")
            sys.exit(1)
        else:
            console.print("[green]All benchmarks passed SLO requirements[/green]")

    # Run the async benchmark
    asyncio.run(run_benchmark())


@bench.command()
@click.option('--category', '-c',
              help='Filter by category')
@click.option('--limit', '-l', default=20, type=int,
              help='Number of results to show (default: 20)')
@click.pass_context
def list(ctx, category, limit):
    """List recent benchmark results."""
    storage = ctx.obj['storage']
    environment = ctx.obj['environment']

    results = storage.list_results(category=category, environment=environment, limit=limit)

    if not results:
        console.print("[yellow]No benchmark results found[/yellow]")
        return

    table = Table(title="Recent Benchmark Results")
    table.add_column("Run ID", style="cyan", width=8)
    table.add_column("Test Name", style="green")
    table.add_column("Category", style="blue")
    table.add_column("Environment", style="magenta")
    table.add_column("Success Rate", justify="right")
    table.add_column("SLO Status", justify="center")
    table.add_column("Timestamp", style="dim")

    for result in results:
        slo_status = "✅" if result['slo_met'] else "❌"
        success_rate = f"{result['success_rate']:.1%}"
        timestamp = result['timestamp'][:19].replace('T', ' ')

        table.add_row(
            result['run_id'][:8],
            result['test_name'],
            result['category'],
            result['environment'],
            success_rate,
            slo_status,
            timestamp
        )

    console.print(table)


@bench.command()
@click.argument('run_id')
@click.pass_context
def show(ctx, run_id):
    """Show detailed benchmark result."""
    storage = ctx.obj['storage']
    reporter = ctx.obj['reporter']

    result = storage.get_result(run_id)
    if not result:
        console.print(f"[red]Benchmark result not found:[/red] {run_id}")
        sys.exit(1)

    console.print(reporter.format_result_summary(result))


@bench.command()
@click.option('--category', '-c', required=True,
              help='Category to analyze')
@click.option('--days', '-d', default=30, type=int,
              help='Number of days to analyze (default: 30)')
@click.pass_context
def trends(ctx, category, days):
    """Show performance trends for a category."""
    reporter = ctx.obj['reporter']
    environment = ctx.obj['environment']

    try:
        trends_table = reporter.format_performance_trends(category, days, environment)
        console.print(trends_table)
    except Exception as e:
        console.print(f"[red]Error generating trends:[/red] {e}")


@bench.command()
@click.pass_context
def regressions(ctx):
    """Show performance regression analysis."""
    reporter = ctx.obj['reporter']
    environment = ctx.obj['environment']

    regression_tree = reporter.format_regression_report(environment)
    console.print(regression_tree)


@bench.command()
@click.argument('release_version')
@click.pass_context
def release(ctx, release_version):
    """Show performance summary for a release."""
    storage = ctx.obj['storage']

    try:
        summary = storage.get_release_summary(release_version)
        if not summary:
            console.print(f"[yellow]No data found for release:[/yellow] {release_version}")
            return

        # Display release summary
        console.print(f"[bold blue]Release Summary:[/bold blue] {release_version}")
        console.print()

        # Basic stats
        table = Table(title="Overview")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Runs", str(summary['total_runs']))
        table.add_row("Overall Success Rate", f"{summary['overall_success_rate']:.1%}")
        table.add_row("SLO Compliance Rate", f"{summary['slo_compliance_rate']:.1%}")
        if summary['avg_cost_per_success']:
            table.add_row("Avg Cost/Success", f"${summary['avg_cost_per_success']:.4f}")
        if summary['total_cost']:
            table.add_row("Total Cost", f"${summary['total_cost']:.4f}")

        console.print(table)
        console.print()

        # Category breakdown
        if summary['categories']:
            cat_table = Table(title="Category Performance")
            cat_table.add_column("Category", style="cyan")
            cat_table.add_column("Runs", justify="center")
            cat_table.add_column("Success Rate", justify="right")
            cat_table.add_column("SLO Compliance", justify="center")
            cat_table.add_column("Avg p95", justify="right")

            for cat_name, cat_data in summary['categories'].items():
                slo_indicator = f"{cat_data['slo_compliance']:.1%}"
                avg_p95 = f"{cat_data['avg_p95_primary']:.0f}ms" if cat_data['avg_p95_primary'] else "N/A"

                cat_table.add_row(
                    cat_name,
                    str(cat_data['runs']),
                    f"{cat_data['success_rate']:.1%}",
                    slo_indicator,
                    avg_p95
                )

            console.print(cat_table)

    except Exception as e:
        console.print(f"[red]Error generating release summary:[/red] {e}")


@bench.command()
@click.pass_context
def slo(ctx):
    """Show current SLO configuration."""
    slo_config = ctx.obj['slo_config']
    environment = ctx.obj['environment']

    console.print(f"[bold blue]SLO Configuration[/bold blue] (Environment: {environment})")
    console.print(f"Version: {slo_config.version}")
    console.print(f"Last Updated: {slo_config.last_updated}")
    console.print()

    table = Table(title="Service Level Objectives")
    table.add_column("Category", style="cyan")
    table.add_column("Primary Metric", style="green")
    table.add_column("Target", style="yellow")
    table.add_column("Success Rate", style="blue")
    table.add_column("Description", style="dim")

    for category_name, category in slo_config.categories.items():
        # Get environment-adjusted values
        env_category = slo_config.get_category(category_name, environment)
        primary_metric = env_category.get_primary_metric()
        primary_target = env_category.get_primary_target()

        # Format metric name
        metric_display = primary_metric.replace('_', ' ').title()

        # Format target with unit
        if primary_metric.endswith('_ms'):
            target_display = f"{primary_target}ms"
        else:
            target_display = str(primary_target)

        table.add_row(
            category_name,
            metric_display,
            target_display,
            f"{env_category.success_rate:.1%}",
            env_category.description
        )

    console.print(table)


@bench.command()
@click.argument('category_name')
@click.argument('metric_name')
@click.argument('metric_value', type=float)
@click.option('--environment', '-e', default='production',
              type=click.Choice(['development', 'staging', 'production']),
              help='Environment to validate against')
@click.pass_context
def validate(ctx, category_name, metric_name, metric_value, environment):
    """Validate a metric against SLO requirements.

    Examples:
      torq bench validate interactive p95_ttfuo_ms 2400
      torq bench validate tool_heavy p95_e2e_ms 28000
    """
    slo_config = ctx.obj['slo_config']

    try:
        # Check if metric meets SLO
        slo_met = slo_config.validate_slo(category_name, metric_value, metric_name, environment)
        degradation_level = slo_config.get_degradation_level(category_name, metric_value, metric_name, environment)

        # Get target value for comparison
        category = slo_config.get_category(category_name, environment)
        target_value = getattr(category, metric_name, None)

        if target_value is None:
            console.print(f"[yellow]Warning:[/yellow] Metric '{metric_name}' not defined for category '{category_name}'")
            console.print(f"  Value: {metric_value}")
            return

        # Display results
        status_color = "green" if slo_met else "red"
        degradation_color = {
            "ok": "green",
            "warning": "yellow",
            "critical": "red"
        }.get(degradation_level, "white")

        console.print(f"[bold]SLO Validation:[/bold] {category_name}.{metric_name}")
        console.print(f"Environment: {environment}")
        console.print()
        console.print(f"Value:     {metric_value}")
        console.print(f"Target:    {target_value}")
        console.print(f"Status:    [{status_color}]{'PASS' if slo_met else 'FAIL'}[/{status_color}]")
        console.print(f"Level:     [{degradation_color}]{degradation_level.upper()}[/{degradation_color}]")

        # Calculate degradation percentage
        if metric_name.endswith('_ms'):
            degradation = ((metric_value - target_value) / target_value) * 100
        else:
            degradation = ((target_value - metric_value) / target_value) * 100

        console.print(f"Degradation: {degradation:+.1f}%")

    except Exception as e:
        console.print(f"[red]Error validating SLO:[/red] {e}")
        sys.exit(1)


def create_benchmark_commands():
    """Create benchmark command group for integration with main CLI."""
    return bench