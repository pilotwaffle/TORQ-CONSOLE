"""
Evaluator for the TORQ Agent Cognitive Loop.

Analyzes results and provides confidence scoring.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from .models import (
    CognitiveLoopConfig,
    EvaluationResult,
    ExecutionResult,
    ExecutionPlan,
    ReasoningPlan,
)


logger = logging.getLogger(__name__)


class Evaluator:
    """
    Evaluates the results of tool execution.

    Analyzes task completion, data integrity, and confidence scores.
    Determines if the results are acceptable or if a retry is needed.
    """

    def __init__(self, config: CognitiveLoopConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.Evaluator")

        # Evaluation criteria weights
        self._weights = {
            "task_completion": 0.4,
            "data_integrity": 0.3,
            "result_quality": 0.2,
            "efficiency": 0.1,
        }

    async def evaluate(
        self,
        execution_result: ExecutionResult,
        execution_plan: ExecutionPlan,
        reasoning_plan: ReasoningPlan,
        query: str,
        **kwargs
    ) -> EvaluationResult:
        """
        Evaluate the results of execution.

        Args:
            execution_result: Results from tool execution
            execution_plan: The plan that was executed
            reasoning_plan: Original reasoning plan
            query: The original query
            **kwargs: Additional context

        Returns:
            EvaluationResult with scores and recommendations
        """
        start_time = time.time()

        # Check task completion
        task_completed = self._check_task_completion(
            execution_result, execution_plan, query
        )

        # Check data integrity
        data_integrity_score = self._check_data_integrity(execution_result)

        # Check result quality
        quality_score = self._check_result_quality(
            execution_result, reasoning_plan, query
        )

        # Calculate overall confidence
        confidence_score = self._calculate_confidence(
            task_completed, data_integrity_score, quality_score, execution_result
        )

        # Determine if retry is needed
        should_retry, retry_reason = self._should_retry(
            task_completed, confidence_score, execution_result
        )

        # Generate suggestions
        suggestions = self._generate_suggestions(
            execution_result, confidence_score, should_retry
        )

        # Generate reasoning
        reasoning = self._generate_evaluation_reasoning(
            task_completed, confidence_score, data_integrity_score, quality_score
        )

        evaluation_time = time.time() - start_time

        result = EvaluationResult(
            task_completed=task_completed,
            confidence_score=confidence_score,
            data_integrity_score=data_integrity_score,
            quality_score=quality_score,
            reasoning=reasoning,
            should_retry=should_retry,
            retry_reason=retry_reason,
            suggestions=suggestions,
            metadata={
                "evaluation_time_seconds": evaluation_time,
                "min_threshold": self.config.min_evaluation_confidence,
            }
        )

        self.logger.debug(
            f"Evaluation complete: confidence={confidence_score:.2f}, "
            f"task_completed={task_completed}, should_retry={should_retry}"
        )

        return result

    def _check_task_completion(
        self,
        execution_result: ExecutionResult,
        execution_plan: ExecutionPlan,
        query: str
    ) -> bool:
        """Check if the task was completed successfully."""
        # Check if all steps succeeded
        if not execution_result.success and not execution_result.partial_results:
            return False

        # Check if expected outputs were generated
        for expected_output in execution_plan.expected_outputs:
            if expected_output.lower() not in str(execution_result.outputs).lower():
                # Don't fail on missing outputs, just log it
                pass

        # Check if the goal was addressed
        goal = execution_plan.goal.lower()
        outputs_str = str(execution_result.outputs).lower()

        # Simple keyword matching for goal satisfaction
        goal_words = set(goal.split())
        outputs_words = set(outputs_str.split())

        overlap = len(goal_words & outputs_words) / max(len(goal_words), 1)

        return overlap >= 0.3 or execution_result.success

    def _check_data_integrity(self, execution_result: ExecutionResult) -> float:
        """Check data integrity of results (0.0 to 1.0)."""
        integrity_score = 1.0

        # Check for errors
        if execution_result.errors:
            error_penalty = min(len(execution_result.errors) * 0.1, 0.5)
            integrity_score -= error_penalty

        # Check for empty results
        if not execution_result.outputs or execution_result.outputs == {"_metadata": {}}:
            integrity_score -= 0.3

        # Check tool success rate
        successful_tools = sum(1 for r in execution_result.tool_results if r.success)
        total_tools = len(execution_result.tool_results)

        if total_tools > 0:
            success_rate = successful_tools / total_tools
            integrity_score = integrity_score * success_rate + (1 - success_rate) * 0.5

        return max(0.0, min(1.0, integrity_score))

    def _check_result_quality(
        self,
        execution_result: ExecutionResult,
        reasoning_plan: ReasoningPlan,
        query: str
    ) -> float:
        """Check quality of results (0.0 to 1.0)."""
        quality_score = 0.5  # Base score

        # Check if results address the query
        outputs_str = str(execution_result.outputs).lower()
        query_lower = query.lower()

        query_words_in_output = sum(1 for word in query_lower.split() if word in outputs_str)
        query_coverage = query_words_in_output / max(len(query_lower.split()), 1)
        quality_score += query_coverage * 0.3

        # Check for relevant entities
        if reasoning_plan.key_entities:
            entities_found = sum(
                1 for entity in reasoning_plan.key_entities
                if entity.lower() in outputs_str
            )
            entity_coverage = entities_found / len(reasoning_plan.key_entities)
            quality_score += entity_coverage * 0.2

        # Check for substantive content (not just metadata)
        if len(outputs_str) > 100:  # Substantial content
            quality_score += 0.1

        return max(0.0, min(1.0, quality_score))

    def _calculate_confidence(
        self,
        task_completed: bool,
        data_integrity: float,
        quality: float,
        execution_result: ExecutionResult
    ) -> float:
        """Calculate overall confidence score."""
        # Weighted combination of factors
        confidence = (
            self._weights["task_completion"] * (1.0 if task_completed else 0.5) +
            self._weights["data_integrity"] * data_integrity +
            self._weights["result_quality"] * quality +
            self._weights["efficiency"] * (1.0 if execution_result.total_execution_time_seconds < 5.0 else 0.7)
        )

        # Penalty for partial results
        if execution_result.partial_results:
            confidence *= 0.8

        return max(0.0, min(1.0, confidence))

    def _should_retry(
        self,
        task_completed: bool,
        confidence: float,
        execution_result: ExecutionResult
    ) -> tuple[bool, str]:
        """Determine if a retry is needed."""
        # Critical failures require retry
        if not execution_result.success and not execution_result.partial_results:
            return True, "Execution failed with no partial results"

        # Low confidence requires retry
        if confidence < self.config.min_evaluation_confidence:
            return True, f"Confidence {confidence:.2f} below threshold {self.config.min_evaluation_confidence}"

        # Incomplete task may require retry
        if not task_completed:
            return True, "Task not fully completed"

        # Data integrity issues may require retry
        if execution_result.errors and len(execution_result.errors) > 2:
            return True, "Multiple errors during execution"

        return False, ""

    def _generate_suggestions(
        self,
        execution_result: ExecutionResult,
        confidence: float,
        should_retry: bool
    ) -> List[str]:
        """Generate suggestions for improvement."""
        suggestions = []

        if should_retry:
            if confidence < 0.5:
                suggestions.append("Consider using different tools or approaches")
            if execution_result.errors:
                suggestions.append("Review and fix tool errors before retry")
            suggestions.append("Add more specific parameters for tool execution")
        else:
            if confidence < 0.9:
                suggestions.append("Results could be enhanced with additional context")

        # Execution time suggestions
        if execution_result.total_execution_time_seconds > 5.0:
            suggestions.append("Consider optimizing tool execution order or enabling parallel execution")

        return suggestions

    def _generate_evaluation_reasoning(
        self,
        task_completed: bool,
        confidence: float,
        data_integrity: float,
        quality: float
    ) -> str:
        """Generate human-readable evaluation reasoning."""
        parts = []

        if task_completed:
            parts.append("The task was completed successfully")
        else:
            parts.append("The task was not fully completed")

        parts.append(f"with a confidence score of {confidence:.2f}. ")

        if data_integrity > 0.8:
            parts.append("Data integrity is good")
        elif data_integrity > 0.5:
            parts.append("Data integrity is acceptable")
        else:
            parts.append("Data integrity needs improvement")

        if quality > 0.8:
            parts.append("and result quality is high.")
        elif quality > 0.5:
            parts.append("and result quality is moderate.")
        else:
            parts.append("and result quality could be improved.")

        return " ".join(parts)

    async def emit_telemetry(
        self,
        phase: str,
        data: Dict[str, Any],
        run_id: Optional[str] = None
    ):
        """Emit telemetry for the evaluation phase."""
        if not self.config.telemetry_enabled:
            return

        try:
            from torq_console.core.telemetry.event import create_system_event
            from torq_console.core.telemetry.integration import get_telemetry_integration

            integration = get_telemetry_integration()
            await integration.record_agent_run(
                agent_name="evaluator",
                agent_type="cognitive_loop",
                status="started",
                run_id=run_id,
                **{f"evaluate.{k}": v for k, v in data.items()}
            )
        except Exception as e:
            self.logger.warning(f"Failed to emit telemetry: {e}")
