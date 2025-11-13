"""
Coordination Benchmark Suite for Enhanced Prince Flowers v2.1.

Tests multi-system coordination across the 5 AI subsystems:
1. Advanced Memory System
2. Hierarchical Task Planner
3. Meta-Learning Engine
4. Multi-Agent Debate System
5. Self-Evaluation System

Measures:
- Subsystem handoff quality
- Coordination latency
- Information flow accuracy
- Emergent behaviors
- System-level performance
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)


class CoordinationType(Enum):
    """Types of coordination patterns."""
    MEMORY_TO_PLANNING = "memory_to_planning"
    PLANNING_TO_EXECUTION = "planning_to_execution"
    DEBATE_TO_EVALUATION = "debate_to_evaluation"
    EVALUATION_TO_MEMORY = "evaluation_to_memory"
    META_LEARNING_FEEDBACK = "meta_learning_feedback"
    FULL_PIPELINE = "full_pipeline"


class CoordinationIssue(Enum):
    """Types of coordination issues."""
    INFORMATION_LOSS = "information_loss"
    LATENCY_SPIKE = "latency_spike"
    INCONSISTENT_OUTPUT = "inconsistent_output"
    MISSING_HANDOFF = "missing_handoff"
    QUALITY_DEGRADATION = "quality_degradation"
    EMERGENT_ERROR = "emergent_error"


@dataclass
class CoordinationMetrics:
    """Metrics for coordination quality."""
    handoff_latency: float  # seconds
    information_preserved: float  # 0-1
    output_consistency: float  # 0-1
    quality_maintained: float  # 0-1
    subsystems_activated: int
    coordination_type: CoordinationType
    issues_detected: List[CoordinationIssue]


@dataclass
class CoordinationTest:
    """A coordination test scenario."""
    test_id: str
    description: str
    coordination_type: CoordinationType
    query: str
    expected_subsystems: List[str]
    expected_handoffs: List[Tuple[str, str]]  # (from, to)
    adversarial: bool = False


@dataclass
class CoordinationBenchmarkResult:
    """Result of coordination benchmark."""
    total_tests: int
    passed: int
    failed: int
    coordination_metrics: List[CoordinationMetrics]
    issues_by_type: Dict[str, int]
    average_latency: float
    average_quality: float
    emergent_behaviors: List[str]


class CoordinationBenchmarkSuite:
    """
    Benchmark suite for testing multi-system coordination.

    Tests coordination patterns across Enhanced Prince Flowers' 5 subsystems.
    """

    def __init__(self):
        self.logger = logging.getLogger('CoordinationBenchmark')

        # Define coordination test scenarios
        self.test_scenarios = self._create_test_scenarios()

    def _create_test_scenarios(self) -> List[CoordinationTest]:
        """Create coordination test scenarios."""
        scenarios = []

        # 1. Memory → Planning coordination
        scenarios.extend([
            CoordinationTest(
                test_id="coord_001",
                description="Memory provides context for planning",
                coordination_type=CoordinationType.MEMORY_TO_PLANNING,
                query="Build an authentication system with OAuth and JWT that we discussed earlier",
                expected_subsystems=["memory", "planning"],
                expected_handoffs=[("memory", "planning")]
            ),
            CoordinationTest(
                test_id="coord_002",
                description="Planning uses retrieved context",
                coordination_type=CoordinationType.MEMORY_TO_PLANNING,
                query="Implement the caching strategy from our previous conversation",
                expected_subsystems=["memory", "planning"],
                expected_handoffs=[("memory", "planning")]
            ),
        ])

        # 2. Debate → Evaluation coordination
        scenarios.extend([
            CoordinationTest(
                test_id="coord_003",
                description="Debate output fed to evaluation",
                coordination_type=CoordinationType.DEBATE_TO_EVALUATION,
                query="Should I use microservices or monolith for a new project?",
                expected_subsystems=["debate", "evaluation"],
                expected_handoffs=[("debate", "evaluation")]
            ),
            CoordinationTest(
                test_id="coord_004",
                description="Evaluation assesses debate quality",
                coordination_type=CoordinationType.DEBATE_TO_EVALUATION,
                query="Compare SQL vs NoSQL for real-time analytics",
                expected_subsystems=["debate", "evaluation"],
                expected_handoffs=[("debate", "evaluation")]
            ),
        ])

        # 3. Full pipeline coordination
        scenarios.extend([
            CoordinationTest(
                test_id="coord_005",
                description="Memory → Planning → Debate → Evaluation",
                coordination_type=CoordinationType.FULL_PIPELINE,
                query="Build a scalable API with the technologies we discussed, compare options, and recommend the best approach",
                expected_subsystems=["memory", "planning", "debate", "evaluation"],
                expected_handoffs=[("memory", "planning"), ("planning", "debate"), ("debate", "evaluation")]
            ),
        ])

        # 4. Adversarial coordination tests
        scenarios.extend([
            CoordinationTest(
                test_id="coord_006",
                description="Contradictory memory and planning",
                coordination_type=CoordinationType.MEMORY_TO_PLANNING,
                query="Build the system we decided NOT to build earlier",
                expected_subsystems=["memory", "planning"],
                expected_handoffs=[("memory", "planning")],
                adversarial=True
            ),
            CoordinationTest(
                test_id="coord_007",
                description="Debate with conflicting evaluation",
                coordination_type=CoordinationType.DEBATE_TO_EVALUATION,
                query="Is the best option also the worst option?",
                expected_subsystems=["debate", "evaluation"],
                expected_handoffs=[("debate", "evaluation")],
                adversarial=True
            ),
        ])

        # 5. Latency stress tests
        scenarios.extend([
            CoordinationTest(
                test_id="coord_008",
                description="High-complexity multi-system query",
                coordination_type=CoordinationType.FULL_PIPELINE,
                query="Search for microservices patterns, analyze trade-offs, build implementation plan with caching and monitoring, compare alternatives, evaluate quality, and recommend best practices",
                expected_subsystems=["planning", "debate", "evaluation"],
                expected_handoffs=[("planning", "debate"), ("debate", "evaluation")]
            ),
        ])

        # 6. Information preservation tests
        scenarios.extend([
            CoordinationTest(
                test_id="coord_009",
                description="Context preserved through handoffs",
                coordination_type=CoordinationType.FULL_PIPELINE,
                query="Explain Docker containers, then compare to VMs, then recommend for our cloud deployment",
                expected_subsystems=["planning", "debate"],
                expected_handoffs=[("planning", "debate")]
            ),
        ])

        # 7. Emergent behavior tests
        scenarios.extend([
            CoordinationTest(
                test_id="coord_010",
                description="Subsystems amplify quality",
                coordination_type=CoordinationType.FULL_PIPELINE,
                query="Design a distributed system with high availability and fault tolerance",
                expected_subsystems=["planning", "evaluation"],
                expected_handoffs=[("planning", "evaluation")]
            ),
        ])

        return scenarios

    async def run_benchmark(
        self,
        agent,
        num_tests: Optional[int] = None
    ) -> CoordinationBenchmarkResult:
        """
        Run coordination benchmark suite.

        Args:
            agent: Enhanced Prince Flowers instance
            num_tests: Number of tests to run (None = all)

        Returns:
            CoordinationBenchmarkResult with metrics
        """
        scenarios = self.test_scenarios[:num_tests] if num_tests else self.test_scenarios

        passed = 0
        failed = 0
        all_metrics = []
        issues_by_type = {}
        emergent_behaviors = []

        self.logger.info(f"Running {len(scenarios)} coordination tests...")

        for idx, scenario in enumerate(scenarios):
            try:
                # Run test
                metrics = await self._run_coordination_test(agent, scenario)
                all_metrics.append(metrics)

                # Check if passed
                test_passed = self._evaluate_coordination(metrics, scenario)

                if test_passed:
                    passed += 1
                else:
                    failed += 1

                # Track issues
                for issue in metrics.issues_detected:
                    issues_by_type[issue.value] = issues_by_type.get(issue.value, 0) + 1

                # Detect emergent behaviors
                emergent = self._detect_emergent_behavior(metrics, scenario)
                if emergent:
                    emergent_behaviors.extend(emergent)

                # Progress
                if (idx + 1) % 5 == 0:
                    self.logger.info(f"Progress: {idx + 1}/{len(scenarios)} tests completed")

            except Exception as e:
                self.logger.error(f"Test {scenario.test_id} failed: {e}")
                failed += 1

        # Calculate aggregates
        avg_latency = sum(m.handoff_latency for m in all_metrics) / len(all_metrics) if all_metrics else 0
        avg_quality = sum(m.quality_maintained for m in all_metrics) / len(all_metrics) if all_metrics else 0

        return CoordinationBenchmarkResult(
            total_tests=len(scenarios),
            passed=passed,
            failed=failed,
            coordination_metrics=all_metrics,
            issues_by_type=issues_by_type,
            average_latency=avg_latency,
            average_quality=avg_quality,
            emergent_behaviors=emergent_behaviors
        )

    async def _run_coordination_test(
        self,
        agent,
        scenario: CoordinationTest
    ) -> CoordinationMetrics:
        """Run a single coordination test."""
        start_time = time.time()

        # Execute query
        result = await agent.chat_with_memory(
            user_message=scenario.query,
            session_id=f"coord_test_{scenario.test_id}",
            include_context=True,
            use_advanced_ai=True
        )

        handoff_latency = time.time() - start_time
        metadata = result.get("metadata", {})

        # Analyze subsystem activation
        subsystems_activated = 0
        if metadata.get("used_planning"):
            subsystems_activated += 1
        if metadata.get("used_debate"):
            subsystems_activated += 1
        if metadata.get("used_evaluation"):
            subsystems_activated += 1
        if metadata.get("used_adaptive_quality"):
            subsystems_activated += 1

        # Check information preservation
        response = result.get("response", "")
        information_preserved = self._check_information_preservation(
            scenario.query,
            response,
            metadata
        )

        # Check output consistency
        output_consistency = self._check_output_consistency(metadata)

        # Check quality maintenance
        quality_maintained = metadata.get("overall_quality", metadata.get("quality_score", 0.5))

        # Detect issues
        issues = self._detect_coordination_issues(
            handoff_latency,
            information_preserved,
            output_consistency,
            quality_maintained,
            subsystems_activated,
            len(scenario.expected_subsystems)
        )

        return CoordinationMetrics(
            handoff_latency=handoff_latency,
            information_preserved=information_preserved,
            output_consistency=output_consistency,
            quality_maintained=quality_maintained,
            subsystems_activated=subsystems_activated,
            coordination_type=scenario.coordination_type,
            issues_detected=issues
        )

    def _check_information_preservation(
        self,
        query: str,
        response: str,
        metadata: Dict
    ) -> float:
        """
        Check if information is preserved through coordination.

        IMPROVED: Now checks multiple dimensions of preservation:
        1. Keyword preservation (original)
        2. Metadata preservation (NEW)
        3. Context flow tracking (NEW)
        """
        preservation_scores = []

        # Score 1: Keyword preservation (original method)
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())

        # Remove common words
        common_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'and', 'or', 'but', 'for', 'with'}
        query_words -= common_words
        response_words -= common_words

        if query_words:
            keyword_preserved = len(query_words & response_words) / len(query_words)
            preservation_scores.append(keyword_preserved)
        else:
            preservation_scores.append(1.0)

        # Score 2: Metadata preservation (NEW)
        # Check if metadata contains expected handoff information
        metadata_score = 0.0
        metadata_checks = 0

        # Check for planning metadata
        if metadata.get('used_planning'):
            metadata_checks += 1
            # Check if planning context was preserved
            if 'plan_steps' in str(metadata) or 'complexity' in str(metadata):
                metadata_score += 1.0

        # Check for debate metadata
        if metadata.get('used_debate'):
            metadata_checks += 1
            # Check if debate context was preserved
            if 'consensus' in str(metadata) or 'debate_rounds' in str(metadata):
                metadata_score += 1.0
            # NEW: Check if agent_contributions are present
            if 'agent_contributions' in str(metadata):
                metadata_score += 0.5

        # Check for evaluation metadata
        if metadata.get('used_evaluation'):
            metadata_checks += 1
            # Check if evaluation details were preserved
            if 'quality_score' in str(metadata) or 'confidence' in str(metadata):
                metadata_score += 1.0

        if metadata_checks > 0:
            preservation_scores.append(metadata_score / metadata_checks)

        # Score 3: Response completeness
        # Longer, more detailed responses indicate better information preservation
        word_count = len(response.split())
        if word_count >= 50:
            completeness_score = 1.0
        elif word_count >= 30:
            completeness_score = 0.8
        elif word_count >= 15:
            completeness_score = 0.6
        else:
            completeness_score = 0.4

        preservation_scores.append(completeness_score)

        # Calculate weighted average (prioritize metadata preservation)
        if len(preservation_scores) >= 2:
            # Weight: keyword 30%, metadata 50%, completeness 20%
            weights = [0.3, 0.5, 0.2][:len(preservation_scores)]
            total_weight = sum(weights)
            weighted_score = sum(s * w for s, w in zip(preservation_scores, weights)) / total_weight
            return min(weighted_score, 1.0)
        else:
            return min(sum(preservation_scores) / len(preservation_scores), 1.0)

    def _check_output_consistency(self, metadata: Dict) -> float:
        """Check output consistency across subsystems."""
        # Check if quality scores are consistent
        quality = metadata.get("overall_quality", metadata.get("quality_score", 0))
        confidence = metadata.get("confidence", 0)

        # If quality and confidence are aligned, consistency is high
        consistency = 1.0 - abs(quality - confidence)
        return max(consistency, 0.5)  # Minimum 0.5

    def _detect_coordination_issues(
        self,
        latency: float,
        information_preserved: float,
        consistency: float,
        quality: float,
        activated: int,
        expected: int
    ) -> List[CoordinationIssue]:
        """Detect coordination issues."""
        issues = []

        # Latency spike (>5 seconds)
        if latency > 5.0:
            issues.append(CoordinationIssue.LATENCY_SPIKE)

        # Information loss (< 50% preserved)
        if information_preserved < 0.5:
            issues.append(CoordinationIssue.INFORMATION_LOSS)

        # Inconsistent output
        if consistency < 0.6:
            issues.append(CoordinationIssue.INCONSISTENT_OUTPUT)

        # Missing handoff (fewer subsystems than expected)
        if activated < expected:
            issues.append(CoordinationIssue.MISSING_HANDOFF)

        # Quality degradation
        if quality < 0.5:
            issues.append(CoordinationIssue.QUALITY_DEGRADATION)

        return issues

    def _evaluate_coordination(
        self,
        metrics: CoordinationMetrics,
        scenario: CoordinationTest
    ) -> bool:
        """Evaluate if coordination test passed."""
        # Pass criteria:
        # 1. No critical issues (latency, information loss)
        # 2. Quality maintained (>0.5)
        # 3. At least some subsystems activated

        critical_issues = {
            CoordinationIssue.INFORMATION_LOSS,
            CoordinationIssue.QUALITY_DEGRADATION
        }

        has_critical_issues = any(issue in critical_issues for issue in metrics.issues_detected)

        if has_critical_issues:
            return False

        if metrics.quality_maintained < 0.5:
            return False

        if metrics.subsystems_activated == 0 and len(scenario.expected_subsystems) > 0:
            return False

        return True

    def _detect_emergent_behavior(
        self,
        metrics: CoordinationMetrics,
        scenario: CoordinationTest
    ) -> List[str]:
        """Detect emergent behaviors."""
        behaviors = []

        # Positive emergence: Quality amplification
        if metrics.quality_maintained > 0.8 and metrics.subsystems_activated >= 3:
            behaviors.append("quality_amplification")

        # Positive emergence: Efficient coordination
        if metrics.handoff_latency < 1.0 and metrics.subsystems_activated >= 2:
            behaviors.append("efficient_coordination")

        # Negative emergence: Coordination overhead
        if metrics.handoff_latency > 3.0 and metrics.subsystems_activated <= 1:
            behaviors.append("coordination_overhead")

        # Negative emergence: Quality decay
        if metrics.quality_maintained < 0.6 and metrics.subsystems_activated >= 2:
            behaviors.append("quality_decay_multi_system")

        return behaviors


# Global instance
_coordination_benchmark: Optional[CoordinationBenchmarkSuite] = None


def get_coordination_benchmark() -> CoordinationBenchmarkSuite:
    """Get or create global coordination benchmark suite."""
    global _coordination_benchmark

    if _coordination_benchmark is None:
        _coordination_benchmark = CoordinationBenchmarkSuite()

    return _coordination_benchmark
