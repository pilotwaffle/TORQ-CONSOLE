"""
Evaluation Engine - Models for Phase 4F

Defines schemas for execution evaluation and scoring.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluatorType(str, Enum):
    """Type of evaluation method."""
    HEURISTIC = "heuristic"
    LLM = "llm"
    HYBRID = "hybrid"


class EvaluationMetric(str, Enum):
    """Metrics for execution evaluation."""
    REASONING_QUALITY = "reasoning_quality"
    COHERENCE = "coherence"
    CONTRADICTION_RESOLUTION = "contradiction_resolution"
    RISK_DETECTION = "risk_detection"
    NEXT_ACTION_QUALITY = "next_action_quality"
    TOOL_USE_EFFICIENCY = "tool_use_efficiency"
    EXECUTION_COMPLETION = "execution_completion"
    OUTPUT_ALIGNMENT = "output_alignment"


class ExecutionEvaluationCreate(BaseModel):
    """Request to create an execution evaluation."""
    execution_id: str = Field(..., description="Execution ID being evaluated")
    workspace_id: Optional[str] = Field(None, description="Associated workspace ID")
    evaluator_type: EvaluatorType = Field(default=EvaluatorType.HYBRID)
    evaluation_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for evaluation"
    )


class ExecutionEvaluationResponse(BaseModel):
    """Response containing evaluation results."""
    evaluation_id: str
    execution_id: str
    workspace_id: Optional[str]
    overall_score: float  # 0-100
    reasoning_score: float
    outcome_score: float
    risk_score: float
    coherence_score: float
    actionability_score: float
    metrics: Dict[str, float]
    evaluator_type: EvaluatorType
    evaluation_content: Dict[str, Any]
    created_at: datetime


class EvaluationScores(BaseModel):
    """Individual evaluation scores."""
    reasoning_quality: float = Field(default=50.0, ge=0, le=100)
    coherence: float = Field(default=50.0, ge=0, le=100)
    contradiction_resolution: float = Field(default=50.0, ge=0, le=100)
    risk_detection: float = Field(default=50.0, ge=0, le=100)
    next_action_quality: float = Field(default=50.0, ge=0, le=100)
    tool_use_efficiency: float = Field(default=50.0, ge=0, le=100)
    execution_completion: float = Field(default=50.0, ge=0, le=100)
    output_alignment: float = Field(default=50.0, ge=0, le=100)


class EvaluationContent(BaseModel):
    """Structured evaluation content."""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    detailed_analysis: str = ""
    metric_breakdown: Dict[str, Any] = Field(default_factory=dict)
