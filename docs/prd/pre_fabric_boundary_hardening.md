# TORQ Console - Pre-Fabric Boundary Hardening PRD
## Post-Layer 10 Architectural Separation Before Layer 11

---

## Document Metadata

| Field | Value |
|-------|-------|
| **PRD ID** | PRD-011-PRE |
| **Status** | Draft |
| **Priority** | Critical (Blocker for Layer 11) |
| **Timeline** | 1-2 weeks |
| **Dependencies** | Layers 1-10 Complete |
| **Blocks** | Layer 11: Distributed Intelligence Fabric |

---

## Executive Summary

### Problem Statement

After Layer 10, TORQ has accumulated significant intelligence capabilities:

- Mission execution (L1-L3)
- Workflow orchestration (L4)
- Knowledge management (L5)
- Human-machine interface (L6)
- Operator control (L7)
- Autonomous learning (L8)
- Organizational intelligence (L9)
- Strategic simulation (L10)

**Risk**: These capabilities have evolved with implicit dependencies and blurred boundaries. Without explicit separation now, Layer 11 (Distributed Intelligence Fabric) would require painful retrofitting.

### Solution

**Pre-Fabric Boundary Hardening**: A focused architecture pass to establish explicit contracts, scopes, and boundaries before distributed implementation begins.

**Objective**: Make TORQ distributable before making it distributed.

---

## Success Criteria

### Primary Success Criteria

1. **Service Contracts**: Every intelligence domain has a stable, versioned contract
2. **State Separation**: Operational and strategic state are fully separated
3. **Policy Scopes**: Every policy declares its scope explicitly
4. **Artifact Standard**: All intelligence outputs follow a standard artifact shape
5. **Event Taxonomy**: Formal event model prevents mixed-state pipelines

### Validation Criteria

- [ ] Contract registry exists with all 9 domains represented
- [ ] No simulation state can leak into production decision systems
- [ ] Policy can travel as metadata, not handwritten logic
- [ ] Intelligence artifacts are self-describing and portable
- [ ] Federation export layer works without exposing local internals
- [ ] UI consumes stable APIs, not internal models

---

## Architecture Domains

### The 9 Intelligence Domains

| Domain | Layer | Responsibility | State Type |
|--------|-------|----------------|------------|
| **Execution Domain** | L1-L3 | Mission execution, readiness, lifecycle | Operational |
| **Memory Domain** | L3, L5 | Mission memory, knowledge artifacts | Operational |
| **Insight Domain** | L8 | Pattern discovery, anomaly detection | Analytical |
| **Pattern Domain** | L8 | Learned patterns, recommendations | Learned |
| **Governance Domain** | L7 | Policy enforcement, authority boundaries | Governing |
| **Organizational Domain** | L9 | Cross-mission aggregation, benchmarking | Federated |
| **Simulation Domain** | L10 | Scenario modeling, forecasting, calibration | Strategic |
| **Audit Domain** | L10 | Decision artifacts, traceability | Archival |
| **Federation Domain** | L11 | Cross-node intelligence sharing | Distributed |

### Domain Interaction Rules

1. **Operational domains** (Execution, Memory) serve live missions
2. **Analytical domains** (Insight, Pattern) produce intelligence from operational data
3. **Governing domain** (Governance) constrains all domains
4. **Strategic domains** (Simulation) never touch operational state directly
5. **Archival domain** (Audit) records decisions for traceability
6. **Federated domain** (Federation) only receives exportable intelligence

---

## 1. Canonical Service Contracts

### 1.1 Contract Definition Schema

All service contracts follow this structure:

```python
class ServiceContract(BaseModel):
    """Canonical contract for a TORQ intelligence domain."""

    # Identity
    contract_id: str
    contract_version: str
    service_name: str
    service_domain: ServiceDomain

    # Interface
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    error_schema: Dict[str, Any]

    # Constraints
    requires_authentication: bool
    required_authority: AuthorityLevel
    rate_limit: Optional[RateLimit]

    # Dependencies
    upstream_contracts: List[str]  # Contract IDs this depends on
    downstream_contracts: List[str]  # Contract IDs that depend on this

    # Governance
    policy_scope: PolicyScope
    federation_eligible: bool
    audit_required: bool

    # Metadata
    stability: StabilityLevel  # stable, experimental, deprecated
    deprecation_date: Optional[datetime]
    contact_owner: str
```

### 1.2 Domain Contracts

#### Execution Domain Contract

```python
class ExecutionContract(ServiceContract):
    """Contract for mission execution operations."""

    service_name = "execution_service"
    service_domain = ServiceDomain.EXECUTION

    # Input
    input_schema = {
        "mission_request": {
            "mission_id": "UUID",
            "mission_type": "str",
            "parameters": "Dict[str, Any]",
            "context": "ExecutionContext",
            "authority": "AuthorityToken",
        }
    }

    # Output
    output_schema = {
        "mission_result": {
            "mission_id": "UUID",
            "status": "MissionStatus",
            "outcome": "MissionOutcome",
            "artifacts": "List[MissionArtifact]",
            "execution_time_ms": "float",
        }
    }
```

#### Simulation Domain Contract

```python
class SimulationContract(ServiceContract):
    """Contract for strategic simulation operations."""

    service_name = "simulation_service"
    service_domain = ServiceDomain.SIMULATION

    # Input
    input_schema = {
        "scenario_request": {
            "scenario_id": "UUID",
            "scope": "SimulationScope",
            "parameters": "SimulationParameters",
            "iterations": "int",
            "context_override": "Optional[SimulationContext]",
        }
    }

    # Output
    output_schema = {
        "simulation_result": {
            "scenario_id": "UUID",
            "result_id": "UUID",
            "predicted_outcomes": "Dict[str, Any]",
            "confidence": "float",
            "total_simulations": "int",
            "artifacts": "List[SimulationArtifact]",
        }
    }

    # Critical: Simulation is NEVER federation_eligible directly
    # Only derived insights (through audit/calibration) can be exported
    federation_eligible = False
```

#### Governance Domain Contract

```python
class GovernanceContract(ServiceContract):
    """Contract for governance policy operations."""

    service_name = "governance_service"
    service_domain = ServiceDomain.GOVERNANCE

    # Input
    input_schema = {
        "policy_query": {
            "policy_id": "Optional[UUID]",
            "scope": "PolicyScope",
            "subject": "str",  # What the policy applies to
            "action": "str",   # Action being governed
        }
    }

    # Output
    output_schema = {
        "governance_decision": {
            "allowed": "bool",
            "policy_id": "UUID",
            "reason": "str",
            "constraints": "List[PolicyConstraint]",
            "authority": "AuthorityLevel",
        }
    }
```

### 1.3 Contract Registry

The Contract Registry maintains all active contracts:

```python
class ContractRegistry:
    """Registry of all TORQ service contracts."""

    def register_contract(self, contract: ServiceContract) -> None:
        """Register a new service contract."""

    def get_contract(self, contract_id: str) -> Optional[ServiceContract]:
        """Get a contract by ID."""

    def list_contracts_by_domain(self, domain: ServiceDomain) -> List[ServiceContract]:
        """List all contracts for a domain."""

    def validate_compatibility(
        self,
        upstream_id: str,
        downstream_id: str
    ) -> CompatibilityResult:
        """Validate that two contracts can interact."""

    def get_contract_graph(self) -> ContractDependencyGraph:
        """Get the full dependency graph of all contracts."""
```

---

## 2. Intelligence Artifact Standard

### 2.1 Base Artifact Schema

All intelligence-producing services emit artifacts following this standard:

```python
class IntelligenceArtifact(BaseModel):
    """Standard artifact emitted by all intelligence services."""

    # Identity
    artifact_id: UUID = Field(default_factory=uuid4)
    artifact_type: ArtifactType
    artifact_version: str = "1.0"

    # Provenance
    origin_service: str
    origin_domain: ServiceDomain
    origin_node_id: Optional[str] = None  # For distributed scenarios

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    valid_at: Optional[datetime] = None  # For future-valid artifacts

    # Content
    title: str
    description: str
    content: Dict[str, Any]

    # Quality & Confidence
    confidence: float = Field(ge=0.0, le=1.0)
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Lineage
    source_artifact_ids: List[UUID] = Field(default_factory=list)
    parent_artifact_id: Optional[UUID] = None
    derivation_chain: List[str] = Field(default_factory=list)  # How was this derived?

    # Reproducibility
    reproducible: bool = True
    reproducibility_metadata: Optional[Dict[str, Any]] = None

    # Scope & Boundaries
    scope: ArtifactScope
    visibility: ArtifactVisibility

    # Governance
    governance_tags: List[str] = Field(default_factory=list)
    policy_references: List[str] = Field(default_factory=list)  # Policies that apply

    # Federation
    federation_eligible: bool = False
    federation_redactions: List[str] = Field(default_factory=list)  # Fields to redact
```

### 2.2 Artifact Types

```python
class ArtifactType(str, Enum):
    """Types of intelligence artifacts."""

    # Execution artifacts
    MISSION_RESULT = "mission_result"
    MISSION_ARTIFACT = "mission_artifact"

    # Memory artifacts
    MEMORY_ENTRY = "memory_entry"
    KNOWLEDGE_ARTIFACT = "knowledge_artifact"

    # Insight artifacts
    PATTERN_DISCOVERY = "pattern_discovery"
    ANOMALY_DETECTION = "anomaly_detection"
    INSIGHT_REPORT = "insight_report"

    # Pattern artifacts
    LEARNED_PATTERN = "learned_pattern"
    RECOMMENDATION = "recommendation"

    # Governance artifacts
    POLICY_DECISION = "policy_decision"
    AUTHORITY_GRANT = "authority_grant"

    # Organizational artifacts
    CROSS_MISSION_AGGREGATION = "cross_mission_aggregation"
    BENCHMARK_SUMMARY = "benchmark_summary"

    # Simulation artifacts
    SIMULATION_RESULT = "simulation_result"
    FORECAST_DATA = "forecast_data"
    SCENARIO_COMPARISON = "scenario_comparison"

    # Audit artifacts
    DECISION_RECORD = "decision_record"
    AUDIT_TRAIL = "audit_trail"

    # Calibration artifacts
    CALIBRATION_DATA = "calibration_data"
    FORECAST_ERROR = "forecast_error"
```

### 2.3 Artifact Scopes

```python
class ArtifactScope(str, Enum):
    """Scope boundaries for artifacts."""

    # Single instance
    SINGLE_MISSION = "single_mission"
    SINGLE_WORKSPACE = "single_workspace"

    # Organizational
    ORGANIZATION = "organization"
    MISSION_TYPE = "mission_type"

    # Simulation (never live)
    SIMULATION_ONLY = "simulation_only"
    SCENARIO = "scenario"

    # Federation
    FEDERATION_EXPORT = "federation_export"
    FEDERATION_SHARED = "federation_shared"

    # System
    SYSTEM_WIDE = "system_wide"
```

### 2.4 Artifact Visibility

```python
class ArtifactVisibility(str, Enum):
    """Visibility levels for artifacts."""

    # Private
    PRIVATE = "private"  # Creator-only access
    INTERNAL = "internal"  # Internal to the node

    # Shared
    ORGANIZATIONAL = "organizational"  # Within organization
    FEDERATED = "federated"  # Shared across nodes

    # Public
    PUBLIC = "public"  # Fully public
```

### 2.5 Artifact Examples

#### Simulation Result Artifact

```python
simulation_artifact = IntelligenceArtifact(
    artifact_type=ArtifactType.SIMULATION_RESULT,
    origin_service="simulation_service",
    origin_domain=ServiceDomain.SIMULATION,
    title="Policy Change Impact Simulation",
    description="Simulated impact of proposed readiness threshold change",
    content={
        "scenario_config": {...},
        "predicted_outcomes": {
            "success_rate": 0.72,
            "avg_duration": 145.0,
            "quality_variance": 0.15,
        },
        "confidence_intervals": {
            "success_rate": [0.65, 0.79],
            "duration": [120.0, 170.0],
        },
    },
    confidence=0.85,
    scope=ArtifactScope.SIMULATION_ONLY,
    visibility=ArtifactVisibility.INTERNAL,
    reproducible=True,
    reproducibility_metadata={
        "scenario_id": str(scenario_id),
        "iterations": 1000,
        "random_seed": 42,
    },
    federation_eligible=False,  # Raw simulations never export
)
```

#### Federatable Insight Artifact

```python
insight_artifact = IntelligenceArtifact(
    artifact_type=ArtifactType.BENCHMARK_SUMMARY,
    origin_service="organizational_intelligence",
    origin_domain=ServiceDomain.ORGANIZATIONAL,
    title="Mission Duration Benchmarks",
    description="Aggregated duration metrics across 500 missions",
    content={
        "metric_type": "duration",
        "statistics": {
            "mean": 120.0,
            "median": 115.0,
            "p95": 180.0,
            "p99": 240.0,
        },
        "sample_size": 500,
        "mission_types": ["analysis", "development", "deployment"],
    },
    confidence=0.95,
    scope=ArtifactScope.ORGANIZATION,
    visibility=ArtifactVisibility.FEDERATED,
    federation_eligible=True,
    federation_redactions=[
        "individual_mission_ids",
        "workspace_identifiers",
    ],
)
```

---

## 3. Event Taxonomy

### 3.1 Event Base Schema

```python
class TorqEvent(BaseModel):
    """Base event for all TORQ system events."""

    # Identity
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    event_category: EventCategory

    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.now)
    correlation_id: Optional[UUID] = None

    # Source
    source_service: str
    source_domain: ServiceDomain
    source_node_id: Optional[str] = None

    # Actor
    actor_id: Optional[str] = None
    actor_type: ActorType
    authority_level: Optional[AuthorityLevel] = None

    # Content
    payload: Dict[str, Any]
    payload_schema: str  # Schema version for payload validation

    # State Classification
    execution_mode: ExecutionMode  # LIVE, SIMULATED, REPLAY

    # Impact
    affected_scopes: List[ArtifactScope]
    affected_resources: List[str]

    # Traceability
    causation_id: Optional[UUID] = None  # Event that caused this
    causation_chain: List[UUID] = Field(default_factory=list)

    # Governance
    requires_audit: bool = True
    federation_eligible: bool = False
```

### 3.2 Event Categories

```python
class EventCategory(str, Enum):
    """High-level categories for TORQ events."""

    # Operational events
    OPERATIONAL = "operational"  # Mission execution, readiness changes
    LIFECYCLE = "lifecycle"  # Service start/stop, configuration changes

    # Intelligence events
    INSIGHT = "insight"  # Pattern discoveries, anomalies
    LEARNING = "learning"  # Pattern updates, model changes
    SIMULATION = "simulation"  # Scenario execution, forecast generation

    # Governance events
    GOVERNANCE = "governance"  # Policy decisions, authority changes
    AUTHORIZATION = "authorization"  # Access grants, denials

    # Organizational events
    AGGREGATION = "aggregation"  # Cross-mission summaries
    BENCHMARK = "benchmark"  # Benchmark generation

    # Audit events
    AUDIT = "audit"  # Decision records, compliance events
    CALIBRATION = "calibration"  # Forecast error recording, parameter updates

    # Federation events
    FEDERATION_EXPORT = "federation_export"  # Intelligence export
    FEDERATION_IMPORT = "federation_import"  # External intelligence received
```

### 3.3 Execution Mode Classification

```python
class ExecutionMode(str, Enum):
    """Execution mode for events and operations."""

    LIVE = "live"  # Real operational execution
    SIMULATED = "simulated"  # Simulation/sandbox execution
    REPLAY = "replay"  # Historical replay for analysis
    TEST = "test"  # Testing/development execution
```

**Critical Rule**: All events must declare their execution mode explicitly. This prevents state contamination between live and simulated operations.

### 3.4 Event Examples

#### Live Mission Event

```python
mission_event = TorqEvent(
    event_type="mission.completed",
    event_category=EventCategory.OPERATIONAL,
    source_service="execution_service",
    source_domain=ServiceDomain.EXECUTION,
    actor_type=ActorType.SYSTEM,
    execution_mode=ExecutionMode.LIVE,
    payload={
        "mission_id": str(mission_id),
        "mission_type": "analysis",
        "status": "completed",
        "duration_ms": 145.2,
        "success": True,
    },
    affected_scopes=[ArtifactScope.SINGLE_MISSION],
    affected_resources=[f"mission:{mission_id}"],
    requires_audit=True,
    federation_eligible=False,  # Raw missions don't export
)
```

#### Simulation Event

```python
simulation_event = TorqEvent(
    event_type="simulation.completed",
    event_category=EventCategory.SIMULATION,
    source_service="simulation_service",
    source_domain=ServiceDomain.SIMULATION,
    actor_type=ActorType.OPERATOR,
    actor_id="user@example.com",
    execution_mode=ExecutionMode.SIMULATED,
    payload={
        "scenario_id": str(scenario_id),
        "scope": "policy_change",
        "iterations": 1000,
        "predicted_success_rate": 0.72,
    },
    affected_scopes=[ArtifactScope.SIMULATION_ONLY],
    affected_resources=[f"scenario:{scenario_id}"],
    requires_audit=True,
    federation_eligible=False,
)
```

#### Federation Export Event

```python
export_event = TorqEvent(
    event_type="federation.exported",
    event_category=EventCategory.FEDERATION_EXPORT,
    source_service="federation_service",
    source_domain=ServiceDomain.FEDERATION,
    actor_type=ActorType.SYSTEM,
    execution_mode=ExecutionMode.LIVE,
    payload={
        "artifact_id": str(artifact_id),
        "artifact_type": "benchmark_summary",
        "destination_nodes": ["node-1", "node-2"],
        "redaction_count": 2,
    },
    affected_scopes=[ArtifactScope.FEDERATION_EXPORT],
    federation_eligible=True,
)
```

---

## 4. Policy Scope Model

### 4.1 Policy Scope Definition

```python
class PolicyScope(BaseModel):
    """Defines where and how a policy applies."""

    scope_id: UUID = Field(default_factory=uuid4)
    scope_name: str

    # Spatial scope
    spatial_boundaries: List[SpatialBoundary]

    # Temporal scope
    temporal_boundary: TemporalBoundary

    # Execution mode scope
    execution_modes: List[ExecutionMode]

    # Domain scope
    applicable_domains: List[ServiceDomain]

    # Authority scope
    minimum_authority: Optional[AuthorityLevel] = None

    # Federation scope
    federation_exportable: bool = False
```

### 4.2 Spatial Boundaries

```python
class SpatialBoundary(str, Enum):
    """Spatial boundaries for policy application."""

    # Single instance
    SINGLE_MISSION = "single_mission"
    SINGLE_WORKSPACE = "single_workspace"
    SINGLE_NODE = "single_node"

    # Organizational
    ORGANIZATION = "organization"
    ORGANIZATIONAL_UNIT = "organizational_unit"

    # Federation
    FEDERATION = "federation"
    FEDERATION_SUBSET = "federation_subset"

    # Global
    SYSTEM_WIDE = "system_wide"
```

### 4.3 Temporal Boundaries

```python
class TemporalBoundary(BaseModel):
    """Time-based policy boundaries."""

    effective_start: datetime
    effective_end: Optional[datetime] = None

    # Recurrence
    recurrence: Optional[RecurrenceRule] = None

    # Triggers
    trigger_conditions: List[str] = Field(default_factory=list)
```

### 4.4 Scope Templates

#### Local Runtime Policy

```python
LOCAL_RUNTIME_SCOPE = PolicyScope(
    scope_name="local_runtime",
    spatial_boundaries=[SpatialBoundary.SINGLE_NODE],
    execution_modes=[ExecutionMode.LIVE],
    applicable_domains=[
        ServiceDomain.EXECUTION,
        ServiceDomain.MEMORY,
    ],
    minimum_authority=AuthorityLevel.OPERATOR,
    federation_exportable=False,
)
```

#### Simulation-Only Policy

```python
SIMULATION_SCOPE = PolicyScope(
    scope_name="simulation_only",
    spatial_boundaries=[SpatialBoundary.SINGLE_NODE],
    execution_modes=[ExecutionMode.SIMULATED],
    applicable_domains=[ServiceDomain.SIMULATION],
    minimum_authority=None,  # Anyone can run simulations
    federation_exportable=False,
)
```

#### Organizational Policy

```python
ORGANIZATIONAL_SCOPE = PolicyScope(
    scope_name="organizational",
    spatial_boundaries=[SpatialBoundary.ORGANIZATION],
    execution_modes=[ExecutionMode.LIVE],
    applicable_domains=[
        ServiceDomain.EXECUTION,
        ServiceDomain.MEMORY,
        ServiceDomain.INSIGHT,
        ServiceDomain.PATTERN,
        ServiceDomain.GOVERNANCE,
    ],
    minimum_authority=AuthorityLevel.MANAGER,
    federation_exportable=False,
)
```

#### Federated Policy

```python
FEDERATED_SCOPE = PolicyScope(
    scope_name="federated",
    spatial_boundaries=[SpatialBoundary.FEDERATION],
    execution_modes=[ExecutionMode.LIVE],
    applicable_domains=[ServiceDomain.FEDERATION],
    minimum_authority=AuthorityLevel.ADMINISTRATOR,
    federation_exportable=True,
)
```

### 4.5 Policy Reference Contract

Policies should travel as references, not embedded code:

```python
class PolicyReference(BaseModel):
    """Reference to a policy that can travel across domains."""

    policy_id: UUID
    policy_version: str
    policy_name: str
    policy_hash: str  # For verification

    # Scope
    scope: PolicyScope

    # Contract
    enforcement_point: str  # Where this policy is enforced
    evaluation_type: PolicyEvaluationType  # SYNC, ASYNC, DEFERRED

    # Metadata
    created_at: datetime
    effective_at: datetime
    expires_at: Optional[datetime] = None

    # Federation
    portable: bool  # Can this policy be applied elsewhere?
    requires_local_adaptation: bool
```

---

## 5. Identity and Boundary Model

### 5.1 Action Identity Schema

Every major system action must answer: who, what, where, when, how?

```python
class ActionIdentity(BaseModel):
    """Complete identity for a system action."""

    # Action Identity
    action_id: UUID = Field(default_factory=uuid4)
    action_type: str
    action_category: str

    # Initiator
    initiated_by: ActorIdentity
    authorized_by: Optional[PolicyReference] = None

    # Service Context
    executing_service: str
    executing_domain: ServiceDomain
    executing_node: Optional[str] = None

    # Scope Context
    target_scope: ArtifactScope
    target_resources: List[str]

    # Execution Context
    execution_mode: ExecutionMode
    execution_environment: ExecutionEnvironment

    # Temporal
    initiated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Traceability
    correlation_id: UUID
    causation_chain: List[UUID] = Field(default_factory=list)

    # State
    action_state: ActionState
    outcome: Optional[ActionOutcome] = None
```

### 5.2 Actor Identity

```python
class ActorIdentity(BaseModel):
    """Identity of who initiated an action."""

    actor_id: str
    actor_type: ActorType

    # For human actors
    human_identity: Optional[HumanIdentity] = None

    # For service actors
    service_identity: Optional[ServiceIdentity] = None

    # Authority
    authority_level: AuthorityLevel
    authority_source: str  # How was this authority granted?

    # Session
    session_id: Optional[str] = None
    session_started_at: Optional[datetime] = None
```

### 5.3 Actor Types

```python
class ActorType(str, Enum):
    """Types of actors that can initiate actions."""

    # Human
    HUMAN_OPERATOR = "human_operator"
    HUMAN_ADMINISTRATOR = "human_administrator"

    # System
    SYSTEM = "system"  # Autonomous system action
    SERVICE = "service"  # Service-initiated action

    # Federation
    FEDERATED_NODE = "federated_node"  # Action from another node
    EXTERNAL_SYSTEM = "external_system"  # External integration
```

### 5.4 Execution Environment

```python
class ExecutionEnvironment(str, Enum):
    """Environment classification for actions."""

    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TESTING = "testing"
    SIMULATION = "simulation"  # Explicitly simulated environment
```

**Critical Rule**: Actions in `SIMULATION` environment can NEVER affect `PRODUCTION` state, regardless of actor authority.

### 5.5 Action State

```python
class ActionState(str, Enum):
    """States of an action's lifecycle."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    RUNNING = "running"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"
```

---

## 6. State Boundary Enforcement

### 6.1 Operational vs Strategic State Separation

```python
class StateBoundary(BaseModel):
    """Enforces boundary between operational and strategic state."""

    boundary_type: StateType
    allowed_transitions: List[StateTransition]
    forbidden_operations: List[str]

    # Promotion
    promotion_required: bool
    promotion_path: Optional[PromotionPath] = None


class StateType(str, Enum):
    """Types of state with boundary enforcement."""

    OPERATIONAL = "operational"  # Live mission state
    STRATEGIC = "strategic"  # Simulation/forecast state
    ANALYTICAL = "analytical"  # Insight/pattern state
    ARCHIVAL = "archival"  # Audit/record state


class PromotionPath(BaseModel):
    """Path for promoting state from one boundary to another."""

    source_type: StateType
    target_type: StateType

    # Approval
    required_authority: AuthorityLevel
    approval_workflow: List[str]

    # Validation
    validation_steps: List[str]
    cooling_off_period: Optional[timedelta] = None

    # Traceability
    audit_required: bool
```

### 6.2 State Contamination Prevention

```python
class StateBoundaryEnforcer:
    """Enforces state boundaries to prevent contamination."""

    async def validate_write(
        self,
        target_type: StateType,
        source_type: StateType,
        operation: str,
        actor_authority: AuthorityLevel,
    ) -> BoundaryDecision:
        """
        Validate if a write operation is allowed across state boundaries.

        Rules:
        1. STRATEGIC state can NEVER write to OPERATIONAL state directly
        2. OPERATIONAL state can NEVER be modified by SIMULATION execution
        3. Promotion requires explicit approval workflow
        4. All cross-boundary writes are audited
        """

    async def promote_state(
        self,
        source_artifact_id: UUID,
        target_type: StateType,
        promoter: ActorIdentity,
        rationale: str,
    ) -> PromotionResult:
        """
        Promote state from one boundary to another.

        Example: Promoting a simulated policy change to operational policy.
        """
```

---

## 7. Federation Export Model

### 7.1 Export Contract

```python
class FederationExportContract(BaseModel):
    """Contract for exporting intelligence across nodes."""

    export_id: UUID = Field(default_factory=uuid4)
    source_artifact_id: UUID

    # Source
    source_node: str
    source_domain: ServiceDomain
    source_service: str

    # Content
    artifact_type: ArtifactType
    content_summary: str  # High-level description (not full content)
    artifact_metadata: Dict[str, Any]

    # Redaction
    redaction_policy: RedactionPolicy
    redacted_fields: List[str]

    # Destination
    target_nodes: List[str]  # Empty = broadcast to federation
    target_audience: FederationAudience

    # Validity
    export_timestamp: datetime
    expires_at: Optional[datetime] = None
    ttl_seconds: Optional[int] = None

    # Governance
    export_authority: AuthorityLevel
    authorized_by: str
    governance_tags: List[str]

    # Provenance
    source_artifact_hash: str
    source_artifact_version: str
```

### 7.2 Redaction Policy

```python
class RedactionPolicy(BaseModel):
    """Defines what gets redacted before federation."""

    redaction_level: RedactionLevel

    # Field patterns to redact
    redacted_patterns: List[str] = [
        "*.secret",
        "*.token",
        "*.password",
        "*.private_key",
        "*._id",  # Internal IDs
        "*.workspace_*",  # Workspace-specific data
    ]

    # Field transformations
    transformation_rules: Dict[str, str] = Field(default_factory=dict)


class RedactionLevel(str, Enum):
    """Levels of redaction for federation."""

    NONE = "none"  # No redaction (internal only)
    MINIMAL = "minimal"  # Remove secrets and internal IDs
    STANDARD = "standard"  # Remove identifying information
    AGGRESSIVE = "aggressive"  # Only aggregate statistics
    FULL = "full"  # Only high-level summaries
```

### 7.3 Import Validation

```python
class FederationImportValidator:
    """Validates incoming federated intelligence."""

    async def validate_import(
        self,
        import_contract: FederationExportContract,
        artifact_data: Dict[str, Any],
    ) -> ImportValidationResult:
        """
        Validate an incoming federated artifact.

        Checks:
        1. Contract integrity and signature
        2. Source node authorization
        3. Redaction policy compliance
        4. Content schema validation
        5. Governance tag requirements
        6. TTL and expiration
        7. Artifact hash verification
        """

    async def apply_import(
        self,
        validated_import: ValidatedImport,
    ) -> ImportResult:
        """
        Apply a validated federated import.

        Note: Federated intelligence NEVER becomes local operational state.
        It can only inform:
        - Local insights (as reference data)
        - Local benchmarks (as comparison data)
        - Local simulations (as external scenarios)
        """
```

---

## 8. Implementation Plan

### Phase 1: Contract Foundation (Week 1)

**Goal**: Establish contract infrastructure

1. Create `torq_console/contracts/` module
2. Implement `ServiceContract` base schema
3. Implement `ContractRegistry` service
4. Create initial contracts for all 9 domains

**Deliverables**:
- [ ] Contract module with registry
- [ ] 9 domain contracts defined
- [ ] Contract validation tests
- [ ] Contract dependency graph visualization

### Phase 2: Artifact Standard (Week 1-2)

**Goal**: Standardize intelligence artifacts

1. Create `torq_console/artifacts/` module
2. Implement `IntelligenceArtifact` base schema
3. Create artifact factory for each domain
4. Implement artifact validation and serialization

**Deliverables**:
- [ ] Artifact module with standard schema
- [ ] Artifact factories for all domains
- [ ] Artifact serialization/deserialization
- [ ] Artifact validation tests

### Phase 3: Event Taxonomy (Week 2)

**Goal**: Formalize event model

1. Create `torq_console/events/` module
2. Implement `TorqEvent` base schema
3. Create event emitters for each domain
4. Implement event classification and routing

**Deliverables**:
- [ ] Event module with taxonomy
- [ ] Event emitters for all domains
- [ ] Event routing and filtering
- [ ] Event validation tests

### Phase 4: Policy Scopes (Week 2)

**Goal**: Define policy boundaries

1. Create `torq_console/governance/scopes/` module
2. Implement `PolicyScope` and `PolicyReference`
3. Create scope templates
4. Implement scope validation

**Deliverables**:
- [ ] Policy scope module
- [ ] Scope templates for all scenarios
- [ ] Scope validation tests
- [ ] Policy portability checks

### Phase 5: State Boundaries (Week 2)

**Goal**: Enforce state separation

1. Create `torq_console/state/boundaries/` module
2. Implement `StateBoundaryEnforcer`
3. Create state promotion workflows
4. Implement boundary violation detection

**Deliverables**:
- [ ] State boundary module
- [ ] Boundary enforcement service
- [ ] State promotion workflows
- [ ] Boundary violation tests

### Phase 6: Integration & Validation (Week 2)

**Goal**: Validate all boundaries

1. Run comprehensive boundary validation
2. Test federation export/import
3. Validate state separation
4. Test policy portability

**Deliverables**:
- [ ] Boundary validation suite
- [ ] Federation tests
- [ ] State separation verification
- [ ] Architecture compliance report

---

## 9. Validation Criteria

### Contract Validation

- [ ] Every domain has a registered contract
- [ ] All contracts define input/output/error schemas
- [ ] Contract dependencies are explicit
- [ ] Contract versioning is enforced
- [ ] Contract compatibility validation works

### Artifact Validation

- [ ] All intelligence outputs use `IntelligenceArtifact`
- [ ] All artifacts have required metadata
- [ ] Artifact lineage is trackable
- [ ] Federation eligibility is correctly flagged
- [ ] Redaction policies are applied

### Event Validation

- [ ] All events use `TorqEvent` base schema
- [ ] Event categories are consistent
- [ ] Execution mode is always declared
- [ ] Event chains are traceable
- [ ] No mixed-state events exist

### Policy Validation

- [ ] Every policy has a declared scope
- [ ] Policy boundaries are enforced
- [ ] Policy references are portable
- [ ] Policy promotion requires approval
- [ ] No hardcoded policies in service code

### State Validation

- [ ] Operational and strategic state are separated
- [ ] Simulation cannot write to operational state
- [ ] State promotion requires explicit workflow
- [ ] All cross-boundary writes are audited
- [ ] State contamination is prevented

### Federation Validation

- [ ] Export contracts are enforced
- [ ] Redaction policies are applied
- [ ] Import validation works
- [ ] Federated data never becomes operational
- [ ] Node identity is verified

---

## 10. Success Metrics

### Quantitative Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Contract Coverage | 100% of domains | 9/9 contracts registered |
| Artifact Standardization | 100% of outputs | All intelligence uses standard artifact |
| Event Classification | 100% of events | All events have category and mode |
| Policy Scoping | 100% of policies | All policies have declared scope |
| State Separation | 0 violations | No cross-boundary state writes |
| Federation Compliance | 100% of exports | All exports follow contract |

### Qualitative Outcomes

- Clear contract boundaries between all domains
- Intelligence artifacts are self-describing and portable
- Event taxonomy prevents ambiguity
- Policies can travel as metadata
- State contamination is architecturally impossible
- Federation is governed by explicit contracts

---

## 11. Risks and Mitigations

### Risk 1: Backward Compatibility

**Risk**: Existing code may not conform to new boundaries

**Mitigation**:
- Gradual migration path
- Adapter layer for legacy interfaces
- Deprecation warnings for non-compliant code

### Risk 2: Performance Overhead

**Risk**: Boundary enforcement may add latency

**Mitigation**:
- Async boundary validation
- Cached validation results
- Optional enforcement for non-critical paths

### Risk 3: Migration Complexity

**Risk**: Migrating existing state and events

**Mitigation**:
- Automated migration scripts
- Backfill tools for historical data
- Validation during migration

### Risk 4: Federation Security

**Risk**: Exported intelligence could leak sensitive data

**Mitigation**:
- Mandatory redaction policies
- Import validation and sandboxing
- Audit of all federation activity

---

## 12. Dependencies and Blocking

### Blocks

- **Layer 11: Distributed Intelligence Fabric** - Cannot begin until boundary hardening is complete

### Depends On

- **Layers 1-10** - All complete ✅

### Integration Points

- **Control Plane (L7)** - Will consume new contracts
- **Organizational Intelligence (L9)** - Will use artifact standard
- **Simulation (L10)** - Will enforce state boundaries
- **Calibration Engine** - Will use artifact lineage

---

## 13. Open Questions

1. **Contract Versioning Strategy**: Should breaking contract changes be allowed? How are they handled?
2. **Artifact Retention**: How long are artifacts retained? What's the cleanup policy?
3. **Federation Trust Model**: How do nodes establish trust in a federation?
4. **State Promotion Authority**: Who approves state promotion from simulation to operational?

---

## 14. Next Steps

1. **Review and Approve**: Review this PRD and approve for implementation
2. **Phase 1 Implementation**: Begin contract foundation
3. **Weekly Checkpoints**: Review progress against validation criteria
4. **Final Validation**: Run complete boundary validation suite
5. **Layer 11 Gate**: Confirm boundaries before Layer 11 begins

---

## Appendix A: Domain Contract Quick Reference

| Domain | Service | Key Contracts | Federation |
|--------|---------|---------------|------------|
| Execution | execution_service | MissionRequest, MissionResult | No |
| Memory | memory_service | MemoryEntry, KnowledgeArtifact | Export only |
| Insight | insight_service | PatternDiscovery, AnomalyReport | Yes (aggregated) |
| Pattern | pattern_service | LearnedPattern, Recommendation | Yes (abstract) |
| Governance | governance_service | PolicyQuery, GovernanceDecision | Yes (metadata) |
| Organizational | org_intelligence | CrossMissionSummary, Benchmark | Yes (aggregated) |
| Simulation | simulation_service | ScenarioRequest, SimulationResult | No (via audit only) |
| Audit | audit_service | DecisionRecord, AuditTrail | Yes (redacted) |
| Federation | federation_service | ExportContract, ImportContract | Yes |

---

## Appendix B: Artifact Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                     Artifact Lifecycle                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. CREATION                                                     │
│     └── Service emits IntelligenceArtifact                      │
│         └── With standard metadata, lineage, scope               │
│                                                                  │
│  2. VALIDATION                                                   │
│     └── Artifact schema validation                               │
│     └── Scope compliance check                                   │
│     └── Governance tag validation                                │
│                                                                  │
│  3. STORAGE                                                      │
│     └── Persist in domain-specific storage                       │
│     └── Index by artifact_id, type, scope                        │
│                                                                  │
│  4. CONSUMPTION                                                  │
│     └── Other services consume via contract                      │
│     └── Traceable usage tracking                                 │
│                                                                  │
│  5. FEDERATION (if eligible)                                    │
│     └── Apply redaction policy                                   │
│     └── Create export contract                                   │
│     └── Export to federation                                     │
│                                                                  │
│  6. ARCHIVAL                                                    │
│     └── Move to cold storage after TTL                           │
│     └── Retain per retention policy                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

**Document Version**: 1.0
**Last Updated**: 2025-03-11
**Status**: Draft - Pending Review
