"""
TORQ Console Evaluation Scoring System

Implements deterministic scoring for evaluation tasks with support for:
- Weighted task scoring
- Category-based scoring
- Tool usage F1 calculation
- Performance benchmarking
- Regression detection
"""

import json
import time
import hashlib
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result of executing an evaluation task"""
    task_id: str
    success: bool
    outputs: List[Dict[str, Any]]
    tools_used: List[str]
    tools_planned: List[str]
    latency_ms: float
    tokens_used: int
    error_message: Optional[str] = None
    timestamps: Dict[str, float] = None


@dataclass
class ScoreBreakdown:
    """Detailed score breakdown for analysis"""
    task_score: float
    weighted_score: float
    accuracy_score: float
    efficiency_score: float
    robustness_score: float
    tool_usage_score: float


class EvaluationScorer:
    """
    Deterministic scoring system for TORQ Console evaluations

    Guarantees same seed → same result through:
    - Fixed random seeds
    - Deterministic algorithms
    - Reproducible calculations
    """

    def __init__(self, seed: int = 42):
        """Initialize scorer with deterministic seed"""
        self.seed = seed
        np.random.seed(seed)
        self._deterministic_cache = {}

    def score_task(self, task: Dict[str, Any], result: TaskResult) -> ScoreBreakdown:
        """
        Score a single task execution

        Args:
            task: Task definition from tasks.json
            result: Execution result

        Returns:
            ScoreBreakdown with detailed scoring
        """
        # Create deterministic cache key
        cache_key = self._create_cache_key(task, result)

        if cache_key in self._deterministic_cache:
            return self._deterministic_cache[cache_key]

        # Calculate individual scores
        accuracy_score = self._calculate_accuracy_score(task, result)
        efficiency_score = self._calculate_efficiency_score(task, result)
        robustness_score = self._calculate_robustness_score(task, result)
        tool_usage_score = self._calculate_tool_usage_score(task, result)

        # Calculate weighted task score
        task_weight = task.get('weight', 1.0)
        task_score = (accuracy_score + efficiency_score + robustness_score + tool_usage_score) / 4.0
        weighted_score = task_score * task_weight

        breakdown = ScoreBreakdown(
            task_score=task_score,
            weighted_score=weighted_score,
            accuracy_score=accuracy_score,
            efficiency_score=efficiency_score,
            robustness_score=robustness_score,
            tool_usage_score=tool_usage_score
        )

        # Cache for determinism
        self._deterministic_cache[cache_key] = breakdown
        return breakdown

    def _calculate_accuracy_score(self, task: Dict[str, Any], result: TaskResult) -> float:
        """Calculate accuracy score based on expected outputs"""
        if not result.success:
            return 0.0

        expected_outputs = task.get('expected_outputs', [])
        if not expected_outputs:
            return 1.0  # No accuracy requirements

        scores = []

        for expected in expected_outputs:
            output_type = expected.get('type')

            if output_type == 'string_match' or output_type == 'keyword_match':
                score = self._score_string_match(expected, result.outputs)
                scores.append(score)

            elif output_type == 'valid_python':
                score = self._score_python_code(result.outputs)
                scores.append(score)

            elif output_type == 'file_created':
                score = self._score_file_creation(expected, result.outputs)
                scores.append(score)

            elif output_type == 'api_call_success':
                score = self._score_api_call(result.outputs)
                scores.append(score)

            elif output_type == 'context_retention':
                score = self._score_context_retention(expected, result.outputs)
                scores.append(score)

            else:
                # Default scoring for unknown types
                score = 0.5
                scores.append(score)

        # Weighted average of accuracy scores
        if not scores:
            return 0.5

        weights = [expected.get('weight', 1.0) for expected in expected_outputs]
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        total_weight = sum(weights)

        return weighted_sum / total_weight

    def _calculate_efficiency_score(self, task: Dict[str, Any], result: TaskResult) -> float:
        """Calculate efficiency score based on performance"""
        if not result.success:
            return 0.0

        # Latency scoring
        max_latency = task.get('max_latency_ms', 10000)
        latency_ratio = min(result.latency_ms / max_latency, 1.0)
        latency_score = 1.0 - (latency_ratio * 0.5)  # Max 50% deduction

        # Token efficiency scoring
        max_tokens = task.get('max_tokens', 5000)
        if max_tokens > 0:
            token_ratio = min(result.tokens_used / max_tokens, 1.0)
            token_score = 1.0 - (token_ratio * 0.3)  # Max 30% deduction
        else:
            token_score = 1.0

        # Combined efficiency score
        return (latency_score + token_score) / 2.0

    def _calculate_robustness_score(self, task: Dict[str, Any], result: TaskResult) -> float:
        """Calculate robustness score based on error handling"""
        if result.success:
            return 1.0

        # Check if errors were expected
        expected_outputs = task.get('expected_outputs', [])
        expected_errors = []

        for expected in expected_outputs:
            if expected.get('type') == 'error_handling':
                expected_errors = expected.get('errors_expected', [])
                break

        if not expected_errors:
            return 0.0  # Unexpected failure

        # Check if the error matches expected
        if result.error_message:
            for error_type in expected_errors:
                if error_type.lower() in result.error_message.lower():
                    return 0.8  # Good error handling

        return 0.2  # Failed but tried

    def _calculate_tool_usage_score(self, task: Dict[str, Any], result: TaskResult) -> float:
        """Calculate tool usage F1 score"""
        required_tools = task.get('tool_requirements', [])

        if not required_tools:
            return 1.0  # No tools required

        # Calculate precision and recall
        used_tools = set(result.tools_used)
        required_tools = set(required_tools)

        if not used_tools and not required_tools:
            return 1.0

        true_positives = len(used_tools & required_tools)
        false_positives = len(used_tools - required_tools)
        false_negatives = len(required_tools - used_tools)

        # Calculate F1 score
        if true_positives == 0:
            return 0.0

        precision = true_positives / (true_positives + false_positives)
        recall = true_positives / (true_positives + false_negatives)

        if precision + recall == 0:
            return 0.0

        f1 = 2 * (precision * recall) / (precision + recall)
        return f1

    def calculate_overall_score(self, task_results: List[Tuple[Dict[str, Any], TaskResult]]) -> Dict[str, float]:
        """
        Calculate overall evaluation scores

        Args:
            task_results: List of (task, result) tuples

        Returns:
            Dictionary with overall scores and breakdowns
        """
        # Score each task
        breakdowns = []
        category_scores = {}

        for task, result in task_results:
            breakdown = self.score_task(task, result)
            breakdowns.append(breakdown)

            # Track category scores
            category = task.get('category', 'core')
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(breakdown)

        # Calculate overall scores
        total_weighted_score = sum(b.weighted_score for b in breakdowns)
        total_weight = sum(task.get('weight', 1.0) for task, _ in task_results)

        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0

        # Calculate category averages
        category_averages = {}
        for category, scores in category_scores.items():
            category_total = sum(s.weighted_score for s in scores)
            category_avg = category_total / len(scores) if scores else 0.0
            category_averages[category] = category_avg

        # Calculate component averages
        avg_accuracy = np.mean([b.accuracy_score for b in breakdowns])
        avg_efficiency = np.mean([b.efficiency_score for b in breakdowns])
        avg_robustness = np.mean([b.robustness_score for b in breakdowns])
        avg_tool_usage = np.mean([b.tool_usage_score for b in breakdowns])

        # Calculate overall tool F1
        all_tools_used = []
        all_tools_required = []
        for task, result in task_results:
            all_tools_used.extend(result.tools_used)
            all_tools_required.extend(task.get('tool_requirements', []))

        overall_tool_f1 = self._calculate_tool_f1(all_tools_used, all_tools_required)

        return {
            'overall_score': overall_score,
            'category_scores': category_averages,
            'component_scores': {
                'accuracy': avg_accuracy,
                'efficiency': avg_efficiency,
                'robustness': avg_robustness,
                'tool_usage': avg_tool_usage
            },
            'tool_f1': overall_tool_f1,
            'total_tasks': len(task_results),
            'successful_tasks': sum(1 for _, r in task_results if r.success),
            'total_weighted_score': total_weighted_score,
            'deterministic': True,
            'seed_used': self.seed
        }

    def check_regression(self, current_scores: Dict[str, float],
                        baseline_scores: Dict[str, float],
                        criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for regressions compared to baseline

        Args:
            current_scores: Current evaluation scores
            baseline_scores: Baseline scores to compare against
            criteria: Passing criteria from tasks.json

        Returns:
            Regression check results
        """
        # Extract criteria
        max_regression_drop = criteria.get('max_regression_drop', 2.0)
        max_domain_regression_drop = criteria.get('max_domain_regression_drop', 3.0)
        min_tool_f1 = criteria.get('tool_f1_min', 0.75)

        # Check overall regression
        current_overall = current_scores.get('overall_score', 0.0)
        baseline_overall = baseline_scores.get('overall_score', 0.0)
        overall_drop = baseline_overall - current_overall

        # Check domain regression
        domain_regressions = {}
        current_categories = current_scores.get('category_scores', {})
        baseline_categories = baseline_scores.get('category_scores', {})

        for domain in baseline_categories:
            current_domain = current_categories.get(domain, 0.0)
            baseline_domain = baseline_categories.get(domain, 0.0)
            domain_drop = baseline_domain - current_domain

            if domain_drop > max_domain_regression_drop:
                domain_regressions[domain] = domain_drop

        # Check tool F1
        current_tool_f1 = current_scores.get('tool_f1', 0.0)
        tool_f1_ok = current_tool_f1 >= min_tool_f1

        # Determine overall pass/fail
        passed = (
            overall_drop <= max_regression_drop and
            len(domain_regressions) == 0 and
            tool_f1_ok
        )

        return {
            'passed': passed,
            'overall_score': current_overall,
            'baseline_score': baseline_overall,
            'overall_drop': overall_drop,
            'max_drop_allowed': max_regression_drop,
            'domain_regressions': domain_regressions,
            'tool_f1': current_tool_f1,
            'tool_f1_threshold': min_tool_f1,
            'regression_detected': not passed,
            'details': {
                'overall_regression': overall_drop > max_regression_drop,
                'domain_regressions_count': len(domain_regressions),
                'tool_f1_failure': not tool_f1_ok
            }
        }

    def _create_cache_key(self, task: Dict[str, Any], result: TaskResult) -> str:
        """Create deterministic cache key"""
        # Create a deterministic string representation
        key_data = {
            'task_id': task['id'],
            'task_hash': hashlib.md5(json.dumps(task, sort_keys=True).encode()).hexdigest()[:8],
            'result_hash': hashlib.md5(json.dumps({
                'success': result.success,
                'outputs': result.outputs,
                'tools_used': sorted(result.tools_used),
                'latency_ms': result.latency_ms,
                'tokens_used': result.tokens_used
            }, sort_keys=True).encode()).hexdigest()[:8],
            'seed': self.seed
        }

        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    # Helper methods for specific scoring
    def _score_string_match(self, expected: Dict[str, Any], outputs: List[Dict[str, Any]]) -> float:
        """Score string matching against expected contains"""
        expected_strings = expected.get('contains', [])
        if isinstance(expected_strings, str):
            expected_strings = [expected_strings]

        output_text = ' '.join([str(o.get('content', '')) for o in outputs]).lower()

        matches = sum(1 for s in expected_strings if s.lower() in output_text)
        return matches / len(expected_strings) if expected_strings else 0.0

    def _score_python_code(self, outputs: List[Dict[str, Any]]) -> float:
        """Score Python code validity"""
        output_text = ' '.join([str(o.get('content', '')) for o in outputs])

        # Simple validation - check for Python syntax
        try:
            compile(output_text, '<string>', 'exec')
            return 1.0
        except SyntaxError:
            return 0.0

    def _score_file_creation(self, expected: Dict[str, Any], outputs: List[Dict[str, Any]]) -> float:
        """Score file creation"""
        # This would check actual file system in a real implementation
        # For now, score based on output mentions
        output_text = ' '.join([str(o.get('content', '')) for o in outputs]).lower()

        if 'created' in output_text or 'saved' in output_text or 'written' in output_text:
            return 1.0
        return 0.0

    def _score_api_call(self, outputs: List[Dict[str, Any]]) -> float:
        """Score API call success"""
        output_text = ' '.join([str(o.get('content', '')) for o in outputs]).lower()

        if 'success' in output_text or '200' in output_text or 'status' in output_text:
            return 1.0
        return 0.0

    def _score_context_retention(self, expected: Dict[str, Any], outputs: List[Dict[str, Any]]) -> float:
        """Score context retention"""
        # Simple check - look for acknowledgment of previous context
        output_text = ' '.join([str(o.get('content', '')) for o in outputs]).lower()

        if 'remember' in output_text or 'mentioned' in output_text or 'told' in output_text:
            return 1.0
        return 0.5  # Partial credit

    def _calculate_tool_f1(self, tools_used: List[str], tools_required: List[str]) -> float:
        """Calculate overall tool F1 score"""
        if not tools_used and not tools_required:
            return 1.0

        used_set = set(tools_used)
        required_set = set(tools_required)

        true_positives = len(used_set & required_set)
        false_positives = len(used_set - required_set)
        false_negatives = len(required_set - used_set)

        if true_positives == 0:
            return 0.0

        precision = true_positives / (true_positives + false_positives)
        recall = true_positives / (true_positives + false_negatives)

        if precision + recall == 0:
            return 0.0

        return 2 * (precision * recall) / (precision + recall)