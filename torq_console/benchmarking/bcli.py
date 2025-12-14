"""
Standalone Benchmark CLI Interface for TORQ Console

Provides direct command line interface for benchmarking without nested command complexity.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console

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
def cli(ctx, config, environment, storage_path):
    """TORQ Console Performance Benchmarking System."""
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


@cli.command()
@click.argument('test_name', required=False)
@click.option('--iterations', '-n', default=10, type=int,
              help='Number of benchmark iterations (default: 10)')
@click.option('--warmup', '-w', default=3, type=int,
              help='Number of warmup iterations (default: 3)')
@click.option('--release', '-r', type=str,
              help='Release version for tracking')
@click.option('--output', '-o', type=click.Path(),
              help='Output file for detailed results (JSON format)')
@click.option('--format', 'output_format', default='table',
              type=click.Choice(['table', 'json', 'csv']),
              help='Output format (default: table)')
@click.pass_context
def run(ctx, test_name, iterations, warmup, release, output, output_format):
    """Run performance benchmarks."""
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
                environment=environment, release_version=release
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


@cli.command()
@click.option('--category', '-c', help='Filter by category')
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

    from rich.table import Table
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


@cli.command()
@click.pass_context
def slo(ctx):
    """Show current SLO configuration."""
    slo_config = ctx.obj['slo_config']
    environment = ctx.obj['environment']

    console.print(f"[bold blue]SLO Configuration[/bold blue] (Environment: {environment})")
    console.print(f"Version: {slo_config.version}")
    console.print(f"Last Updated: {slo_config.last_updated}")
    console.print()

    from rich.table import Table
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


def main():
    """Main entry point for benchmark CLI."""
    cli()