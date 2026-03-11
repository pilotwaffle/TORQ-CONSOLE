"""
Evaluation Engine - Service

Orchestrates execution evaluation using heuristic and LLM methods.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import (
    EvaluatorType,
    ExecutionEvaluationCreate,
    ExecutionEvaluationResponse,
    EvaluationScores,
    EvaluationContent,
)
from .scorers import (
    score_reasoning_quality,
    score_coherence,
    score_contradiction_resolution,
    score_risk_detection,
    score_next_action_quality,
    score_tool_use_efficiency,
    score_execution_completion,
    score_output_alignment,
    calculate_overall_score,
)

logger = logging.getLogger(__name__)


class EvaluationService:
    def __init__(self, supabase_client: Any, llm_client: Optional[Any] = None):
        """
        Initialize evaluation service.

        Args:
            supabase_client: Supabase client for persistence
            llm_client: Optional LLM client for enhanced evaluation
        """
        self.supabase = supabase_client
        self.llm_client = llm_client

    async def evaluate_execution(
        self,
        request: ExecutionEvaluationCreate,
        execution_data: Optional[Dict[str, Any]] = None,
        grouped_entries: Optional[Dict[str, List[Dict]]] = None,
    ) -> ExecutionEvaluationResponse:
        """
        Evaluate a completed execution.

        Args:
            request: Evaluation request
            execution_data: Execution outcome data
            grouped_entries: Workspace entries grouped by type

        Returns:
            Evaluation response with scores and analysis
        """
        evaluation_id = str(uuid.uuid())

        # Default values if not provided
        if execution_data is None:
            execution_data = {}
        if grouped_entries is None:
            grouped_entries = {}

        # Calculate scores based on evaluator type
        if request.evaluator_type == EvaluatorType.HEURISTIC:
            scores = self._heuristic_evaluation(execution_data, grouped_entries)
            content = self._heuristic_content(execution_data, grouped_entries)
        elif request.evaluator_type == EvaluatorType.LLM:
            scores = await self._llm_evaluation(execution_data, grouped_entries)
            content = await self._llm_content(execution_data, grouped_entries)
        else:  # HYBRID
            scores = self._heuristic_evaluation(execution_data, grouped_entries)
            content = await self._llm_content(execution_data, grouped_entries)

        # Calculate overall score
        overall = calculate_overall_score(scores)

        # Build response
        response = ExecutionEvaluationResponse(
            evaluation_id=evaluation_id,
            execution_id=request.execution_id,
            workspace_id=request.workspace_id,
            overall_score=overall,
            reasoning_score=scores.get("reasoning_quality", 50),
            outcome_score=scores.get("output_alignment", 50),
            risk_score=scores.get("risk_detection", 50),
            coherence_score=scores.get("coherence", 50),
            actionability_score=scores.get("next_action_quality", 50),
            metrics=scores,
            evaluator_type=request.evaluator_type,
            evaluation_content=content.model_dump(),
            created_at=datetime.now(timezone.utc),
        )

        # Persist evaluation
        await self._persist_evaluation(response)

        return response

    def _heuristic_evaluation(
        self,
        execution_data: Dict[str, Any],
        grouped_entries: Dict[str, List[Dict]],
    ) -> Dict[str, float]:
        """Calculate heuristic scores."""
        return {
            "reasoning_quality": score_reasoning_quality(grouped_entries),
            "coherence": score_coherence(grouped_entries),
            "contradiction_resolution": score_contradiction_resolution(grouped_entries),
            "risk_detection": score_risk_detection(grouped_entries),
            "next_action_quality": score_next_action_quality(grouped_entries),
            "tool_use_efficiency": score_tool_use_efficiency(execution_data),
            "execution_completion": score_execution_completion(execution_data),
            "output_alignment": score_output_alignment(execution_data, grouped_entries),
        }

    async def _llm_evaluation(
        self,
        execution_data: Dict[str, Any],
        grouped_entries: Dict[str, List[Dict]],
    ) -> Dict[str, float]:
        """Calculate LLM-based scores."""
        # First get heuristic baseline
        heuristic = self._heuristic_evaluation(execution_data, grouped_entries)

        # If LLM available, enhance with structured evaluation
        if self.llm_client:
            try:
                prompt = self._build_evaluation_prompt(execution_data, grouped_entries)
                response = await self.llm_client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=800,
                    temperature=0.2,
                    system="You are an execution evaluator. Return JSON with scores 0-100.",
                    messages=[{"role": "user", "content": prompt}],
                )
                text_blocks = [b.text for b in response.content if getattr(b, "type", None) == "text"]
                text = "".join(text_blocks).strip()

                # Parse LLM response for score adjustments
                # For now, apply heuristic scores with potential LLM adjustments
                # TODO: Implement structured JSON parsing from LLM response
                return heuristic

            except Exception as e:
                logger.warning(f"LLM evaluation failed, using heuristic: {e}")
                return heuristic

        return heuristic

    def _heuristic_content(
        self,
        execution_data: Dict[str, Any],
        grouped_entries: Dict[str, List[Dict]],
    ) -> EvaluationContent:
        """Generate heuristic-based evaluation content."""
        strengths = []
        weaknesses = []
        recommendations = []

        facts = grouped_entries.get("facts", [])
        decisions = grouped_entries.get("decisions", [])
        questions = grouped_entries.get("questions", [])

        # Analyze strengths
        if len(facts) >= 5:
            strengths.append("Strong factual foundation with multiple verified facts")
        if len(decisions) >= 3:
            strengths.append("Good decision-making with clear rationale")
        if all(q.get("status") == "resolved" for q in questions):
            strengths.append("All questions resolved")

        # Analyze weaknesses
        unresolved = [q for q in questions if q.get("status") != "resolved"]
        if len(unresolved) > 3:
            weaknesses.append(f"{len(unresolved)} unresolved questions remain")

        if len(decisions) == 0 and len(facts) > 5:
            weaknesses.append("Facts gathered but no decisions made")

        # Generate recommendations
        if unresolved:
            recommendations.append(f"Address {len(unresolved)} unresolved questions")
        if len(decisions) == 0:
            recommendations.append("Make explicit decisions to move forward")

        return EvaluationContent(
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            detailed_analysis=f"Evaluated {len(facts)} facts, {len(decisions)} decisions, {len(questions)} questions",
            metric_breakdown={
                "entry_counts": {
                    "facts": len(facts),
                    "decisions": len(decisions),
                    "questions": len(questions),
                }
            },
        )

    async def _llm_content(
        self,
        execution_data: Dict[str, Any],
        grouped_entries: Dict[str, List[Dict]],
    ) -> EvaluationContent:
        """Generate LLM-based evaluation content."""
        if not self.llm_client:
            return self._heuristic_content(execution_data, grouped_entries)

        try:
            prompt = self._build_content_prompt(execution_data, grouped_entries)
            response = await self.llm_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=800,
                temperature=0.3,
                system="You analyze execution quality and provide structured feedback.",
                messages=[{"role": "user", "content": prompt}],
            )
            text_blocks = [b.text for b in response.content if getattr(b, "type", None) == "text"]
            text = "".join(text_blocks).strip()

            # Parse LLM response
            # For now return heuristic with LLM text appended
            heuristic = self._heuristic_content(execution_data, grouped_entries)
            heuristic.detailed_analysis = text
            return heuristic

        except Exception as e:
            logger.warning(f"LLM content generation failed: {e}")
            return self._heuristic_content(execution_data, grouped_entries)

    def _build_evaluation_prompt(
        self,
        execution_data: Dict[str, Any],
        grouped_entries: Dict[str, List[Dict]],
    ) -> str:
        """Build prompt for LLM evaluation."""
        facts = grouped_entries.get("facts", [])
        decisions = grouped_entries.get("decisions", [])
        questions = grouped_entries.get("questions", [])

        return f"""Evaluate this workflow execution:

Execution Status: {execution_data.get('status', 'unknown')}
Nodes Completed: {execution_data.get('nodes_completed', 0)}
Nodes Failed: {execution_data.get('nodes_failed', 0)}

Facts ({len(facts)}):
{self._format_entries(facts[:5])}

Decisions ({len(decisions)}):
{self._format_entries(decisions[:5])}

Questions ({len(questions)}):
{self._format_entries(questions[:5])}

Provide scores (0-100) for:
- reasoning_quality
- coherence
- contradiction_resolution
- risk_detection
- next_action_quality
"""

    def _build_content_prompt(
        self,
        execution_data: Dict[str, Any],
        grouped_entries: Dict[str, List[Dict]],
    ) -> str:
        """Build prompt for LLM content generation."""
        return f"""Analyze this execution and provide:

1. Strengths (3-5 bullet points)
2. Weaknesses (3-5 bullet points)
3. Recommendations (3-5 bullet points)

Execution Data:
{execution_data}

Workspace Entries:
{grouped_entries}
"""

    def _format_entries(self, entries: List[Dict]) -> str:
        """Format entries for prompt display."""
        if not entries:
            return "(none)"
        return "\n".join(
            f"- {str(e.get('content', e))[:100]}"
            for e in entries
        )

    async def _persist_evaluation(self, evaluation: ExecutionEvaluationResponse) -> None:
        """Persist evaluation to database."""
        if not self.supabase:
            return

        try:
            self.supabase.table("execution_evaluations").insert({
                "id": evaluation.evaluation_id,
                "execution_id": evaluation.execution_id,
                "workspace_id": evaluation.workspace_id,
                "overall_score": evaluation.overall_score,
                "reasoning_score": evaluation.reasoning_score,
                "outcome_score": evaluation.outcome_score,
                "risk_score": evaluation.risk_score,
                "coherence_score": evaluation.coherence_score,
                "actionability_score": evaluation.actionability_score,
                "evaluator_type": evaluation.evaluator_type.value,
                "evaluation_content": evaluation.evaluation_content,
                "created_at": evaluation.created_at.isoformat(),
            }).execute()

            logger.info(f"Persisted evaluation {evaluation.evaluation_id}")

        except Exception as e:
            logger.warning(f"Failed to persist evaluation: {e}")
