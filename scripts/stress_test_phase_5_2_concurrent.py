#!/usr/bin/env python3
"""
Phase 5.2A Concurrent Execution Stress Test

Execute 20 concurrent team executions to verify:
- No duplicate messages
- No race conditions
- No execution lockups
- Correct message ordering

This stress test validates runtime stability under load.
"""

import os
import sys
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import datetime
from uuid import UUID, uuid4
from typing import List, Dict, Any
from collections import Counter, defaultdict
import time

from torq_console.dependencies import get_supabase_client
from torq_console.teams import (
    execute_team_node,
    TeamPersistence,
    TeamDefinitionRegistry,
    initialize_registry,
)


class ConcurrentStressTest:
    """Stress test agent teams under concurrent load."""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.persistence = TeamPersistence(self.supabase)
        self.results = []
        self.errors = []

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

    def get_test_objectives(self, count: int) -> List[Dict[str, Any]]:
        """Generate diverse test objectives for concurrent execution."""
        templates = [
            "Analyze {domain} architecture in TORQ Console",
            "Review {aspect} security mechanisms",
            "Evaluate {topic} performance characteristics",
            "Plan integration of {feature} into TORQ Console",
            "Design {process} strategy for the codebase",
            "Assess {component} scalability options",
            "Propose improvements to {system} design",
            "Identify potential {risk_type} in {area}",
            "Optimize {target} for better {metric}",
            "Document {subject} behavior and patterns",
        ]

        domains = ["authentication", "authorization", "database", "API", "frontend"]
        aspects = ["authentication", "data validation", "access control", "input sanitization"]
        topics = ["query execution", "request handling", "data processing", "caching"]
        features = ["new AI model", "vector database", "real-time updates", "audit logging"]
        processes = ["code review", "testing", "deployment", "monitoring"]
        components = ["database connections", "API endpoints", "message queue", "cache layer"]
        risk_types = ["bottlenecks", "security issues", "failure modes", "edge cases"]
        areas = ["mission execution", "agent orchestration", "decision engine", "persistence layer"]
        targets = ["agent execution", "database queries", "API responses", "mission planning"]
        metrics = ["throughput", "latency", "reliability", "scalability"]
        subjects = ["team collaboration", "role execution", "decision synthesis", "validator behavior"]
        systems = ["mission graph", "execution engine", "team orchestrator", "control surface"]

        objectives = []
        for i in range(count):
            template = templates[i % len(templates)]

            # Generate unique objective
            if "{domain}" in template:
                obj = template.format(domain=domains[i % len(domains)])
            elif "{aspect}" in template:
                obj = template.format(aspect=aspects[i % len(aspects)])
            elif "{topic}" in template:
                obj = template.format(topic=topics[i % len(topics)])
            elif "{feature}" in template:
                obj = template.format(feature=features[i % len(features)])
            elif "{process}" in template:
                obj = template.format(process=processes[i % len(processes)])
            elif "{component}" in template:
                obj = template.format(component=components[i % len(components)])
            elif "{risk_type}" in template:
                obj = template.format(risk_type=risk_types[i % len(risk_types)], area=areas[i % len(areas)])
            elif "{target}" in template:
                obj = template.format(target=targets[i % len(targets)], metric=metrics[i % len(metrics)])
            elif "{subject}" in template:
                obj = template.format(subject=subjects[i % len(subjects)])
            elif "{system}" in template:
                obj = template.format(system=systems[i % len(systems)])
            else:
                obj = f"Test objective {i+1}: {template}"

            objectives.append({
                "name": f"Concurrent Test {i+1}",
                "team": "research_team" if i % 2 == 0 else "planning_team",
                "objective": obj,
                "constraints": ["Test constraint 1", "Test constraint 2"],
            })

        return objectives

    async def execute_single(self, test_case: Dict[str, Any], mission_id: UUID, node_id: UUID, index: int) -> Dict[str, Any]:
        """Execute a single team execution."""
        start_time = time.time()

        try:
            result = await execute_team_node(
                supabase=self.supabase,
                mission_id=mission_id,
                node_id=node_id,
                team_id=test_case["team"],
                objective=test_case["objective"],
                constraints=test_case["constraints"],
            )

            duration = time.time() - start_time

            # Get execution details
            execution = await self.persistence.get_execution(result.team_execution_id)
            messages = await self.persistence.get_messages(result.team_execution_id)

            return {
                "index": index,
                "name": test_case["name"],
                "team": test_case["team"],
                "success": True,
                "duration_seconds": duration,
                "confidence": result.confidence_score,
                "validator_status": str(result.validator_status),
                "rounds": execution.current_round if execution else 0,
                "message_count": len(messages),
                "execution_id": str(result.team_execution_id),
                "error": None,
            }

        except Exception as e:
            duration = time.time() - start_time
            self.errors.append({
                "index": index,
                "name": test_case["name"],
                "error": str(e),
            })

            return {
                "index": index,
                "name": test_case["name"],
                "team": test_case["team"],
                "success": False,
                "duration_seconds": duration,
                "error": str(e),
            }

    async def execute_concurrent_batch(self, test_cases: List[Dict[str, Any]], mission_id: UUID, node_id: UUID):
        """Execute all test cases concurrently."""
        print(f"\nLaunching {len(test_cases)} concurrent executions...")

        start_time = time.time()

        # Create all tasks concurrently
        tasks = [
            self.execute_single(test_case, mission_id, node_id, i)
            for i, test_case in enumerate(test_cases)
        ]

        # Wait for all to complete
        self.results = await asyncio.gather(*tasks, return_exceptions=True)

        total_duration = time.time() - start_time

        # Handle any unexpected exceptions
        final_results = []
        for i, result in enumerate(self.results):
            if isinstance(result, Exception):
                self.errors.append({
                    "index": i,
                    "name": f"Test {i+1}",
                    "error": f"Unexpected exception: {result}",
                })
            elif isinstance(result, dict):
                final_results.append(result)

        self.results = final_results

        print(f"Completed {len(final_results)} executions in {total_duration:.2f}s")
        print(f"Average per execution: {total_duration / len(test_cases):.2f}s")

    async def verify_integrity(self):
        """Verify data integrity after concurrent execution."""
        print("\n" + "="*60)
        print("INTEGRITY VERIFICATION")
        print("="*60)

        execution_ids = [r["execution_id"] for r in self.results if r.get("success")]

        print(f"\nChecking {len(execution_ids)} execution records...")

        # Check for duplicate messages
        all_message_counts = []
        round_counts = defaultdict(int)
        message_type_counts = Counter()

        for exec_id in execution_ids:
            messages = await self.persistence.get_messages(UUID(exec_id))
            all_message_counts.append(len(messages))

            for msg in messages:
                round_counts[msg.round_number] += 1
                message_type_counts[msg.message_type.value] += 1

        # Check message counts
        print(f"\nMessage Count Analysis:")
        print(f"  Total messages: {sum(all_message_counts)}")
        print(f"  Mean per execution: {sum(all_message_counts) / len(all_message_counts):.1f}")
        print(f"  Min: {min(all_message_counts)}")
        print(f"  Max: {max(all_message_counts)}")

        # Check for duplicates (same execution_id, round_number, sender_role combination)
        print(f"\nDuplicate Check:")
        seen = set()
        duplicate_count = 0
        for exec_id in execution_ids:
            messages = await self.persistence.get_messages(UUID(exec_id))
            for msg in messages:
                key = (str(msg.team_execution_id), msg.round_number, msg.sender_role.value, msg.message_type.value)
                if key in seen:
                    duplicate_count += 1
                seen.add(key)

        if duplicate_count > 0:
            print(f"  [WARN] Found {duplicate_count} duplicate message combinations")
        else:
            print(f"  [OK] No duplicate messages detected")

        # Check round distribution
        print(f"\nRound Distribution:")
        for round_num in sorted(round_counts.keys()):
            print(f"  Round {round_num}: {round_counts[round_num]} messages")

        # Check message types
        print(f"\nMessage Type Distribution:")
        for msg_type, count in message_type_counts.most_common():
            print(f"  {msg_type}: {count}")

        # Check for message ordering issues
        print(f"\nMessage Ordering Check:")
        ordering_issues = 0
        for exec_id in execution_ids:
            messages = await self.persistence.get_messages(UUID(exec_id))
            # Messages should be ordered by round_number
            rounds = [m.round_number for m in messages]
            if rounds != sorted(rounds):
                ordering_issues += 1

        if ordering_issues > 0:
            print(f"  [WARN] {ordering_issues} executions have ordering issues")
        else:
            print(f"  [OK] All messages properly ordered")

        return duplicate_count == 0 and ordering_issues == 0

    async def run_stress_test(self, num_concurrent: int = 20):
        """Run concurrent execution stress test."""
        print("="*60)
        print(f"PHASE 5.2A CONCURRENT STRESS TEST")
        print(f"Executing {num_concurrent} concurrent team executions")
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

        # Generate test cases
        test_cases = self.get_test_objectives(num_concurrent)
        print(f"\nGenerated {len(test_cases)} unique test objectives")

        # Execute concurrently
        await self.execute_concurrent_batch(test_cases, mission_id, node_id)

        # Analyze results
        self._analyze_results()

        # Verify integrity
        integrity_ok = await self.verify_integrity()

        # Final assessment
        print("\n" + "="*60)
        print("STRESS TEST FINAL ASSESSMENT")
        print("="*60)

        checks = {
            "All Executions Successful": len(self.results) == num_concurrent,
            "No Errors": len(self.errors) == 0,
            "Data Integrity OK": integrity_ok,
        }

        for check, passed in checks.items():
            status = "[OK]" if passed else "[FAIL]"
            print(f"{status} {check}")

        all_passed = all(checks.values())

        print("\n" + "="*60)
        if all_passed:
            print("[SUCCESS] STRESS TEST PASSED")
            print("="*60)
            print("\nRuntime is rock solid under concurrent load.")
            print("Ready for production deployment of Phase 5.2B.")
        else:
            print("[FAILURE] STRESS TEST FAILED")
            print("="*60)
            print("\nIssues detected that need resolution.")

    def _analyze_results(self):
        """Analyze stress test results."""
        print("\n" + "="*60)
        print("STRESS TEST RESULTS")
        print("="*60)

        successful = [r for r in self.results if r.get("success")]
        failed = [r for r in self.results if not r.get("success")]

        print(f"\nExecution Summary:")
        print(f"  Total: {len(self.results)}")
        print(f"  Successful: {len(successful)}")
        print(f"  Failed: {len(failed)}")
        print(f"  Errors: {len(self.errors)}")

        if successful:
            # Duration analysis
            durations = [r["duration_seconds"] for r in successful]
            print(f"\nDuration Analysis:")
            print(f"  Mean: {sum(durations) / len(durations):.2f}s")
            print(f"  Min: {min(durations):.2f}s")
            print(f"  Max: {max(durations):.2f}s")

            # Team distribution
            team_counts = Counter(r["team"] for r in successful)
            print(f"\nTeam Distribution:")
            for team, count in team_counts.items():
                print(f"  {team}: {count}")


async def main():
    """Run concurrent stress test."""
    stress_test = ConcurrentStressTest()

    # Default to 20 concurrent executions
    num_concurrent = 20
    if len(sys.argv) > 1:
        try:
            num_concurrent = int(sys.argv[1])
        except ValueError:
            pass

    await stress_test.run_stress_test(num_concurrent)


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(0 if exit_code is None else 1)
