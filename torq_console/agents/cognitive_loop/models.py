"""
Data models for the TORQ Agent Cognitive Loop System.

Defines the core data structures used throughout the cognitive reasoning cycle.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union
from uuid import uuid4


class CognitiveLoopStatus(str, Enum):
    """Status of the cognitive loop execution."""
    IDLE = "idle"
    REASONING = "reasoning"
    RETRIEVING = "retrieving"
    PLANNING = "planning"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    LEARNING = "learning"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class IntentType(str, Enum):
    """Types of user intents."""
    QUERY = "query"
    TASK = "task"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    RESEARCH = "research"
    UNKNOWN = "unknown"


class StepStatus(str, Enum):
    """Status of an execution step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ToolCategory(str, Enum):
    """Categories of tools available for execution."""
    WEB_SEARCH = "web_search"
    DATABASE = "database"
    FILE_OPERATIONS = "file_operations"
    CODE_EXECUTION = "code_execution"
    API_CALL = "api_call"
    DOCUMENT_GENERATION = "document_generation"
    DATA_ANALYSIS = "data_analysis"
    COMMUNICATION = "communication"
    CUSTOM = "custom"


@dataclass
class CognitiveLoopConfig:
    """Configuration for the cognitive loop system."""

    # Performance targets
    max_loop_latency_seconds: float = 2.0
    min_tool_success_rate: float = 0.95
    min_evaluation_confidence: float = 0.80

    # Retry and failure handling
    max_retries: int = 3
    retry_delay_seconds: float = 0.5
    enable_fallback: bool = True

    # Knowledge retrieval
    knowledge_enabled: bool = True
    max_knowledge_contexts: int = 5
    knowledge_similarity_threshold: float = 0.75

    # Planning
    max_plan_steps: int = 10
    enable_parallel_execution: bool = True

    # Tool execution
    tool_timeout_seconds: float = 30.0
    enable_tool_caching: bool = True

    # Learning
    learning_enabled: bool = True
    min_confidence_for_learning: float = 0.70

    # Telemetry
    telemetry_enabled: bool = True
    emit_detailed_spans: bool = True

    # Storage
    learning_storage_path: str = ".torq/cognitive_learning"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CognitiveLoopConfig":
        """Create config from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class KnowledgeContext:
    """Retrieved knowledge context from the Knowledge Plane."""
    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    source: str = ""
    similarity: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    retrieved_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ReasoningPlan:
    """Output of the reasoning phase."""
    intent: IntentType = IntentType.UNKNOWN
    intent_confidence: float = 0.0
    reasoning: str = ""
    key_entities: List[str] = field(default_factory=list)
    key_concepts: List[str] = field(default_factory=list)
    requires_tools: bool = False
    suggested_tools: List[str] = field(default_factory=list)
    complexity_estimate: float = 0.5  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionStep:
    """A single step in the execution plan."""
    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    tool_name: str = ""
    tool_category: ToolCategory = ToolCategory.CUSTOM
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Step IDs
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_order: int = 0
    estimated_duration_seconds: float = 1.0


@dataclass
class ExecutionPlan:
    """Output of the planning phase."""
    goal: str = ""
    steps: List[ExecutionStep] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)
    estimated_duration_seconds: float = 0.0
    requires_parallel_execution: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_ready_steps(self) -> List[ExecutionStep]:
        """Get steps that are ready to execute (dependencies satisfied)."""
        completed_step_ids = {s.id for s in self.steps if s.status == StepStatus.COMPLETED}
        return [
            s for s in self.steps
            if s.status == StepStatus.PENDING and
            all(dep in completed_step_ids for dep in s.dependencies)
        ]

    def get_step_by_id(self, step_id: str) -> Optional[ExecutionStep]:
        """Get a step by its ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def is_complete(self) -> bool:
        """Check if all steps are complete."""
        return all(s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED) for s in self.steps)

    def has_failed_steps(self) -> bool:
        """Check if any steps have failed."""
        return any(s.status == StepStatus.FAILED for s in self.steps)


@dataclass
class ToolCallResult:
    """Result of a single tool execution."""
    tool_name: str
    success: bool = False
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Output of the execution phase."""
    success: bool = False
    tool_results: List[ToolCallResult] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    total_execution_time_seconds: float = 0.0
    partial_results: bool = False
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Output of the evaluation phase."""
    task_completed: bool
    confidence_score: float  # 0.0 to 1.0
    data_integrity_score: float  # 0.0 to 1.0
    quality_score: float  # 0.0 to 1.0
    reasoning: str = ""
    should_retry: bool = False
    retry_reason: str = ""
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_acceptable(self) -> bool:
        """Check if the result meets minimum quality thresholds."""
        return (
            self.task_completed and
            self.confidence_score >= 0.70 and
            self.data_integrity_score >= 0.70
        )


@dataclass
class LearningEvent:
    """Event to be stored in the learning system."""
    id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = "torq_agent"
    query: str = ""
    intent: IntentType = IntentType.UNKNOWN
    reasoning_plan: ReasoningPlan = field(default_factory=ReasoningPlan)
    execution_plan: ExecutionPlan = field(default_factory=ExecutionPlan)
    tools_used: List[str] = field(default_factory=list)
    execution_result: Optional[ExecutionResult] = None
    evaluation_result: Optional[EvaluationResult] = None
    success: bool = True
    success_score: float = 0.0  # 0.0 to 1.0
    execution_time_seconds: float = 0.0
    retry_count: int = 0
    learned_insights: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "query": self.query,
            "intent": self.intent.value,
            "success": self.success,
            "success_score": self.success_score,
            "execution_time_seconds": self.execution_time_seconds,
            "retry_count": self.retry_count,
            "tools_used": self.tools_used,
            "learned_insights": self.learned_insights,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class CognitiveLoopResult:
    """Final result of a cognitive loop execution."""
    success: bool = False
    query: str = ""
    status: CognitiveLoopStatus = CognitiveLoopStatus.COMPLETED
    reasoning_plan: Optional[ReasoningPlan] = None
    knowledge_contexts: List[KnowledgeContext] = field(default_factory=list)
    execution_plan: Optional[ExecutionPlan] = None
    execution_result: Optional[ExecutionResult] = None
    evaluation_result: Optional[EvaluationResult] = None
    learning_event: Optional[LearningEvent] = None
    total_time_seconds: float = 0.0
    phase_times_seconds: Dict[str, float] = field(default_factory=dict)
    retry_count: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def confidence(self) -> float:
        """Get the overall confidence score."""
        if self.evaluation_result:
            return self.evaluation_result.confidence_score
        return 0.0

    def to_summary(self) -> str:
        """Get a human-readable summary of the result."""
        if self.error:
            return f"Failed: {self.error}"

        parts = [f"Status: {self.status.value}"]

        if self.reasoning_plan:
            parts.append(f"Intent: {self.reasoning_plan.intent.value}")

        if self.evaluation_result:
            parts.append(f"Confidence: {self.evaluation_result.confidence_score:.2f}")

        parts.append(f"Time: {self.total_time_seconds:.2f}s")

        if self.retry_count > 0:
            parts.append(f"Retries: {self.retry_count}")

        return " | ".join(parts)


# Type variables for generic tool result handling
T = TypeVar('T')


@dataclass
class ToolSpec:
    """Specification of an available tool."""
    name: str
    description: str
    category: ToolCategory
    parameters: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable] = None
    async_handler: Optional[Callable] = None
    requires_auth: bool = False
    timeout_seconds: float = 30.0


@dataclass
class SessionContext:
    """Context maintained across cognitive loop iterations."""
    session_id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = "torq_agent"
    user_id: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    working_memory: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def update_conversation(self, role: str, content: str, metadata: Dict[str, Any] | None = None):
        """Add a message to the conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            **(metadata or {})
        })
        self.last_updated = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/transmission."""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "working_memory": self.working_memory,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }
