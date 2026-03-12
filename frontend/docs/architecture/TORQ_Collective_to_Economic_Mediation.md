# TORQ Console
# Collective to Economic Mediation Architecture

**Document Location:** docs/architecture/TORQ_Collective_to_Economic_Mediation.md
**Purpose:** Defines critical separation between collective intelligence exchange (L12) and economic/resource optimization (L13)
**Status:** Design Constraint — Must be implemented before Layer 12 activation

---

# 1. The Critical Separation

## Core Principle

**Collective intelligence is epistemic. Economic intelligence is allocative. Those are not the same thing.**

Collective intelligence answers: *What do we know?*
Economic intelligence answers: *Where do we put effort?*

If combined too early, the system allocates resources based on partially validated shared knowledge, then reinforces that knowledge with more resources — creating dangerous feedback loops.

---

# 2. The Forbidden Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 12: Collective Intelligence Exchange                      │
│   - Insights shared across nodes                              │
│   - Patterns distributed                                       │
│   - Benchmarks published                                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 13: Economic Intelligence                                │
│   - Routing by cost                                            │
│   - Model selection by spend                                    │
│   - ROI-based prioritization                                   │
│   - Throughput optimization                                     │
└─────────────────────────────────────────────────────────────┘
```

**This architecture is FORBIDDEN.**

It allows federated intelligence to directly drive allocation without mediation, creating the following failure modes:

1. **Local truth overwritten** — Global optimization drowns out context-specific knowledge
2. **Legibility over truth** — System selects for what scores easily, not what's true
3. **Hidden control surface** — Shared intelligence becomes de facto policy without governance
4. **Incentive loops** — System optimizes for adoption/adaptability rather than validity

---

# 3. The Required Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 12: Collective Intelligence Exchange                      │
│   - Insights shared across nodes                              │
│   - Patterns distributed                                       │
│   - Benchmarks published                                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│     Collective Intelligence Qualification Layer                 │
│                                                               │
│   Evaluates federated artifacts along:                       │
│   - Transferability (can this move safely?)                 │
│   - Context Dependency (when is it valid?)                   │
│   - Governance Compatibility (policy fit?)                    │
│   - Economic Safety (does allocation create bias?)            │
│   - Confidence Stability (is this robust?)                    │
│                                                               │
│   Produces classification:                                    │
│   - Informational (awareness only)                            │
│   - Advisory (inform decisions, no direct action)              │
│   - Allocative-Eligible (may influence routing)               │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│     Governance Review / Policy Mediation                        │
│                                                               │
│   - Governance scope checks                                  │
│   - Authority validation                                      │
│   - Simulation testing (local fit verification)               │
│   - Policy compliance                                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 13: Economic Intelligence                                │
│   - Routing by cost                                            │
│   - Model selection by spend                                    │
│   - ROI-based prioritization                                   │
│   - Throughput optimization                                     │
│                                                               │
│   ONLY consumes artifacts marked: allocative-eligible        │
└─────────────────────────────────────────────────────────────┘
```

---

# 4. Artifact Qualification Categories

Every federated intelligence artifact must be classified:

## Category A — Informational

**Use**: Awareness, dashboards, planning
**Cannot**: Directly influence decisions or routing

**Examples**:
- Benchmark summaries
- Observational trends
- Cross-node statistics

## Category B — Advisory

**Use**: Inform local decisions
**Cannot**: Directly influence routing or allocation without local governance review

**Examples**:
- Shared playbooks
- Cross-node patterns
- Strategic lessons
- Best practices

## Category C — Allocative-Eligible

**Use**: May influence economic optimization
**Requires**: Qualification + Governance + Simulation

**Examples**:
- Validated cross-node cost/performance models
- Policy-cleared routing recommendations
- Simulation-tested resource allocations

---

# 5. The Qualification Process

### 5.1 Transferability Assessment

```typescript
interface TransferabilityCheck {
  canMoveAcrossNodes: boolean;
  requiresContext: string[];
  localAdaptationRequired: boolean;
  riskLevel: 'low' | 'medium' | 'high';
}
```

### 5.2 Context Dependency Documentation

```typescript
interface ContextDependency {
  validDomains: string[];
  validAgentTypes: string[];
  validMissionTypes: string[];
  requiredConditions: string[];
  knownLimitations: string[];
}
```

### 5.3 Governance Compatibility Check

```typescript
interface GovernanceCheck {
  compatibleWith: string[];  // Policy IDs
  conflictsWith: string[];    // Policy IDs
  requiresApproval: boolean;
  authorityLevel: 'node' | 'region' | 'network';
}
```

### 5.4 Economic Safety Evaluation

```typescript
interface EconomicSafety {
  createsBias: boolean;
  underinvestmentRisk: string[];
  monocultureRisk: boolean;
  feedbackLoopRisk: boolean;
}
```

---

# 6. Input Boundary Rules

### 6.1 What Layer 13 MAY Consume

Only artifacts that have passed:

```typescript
{
  qualification: {
    transferability: 'high',
    contextDependency: 'documented',
    governanceCheck: 'passed',
    economicSafety: 'safe'
  },
  category: 'allocative-eligible',
  governanceApproval: {
    approvedBy: string,
    approvedAt: number,
    scope: string
  },
  simulationResults: {
    localFitTest: 'passed',
    confidence: number
  }
}
```

### 6.2 What Layer 13 MUST NOT Directly Consume

Raw outputs from:
- Shared insight registries
- Federated pattern stores
- Cross-node leaderboards
- Benchmark rankings
- Artifact reuse scores

These may inform dashboards, planners, or simulations, but NOT drive allocation directly.

---

# 7. The Golden Rule

## Rule Statement

**No federated intelligence artifact may directly influence routing, prioritization, or resource allocation unless it has passed qualification, governance scoping, and local simulation.**

---

# 8. Implementation Requirements

### 8.1 Qualification Layer Service

```typescript
class CollectiveIntelligenceQualifier {
  async qualifyArtifact(
    artifact: FederatedArtifact
  ): Promise<QualificationResult> {
    // 1. Transferability check
    // 2. Context dependency documentation
    // 3. Governance compatibility check
    // 4. Economic safety evaluation
    // 5. Category determination
  }
}
```

### 8.2 Artifact Metadata Requirements

Every federated artifact MUST include:

```typescript
interface FederatedArtifactMetadata {
  // Core content
  content: ArtifactContent;

  // Provenance
  sourceNode: string;
  sourceLayer: number;
  publishedAt: number;

  // Validation (required for allocative-eligible)
  validation?: {
    transferability: TransferabilityCheck;
    governanceCheck: GovernanceCheck;
    economicSafety: EconomicSafety;
    simulationResults?: SimulationResults;
  };

  // Classification
  category: 'informational' | 'advisory' | 'allocative-eligible';
}
```

### 8.3 Economic Service Constraints

```typescript
class EconomicOptimizer {
  async optimizeAllocation(
    resources: Resources,
    options: AllocationOption[]
  ): Promise<AllocationPlan> {

    // Filter to only allocative-eligible artifacts
    const eligibleOptions = options.filter(
      opt => opt.artifact.category === 'allocative-eligible'
        && opt.artifact.validation?.economicSafety?.createsBias === false
    );

    // Must respect governance scopes
    return this.planWithinGovernance(eligibleOptions);
  }
}
```

---

# 9. Failure Mode Comparison

## 9.1 Without Mediation (The Mistake)

```
Node publishes pattern
    ↓
Network sees success
    ↓
Pattern gets high score
    ↓
Economic layer routes more work through it
    ↓
More data reinforces pattern
    ↓
Alternatives starve
    ↓
Local nuance disappears
    ↓
Hidden policy emerges
```

**Result**: Brittle, monocultural intelligence

## 9.2 With Mediation (Correct)

```
Node publishes pattern
    ↓
Collective exchange distributes artifact
    ↓
Receiving node qualifies artifact
    ↓
Governance checks allowed use
    ↓
Simulation tests local fit
    ↓
Only then may economic layer consider it
    ↓
Allocation remains bounded and explainable
```

**Result**: Governed adaptation

---

# 10. Testing Requirements

### 10.1 Qualification Layer Tests

```typescript
describe('Collective Intelligence Qualification', () => {
  test('should reject artifacts without context documentation', async () => {
    const artifact = createTestArtifact();
    delete artifact.metadata.contextDependency;

    const result = await qualifier.qualifyArtifact(artifact);

    expect(result.category).toBe('informational');
    expect(result.canInfluenceAllocation).toBe(false);
  });

  test('should detect economic safety risks', async () => {
    const artifact = createTestArtifact();
    artifact.content.biasSignal = 'strong';

    const result = await qualifier.qualifyArtifact(artifact);

    expect(result.economicSafety.createsBias).toBe(true);
    expect(result.category).not.toBe('allocative-eligible');
  });
});
```

### 10.2 Economic Service Input Validation

```typescript
describe('Economic Intelligence', () => {
  test('should only consume allocative-eligible artifacts', async () => {
    const advisoryArtifact = createArtifact({ category: 'advisory' });
    const allocativeArtifact = createArtifact({
      category: 'allocative-eligible',
      validation: { economicSafety: { createsBias: false } }
    });

    const plan = await economicOptimizer.optimizeAllocation(resources, [
      { artifact: advisoryArtifact, score: 0.9 },
      { artifact: allocativeArtifact, score: 0.7 }
    ]);

    // Only allocative-eligible should influence plan
    expect(plan.consideredArtifacts).not.toContain(advisoryArtifact.id);
    expect(plan.consideredArtifacts).toContain(allocativeArtifact.id);
  });
});
```

---

# 11. Monitoring and Alerting

### 11.1 Metrics to Track

| Metric | Purpose | Alert Threshold |
|--------|---------|----------------|
| `allocation_from_unqualified` | Direct economic use of unqualified artifacts | > 0 |
| `category_c_drift` | Advisory artifacts being used as allocative | > 5% |
| `bias_signal_strength` | Detection of reinforcing loops | Increasing trend |
| `local_truth_suppression` | Context-valid knowledge being overlooked | Regional variance |

### 11.2 Governance Alerts

Alert conditions:
- Economic layer consuming informational artifacts directly
- Qualification layer bypassed or disabled
- Governance checks consistently skipped
- Local simulation testing not performed

---

# 12. Phase-In Strategy

### Phase 1: Qualification Layer (Before L12 Activation)

1. Implement `CollectiveIntelligenceQualifier` service
2. Add artifact metadata requirements
3. Establish category classification
4. Create governance review interfaces

### Phase 2: Economic Layer Isolation (L13 Initial)

1. Implement `EconomicOptimizer` with input filtering
2. Add governance scope enforcement
3. Create simulation testing framework
4. Monitor category usage patterns

### Phase 3: Full Mediation (L12-L13 Integration)

1. Enable full qualification pipeline
2. Implement adaptive qualification thresholds
3. Add feedback loop detection
4. Create intervention controls

---

# 13. Design Principles

### 13.1 Separation of Concerns

- Epistemic intelligence (what we know) is separate from allocative intelligence (what we prioritize)
- Neither should dominate the other
- Governance mediates between them

### 13.2 Progressive Validation

- Information → Advisory → Allocative progression
- Each step requires additional validation
- Regression is prevented by category barriers

### 13.3 Local Autonomy

- Nodes retain authority over local decisions
- Federated intelligence informs but doesn't command
- Economic optimization respects local governance

### 13.4 Explainability

- Every allocation decision must be traceable to qualified inputs
- Hidden control surfaces are explicitly forbidden
- Audit trails must preserve mediation steps

---

# 14. Relationship to Other Architectural Constraints

This mediation layer enforces several architectural principles from `TORQ_Master_Architecture.md`:

| Principle | Enforcement |
|-----------|--------------|
| **Boundary Discipline** | Qualification checks prevent state contamination |
| **Governance First** | Governance review precedes economic use |
| **Layered Intelligence** | Higher layers cannot bypass lower-layer validation |

---

# 15. Summary

The Layer 12-13 transition is a critical architectural threshold. The mistake of letting collective intelligence and economic optimization merge too early causes:

1. **Local truth suppression** by global optimization
2. **Legibility selection** over truth
3. **Hidden policy emergence** from shared intelligence
4. **Incentive gaming** instead of intelligence accumulation

**The Solution**: A qualification and mediation layer between collective intelligence exchange and economic optimization that:
- Classifies artifacts by their safe-use category
- Validates transferability, context, and governance fit
- Requires simulation testing before allocative use
- Preserves local autonomy and explainability

**The Golden Rule**: No federated intelligence artifact may directly influence routing, prioritization, or resource allocation unless it has passed qualification, governance scoping, and local simulation.

This constraint must be implemented before Layer 12 becomes active.

---

**End of Document**
