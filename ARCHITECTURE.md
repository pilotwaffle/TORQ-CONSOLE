# TORQ Console Architecture Documentation

**Version:** 1.0.0
**Status:** Production Platform Foundation
**Last Updated:** 2025-03-07

---

## Executive Summary

TORQ Console is an AI-native operations platform foundation. It enables autonomous monitoring, plan generation, governed execution, and enterprise workflow automation across external systems.

### The Transition Point (Commit `cd79505b`)

At commit `cd79505b`, TORQ Console crossed the threshold from prototype to production platform. This is where the system gained:

- **Complete execution provenance** - Every action traceable from trigger to verification
- **Enterprise governance** - Multi-tenant RBAC, policy hierarchies, audit trails
- **External integration fabric** - Safe, governed execution across external systems
- **Self-improvement capabilities** - Learning from outcomes and pattern detection

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TORQ CONSOLE PLATFORM                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│  │   Phase 1    │     │   Phase 2    │     │   Phase 3    │              │
│  │ Agent Routing │     │  Routing     │     │ Tool Policy  │              │
│  │              │     │  Override    │     │   Engine     │              │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘              │
│         │                    │                    │                       │
│         └────────────────────┴────────────────────┘                       │
│                              │                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                         Phase 4: Multi-Agent Orchestration          │ │
│  │                    Executive Controller + Coordination               │ │
│  └───────────────────────────────────────┬──────────────────────────────┘ │
│                                          │                                  │
│  ┌───────────────────────────────────────┼──────────────────────────────┐ │
│  │              Phase 5: Autonomous Operations                   │      │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐               │      │
│  │  │ Observe │->│ Prepare │->│ Execute │               │      │
│  │  └─────────┘  └─────────┘  └─────────┘               │      │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                          │                                  │
│  ┌───────────────────────────────────────┼──────────────────────────────┐ │
│  │                   Phase 6: Governance                       │      │
│  │              RBAC + Workspaces + Quotas                  │      │
│  └───────────────────────────────────────┼──────────────────────────────┘ │
│                                          │                                  │
│  ┌───────────────────────────────────────┼──────────────────────────────┐ │
│  │                   Phase 7: Learning                         │      │
│  │         Outcomes + Patterns + Suggestions                 │      │
│  └───────────────────────────────────────┼──────────────────────────────┘ │
│                                          │                                  │
│  ┌───────────────────────────────────────┴──────────────────────────────┐ │
│  │                  Phase 8: External Action Fabric               │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │ │
│  │  │ Connectors │->│  Action    │->│  Workflow  │             │ │
│  │  │            │  │   Fabric   │  │   Engine   │             │ │
│  │  └────────────┘  └────────────┘  └────────────┘             │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase-By-Phase Architecture

### Phase 1: Agent Routing System

**Purpose:** Intelligently route user queries to appropriate agents.

**Key Components:**
- `ChatIntentRouter` - Analyzes user intent and selects best agent
- `IntentDetector` - Classifies queries (research, coding, debugging, etc.)
- `AgentCapabilityRegistry` - Tracks agent capabilities and availability

**Flow:**
```
User Query -> Intent Detection -> Agent Selection -> Agent Execution
```

### Phase 2: Routing Override System

**Purpose:** Enable runtime override of routing decisions.

**Key Components:**
- `RealtimeOverrideEngine` - Admin override capabilities
- `RoutingStateStore` - Current routing state management
- `OverrideAuditor` - Audit trail for overrides

### Phase 3: Tool Policy Engine

**Purpose:** Enforce safety policies on tool usage.

**Key Components:**
- `ToolPolicyEngine` - Validates tool usage against policies
- `ToolPolicyRule` - Policy rule definitions
- `DefaultPolicies` - Built-in safety policies

### Phase 4: Multi-Agent Orchestration

**Purpose:** Coordinate multiple agents for complex tasks.

**Key Components:**
- `AgentOrchestrator` - Central coordination
- `ExecutionPlan` - Multi-step execution plans
- `AgentCoordinator` - Agent selection and delegation
- `ExecutionModes` - Single, Multi, Pipeline, Parallel

**Execution Modes:**
- **Single:** One agent completes the task
- **Multi:** Multiple agents collaborate
- **Pipeline:** Sequential agent processing
- **Parallel:** Concurrent agent execution

### Phase 5: Autonomous Operations

#### Phase 5A: Observe-Only Autonomy
- Monitors systems without acting
- Detects events and changes
- Generates summaries and alerts

#### Phase 5B: Prepare Mode Autonomy
- Creates execution plans
- Dry-run simulations
- Recommendations without action

#### Phase 5C: Execute Mode Autonomy
- Executes approved plans
- Tool policy enforcement
- Rollback capabilities

**Progressive Trust:**
```
Observe -> Prepare -> Execute
(No straight-to-execute)
```

### Phase 6: Multi-Tenant Governance

**Purpose:** Enterprise control plane with hard tenant boundaries.

**Key Components:**
- `GovernanceEngine` - Central governance
- `Workspace` - Tenant isolation
- `Role` & `Permission` - RBAC with ADMIN wildcard
- `QuotaLimit` - Resource limits
- `AuditEvent` - SOC2-compliance logging

**Policy Hierarchy:**
```
Platform -> Organization -> Workspace -> Environment
```

**Hard Tenant Boundaries:**
- Every object has `workspace_id` and `environment`
- RBAC enforced in backend, not just UI
- No cross-tenant data leakage

### Phase 7: Self-Improvement & Agent Generation

**Purpose:** Learn from outcomes and improve capabilities.

**Key Components:**
- `LearningEngine` - Central learning system
- `TaskOutcome` - Execution outcome tracking
- `PerformanceMetrics` - Per-agent/task metrics
- `ImprovementSuggestion` - Auto-generated improvements
- `PatternDetection` - Failure/slow task detection

**Learning Loop:**
```
Execute -> Record Outcome -> Detect Patterns -> Generate Suggestions -> Implement
```

### Phase 8: External Action Fabric

**Purpose:** Safe execution across external systems.

**Key Components:**
- `ExternalActionFabric` - Central execution layer
- `ConnectorRegistry` - Connector management
- `BaseConnector` - Standard connector interface
- `WorkflowExecutionEngine` - Multi-step workflows
- `ProvenanceStore` - Execution traceability
- `CircuitBreaker` - Failure isolation

**Controlled Action Fabric Model:**
```
Agent Plan -> Policy Evaluation -> Connector Action ->
Execution Fabric -> External System -> Result Verification -> Audit Record
```

---

## Core Architectural Principles

### 1. Progressive Trust

Actions progress through modes with explicit approval:
- **OBSERVE:** Read-only monitoring
- **PREPARE:** Plan/recommend only
- **EXECUTE:** Perform actions (requires approval for high-risk)

No straight-to-execute for high-risk operations.

### 2. Hard Tenant Boundaries

Every object carries `workspace_id` and `environment`:
- Policy enforcement at all layers
- RBAC in backend, not UI
- Audit trails for compliance

### 3. Governance Before Autonomy

Phase 6 (Governance) is the foundation for Phases 5 and 7:
- Without RBAC, agents become dangerous
- Without quotas, costs can spiral
- Without audit, compliance is impossible

### 4. Controlled Action Fabric

Agents never directly execute external actions:
- Agents propose → Fabric evaluates → Fabric executes
- Policy compliance at every step
- Idempotency keys prevent duplicate execution
- Circuit breakers prevent cascading failures

### 5. Execution Provenance

Every action is traceable:
```
trigger -> plan -> approval -> workflow -> node ->
connector action -> verification result
```

### 6. Idempotency Everywhere

All externally visible actions have stable idempotency keys:
- Slack/webhook messages
- Jira ticket creation
- Deployment actions
- API calls

---

## Connector Architecture

### Connector Categories

| Category | Examples | Use Cases |
|-----------|----------|-----------|
| **SaaS** | Slack, Notion, Salesforce | Notifications, CRM |
| **Infrastructure** | AWS, Railway, Kubernetes | Deployments, scaling |
| **Data Platform** | Snowflake, BigQuery, Supabase | Analytics, ETL |
| **Communication** | Email, SMS, Discord | Alerts, notifications |

### Connector Interface

All connectors implement `BaseConnector`:

```python
class BaseConnector(ABC):
    async def execute(self, action: ExternalAction) -> ActionExecutionResult
    async def validate_parameters(self, action_type, params) -> (bool, Optional[str])
    def get_capabilities(self) -> List[ConnectorCapability]
    async def health_check(self) -> HealthCheckResult
```

### Circuit Breaking Pattern

```
              Failure Count ≥ Threshold
                       │
                       ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  CLOSED  │───>│   OPEN   │───>│ HALF_OPEN│
    └──────────┘    └──────────┘    └──────────┘
         ▲                │                │
         └────────────────┴────────────────┘
              Success Threshold / Timeout
```

- **CLOSED:** Normal operation, requests pass through
- **OPEN:** Circuit tripped, fail fast immediately
- **HALF_OPEN:** Testing if service has recovered

---

## Data Models

### Core Entities

```python
# Autonomous Task
AutonomousTask:
    task_id: str
    name: str
    execution_mode: OBSERVE | PREPARE | EXECUTE
    trigger_event: TriggerEvent
    state: TaskState
    workspace_id: str
    environment: str

# Workspace
Workspace:
    workspace_id: str
    name: str
    owner_id: str
    environment: str
    members: List[WorkspaceMember]
    quotas: Dict[str, QuotaLimit]

# External Action
ExternalAction:
    action_id: str
    action_type: str
    connector_type: str
    parameters: Dict[str, Any]
    risk_level: LOW | MEDIUM | HIGH | CRITICAL
    idempotency_key: str
    workspace_id: str
    state: ActionState

# Execution Provenance
ExecutionProvenance:
    provenance_id: str
    trace_id: str
    trigger_id: str
    plan_id: str
    workflow_id: str
    action_id: str
    connector_type: str
    idempotency_key: str
    status: str
    result: Dict[str, Any]
```

---

## Security Architecture

### Multi-Layer Security

1. **Authentication**
   - User authentication (OAuth, SAML)
   - Service authentication (API keys, tokens)

2. **Authorization (RBAC)**
   - Role-based access control
   - Permission sets per role
   - ADMIN permission as wildcard

3. **Policy Enforcement**
   - Pre-execution policy checks
   - Tool policy validation
   - Approval gates for high-risk actions

4. **Tenant Isolation**
   - Hard boundaries at data layer
   - Scoped queries everywhere
   - Audit trail for compliance

5. **Audit Logging**
   - All actions logged
   - SOC2 compliance ready
   - Immutable audit records

### Risk Levels

| Level | Description | Approval Required |
|-------|-------------|-------------------|
| LOW | Read operations, notifications | No |
| MEDIUM | Write to non-production | No (policy-dependent) |
| HIGH | Production writes, sensitive data | Yes |
| CRITICAL | Infrastructure changes, deletions | Yes |

---

## Technology Stack

### Backend
- **Python 3.10+** - Core runtime
- **Pydantic 2.x** - Data validation
- **asyncio** - Async I/O
- **aiohttp** - HTTP client

### Frontend
- **TypeScript** - Type safety
- **React 18** - UI framework
- **React Router v6** - Routing
- **Zustand** - State management

### Infrastructure
- **Railway** - Deployment platform
- **Vercel** - Frontend hosting
- **Supabase** - Database/auth (planned)

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Railway (Backend)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  TORQ API    │  │  Worker      │  │  PostgreSQL  │        │
│  │  (FastAPI)   │  │  Processes   │  │              │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Vercel (Frontend)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  React App   │  │  Static      │  │  Edge        │        │
│  │              │  │  Assets     │  │  Functions   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Development Workflow

### Repository Structure

```
torq_console/
├── agents/           # Phase 1-4: Multi-agent system
│   ├── core/         # Agent registry and base classes
│   ├── orchestration/ # Executive coordination
│   └── routing/      # Intent-based routing
├── autonomy/         # Phase 5-7: Autonomous operations
│   ├── models.py     # Core data structures
│   ├── trigger_engine.py
│   ├── task_engine.py
│   ├── preparation.py
│   ├── execution.py
│   ├── governance.py
│   └── learning.py
├── connectors/       # Phase 8: External integrations
│   ├── base.py       # Connector interface
│   ├── webhook.py
│   └── slack.py
├── execution/        # Phase 8: Action fabric
│   ├── action_fabric.py
│   ├── provenance.py
│   └── circuit_breaker.py
├── workflows/        # Phase 8: Workflow execution
│   └── execution_engine.py
└── tests/            # Comprehensive test suite
```

### Testing Strategy

- **Unit Tests:** Model validation, business logic
- **Integration Tests:** Multi-component interactions
- **End-to-End Tests:** Complete workflows

**Total Test Coverage:** 197+ tests across all phases

---

## Performance Considerations

### Scalability
- Async I/O throughout
- Connection pooling for databases
- Circuit breakers prevent cascading failures
- Idempotency enables safe retries

### Cost Management
- Quota enforcement per workspace
- Token usage tracking
- Rate limiting on external APIs
- Circuit breaking prevents runaway costs

### Reliability
- Circuit breakers isolate failures
- Retry logic with exponential backoff
- Health monitoring for connectors
- Provenance tracking for debugging

---

## Compliance & Auditing

### SOC2 Readiness
- Complete audit trails
- Immutable action records
- Multi-factor authentication support
- Role-based access control
- Change management logging

### Data Residency
- Workspace-based data isolation
- Environment segregation (dev/staging/prod)
- Scoped credentials per workspace

---

## Future Roadmap

### Near Term
- Additional connectors (Jira, GitHub, AWS, etc.)
- Enhanced workflow builder UI
- Real-time execution monitoring
- Advanced analytics dashboard

### Long Term
- AI-powered workflow generation
- Predictive scaling recommendations
- Multi-region deployment
- Advanced threat detection

---

## Contributing

See `CONTRIBUTING.md` for:
- Development setup
- Code style guidelines
- Pull request process
- Test requirements

---

## License

MIT License - See `LICENSE` for details.
