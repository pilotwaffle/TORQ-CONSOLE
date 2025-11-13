"""
Enhanced Handoff Context Preservation System.

Fixes information loss during subsystem handoffs by:
1. Preserving full context objects (not just truncated text)
2. Maintaining structured metadata throughout the pipeline
3. Tracking information flow across subsystem boundaries

Addresses the 70% information loss issue in:
- Memory → Planning handoffs
- Debate → Evaluation handoffs
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class HandoffType(Enum):
    """Types of subsystem handoffs."""
    MEMORY_TO_PLANNING = "memory_to_planning"
    PLANNING_TO_DEBATE = "planning_to_debate"
    DEBATE_TO_EVALUATION = "debate_to_evaluation"
    EVALUATION_TO_MEMORY = "evaluation_to_memory"


@dataclass
class MemoryContext:
    """
    Enhanced memory context with full preservation.

    Fixes the truncation issue where only 200 chars were preserved.
    """
    memories: List[Dict[str, Any]] = field(default_factory=list)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    full_content: List[str] = field(default_factory=list)  # Full text, no truncation
    metadata: Dict[str, Any] = field(default_factory=dict)
    similarity_scores: List[float] = field(default_factory=list)
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def get_full_context_text(self) -> str:
        """Get full context text without truncation."""
        context_parts = []

        if self.memories:
            context_parts.append("## Relevant Memories:")
            for i, mem in enumerate(self.memories):
                similarity = self.similarity_scores[i] if i < len(self.similarity_scores) else 0
                # Use full content, not truncated
                content = self.full_content[i] if i < len(self.full_content) else mem.get('content', '')
                context_parts.append(f"[{similarity*100:.1f}% match] {content}")

        if self.patterns:
            context_parts.append("\n## Learned Patterns:")
            for pattern in self.patterns:
                pattern_type = pattern.get('pattern_type', 'unknown')
                success_rate = pattern.get('success_rate', 0) * 100
                # Include full pattern details
                pattern_content = pattern.get('pattern_content', {})
                context_parts.append(f"- {pattern_type} (success: {success_rate:.0f}%): {pattern_content}")

        return "\n".join(context_parts)

    def get_structured_context(self) -> Dict[str, Any]:
        """Get context as structured data for processing."""
        return {
            "memories": self.memories,
            "patterns": self.patterns,
            "full_content": self.full_content,
            "metadata": self.metadata,
            "similarity_scores": self.similarity_scores
        }


@dataclass
class DebateContext:
    """
    Enhanced debate context preserving all nuance.

    Fixes the information loss where only final synthesis was preserved.
    """
    query: str
    all_rounds: List[Any] = field(default_factory=list)  # All DebateRound objects
    all_arguments: List[Any] = field(default_factory=list)  # All DebateArgument objects
    agent_contributions: Dict[str, List[str]] = field(default_factory=dict)
    final_synthesis: str = ""
    confidence: float = 0.8
    consensus_score: float = 0.0
    debate_metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_full_debate_summary(self) -> str:
        """Get comprehensive debate summary with all perspectives."""
        summary_parts = [
            f"# Debate Summary for: {self.query}",
            f"Rounds: {len(self.all_rounds)}, Arguments: {len(self.all_arguments)}",
            f"Consensus: {self.consensus_score:.2f}, Confidence: {self.confidence:.2f}",
            ""
        ]

        # Include contributions from each agent role
        if self.agent_contributions:
            summary_parts.append("## Agent Contributions:")
            for role, contributions in self.agent_contributions.items():
                summary_parts.append(f"\n### {role}:")
                for contrib in contributions:
                    summary_parts.append(f"- {contrib}")

        # Include final synthesis
        summary_parts.append("\n## Final Synthesis:")
        summary_parts.append(self.final_synthesis)

        return "\n".join(summary_parts)

    def get_structured_debate_context(self) -> Dict[str, Any]:
        """Get debate context as structured data."""
        return {
            "query": self.query,
            "rounds": [
                {
                    "round_number": r.round_number,
                    "arguments_count": len(r.arguments),
                    "consensus_score": r.consensus_score,
                    "arguments": [
                        {
                            "role": arg.agent_role.value,
                            "content": arg.content,
                            "confidence": arg.confidence,
                            "evidence": arg.supporting_evidence
                        }
                        for arg in r.arguments
                    ]
                }
                for r in self.all_rounds
            ],
            "agent_contributions": self.agent_contributions,
            "final_synthesis": self.final_synthesis,
            "confidence": self.confidence,
            "consensus_score": self.consensus_score,
            "metadata": self.debate_metadata
        }


@dataclass
class PlanningContext:
    """Enhanced planning context with full upstream information."""
    query: str
    memory_context: Optional[MemoryContext] = None
    plan_steps: List[Dict[str, Any]] = field(default_factory=list)
    complexity_analysis: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_full_planning_context(self) -> Dict[str, Any]:
        """Get complete planning context including memory."""
        context = {
            "query": self.query,
            "plan_steps": self.plan_steps,
            "complexity_analysis": self.complexity_analysis,
            "metadata": self.metadata
        }

        # Include full memory context if available
        if self.memory_context:
            context["memory_context"] = self.memory_context.get_structured_context()

        return context


@dataclass
class EvaluationContext:
    """Enhanced evaluation context preserving all upstream information."""
    query: str
    response: str
    memory_context: Optional[MemoryContext] = None
    planning_context: Optional[PlanningContext] = None
    debate_context: Optional[DebateContext] = None
    trajectory: Optional[Any] = None  # ResponseTrajectory
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_full_evaluation_context(self) -> Dict[str, Any]:
        """Get complete evaluation context from all subsystems."""
        context = {
            "query": self.query,
            "response": self.response,
            "metadata": self.metadata
        }

        # Include full memory context
        if self.memory_context:
            context["memory_context"] = self.memory_context.get_structured_context()

        # Include full planning context
        if self.planning_context:
            context["planning_context"] = self.planning_context.get_full_planning_context()

        # Include full debate context (ALL the nuance!)
        if self.debate_context:
            context["debate_context"] = self.debate_context.get_structured_debate_context()
            # Also include the summary for easy reading
            context["debate_summary"] = self.debate_context.get_full_debate_summary()

        # Include trajectory
        if self.trajectory:
            context["trajectory"] = {
                "steps": self.trajectory.steps,
                "intermediate_outputs": self.trajectory.intermediate_outputs,
                "decision_points": self.trajectory.decision_points,
                "total_duration": self.trajectory.total_duration
            }

        return context


class HandoffPreservationTracker:
    """
    Tracks information preservation across handoffs.

    Measures how much information is maintained when data flows
    between subsystems.
    """

    def __init__(self):
        self.handoff_records: List[Dict[str, Any]] = []

    def record_handoff(
        self,
        handoff_type: HandoffType,
        input_size: int,
        output_size: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a handoff event for tracking."""
        preservation_ratio = output_size / input_size if input_size > 0 else 0.0

        self.handoff_records.append({
            "handoff_type": handoff_type.value,
            "input_size": input_size,
            "output_size": output_size,
            "preservation_ratio": preservation_ratio,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        })

    def get_preservation_stats(self) -> Dict[str, Any]:
        """Get statistics on information preservation."""
        if not self.handoff_records:
            return {"total_handoffs": 0, "average_preservation": 0.0}

        by_type = {}
        for record in self.handoff_records:
            htype = record["handoff_type"]
            if htype not in by_type:
                by_type[htype] = []
            by_type[htype].append(record["preservation_ratio"])

        stats = {
            "total_handoffs": len(self.handoff_records),
            "by_type": {}
        }

        for htype, ratios in by_type.items():
            stats["by_type"][htype] = {
                "count": len(ratios),
                "average_preservation": sum(ratios) / len(ratios),
                "min_preservation": min(ratios),
                "max_preservation": max(ratios)
            }

        all_ratios = [r["preservation_ratio"] for r in self.handoff_records]
        stats["average_preservation"] = sum(all_ratios) / len(all_ratios)

        return stats


# Global tracker instance
_handoff_tracker: Optional[HandoffPreservationTracker] = None


def get_handoff_tracker() -> HandoffPreservationTracker:
    """Get or create global handoff preservation tracker."""
    global _handoff_tracker
    if _handoff_tracker is None:
        _handoff_tracker = HandoffPreservationTracker()
    return _handoff_tracker
