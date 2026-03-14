#!/usr/bin/env python3
"""
Federation Simulation Runner

Layer 12 Phase 2A — Federation Stability Validation Harness

Command-line interface for running federation simulations.
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Setup path for imports - need torq_console root in path
# Current file: E:/TORQ-CONSOLE/torq_console/layer12/federation/simulator/run_simulation.py
# We need: E:/TORQ-CONSOLE in sys.path for absolute imports to work
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent.parent.parent.parent  # Go up to E:/TORQ-CONSOLE
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Now we can import from the simulator package
from torq_console.layer12.federation.simulator import (
    get_scenario,
    AsyncFederationSimulationExecutor,
    FederationHealthIndexCalculator,
    AssertionRunner,
    list_scenarios,
    SCENARIO_REGISTRY,
    create_baseline_healthy_assertions,
    create_insight_flooding_assertions,
    create_semantic_monoculture_assertions,
    create_authority_concentration_assertions,
    create_compound_adversarial_assertions,
    create_async_executor,
)


# Configure logging
def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format=format,
        handlers=handlers,
    )

    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def _format_status(status: Any) -> str:
    """Format PredictiveRiskStatus enum or string for display."""
    if hasattr(status, 'value'):
        return status.value.upper().replace('_', ' ')
    return str(status).upper().replace('_', ' ')


def print_simulation_summary(report, assertions=None, runner=None) -> None:
    """Print a comprehensive simulation summary."""
    print("\n" + "="*80)
    print(f"SIMULATION SUMMARY: {report.scenario.name}")
    print("="*80)

    # Basic info
    print(f"Scenario: {report.scenario.description}")
    print(f"Nodes: {report.scenario.num_nodes}")
    print(f"Rounds: {len(report.metrics.round_history)}")
    print(f"Execution Time: {report.execution_time.total_seconds():.2f}s")
    print()

    # Health status
    print("HEALTH STATUS:")
    print(f"  Overall Health Index: {report.metrics.overall_health_index:.3f}")
    print(f"  Status: {report.scenario.name.split('_')[0].title()}")
    print()

    # Category breakdown
    print("CATEGORY BREAKDOWN:")
    categories = [
        ("Diversity Health", report.metrics.diversity_health),
        ("Influence Balance", report.metrics.influence_balance),
        ("Trust Stability", report.metrics.trust_stability),
        ("Quality Integrity", report.metrics.quality_integrity),
        ("Resilience", report.metrics.resilience),
    ]
    for category, score in categories:
        status = "Healthy" if score >= 0.85 else "Stable" if score >= 0.70 else "Degraded"
        print(f"  {category}: {score:.3f} ({status})")
    print()

    # Safeguard triggers
    if report.guardian_triggers_detected:
        print("SAFEGUARD TRIGGERS:")
        for guardian, count in report.guardian_triggers_detected.items():
            print(f"  {guardian}: {count} triggers")
        print()

    # Assertion results
    if assertions and runner:
        print("ASSERTION RESULTS:")
        summary = runner.validate_assertion_results(assertions)
        print(f"  Total: {summary['total']}")
        print(f"  Passed: {summary['passed']} ({summary['pass_rate']:.1%})")
        print(f"  Failed: {summary['failed']}")
        print(f"  Unknown: {summary['unknown']}")

        if summary['critical_failures']:
            print(f"  Critical Failures: {', '.join(summary['critical_failures'])}")

        if summary['recommendations']:
            print("\nRECOMMENDATIONS:")
            for rec in summary['recommendations']:
                print(f"  - {rec}")
        print()

    # Failure points
    if report.failure_points:
        print("FAILURE POINTS:")
        for failure in report.failure_points:
            print(f"  - {failure}")
        print()

    # Key metrics
    print("KEY METRICS:")
    print(f"  Topic Entropy: {report.metrics.topic_entropy:.3f}")
    print(f"  Stance Entropy: {report.metrics.stance_entropy:.3f}")
    print(f"  Gini Coefficient: {report.metrics.gini_coefficient:.3f}")
    print(f"  HHI: {report.metrics.herfindahl_index:.3f}")
    print(f"  Acceptance Rate: {report.metrics.acceptance_rate:.1%}")
    print(f"  Trust Volatility: {report.metrics.trust_volatility:.3f}")
    print()

    # Predictive metrics (EDDR, ACA, FCRI)
    has_predictive_metrics = (
        hasattr(report, 'eddr_result') or
        hasattr(report, 'aca_result') or
        hasattr(report, 'fcri_result')
    )

    if has_predictive_metrics:
        print("PREDICTIVE STABILITY METRICS:")

        # EDDR - Epistemic Diversity Decay Rate
        if hasattr(report, 'eddr_result') and report.eddr_result is not None:
            eddr = report.eddr_result
            print(f"\n  Epistemic Diversity Decay Rate (EDDR):")
            print(f"    Value: {eddr.eddr:.4f}")
            print(f"    Status: {_format_status(eddr.status)}")
            print(f"    Diversity Score: {eddr.current_diversity_score:.3f}")
            print(f"    Window Size: {eddr.window_size} rounds")

            # Additional details if available
            if hasattr(eddr, 'topic_entropy') and eddr.topic_entropy > 0:
                print(f"    Topic Entropy: {eddr.topic_entropy:.3f}")
            if hasattr(eddr, 'stance_entropy') and eddr.stance_entropy > 0:
                print(f"    Stance Entropy: {eddr.stance_entropy:.3f}")
            if hasattr(eddr, 'minority_ratio') and eddr.minority_ratio > 0:
                print(f"    Minority Ratio: {eddr.minority_ratio:.3f}")

            # Notes
            if hasattr(eddr, 'notes') and eddr.notes:
                print(f"    Notes:")
                for note in eddr.notes[:3]:  # Show up to 3 notes
                    print(f"      - {note}")

        # ACA - Authority Capture Acceleration
        if hasattr(report, 'aca_result') and report.aca_result is not None:
            aca = report.aca_result
            print(f"\n  Authority Capture Acceleration (ACA):")
            print(f"    Value: {aca.aca:.4f}")
            print(f"    Status: {_format_status(aca.status)}")
            print(f"    Concentration Score: {aca.current_concentration_score:.3f}")
            print(f"    Window Size: {aca.window_size} rounds")

            # Additional details if available
            if hasattr(aca, 'gini') and aca.gini > 0:
                print(f"    Gini Coefficient: {aca.gini:.3f}")
            if hasattr(aca, 'hhi') and aca.hhi > 0:
                print(f"    Herfindahl Index: {aca.hhi:.3f}")
            if hasattr(aca, 'top_1_share') and aca.top_1_share > 0:
                print(f"    Top-1 Node Share: {aca.top_1_share:.1%}")
            if hasattr(aca, 'top_2_share') and aca.top_2_share > 0:
                print(f"    Top-2 Nodes Share: {aca.top_2_share:.1%}")

            # Dominant nodes
            if hasattr(aca, 'dominant_nodes') and aca.dominant_nodes:
                print(f"    Dominant Nodes: {', '.join(aca.dominant_nodes[:5])}")

            # Dominant domains
            if hasattr(aca, 'dominant_domains') and aca.dominant_domains:
                print(f"    Dominant Domains: {', '.join(aca.dominant_domains[:3])}")

            # Notes
            if hasattr(aca, 'notes') and aca.notes:
                print(f"    Notes:")
                for note in aca.notes[:3]:  # Show up to 3 notes
                    print(f"      - {note}")

        # FCRI - Federation Collapse Risk Index
        if hasattr(report, 'fcri_result') and report.fcri_result is not None:
            fcri = report.fcri_result
            print(f"\n  Federation Collapse Risk Index (FCRI):")
            print(f"    Value: {fcri.fcri:.4f}")
            print(f"    Status: {_format_status(fcri.status)}")
            print(f"    Primary Driver: {fcri.primary_driver}")

            # Component values
            if hasattr(fcri, 'eddr'):
                print(f"    EDDR Component: {fcri.eddr:.4f}")
            if hasattr(fcri, 'aca'):
                print(f"    ACA Component: {fcri.aca:.4f}")

            # Dominant entities
            if hasattr(fcri, 'dominant_nodes') and fcri.dominant_nodes:
                print(f"    At-Risk Nodes: {', '.join(fcri.dominant_nodes[:5])}")
            if hasattr(fcri, 'dominant_domains') and fcri.dominant_domains:
                print(f"    At-Risk Domains: {', '.join(fcri.dominant_domains[:3])}")

            # Recommended actions
            if hasattr(fcri, 'recommended_actions') and fcri.recommended_actions:
                print(f"    Recommended Actions:")
                for action in fcri.recommended_actions[:4]:  # Show top 4 actions
                    print(f"      - {action}")

        print()  # Blank line after predictive metrics

    # Legacy predictive_metrics dict support (for backward compatibility)
    elif hasattr(report, 'predictive_metrics') and report.predictive_metrics:
        print("PREDICTIVE COLLAPSE RISK METRICS:")
        pm = report.predictive_metrics

        # EDDR
        if 'eddr' in pm:
            eddr = pm['eddr']
            print(f"  Epistemic Diversity Decay Rate (EDDR): {eddr.get('value', 0):.4f}")
            print(f"    Status: {eddr.get('status', 'unknown').upper()}")
            if eddr.get('notes'):
                for note in eddr['notes']:
                    print(f"    Note: {note}")

        # ACA
        if 'aca' in pm:
            aca = pm['aca']
            print(f"  Authority Capture Acceleration (ACA): {aca.get('value', 0):.4f}")
            print(f"    Status: {aca.get('status', 'unknown').upper()}")
            if aca.get('dominant_nodes'):
                print(f"    Dominant Nodes: {', '.join(aca['dominant_nodes'])}")

        # FCRI
        if 'fcri' in pm:
            fcri = pm['fcri']
            print(f"  Federation Collapse Risk Index (FCRI): {fcri.get('value', 0):.4f}")
            print(f"    Status: {fcri.get('status', 'unknown').upper()}")
            print(f"    Primary Driver: {fcri.get('primary_driver', 'unknown')}")
            if fcri.get('recommended_actions'):
                print(f"    Recommended Actions:")
                for action in fcri['recommended_actions'][:3]:  # Show top 3
                    print(f"      - {action}")
        print()

    # Recommendations
    if report.recommendations:
        print("RECOMMENDATIONS:")
        for rec in report.recommendations:
            print(f"  - {rec}")
        print()

    print("="*80)


def save_results(report, assertions=None, filename: Optional[str] = None) -> None:
    """Save simulation results to file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simulation_results_{timestamp}.json"

    # Prepare results for JSON serialization
    results = {
        "simulation": {
            "scenario": report.scenario.name,
            "timestamp": report.scenario.name,
            "execution_time_seconds": report.execution_time.total_seconds(),
            "success_rate": report.success_rate,
        },
        "metrics": {
            "overall_health_index": report.metrics.overall_health_index,
            "diversity_health": report.metrics.diversity_health,
            "influence_balance": report.metrics.influence_balance,
            "trust_stability": report.metrics.trust_stability,
            "quality_integrity": report.metrics.quality_integrity,
            "resilience": report.metrics.resilience,
            "detailed_metrics": {
                "topic_entropy": report.metrics.topic_entropy,
                "stance_entropy": report.metrics.stance_entropy,
                "gini_coefficient": report.metrics.gini_coefficient,
                "herfindahl_index": report.metrics.herfindahl_index,
                "average_trust_drift": report.metrics.average_trust_drift,
                "trust_volatility": report.metrics.trust_volatility,
                "acceptance_rate": report.metrics.acceptance_rate,
                "rejection_rate": report.metrics.rejection_rate,
                "spam_detected_rate": report.metrics.spam_detected_rate,
                "duplicate_suppression_rate": report.metrics.duplicate_suppression_rate,
            }
        },
        "safeguard_triggers": dict(report.guardian_triggers_detected),
        "safeguard_effectiveness": report.safeguard_effectiveness,
        "failure_points": report.failure_points,
        "recommendations": report.recommendations,
    }

    # Add predictive metrics if available
    if hasattr(report, 'eddr_result') and report.eddr_result is not None:
        results["predictive_metrics"] = results.get("predictive_metrics", {})
        results["predictive_metrics"]["eddr"] = {
            "value": report.eddr_result.eddr,
            "status": _format_status(report.eddr_result.status),
            "diversity_score": report.eddr_result.current_diversity_score,
        }
    if hasattr(report, 'aca_result') and report.aca_result is not None:
        results["predictive_metrics"] = results.get("predictive_metrics", {})
        results["predictive_metrics"]["aca"] = {
            "value": report.aca_result.aca,
            "status": _format_status(report.aca_result.status),
            "concentration_score": report.aca_result.current_concentration_score,
        }
    if hasattr(report, 'fcri_result') and report.fcri_result is not None:
        results["predictive_metrics"] = results.get("predictive_metrics", {})
        results["predictive_metrics"]["fcri"] = {
            "value": report.fcri_result.fcri,
            "status": _format_status(report.fcri_result.status),
            "primary_driver": report.fcri_result.primary_driver,
        }

    # Add assertion results if available
    if assertions:
        runner = AssertionRunner()
        assertion_summary = runner.validate_assertion_results(assertions)
        results["assertions"] = assertion_summary

    # Save to file
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results saved to: {filename}")


def run_single_scenario(
    scenario_name: str,
    verbose: bool = False,
    save_results_flag: bool = False,
    output_file: Optional[str] = None
) -> None:
    """Run a single simulation scenario."""
    # Setup logging
    setup_logging(verbose)

    # Get scenario
    try:
        scenario = get_scenario(scenario_name)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Running scenario: {scenario.name}")
    print(f"Description: {scenario.description}")

    # Create async executor and run simulation
    async def run_async():
        executor = create_async_executor(
            enable_all_safeguards=True,
            enable_metrics=True,
            enable_health_index=True,
        )
        return await executor.run_simulation(scenario, verbose=verbose)

    # Run the async simulation
    start_time = time.time()
    try:
        report = asyncio.run(run_async())
    except Exception as e:
        print(f"Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    finally:
        end_time = time.time()

    # Run assertions
    runner = AssertionRunner()
    assertions, assertion_registry = runner.run_scenario_assertions(scenario, report)

    # Print summary
    print_simulation_summary(report, assertions, runner)

    # Save results if requested
    if save_results_flag:
        save_results(report, assertions, output_file)

    # Print execution time
    print(f"Total execution time: {end_time - start_time:.2f}s")


def list_available_scenarios() -> None:
    """List all available scenarios."""
    print("Available Scenarios:")
    print("=" * 40)

    scenarios = list_scenarios()
    for name, description in scenarios.items():
        print(f"{name}")
        print(f"  {description}")
        print()


def run_all_scenarios(
    verbose: bool = False,
    save_individual: bool = False,
    summary_file: Optional[str] = None
) -> None:
    """Run all available scenarios."""
    setup_logging(verbose)

    scenarios = list(SCENARIO_REGISTRY.keys())
    results = {}

    print(f"Running {len(scenarios)} scenarios...")
    print("=" * 50)

    async def run_scenario_async(scenario_name):
        """Run a single scenario async."""
        print(f"\nRunning: {scenario_name}")
        try:
            executor = create_async_executor(
                enable_all_safeguards=True,
                enable_metrics=True,
                enable_health_index=True,
            )
            scenario = get_scenario(scenario_name)
            report = await executor.run_simulation(scenario, verbose=False)

            # Run assertions
            runner = AssertionRunner()
            assertions, _ = runner.run_scenario_assertions(scenario, report)
            assertion_summary = runner.validate_assertion_results(assertions)

            # Store results
            result = {
                "health_index": report.metrics.overall_health_index,
                "status": assertion_summary["pass_rate"] > 0.7,
                "pass_rate": assertion_summary["pass_rate"],
                "safeguard_triggers": len(report.guardian_triggers_detected),
                "execution_time": report.execution_time.total_seconds(),
            }

            # Print individual result
            print(f"  Health Index: {report.metrics.overall_health_index:.3f}")
            print(f"  Pass Rate: {assertion_summary['pass_rate']:.1%}")
            print(f"  Execution Time: {report.execution_time.total_seconds():.2f}s")

            # Save individual results if requested
            if save_individual:
                save_results(report, assertions, f"results_{scenario_name}.json")

            return scenario_name, result

        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            return scenario_name, {
                "error": str(e),
                "status": False,
            }

    # Run all scenarios
    async def run_all_async():
        tasks = [run_scenario_async(name) for name in scenarios]
        return await asyncio.gather(*tasks)

    scenario_results = asyncio.run(run_all_async())

    for scenario_name, result in scenario_results:
        results[scenario_name] = result

    # Print summary
    print("\n" + "=" * 50)
    print("ALL SCENARIOS SUMMARY")
    print("=" * 50)

    for scenario_name, result in results.items():
        if "error" in result:
            print(f"{scenario_name}: FAILED - {result['error']}")
        else:
            status = "PASS" if result["status"] else "FAIL"
            print(f"{scenario_name}: {status} (HI: {result['health_index']:.3f}, PR: {result['pass_rate']:.1%})")

    # Save summary if requested
    if summary_file:
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nSummary saved to: {summary_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="TORQ Federation Simulation Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a specific scenario
  python run_simulation.py --scenario baseline_healthy_exchange --verbose

  # Run all scenarios
  python run_simulation.py --all --save-summary all_scenarios.json

  # List available scenarios
  python run_simulation.py --list

  # Save results to file
  python run_simulation.py --scenario semantic_monoculture --save-results --output results.json
        """
    )

    # Main options
    parser.add_argument(
        "--scenario",
        type=str,
        help="Name of scenario to run"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all available scenarios"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--save-results",
        action="store_true",
        help="Save simulation results to file"
    )
    parser.add_argument(
        "--save-individual",
        action="store_true",
        help="Save individual scenario results when running all"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file name for results"
    )
    parser.add_argument(
        "--summary-file",
        type=str,
        help="Summary file name when running all scenarios"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Log file path"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose, args.log_file)

    # Handle list command
    if args.list:
        list_available_scenarios()
        return

    # Handle all scenarios
    if args.all:
        run_all_scenarios(
            verbose=args.verbose,
            save_individual=args.save_individual,
            summary_file=args.summary_file
        )
        return

    # Handle single scenario
    if args.scenario:
        run_single_scenario(
            scenario_name=args.scenario,
            verbose=args.verbose,
            save_results_flag=args.save_results,
            output_file=args.output
        )
        return

    # No command provided
    print("No command provided. Use --help for usage information.")
    print("\nUse --list to see available scenarios.")
    sys.exit(1)


if __name__ == "__main__":
    main()
