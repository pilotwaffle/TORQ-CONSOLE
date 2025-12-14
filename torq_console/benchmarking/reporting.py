"""
Benchmark Performance Reporting

Generates detailed performance reports, visualizations, and SLO compliance analysis.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, BarColumn, TaskProgressColumn
from rich.tree import Tree
import rich.repr

from .slo_config import SLOConfig
from .storage import BenchmarkResult, BenchmarkStorage


class BenchmarkReporter:
    """Generates comprehensive benchmark reports."""

    def __init__(self, slo_config: Optional[SLOConfig] = None,
                 storage: Optional[BenchmarkStorage] = None,
                 console: Optional[Console] = None):
        """Initialize benchmark reporter.

        Args:
            slo_config: SLO configuration. If None, loads default.
            storage: Storage backend. If None, creates default.
            console: Rich console for output. If None, creates new.
        """
        self.slo_config = slo_config or SLOConfig.load_default()
        self.storage = storage or BenchmarkStorage()
        self.console = console or Console()

    def format_result_summary(self, result: BenchmarkResult) -> Table:
        """Create a rich table showing benchmark result summary."""
        table = Table(title=f"Benchmark Result: {result.test_name}", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Value", style="green")
        table.add_column("Target", style="yellow")
        table.add_column("Status", style="bold")

        # Basic metrics
        table.add_row("Category", result.category, "", "")
        table.add_row("Environment", result.environment, "", "")
        table.add_row("Iterations", f"{result.successful_iterations}/{result.total_iterations}", "", "")
        table.add_row("Success Rate", f"{result.success_rate:.1%}", "", "")

        # Performance metrics
        if result.p50_duration is not None:
            table.add_row("p50 Duration", f"{result.p50_duration:.0f}ms", "", "")
        if result.p95_duration is not None:
            table.add_row("p95 Duration", f"{result.p95_duration:.0f}ms", "", "")

        # Primary metric (SLO target)
        slo_category = self.slo_config.get_category(result.category, result.environment)
        primary_metric = slo_category.get_primary_metric()
        primary_target = slo_category.get_primary_target()
        primary_value = getattr(result, 'p95_primary', None)

        if primary_value is not None:
            metric_name = primary_metric.replace('_', ' ').title()
            table.add_row(
                f"p95 {metric_name}",
                f"{primary_value:.0f}ms",
                f"{primary_target}ms",
                "✅ PASS" if result.slo_met else "❌ FAIL"
            )

        # Token metrics
        if result.avg_tokens_per_sec is not None:
            table.add_row("Tokens/sec", f"{result.avg_tokens_per_sec:.1f}", "", "")
        if result.cost_per_success is not None:
            table.add_row("Cost/Success", f"${result.cost_per_success:.4f}", "", "")

        # SLO compliance
        degradation_style = {
            "ok": "green",
            "warning": "yellow",
            "critical": "red"
        }.get(result.slo_degradation_level, "white")

        table.add_row(
            "SLO Status",
            result.slo_degradation_level.upper(),
            "",
            f"[{degradation_style}]{result.slo_degradation_level.upper()}[/{degradation_style}]"
        )

        return table

    def format_comparison_table(self, results: List[BenchmarkResult]) -> Table:
        """Create a comparison table for multiple benchmark results."""
        if not results:
            return Table(title="No Results")

        table = Table(title="Benchmark Comparison", show_header=True, header_style="bold magenta")
        table.add_column("Test Name", style="cyan")
        table.add_column("Category", style="blue")
        table.add_column("Iterations", justify="center")
        table.add_column("Success Rate", justify="right")
        table.add_column("p95 Primary", justify="right")
        table.add_column("Tokens/sec", justify="right")
        table.add_column("Cost", justify="right")
        table.add_column("SLO", justify="center")

        for result in results:
            slo_indicator = "✅" if result.slo_met else "❌"
            cost_str = f"${result.cost_per_success:.4f}" if result.cost_per_success else "N/A"
            tokens_str = f"{result.avg_tokens_per_sec:.1f}" if result.avg_tokens_per_sec else "N/A"
            p95_str = f"{result.p95_primary:.0f}ms" if result.p95_primary else "N/A"

            table.add_row(
                result.test_name,
                result.category,
                f"{result.successful_iterations}/{result.total_iterations}",
                f"{result.success_rate:.1%}",
                p95_str,
                tokens_str,
                cost_str,
                slo_indicator
            )

        return table

    def format_slo_summary(self, results: List[BenchmarkResult]) -> Panel:
        """Create an SLO compliance summary panel."""
        if not results:
            return Panel("No results to analyze", title="SLO Summary")

        total_tests = len(results)
        slo_met_count = sum(1 for r in results if r.slo_met)
        slo_met_rate = slo_met_count / total_tests

        # Count by degradation level
        degradation_counts = {}
        for result in results:
            level = result.slo_degradation_level
            degradation_counts[level] = degradation_counts.get(level, 0) + 1

        # Build summary text
        summary_text = f"""
Overall SLO Compliance: {slo_met_rate:.1%} ({slo_met_count}/{total_tests})

Breakdown by Degradation Level:
• ✅ OK: {degradation_counts.get('ok', 0)} tests
• ⚠️ WARNING: {degradation_counts.get('warning', 0)} tests
• ❌ CRITICAL: {degradation_counts.get('critical', 0)} tests

Average Performance:
• Mean Success Rate: {np.mean([r.success_rate for r in results]):.1%}
• Mean Tokens/sec: {np.mean([r.avg_tokens_per_sec for r in results if r.avg_tokens_per_sec]):.1f}
• Mean Cost/Success: ${np.mean([r.cost_per_success for r in results if r.cost_per_success]):.4f}
        """.strip()

        style = "green" if slo_met_rate >= 0.9 else "yellow" if slo_met_rate >= 0.7 else "red"
        return Panel(summary_text, title="SLO Compliance Summary", border_style=style)

    def format_performance_trends(self, category: str, days: int = 30,
                                 environment: str = "production") -> Table:
        """Create a performance trends table."""
        slo_category = self.slo_config.get_category(category, environment)
        primary_metric = slo_category.get_primary_metric()

        trend_data = self.storage.get_trend_data(category, primary_metric, days, environment)

        if not trend_data:
            return Table(title=f"No trend data for {category} in last {days} days")

        table = Table(title=f"Performance Trends: {category} ({primary_metric})", show_header=True)
        table.add_column("Date", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Target", style="yellow")
        table.add_column("Status", justify="center")
        table.add_column("Release", style="blue")

        for data_point in trend_data[-10:]:  # Show last 10 data points
            timestamp = datetime.fromisoformat(data_point['timestamp']).strftime("%Y-%m-%d %H:%M")
            value = data_point['metric_value']
            target = data_point['slo_target']
            degradation = data_point['degradation_level']

            status_style = {
                "ok": "green",
                "warning": "yellow",
                "critical": "red"
            }.get(degradation, "white")

            status_text = f"[{status_style}]{degradation.upper()}[/{status_style}]"

            table.add_row(
                timestamp,
                f"{value:.0f}",
                f"{target:.0f}",
                status_text,
                data_point.get('release_version', 'N/A')
            )

        return table

    def format_regression_report(self, environment: str = "production") -> Tree:
        """Create a regression detection report tree."""
        tree = Tree("🔍 Performance Regression Detection")

        categories = self.slo_config.list_categories()
        regressions_found = False

        for category in categories:
            regressions = self.storage.detect_regressions(category, environment)

            if regressions:
                regressions_found = True
                category_branch = tree.add(f"📊 {category}")

                for regression in regressions:
                    metric_name = regression['metric_name'].replace('_', ' ').title()
                    avg_value = regression['avg_value']
                    target = regression['slo_target']
                    degradation_level = regression['degradation_level']

                    regression_text = (
                        f"⚠️ {metric_name}: {avg_value:.0f} vs target {target:.0f} "
                        f"({degradation_level.upper()})"
                    )

                    style = "red" if degradation_level == "critical" else "yellow"
                    category_branch.add(f"[{style}]{regression_text}[/{style}]")

        if not regressions_found:
            tree.add("✅ No performance regressions detected")

        return tree

    def generate_json_report(self, results: List[BenchmarkResult],
                           output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Generate comprehensive JSON report."""
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "slo_config_version": self.slo_config.version,
                "total_results": len(results)
            },
            "summary": {
                "overall_slo_compliance": sum(1 for r in results if r.slo_met) / len(results) if results else 0,
                "total_tests": len(results),
                "successful_tests": sum(1 for r in results if r.success_rate > 0.5),
                "categories": list(set(r.category for r in results)),
                "environments": list(set(r.environment for r in results))
            },
            "results": [result.dict() for result in results],
            "slo_analysis": self._analyze_slo_compliance(results),
            "performance_analysis": self._analyze_performance_trends(results),
            "cost_analysis": self._analyze_costs(results)
        }

        if output_path:
            output_path.write_text(json.dumps(report, indent=2), encoding='utf-8')

        return report

    def _analyze_slo_compliance(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Analyze SLO compliance across results."""
        analysis = {
            "overall_compliance_rate": 0,
            "compliance_by_category": {},
            "degradation_levels": {"ok": 0, "warning": 0, "critical": 0},
            "failing_tests": []
        }

        if not results:
            return analysis

        analysis["overall_compliance_rate"] = sum(1 for r in results if r.slo_met) / len(results)

        # Group by category
        for category in set(r.category for r in results):
            category_results = [r for r in results if r.category == category]
            compliance_rate = sum(1 for r in category_results if r.slo_met) / len(category_results)
            analysis["compliance_by_category"][category] = {
                "compliance_rate": compliance_rate,
                "total_tests": len(category_results),
                "passing_tests": sum(1 for r in category_results if r.slo_met)
            }

        # Count degradation levels
        for result in results:
            analysis["degradation_levels"][result.slo_degradation_level] += 1
            if not result.slo_met:
                analysis["failing_tests"].append({
                    "test_name": result.test_name,
                    "category": result.category,
                    "degradation_level": result.slo_degradation_level,
                    "p95_primary": result.p95_primary
                })

        return analysis

    def _analyze_performance_trends(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Analyze performance trends across results."""
        analysis = {
            "performance_by_category": {},
            "outliers": []
        }

        # Group by category
        for category in set(r.category for r in results):
            category_results = [r for r in results if r.category == category]
            p95_values = [r.p95_primary for r in category_results if r.p95_primary is not None]

            if p95_values:
                analysis["performance_by_category"][category] = {
                    "mean_p95": np.mean(p95_values),
                    "median_p95": np.median(p95_values),
                    "std_p95": np.std(p95_values),
                    "min_p95": np.min(p95_values),
                    "max_p95": np.max(p95_values)
                }

                # Identify outliers (values > 2 standard deviations from mean)
                mean_val = np.mean(p95_values)
                std_val = np.std(p95_values)
                threshold = mean_val + 2 * std_val

                for result in category_results:
                    if result.p95_primary and result.p95_primary > threshold:
                        analysis["outliers"].append({
                            "test_name": result.test_name,
                            "category": category,
                            "p95_primary": result.p95_primary,
                            "threshold": threshold
                        })

        return analysis

    def _analyze_costs(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Analyze cost metrics across results."""
        costs = [r.cost_per_success for r in results if r.cost_per_success is not None]
        total_costs = [r.total_cost for r in results if r.total_cost is not None]

        analysis = {
            "cost_per_success_stats": {},
            "total_cost_stats": {},
            "cost_by_category": {}
        }

        if costs:
            analysis["cost_per_success_stats"] = {
                "mean": np.mean(costs),
                "median": np.median(costs),
                "std": np.std(costs),
                "min": np.min(costs),
                "max": np.max(costs)
            }

        if total_costs:
            analysis["total_cost_stats"] = {
                "mean": np.mean(total_costs),
                "median": np.median(total_costs),
                "std": np.std(total_costs),
                "min": np.min(total_costs),
                "max": np.max(total_costs),
                "total": np.sum(total_costs)
            }

        # Cost by category
        for category in set(r.category for r in results):
            category_costs = [r.cost_per_success for r in results
                            if r.category == category and r.cost_per_success is not None]
            if category_costs:
                analysis["cost_by_category"][category] = {
                    "mean": np.mean(category_costs),
                    "median": np.median(category_costs),
                    "total": np.sum(category_costs)
                }

        return analysis

    def print_full_report(self, results: List[BenchmarkResult],
                         include_trends: bool = True,
                         include_regressions: bool = True) -> None:
        """Print a comprehensive benchmark report to the console."""
        if not results:
            self.console.print("[yellow]No benchmark results to report[/yellow]")
            return

        # Title
        self.console.print()
        self.console.print("🎯 TORQ Console Benchmark Report", style="bold blue", justify="center")
        self.console.print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim", justify="center")
        self.console.print()

        # SLO Summary
        self.console.print(self.format_slo_summary(results))
        self.console.print()

        # Comparison Table
        self.console.print(self.format_comparison_table(results))
        self.console.print()

        # Detailed results
        for result in results:
            self.console.print(self.format_result_summary(result))
            self.console.print()

        # Performance trends
        if include_trends:
            categories = set(r.category for r in results)
            for category in categories:
                try:
                    trends_table = self.format_performance_trends(category)
                    self.console.print(trends_table)
                    self.console.print()
                except Exception:
                    # Skip trends if data not available
                    pass

        # Regression report
        if include_regressions:
            self.console.print("📊 Performance Regression Analysis")
            regression_tree = self.format_regression_report()
            self.console.print(regression_tree)
            self.console.print()

    def export_csv_report(self, results: List[BenchmarkResult], output_path: Path) -> None:
        """Export benchmark results to CSV format."""
        import csv

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'run_id', 'test_name', 'category', 'environment', 'timestamp',
                'total_iterations', 'successful_iterations', 'success_rate',
                'p50_duration', 'p90_duration', 'p95_duration', 'p99_duration',
                'p50_primary', 'p90_primary', 'p95_primary', 'p99_primary',
                'total_tokens', 'avg_tokens_per_sec', 'total_cost', 'cost_per_success',
                'slo_met', 'slo_degradation_level'
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                row = {
                    'run_id': result.run_id,
                    'test_name': result.test_name,
                    'category': result.category,
                    'environment': result.environment,
                    'timestamp': result.timestamp.isoformat(),
                    'total_iterations': result.total_iterations,
                    'successful_iterations': result.successful_iterations,
                    'success_rate': result.success_rate,
                    'p50_duration': result.p50_duration,
                    'p90_duration': result.p90_duration,
                    'p95_duration': result.p95_duration,
                    'p99_duration': result.p99_duration,
                    'p50_primary': result.p50_primary,
                    'p90_primary': result.p90_primary,
                    'p95_primary': result.p95_primary,
                    'p99_primary': result.p99_primary,
                    'total_tokens': result.total_tokens,
                    'avg_tokens_per_sec': result.avg_tokens_per_sec,
                    'total_cost': result.total_cost,
                    'cost_per_success': result.cost_per_success,
                    'slo_met': result.slo_met,
                    'slo_degradation_level': result.slo_degradation_level
                }
                writer.writerow(row)