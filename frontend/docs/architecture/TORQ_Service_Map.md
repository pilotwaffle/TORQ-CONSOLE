# TORQ Console
# Service Map

**Document Location:** docs/architecture/TORQ_Service_Map.md
**Purpose:** Maps actual services/modules to their architectural layers
**Companion:** TORQ_Master_Architecture.md (conceptual), TORQ_Data_Flow_Architecture.md (flows)

---

# 1. Overview

This document maps TORQ's **actual code services and modules** to their architectural layers. It serves as:

- A navigation guide for the codebase
- A reference for where new code belongs
- An inventory of implemented vs planned services
- A dependency map between services

---

# 2. Service Layer Map

```
┌─────────────────────────────────────────────────────────────────┐
│ L15  Meta-Strategic Intelligence                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ PLANNED: EvolutionPlanner, StrategicHorizonModeler        │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ L14  Institutional Governance                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ PLANNED: ConstitutionalEngine, AuthorityEscalation        │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ L13  Economic & Resource Intelligence                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ PLANNED: CostTracker, ResourceAllocator, ROIAnalyzer       │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ L12  Collective Intelligence Exchange                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ PLANNED: InsightFederation, PatternExchange              │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ L11  Distributed Intelligence Fabric                              │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✅ NodeCoordinator, FederationRouter, FailoverManager      │ │
│ │ ✅ BoundaryEnforcer, RedactionService                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ L10  Strategic Simulation                                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✅ SimulationEngine, ScenarioBuilder, ForecastingModel    │ │
│ │ ✅ PolicyTesting, RiskModeler                              │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ L9   Organizational Intelligence                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✅ OrgIntelligenceService, CapabilityMapper                │ │
│ │ ✅ BottleneckDetector, TeamTopologyAnalyzer                │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ L8   Autonomous Intelligence                                      │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✅ LearningLoopService, RecommendationEngine               │ │
│ │ ✅ OutcomeAnalyzer, PerformanceOptimizer                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ L7   Operator Control Plane                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✅ ControlService, InterventionManager                     │ │
│ │ ✅ ActionApproval, AuditLogger                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ L6   Readiness Governance                                      │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✅ ReadinessService, PromotionGovernor                      │ │
│ │ ✅ PolicyEnforcer, RuleValidator                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ L5   Pattern Intelligence                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✅ PatternDetector, SignalExtractor                         │
│ │ ✅ RecurringSignalFinder, PredictiveModeler               │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ L4   Insight Intelligence                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✅ InsightService (M1-M4: 55/55 tests passing)             │ │
│ │ ✅ InsightExtractor, InsightValidator, InsightPublisher   │ │
│ │ ✅ ApprovalWorkflow, InsightRetrieval                       │ │
│ │ 🔄 M5: ConcurrentPublication, DuplicateDetection          │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ L3   Governed Strategic Memory                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✅ MemoryService, MemoryValidator                          │ │
│ │ ✅ ProvenanceTracker, FreshnessScorer                       │ │
│ │ ✅ MemoryStore (Supabase integration)                       │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ L2   Artifact Persistence                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✅ ArtifactService, ArtifactStore                          │ │
│ │ ✅ TraceCapture, OutputLogger                             │ │
│ │ ✅ ArtifactIndexer, RetentionPolicy                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ L1   Execution Fabric                                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✅ WorkflowEngine, AgentOrchestrator                       │ │
│ │ ✅ TaskExecutor, ToolRegistry                              │ │
│ │ ✅ ExecutionMonitor, EventStream                          │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

# 3. Service Directory by Layer

## Layer 1: Execution Fabric

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `WorkflowEngine` | `features/workflows/` | ✅ Complete | Orchestrates workflow execution |
| `AgentOrchestrator` | `features/agents/` | ✅ Complete | Coordinates multi-agent execution |
| `TaskExecutor` | `features/tasks/` | ✅ Complete | Executes individual tasks |
| `ToolRegistry` | `lib/tools/` | ✅ Complete | Manages available tools |
| `ExecutionMonitor` | `features/monitoring/` | ✅ Complete | Tracks execution in real-time |
| `EventStream` | `features/events/` | ✅ Complete | Publishes execution events |

## Layer 2: Artifact Persistence

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `ArtifactService` | `services/artifactService.ts` | ✅ Complete | Manages artifact lifecycle |
| `ArtifactStore` | `features/artifacts/` | ✅ Complete | Database persistence layer |
| `TraceCapture` | `features/tracing/` | ✅ Complete | Captures execution traces |
| `OutputLogger` | `features/logging/` | ✅ Complete | Logs agent/task outputs |
| `ArtifactIndexer` | `services/indexing/` | ✅ Complete | Indexes artifacts for retrieval |
| `RetentionPolicy` | `services/retention/` | ✅ Complete | Manages data retention rules |

## Layer 3: Governed Strategic Memory

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `MemoryService` | `services/memoryService.ts` | ✅ Complete | Manages memory lifecycle |
| `MemoryValidator` | `services/memoryValidator.ts` | ✅ Complete | Validates memory candidates |
| `ProvenanceTracker` | `services/provenance/` | ✅ Complete | Tracks data lineage |
| `FreshnessScorer` | `services/freshness/` | ✅ Complete | Calculates memory freshness |
| `MemoryStore` | `lib/supabase/` | ✅ Complete | Supabase-backed storage |

## Layer 4: Insight Intelligence

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `InsightService` | `services/insightService.ts` | ✅ M1-M4 Complete | Core insight management |
| `InsightExtractor` | `services/insightExtractor.ts` | ✅ Complete | Extracts insights from memory |
| `InsightValidator` | `services/insightValidator.ts` | ✅ Complete | Validates insight quality |
| `InsightPublisher` | `services/insightPublisher.ts` | ✅ Complete | Publishes validated insights |
| `ApprovalWorkflow` | `services/approval/` | ✅ Complete | Manages approval process |
| `InsightRetrieval` | `services/insightRetrieval.ts` | ✅ Complete | Context-aware retrieval |

**Milestone Status**:
- ✅ M1: Insight Types, Lifecycle, Publishing Rules
- ✅ M2: Extraction → Validation → Approval → Persistence
- ✅ M3: Context-Aware Retrieval
- ✅ M4: Inspection, Audit, Governance Controls
- 🔄 M5: Concurrent Publication, Duplicate Detection (in progress)

## Layer 5: Pattern Intelligence

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `PatternDetector` | `services/patternDetector.ts` | ✅ Complete | Detects recurring patterns |
| `SignalExtractor` | `services/signals/` | ✅ Complete | Extracts predictive signals |
| `RecurringSignalFinder` | `services/patterns/` | ✅ Complete | Finds signals across missions |
| `PredictiveModeler` | `services/prediction/` | ✅ Complete | Builds predictive models |

## Layer 6: Readiness Governance

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `ReadinessService` | `services/readinessService.ts` | ✅ Complete | Evaluates readiness scores |
| `PromotionGovernor` | `services/promotion/` | ✅ Complete | Controls layer promotions |
| `PolicyEnforcer` | `services/policy/` | ✅ Complete | Enforces governance rules |
| `RuleValidator` | `services/validation/` | ✅ Complete | Validates against rulesets |

## Layer 7: Operator Control Plane

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `ControlService` | `features/control/` | ✅ Complete | Main control surface |
| `InterventionManager` | `features/intervention/` | ✅ Complete | Manages human interventions |
| `ActionApproval` | `features/approval/` | ✅ Complete | Handles action approvals |
| `AuditLogger` | `services/audit/` | ✅ Complete | Logs all actions for audit |

## Layer 8: Autonomous Intelligence

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `LearningLoopService` | `services/learning/` | ✅ Complete | Orchestrates learning cycles |
| `RecommendationEngine` | `services/recommendations/` | ✅ Complete | Generates recommendations |
| `OutcomeAnalyzer` | `services/outcomes/` | ✅ Complete | Analyzes mission outcomes |
| `PerformanceOptimizer` | `services/optimization/` | ✅ Complete | Optimizes system performance |

## Layer 9: Organizational Intelligence

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `OrgIntelligenceService` | `services/orgIntelligence.ts` | ✅ Complete | Analyzes org capability |
| `CapabilityMapper` | `services/capability/` | ✅ Complete | Maps capabilities across teams |
| `BottleneckDetector` | `services/bottlenecks/` | ✅ Complete | Identifies bottlenecks |
| `TeamTopologyAnalyzer` | `services/teams/` | ✅ Complete | Analyzes team structures |

## Layer 10: Strategic Simulation

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `SimulationEngine` | `services/simulation/` | ✅ Complete | Runs strategic simulations |
| `ScenarioBuilder` | `services/scenarios/` | ✅ Complete | Builds simulation scenarios |
| `ForecastingModel` | `services/forecasting/` | ✅ Complete | Creates forecasts |
| `PolicyTesting` | `services/policyTesting/` | ✅ Complete | Tests policy impacts |
| `RiskModeler` | `services/risk/` | ✅ Complete | Models risks and mitigations |

## Layer 11: Distributed Intelligence Fabric

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `NodeCoordinator` | `services/fabric/` | ✅ Complete | Coordinates node activities |
| `FederationRouter` | `services/federation/` | ✅ Complete | Routes federation requests |
| `FailoverManager` | `services/failover/` | ✅ Complete | Manages failover events |
| `BoundaryEnforcer` | `services/boundaries/` | ✅ Complete | Enforces domain boundaries |
| `RedactionService` | `services/redaction/` | ✅ Complete | Redacts sensitive data |

## Layer 12: Collective Intelligence Exchange

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `InsightFederation` | `services/federation/` | 🔄 Planned | Shares insights across nodes |
| `PatternExchange` | `services/exchange/` | 🔄 Planned | Exchanges patterns securely |

## Layer 13: Economic & Resource Intelligence

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `CostTracker` | `services/economics/` | 🔄 Planned | Tracks costs per mission |
| `ResourceAllocator` | `services/resources/` | 🔄 Planned | Optimizes resource allocation |
| `ROIAnalyzer` | `services/roi/` | 🔄 Planned | Analyzes return on investment |

## Layer 14: Institutional Governance

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `ConstitutionalEngine` | `services/constitution/` | 🔄 Planned | Enforces constitutional rules |
| `AuthorityEscalation` | `services/authority/` | 🔄 Planned | Manages authority escalation |

## Layer 15: Meta-Strategic Intelligence

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| `EvolutionPlanner` | `services/evolution/` | 🔄 Planned | Plans system evolution |
| `StrategicHorizonModeler` | `services/strategy/` | 🔄 Planned | Models long-term strategy |

---

# 4. Frontend Module Map

## UI Components by Layer

| Layer | UI Module | Path | Status |
|-------|-----------|------|--------|
| **L1** | Workflow Editor | `features/workflows/components/WorkflowEditor.tsx` | ✅ |
| **L1** | Execution Graph | `features/workflows/components/WorkflowGraphCanvas.tsx` | ✅ |
| **L4** | Insight Explorer | `features/insights/` | 🔄 Planned |
| **L6** | Readiness Dashboard | `features/readiness/` | 🔄 Planned |
| **L7** | Control Surface | `features/control/pages/ControlPage.tsx` | ✅ |
| **L7** | Mission Portfolio | `features/control/pages/MissionPortfolioPage.tsx` | ✅ |
| **L7** | Mission Detail | `features/control/pages/MissionDetailPage.tsx` | ✅ |
| **L9** | Org Dashboard | `features/org/` | 🔄 Planned |
| **L10** | Simulation Workspace | `features/simulation/` | 🔄 Planned |
| **L11** | Fabric Nodes | `features/fabric/pages/FabricNodesPage.tsx` | ✅ |
| **L11** | Failover Management | `features/fabric/pages/FabricFailoverPage.tsx` | ✅ |

## Shared UI Components

| Component | Path | Purpose |
|-----------|------|---------|
| `OperatorShell` | `components/layout/OperatorShell.tsx` | Main app shell (L7) |
| `TopNavigation` | `components/layout/TopNav.tsx` | Top nav bar |
| `SidebarNavigation` | `components/layout/SidebarNavigation.tsx` | Side navigation |
| `TORQLogo` | `components/ui/TorqLogo.tsx` | Branded logo |
| `AgentSidebar` | `components/layout/AgentSidebar.tsx` | Chat agent selector |

---

# 5. Database Schema Map

## Tables by Layer

### Supabase Tables

| Table | Layer | Purpose | Status |
|-------|------|---------|--------|
| `artifacts` | L2 | Raw execution outputs | ✅ |
| `memory` | L3 | Validated knowledge | ✅ |
| `insights` | L4 | Published intelligence | ✅ |
| `patterns` | L5 | Detected patterns | ✅ |
| `readiness_scores` | L6 | Readiness evaluations | ✅ |
| `actions` | L7 | Operator actions | ✅ |
| `learning_events` | L8 | Learning loop logs | ✅ |
| `org_metrics` | L9 | Organizational metrics | ✅ |
| `simulations` | L10 | Simulation runs | ✅ |
| `nodes` | L11 | Fabric node registry | ✅ |
| `failover_events` | L11 | Failover history | ✅ |

---

# 6. API Endpoints by Layer

### Internal API Routes

| Layer | Route | Service | Status |
|-------|-------|---------|--------|
| **L1** | `/api/workflows` | `WorkflowEngine` | ✅ |
| **L1** | `/api/executions` | `ExecutionMonitor` | ✅ |
| **L2** | `/api/artifacts` | `ArtifactService` | ✅ |
| **L3** | `/api/memory` | `MemoryService` | ✅ |
| **L4** | `/api/insights` | `InsightService` | ✅ |
| **L4** | `/api/insights/publish` | `InsightPublisher` | ✅ |
| **L5** | `/api/patterns` | `PatternDetector` | ✅ |
| **L6** | `/api/readiness` | `ReadinessService` | ✅ |
| **L7** | `/api/control` | `ControlService` | ✅ |
| **L7** | `/api/actions` | `ActionApproval` | ✅ |
| **L8** | `/api/learning` | `LearningLoopService` | ✅ |
| **L9** | `/api/org-intelligence` | `OrgIntelligenceService` | ✅ |
| **L10** | `/api/simulation` | `SimulationEngine` | ✅ |
| **L11** | `/api/fabric/nodes` | `NodeCoordinator` | ✅ |
| **L11** | `/api/fabric/failover` | `FailoverManager` | ✅ |

---

# 7. External Integrations

| Service | Layer | Integration | Status |
|---------|------|-------------|--------|
| **Supabase** | L2-L4 | Database, Auth, Storage | ✅ |
| **n8n** | L1 | Workflow execution | ✅ |
| **Vercel** | L11 | Edge deployment | ✅ |
| **Claude API** | L1-L4 | Agent intelligence | ✅ |
| **Marvin 3.0** | L4-L10 | Spec analysis | ✅ |
| **Railway** | L11 | Node deployment | 🔄 Planned |

---

# 8. Service Dependencies

## Dependency Graph (Simplified)

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                         │
│                  (React App / Express API)                    │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
    ┌─────────┐      ┌─────────┐      ┌─────────┐
    │Services │      │ Stores  │      │ Utils   │
    └────┬────┘      └────┬────┘      └─────────┘
         │                │
         ▼                ▼
    ┌────────────────────────────┐
    │     External Services       │
    │  (Supabase, n8n, Claude)    │
    └────────────────────────────┘
```

## Critical Dependencies

| Service | Depends On | Critical For |
|---------|-----------|--------------|
| `InsightService` | `MemoryService`, `PatternDetector` | L4 intelligence |
| `LearningLoopService` | `OutcomeAnalyzer`, `RecommendationEngine` | L8 autonomy |
| `SimulationEngine` | `OrgIntelligenceService`, `ForecastingModel` | L10 strategy |
| `NodeCoordinator` | `FailoverManager`, `FederationRouter` | L11 fabric |
| `ReadinessService` | `PolicyEnforcer`, `RuleValidator` | L6 governance |

---

# 9. Adding New Services

## 9.1 When Adding a Service

1. **Identify the target layer** — Use master architecture to find where it fits
2. **Create the service module** — Place in appropriate directory
3. **Implement interfaces** — Follow layer contracts
4. **Add API routes** — If external access needed
5. **Update this map** — Keep documentation current

## 9.2 Service Template

```typescript
// services/yourService/YourService.ts

import { BaseService } from '../base/BaseService';

export class YourService extends BaseService {
  constructor() {
    super('YourService');
    this.layer = 1; // Set appropriate layer
  }

  async execute(params: YourParams): Promise<YourResult> {
    // Implementation
  }

  async validate(input: any): Promise<boolean> {
    // Validation logic
  }
}
```

---

# 10. Service Health Status

## Health Check Endpoints

| Service | Health Check | Status |
|---------|--------------|--------|
| `WorkflowEngine` | `/api/health/workflows` | ✅ |
| `ArtifactService` | `/api/health/artifacts` | ✅ |
| `MemoryService` | `/api/health/memory` | ✅ |
| `InsightService` | `/api/health/insights` | ✅ |
| `NodeCoordinator` | `/api/health/fabric` | ✅ |

---

# 11. Module Location Index

```
frontend/
├── src/
│   ├── components/           # UI components
│   │   ├── layout/           # Layout components (L7)
│   │   ├── ui/              # Shared UI elements
│   │   └── ...
│   ├── features/            # Feature modules (L1-L11)
│   │   ├── workflows/        # L1: Workflow execution
│   │   ├── agents/          # L1: Agent orchestration
│   │   ├── artifacts/       # L2: Artifact management
│   │   ├── control/         # L7: Operator control
│   │   ├── fabric/          # L11: Distributed fabric
│   │   └── ...
│   ├── services/             # Business logic services
│   │   ├── insightService.ts # L4
│   │   ├── memoryService.ts  # L3
│   │   ├── patternDetector.ts # L5
│   │   └── ...
│   ├── stores/              # State management
│   ├── lib/                  # Core utilities
│   │   ├── supabase/        # Database client
│   │   └── tools/           # Tool definitions
│   └── types/               # TypeScript types
└── docs/
    └── architecture/        # This directory
        ├── TORQ_Master_Architecture.md
        ├── TORQ_Data_Flow_Architecture.md
        └── TORQ_Service_Map.md
```

---

# 12. Summary

This service map provides:

- **Complete inventory** of all implemented and planned services
- **Layer assignments** for every service
- **Status tracking** for implementation progress
- **Code locations** for easy navigation
- **Dependency mapping** between services
- **API endpoint reference** for external integrators

When adding new functionality, reference this map to:
1. Find the appropriate layer
2. Locate similar services for patterns
3. Understand integration points
4. Maintain architectural consistency

---

**End of Document**
