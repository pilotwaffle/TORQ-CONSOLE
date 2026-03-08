"""
Mission Graph Models

Phase 5: Mission Graph Planning

Turns TORQ from a system that runs agents into a system that structures
complex missions the way a strong consulting team would.

A mission graph contains:
- Objective nodes (top-level mission)
- Task nodes (concrete reasoning/execution)
- Decision nodes (branch points)
- Evidence nodes (facts/data/artifacts)
- Deliverable nodes (expected outputs)
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Mission & Graph Types
# ============================================================================

class MissionStatus(str, Enum):
    """Status of a mission."""
    DRAFT = "draft"
    PLANNED = "planned"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MissionType(str, Enum):
    """High-level mission categories."""
    ANALYSIS = "analysis"  # Research, investigation, assessment
    PLANNING = "planning"  # Strategy, roadmap, execution plan
    EVALUATION = "evaluation"  # Risk assessment, audit, review
    DESIGN = "design"  # Architecture, system, process design
    TRANSFORMATION = "transformation"  # Change management, migration


class GraphStatus(str, Enum):
    """Status of a mission graph."""
    DRAFT = "draft"
    VALIDATING = "validating"
    VALIDATED = "validated"
    ACTIVE = "active"
    ARCHIVED = "archived"


# ============================================================================
# Node Types
# ============================================================================

class NodeType(str, Enum):
    """Types of nodes in a mission graph."""
    OBJECTIVE = "objective"  # Top-level mission or sub-objective
    TASK = "task"  # Concrete reasoning or execution task
    DECISION = "decision"  # Branch point requiring choice
    EVIDENCE = "evidence"  # Required facts, data, or artifacts
    DELIVERABLE = "deliverable"  # Expected output


class NodeStatus(str, Enum):
    """Status of a mission node."""
    PENDING = "pending"  # Not yet ready to run
    READY = "ready"  # Ready to be dispatched
    RUNNING = "running"  # Currently executing
    BLOCKED = "blocked"  # Waiting for dependency or condition
    COMPLETED = "completed"  # Finished successfully
    FAILED = "failed"  # Failed during execution
    SKIPPED = "skipped"  # Not executed (e.g., branch not taken)


class NodePriority(str, Enum):
    """Priority level for task nodes."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# Edge Types
# ============================================================================

class EdgeType(str, Enum):
    """Types of relationships between nodes."""
    DEPENDS_ON = "depends_on"  # Target waits for source completion
    INFORMS = "informs"  # Source improves target but not required
    BLOCKS = "blocks"  # Source prevents target until resolved
    BRANCHES_TO = "branches_to"  # Decision outcome activates branch
    PRODUCES = "produces"  # Task generates evidence/deliverable


# ============================================================================
# Reasoning Strategies
# ============================================================================

class ReasoningStrategy(str, Enum):
    """Structured cognition patterns for task execution."""
    DECOMPOSITION_FIRST = "decomposition_first"  # Break down problem first
    RISK_FIRST = "risk_first"  # Identify risks early
    EVIDENCE_WEIGHTED = "evidence_weighted"  # Weight decisions by evidence strength
    CHECKLIST_DRIVEN = "checklist_driven"  # Follow explicit checklist
    CONTRADICTION_FIRST = "contradiction_first"  # Surface conflicts early
    HYPOTHESIS_DRIVEN = "hypothesis_driven"  # Test hypotheses sequentially


# ============================================================================
# Agent Types
# ============================================================================

class AgentType(str, Enum):
    """Types of agents in hierarchical teams."""
    STRATEGIC_PLANNER = "strategic_planner"  # Builds/monitors graph
    DOMAIN_LEAD = "domain_lead"  # Owns workstream (finance, ops, market, compliance)
    SPECIALIST = "specialist"  # Executes specific tasks
    SYNTHESIZER = "synthesizer"  # Combines outputs into deliverables
    RISK_QA = "risk_qa"  # Reviews contradictions, risks, quality
    EXECUTIVE = "executive"  # Final review and approval


# ============================================================================
# Core Models
# ============================================================================

class Mission(BaseModel):
    """Top-level mission record."""
    id: str
    title: str
    mission_type: MissionType
    objective: str
    status: MissionStatus = MissionStatus.DRAFT

    # Scope and context
    scope: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)

    # Strategic memory integration
    injected_memory_ids: List[str] = Field(default_factory=list)
    reasoning_strategy: Optional[ReasoningStrategy] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.now)

    # Results
    overall_score: Optional[float] = None
    deliverables: List[str] = Field(default_factory=list)


class MissionNode(BaseModel):
    """A node in the mission graph."""
    id: str
    graph_id: str
    node_type: NodeType
    title: str
    description: Optional[str] = None

    # Execution
    status: NodeStatus = NodeStatus.PENDING
    priority: NodePriority = NodePriority.MEDIUM
    agent_type: Optional[AgentType] = None
    reasoning_strategy: Optional[ReasoningStrategy] = None

    # Requirements
    input_requirements: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)

    # Dependencies
    # Database alias: depends_on field maps to depends_on_nodes
    depends_on_nodes: List[str] = Field(default_factory=list, alias="depends_on")
    blocked_by_nodes: List[str] = Field(default_factory=list, alias="blocks")
    informs_nodes: List[str] = Field(default_factory=list)

    # Allow population from database by alias
    class Config:
        populate_by_name = True

    # Decision-specific
    decision_condition: Optional[Dict[str, Any]] = None
    decision_outcome: Optional[str] = None  # Which branch was taken

    # Evidence-specific
    evidence_type: Optional[str] = None
    required_by_nodes: List[str] = Field(default_factory=list)

    # Deliverable-specific
    deliverable_type: Optional[str] = None
    format_spec: Optional[Dict[str, Any]] = None

    # Workspace linkage
    workspace_id: Optional[str] = None

    # Strategic memory
    injected_memory_ids: List[str] = Field(default_factory=list)

    # Timing
    estimated_duration_seconds: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Results
    output_count: int = 0
    error_message: Optional[str] = None


class MissionEdge(BaseModel):
    """Relationship between two nodes in the graph."""
    id: str
    graph_id: str
    source_node_id: str
    target_node_id: str
    edge_type: EdgeType

    # For conditional edges
    condition: Optional[Dict[str, Any]] = None

    # For tracking
    satisfied: bool = False
    satisfied_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.now)


class MissionGraph(BaseModel):
    """A mission graph with nodes and edges."""
    id: str
    mission_id: str
    version: str = "1.0"
    status: GraphStatus = GraphStatus.DRAFT

    # Graph structure
    nodes: List[MissionNode] = Field(default_factory=list)
    edges: List[MissionEdge] = Field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    graph_stats: Dict[str, Any] = Field(default_factory=dict)

    # Validation
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class MissionNodeOutput(BaseModel):
    """Output or artifact from a node execution."""
    id: str
    node_id: str
    workspace_id: Optional[str] = None
    output_type: str  # "reasoning", "evidence", "deliverable", "decision"
    content: Dict[str, Any]

    # Quality metrics
    confidence_score: Optional[float] = None
    contradiction_count: Optional[int] = None

    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Decision Gate Models
# ============================================================================

class DecisionGateType(str, Enum):
    """Types of decision gates."""
    CONFIDENCE_THRESHOLD = "confidence_threshold"  # Pass if metric >= value
    RISK_THRESHOLD = "risk_threshold"  # Pass if risk <= value
    CONTRADICTION_THRESHOLD = "contradiction_threshold"  # Pass if contradictions <= value
    EVIDENCE_COMPLETENESS = "evidence_completeness"  # Pass if evidence present
    HUMAN_APPROVAL = "human_approval"  # Pass if human approves
    BUDGET_THRESHOLD = "budget_threshold"  # Pass if within budget
    TIME_THRESHOLD = "time_threshold"  # Pass if within time limit


class GateCondition(BaseModel):
    """Condition for a decision gate."""
    gate_type: DecisionGateType
    metric: str  # e.g., "market_confidence", "regulatory_risk"
    operator: str  # ">=", "<=", ">", "<", "=="
    value: float
    on_pass: str  # "continue", "spawn_subgraph", "escalate"
    on_fail: str  # "stop", "alternate_branch", "spawn_validation"


class DecisionOutcome(BaseModel):
    """Result of a decision gate evaluation."""
    gate_id: str
    condition: GateCondition
    passed: bool
    actual_value: float
    decision: str  # What action to take
    reason: str
    evaluated_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Graph Creation Request
# ============================================================================

class MissionCreateRequest(BaseModel):
    """Request to create a new mission."""
    title: str
    mission_type: MissionType
    objective: str
    context: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    reasoning_strategy: Optional[ReasoningStrategy] = None

    # Optional: provide initial graph structure
    initial_graph: Optional[MissionGraph] = None


class MissionGraphCreateRequest(BaseModel):
    """Request to create a mission graph."""
    mission_id: str
    objective: str
    context: Dict[str, Any]

    # Graph structure hints
    suggested_workstreams: List[str] = Field(default_factory=list)
    required_deliverables: List[str] = Field(default_factory=list)
    risk_areas: List[str] = Field(default_factory=list)

    # Strategic memory to incorporate
    use_strategic_memory: bool = True
    reasoning_strategy: Optional[ReasoningStrategy] = None


# ============================================================================
# Graph Execution Models
# ============================================================================

class NodeExecutionRequest(BaseModel):
    """Request to execute a node."""
    node_id: str
    mission_id: str
    graph_id: str

    # Execution context
    workspace_id: Optional[str] = None
    agent_type: Optional[AgentType] = None
    reasoning_strategy: Optional[ReasoningStrategy] = None

    # Inputs from dependencies
    input_data: Dict[str, Any] = Field(default_factory=dict)

    # Configuration
    timeout_seconds: int = 300
    allow_parallel: bool = True


class NodeExecutionResult(BaseModel):
    """Result from executing a node."""
    node_id: str
    mission_id: str
    status: NodeStatus

    # Outputs
    outputs: List[MissionNodeOutput] = Field(default_factory=list)
    workspace_id: Optional[str] = None

    # Metrics
    duration_seconds: float
    token_count: Optional[int] = None
    confidence_score: Optional[float] = None

    # Decision outcomes
    decision_outcomes: List[DecisionOutcome] = Field(default_factory=list)

    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0

    completed_at: datetime = Field(default_factory=datetime.now)


class GraphExecutionState(BaseModel):
    """Current state of graph execution."""
    mission_id: str
    graph_id: str
    status: MissionStatus

    # Node status summary
    total_nodes: int
    pending_nodes: int
    ready_nodes: int
    running_nodes: int
    blocked_nodes: int
    completed_nodes: int
    failed_nodes: int
    skipped_nodes: int

    # Progress
    progress_percent: float
    estimated_completion_seconds: Optional[int] = None

    # Active work
    ready_node_ids: List[str] = Field(default_factory=list)
    blocked_node_ids: List[str] = Field(default_factory=list)
    running_node_ids: List[str] = Field(default_factory=list)

    # Deliverables
    completed_deliverables: List[str] = Field(default_factory=list)
    pending_deliverables: List[str] = Field(default_factory=list)

    updated_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Workstream Models
# ============================================================================

class Workstream(BaseModel):
    """A group of related nodes forming a logical workstream."""
    id: str
    mission_id: str
    name: str
    domain: str  # "finance", "operations", "market", "compliance"
    lead_agent_type: AgentType

    # Nodes in this workstream
    node_ids: List[str] = Field(default_factory=list)

    # Status
    status: NodeStatus = NodeStatus.PENDING
    progress_percent: float = 0.0

    # Dependencies
    depends_on_workstreams: List[str] = Field(default_factory=list)


# ============================================================================
# Example Graphs
# ============================================================================

EXAMPLE_MARKET_ENTRY_GRAPH = MissionGraph(
    id="graph_example_001",
    mission_id="mission_example_001",
    version="1.0",
    nodes=[
        MissionNode(
            id="n1",
            graph_id="graph_example_001",
            node_type=NodeType.OBJECTIVE,
            title="Assess market opportunity",
            description="Determine viability, risks, and recommended entry strategy for Segment X"
        ),
        MissionNode(
            id="n2",
            graph_id="graph_example_001",
            node_type=NodeType.TASK,
            title="Estimate market size",
            agent_type=AgentType.SPECIALIST,
            reasoning_strategy=ReasoningStrategy.EVIDENCE_WEIGHTED,
            depends_on_nodes=[]
        ),
        MissionNode(
            id="n3",
            graph_id="graph_example_001",
            node_type=NodeType.TASK,
            title="Evaluate regulatory exposure",
            agent_type=AgentType.DOMAIN_LEAD,
            reasoning_strategy=ReasoningStrategy.RISK_FIRST,
            depends_on_nodes=[]
        ),
        MissionNode(
            id="n4",
            graph_id="graph_example_001",
            node_type=NodeType.DECISION,
            title="Go/no-go gate",
            decision_condition={
                "market_confidence_min": 0.75,
                "regulatory_risk_max": 0.40
            },
            depends_on_nodes=["n2", "n3"]
        ),
        MissionNode(
            id="n5",
            graph_id="graph_example_001",
            node_type=NodeType.DELIVERABLE,
            title="Executive brief",
            deliverable_type="executive_brief",
            depends_on_nodes=["n4"]
        )
    ],
    edges=[
        MissionEdge(
            id="e1",
            graph_id="graph_example_001",
            source_node_id="n2",
            target_node_id="n4",
            edge_type=EdgeType.DEPENDS_ON
        ),
        MissionEdge(
            id="e2",
            graph_id="graph_example_001",
            source_node_id="n3",
            target_node_id="n4",
            edge_type=EdgeType.DEPENDS_ON
        ),
        MissionEdge(
            id="e3",
            graph_id="graph_example_001",
            source_node_id="n4",
            target_node_id="n5",
            edge_type=EdgeType.DEPENDS_ON
        )
    ]
)
