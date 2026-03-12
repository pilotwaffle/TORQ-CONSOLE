# TORQ Console - Pre-Fabric Boundary Architecture
## Visual Reference for Domain Separation

---

## The 9 Intelligence Domains

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TORQ INTELLIGENCE FABRIC                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                │
│  │   EXECUTION    │  │     MEMORY     │  │    INSIGHT     │                │
│  │     Domain     │  │     Domain     │  │     Domain     │                │
│  │   (L1-L3)      │  │  (L3, L5)      │  │     (L8)       │                │
│  │                │  │                │  │                │                │
│  │ • Missions     │  │ • Artifacts    │  │ • Patterns     │                │
│  │ • Readiness    │  │ • Knowledge    │  │ • Anomalies    │                │
│  │ • Lifecycle    │  │ • Context      │  │ • Discovery    │                │
│  │                │  │                │  │                │                │
│  │ Type: OP       │  │ Type: OP       │  │ Type: ANA      │                │
│  │ Fed:  No       │  │ Fed: Export    │  │ Fed:  Yes      │                │
│  └────────────────┘  └────────────────┘  └────────────────┘                │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                │
│  │    PATTERN     │  │  GOVERNANCE    │  │   ORGANIZATIONAL│                │
│  │     Domain     │  │     Domain     │  │     Domain     │                │
│  │     (L8)       │  │     (L7)       │  │     (L9)       │                │
│  │                │  │                │  │                │                │
│  │ • Learned      │  │ • Policies     │  │ • Aggregation  │                │
│  │ • Models       │  │ • Authority    │  │ • Benchmarks   │                │
│  │ • Recommend.   │  │ • Enforcement  │  │ • Comparison   │                │
│  │                │  │                │  │                │                │
│  │ Type: LEARN    │  │ Type: GOV      │  │ Type: FED      │                │
│  │ Fed: Abstract  │  │ Fed: Metadata  │  │ Fed:  Yes      │                │
│  └────────────────┘  └────────────────┘  └────────────────┘                │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                │
│  │   SIMULATION   │  │     AUDIT      │  │  FEDERATION    │                │
│  │     Domain     │  │     Domain     │  │     Domain     │                │
│  │    (L10)       │  │    (L10)       │  │    (L11)       │                │
│  │                │  │                │  │                │                │
│  │ • Scenarios    │  │ • Decisions    │  │ • Export       │                │
│  │ • Forecasts    │  │ • Traceability │  │ • Import       │                │
│  │ • Calibration  │  │ • Compliance   │  │ • Sync         │                │
│  │                │  │                │  │                │                │
│  │ Type: STRAT    │  │ Type: ARCH     │  │ Type: DIST     │                │
│  │ Fed:  No       │  │ Fed: Redacted  │  │ Fed:  Yes      │                │
│  └────────────────┘  └────────────────┘  └────────────────┘                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

Legend:
  OP    = Operational (live mission state)
  ANA   = Analytical (insights and patterns)
  LEARN = Learned (machine learning outputs)
  GOV   = Governing (policy enforcement)
  FED   = Federated (cross-node sharing)
  STRAT = Strategic (simulation and planning)
  ARCH  = Archival (audit and records)
  DIST  = Distributed (node-to-node communication)
```

---

## State Boundary Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STATE BOUNDARIES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         OPERATIONAL STATE                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │   Missions  │  │   Memory    │  │  Readiness  │                 │   │
│  │  │             │  │             │  │             │                 │   │
│  │  │ • Active    │  │ • Context   │  │ • Status    │                 │   │
│  │  │ • Pending   │  │ • History   │  │ • Metrics   │                 │   │
│  │  │ • Complete  │  │ • Artifacts │  │ • Health    │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    │ PRODUCES                               │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        ANALYTICAL STATE                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │   Patterns  │  │   Insights  │  │  Anomalies  │                 │   │
│  │  │             │  │             │  │             │                 │   │
│  │  │ • Learned   │  │ • Derived   │  │ • Detected  │                 │   │
│  │  │ • Models    │  │ • Mined     │  │ • Alerts    │                 │   │
│  │  │ • Rules     │  │ • Stats     │  │ • Scores    │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    │ INFORMS (BUT CANNOT MODIFY)           │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        STRATEGIC STATE                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │ Simulations │  │  Forecasts  │  │  Scenarios  │                 │   │
│  │  │             │  │             │  │             │                 │   │
│  │  │ • Virtual   │  │ • Predicted │  │ • What-ifs  │                 │   │
│  │  │ • Isolated  │  │ • Trends    │  │ • Models    │                 │   │
│  │  │ • Monte C.  │  │ • Bands     │  │ • Params    │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  │                                                                      │   │
│  │  ⚠️  CANNOT WRITE TO OPERATIONAL STATE WITHOUT EXPLICIT PROMOTION   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    │ CAPTURED BY                            │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         ARCHIVAL STATE                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │    Audit    │  │  Decisions  │  │ Outcomes    │                 │   │
│  │  │             │  │             │  │             │                 │   │
│  │  │ • Trails    │  │ • Records   │  │ • Actual    │                 │   │
│  │  │ • Logs      │  │ • Rationale │  │ • Results   │                 │   │
│  │  │ • Compliance│  │ • Approval  │  │ • Calibration│                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

CRITICAL RULES:
  1. STRATEGIC state can NEVER write directly to OPERATIONAL state
  2. SIMULATION execution mode is isolated from LIVE execution mode
  3. State promotion requires explicit approval workflow
  4. All cross-boundary writes are audited
```

---

## Federation Export Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FEDERATION EXPORT FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  LOCAL NODE                                                           │   │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                         STEP 1: CREATE                            │    │
│  │  ┌─────────────────────────────────────────────────────────┐      │    │
│  │  │ IntelligenceArtifact                                      │      │    │
│  │  │  • artifact_id: uuid                                      │      │    │
│  │  │  • artifact_type: BENCHMARK_SUMMARY                        │      │    │
│  │  │  • content: {statistics, sample_size, ...}                │      │    │
│  │  │  • federation_eligible: true                               │      │    │
│  │  │  • scope: ORGANIZATION                                     │      │    │
│  │  │  • visibility: FEDERATED                                   │      │    │
│  │  └─────────────────────────────────────────────────────────┘      │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                      STEP 2: REDACT                               │    │
│  │  ┌─────────────────────────────────────────────────────────┐      │    │
│  │  │ RedactionPolicy.STANDARD                                  │      │    │
│  │  │  • Remove: *_id, workspace_*, secrets                     │      │    │
│  │  │  • Keep: aggregates, patterns, statistics                 │      │    │
│  │  │  • Transform: user_id → hash(user_id)                     │      │    │
│  │  └─────────────────────────────────────────────────────────┘      │    │
│  │                                                                   │    │
│  │  BEFORE: {mission_id: "123", workspace: "prod", ...}             │    │
│  │  AFTER:  {mission_id: "***", workspace: "***", ...}              │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                    STEP 3: CREATE CONTRACT                        │    │
│  │  ┌─────────────────────────────────────────────────────────┐      │    │
│  │  │ FederationExportContract                                   │      │    │
│  │  │  • export_id: uuid                                         │      │    │
│  │  │  • source_node: "torq-node-1"                              │      │    │
│  │  │  • source_artifact_id: uuid                                │      │    │
│  │  │  • artifact_metadata: {...}                                │      │    │
│  │  │  • redacted_fields: [mission_id, workspace, secrets]       │      │    │
│  │  │  • target_nodes: ["torq-node-2", "torq-node-3"]            │      │    │
│  │  │  • governance_tags: ["benchmark", "duration", "public"]    │      │    │
│  │  └─────────────────────────────────────────────────────────┘      │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                      STEP 4: VALIDATE                             │    │
│  │  ✓ Source node authorized?                                       │    │
│  │  ✓ Contract signature valid?                                     │    │
│  │  ✓ Redaction policy applied?                                     │    │
│  │  ✓ Governance tags present?                                      │    │
│  │  ✓ Content schema valid?                                         │    │
│  │  ✓ TTL within limits?                                            │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│                              ═════════════════════════════════════════════│
│                                                                              │
│  REMOTE NODES                                                    │   │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                      STEP 5: RECEIVE                              │    │
│  │  ┌─────────────────────────────────────────────────────────┐      │    │
│  │  │ FederationImportValidator.validate()                      │      │    │
│  │  │  → Verifies contract                                       │      │    │
│  │  │  → Checks source authorization                             │      │    │
│  │  │  → Validates redaction compliance                          │      │    │
│  │  │  → Confirms governance tags                                │      │    │
│  │  └─────────────────────────────────────────────────────────┘      │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                      STEP 6: APPLY                                │    │
│  │  ┌─────────────────────────────────────────────────────────┐      │    │
│  │  │ Federated Intelligence (Local)                            │      │    │
│  │  │  • Available for: INSIGHT, PATTERN domains               │      │    │
│  │  │  • NOT available for: EXECUTION, MEMORY (operational)    │      │    │
│  │  │  • Used as: Reference data, comparison baselines         │      │    │
│  │  └─────────────────────────────────────────────────────────┘      │    │
│  │                                                                   │    │
│  │  ⚠️  FEDERATED DATA NEVER BECOMES LOCAL OPERATIONAL STATE      │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Contract Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONTRACT DEPENDENCY GRAPH                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                    ┌──────────────────────┐                                 │
│                    │  EXECUTION CONTRACT  │                                 │
│                    │  • MissionRequest    │                                 │
│                    │  • MissionResult     │                                 │
│                    └──────────┬───────────┘                                 │
│                               │                                             │
│                               │ produces                                    │
│                               ▼                                             │
│                    ┌──────────────────────┐                                 │
│                    │    MEMORY CONTRACT    │                                 │
│                    │  • MemoryEntry       │                                 │
│                    │  • KnowledgeArtifact  │                                 │
│                    └──────────┬───────────┘                                 │
│                               │                                             │
│                               │ feeds                                       │
│                               ▼                                             │
│         ┌─────────────────────┼─────────────────────┐                       │
│         │                     │                     │                       │
│         ▼                     ▼                     ▼                       │
│  ┌──────────┐          ┌──────────┐          ┌──────────┐                  │
│  │ INSIGHT  │          │ PATTERN  │          │    ORG   │                  │
│  │          │          │          │          │          │                  │
│  │ consumed │          │ consumed │          │ consumed │                  │
│  │ by       │          │ by       │          │ by       │                  │
│  │          │          │          │          │          │                  │
│  └────┬─────┘          └────┬─────┘          └────┬─────┘                  │
│       │                     │                     │                         │
│       └─────────────────────┼─────────────────────┘                         │
│                             │                                               │
│                             │ informs                                       │
│                             ▼                                               │
│                    ┌──────────────────────┐                                 │
│                    │   SIMULATION CONTRACT │                                 │
│                    │  • ScenarioRequest    │                                 │
│                    │  • SimulationResult   │                                 │
│                    └──────────┬───────────┘                                 │
│                               │                                             │
│                               │ captured by                                 │
│                               ▼                                             │
│                    ┌──────────────────────┐                                 │
│                    │     AUDIT CONTRACT    │                                 │
│                    │  • DecisionRecord     │                                 │
│                    │  • AuditTrail         │                                 │
│                    └──────────┬───────────┘                                 │
│                               │                                             │
│                               │ exportable (redacted)                       │
│                               ▼                                             │
│                    ┌──────────────────────┐                                 │
│                    │  FEDERATION CONTRACT  │                                 │
│                    │  • ExportContract     │                                 │
│                    │  • ImportContract     │                                 │
│                    └──────────────────────┘                                 │
│                                                                              │
│                    ┌──────────────────────┐                                 │
│                    │  GOVERNANCE CONTRACT  │◄──────────┐                    │
│                    │  • PolicyQuery        │           │                    │
│                    │  • GovernanceDecision │           │ applies to        │
│                    └──────────────────────┘           │ all domains        │
│                                                     │                    │
│                                                     │                    │
│                                    All contracts are versioned and       │
│                                    registered in the Contract Registry  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Policy Scope Examples

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POLICY SCOPE EXAMPLES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SCOPE 1: LOCAL_RUNTIME                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ spatial_boundaries:   [SINGLE_NODE]                                  │   │
│  │ execution_modes:      [LIVE]                                         │   │
│  │ applicable_domains:   [EXECUTION, MEMORY]                            │   │
│  │ minimum_authority:    OPERATOR                                       │   │
│  │ federation_exportable: false                                         │   │
│  │                                                                       │   │
│  │ Example: "Only operators can start missions on this node"            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  SCOPE 2: SIMULATION_ONLY                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ spatial_boundaries:   [SINGLE_NODE]                                  │   │
│  │ execution_modes:      [SIMULATED]                                    │   │
│  │ applicable_domains:   [SIMULATION]                                   │   │
│  │ minimum_authority:    None (anyone can simulate)                     │   │
│  │ federation_exportable: false                                         │   │
│  │                                                                       │   │
│  │ Example: "Anyone can run policy simulations"                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  SCOPE 3: ORGANIZATIONAL                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ spatial_boundaries:   [ORGANIZATION]                                 │   │
│  │ execution_modes:      [LIVE]                                         │   │
│  │ applicable_domains:   [EXECUTION, MEMORY, INSIGHT, PATTERN]         │   │
│  │ minimum_authority:    MANAGER                                        │   │
│  │ federation_exportable: false                                         │   │
│  │                                                                       │   │
│  │ Example: "Managers can view all organization patterns"               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  SCOPE 4: FEDERATION_EXPORT                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ spatial_boundaries:   [FEDERATION]                                   │   │
│  │ execution_modes:      [LIVE]                                         │   │
│  │ applicable_domains:   [FEDERATION]                                   │   │
│  │ minimum_authority:    ADMINISTRATOR                                  │   │
│  │ federation_exportable: true                                          │   │
│  │                                                                       │   │
│  │ Example: "Administrators can export benchmark summaries"             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  SCOPE 5: SYSTEM_WIDE                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ spatial_boundaries:   [SYSTEM_WIDE]                                  │   │
│  │ execution_modes:      [LIVE, SIMULATED]                              │   │
│  │ applicable_domains:   [ALL_DOMAINS]                                  │   │
│  │ minimum_authority:    ADMINISTRATOR                                  │   │
│  │ federation_exportable: false (policy metadata only)                  │   │
│  │                                                                       │   │
│  │ Example: "Administrators can enforce governance across all domains"  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Artifact Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARTIFACT LIFECYCLE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. CREATION                                                                 │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │ Service emits IntelligenceArtifact                               │     │
│     │  • artifact_id: auto-generated UUID                              │     │
│     │  • origin_service: "pattern_service"                             │     │
│     │  • origin_domain: ServiceDomain.PATTERN                          │     │
│     │  • content: {...}                                                │     │
│     │  • confidence: 0.85                                              │     │
│     │  • scope: ArtifactScope.ORGANIZATION                             │     │
│     │  • federation_eligible: true                                     │     │
│     │  • reproducibility_metadata: {model_version, data_hash...}       │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                    │                                        │
│                                    ▼                                        │
│  2. VALIDATION                                                               │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │ ArtifactValidator.validate()                                     │     │
│     │  ✓ Required fields present                                       │     │
│     │  ✓ Confidence in [0, 1]                                          │     │
│     │  ✓ Scope is valid                                               │     │
│     │  ✓ Lineage references resolve                                   │     │
│     │  ✓ Governance tags present if required                           │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                    │                                        │
│                                    ▼                                        │
│  3. STORAGE                                                                  │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │ ArtifactStore.save()                                             │     │
│     │  • Persist to domain-specific storage                            │     │
│     │  • Index by: artifact_id, type, scope, timestamp                │     │
│     │  • Create lineage graph                                          │     │
│     │  • Apply retention policy                                        │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                    │                                        │
│                                    ▼                                        │
│  4. CONSUMPTION                                                              │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │ Consumer service loads via Contract                              │     │
│     │  • Validate contract compatibility                              │     │
│     │  • Check consumer permissions                                    │     │
│     │  • Log consumption for traceability                              │     │
│     │  • Update usage metrics                                          │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                    │                                        │
│                                    ▼                                        │
│  5. FEDERATION (if eligible)                                               │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │ FederationService.export()                                       │     │
│     │  • Apply RedactionPolicy                                         │     │
│     │  • Create FederationExportContract                               │     │
│     │  • Send to target nodes                                          │     │
│     │  • Log export event                                              │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                    │                                        │
│                                    ▼                                        │
│  6. ARCHIVAL                                                                │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │ ArchiveManager.maybe_archive()                                   │     │
│     │  • Check TTL/expiration                                         │     │
│     │  • Move to cold storage if expired                              │     │
│     │  • Apply retention policy (keep vs delete)                      │     │
│     │  • Update archive index                                         │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         ARTIFACT LINEAGE                           │   │
│  │                                                                     │   │
│  │  Mission Artifact (execution)                                       │   │
│  │         │                                                           │   │
│  │         └──► Memory Entry (memory)                                  │   │
│  │                   │                                                 │   │
│  │                   └──► Pattern Discovery (insight)                  │   │
│  │                             │                                       │   │
│  │                             └──► Learned Pattern (pattern)          │   │
│  │                                       │                             │   │
│  │                                       └──► Recommendation (pattern)  │   │
│  │                                                 │                   │   │
│  │                                                 └──► [FEDERATION]   │   │
│  │                                                                     │   │
│  │  Every artifact tracks its source_artifact_ids for full lineage   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## State Promotion Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        STATE PROMOTION FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SCENARIO: Promoting a simulated policy change to operational               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ STEP 1: RUN SIMULATION                                               │   │
│  │  ┌─────────────────────────────────────────────────────────────┐     │   │
│  │  │ Simulation Service                                            │     │   │
│  │  │  • Execute scenario with proposed policy                      │     │   │
│  │  │  • Generate SimulationResult artifact                         │     │   │
│  │  │  • Scope: SIMULATION_ONLY                                     │     │   │
│  │  │  • Cannot affect OPERATIONAL state                            │     │   │
│  │  └─────────────────────────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ STEP 2: CREATE DECISION RECORD                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────┐     │   │
│  │  │ Decision Audit Service                                        │     │   │
│  │  │  • Record simulation results                                   │     │   │
│  │  │  • Record operator rationale                                   │     │   │
│  │  │  • Attach simulation artifacts                                 │     │   │
│  │  │  • Status: PENDING_APPROVAL                                    │     │   │
│  │  └─────────────────────────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ STEP 3: REQUEST PROMOTION                                            │   │
│  │  ┌─────────────────────────────────────────────────────────────┐     │   │
│  │  │ StateBoundaryEnforcer.request_promotion()                      │     │   │
│  │  │  • Validate promotion is allowed                              │     │   │
│  │  │  • Check required authority                                    │     │   │
│  │  │  • Create promotion request                                    │     │   │
│  │  └─────────────────────────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ STEP 4: AUTHORIZATION                                                │   │
│  │  ┌─────────────────────────────────────────────────────────────┐     │   │
│  │  │ Approval Workflow                                              │     │   │
│  │  │  • Required authority: ADMINISTRATOR                           │     │   │
│  │  │  • Review simulation results                                   │     │   │
│  │  │  • Confirm risk assessment                                    │     │   │
│  │  │  • Approve or reject                                           │     │   │
│  │  └─────────────────────────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ STEP 5: PROMOTE (if approved)                                        │   │
│  │  ┌─────────────────────────────────────────────────────────────┐     │   │
│  │  │ StateBoundaryEnforcer.promote_state()                         │     │   │
│  │  │  • Create OPERATIONAL state artifact                          │     │
│  │  │  • Link to SIMULATION artifact for traceability               │     │   │
│  │  │  • Apply cooling-off period if configured                      │     │   │
│  │  │  • Record promotion in audit trail                             │     │   │
│  │  │  • Update Governance Service with new policy                  │     │   │
│  │  └─────────────────────────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ STEP 6: MONITOR & CALIBRATE                                          │   │
│  │  ┌─────────────────────────────────────────────────────────────┐     │   │
│  │  │ Calibration Engine                                             │     │   │
│  │  │  • Monitor actual outcomes vs predicted                        │     │   │
│  │  │  • Record forecast errors                                      │     │   │
│  │  │  • Update calibration parameters                               │     │   │
│  │  │  • Feed back into future simulations                           │     │   │
│  │  └─────────────────────────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ⚠️  CRITICAL: Without this explicit promotion flow,                       │
│     simulated changes could accidentally affect production.                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Document Version**: 1.0
**Last Updated**: 2025-03-11
**Related**: PRD-011-PRE, ADR-011
