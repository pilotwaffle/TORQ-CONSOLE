"""
Core state management for TORQ Prince Flowers agent.

This module defines the core data structures and enums that represent
the agent's state, reasoning modes, and action tracking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


class ReasoningMode(Enum):
    """Different reasoning modes available to the agent."""
    DIRECT = "direct"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    COMPOSITION = "composition"
    META_PLANNING = "meta_planning"


@dataclass
class AgenticAction:
    """Represents a single action taken by the agent."""
    action_type: str
    parameters: Dict[str, Any]
    timestamp: datetime
    result: Optional[Dict[str, Any]] = None
    success: bool = False
    execution_time: float = 0.0
    tool_used: Optional[str] = None


@dataclass
class ReasoningTrajectory:
    """Tracks the reasoning trajectory for learning and analysis."""
    trajectory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    mode: ReasoningMode = ReasoningMode.DIRECT
    actions: List[AgenticAction] = field(default_factory=list)
    success: bool = False
    total_time: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    intermediate_results: List[Dict[str, Any]] = field(default_factory=list)
    final_result: Optional[str] = None
    confidence_score: float = 0.0
    self_corrections: int = 0

    def add_action(self, action: AgenticAction):
        """Add an action to the trajectory."""
        self.actions.append(action)

    def mark_complete(self, success: bool, final_result: str = None):
        """Mark the trajectory as complete."""
        self.success = success
        self.end_time = datetime.now()
        self.total_time = (self.end_time - self.start_time).total_seconds()
        if final_result:
            self.final_result = final_result

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of the trajectory execution."""
        return {
            "trajectory_id": self.trajectory_id,
            "query": self.query,
            "mode": self.mode.value,
            "total_actions": len(self.actions),
            "successful_actions": sum(1 for a in self.actions if a.success),
            "success": self.success,
            "total_time": self.total_time,
            "self_corrections": self.self_corrections,
            "confidence_score": self.confidence_score
        }


@dataclass
class TORQAgentResult:
    """Standard result format for TORQ agent operations."""
    success: bool
    response: str
    trajectory: Optional[ReasoningTrajectory] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tools_used: List[str] = field(default_factory=list)
    error: Optional[str] = None
    confidence: float = 0.0
    execution_time: float = 0.0
    reasoning_summary: Optional[str] = None

    def add_tool_used(self, tool_name: str):
        """Add a tool to the list of tools used."""
        if tool_name not in self.tools_used:
            self.tools_used.append(tool_name)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "success": self.success,
            "response": self.response,
            "trajectory_id": self.trajectory.trajectory_id if self.trajectory else None,
            "metadata": self.metadata,
            "tools_used": self.tools_used,
            "error": self.error,
            "confidence": self.confidence,
            "execution_time": self.execution_time,
            "reasoning_summary": self.reasoning_summary,
            "trajectory_summary": self.trajectory.get_execution_summary() if self.trajectory else None
        }