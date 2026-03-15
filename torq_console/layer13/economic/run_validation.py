"""TORQ Layer 13 - Validation CLI

Command-line interface for running Layer 13 validation tests.

Usage:
    python -m torq_console.layer13.economic.run_validation [--scenarios SCENARIOS] [--verbose]
"""

import argparse
import asyncio
import sys

from .validation import ValidationRunner
from .validation.scenario_definitions import list_scenario_names
from . import (
    create_allocation_engine,
    create_evaluation_engine,
    create_opportunity_cost_model,
    create_prioritization_engine,
)


async def main():
    """Main entry point for validation CLI."""
    parser = argparse.ArgumentParser(
        description="TORQ Layer 13 Economic Intelligence Validation"
    )
    parser.add_argument(
        "--scenarios",
        type=str,
        help="Comma-separated list of scenario names (default: all)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios",
    )

    args = parser.parse_args()

    # List scenarios if requested
    if args.list:
        print("Available validation scenarios:")
        for name in list_scenario_names():
            print(f"  - {name}")
        return 0

    # Parse scenario names
    scenario_names = None
    if args.scenarios:
        scenario_names = [s.strip() for s in args.scenarios.split(",")]

    # Create engines
    evaluation_engine = create_evaluation_engine()
    prioritization_engine = create_prioritization_engine()
    allocation_engine = create_allocation_engine()
    opportunity_model = create_opportunity_cost_model()

    # Create validation runner
    runner = ValidationRunner()

    # Run scenarios
    results = await runner.run_all_scenarios(
        evaluation_engine,
        prioritization_engine,
        allocation_engine,
        opportunity_model,
        scenario_names,
    )

    # Print results
    runner.print_results(results, verbose=args.verbose)
    runner.print_summary(results)

    # Return exit code
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
