#!/usr/bin/env python3
"""
Phase 5.2A Production Readiness Validation

Run 3-5 additional team executions with different objectives
to confirm system stability before moving to Phase 5.2B.

Validates:
- Confidence distribution stability
- Round count stability
- Validator behavior correctness
- Message count reasonableness
"""

import os
import sys
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import datetime
from uuid import uuid4, UUID
from typing import List, Dict, Any
from statistics import mean, stdev

from torq_console.dependencies import get_supabase_client
from torq_console.teams import (
    execute_team_node,
    TeamPersistence,
    TeamDefinitionRegistry,
    initialize_registry,
)


class ProductionValidator:
    """Validate production readiness of agent teams."""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.persistence = TeamPersistence(self.supabase)
        self.results = []

    async def get_test_context(self) -> tuple[UUID, UUID]:
        """Get existing mission and node for testing."""
        missions_result = self.supabase.table("missions").select("*").limit(1).execute()
        if not missions_result.data:
            raise ValueError("No missions found. Create a test mission first.")

        mission_id = UUID(missions_result.data[0]["id"])

        nodes_result = self.supabase.table("mission_nodes").select("*").eq(
            "mission_id", str(mission_id)
        ).limit(1).execute()

        if not nodes_result.data:
            raise ValueError("No nodes found for mission.")

        node_id = UUID(nodes_result.data[0]["id"])

        return mission_id, node_id

    def get_test_objectives(self) -> List[Dict[str, Any]]:
        """Get diverse test objectives for validation."""
        return [
            {
                "name": "Architecture Analysis",
                "team": "research_team",
                "objective": "Analyze TORQ Console architecture and identify key components",
                "constraints": ["Use verified information only", "Focus on execution fabric"],
            },
            {
                "name": "Security Review",
                "team": "research_team",
                "objective": "Review authentication and authorization mechanisms in TORQ Console",
                "constraints": ["Focus on security best practices", "Identify potential vulnerabilities"],
            },
            {
                "name": "Performance Evaluation",
                "team": "research_team",
                "objective": "Evaluate TORQ Console performance characteristics and optimization opportunities",
                "constraints": ["Consider scalability", "Identify bottlenecks"],
            },
            {
                "name": "Integration Planning",
                "team": "planning_team",
                "objective": "Plan integration of a new AI model into TORQ Console",
                "constraints": ["Maintain backward compatibility", "Consider API design"],
            },
            {
                "name": "Code Review Strategy",
                "team": "planning_team",
                "objective": "Design a code review strategy for the TORQ Console codebase",
                "constraints": ["Balance thoroughness with speed", "Consider team size"],
            },
        ]

    async def execute_test(self, test_case: Dict[str, Any], mission_id: UUID, node_id: UUID) -> Dict[str, Any]:
        """Execute a single test case."""
        print(f"\n{'='*60}")
        print(f"Test: {test_case['name']}")
        print(f"Team: {test_case['team']}")
        print(f"{'='*60}")

        start_time = datetime.now()

        try:
            result = await execute_team_node(
                supabase=self.supabase,
                mission_id=mission_id,
                node_id=node_id,
                team_id=test_case["team"],
                objective=test_case["objective"],
                constraints=test_case["constraints"],
            )

            duration = (datetime.now() - start_time).total_seconds()

            # Get execution details
            execution = await self.persistence.get_execution(result.team_execution_id)
            messages = await self.persistence.get_messages(result.team_execution_id)

            test_result = {
                "name": test_case["name"],
                "team": test_case["team"],
                "success": True,
                "duration_seconds": duration,
                "confidence": result.confidence_score,
                "validator_status": str(result.validator_status),
                "rounds": execution.current_round if execution else 0,
                "message_count": len(messages),
                "decision_policy": result.decision_policy,
                "has_dissent": result.dissent_summary.get("has_dissent", False),
                "execution_id": str(result.team_execution_id)[:8],
            }

            self._print_test_result(test_result)
            return test_result

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"[FAIL] Execution error: {e}")

            return {
                "name": test_case["name"],
                "team": test_case["team"],
                "success": False,
                "duration_seconds": duration,
                "error": str(e),
            }

    def _print_test_result(self, result: Dict[str, Any]):
        """Print test result summary."""
        if result["success"]:
            print(f"\n[OK] Execution completed")
            print(f"  Duration: {result['duration_seconds']:.2f}s")
            print(f"  Confidence: {result['confidence']:.2f}")
            print(f"  Validator: {result['validator_status']}")
            print(f"  Rounds: {result['rounds']}")
            print(f"  Messages: {result['message_count']}")
            print(f"  Policy: {result['decision_policy']}")
            print(f"  Dissent: {result['has_dissent']}")
            print(f"  ID: {result['execution_id']}...")
        else:
            print(f"\n[FAIL] {result.get('error', 'Unknown error')}")

    async def run_validation(self, num_tests: int = 5):
        """Run production readiness validation."""
        print("="*60)
        print("PHASE 5.2A PRODUCTION READINESS VALIDATION")
        print("="*60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Initialize registry
        registry = TeamDefinitionRegistry()
        await registry.initialize(self.supabase, load_from_db=True)

        # Get test context
        mission_id, node_id = await self.get_test_context()
        print(f"\nTest Context:")
        print(f"  Mission: {str(mission_id)[:8]}...")
        print(f"  Node: {str(node_id)[:8]}...")

        # Get test cases
        test_cases = self.get_test_objectives()[:num_tests]

        print(f"\nRunning {len(test_cases)} validation tests...")

        # Execute tests
        for test_case in test_cases:
            result = await self.execute_test(test_case, mission_id, node_id)
            self.results.append(result)

        # Analyze results
        self._analyze_results()

    def _analyze_results(self):
        """Analyze validation results and assess production readiness."""
        print("\n" + "="*60)
        print("PRODUCTION READINESS ANALYSIS")
        print("="*60)

        successful = [r for r in self.results if r["success"]]
        failed = [r for r in self.results if not r["success"]]

        print(f"\nExecution Summary:")
        print(f"  Total: {len(self.results)}")
        print(f"  Successful: {len(successful)}")
        print(f"  Failed: {len(failed)}")

        if not successful:
            print("\n[FAIL] No successful executions. System not production-ready.")
            return

        # Confidence analysis
        confidences = [r["confidence"] for r in successful]
        print(f"\nConfidence Distribution:")
        print(f"  Mean: {mean(confidences):.3f}")
        print(f"  Min: {min(confidences):.3f}")
        print(f"  Max: {max(confidences):.3f}")
        if len(confidences) > 1:
            print(f"  StdDev: {stdev(confidences):.3f}")

        # Round analysis
        rounds = [r["rounds"] for r in successful]
        print(f"\nRound Count:")
        print(f"  Mean: {mean(rounds):.1f}")
        print(f"  Min: {min(rounds)}")
        print(f"  Max: {max(rounds)}")

        # Message count analysis
        messages = [r["message_count"] for r in successful]
        print(f"\nMessage Count:")
        print(f"  Mean: {mean(messages):.1f}")
        print(f"  Min: {min(messages)}")
        print(f"  Max: {max(messages)}")

        # Duration analysis
        durations = [r["duration_seconds"] for r in successful]
        print(f"\nExecution Duration:")
        print(f"  Mean: {mean(durations):.2f}s")
        print(f"  Min: {min(durations):.2f}s")
        print(f"  Max: {max(durations):.2f}s")

        # Validator status distribution
        validator_counts = {}
        for r in successful:
            status = r["validator_status"]
            validator_counts[status] = validator_counts.get(status, 0) + 1

        print(f"\nValidator Status Distribution:")
        for status, count in validator_counts.items():
            print(f"  {status}: {count}")

        # Dissent analysis
        dissent_count = sum(1 for r in successful if r.get("has_dissent", False))
        print(f"\nDissent Analysis:")
        print(f"  With dissent: {dissent_count}/{len(successful)}")

        # Production readiness assessment
        print("\n" + "="*60)
        print("PRODUCTION READINESS ASSESSMENT")
        print("="*60)

        checks = {
            "Success Rate > 80%": len(successful) / len(self.results) >= 0.8,
            "Confidence Stable (stdev < 0.15)": stdev(confidences) < 0.15 if len(confidences) > 1 else True,
            "Rounds As Expected (all 3)": all(r == 3 for r in rounds),
            "Messages Reasonable (12-18)": all(12 <= m <= 18 for m in messages),
            "No Crashes": len(failed) == 0,
        }

        for check, passed in checks.items():
            status = "[OK]" if passed else "[WARN]"
            print(f"{status} {check}")

        all_passed = all(checks.values())

        print("\n" + "="*60)
        if all_passed:
            print("[SUCCESS] PHASE 5.2A PRODUCTION-READY")
            print("="*60)
            print("\nAll stability checks passed.")
            print("System is ready for Phase 5.2B: Observability + UI")
        else:
            print("[WARNING] PHASE 5.2A NEEDS ATTENTION")
            print("="*60)
            failed_checks = [c for c, p in checks.items() if not p]
            print(f"\nFailed checks: {', '.join(failed_checks)}")


async def main():
    """Run production readiness validation."""
    validator = ProductionValidator()

    # Run 5 tests (can be adjusted via command line)
    num_tests = 5
    if len(sys.argv) > 1:
        try:
            num_tests = int(sys.argv[1])
        except ValueError:
            pass

    await validator.run_validation(num_tests)


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(0 if exit_code is None else 1)
