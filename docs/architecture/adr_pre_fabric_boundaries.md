# Architecture Decision Record: Pre-Fabric Boundary Hardening
## ADR-011: Establishing Domain Boundaries Before Distributed Intelligence

---

## Metadata

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-011 |
| **Status** | Proposed |
| **Date** | 2025-03-11 |
| **Context** | Post-Layer 10, Pre-Layer 11 |
| **Related PRDs** | PRD-011-PRE |

---

## Context

TORQ Console has completed 10 layers of intelligence capabilities:

1. Core Foundation (L1)
2. Mission Execution Engine (L2)
3. Mission Memory System (L3)
4. Workflow Orchestration (L4)
5. Knowledge Management (L5)
6. Human-Machine Interface (L6)
7. Operator Control Surface (L7)
8. Autonomous Intelligence (L8)
9. Organizational Intelligence (L9)
10. Strategic Simulation (L10)

As we approach Layer 11 (Distributed Intelligence Fabric), we face a critical architectural inflection point. The system is now powerful enough that:
- Cross-domain dependencies are becoming implicit
- State boundaries are becoming blurred
- Governance enforcement is becoming centralized
- Federation requirements are becoming urgent

**Risk**: Without explicit boundary establishment now, Layer 11 would require painful retrofitting.

---

## Decision

We will implement **Pre-Fabric Boundary Hardening** before Layer 11 development begins.

This establishes:
1. **Canonical Service Contracts** - Every domain has a stable, versioned contract
2. **Intelligence Artifact Standard** - All outputs follow a standard shape
3. **Event Taxonomy** - Formal event model prevents mixed-state pipelines
4. **Policy Scope Model** - Every policy declares its scope explicitly
5. **Identity and Boundary Model** - Every action answers who, what, where, when, how

---

## Drivers

### Positive Drivers

- **Layer 11 Readiness**: Distributed intelligence requires clean boundaries
- **Federation Requirements**: Cross-node sharing needs explicit contracts
- **Operational Safety**: State separation prevents contamination
- **Development Velocity**: Clean contracts enable parallel development
- **Testing**: Bounded domains are easier to test in isolation

### Negative Drivers

- **Development Overhead**: Contract establishment takes time
- **Migration Effort**: Existing code must conform to new boundaries
- **Complexity**: Additional abstraction layers add complexity
- **Performance**: Boundary enforcement may add latency

---

## Alternatives Considered

### Alternative 1: Defer Boundaries Until Layer 11

**Approach**: Build Layer 11 first, refactor boundaries as needed

**Pros**:
- Faster initial Layer 11 progress
- Boundaries informed by actual distributed requirements

**Cons**:
- Risk of major Layer 11 rework
- Tight coupling becomes harder to untangle
- State contamination may occur before detection
- **Rejected**: Higher long-term cost

### Alternative 2: Full Microservices Decomposition

**Approach**: Break each domain into separate deployable service

**Pros**:
- Maximum isolation
- Independent scaling
- Clear failure boundaries

**Cons**:
- Significant operational overhead
- Increased deployment complexity
- Over-engineered for current scale
- **Rejected**: Too much overhead at this stage

### Alternative 3: Minimal Boundary Addition

**Approach**: Add only federation-related boundaries

**Pros**:
- Minimal changes
- Fastest implementation

**Cons**:
- Doesn't address internal coupling
- State contamination risk remains
- Governance remains centralized
- **Rejected**: Incomplete solution

### Alternative 4: Pre-Fabric Boundary Hardening (SELECTED)

**Approach**: Establish all boundaries without full decomposition

**Pros**:
- Enables clean Layer 11 implementation
- Addresses all identified risks
- Maintains monolithic deployment (simpler ops)
- Clear migration path to future microservices if needed

**Cons**:
- 1-2 week implementation time
- Requires existing code changes

**Selected**: Best balance of risk mitigation and implementation cost

---

## Decision Details

### 1. Service Contract Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                     Contract Registry                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Execution Contract  │  Memory Contract  │  Insight Contract   │
│  ├─ input_schema     │  ├─ input_schema  │  ├─ input_schema    │
│  ├─ output_schema    │  ├─ output_schema │  ├─ output_schema   │
│  └─ dependencies     │  └─ dependencies  │  └─ dependencies    │
│                                                                  │
│  Pattern Contract   │  Governance       │  Simulation          │
│  ├─ input_schema     │  ├─ input_schema  │  ├─ input_schema    │
│  ├─ output_schema    │  ├─ output_schema │  ├─ output_schema   │
│  └─ dependencies     │  └─ dependencies  │  └─ dependencies    │
│                                                                  │
│  Organizational     │  Audit            │  Federation          │
│  ├─ input_schema     │  ├─ input_schema  │  ├─ input_schema    │
│  ├─ output_schema    │  ├─ output_schema │  ├─ output_schema   │
│  └─ dependencies     │  └─ dependencies  │  └─ dependencies    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2. State Boundary Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      State Boundaries                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │   OPERATIONAL    │    │    STRATEGIC     │                  │
│  │                  │    │                  │                  │
│  │  • Live missions │    │  • Simulations   │                  │
│  │  • Active memory │    │  • Forecasts     │                  │
│  │  • Real decisions│    │  • Scenarios     │                  │
│  │                  │    │  • What-ifs      │                  │
│  └──────────────────┘    └──────────────────┘                  │
│           │                         │                           │
│           │                         │                           │
│           ▼                         ▼                           │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │    ANALYTICAL    │    │     ARCHIVAL     │                  │
│  │                  │    │                  │                  │
│  │  • Patterns      │    │  • Audit trails  │                  │
│  │  • Insights      │    │  • Decisions     │                  │
│  │  • Anomalies     │    │  • Outcomes      │                  │
│  │                  │    │  • Compliance    │                  │
│  └──────────────────┘    └──────────────────┘                  │
│                                                                  │
│  Rule: Operational state can ONLY be modified by               │
│  ExecutionMode.LIVE actions within the same boundary.          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Domain Interaction Rules

| Source Domain | Target Domain | Allowed? | Promotion Required? |
|---------------|---------------|----------|---------------------|
| Operational | Operational | ✅ Yes | No |
| Operational | Strategic | ❌ No | N/A |
| Operational | Analytical | ✅ Yes | No |
| Operational | Archival | ✅ Yes | No |
| Strategic | Operational | ❌ No | Yes (explicit) |
| Strategic | Strategic | ✅ Yes | No |
| Strategic | Analytical | ✅ Yes | No |
| Strategic | Archival | ✅ Yes | No |
| Analytical | Operational | ❌ No | Yes (explicit) |
| Analytical | Strategic | ✅ Yes | No |
| Analytical | Analytical | ✅ Yes | No |
| Analytical | Archival | ✅ Yes | No |

### 4. Federation Export Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   Federation Export Flow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. ARTIFACT CREATION                                           │
│     └── Service emits IntelligenceArtifact                      │
│         └── federation_eligible = bool                           │
│                                                                  │
│  2. REDACTION                                                   │
│     └── Apply RedactionPolicy                                   │
│         ├── Remove: secrets, internal IDs, private data         │
│         └── Keep: aggregates, patterns, insights                │
│                                                                  │
│  3. EXPORT CONTRACT                                             │
│     └── Create FederationExportContract                         │
│         ├── artifact_metadata                                   │
│         ├── redacted_fields                                     │
│         ├── target_nodes                                        │
│         └── governance_tags                                     │
│                                                                  │
│  4. VALIDATION                                                  │
│     ├── Source node authorization                               │
│     ├── Contract integrity                                      │
│     ├── Redaction compliance                                    │
│     └── Governance tag requirements                             │
│                                                                  │
│  5. EXPORT                                                      │
│     └── Send to target nodes / federation                       │
│                                                                  │
│  6. IMPORT (Receiving Side)                                     │
│     ├── Validate import contract                                │
│     ├── Apply to local insights (NOT operational)               │
│     └── Audit import                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Strategy

### Phase 1: Contract Foundation
- Create contract module
- Implement ContractRegistry
- Define 9 domain contracts
- Validate contract dependencies

### Phase 2: Artifact Standard
- Create artifact module
- Implement IntelligenceArtifact
- Create domain-specific factories
- Validate artifact lineage

### Phase 3: Event Taxonomy
- Create event module
- Implement TorqEvent base
- Create domain emitters
- Validate event classification

### Phase 4: Policy Scopes
- Create scope module
- Implement PolicyScope
- Define scope templates
- Validate policy portability

### Phase 5: State Boundaries
- Create boundary module
- Implement StateBoundaryEnforcer
- Create promotion workflows
- Validate state separation

### Phase 6: Integration
- Comprehensive validation
- Federation tests
- Architecture compliance

---

## Consequences

### Positive Consequences

1. **Clean Layer 11 Foundation**
   - Federation becomes straightforward
   - Node communication is governed by contracts
   - State isolation is guaranteed

2. **Improved Testability**
   - Each domain can be tested in isolation
   - Mock contracts enable fast unit tests
   - Integration tests use real contracts

3. **Better Governance**
   - Policies travel as metadata
   - Scope boundaries are explicit
   - Authority is delegatable

4. **Operational Safety**
   - State contamination is architecturally impossible
   - Simulation cannot affect production
   - Audit trail is complete

5. **Future Flexibility**
   - Can evolve to microservices if needed
   - Contracts enable independent versioning
   - Federation is additive, not disruptive

### Negative Consequences

1. **Implementation Effort**
   - 1-2 weeks of focused work
   - Existing code must conform to boundaries
   - Some refactoring required

2. **Short-term Complexity**
   - Additional abstraction layers
   - More explicit contract definitions
   - Learning curve for new patterns

3. **Performance Overhead**
   - Boundary validation adds latency
   - Artifact creation overhead
   - Contract resolution cost

### Mitigation Strategies

- **Performance**: Cache validation results, use async checks
- **Complexity**: Provide clear documentation and examples
- **Migration**: Gradual adoption with adapter layers

---

## Validation Criteria

### Contract Validation
- [ ] All 9 domains have registered contracts
- [ ] Contract dependencies are explicit
- [ ] Contract versioning is enforced

### Artifact Validation
- [ ] All intelligence outputs use standard artifact
- [ ] Artifact lineage is trackable
- [ ] Federation eligibility is correctly flagged

### Event Validation
- [ ] All events have category and execution mode
- [ ] Event chains are traceable
- [ ] No mixed-state events

### Policy Validation
- [ ] All policies have declared scope
- [ ] Policy references are portable
- [ ] No hardcoded policies

### State Validation
- [ ] Operational and strategic state are separated
- [ ] Simulation cannot write to operational state
- [ ] All cross-boundary writes are audited

### Federation Validation
- [ ] Export contracts are enforced
- [ ] Redaction policies are applied
- [ ] Federated data never becomes operational

---

## Status

**Status**: **Proposed**

**Next Steps**:
1. Review and approve this ADR
2. Review and approve PRD-011-PRE
3. Begin Phase 1 implementation

**Timeline**: 1-2 weeks

**Blocks**: Layer 11 implementation cannot begin until this is complete.

---

**Document Version**: 1.0
**Last Updated**: 2025-03-11
**Authors**: TORQ Architecture Team
