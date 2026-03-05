#!/usr/bin/env python3
"""
Comprehensive Test Suite for TORQ Agent Cognitive Loop System

This script tests the complete cognitive loop with real queries, measuring:
1. Loop execution times (target < 2s)
2. Phase-by-phase results
3. Success/error rates
4. Confidence scores
5. Learning events stored
6. Telemetry spans emitted
7. Failure handling (tool retry, fallback)
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add TORQ-CONSOLE to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cognitive_loop_test_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class CognitiveLoopTestResults:
    """Container for test results."""

    def __init__(self):
        self.test_queries = []
        self.phase_metrics = {
            "reason": [],
            "retrieve": [],
            "plan": [],
            "act": [],
            "evaluate": [],
            "learn": []
        }
        self.loop_latencies = []
        self.success_count = 0
        self.failure_count = 0
        self.retry_count = 0
        self.confidence_scores = []
        self.learning_events = []
        self.telemetry_spans = []
        self.error_details = []

    def add_query_result(self, query: str, result: Any, latency: float):
        """Add a query result to the test results."""
        self.test_queries.append({
            "query": query,
            "success": result.success if hasattr(result, 'success') else False,
            "status": str(result.status) if hasattr(result, 'status') else "unknown",
            "latency": latency,
            "confidence": result.confidence if hasattr(result, 'confidence') else 0.0,
            "retry_count": result.retry_count if hasattr(result, 'retry_count') else 0,
            "error": result.error if hasattr(result, 'error') else None
        })

        # Track metrics
        self.loop_latencies.append(latency)
        if hasattr(result, 'success'):
            if result.success:
                self.success_count += 1
            else:
                self.failure_count += 1

        if hasattr(result, 'confidence'):
            self.confidence_scores.append(result.confidence)

        if hasattr(result, 'retry_count'):
            self.retry_count += result.retry_count

        # Track phase times
        if hasattr(result, 'phase_times_seconds'):
            for phase, phase_time in result.phase_times_seconds.items():
                if phase in self.phase_metrics:
                    self.phase_metrics[phase].append(phase_time)

        # Track learning events
        if hasattr(result, 'learning_event') and result.learning_event:
            self.learning_events.append(result.learning_event)

        # Track errors
        if hasattr(result, 'error') and result.error:
            self.error_details.append({
                "query": query,
                "error": result.error,
                "latency": latency
            })

    def get_summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        total_tests = len(self.test_queries)
        success_rate = (self.success_count / total_tests * 100) if total_tests > 0 else 0

        avg_latency = sum(self.loop_latencies) / len(self.loop_latencies) if self.loop_latencies else 0
        max_latency = max(self.loop_latencies) if self.loop_latencies else 0
        min_latency = min(self.loop_latencies) if self.loop_latencies else 0

        avg_confidence = sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 0

        phase_summary = {}
        for phase, times in self.phase_metrics.items():
            if times:
                phase_summary[phase] = {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "count": len(times)
                }

        return {
            "total_tests": total_tests,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": success_rate,
            "total_retries": self.retry_count,
            "avg_confidence": avg_confidence,
            "latency": {
                "avg": avg_latency,
                "min": min_latency,
                "max": max_latency,
                "target_met": avg_latency < 2.0
            },
            "phase_times": phase_summary,
            "learning_events_stored": len(self.learning_events),
            "errors": self.error_details
        }


class CognitiveLoopTester:
    """Comprehensive tester for the TORQ Cognitive Loop."""

    def __init__(self):
        self.results = CognitiveLoopTestResults()
        self.loop = None
        self.telemetry = None
        self.temp_dir = Path(".torq/test_cognitive_learning")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Initialize the cognitive loop with all modules."""
        logger.info("=== Initializing TORQ Cognitive Loop ===")

        try:
            from torq_console.agents.cognitive_loop.cognitive_loop import CognitiveLoop
            from torq_console.agents.cognitive_loop.config import get_cognitive_config

            # Create test configuration
            config = get_cognitive_config(overrides={
                "max_loop_latency_seconds": 2.0,
                "max_retries": 2,
                "knowledge_enabled": False,  # Disable for faster tests
                "telemetry_enabled": True,
                "emit_detailed_spans": True,
                "learning_enabled": True,
                "learning_storage_path": str(self.temp_dir)
            })

            self.loop = CognitiveLoop(
                agent_id="test_cognitive_agent",
                config=config
            )

            # Initialize telemetry if available
            try:
                from torq_console.agents.telemetry import get_cognitive_telemetry
                self.telemetry = get_cognitive_telemetry(service_name="torq-cognitive-test")
                logger.info("Telemetry initialized successfully")
            except Exception as e:
                logger.warning(f"Telemetry not available: {e}")

            logger.info("Cognitive Loop initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize cognitive loop: {e}", exc_info=True)
            return False

    async def test_full_cycle(self, query: str, test_name: str) -> Dict[str, Any]:
        """Test the full cognitive cycle: Reason -> Retrieve -> Plan -> Act -> Evaluate -> Learn."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Test: {test_name}")
        logger.info(f"Query: {query}")
        logger.info(f"{'='*60}")

        test_result = {
            "test_name": test_name,
            "query": query,
            "start_time": time.time(),
            "phases": {},
            "success": False,
            "error": None
        }

        try:
            # Create session context
            session = self.loop.create_session(
                user_id="test_user",
                test_name=test_name
            )

            # Run the cognitive loop
            start_time = time.time()
            result = await self.loop.run(query, session_context=session)
            latency = time.time() - start_time

            # Store results
            self.results.add_query_result(query, result, latency)

            # Analyze each phase
            test_result["latency"] = latency
            test_result["success"] = result.success if hasattr(result, 'success') else False
            test_result["status"] = str(result.status) if hasattr(result, 'status') else "unknown"

            # Phase analysis
            if hasattr(result, 'reasoning_plan') and result.reasoning_plan:
                test_result["phases"]["reason"] = {
                    "intent": result.reasoning_plan.intent.value,
                    "confidence": result.reasoning_plan.intent_confidence,
                    "complexity": result.reasoning_plan.complexity_estimate,
                    "tools_suggested": result.reasoning_plan.suggested_tools
                }

            if hasattr(result, 'knowledge_contexts'):
                test_result["phases"]["retrieve"] = {
                    "contexts_count": len(result.knowledge_contexts),
                    "sources": [c.source for c in result.knowledge_contexts]
                }

            if hasattr(result, 'execution_plan') and result.execution_plan:
                test_result["phases"]["plan"] = {
                    "steps": len(result.execution_plan.steps),
                    "tools": result.execution_plan.required_tools,
                    "estimated_duration": result.execution_plan.estimated_duration_seconds,
                    "parallel": result.execution_plan.requires_parallel_execution
                }

            if hasattr(result, 'execution_result') and result.execution_result:
                test_result["phases"]["act"] = {
                    "tools_executed": len(result.execution_result.tool_results),
                    "success": result.execution_result.success,
                    "execution_time": result.execution_result.total_execution_time_seconds,
                    "partial_results": result.execution_result.partial_results
                }

            if hasattr(result, 'evaluation_result') and result.evaluation_result:
                test_result["phases"]["evaluate"] = {
                    "confidence": result.evaluation_result.confidence_score,
                    "task_completed": result.evaluation_result.task_completed,
                    "data_integrity": result.evaluation_result.data_integrity_score,
                    "quality": result.evaluation_result.quality_score,
                    "should_retry": result.evaluation_result.should_retry
                }

            if hasattr(result, 'learning_event') and result.learning_event:
                test_result["phases"]["learn"] = {
                    "stored": True,
                    "success": result.learning_event.success,
                    "score": result.learning_event.success_score,
                    "insights": len(result.learning_event.learned_insights)
                }

            # Log detailed results
            logger.info(f"Result: {test_result['status']}")
            logger.info(f"Latency: {latency:.3f}s (target: <2s)")
            logger.info(f"Success: {test_result['success']}")

            if hasattr(result, 'confidence'):
                logger.info(f"Confidence: {result.confidence:.2f}")

            if hasattr(result, 'retry_count') and result.retry_count > 0:
                logger.info(f"Retries: {result.retry_count}")

        except Exception as e:
            logger.error(f"Test failed with exception: {e}", exc_info=True)
            test_result["error"] = str(e)
            test_result["latency"] = time.time() - test_result["start_time"]
            self.results.error_details.append({
                "query": query,
                "error": str(e),
                "latency": test_result["latency"]
            })

        return test_result

    async def test_failure_handling(self):
        """Test failure handling with tool retry and fallback."""
        logger.info(f"\n{'='*60}")
        logger.info("Test: Failure Handling (Tool Retry & Fallback)")
        logger.info(f"{'='*60}")

        # Test with a query that should trigger retries
        # We'll simulate this by using a malformed query
        test_queries = [
            "Execute non_existent_tool with invalid parameters",
            "Search for something that will timeout immediately",
            ""
        ]

        for query in test_queries:
            try:
                session = self.loop.create_session(user_id="test_user_failure")
                start_time = time.time()
                result = await self.loop.run(query, session_context=session)
                latency = time.time() - start_time

                logger.info(f"Failure test query: {query[:50]}...")
                logger.info(f"Handled gracefully: {result.status}")
                logger.info(f"Latency: {latency:.3f}s")

                self.results.add_query_result(query, result, latency)

            except Exception as e:
                logger.info(f"Exception caught (expected): {str(e)[:100]}")

    async def test_concurrent_execution(self):
        """Test multiple concurrent cognitive loop executions."""
        logger.info(f"\n{'='*60}")
        logger.info("Test: Concurrent Execution")
        logger.info(f"{'='*60}")

        queries = [
            "What is Python?",
            "What is JavaScript?",
            "What is Go?",
            "Explain async/await",
            "What is a database?"
        ]

        start_time = time.time()
        results = await asyncio.gather(*[
            self.loop.run(q, session_context=self.loop.create_session())
            for q in queries
        ])
        total_latency = time.time() - start_time

        logger.info(f"Executed {len(queries)} queries concurrently")
        logger.info(f"Total time: {total_latency:.3f}s")
        logger.info(f"Average per query: {total_latency/len(queries):.3f}s")

        for i, result in enumerate(results):
            self.results.add_query_result(queries[i], result, total_latency/len(queries))

    async def verify_telemetry_spans(self):
        """Verify that telemetry spans are being emitted."""
        logger.info(f"\n{'='*60}")
        logger.info("Test: Telemetry Span Verification")
        logger.info(f"{'='*60}")

        if not self.telemetry:
            logger.warning("Telemetry not available, skipping span verification")
            return

        # Get metrics from telemetry
        try:
            metrics = self.telemetry.get_aggregated_metrics()
            logger.info(f"Telemetry Metrics:")
            logger.info(f"  Total loops: {metrics.get('total_loops', 0)}")
            logger.info(f"  Avg latency: {metrics.get('avg_latency_ms', 0):.2f}ms")
            logger.info(f"  Avg confidence: {metrics.get('avg_confidence', 0):.3f}")
            logger.info(f"  Success rate: {metrics.get('success_rate', 0):.3f}")
            logger.info(f"  Most used tools: {metrics.get('most_used_tools', {})}")

            # Check for recent loops
            recent = self.telemetry.get_loop_metrics(limit=10)
            logger.info(f"  Recent loops tracked: {len(recent)}")

            self.results.telemetry_spans = recent

        except Exception as e:
            logger.error(f"Failed to verify telemetry: {e}")

    async def verify_learning_events(self):
        """Verify that learning events are being stored."""
        logger.info(f"\n{'='*60}")
        logger.info("Test: Learning Event Storage")
        logger.info(f"{'='*60}")

        try:
            stats = await self.loop.get_learning_statistics()
            logger.info(f"Learning Statistics:")
            logger.info(f"  Total events: {stats.get('total_events', 0)}")
            logger.info(f"  Successful events: {stats.get('successful_events', 0)}")
            logger.info(f"  Failed events: {stats.get('failed_events', 0)}")
            logger.info(f"  Success rate: {stats.get('success_rate', 0):.3f}")
            logger.info(f"  Avg confidence: {stats.get('avg_confidence', 0):.3f}")
            logger.info(f"  Storage path: {stats.get('storage_path', '')}")

        except Exception as e:
            logger.error(f"Failed to verify learning events: {e}")

    async def run_test_suite(self):
        """Run the complete test suite."""
        logger.info("\n" + "="*80)
        logger.info("TORQ AGENT COGNITIVE LOOP - COMPREHENSIVE TEST SUITE")
        logger.info("="*80)
        logger.info(f"Test started at: {datetime.now().isoformat()}")

        # Initialize
        if not await self.initialize():
            logger.error("Failed to initialize cognitive loop. Aborting tests.")
            return

        # Test queries from the test plan
        test_queries = [
            ("Analyze the current TORQ architecture", "Architecture Analysis"),
            ("Search for financial insights about AI companies", "Financial Research"),
            ("Generate a summary of recent learning events", "Learning Summary"),
            ("What is async programming in Python?", "Technical Query"),
            ("Create a function to calculate fibonacci numbers", "Code Generation"),
            ("Compare and contrast REST vs GraphQL APIs", "Comparative Analysis"),
            ("Research the latest trends in AI", "Research Task"),
        ]

        # Run each test query
        for query, test_name in test_queries:
            await self.test_full_cycle(query, test_name)
            await asyncio.sleep(0.1)  # Small delay between tests

        # Test failure handling
        await self.test_failure_handling()

        # Test concurrent execution
        await self.test_concurrent_execution()

        # Verify telemetry
        await self.verify_telemetry_spans()

        # Verify learning events
        await self.verify_learning_events()

        # Generate final report
        await self.generate_report()

        # Cleanup
        await self.loop.shutdown()

    async def generate_report(self):
        """Generate comprehensive test report."""
        logger.info("\n" + "="*80)
        logger.info("FINAL TEST REPORT")
        logger.info("="*80)

        summary = self.results.get_summary()

        # Overall statistics
        logger.info(f"\nOVERALL STATISTICS:")
        logger.info(f"  Total Tests: {summary['total_tests']}")
        logger.info(f"  Successful: {summary['success_count']}")
        logger.info(f"  Failed: {summary['failure_count']}")
        logger.info(f"  Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"  Total Retries: {summary['total_retries']}")

        # Latency metrics
        logger.info(f"\nLATENCY METRICS:")
        logger.info(f"  Average: {summary['latency']['avg']:.3f}s")
        logger.info(f"  Min: {summary['latency']['min']:.3f}s")
        logger.info(f"  Max: {summary['latency']['max']:.3f}s")
        logger.info(f"  Target (<2s): {'✓ MET' if summary['latency']['target_met'] else '✗ NOT MET'}")

        # Confidence scores
        logger.info(f"\nCONFIDENCE SCORES:")
        logger.info(f"  Average: {summary['avg_confidence']:.3f}")
        logger.info(f"  Min Threshold: 0.70")
        logger.info(f"  Above Threshold: {'✓ YES' if summary['avg_confidence'] >= 0.70 else '✗ NO'}")

        # Phase-by-phase breakdown
        logger.info(f"\nPHASE-BY-PHASE BREAKDOWN:")
        for phase, metrics in summary['phase_times'].items():
            logger.info(f"  {phase.upper():10} - Avg: {metrics['avg']:.3f}s, "
                       f"Min: {metrics['min']:.3f}s, Max: {metrics['max']:.3f}s, "
                       f"Count: {metrics['count']}")

        # Learning events
        logger.info(f"\nLEARNING EVENTS:")
        logger.info(f"  Events Stored: {summary['learning_events_stored']}")

        # Errors
        if summary['errors']:
            logger.info(f"\nERRORS ({len(summary['errors'])}):")
            for error in summary['errors'][:5]:  # Show first 5 errors
                logger.info(f"  Query: {error['query'][:50]}...")
                logger.info(f"  Error: {error['error'][:80]}...")

        # Save report to JSON
        report_path = Path("cognitive_loop_test_report.json")
        with open(report_path, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "test_queries": self.results.test_queries,
                "learning_events": [
                    event.to_dict() if hasattr(event, 'to_dict') else str(event)
                    for event in self.results.learning_events[:10]
                ]
            }, f, indent=2)

        logger.info(f"\nDetailed report saved to: {report_path.absolute()}")
        logger.info(f"Log file saved to: cognitive_loop_test_results.log")

        logger.info("\n" + "="*80)
        logger.info("TEST SUITE COMPLETE")
        logger.info("="*80)


async def main():
    """Main entry point."""
    tester = CognitiveLoopTester()
    await tester.run_test_suite()


if __name__ == "__main__":
    asyncio.run(main())
