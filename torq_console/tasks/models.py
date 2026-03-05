"""
Data models for Task Graph Engine.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class GraphStatus(str, Enum):
    """Status of a task graph."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class NodeStatus(str, Enum):
    """Status of a task node."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class NodeType(str, Enum):
    """Type of task node."""
    AGENT = "agent"
    TOOL = "tool"
    API_CALL = "api_call"
    ANALYSIS = "analysis"
    CONDITION = "condition"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


class ExecutionStatus(str, Enum):
    """Status of a graph execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TriggerType(str, Enum):
    """Type of execution trigger."""
    MANUAL = "manual"
    WEBHOOK = "webhook"
    TIMER = "timer"
    EVENT = "event"


class FailureStrategy(str, Enum):
    """Strategy for handling node failures."""
    RETRY = "retry"
    SKIP = "skip"
    REROUTE = "reroute"
    FAIL = "fail"


# ============================================================================
# Request/Response Models
# ============================================================================

class RetryPolicy(BaseModel):
    """Retry configuration for a node."""
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_ms: int = Field(default=1000, ge=0, le=60000)
    backoff_multiplier: float = Field(default=2.0, ge=1.0, le=10.0)
    failure_strategy: FailureStrategy = Field(default=FailureStrategy.RETRY)


class NodeDefinition(BaseModel):
    """Definition of a task node."""
    node_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    node_type: NodeType
    agent_id: Optional[str] = None
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    retry_policy: Optional[RetryPolicy] = None
    timeout_seconds: int = Field(default=300, ge=10, le=3600)
    depends_on: List[UUID] = Field(default_factory=list)
    position_x: int = 0
    position_y: int = 0


class EdgeDefinition(BaseModel):
    """Definition of an edge between nodes."""
    source_node_id: UUID
    target_node_id: UUID
    condition: Optional[Dict[str, Any]] = None


class TaskGraphCreate(BaseModel):
    """Request to create a task graph."""
    name: str
    description: Optional[str] = None
    nodes: List[NodeDefinition]
    edges: List[EdgeDefinition]
    config: Dict[str, Any] = Field(default_factory=dict)


class TaskGraphResponse(BaseModel):
    """Response with task graph details."""
    graph_id: UUID
    name: str
    description: Optional[str]
    status: GraphStatus
    created_at: datetime
    updated_at: datetime
    nodes: List[NodeDefinition]
    edges: List[EdgeDefinition]
    config: Dict[str, Any]


class ExecutionCreate(BaseModel):
    """Request to execute a task graph."""
    trigger_type: TriggerType = TriggerType.MANUAL
    trigger_source: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResponse(BaseModel):
    """Response with execution details."""
    execution_id: UUID
    graph_id: UUID
    status: ExecutionStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    output: Dict[str, Any]
    error_message: Optional[str]
    total_duration_ms: Optional[int]
    nodes_completed: int
    nodes_failed: int
    trace_id: Optional[str]


class NodeResult(BaseModel):
    """Result of a single node execution."""
    result_id: UUID
    execution_id: UUID
    node_id: UUID
    status: NodeStatus
    output: Dict[str, Any]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    retry_count: int


# ============================================================================
# Database Models (for internal use)
# ============================================================================

class TaskGraphNode(BaseModel):
    """A node in the task graph DAG."""
    node_id: UUID = Field(default_factory=uuid4)
    name: str
    node_type: NodeType
    agent_id: Optional[str] = None
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    timeout_seconds: int = 300
    depends_on: List[UUID] = Field(default_factory=list)
    position: tuple[int, int] = (0, 0)


class TaskGraphEdge(BaseModel):
    """An edge connecting two nodes."""
    source: UUID
    target: UUID
    condition: Optional[Dict[str, Any]] = None
