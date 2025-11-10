"""
Maxim AI Integration - Phase 2: A/B Testing Framework
Advanced A/B testing system for Prince Flowers routing strategies

This module implements comprehensive A/B testing capabilities:
- Traffic splitting algorithms
- Statistical significance testing
- Real-time experiment monitoring
- Variant performance comparison
"""

import asyncio
import json
import time
import logging
import random
import hashlib
import math
import uuid
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime, timedelta
import statistics
import os

from experiment_manager import ExperimentManager, ExperimentConfig, ExperimentResult, ExperimentStatus

class TrafficSplitType(Enum):
    """Types of traffic splitting algorithms"""
    EQUAL_SPLIT = "equal_split"
    WEIGHTED_SPLIT = "weighted_split"
    STICKY_SPLIT = "sticky_split"
    GRADUAL_ROLLOUT = "gradual_rollout"
    BANDIT_ALGORITHM = "bandit_algorithm"

class StatisticalTest(Enum):
    """Statistical tests for significance"""
    T_TEST = "t_test"
    CHI_SQUARE = "chi_square"
    Z_TEST = "z_test"
    WILCOXON = "wilcoxon"
    BAYESIAN = "bayesian"

@dataclass
class TrafficSplit:
    """Traffic split configuration"""
    variant_name: str
    weight: float  # 0.0 to 1.0
    allocation_percentage: float  # 0 to 100
    sticky_key: Optional[str] = None  # For sticky splitting

@dataclass
class ABTestConfig:
    """A/B test configuration"""
    test_id: str
    name: str
    description: str
    control_variant: str
    treatment_variants: List[str]
    traffic_split_type: TrafficSplitType
    traffic_splits: List[TrafficSplit]
    primary_metric: str
    secondary_metrics: List[str]
    success_criteria: Dict[str, float]
    sample_size_required: int
    confidence_level: float
    test_duration_hours: int
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class VariantPerformance:
    """Performance data for a single variant"""
    variant_name: str
    total_requests: int
    successful_requests: int
    metrics: Dict[str, float]
    response_times: List[float]
    confidence_scores: List[float]
    error_rates: Dict[str, int]
    last_updated: datetime

@dataclass
class StatisticalResult:
    """Statistical test result"""
    test_name: str
    metric: str
    control_value: float
    treatment_value: float
    improvement: float
    confidence_interval: Tuple[float, float]
    p_value: float
    is_significant: bool
    statistical_power: float

@dataclass
class ABTestResult:
    """Complete A/B test result"""
    test_id: str
    status: ExperimentStatus
    variant_performances: Dict[str, VariantPerformance]
    statistical_results: List[StatisticalResult]
    winning_variant: Optional[str]
    confidence_level: float
    test_duration: timedelta
    recommendations: List[str]
    next_steps: List[str]
    completed_at: datetime

class ABTestingFramework:
    """
    Advanced A/B testing framework for Prince Flowers routing strategies
    """

    def __init__(self, experiment_manager: ExperimentManager):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

        self.experiment_manager = experiment_manager
        self.active_tests: Dict[str, ABTestConfig] = {}
        self.test_results: Dict[str, ABTestResult] = {}
        self.user_assignments: Dict[str, str] = {}  # For sticky splitting
        self.variant_counters: Dict[str, int] = {}  # Track allocations

        # Performance tracking
        self.performance_data: Dict[str, Dict[str, List[float]]] = {}
        self.error_tracking: Dict[str, Dict[str, int]] = {}

        self.logger.info("A/B Testing Framework initialized")

    def setup_logging(self):
        """Setup logging for A/B testing framework"""
        os.makedirs("E:/TORQ-CONSOLE/logs", exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('E:/TORQ-CONSOLE/logs/ab_testing.log'),
                logging.StreamHandler()
            ]
        )

    def create_routing_ab_test(self, name: str, description: str,
                             routing_strategies: Dict[str, Dict],
                             traffic_split: Dict[str, float],
                             metrics: Dict[str, Any]) -> str:
        """
        Create an A/B test for routing strategies

        Args:
            name: Test name
            description: Test description
            routing_strategies: Dict of strategy_name -> strategy_config
            traffic_split: Dict of strategy_name -> weight (0.0-1.0)
            metrics: Configuration for metrics to track

        Returns:
            Test ID
        """
        test_id = str(uuid.uuid4())

        # Validate traffic split
        total_weight = sum(traffic_split.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Traffic split weights must sum to 1.0, got {total_weight}")

        # Create traffic splits
        splits = []
        for variant_name, weight in traffic_split.items():
            splits.append(TrafficSplit(
                variant_name=variant_name,
                weight=weight,
                allocation_percentage=weight * 100,
                sticky_key=hashlib.md5(variant_name.encode()).hexdigest()[:8]
            ))

        # Identify control and treatment variants
        variant_names = list(routing_strategies.keys())
        control_variant = variant_names[0]
        treatment_variants = variant_names[1:]

        # Create test configuration
        test_config = ABTestConfig(
            test_id=test_id,
            name=name,
            description=description,
            control_variant=control_variant,
            treatment_variants=treatment_variants,
            traffic_split_type=TrafficSplitType.WEIGHTED_SPLIT,
            traffic_splits=splits,
            primary_metric=metrics.get("primary_metric", "success_rate"),
            secondary_metrics=metrics.get("secondary_metrics", []),
            success_criteria=metrics.get("success_criteria", {}),
            sample_size_required=metrics.get("sample_size_required", 100),
            confidence_level=metrics.get("confidence_level", 0.95),
            test_duration_hours=metrics.get("test_duration_hours", 72)
        )

        self.active_tests[test_id] = test_config

        # Initialize performance tracking
        self.performance_data[test_id] = {variant: [] for variant in variant_names}
        self.error_tracking[test_id] = {variant: 0 for variant in variant_names}
        self.variant_counters[test_id] = {variant: 0 for variant in variant_names}

        self.logger.info(f"Created A/B test: {test_id} - {name}")
        return test_id

    def assign_variant(self, test_id: str, user_id: str, query: str) -> str:
        """
        Assign a user to a test variant based on traffic split

        Args:
            test_id: Test ID
            user_id: User identifier (for sticky splitting)
            query: User query (for context-aware assignment)

        Returns:
            Assigned variant name
        """
        test_config = self.active_tests.get(test_id)
        if not test_config:
            raise ValueError(f"Test {test_id} not found")

        # Use sticky assignment if configured
        assignment_key = f"{test_id}_{user_id}"
        if assignment_key in self.user_assignments:
            variant = self.user_assignments[assignment_key]
            self.variant_counters[test_id][variant] += 1
            return variant

        # Assign based on traffic split type
        if test_config.traffic_split_type == TrafficSplitType.EQUAL_SPLIT:
            variant = self._equal_split_assignment(test_config)
        elif test_config.traffic_split_type == TrafficSplitType.WEIGHTED_SPLIT:
            variant = self._weighted_split_assignment(test_config)
        elif test_config.traffic_split_type == TrafficSplitType.STICKY_SPLIT:
            variant = self._sticky_split_assignment(test_config, user_id)
        elif test_config.traffic_split_type == TrafficSplitType.GRADUAL_ROLLOUT:
            variant = self._gradual_rollout_assignment(test_config)
        else:
            variant = self._weighted_split_assignment(test_config)

        # Store assignment for sticky behavior
        self.user_assignments[assignment_key] = variant
        self.variant_counters[test_id][variant] += 1

        return variant

    def _equal_split_assignment(self, test_config: ABTestConfig) -> str:
        """Equal split assignment"""
        variants = [test_config.control_variant] + test_config.treatment_variants
        return random.choice(variants)

    def _weighted_split_assignment(self, test_config: ABTestConfig) -> str:
        """Weighted split assignment"""
        rand_val = random.random()
        cumulative_weight = 0.0

        for split in test_config.traffic_splits:
            cumulative_weight += split.weight
            if rand_val <= cumulative_weight:
                return split.variant_name

        # Fallback to control
        return test_config.control_variant

    def _sticky_split_assignment(self, test_config: ABTestConfig, user_id: str) -> str:
        """Sticky split assignment based on user ID"""
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
        variants = [test_config.control_variant] + test_config.treatment_variants
        variant_index = user_hash % len(variants)
        return variants[variant_index]

    def _gradual_rollout_assignment(self, test_config: ABTestConfig) -> str:
        """Gradual rollout assignment - start with control, gradually increase treatment"""
        # Get current counts
        counts = self.variant_counters.get(test_config.test_id, {})
        total_requests = sum(counts.values())

        # Gradual rollout: 0% treatment initially, up to 50% over time
        treatment_percentage = min(0.5, total_requests / (test_config.sample_size_required * 2))

        if random.random() < treatment_percentage and test_config.treatment_variants:
            return random.choice(test_config.treatment_variants)
        else:
            return test_config.control_variant

    async def record_request_result(self, test_id: str, variant: str, query: str,
                                   result: Dict[str, Any]) -> None:
        """
        Record the result of a request for analysis

        Args:
            test_id: Test ID
            variant: Variant used
            query: Original query
            result: Request result
        """
        if test_id not in self.active_tests:
            return

        # Record performance metrics
        performance_metrics = self._extract_performance_metrics(result)
        for metric_name, value in performance_metrics.items():
            if metric_name not in self.performance_data[test_id]:
                self.performance_data[test_id][metric_name] = {}
            if variant not in self.performance_data[test_id][metric_name]:
                self.performance_data[test_id][metric_name][variant] = []
            self.performance_data[test_id][metric_name][variant].append(value)

        # Record errors
        if not result.get("success", True):
            self.error_tracking[test_id][variant] += 1

        self.logger.debug(f"Recorded result for test {test_id}, variant {variant}")

    def _extract_performance_metrics(self, result: Dict[str, Any]) -> Dict[str, float]:
        """Extract performance metrics from result"""
        metrics = {}

        # Basic metrics
        metrics["success"] = 1.0 if result.get("success", True) else 0.0
        metrics["execution_time"] = result.get("execution_time", 0.0)
        metrics["confidence"] = result.get("confidence", 0.0)

        # Extract detailed metrics if available
        if "metrics" in result:
            for metric_name, value in result["metrics"].items():
                metrics[metric_name] = float(value)

        # Calculate derived metrics
        metrics["success_rate"] = metrics["success"]
        metrics["avg_confidence"] = metrics["confidence"]

        return metrics

    async def analyze_test_results(self, test_id: str) -> ABTestResult:
        """
        Analyze A/B test results and determine statistical significance

        Args:
            test_id: Test ID to analyze

        Returns:
            Complete A/B test result
        """
        test_config = self.active_tests.get(test_id)
        if not test_config:
            raise ValueError(f"Test {test_id} not found")

        self.logger.info(f"Analyzing A/B test results for: {test_config.name}")

        # Calculate variant performances
        variant_performances = {}
        all_variants = [test_config.control_variant] + test_config.treatment_variants

        for variant in all_variants:
            performance = self._calculate_variant_performance(test_id, variant)
            variant_performances[variant] = performance

        # Run statistical tests
        statistical_results = []
        for treatment_variant in test_config.treatment_variants:
            # Test primary metric
            result = self._run_statistical_test(
                test_config, test_id, test_config.control_variant,
                treatment_variant, test_config.primary_metric
            )
            statistical_results.append(result)

            # Test secondary metrics
            for metric in test_config.secondary_metrics:
                result = self._run_statistical_test(
                    test_config, test_id, test_config.control_variant,
                    treatment_variant, metric
                )
                statistical_results.append(result)

        # Determine winning variant
        winning_variant = self._determine_winning_variant(
            test_config, variant_performances, statistical_results
        )

        # Generate recommendations
        recommendations = self._generate_ab_test_recommendations(
            test_config, variant_performances, statistical_results, winning_variant
        )

        # Determine next steps
        next_steps = self._determine_ab_test_next_steps(
            test_config, statistical_results, winning_variant
        )

        # Calculate test duration
        created_at = test_config.created_at
        completed_at = datetime.now()
        test_duration = completed_at - created_at

        # Create result
        result = ABTestResult(
            test_id=test_id,
            status=ExperimentStatus.COMPLETED,
            variant_performances=variant_performances,
            statistical_results=statistical_results,
            winning_variant=winning_variant,
            confidence_level=test_config.confidence_level,
            test_duration=test_duration,
            recommendations=recommendations,
            next_steps=next_steps,
            completed_at=completed_at
        )

        # Store result
        self.test_results[test_id] = result

        # Save to file
        await self._save_ab_test_result(test_id, result)

        return result

    def _calculate_variant_performance(self, test_id: str, variant: str) -> VariantPerformance:
        """Calculate performance metrics for a variant"""
        total_requests = self.variant_counters[test_id].get(variant, 0)
        successful_requests = 0
        metrics = {}
        response_times = []
        confidence_scores = []

        # Get performance data
        performance_data = self.performance_data.get(test_id, {})

        # Calculate success rate
        if "success" in performance_data and variant in performance_data["success"]:
            successes = performance_data["success"][variant]
            successful_requests = sum(successes)

        # Calculate metrics
        for metric_name, metric_data in performance_data.items():
            if variant in metric_data and metric_data[variant]:
                values = metric_data[variant]
                metrics[metric_name] = statistics.mean(values)

                # Store specific metric types
                if metric_name == "execution_time":
                    response_times = values
                elif metric_name == "confidence":
                    confidence_scores = values

        # Get error rates
        error_rates = self.error_tracking.get(test_id, {})
        total_errors = error_rates.get(variant, 0)

        return VariantPerformance(
            variant_name=variant,
            total_requests=total_requests,
            successful_requests=successful_requests,
            metrics=metrics,
            response_times=response_times,
            confidence_scores=confidence_scores,
            error_rates={"total": total_errors},
            last_updated=datetime.now()
        )

    def _run_statistical_test(self, test_config: ABTestConfig, test_id: str,
                            control_variant: str, treatment_variant: str,
                            metric: str) -> StatisticalResult:
        """Run statistical test between control and treatment variants"""
        performance_data = self.performance_data.get(test_id, {})

        if metric not in performance_data:
            return StatisticalResult(
                test_name="No Data",
                metric=metric,
                control_value=0.0,
                treatment_value=0.0,
                improvement=0.0,
                confidence_interval=(0.0, 0.0),
                p_value=1.0,
                is_significant=False,
                statistical_power=0.0
            )

        control_data = performance_data[metric].get(control_variant, [])
        treatment_data = performance_data[metric].get(treatment_variant, [])

        if not control_data or not treatment_data:
            return StatisticalResult(
                test_name="Insufficient Data",
                metric=metric,
                control_value=0.0,
                treatment_value=0.0,
                improvement=0.0,
                confidence_interval=(0.0, 0.0),
                p_value=1.0,
                is_significant=False,
                statistical_power=0.0
            )

        # Calculate basic statistics
        control_mean = statistics.mean(control_data)
        treatment_mean = statistics.mean(treatment_data)
        improvement = (treatment_mean - control_mean) / control_mean if control_mean != 0 else 0.0

        # Run appropriate statistical test
        if len(control_data) >= 30 and len(treatment_data) >= 30:
            # Use Z-test for large samples
            test_result = self._z_test(control_data, treatment_data, test_config.confidence_level)
        else:
            # Use t-test for small samples
            test_result = self._t_test(control_data, treatment_data, test_config.confidence_level)

        return StatisticalResult(
            test_name=test_result["test_name"],
            metric=metric,
            control_value=control_mean,
            treatment_value=treatment_mean,
            improvement=improvement,
            confidence_interval=test_result["confidence_interval"],
            p_value=test_result["p_value"],
            is_significant=test_result["is_significant"],
            statistical_power=test_result["statistical_power"]
        )

    def _t_test(self, control_data: List[float], treatment_data: List[float],
                confidence_level: float) -> Dict[str, Any]:
        """Perform t-test between two samples"""
        from scipy import stats

        # Calculate t-test
        t_stat, p_value = stats.ttest_ind(treatment_data, control_data)

        # Calculate confidence interval
        pooled_std = math.sqrt(
            ((len(control_data) - 1) * statistics.variance(control_data) +
             (len(treatment_data) - 1) * statistics.variance(treatment_data)) /
            (len(control_data) + len(treatment_data) - 2)
        )

        mean_diff = statistics.mean(treatment_data) - statistics.mean(control_data)
        se = pooled_std * math.sqrt(1/len(control_data) + 1/len(treatment_data))
        t_critical = stats.t.ppf((1 + confidence_level) / 2, len(control_data) + len(treatment_data) - 2)

        margin_error = t_critical * se
        confidence_interval = (mean_diff - margin_error, mean_diff + margin_error)

        # Calculate statistical power (simplified)
        effect_size = mean_diff / pooled_std if pooled_std != 0 else 0.0
        statistical_power = min(0.99, abs(effect_size) * math.sqrt(min(len(control_data), len(treatment_data)) / 2))

        return {
            "test_name": "Two-Sample t-test",
            "confidence_interval": confidence_interval,
            "p_value": p_value,
            "is_significant": p_value < (1 - confidence_level),
            "statistical_power": statistical_power
        }

    def _z_test(self, control_data: List[float], treatment_data: List[float],
               confidence_level: float) -> Dict[str, Any]:
        """Perform Z-test between two samples"""
        from scipy import stats

        # Calculate means and standard errors
        control_mean = statistics.mean(control_data)
        treatment_mean = statistics.mean(treatment_data)
        control_se = statistics.stdev(control_data) / math.sqrt(len(control_data))
        treatment_se = statistics.stdev(treatment_data) / math.sqrt(len(treatment_data))

        # Z-test
        z_stat = (treatment_mean - control_mean) / math.sqrt(control_se**2 + treatment_se**2)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

        # Confidence interval
        se_diff = math.sqrt(control_se**2 + treatment_se**2)
        z_critical = stats.norm.ppf((1 + confidence_level) / 2)
        margin_error = z_critical * se_diff
        mean_diff = treatment_mean - control_mean
        confidence_interval = (mean_diff - margin_error, mean_diff + margin_error)

        # Statistical power
        effect_size = mean_diff / math.sqrt((statistics.variance(control_data) + statistics.variance(treatment_data)) / 2)
        statistical_power = min(0.99, abs(effect_size) * math.sqrt(min(len(control_data), len(treatment_data)) / 2))

        return {
            "test_name": "Two-Sample Z-test",
            "confidence_interval": confidence_interval,
            "p_value": p_value,
            "is_significant": p_value < (1 - confidence_level),
            "statistical_power": statistical_power
        }

    def _determine_winning_variant(self, test_config: ABTestConfig,
                                 variant_performances: Dict[str, VariantPerformance],
                                 statistical_results: List[StatisticalResult]) -> Optional[str]:
        """Determine the winning variant based on statistical significance"""
        significant_improvements = []

        for result in statistical_results:
            if result.is_significant and result.metric == test_config.primary_metric:
                if result.improvement > 0:
                    # Find which variant this improvement belongs to
                    for variant in test_config.treatment_variants:
                        variant_performance = variant_performances[variant]
                        if abs(variant_performance.metrics.get(result.metric, 0) - result.treatment_value) < 0.001:
                            significant_improvements.append((variant, result.improvement))
                            break

        if significant_improvements:
            # Return variant with highest significant improvement
            return max(significant_improvements, key=lambda x: x[1])[0]

        return None

    def _generate_ab_test_recommendations(self, test_config: ABTestConfig,
                                        variant_performances: Dict[str, VariantPerformance],
                                        statistical_results: List[StatisticalResult],
                                        winning_variant: Optional[str]) -> List[str]:
        """Generate recommendations based on A/B test results"""
        recommendations = []

        # Check if we have a statistically significant winner
        significant_results = [r for r in statistical_results if r.is_significant]

        if winning_variant and significant_results:
            recommendations.append(f"Deploy winning variant '{winning_variant}' - shows statistically significant improvement")

            # Quantify improvement
            primary_results = [r for r in significant_results if r.metric == test_config.primary_metric]
            if primary_results:
                improvement = primary_results[0].improvement
                recommendations.append(f"Primary metric improvement: {improvement:+.1%}")
        else:
            recommendations.append("No statistically significant improvement detected")
            recommendations.append("Consider running test longer or with larger sample size")

        # Check performance consistency
        control_perf = variant_performances[test_config.control_variant]
        for variant in test_config.treatment_variants:
            variant_perf = variant_performants[variant]
            if variant_perf.metrics.get("success_rate", 0) < control_perf.metrics.get("success_rate", 0) * 0.95:
                recommendations.append(f"Variant '{variant}' shows degraded performance - investigate issues")

        # Sample size recommendations
        min_sample_size = min(len(vp.response_times) for vp in variant_performances.values() if vp.response_times)
        if min_sample_size < test_config.sample_size_required:
            recommendations.append(f"Sample size ({min_sample_size}) below recommended ({test_config.sample_size_required}) - run test longer")

        return recommendations

    def _determine_ab_test_next_steps(self, test_config: ABTestConfig,
                                    statistical_results: List[StatisticalResult],
                                    winning_variant: Optional[str]) -> List[str]:
        """Determine next steps for the A/B test"""
        next_steps = []

        significant_results = [r for r in statistical_results if r.is_significant]

        if winning_variant and significant_results:
            next_steps.append(f"Gradually roll out winning variant '{winning_variant}' to production")
            next_steps.append("Monitor performance metrics in production environment")
            next_steps.append("Plan follow-up test to validate long-term performance")
        else:
            next_steps.extend([
                "Analyze why variants didn't show significant improvement",
                "Review test design and traffic allocation",
                "Consider testing different routing strategies",
                "Increase sample size or test duration"
            ])

        # Always document learnings
        next_steps.extend([
            "Document test learnings and insights",
            "Update routing strategy documentation",
            "Share results with development team"
        ])

        return next_steps

    async def _save_ab_test_result(self, test_id: str, result: ABTestResult):
        """Save A/B test result to file"""
        os.makedirs("E:/TORQ-CONSOLE/ab_test_results", exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"E:/TORQ-CONSOLE/ab_test_results/ab_test_{test_id}_{timestamp}.json"

        # Convert to serializable format
        result_data = asdict(result)
        result_data["completed_at"] = result.completed_at.isoformat()
        result_data["test_duration"] = str(result.test_duration)
        result_data["status"] = result.status.value

        # Convert variant performances
        for variant_name, performance in result_data["variant_performances"].items():
            performance["last_updated"] = performance["last_updated"].isoformat()

        # Convert statistical results
        for stat_result in result_data["statistical_results"]:
            stat_result["confidence_interval"] = list(stat_result["confidence_interval"])

        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)

        self.logger.info(f"A/B test result saved to: {result_file}")

    def get_test_status(self, test_id: str) -> Dict[str, Any]:
        """Get current status of an A/B test"""
        test_config = self.active_tests.get(test_id)
        if not test_config:
            return {"status": "not_found"}

        # Get current counts
        counts = self.variant_counters.get(test_id, {})
        total_requests = sum(counts.values())

        # Calculate elapsed time
        elapsed = datetime.now() - test_config.created_at
        remaining_time = timedelta(hours=test_config.test_duration_hours) - elapsed

        return {
            "status": "running",
            "test_name": test_config.name,
            "total_requests": total_requests,
            "requests_per_variant": counts,
            "sample_size_required": test_config.sample_size_required,
            "progress_percentage": min(100, (total_requests / test_config.sample_size_required) * 100),
            "time_elapsed": str(elapsed),
            "time_remaining": str(max(timedelta(0), remaining_time)),
            "is_complete": total_requests >= test_config.sample_size_required
        }

    def print_test_result(self, test_id: str):
        """Print formatted A/B test result"""
        result = self.test_results.get(test_id)
        test_config = self.active_tests.get(test_id)

        if not result or not test_config:
            print(f"A/B test {test_id} not found")
            return

        print(f"\n{'='*80}")
        print(f"A/B TEST RESULT: {test_config.name}")
        print(f"{'='*80}")
        print(f"Test ID: {test_id}")
        print(f"Status: {result.status.value}")
        print(f"Test Duration: {result.test_duration}")
        print(f"Confidence Level: {result.confidence_level:.1%}")
        print(f"Completed: {result.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"\nVARIANT PERFORMANCE:")
        for variant_name, performance in result.variant_performances.items():
            status = "🏆 WINNER" if variant_name == result.winning_variant else "  "
            print(f"  {status} {variant_name}:")
            print(f"    Total Requests: {performance.total_requests}")
            print(f"    Success Rate: {performance.metrics.get('success_rate', 0):.1%}")
            print(f"    Avg Confidence: {performance.metrics.get('avg_confidence', 0):.1%}")
            print(f"    Avg Execution Time: {performance.metrics.get('execution_time', 0):.2f}s")

        print(f"\nSTATISTICAL SIGNIFICANCE:")
        for stat_result in result.statistical_results:
            significance = "✅ SIGNIFICANT" if stat_result.is_significant else "❌ NOT SIGNIFICANT"
            print(f"  {significance} {stat_result.metric}:")
            print(f"    Control: {stat_result.control_value:.3f}")
            print(f"    Treatment: {stat_result.treatment_value:.3f}")
            print(f"    Improvement: {stat_result.improvement:+.1%}")
            print(f"    P-value: {stat_result.p_value:.4f}")
            print(f"    Confidence Interval: ({stat_result.confidence_interval[0]:.3f}, {stat_result.confidence_interval[1]:.3f})")

        print(f"\nWINNING VARIANT: {result.winning_variant or 'No significant improvement'}")

        print(f"\nRECOMMENDATIONS:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")

        print(f"\nNEXT STEPS:")
        for i, step in enumerate(result.next_steps, 1):
            print(f"  {i}. {step}")

        print(f"{'='*80}")

# Main execution function for testing
async def main():
    """Main execution function for testing A/B testing framework"""
    print("🧪 Maxim AI - Phase 2: A/B Testing Framework")
    print("=" * 60)

    # Initialize components
    experiment_manager = ExperimentManager()
    ab_framework = ABTestingFramework(experiment_manager)

    # Create A/B test for routing strategies
    print("\n📊 Creating Routing Strategy A/B Test...")

    routing_strategies = {
        "default_routing": {
            "logic": "existing_orchestrator_logic",
            "description": "Current default routing logic"
        },
        "enhanced_keyword_routing": {
            "logic": "improved_keyword_detection",
            "description": "Enhanced keyword-based routing with better accuracy"
        },
        "ml_based_routing": {
            "logic": "machine_learning_classifier",
            "description": "ML-based routing using historical performance data"
        }
    }

    traffic_split = {
        "default_routing": 0.5,
        "enhanced_keyword_routing": 0.25,
        "ml_based_routing": 0.25
    }

    metrics_config = {
        "primary_metric": "tool_selection_efficiency",
        "secondary_metrics": ["success_rate", "execution_performance"],
        "success_criteria": {
            "tool_selection_efficiency": 0.05,
            "success_rate": 0.02
        },
        "sample_size_required": 100,
        "confidence_level": 0.95,
        "test_duration_hours": 24
    }

    # Create A/B test
    test_id = ab_framework.create_routing_ab_test(
        name="Routing Strategy Comparison",
        description="Compare different routing strategies for Prince Flowers queries",
        routing_strategies=routing_strategies,
        traffic_split=traffic_split,
        metrics=metrics_config
    )

    print(f"✅ Created A/B test: {test_id}")

    # Simulate test execution
    print("\n🚀 Simulating test execution...")

    # Simulate user assignments and requests
    test_queries = [
        "Search for Python tutorials",
        "Explain machine learning concepts",
        "Create a REST API example",
        "What are your capabilities?",
        "Compare different programming languages"
    ]

    # Simulate requests
    for i, query in enumerate(test_queries):
        for user_id in range(20):  # 20 users per query
            # Assign variant
            variant = ab_framework.assign_variant(test_id, f"user_{user_id}", query)

            # Simulate request result
            mock_result = {
                "success": random.random() > 0.1,  # 90% success rate
                "execution_time": 0.5 + random.random() * 2.0,
                "confidence": 0.7 + random.random() * 0.3,
                "metrics": {
                    "tool_selection_efficiency": 0.7 + random.random() * 0.3,
                    "success_rate": 1.0 if random.random() > 0.1 else 0.0,
                    "execution_performance": 0.8 + random.random() * 0.2
                }
            }

            await ab_framework.record_request_result(test_id, variant, query, mock_result)

    # Analyze results
    print("\n📈 Analyzing test results...")
    result = await ab_framework.analyze_test_results(test_id)

    # Print results
    ab_framework.print_test_result(test_id)

    print(f"\n✅ A/B testing framework demonstration completed!")

if __name__ == "__main__":
    import uuid
    import random
    asyncio.run(main())