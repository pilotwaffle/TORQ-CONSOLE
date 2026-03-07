"""
Autonomy Models - Core data structures for autonomous operations.

Defines the object model for monitors, triggers, tasks, approvals, and policies.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any, Dict, List, Optional, Set,
    Callable, Awaitable, Union
)

from pydantic import BaseModel, Field


# ============================================================================
# Monitor Types
# ============================================================================

class MonitorType(str, Enum):
    """Types of monitors that can watch systems over time."""
    HEALTH_CHECK = "health_check"      # Endpoint health monitoring
    THRESHOLD = "threshold"             # Numeric threshold crossing
    SCHEDULE = "schedule"               # Time-based execution
    STATUS_CHANGE = "status_change"     # State transition detection
    ABSENCE = "absence"                 # Missing expected event
    TOPIC = "topic"                     # News/topic tracking
    WORKFLOW_FAILURE = "workflow_failure"  # Workflow execution failure
    POLICY_VIOLATION = "policy_violation"  # Policy rule breach


class TriggerType(str, Enum):
    """Types of trigger events."""
    THRESHOLD_CROSSED = "threshold_crossed"
    STATUS_CHANGED = "status_changed"
    HEARTBEAT_MISSED = "heartbeat_missed"
    SCHEDULE_REACHED = "schedule_reached"
    TOPIC_MATCHED = "topic_matched"
    WORKFLOW_FAILED = "workflow_failed"
    ANOMALY_DETECTED = "anomaly_detected"


class ExecutionMode(str, Enum):
    """Execution modes for autonomous operations."""
    OBSERVE = "observe"       # Read-only monitoring and summarization
    PREPARE = "prepare"       # Create plans/recommendations, but do not act
    EXECUTE = "execute"       # Perform approved or policy-allowed actions


class TaskState(str, Enum):
    """States in the autonomous task lifecycle."""
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_TOOL = "waiting_for_tool"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    RETRY_SCHEDULED = "retry_scheduled"


class ApprovalStatus(str, Enum):
    """Status of approval requests."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PolicyLevel(str, Enum):
    """Policy levels for autonomous actions."""
    ALLOW = "allow"                    # Auto-allow, no logging required
    ALLOW_WITH_LOG = "allow_with_log"  # Auto-allow, must log
    REQUIRE_APPROVAL = "require_approval"  # Must get approval
    DENY = "deny"                      # Never allowed


class ActionRisk(str, Enum):
    """Risk levels for autonomous actions."""
    LOW = "low"          # Read-only, no side effects
    MEDIUM = "medium"    # Creates content, no external actions
    HIGH = "high"        # External side effects, system changes
    CRITICAL = "critical"  # Destructive, requires explicit approval


# ============================================================================
# Pydantic Models for API serialization
# ============================================================================

class MonitorConfig(BaseModel):
    """Configuration for a monitor."""
    monitor_id: str
    type: MonitorType
    name: str
    description: Optional[str] = None

    # Target configuration
    target: str  # URL, endpoint, metric path, etc.

    # Schedule/interval
    interval_seconds: int = 300  # Default 5 minutes
    schedule_cron: Optional[str] = None  # Cron expression

    # Trigger condition
    trigger_condition: Dict[str, Any]  # Condition that triggers action

    # Action policy
    execution_mode: ExecutionMode = ExecutionMode.OBSERVE
    action_policy: PolicyLevel = PolicyLevel.ALLOW_WITH_LOG

    # Workspace/tenant scoping
    workspace_id: Optional[str] = None
    environment: Optional[str] = None  # dev, staging, production

    # Cooldown to prevent noisy triggers
    cooldown_seconds: int = 300

    # Metadata
    enabled: bool = True
    created_at: float = Field(default_factory=time.time)
    created_by: Optional[str] = None

    # Last state
    last_check: Optional[float] = None
    last_trigger: Optional[float] = None
    last_result: Optional[Dict[str, Any]] = None


class Monitor(MonitorConfig):
    """Active monitor with runtime state."""

    @property
    def is_due(self) -> bool:
        """Check if monitor is due for execution."""
        if not self.enabled:
            return False

        now = time.time()
        if self.last_check is None:
            return True

        elapsed = now - self.last_check
        return elapsed >= self.interval_seconds

    @property
    def is_in_cooldown(self) -> bool:
        """Check if monitor is in cooldown period after triggering."""
        if self.last_trigger is None:
            return False

        now = time.time()
        elapsed = now - self.last_trigger
        return elapsed < self.cooldown_seconds


class TriggerEvent(BaseModel):
    """A detected trigger event."""
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    monitor_id: str
    event_type: TriggerType
    severity: str = "medium"  # low, medium, high, critical

    # Event payload
    payload: Dict[str, Any] = Field(default_factory=dict)

    # Event metadata
    detected_at: float = Field(default_factory=time.time)
    workspace_id: Optional[str] = None
    environment: Optional[str] = None

    # Processing state
    processed: bool = False
    task_id: Optional[str] = None

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


class AutonomousTaskConfig(BaseModel):
    """Configuration for an autonomous task."""
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:12]}")
    name: str
    description: Optional[str] = None

    # Trigger source
    event_id: Optional[str] = None
    monitor_id: Optional[str] = None

    # Execution configuration
    execution_mode: ExecutionMode
    agents: List[str] = Field(default_factory=list)  # Specialist agents to use
    tool_policy: str = "optional"  # required, preferred, optional

    # Task parameters
    prompt_template: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Policy and approval
    approval_required: bool = False
    risk_level: ActionRisk = ActionRisk.LOW
    policy_decision: Optional[PolicyDecision] = None

    # Workspace/tenant scoping
    workspace_id: Optional[str] = None
    environment: Optional[str] = None

    # Scheduling
    scheduled_for: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3

    # Metadata
    created_at: float = Field(default_factory=time.time)
    created_by: Optional[str] = None  # user or system

    # State tracking
    state: TaskState = TaskState.CREATED


class AutonomousTask(AutonomousTaskConfig):
    """Active autonomous task with execution state."""

    # Execution tracking
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    execution_time: Optional[float] = None

    # Results
    result: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    # Agent results
    agent_results: List[Dict[str, Any]] = Field(default_factory=list)

    # Approval tracking
    approval_id: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[float] = None

    # Linked artifacts
    linked_artifacts: List[str] = Field(default_factory=list)

    @property
    def is_finished(self) -> bool:
        """Check if task is finished."""
        return self.state in [
            TaskState.SUCCEEDED,
            TaskState.FAILED,
            TaskState.CANCELLED
        ]

    @property
    def can_execute(self) -> bool:
        """Check if task can be executed."""
        return (
            self.state in [TaskState.CREATED, TaskState.QUEUED, TaskState.RETRY_SCHEDULED]
            and not self.approval_required
        )

    @property
    def needs_approval(self) -> bool:
        """Check if task needs approval."""
        return (
            self.approval_required
            and self.approval_id is None
            and self.state != TaskState.CANCELLED
        )


class PolicyDecision(BaseModel):
    """Result of policy engine evaluation."""
    allowed: bool
    policy_level: PolicyLevel
    reason: str
    requires_approval: bool = False
    risk_level: ActionRisk = ActionRisk.LOW

    # Additional context
    evaluated_at: float = Field(default_factory=time.time)
    policy_rules_matched: List[str] = Field(default_factory=list)
    confidence: float = 1.0


class ApprovalRequest(BaseModel):
    """Request for human approval of an autonomous action."""
    approval_id: str = Field(default_factory=lambda: f"apr_{uuid.uuid4().hex[:12]}")
    task_id: str

    # What is being requested
    requested_action: str
    action_description: str

    # Risk and policy
    risk_level: ActionRisk
    policy_level: PolicyLevel

    # Context
    trigger_reason: str
    workspace_id: Optional[str] = None
    environment: Optional[str] = None

    # State
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float = Field(default_factory=time.time)
    expires_at: Optional[float] = None

    # Resolution
    approved_by: Optional[str] = None
    approved_at: Optional[float] = None
    denied_reason: Optional[str] = None

    # Supporting information
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_impact: Optional[str] = None


# ============================================================================
# Task State Record for persistence
# ============================================================================

@dataclass
class TaskStateRecord:
    """Persistent record of task state."""
    task_id: str
    state: TaskState
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "state": self.state.value,
            "timestamp": self.timestamp,
            "data": self.data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskStateRecord":
        return cls(
            task_id=data["task_id"],
            state=TaskState(data["state"]),
            timestamp=data["timestamp"],
            data=data.get("data", {})
        )


@dataclass
class MonitorState:
    """Persistent state of a monitor."""
    monitor_id: str
    last_check: Optional[float] = None
    last_trigger: Optional[float] = None
    last_result: Optional[Dict[str, Any]] = None
    trigger_count: int = 0
    last_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "monitor_id": self.monitor_id,
            "last_check": self.last_check,
            "last_trigger": self.last_trigger,
            "last_result": self.last_result,
            "trigger_count": self.trigger_count,
            "last_error": self.last_error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonitorState":
        return cls(
            monitor_id=data["monitor_id"],
            last_check=data.get("last_check"),
            last_trigger=data.get("last_trigger"),
            last_result=data.get("last_result"),
            trigger_count=data.get("trigger_count", 0),
            last_error=data.get("last_error")
        )
