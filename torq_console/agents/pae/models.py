"""
PAE (Plan-Approve-Execute) Pattern Models

Core data models for the Plan-Approve-Execute workflow pattern.
Provides structured, type-safe representations of plans, steps, checkpoints,
and execution context for human-in-the-loop AI workflows.
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class PlanPhase(str, Enum):
    """Phases of a PAE workflow"""
    PLANNING = "planning"
    APPROVAL = "approval"
    EXECUTION = "execution"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PlanStatus(str, Enum):
    """Status of an action plan"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Status of a plan step"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class ActionType(str, Enum):
    """Types of actions that can be executed"""
    CODE_GENERATION = "code_generation"
    FILE_OPERATION = "file_operation"
    API_CALL = "api_call"
    COMMAND_EXECUTION = "command_execution"
    DATABASE_OPERATION = "database_operation"
    USER_INTERACTION = "user_interaction"
    VALIDATION = "validation"
    ROLLBACK = "rollback"


class PlanStep(BaseModel):
    """Individual step within an action plan"""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Human-readable name of the step")
    description: str = Field(..., description="Detailed description of what this step does")
    action_type: ActionType = Field(..., description="Type of action this step performs")

    # Execution details
    agent: str = Field(..., description="Name of the agent responsible for this step")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the step")

    # Dependencies and ordering
    depends_on: List[UUID] = Field(default_factory=list, description="IDs of steps this step depends on")
    order: int = Field(..., description="Execution order within the plan")

    # Status tracking
    status: StepStatus = Field(default=StepStatus.PENDING, description="Current status of the step")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Result of step execution")
    error: Optional[str] = Field(default=None, description="Error message if step failed")

    # Risk and safety
    risk_level: str = Field(default="low", description="Risk level: low, medium, high, critical")
    requires_confirmation: bool = Field(default=False, description="Whether this step needs explicit confirmation")
    rollback_command: Optional[str] = Field(default=None, description="Command to rollback this step")

    # Checkpoints
    checkpoint_before: bool = Field(default=False, description="Create checkpoint before this step")
    checkpoint_after: bool = Field(default=True, description="Create checkpoint after this step")

    # Metadata
    estimated_duration: Optional[int] = Field(default=None, description="Estimated duration in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    class Config:
        use_enum_values = True


class WorkflowCheckpoint(BaseModel):
    """Checkpoint in the workflow for rollback capability"""
    id: UUID = Field(default_factory=uuid4)
    plan_id: UUID
    step_id: Optional[UUID] = Field(default=None, description="Step after which this checkpoint was created")

    # Checkpoint data
    state: Dict[str, Any] = Field(..., description="Complete state snapshot")
    files_changed: List[str] = Field(default_factory=list, description="List of files changed since last checkpoint")
    resources_created: List[str] = Field(default_factory=list, description="Resources created at this checkpoint")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = Field(default=None, description="Human-readable description")

    # Rollback info
    rollback_commands: List[str] = Field(default_factory=list, description="Commands to rollback to this checkpoint")
    rollback_successful: Optional[bool] = Field(default=None, description="Whether rollback was successful")


class ApprovalRequest(BaseModel):
    """Request for human approval"""
    id: UUID = Field(default_factory=uuid4)
    plan_id: UUID

    # Request details
    title: str = Field(..., description="Title of the approval request")
    description: str = Field(..., description="Detailed description of what needs approval")
    plan_summary: str = Field(..., description="Summary of the plan to be approved")

    # Risk assessment
    risk_level: str = Field(..., description="Overall risk level of the plan")
    warnings: List[str] = Field(default_factory=list, description="Warnings about the plan")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for approval")

    # Approval details
    approver: Optional[str] = Field(default=None, description="Who should approve this request")
    deadline: Optional[datetime] = Field(default=None, description="Deadline for approval")

    # Response
    approved: Optional[bool] = Field(default=None, description="Whether the request was approved")
    approved_by: Optional[str] = Field(default=None, description="Who approved the request")
    approved_at: Optional[datetime] = Field(default=None, description="When the request was approved")
    comments: Optional[str] = Field(default=None, description="Comments from the approver")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None, description="When this request expires")


class ExecutionContext(BaseModel):
    """Context for plan execution"""
    session_id: UUID = Field(default_factory=uuid4)
    user_id: str = Field(..., description="ID of the user requesting execution")
    workspace_path: str = Field(..., description="Path to the workspace")

    # Environment
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    permissions: Set[str] = Field(default_factory=set, description="User permissions")

    # Configuration
    auto_approve_safe: bool = Field(default=False, description="Auto-approve low-risk operations")
    require_approval_for: List[ActionType] = Field(
        default_factory=lambda: [ActionType.FILE_OPERATION, ActionType.COMMAND_EXECUTION],
        description="Action types that require approval"
    )

    # Safety settings
    sandbox_mode: bool = Field(default=True, description="Run in sandbox mode when possible")
    dry_run: bool = Field(default=False, description="Perform a dry run without making changes")
    max_parallel_steps: int = Field(default=1, description="Maximum number of parallel steps")

    # Checkpoint settings
    auto_checkpoint: bool = Field(default=True, description="Automatically create checkpoints")
    checkpoint_frequency: int = Field(default=5, description="Create checkpoint every N steps")
    keep_checkpoints: int = Field(default=10, description="Number of checkpoints to keep")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ActionPlan(BaseModel):
    """Complete action plan for a PAE workflow"""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Name of the plan")
    description: str = Field(..., description="Description of what this plan accomplishes")

    # Plan structure
    steps: List[PlanStep] = Field(..., description="Steps in the plan")
    checkpoints: List[WorkflowCheckpoint] = Field(default_factory=list, description="Checkpoints in the workflow")

    # Status and phase
    status: PlanStatus = Field(default=PlanStatus.DRAFT)
    phase: PlanPhase = Field(default=PlanPhase.PLANNING)

    # Progress tracking
    total_steps: int = Field(..., description="Total number of steps")
    completed_steps: int = Field(default=0, description="Number of completed steps")
    current_step: Optional[UUID] = Field(default=None, description="ID of the currently executing step")

    # Approval
    approval_request: Optional[ApprovalRequest] = Field(default=None, description="Approval request if needed")
    approved_by: Optional[str] = Field(default=None, description="Who approved this plan")
    approved_at: Optional[datetime] = Field(default=None)

    # Execution context
    context: ExecutionContext = Field(..., description="Context for execution")

    # Results and errors
    result: Optional[Dict[str, Any]] = Field(default=None, description="Final result of plan execution")
    errors: List[str] = Field(default_factory=list, description="Errors encountered during execution")
    warnings: List[str] = Field(default_factory=list, description="Warnings generated during execution")

    # Rollback
    can_rollback: bool = Field(default=True, description="Whether this plan can be rolled back")
    rolled_back: bool = Field(default=False, description="Whether this plan has been rolled back")
    rollback_checkpoint: Optional[UUID] = Field(default=None, description="Checkpoint to rollback to")

    # Metadata
    created_by: str = Field(..., description="Who created this plan")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    @validator('steps')
    def validate_steps(cls, v):
        """Validate step dependencies and ordering"""
        if not v:
            raise ValueError("Plan must have at least one step")

        # Check for unique order values
        orders = [step.order for step in v]
        if len(orders) != len(set(orders)):
            raise ValueError("Step orders must be unique")

        # Check dependencies
        step_ids = {step.id for step in v}
        for step in v:
            for dep_id in step.depends_on:
                if dep_id not in step_ids:
                    raise ValueError(f"Step {step.name} depends on non-existent step {dep_id}")

        return v

    @validator('total_steps')
    def validate_total_steps(cls, v, values):
        """Validate total steps matches steps list"""
        if 'steps' in values and v != len(values['steps']):
            raise ValueError("total_steps must match length of steps list")
        return v

    @property
    def is_ready_for_approval(self) -> bool:
        """Check if plan is ready for approval"""
        return self.status == PlanStatus.DRAFT and self.phase == PlanPhase.PLANNING

    @property
    def is_ready_for_execution(self) -> bool:
        """Check if plan is ready for execution"""
        return self.status == PlanStatus.APPROVED and self.phase == PlanPhase.APPROVAL

    @property
    def progress_percentage(self) -> float:
        """Calculate progress as percentage"""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100

    @property
    def risk_level(self) -> str:
        """Calculate overall risk level of the plan"""
        if not self.steps:
            return "low"

        risk_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        max_score = max(risk_scores.get(step.risk_level, 1) for step in self.steps)

        if max_score >= 4:
            return "critical"
        elif max_score >= 3:
            return "high"
        elif max_score >= 2:
            return "medium"
        return "low"

    def get_step_by_id(self, step_id: UUID) -> Optional[PlanStep]:
        """Get a step by its ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_next_steps(self) -> List[PlanStep]:
        """Get steps that are ready to execute"""
        completed = {step.id for step in self.steps if step.status == StepStatus.COMPLETED}
        ready = []

        for step in self.steps:
            if step.status == StepStatus.PENDING:
                # Check if all dependencies are completed
                if all(dep in completed for dep in step.depends_on):
                    ready.append(step)

        return sorted(ready, key=lambda s: s.order)

    def create_checkpoint(self, after_step: Optional[UUID] = None, description: Optional[str] = None) -> WorkflowCheckpoint:
        """Create a checkpoint"""
        checkpoint = WorkflowCheckpoint(
            plan_id=self.id,
            step_id=after_step,
            description=description,
            state={}  # TODO: Capture actual state
        )
        self.checkpoints.append(checkpoint)
        return checkpoint

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }