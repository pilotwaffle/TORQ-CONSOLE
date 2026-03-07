"""
TORQ Console Autonomy Module

Phase 5: Persistent Autonomous Operations & Task Governance

Provides the autonomous operations layer that enables TORQ Console to:
- Monitor systems continuously
- Detect meaningful events and changes
- Execute approved workflows automatically
- Request approval when risk is high
- Maintain memory, telemetry, and audit trails

Execution Modes:
- OBSERVE: Read-only monitoring and summarization
- PREPARE: Create plans/recommendations, but do not act
- EXECUTE: Perform approved or policy-allowed actions
"""

# Core models
from .models import (
    Monitor,
    MonitorType,
    TriggerEvent,
    TriggerType,
    AutonomousTask,
    TaskState,
    ExecutionMode,
    ApprovalRequest,
    ApprovalStatus,
    PolicyLevel,
    PolicyDecision,
    ActionRisk,
    TaskStateRecord,
    MonitorState,
)

# Task engine
from .task_engine import (
    TaskEngine,
    TaskScheduler,
    TaskQueue,
    get_task_engine,
)

# Trigger engine
from .trigger_engine import (
    TriggerEngine,
    TriggerEvaluator,
    get_trigger_engine,
)

# Policy engine
from .policy_engine import (
    PolicyEngine,
    PolicyRule,
    ActionRisk,
    get_policy_engine,
)

# Execution planner
from .execution_planner import (
    ExecutionPlanner,
    ExecutionPlan as AutonomyExecutionPlan,
    get_execution_planner,
)

# Approval manager
from .approval_manager import (
    ApprovalManager,
    ApprovalInbox,
    get_approval_manager,
)

# State store
from .state_store import (
    StateStore,
    MonitorState,
    TaskStateRecord,
    get_state_store,
)

# Orchestrator
from .orchestrator import (
    AutonomousOrchestrator,
    get_autonomous_orchestrator,
)

# Preparation Engine (Phase 5B)
from .preparation import (
    PreparationEngine,
    PreparationPlan,
    PreparationStep,
    PlanType,
    PlanStatus,
    Recommendation,
    DryRunResult,
    SimulationResult,
    get_preparation_engine,
)

# Execution Engine (Phase 5C)
from .execution import (
    ExecutionEngine,
    ExecutionResult,
    ExecutionStepResult,
    ExecutionStatus,
    ExecutionMetrics,
    ToolPolicyEnforcer,
    ToolPolicyRule,
    ToolPolicy,
    RollbackAction,
    get_execution_engine,
)

# Governance (Phase 6)
from .governance import (
    GovernanceEngine,
    Workspace,
    WorkspaceMember,
    Role,
    RoleType,
    Permission,
    PermissionSet,
    ResourceType,
    User,
    QuotaLimit,
    QuotaType,
    AuditEvent,
    AuditEventType,
    PolicyHierarchy,
    get_governance_engine,
)

# Learning Engine (Phase 7)
from .learning import (
    LearningEngine,
    TaskOutcome,
    OutcomeCategory,
    PerformanceMetrics,
    ImprovementSuggestion,
    ImprovementType,
    ModelFeedback,
    FeedbackType,
    LearningSourceType,
    ObservationRecord,
    get_learning_engine,
)

__all__ = [
    # Models
    'Monitor',
    'MonitorType',
    'TriggerEvent',
    'TriggerType',
    'AutonomousTask',
    'TaskState',
    'ExecutionMode',
    'ApprovalRequest',
    'ApprovalStatus',
    'PolicyLevel',
    'PolicyDecision',
    'ActionRisk',
    'TaskStateRecord',
    'MonitorState',
    # Task Engine
    'TaskEngine',
    'TaskScheduler',
    'TaskQueue',
    'get_task_engine',
    # Trigger Engine
    'TriggerEngine',
    'TriggerEvaluator',
    'get_trigger_engine',
    # Policy Engine
    'PolicyEngine',
    'PolicyRule',
    'ActionRisk',
    'get_policy_engine',
    # Execution Planner
    'ExecutionPlanner',
    'AutonomyExecutionPlan',
    'get_execution_planner',
    # Approval Manager
    'ApprovalManager',
    'ApprovalInbox',
    'get_approval_manager',
    # State Store
    'StateStore',
    'MonitorState',
    'TaskStateRecord',
    'get_state_store',
    # Orchestrator
    'AutonomousOrchestrator',
    'get_autonomous_orchestrator',
    # Preparation Engine (Phase 5B)
    'PreparationEngine',
    'PreparationPlan',
    'PreparationStep',
    'PlanType',
    'PlanStatus',
    'Recommendation',
    'DryRunResult',
    'SimulationResult',
    'get_preparation_engine',
    # Execution Engine (Phase 5C)
    'ExecutionEngine',
    'ExecutionResult',
    'ExecutionStepResult',
    'ExecutionStatus',
    'ExecutionMetrics',
    'ToolPolicyEnforcer',
    'ToolPolicyRule',
    'ToolPolicy',
    'RollbackAction',
    'get_execution_engine',
    # Governance (Phase 6)
    'GovernanceEngine',
    'Workspace',
    'WorkspaceMember',
    'Role',
    'RoleType',
    'Permission',
    'PermissionSet',
    'ResourceType',
    'User',
    'QuotaLimit',
    'QuotaType',
    'AuditEvent',
    'AuditEventType',
    'PolicyHierarchy',
    'get_governance_engine',
    # Learning Engine (Phase 7)
    'LearningEngine',
    'TaskOutcome',
    'OutcomeCategory',
    'PerformanceMetrics',
    'ImprovementSuggestion',
    'ImprovementType',
    'ModelFeedback',
    'FeedbackType',
    'LearningSourceType',
    'ObservationRecord',
    'get_learning_engine',
]

__version__ = '1.0.0'
