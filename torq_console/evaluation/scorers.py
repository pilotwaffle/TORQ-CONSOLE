"""
Evaluation Engine - Heuristic Scorers

Provides rule-based scoring for execution evaluation.
Used as fallback when LLM evaluation is unavailable.
"""

from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime


def score_reasoning_quality(grouped_entries: Dict[str, List[Dict]]) -> float:
    """
    Score the quality of reasoning based on workspace entries.

    Factors:
    - Number of facts (more facts = better)
    - Number of decisions (decisions show progress)
    - Fact to decision ratio
    - Reasoning depth (hypotheses, questions)
    """
    facts = grouped_entries.get("facts", [])
    hypotheses = grouped_entries.get("hypotheses", [])
    questions = grouped_entries.get("questions", [])
    decisions = grouped_entries.get("decisions", [])

    score = 50.0  # Base score

    # More facts = better reasoning
    score += min(len(facts) * 5, 20)

    # Decisions show progress
    score += min(len(decisions) * 5, 15)

    # Hypotheses show depth
    score += min(len(hypotheses) * 3, 10)

    # Too many unresolved questions is bad
    unresolved = [q for q in questions if q.get("status") != "resolved"]
    score -= min(len(unresolved) * 2, 10)

    return max(0, min(100, score))


def score_coherence(grouped_entries: Dict[str, List[Dict]]) -> float:
    """
    Score coherence based on contradictions and decision alignment.

    Factors:
    - Number of contradictions (fewer = better)
    - Consistency in reasoning
    - Decision alignment
    """
    facts = grouped_entries.get("facts", [])
    decisions = grouped_entries.get("decisions", [])

    score = 70.0  # Start with assumption of coherence

    # Check for contradiction indicators in facts
    fact_texts = [str(f.get("content", {})).lower() for f in facts]
    contradiction_indicators = 0
    for text in fact_texts:
        if "however" in text or "but" in text or "although" in text:
            contradiction_indicators += 1
        if "not" in text and "is" in text:
            contradiction_indicators += 1

    score -= min(contradiction_indicators * 5, 30)

    return max(0, min(100, score))


def score_contradiction_resolution(grouped_entries: Dict[str, List[Dict]]) -> float:
    """
    Score how well contradictions were resolved.

    Factors:
    - Ratio of resolved questions
    - Number of contradictions vs decisions addressing them
    """
    questions = grouped_entries.get("questions", [])
    decisions = grouped_entries.get("decisions", [])

    total_questions = len(questions)
    if total_questions == 0:
        return 50.0  # Neutral score if no questions

    resolved_count = sum(1 for q in questions if q.get("status") == "resolved")
    resolution_rate = (resolved_count / total_questions) * 100

    return resolution_rate


def score_risk_detection(grouped_entries: Dict[str, List[Dict]]) -> float:
    """
    Score risk detection capability.

    Factors:
    - Number of questions (shows awareness)
    - Diversity of entry types (shows multi-dimensional thinking)
    - Explicit risk mentions
    """
    questions = grouped_entries.get("questions", [])
    hypotheses = grouped_entries.get("hypotheses", [])
    decisions = grouped_entries.get("decisions", [])

    score = 50.0

    # Questions indicate risk awareness
    score += min(len(questions) * 3, 20)

    # Hypotheses show consideration of alternatives
    score += min(len(hypotheses) * 2, 15)

    # Decisions addressing risks
    risk_decisions = sum(
        1 for d in decisions
        if "risk" in str(d.get("content", {})).lower()
    )
    score += min(risk_decisions * 5, 15)

    return max(0, min(100, score))


def score_next_action_quality(grouped_entries: Dict[str, List[Dict]]) -> float:
    """
    Score the quality of next actions/recommendations.

    Factors:
    - Specificity of next actions
    - Actionability
    - Prioritization
    """
    decisions = grouped_entries.get("decisions", [])
    notes = grouped_entries.get("notes", [])

    score = 50.0

    # Check for actionable decisions
    actionable_count = 0
    for decision in decisions:
        content = str(decision.get("content", {})).lower()
        if any(word in content for word in ["will", "should", "must", "plan"]):
            actionable_count += 1

    score += min(actionable_count * 10, 40)

    # Notes with categories show organization
    categorized_notes = sum(
        1 for n in notes
        if n.get("category") and n.get("category") != "general"
    )
    score += min(categorized_notes * 5, 10)

    return max(0, min(100, score))


def score_tool_use_efficiency(execution_data: Dict[str, Any]) -> float:
    """
    Score tool use efficiency during execution.

    Factors:
    - Node completion rate
    - Tool failure rate
    - Execution time
    """
    score = 70.0  # Start with assumption of efficiency

    # Node completion
    nodes_completed = execution_data.get("nodes_completed", 0)
    nodes_total = execution_data.get("nodes_total", nodes_completed + nodes_failed)
    nodes_failed = execution_data.get("nodes_failed", 0)

    if nodes_total > 0:
        completion_rate = nodes_completed / nodes_total
        score += completion_rate * 20
        score -= (nodes_failed / nodes_total) * 15

    # Tool failures
    tool_failures = execution_data.get("tool_failures", 0)
    score -= min(tool_failures * 10, 50)

    return max(0, min(100, score))


def score_execution_completion(execution_data: Dict[str, Any]) -> float:
    """
    Score execution completion.

    Factors:
    - Did execution finish successfully?
    - Output quality
    - Error handling
    """
    status = execution_data.get("status", "unknown")

    if status == "completed":
        return 100.0
    elif status == "failed":
        return 20.0
    elif status == "cancelled":
        return 40.0
    else:
        return 50.0


def score_output_alignment(
    execution_data: Dict[str, Any],
    grouped_entries: Dict[str, List[Dict]]
) -> float:
    """
    Score how well output aligns with objectives.

    Factors:
    - Output presence
    - Goal achievement indicators
    """
    output = execution_data.get("output", {})
    decisions = grouped_entries.get("decisions", [])

    score = 50.0

    # Has output
    if output:
        score += 20

    # Output size indicates substantial work
    if isinstance(output, dict):
        output_size = len(str(output))
        score += min(output_size / 1000, 20)

    # Decision-driven output
    if decisions and output:
        score += 10

    return max(0, min(100, score))


def calculate_overall_score(scores: Dict[str, float]) -> float:
    """Calculate overall score from individual metrics."""
    weights = {
        "reasoning_quality": 0.20,
        "coherence": 0.15,
        "contradiction_resolution": 0.10,
        "risk_detection": 0.10,
        "next_action_quality": 0.15,
        "tool_use_efficiency": 0.15,
        "execution_completion": 0.10,
        "output_alignment": 0.05,
    }

    overall = sum(scores.get(metric, 50) * weight for metric, weight in weights.items())
    return round(overall, 2)
