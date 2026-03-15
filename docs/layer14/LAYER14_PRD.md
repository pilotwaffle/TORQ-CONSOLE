# Layer 14 PRD - Constitutional Governance
## Product Requirements Document

**Version:** 0.14.0-planning
**Status:** DRAFT
**Author:** Agent 2
**Date:** 2026-03-14

---

## Executive Summary

Layer 14 introduces **constitutional governance** to the TORQ system, transforming it from a coordinated intelligence system into a **self-governing AI infrastructure**. This layer provides legitimacy checking, authority boundary enforcement, and immutable audit logging for all system decisions.

### Purpose

To ensure that TORQ's distributed intelligence operates within defined constitutional constraints, preventing:
- Self-approval and concentration of power
- Authority boundary violations
- Economic override attempts
- Plurality suppression (collapsing disagreement)
- System capture by single agents

### Position in Architecture

```
L1-L11:  Execution Fabric
L12:     Collective Intelligence Exchange
L13:     Economic Intelligence
L14:     Constitutional Governance ← NEW
```

**Decision Flow:**
```
Layer 13: Economic Prioritization
         ↓
Layer 14: Legitimacy Check ← INTERCEPT HERE
         ↓
Layer 6-11: Execution (if legitimate)
```

---

## Governance Principles

### GP-1: No Self-Approval

**Rule:** An agent cannot approve its own proposal or decision.

**Rationale:** Prevents concentration of power and ensures distributed oversight.

**Implementation:**
- Decision ID includes proposing agent ID
- Approval agent ID must differ from proposing agent ID
- Violation results in automatic rejection

### GP-2: Economic Budgets Must Be Respected

**Rule:** Layer 13 economic decisions cannot be overridden or bypassed.

**Rationale:** Economic constraints are fundamental to resource allocation fairness.

**Implementation:**
- Legitimacy score penalty for budget violations
- Execution blocked if budget not approved by Layer 13
- Override attempts logged as constitutional violations

### GP-3: Plurality Must Be Preserved

**Rule:** Disagreement and conflicting claims must not be artificially suppressed.

**Rationale:** Intelligence emerges from diversity of opinion and federated reasoning.

**Implementation:**
- Federation layer must surface conflicting claims
- Attempting to remove conflict flagged as violation
- Plurality index monitored and protected

### GP-4: Authority Boundaries Must Be Enforced

**Rule:** Agents cannot operate outside their defined authority domain.

**Rationale:** Prevents scope creep and maintains system stability.

**Implementation:**
- Each agent has defined authority scope
- Actions outside scope automatically blocked
- Authority changes require constitutional amendment

### GP-5: Governance Audit Must Be Immutable

**Rule:** All governance events must be logged in an immutable audit trail.

**Rationale:** Ensures accountability and prevents retrospective tampering.

**Implementation:**
- Append-only governance audit ledger
- Cryptographic hashing of records
- Records signed by governing authority

---

## Core Components

### C1: ConstitutionalFrameworkEngine

**Purpose:** Load and evaluate constitutional rules.

**Responsibilities:**
- Maintain current constitution (rule set)
- Evaluate decisions against rules
- Detect rule violations
- Return compliance verdict

**Interface:**
```python
class ConstitutionalFrameworkEngine:
    async def evaluate_decision(
        self,
        decision: DecisionPacket
    ) -> ConstitutionEvaluation:
        """Evaluate a decision against constitutional rules."""
        pass
```

**Output Model:**
```python
class ConstitutionEvaluation(BaseModel):
    compliant: bool
    violated_rules: list[str]
    warnings: list[str]
    rule_scores: dict[str, float]  # rule_id -> compliance_score
```

### C2: AuthorityBoundaryEnforcer

**Purpose:** Enforce agent authority limits.

**Responsibilities:**
- Define authority scopes for each agent type
- Check if action is within agent's authority
- Block unauthorized actions
- Log authority violations

**Interface:**
```python
class AuthorityBoundaryEnforcer:
    def check_authority(
        self,
        agent_id: str,
        action: ActionType
    ) -> AuthorityCheck:
        """Check if agent has authority for action."""
        pass
```

**Output Model:**
```python
class AuthorityCheck(BaseModel):
    authorized: bool
    reason: str | None
    required_scope: str | None
```

**Authority Scope Examples:**
| Agent Type | Can Approve | Cannot Approve |
|------------|-------------|----------------|
| Planner | Execution plans | Resource allocations |
| Executor | Task execution | Governance rules |
| Economist | Budget decisions | Constitutional amendments |

### C3: LegitimacyScoringEngine

**Purpose:** Compute legitimacy scores for decisions.

**Responsibilities:**
- Calculate multi-dimensional legitimacy score
- Flag decisions below legitimacy threshold
- Provide legitimacy breakdown
- Track legitimacy trends over time

**Interface:**
```python
class LegitimacyScoringEngine:
    async def compute_legitimacy(
        self,
        decision: DecisionPacket,
        constitution_eval: ConstitutionEvaluation,
        authority_check: AuthorityCheck
    ) -> LegitimacyScore:
        """Compute legitimacy score for decision."""
        pass
```

**Output Model:**
```python
class LegitimacyScore(BaseModel):
    decision_id: str
    score: float  # 0.0 to 1.0
    threshold: float  # Minimum for execution
    passes: bool
    breakdown: LegitimacyBreakdown
    warnings: list[str]
    violations: list[str]

class LegitimacyBreakdown(BaseModel):
    rule_compliance: float
    authority_validity: float
    plurality_integrity: float
    economic_respect: float
    audit_completeness: float
```

**Scoring Formula:**
```
legitimacy_score = (
    0.30 * rule_compliance +
    0.25 * authority_validity +
    0.20 * plurality_integrity +
    0.15 * economic_respect +
    0.10 * audit_completeness
)
```

### C4: AuthorityCaptureDetector

**Purpose:** Detect excessive influence concentration.

**Responsibilities:**
- Track decision share by agent
- Track approval share by agent
- Track resource control by agent
- Alert on capture indicators

**Interface:**
```python
class AuthorityCaptureDetector:
    async def analyze_capture(
        self,
        time_window: timedelta
    ) -> CaptureAnalysis:
        """Analyze system for authority capture."""
        pass
```

**Output Model:**
```python
class CaptureAnalysis(BaseModel):
    period_start: datetime
    period_end: datetime
    metrics: CaptureMetrics
    risk_level: CaptureRiskLevel
    warnings: list[str]

class CaptureMetrics(BaseModel):
    decision_share: dict[str, float]  # agent_id -> proportion
    approval_share: dict[str, float]
    resource_control: dict[str, float]
    herfindahl_index: float  # Concentration measure

class CaptureRiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
```

**Capture Indicators:**
| Metric | Low Risk | Moderate Risk | High Risk | Critical |
|--------|----------|---------------|-----------|----------|
| Decision share (top agent) | <30% | 30-50% | 50-70% | >70% |
| Herfindahl index | <0.15 | 0.15-0.25 | 0.25-0.40 | >0.40 |

### C5: GovernanceAuditLedger

**Purpose:** Maintain immutable audit log of governance events.

**Responsibilities:**
- Append-only record of governance events
- Cryptographic integrity verification
- Query interface for audits
- Export capability

**Interface:**
```python
class GovernanceAuditLedger:
    async def record_event(
        self,
        event: GovernanceEvent
    ) -> str:
        """Record event and return record ID."""
        pass

    async def query_events(
        self,
        filter: EventFilter
    ) -> list[GovernanceEvent]:
        """Query events by filter."""
        pass

    async def verify_integrity(
        self
    ) -> IntegrityReport:
        """Verify cryptographic integrity of ledger."""
        pass
```

**Event Model:**
```python
class GovernanceEvent(BaseModel):
    record_id: str
    timestamp: datetime
    event_type: GovernanceEventType
    decision_id: str
    agent_id: str
    legitimacy_score: float | None
    violations: list[str]
    signature: str  # Cryptographic signature
    previous_hash: str  # For chain integrity
    record_hash: str
```

---

## Decision Flow

### Complete Governance Pipeline

```
1. PROPOSAL
   Agent proposes action/decision
   ↓
2. LAYER 13: ECONOMIC EVALUATION
   Budget checked, priorities calculated
   ↓
3. LAYER 14: CONSTITUTIONAL CHECK
   ├─ ConstitutionalFrameworkEngine.evaluate_decision()
   ├─ AuthorityBoundaryEnforcer.check_authority()
   └─ LegitimacyScoringEngine.compute_legitimacy()
   ↓
4. LEGITIMACY VERDICT
   IF score >= threshold:
       → GovernanceAuditLedger.record_event()
       → EXECUTE (Layer 6-11)
   ELSE:
       → REJECT
       → RETURN TO AGENT WITH REASON
```

### Rejection Reasons

| Reason | Source | Action |
|--------|--------|--------|
| Self-approval detected | Constitutional check | Reject, log violation |
| Authority exceeded | Authority check | Reject, log violation |
| Legitimacy too low | Legitimacy scoring | Reject, provide breakdown |
| Budget violated | Economic respect | Reject, refer to Layer 13 |
| Plurality suppressed | Plurality check | Reject, restore conflicts |

---

## Integration with Layer 13

### Economic Respect

Layer 14 must respect Layer 13's economic decisions:

```python
class LegitimacyBreakdown(BaseModel):
    economic_respect: float  # NEW
```

**Economic Respect Calculation:**
```python
def calculate_economic_respect(
    decision: DecisionPacket,
    allocation: AllocationResult
) -> float:
    """Score based on respecting Layer 13 economic output."""

    # Check if decision matches Layer 13 allocation
    if decision.funded_missions != allocation.funded_mission_ids:
        return 0.0  # Complete override

    # Calculate alignment
    funded_aligned = len(
        set(decision.funded_missions) &
        set(allocation.funded_mission_ids)
    )
    alignment = funded_aligned / len(decision.funded_missions)

    return alignment
```

**Violations:**
- Changing funded mission set
- Exceeding allocated budget
- Ignoring priority order without justification

---

## Validation Metrics

### System-Level Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| rule_violation_rate | Decisions violating constitutional rules | <1% |
| authority_distribution_index | Evenness of authority distribution | >0.7 |
| legitimacy_score_average | Mean legitimacy score | >0.85 |
| governance_audit_integrity | Cryptographic verification pass rate | 100% |
| capture_detection_rate | Correct identification of capture attempts | >95% |

### Component-Level Metrics

**ConstitutionalFrameworkEngine:**
- rule_evaluation_latency: <5ms per decision
- rule_coverage: 100% of governance principles

**AuthorityBoundaryEnforcer:**
- authority_check_latency: <2ms per check
- unauthorized_block_rate: 100%

**LegitimacyScoringEngine:**
- scoring_latency: <10ms per decision
- score_distribution: 90% of scores >0.7

**AuthorityCaptureDetector:**
- detection_latency: <100ms for time window
- false_positive_rate: <5%

**GovernanceAuditLedger:**
- write_latency: <5ms per event
- query_latency: <50ms for typical queries
- integrity_verification: 100% pass rate

---

## Failure Modes

### F1: Constitution Unavailable

**Scenario:** ConstitutionalFrameworkEngine cannot load rules.

**Mitigation:**
- Cache last valid constitution
- Fail-open with warnings (allow execution but log)
- Alert operators

### F2: Legitimacy Score Inconclusive

**Scenario:** Cannot compute legitimacy score (missing data).

**Mitigation:**
- Require minimum data completeness
- Fail closed (block execution) if critical data missing
- Return error to proposing agent

### F3: Audit Ledger Compromised

**Scenario:** Cryptographic integrity check fails.

**Mitigation:**
- Immediate system halt
- Alert operators
- Restore from last verified backup
- Investigate tampering

### F4: Authority Definition Missing

**Scenario:** Agent ID not found in authority definitions.

**Mitigation:**
- Default to minimal authority (read-only)
- Log event for review
- Require explicit authority grant

---

## Security Considerations

### SC-1: Constitution Tampering

**Threat:** Unauthorized modification of constitutional rules.

**Mitigation:**
- Constitution stored in immutable storage
- Changes require multi-agent approval
- All changes signed and logged
- Version control with cryptographic verification

### SC-2: Audit Trail Spoofing

**Threat:** Fake governance events inserted into ledger.

**Mitigation:**
- Append-only ledger design
- Each record signed by governing authority
- Chain hashing prevents insertion
- Regular integrity verification

### SC-3: Legitimacy Gaming

**Threat:** Agents manipulate decisions to maximize legitimacy without genuine compliance.

**Mitigation:**
- Multi-dimensional scoring (hard to game all)
- Pattern detection for gaming behavior
- Calibration based on actual outcomes
- Human oversight for critical decisions

### SC-4: Authority Escalation

**Threat:** Agent gradually expands authority through small changes.

**Mitigation:**
- Authority changes require constitutional amendment
- Explicit scope definitions
- Audit of authority usage patterns
- Alerts on scope expansion

---

## Non-Goals

### Out of Scope for Layer 14

1. **Dynamic Constitution Modification** - Constitution changes are manual and require explicit approval
2. **Real-time Governance Learning** - Rules are static, not learned from behavior
3. **Cross-System Governance** - Only governs TORQ, not external systems
4. **Human-in-the-Loop Governance** - Fully automated (human oversight only for audit/alerts)
5. **Dispute Resolution** - Does not mediate agent disagreements (Layer 12)

---

## Dependencies

### Required Layers

- **Layer 12:** Collective Intelligence (for federation data)
- **Layer 13:** Economic Intelligence (for allocation data)

### Required Data

- Constitutional rules definition
- Authority scope definitions
- Legitimacy threshold configuration
- Audit storage backend

### External Dependencies

- Cryptographic library (for signatures/hashing)
- Immutable storage (for audit ledger)
- Time synchronization (for event ordering)

---

## Success Criteria

Layer 14 is complete when:

1. ✅ All 5 engines implemented and tested
2. ✅ Decision flow integrated with Layer 13
3. ✅ All validation scenarios passing
4. ✅ CLI tools functional
5. ✅ Audit ledger immutable and verifiable
6. ✅ No regression in Layer 13 functionality

---

## Open Questions

1. **Constitution Amendment Process:** How should constitutional rules be modified?
   - Proposal: Manual file update with multi-agent signature required

2. **Legitimacy Threshold:** Should threshold be configurable?
   - Proposal: Default 0.70, configurable per deployment

3. **Audit Retention:** How long should audit records be kept?
   - Proposal: Minimum 1 year, configurable

4. **Capture Response:** What happens when capture is detected?
   - Proposal: Alert only, automatic response requires human decision

---

**Document Status:** DRAFT
**Next:** VALIDATION_SCENARIOS.md
