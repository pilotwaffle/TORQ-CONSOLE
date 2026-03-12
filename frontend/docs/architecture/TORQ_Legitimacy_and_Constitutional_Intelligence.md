# TORQ Console
# Legitimacy and Constitutional Intelligence Architecture

**Document Location:** docs/architecture/TORQ_Legitimacy_and_Constitutional_Intelligence.md
**Purpose:** Defines Layer 14 — how TORQ exercises authority legitimately rather than merely correctly
**Status:** Design Specification for Layer 14 Implementation
**Companion:** TORQ_Federated_Epistemology.md (L12), TORQ_Collective_to_Economic_Mediation.md (L12→L13)

---

# 1. The Legitimacy Problem

## 1.1 What Is Legitimacy?

A system has a **legitimacy problem** when it can make, shape, or constrain decisions, but it is no longer clear:

- **Why it has that authority**
- **Who granted it**
- **Within what limits**
- **How that authority can be challenged, overridden, or revoked**

This is the moment where an AI system stops being "just software" and starts acting like an **institution**.

## 1.2 Why Legitimacy Appears at Layer 14

By the time TORQ reaches Layer 14, it will already have:

- Distributed intelligence exchange (L12)
- Strategic simulation (L10)
- Readiness governance (L6)
- Economic optimization (L13)
- Operator oversight (L7)
- Federated learning across nodes

At that point TORQ will not merely recommend. It will increasingly:

- Prioritize work
- Shape routing
- Influence resource allocation
- Elevate or suppress strategic options
- Determine when conditions are "ready"
- Propagate qualified knowledge across nodes

That means TORQ begins to exercise **practical authority**.

**The legitimacy problem**: What makes that authority acceptable, bounded, and contestable?

## 1.3 Why Governance Is Not Enough

Most AI systems stop at governance. They ask:

```
Did the system follow the rules?
```

Legitimacy asks a deeper question:

```
Did the system have the right to act this way at all?
```

That distinction is why Layer 14 exists at all.

| Dimension | Governance (L6) | Legitimacy (L14) |
|-----------|----------------|------------------|
| Question | "Was this allowed?" | "Was this authorized?" |
| Focus | Rule compliance | Authority source |
| Failure mode | Rule violation | Illegitimate authority |
| Remedy | Fix rules | Clarify delegation |

## 1.4 What Goes Wrong Without Legitimacy Design

### Hidden Authority

The system starts acting like policy without formally being policy.

**Example**: A routing recommendation becomes the default behavior everywhere because it scores well, even though nobody explicitly approved it as institutional policy.

### Delegation Ambiguity

Humans assume TORQ "owns" a decision, while TORQ assumes it is "just advising."

**Result**: No one clearly owns responsibility when something goes wrong.

### Procedural Opacity

The system makes high-impact recommendations or decisions, but people cannot answer:

- What rule allowed this?
- Which authority tier approved this?
- What alternatives were considered?
- How do we challenge it?

### Governance Drift

Over time, optimization, shared patterns, and operator habits become de facto law without ever being reviewed as law.

That is how institutions quietly lose control of their own systems.

---

# 2. Constitutional Principles

Before describing services, we must define the **non-negotiable rules** TORQ will operate under.

These principles act like constitutional law for the system.

## 2.1 Constitutional Principle 1 — Authority Must Be Explicit

**Rule**: No action may become institutionally binding without a declared authority source.

**Anti-Pattern**: Recommendations become defaults through repeated adoption.

**Enforcement**: Every institutionally binding action must cite its authority source.

## 2.2 Constitutional Principle 2 — Authority Must Be Scoped

**Rule**: Every TORQ action must declare its scope.

**Valid Scopes**:

```typescript
type AuthorityScope =
  | "informational"           // Awareness only, no action permitted
  | "advisory"                // May inform decisions, not drive them
  | "local_execution"         // Can execute within bounded local context
  | "cross_node_influence"    // Can affect other nodes through federation
  | "network_impact"          // Affects entire TORQ network
  | "emergency";              // Crisis authority, time-limited
```

**Anti-Pattern**: Advisory patterns driving routing decisions directly.

**Enforcement**: Scope checks before every action.

## 2.3 Constitutional Principle 3 — Authority Must Be Contestable

**Rule**: Every decision must have an override path.

**Requirements**:

- Clear override mechanism
- Defined who may override
- Time window for challenge
- Escalation path for disputes

**Anti-Pattern**: Unchallengeable automated decisions.

**Enforcement**: Contestability metadata required for all high-impact actions.

## 2.4 Constitutional Principle 4 — Authority Must Be Auditable

**Rule**: All actions invoking authority must produce a legitimacy audit record.

**Required Fields**:

- Authority source
- Scope invoked
- Procedural steps taken
- Approving authority
- Override path available
- Timestamp and lineage

**Anti-Pattern**: Authority exercised without traceable provenance.

**Enforcement**: Audit records generated atomically with actions.

## 2.5 Constitutional Principle 5 — Authority Must Be Temporary Unless Ratified

**Rule**: Emergency or temporary authority expires automatically unless explicitly renewed.

**Anti-Pattern**: Crisis measures becoming permanent policy.

**Enforcement**: Time-bound authority with explicit ratification requirement.

## 2.6 Constitutional Principle 6 — State Boundaries Are Absolute

**Rule**: Operational state cannot be federated or shared, regardless of authority level.

**Anti-Pattern**: High authority being used to bypass data boundary rules.

**Enforcement**: Boundary checks override all other authority claims.

---

# 3. Four Dimensions of Legitimacy

Legitimacy is not a single property. It has four dimensions that must all be satisfied for an action to be institutionally legitimate.

## 3.1 Source Legitimacy

**Question**: Where does this authority come from?

**Valid Sources**:

- Human operator delegation
- Organizational policy
- Constitutional rule
- Regional/node governance charter
- Approved simulation/policy framework
- Emergency escalation (time-limited)

**Every meaningful TORQ action should trace back to one of these.**

## 3.2 Scope Legitimacy

**Question**: What is TORQ allowed to do in this context?

**Valid Scopes**:

| Scope | Description | Example |
|-------|-------------|---------|
| Informational | Awareness only | Dashboard displays |
| Advisory | Inform decisions | Playbooks and insights |
| Local Execution | Constrained local action | Single-node routing |
| Cross-Node Influence | Affect other nodes | Federated insight sharing |
| Network Impact | Affects entire network | Resource reallocation |
| Emergency | Crisis authority | Incident response |

**Authority must always be scoped, never implied.**

## 3.3 Procedural Legitimacy

**Question**: Was the decision made through an acceptable process?

**Required Elements**:

- Correct policy checks
- Correct authority tier invoked
- Correct simulation or validation requirements
- Correct audit trail
- Correct review path

**A procedurally legitimate action follows the right process even if the outcome is wrong.**

## 3.4 Contestability Legitimacy

**Question**: Can the decision be questioned, overridden, or appealed?

**Required Elements**:

- Clear override mechanism
- Defined who may override
- Time window for challenge
- Escalation path for disputes
- Record of challenges and resolutions

**If not contestable, the system becomes institutionally dangerous.**

## 3.5 Legitimacy Dimensions Table

| Dimension | Key Question | Failure Example |
|-----------|--------------|-----------------|
| Source | Who granted this authority? | Default behavior with no delegator |
| Scope | What actions are allowed? | Advisory pattern driving routing |
| Procedural | Was the correct process followed? | High-impact action skips simulation |
| Contestability | Can this be challenged? | No override path exists |

---

# 4. Governance vs. Legitimacy (Layer 6 vs. Layer 14)

This distinction is critical for understanding why Layer 14 exists at all.

## 4.1 Layer 6: Readiness Governance

**Function**: Rule compliance and readiness scoring

**Questions**:
- Is this action permitted by policy?
- Does the mission meet readiness thresholds?
- Are required approvals in place?

**Example**:
```
Action allowed because readiness rule R-105 passed.
```

## 4.2 Layer 14: Constitutional Legitimacy

**Function**: Authority source validation and decision legitimacy

**Questions**:
- Does TORQ have the right to act this way at all?
- Who granted that authority?
- Within what scope?
- How do we challenge it?

**Example**:
```
Action allowed because operator delegation O-42 granted local-execution
scope for routing decisions in the financial-planning domain.
```

## 4.3 Comparison Table

| Dimension | Layer 6 (Governance) | Layer 14 (Legitimacy) |
|-----------|----------------------|----------------------|
| Focus | Rule compliance | Authority source |
| Question | "Was this allowed?" | "Was this authorized?" |
| Failure mode | Rule violation | Illegitimate authority |
| Remedy | Fix rules | Clarify delegation |
| Scope | Single node | Institutional |
| Time horizon | Immediate | Long-term constitutional |

## 4.4 Why Both Are Needed

A system can be well-governed but illegitimate:

```
The system followed every rule perfectly.
But it was never granted the authority to make those decisions at all.
```

A system can be legitimate but poorly governed:

```
The system had full authority to act.
But it violated its own procedural rules in doing so.
```

TORQ needs both.

---

# 5. Authority Model

Layer 14 must define **authority tiers**. Without this, the legitimacy model remains abstract.

## 5.1 Authority Tiers

```typescript
type AuthorityTier =
  | "operator"        // Individual operator authority
  | "node"            // Node-level authority
  | "regional"        // Multi-node regional authority
  | "network"         // TORQ network-wide authority
  | "constitutional"; // Non-overridable constitutional authority
```

## 5.2 Tier Definitions

### Operator Authority

**Scope**: Single operator, bounded context

**Can Delegate**:
- Local execution permissions
- Advisory scope for specific domains
- Temporary emergency measures

**Cannot Delegate**:
- Cross-node authority
- Network impact authority
- Constitutional rule changes

**Example**: Operator grants TORQ permission to auto-route within a specific mission type.

### Node Authority

**Scope**: Single TORQ node

**Can Delegate**:
- Node-level policy
- Local execution defaults
- Node operator permissions

**Cannot Delegate**:
- Regional or network authority
- Constitutional interpretations

**Example**: Node policy allows advisory patterns to inform routing decisions locally.

### Regional Authority

**Scope**: Multi-node region

**Can Delegate**:
- Regional policy harmonization
- Cross-node federation rules
- Regional emergency authority

**Cannot Delegate**:
- Network-wide defaults
- Constitutional changes

**Example**: Regional authority allows federated insights to be shared across nodes in the region.

### Network Authority

**Scope**: Entire TORQ network

**Can Delegate**:
- Network-wide defaults
- Cross-regional federation
- Network emergency protocols

**Cannot Delegate**:
- Constitutional rule changes

**Example**: Network authority defines which insight types are allocative-eligible.

### Constitutional Authority

**Scope**: Non-overridable

**Cannot Be Delegated**: Only explicitly amended through constitutional process

**Includes**:
- State boundary rules
- Contestability requirements
- Audit requirements
- Authority source requirements

**Example**: Constitutional rule that no operational state may be federated.

## 5.3 Delegation Rules

```typescript
interface Delegation {
  delegatingTier: AuthorityTier;
  receivingTier: AuthorityTier;
  scope: AuthorityScope;
  domain?: string;
  conditions: Condition[];
  expiresAt?: number;
  revocable: boolean;
  ratificationRequired?: boolean;
}
```

**Rules**:

- Lower tiers cannot delegate to higher tiers
- Emergency authority expires unless ratified
- All delegation is revocable
- Delegation outside tier bounds requires constitutional amendment

---

# 6. Layer 14 Architecture

Layer 14 consists of six core services that together form the **constitutional infrastructure**.

## 6.1 Constitution Engine

**Purpose**: Stores and enforces constitutional rules

**Responsibilities**:
- Maintain canonical constitution
- Validate actions against constitutional principles
- Detect constitutional conflicts
- Manage constitutional amendment process

**Key Interface**:

```typescript
class ConstitutionEngine {
  async validateAction(action: Action): Promise<ConstitutionalCheck>;
  async getConstitutionalRules(): Promise<ConstitutionalRule[]>;
  async proposeAmendment(amendment: Amendment): Promise<AmendmentStatus>;
}
```

**Critical Property**: Constitutional rules override all other authority claims.

## 6.2 Authority Boundary Manager

**Purpose**: Determines whether a requested action is within scope

**Responsibilities**:
- Validate action scope against granted authority
- Check tier boundaries
- Enforce domain constraints
- Detect scope creep

**Key Interface**:

```typescript
class AuthorityBoundaryManager {
  async checkScope(action: Action, grantedAuthority: GrantedAuthority): Promise<ScopeCheck>;
  async validateTier(delegation: Delegation): Promise<TierValidation>;
  async detectScopeCreep(actionHistory: Action[]): Promise<ScopeCreepWarning[]>;
}
```

**Critical Property**: Actions outside granted scope are illegitimate, regardless of outcome quality.

## 6.3 Delegation Registry

**Purpose**: Tracks who delegated authority and under what conditions

**Responsibilities**:
- Record all delegations
- Validate delegation chains
- Track expiry and revocation
- Maintain delegation lineage

**Key Interface**:

```typescript
class DelegationRegistry {
  async grantDelegation(delegation: Delegation): Promise<DelegationRecord>;
  async validateDelegationChain(action: Action): Promise<ChainValidation>;
  async revokeDelegation(delegationId: string): Promise<RevocationRecord>;
  async checkExpiry(): Promise<ExpiredDelegation[]>;
}
```

**Critical Property**: All authority must be traceable to a delegating source.

## 6.4 Legitimacy Evaluator

**Purpose**: Validates whether a decision invocation is legitimate

**Responsibilities**:
- Evaluate all four legitimacy dimensions
- Generate legitimacy scores
- Flag illegitimate actions
- Recommend contestability paths

**Key Interface**:

```typescript
class LegitimacyEvaluator {
  async evaluateLegitimacy(action: Action): Promise<LegitimacyAssessment>;
  async checkSourceLegitimacy(action: Action): Promise<SourceLegitimacy>;
  async checkScopeLegitimacy(action: Action): Promise<ScopeLegitimacy>;
  async checkProceduralLegitimacy(action: Action): Promise<ProceduralLegitimacy>;
  async checkContestability(action: Action): Promise<ContestabilityAssessment>;
}
```

**Critical Property**: An action must pass all four dimensions to be legitimate.

## 6.5 Escalation Law

**Purpose**: Defines when TORQ must defer or escalate

**Responsibilities**:
- Define escalation triggers
- Route disputes to correct tier
- Manage emergency authority transitions
- Enforce escalation time limits

**Key Interface**:

```typescript
class EscalationLaw {
  async shouldEscalate(action: Action): Promise<EscalationDecision>;
  async routeDispute(dispute: Dispute): Promise<DisputeRoute>;
  async manageEmergencyTransition(emergency: Emergency): Promise<TransitionPlan>;
}
```

**Escalation Triggers**:
- Cross-node conflicts
- Constitutional ambiguity
- High-impact resource reallocation
- Policy contradiction
- Unresolved legitimacy dispute

## 6.6 Institutional Audit Service

**Purpose**: Maintains legitimacy trace records

**Responsibilities**:
- Generate legitimacy records for all high-impact actions
- Preserve authority lineage
- Enable retrospective legitimacy audits
- Support accountability investigations

**Key Interface**:

```typescript
class InstitutionalAuditService {
  async recordLegitimacy(action: Action, assessment: LegitimacyAssessment): Promise<void>;
  async queryLegitimacyRecord(actionId: string): Promise<LegitimacyRecord>;
  async auditAuthorityUsage(tier: AuthorityTier, timeRange: TimeRange): Promise<AuthorityAudit>;
}
```

**Critical Property**: Every high-impact action produces an immutable legitimacy record.

---

# 7. The Golden Rule of Legitimacy

## 7.1 The Rule

**No TORQ action may become institutionally binding unless its authority source, scope, procedural compliance, and contestability path are explicitly defined.**

## 7.2 What This Prevents

- Hidden authority emerging from optimization
- Advisory patterns becoming defaults
- Network-wide behavior without explicit delegation
- Unchallengeable automated decisions
- Authority exercised without audit trail

## 7.3 The Legitimacy Checklist

Before any institutionally binding action, the system must verify:

```typescript
interface LegitimacyChecklist {
  // Source
  authoritySource: string;           // Who granted authority?
  authorityTier: AuthorityTier;      // At what level?

  // Scope
  authorityScope: AuthorityScope;    // What actions allowed?
  domain: string;                    // In what domain?

  // Procedural
  policyChecksPassed: string[];      // Which policies satisfied?
  simulationRequired: boolean;       // Was simulation run?
  simulationPassed: boolean;

  // Contestability
  overridePath: string;              // How to challenge?
  overrideWindow: number;            // How long to challenge?
  escalationPath: string;            // Where to escalate dispute?

  // Audit
  auditRecordId: string;             // Where is this recorded?
}
```

**If any field is missing, the action is illegitimate.**

---

# 8. Failure Modes & Anti-Patterns

## 8.1 Hidden Authority

**Description**: Patterns become defaults without explicit delegation.

**How It Happens**:
- High-scoring recommendations get widely adopted
- Repeated use creates expectation
- No explicit delegation ever occurred

**Prevention**:
- Explicit scope declarations
- Adoption requires delegation
- Scope creep detection

## 8.2 Delegation Ambiguity

**Description**: Humans assume TORQ owns decisions while TORQ assumes it is advisory.

**How It Happens**:
- Authority not clearly specified
- Scope boundaries fuzzy
- No clear ownership statement

**Prevention**:
- Explicit authority scope on every action
- Clear advisory vs. execution distinction
- Ownership metadata required

## 8.3 Procedural Opacity

**Description**: High-impact decisions cannot be explained.

**How It Happens**:
- Missing audit trail
- No procedural documentation
- Authority lineage lost

**Prevention**:
- Comprehensive audit records
- Procedural step logging
- Authority lineage preservation

## 8.4 Governance Drift

**Description**: Optimization and habits become policy without review.

**How It Happens**:
- Repeated patterns become expectations
- No formal policy process
- Institutional memory fades

**Prevention**:
- Time-bound authority
- Explicit ratification requirements
- Pattern review before default adoption

## 8.5 Scope Creep

**Description**: Authority slowly expands beyond original delegation.

**How It Happens**:
- Gradual expansion of use cases
- No scope enforcement
- Missing boundary checks

**Prevention**:
- Scope validation on every action
- Automated scope creep detection
- Explicit re-delegation for scope changes

## 8.6 Emergency Entrenchment

**Description**: Crisis measures become permanent policy.

**How It Happens**:
- Emergency authority granted
- Crisis passes but authority remains
- No expiry mechanism

**Prevention**:
- Automatic expiry of emergency authority
- Explicit ratification required
- Sunset clauses built in

---

# 9. Integration with Layers 12–13

Layer 14 does not stand alone. It integrates with the federated epistemology of L12 and the economic mediation of L13.

## 9.1 The Constitutional Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 12: Federated Epistemology                            │
│   - Nodes exchange claims, not truth                         │
│   - Local interpretation required                           │
│   - Allowed-use metadata                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Collective→Economic Mediation                               │
│   - Qualification layer                                     │
│   - Informational / Advisory / Allocative-Eligible          │
│   - Governance review required                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 13: Economic Intelligence                             │
│   - Only consumes allocative-eligible artifacts             │
│   - Cost-aware routing                                      │
│   - ROI-based prioritization                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 14: Constitutional Legitimacy                          │
│   - Authority source validation                             │
│   - Scope boundary enforcement                              │
│   - Contestability requirements                             │
│   - Institutional audit                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    Institutional Action
```

## 9.2 Cross-Layer Constraints

| Layer | Output | Constraint Before L14 |
|-------|--------|----------------------|
| L12 | Epistemic claims | Allowed-use metadata required |
| L12→L13 | Qualification | Only allocative-eligible may pass |
| L13 | Economic decisions | Authority source required |
| L14 | Legitimacy judgment | All four dimensions must pass |

## 9.3 Constitutional Consistency

Layer 14 ensures constitutional rules are respected across all layers:

**State boundaries** (constitutional) override federation preferences (L12)
**Contestability** (constitutional) overrides economic optimization (L13)
**Authority scope** (constitutional) constrains collective intelligence (L12)

---

# 10. Legitimacy Audit Model

Every high-impact action should produce a **Legitimacy Record** that creates institutional memory of authority use.

## 10.1 Legitimacy Record Structure

```typescript
interface LegitimacyRecord {
  // Identity
  recordId: string;
  actionId: string;
  timestamp: number;

  // Authority Source
  authoritySource: {
    tier: AuthorityTier;
    delegatingEntity: string;
    delegationId: string;
    delegationChain: string[];
  };

  // Scope
  authorityScope: {
    scope: AuthorityScope;
    domain: string;
    constraints: string[];
  };

  // Procedural
  proceduralCompliance: {
    policiesChecked: string[];
    policiesPassed: string[];
    policiesFailed: string[];
    simulationRequired: boolean;
    simulationRun: boolean;
    simulationPassed: boolean;
  };

  // Legitimacy Assessment
  legitimacy: {
    sourceLegitimate: boolean;
    scopeLegitimate: boolean;
    procedurallyLegitimate: boolean;
    contestable: boolean;
    overallLegitimate: boolean;
  };

  // Contestability
  contestability: {
    overridePath: string;
    overrideWindow: number;  // milliseconds
    escalationPath: string;
    challenges: Challenge[];
  };

  // Audit Trail
  auditTrail: {
    createdAt: number;
    createdBy: string;
    reviewedBy: string[];
    reviewedAt: number[];
    amendments: Amendment[];
  };
}
```

## 10.2 Audit Query Interface

```typescript
class LegitimacyAuditQuery {
  async getByActionId(actionId: string): Promise<LegitimacyRecord>;
  async getByTimeRange(start: number, end: number): Promise<LegitimacyRecord[]>;
  async getByAuthorityTier(tier: AuthorityTier): Promise<LegitimacyRecord[]>;
  async getIllegitimateActions(): Promise<LegitimacyRecord[]>;
  async getContestedActions(): Promise<LegitimacyRecord[]>;
}
```

## 10.3 Institutional Memory

The legitimacy audit system serves as TORQ's institutional memory:

- **What authority was exercised**: By whom, for what, under what scope
- **What actions were contested**: Challenges, overrides, escalations
- **What patterns emerged**: Scope usage, delegation patterns, procedural compliance

This enables retrospective institutional analysis:

```
"Are we seeing scope creep in routing authority?"
"Which delegations are being challenged most often?"
"Is emergency authority being overused?"
```

---

# 11. Implementation Requirements

## 11.1 Phase 1: Constitutional Foundation

Before Layer 14 activation:

1. Constitution Engine service
2. Authority tier definitions
3. Delegation Registry schema
4. Legitimacy Record structure

## 11.2 Phase 2: Legitimacy Evaluation

After foundation is in place:

1. Legitimacy Evaluator service
2. Authority Boundary Manager
3. Scope validation on all actions
4. Contestability path requirements

## 11.3 Phase 3: Institutional Controls

Full Layer 14 activation:

1. Escalation Law service
2. Institutional Audit service
3. Automated scope creep detection
4. Emergency authority expiry

## 11.4 Integration Points

Layer 14 must integrate with:

- **Layer 6**: Readiness governance provides rule compliance data
- **Layer 7**: Operator Control Plane provides human authority delegation
- **Layer 12**: Federated epistemology provides claim provenance
- **Layer 13**: Economic intelligence provides allocative decisions

---

# 12. Monitoring and Safeguards

## 12.1 Metrics to Track

| Metric | Purpose | Alert Threshold |
|--------|---------|-----------------|
| `illegitimate_action_rate` | Actions without proper authority | > 0% |
| `scope_violation_rate` | Actions outside granted scope | > 0% |
| `uncontested_authority_expansion` | Authority expanding without re-delegation | Any growth |
| `emergency_authority_expiry_rate` | Emergency authority not expiring | Failure to expire |
| `contestability_bypass_rate` | Actions without override path | > 0% |
| `audit_record_gaps` | Actions without legitimacy records | > 0% |

## 12.2 Governance Alerts

Alert conditions:

- Action taken without clear authority source
- Scope violation detected
- Emergency authority not expiring
- Contestability path missing
- Audit record incomplete
- Delegation chain broken

## 12.3 Constitutional Violations

Any violation of constitutional principles must:

1. Block the action immediately
2. Alert operators
3. Create violation record
4. Require explicit override

---

# 13. Testing Requirements

## 13.1 Legitimacy Validation Tests

```typescript
describe('Layer 14 Legitimacy', () => {
  test('should reject action without authority source', async () => {
    const action = createTestAction();
    delete action.authority.source;

    const assessment = await legitimacyEvaluator.evaluate(action);

    expect(assessment.legitimate).toBe(false);
    expect(assessment.failures).toContain('missing_authority_source');
  });

  test('should reject action outside granted scope', async () => {
    const action = createTestAction({ scope: 'network_impact' });
    const authority = createAuthority({ scope: 'advisory' });

    const assessment = await legitimacyEvaluator.evaluate(action, authority);

    expect(assessment.legitimate).toBe(false);
    expect(assessment.failures).toContain('scope_violation');
  });

  test('should require contestability for high-impact actions', async () => {
    const action = createTestAction({ impact: 'high' });
    delete action.contestability.overridePath;

    const assessment = await legitimacyEvaluator.evaluate(action);

    expect(assessment.legitimate).toBe(false);
    expect(assessment.failures).toContain('missing_contestability');
  });

  test('should detect scope creep', async () => {
    const history = createActionHistory([
      { scope: 'advisory', count: 100 },
      { scope: 'local_execution', count: 10 },
      { scope: 'cross_node_influence', count: 1 }  // Outside original delegation
    ]);

    const warnings = await boundaryManager.detectScopeCreep(history);

    expect(warnings).toContainEqual(
      expect.objectContaining({ type: 'scope_expansion_detected' })
    );
  });
});
```

## 13.2 Constitutional Compliance Tests

```typescript
describe('Constitutional Compliance', () => {
  test('should enforce state boundary rules', async () => {
    const action = createFederateStateAction();

    const result = await constitutionEngine.validateAction(action);

    expect(result.compliant).toBe(false);
    expect(result.violatedPrinciple).toBe('state_boundaries_absolute');
  });

  test('should enforce automatic expiry of emergency authority', async () => {
    const emergency = createEmergencyAuthority({ grantedAt: Date.now() - 25 * 60 * 60 * 1000 });  // 25 hours ago

    const valid = await delegationRegistry.checkExpiry(emergency);

    expect(valid).toBe(false);
    expect(emergency.status).toBe('expired');
  });

  test('should require explicit delegation for scope expansion', async () => {
    const currentScope = 'advisory';
    const requestedScope = 'network_impact';

    const result = await delegationRegistry.validateScopeExpansion(
      currentScope,
      requestedScope
    );

    expect(result.allowed).toBe(false);
    expect(result.requires).toContain('explicit_delegation');
  });
});
```

---

# 14. Design Principles

## 14.1 Authority Over Optimization

Legitimacy takes precedence over performance. An effective but illegitimate action is still illegitimate.

## 14.2 Explicit Over Implicit

Authority must be explicitly granted, never assumed. Repeated use does not create authority.

## 14.3 Contestability Over Efficiency

The ability to challenge decisions is more important than decision speed for high-impact actions.

## 14.4 Auditability Over Convenience

Every high-impact action must have a complete legitimacy record, even when inconvenient.

## 14.5 Temporary Over Permanent

Authority should be time-bound by default. Permanent authority requires explicit ratification.

---

# 15. Relationship to Other Architectural Constraints

Layer 14 enforces several architectural principles from across the TORQ architecture:

| Principle | Enforcement |
|-----------|-------------|
| **Boundary Discipline** | State boundaries override all authority claims |
| **Governance First** | Legitimacy precedes economic optimization |
| **Federated Epistemology** | Authority is local, not implied by network adoption |
| **Economic Mediation** | Legitimacy constrains allocative decisions |

---

# 16. Summary

The Legitimacy Problem is the final architectural challenge for TORQ. As the system gains distributed intelligence, economic optimization, and strategic simulation capabilities, it will inevitably exercise practical authority over decisions.

The question is not **"Can TORQ make good decisions?"**

The question is **"Under what authority may TORQ participate in decisions, and how is that authority structured, limited, reviewed, and revoked?"**

Layer 14 provides the answer through:

1. **Constitutional Principles** — Non-negotiable rules about authority
2. **Authority Model** — Clear tiers and delegation rules
3. **Four-Dimensional Legitimacy** — Source, scope, procedural, contestability
4. **Constitutional Infrastructure** — Services that enforce legitimacy
5. **Legitimacy Audit** — Institutional memory of authority use
6. **Golden Rule** — No binding action without explicit authority, scope, procedure, and contestability

This ensures TORQ evolves like this:

```
knowledge → governance → authority → institution
```

Instead of:

```
optimization → influence → hidden authority → institutional crisis
```

---

# 17. The One-Sentence Takeaway

## The Legitimacy Problem

**As TORQ gains the ability to shape real decisions across nodes, it must not only be accurate and governed; it must be constitutionally authorized, procedurally bounded, and contestable.**

---

**End of Document**
