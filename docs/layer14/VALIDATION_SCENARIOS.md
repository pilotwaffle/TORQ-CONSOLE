# Layer 14 Validation Scenarios
## Constitutional Governance Test Cases

**Version:** 0.14.0-planning
**Status:** DRAFT
**Author:** Agent 2
**Date:** 2026-03-14

---

## Overview

This document defines validation scenarios for Layer 14 constitutional governance. Each scenario tests a specific governance principle or constraint.

**Total Scenarios:** 8
**Coverage:** All 5 governance principles + 3 edge cases

---

## Scenario Definitions

### Scenario 1: Self-Approval Violation

**Purpose:** Validate GP-1 (No Self-Approval)

**Setup:**
- Agent A proposes decision D1
- Agent A attempts to approve D1

**Expected Result:**
```
LegitimacyScore.score < threshold
LegitimacyScore.passes = False
LegitimacyScore.violations contains "self_approval"
ConstitutionalEvaluation.compliant = False
Decision rejected
GovernanceEvent recorded with violation
```

**Test Data:**
```python
proposing_agent = "planner_001"
approving_agent = "planner_001"  # Same agent
decision_id = "DEC_001"
decision = DecisionPacket(
    decision_id=decision_id,
    proposing_agent=proposing_agent,
    approving_agent=approving_agent,
    action="allocate_budget",
    funded_missions=["m1", "m2"],
)
```

**Validation Checks:**
1. ✅ Legitimacy score < 0.5 (below threshold)
2. ✅ "self_approval" in violations
3. ✅ Decision rejected (not executed)
4. ✅ Audit event logged
5. ✅ Rejection reason includes "self-approval"

---

### Scenario 2: Authority Boundary Violation

**Purpose:** Validate GP-4 (Authority Boundaries)

**Setup:**
- Executor agent attempts to modify governance rules
- Authority scope for "executor" does not include "governance"

**Expected Result:**
```
AuthorityCheck.authorized = False
AuthorityCheck.reason = "Agent type 'executor' cannot modify governance rules"
ConstitutionalEvaluation.compliant = False
Decision blocked
```

**Test Data:**
```python
agent_id = "executor_001"
action = ActionType(
    type="modify_governance",
    target="constitutional_rules",
)
agent_scope = AuthorityScope(
    agent_type="executor",
    can_approve=["execution_plan"],
    cannot_approve=["governance_rules", "constitutional_amendments"],
)
```

**Validation Checks:**
1. ✅ Authority check returns unauthorized
2. ✅ Reason clearly explains limitation
3. ✅ Decision blocked
4. ✅ Audit event logged with authority violation

---

### Scenario 3: Plurality Suppression Attempt

**Purpose:** Validate GP-3 (Plurality Preservation)

**Setup:**
- Layer 12 surfaces 3 conflicting claims
- System attempts to suppress 2 claims to create "consensus"

**Expected Result:**
```
ConstitutionalEvaluation.compliant = False
ConstitutionalEvaluation.violated_rules contains "plurality_suppression"
PluralityIndex.before < PluralityIndex.after (suppression detected)
```

**Test Data:**
```python
federation_result = FederationResult(
    claim_id="FC_001",
    conflicting_claims=[
        Claim(id="C1", content="Option A", confidence=0.8),
        Claim(id="C2", content="Option B", confidence=0.75),
        Claim(id="C3", content="Option C", confidence=0.70),
    ],
    suppression_attempted=True,  # Someone tried to suppress
)
```

**Validation Checks:**
1. ✅ Plurality suppression detected
2. ✅ Violation logged
3. ✅ Constitutional evaluation fails
4. ✅ System requires preservation of all claims

---

### Scenario 4: Economic Override Attempt

**Purpose:** Validate GP-2 (Economic Budgets Respected)

**Setup:**
- Layer 13 allocates budget to missions {m1, m2, m3}
- Layer 14 decision attempts to fund {m1, m4} (m4 not approved by Layer 13)

**Expected Result:**
```
LegitimacyScore.breakdown.economic_respect = 0.0
LegitimacyScore.score < threshold
LegitimacyScore.violations contains "budget_override"
Decision rejected
```

**Test Data:**
```python
layer13_allocation = AllocationResult(
    funded_mission_ids=["m1", "m2", "m3"],
    total_budget=1000.0,
)

layer14_decision = DecisionPacket(
    decision_id="DEC_004",
    funded_missions=["m1", "m4"],  # m4 not in Layer 13
    total_budget=1000.0,
)
```

**Validation Checks:**
1. ✅ Economic respect score = 0.0 (complete override)
2. ✅ Legitimacy score below threshold
3. ✅ "budget_override" in violations
4. ✅ Decision rejected
5. ✅ Audit references Layer 13 allocation

---

### Scenario 5: Authority Capture Simulation

**Purpose:** Validate authority capture detection

**Setup:**
- Single agent (agent_A) makes 80% of decisions in time window
- Single agent approves 75% of decisions
- Single agent controls 70% of resources

**Expected Result:**
```
CaptureAnalysis.risk_level = CaptureRiskLevel.CRITICAL
CaptureAnalysis.warnings contains "excessive_decision_concentration"
CaptureAnalysis.warnings contains "excessive_approval_concentration"
CaptureMetrics.herfindahl_index > 0.40
```

**Test Data:**
```python
decisions_in_window = [
    # agent_A makes 80 decisions, agent_B makes 20
    Decision(proposer="agent_A", approver="agent_A") * 60,  # Self-approvals
    Decision(proposer="agent_A", approver="agent_B") * 20,
    Decision(proposer="agent_B", approver="agent_A") * 15,
    Decision(proposer="agent_B", approver="agent_B") * 5,
]
```

**Validation Checks:**
1. ✅ Risk level = CRITICAL
2. ✅ Herfindahl index > 0.40
3. ✅ Warnings for decision concentration
4. ✅ Warnings for approval concentration
5. ✅ Alert generated

---

### Scenario 6: Legitimate Decision (Happy Path)

**Purpose:** Validate that legitimate decisions pass governance

**Setup:**
- Agent A proposes decision
- Agent B approves (different agent)
- Within authority scope
- Respects Layer 13 allocation
- Preserves plurality

**Expected Result:**
```
ConstitutionalEvaluation.compliant = True
AuthorityCheck.authorized = True
LegitimacyScore.score > threshold (e.g., 0.85)
LegitimacyScore.passes = True
GovernanceEvent recorded (no violations)
Decision executes
```

**Test Data:**
```python
legitimate_decision = DecisionPacket(
    decision_id="DEC_006",
    proposing_agent="planner_001",
    approving_agent="executor_001",  # Different agent
    action="execute_plan",
    funded_missions=["m1", "m2", "m3"],  # Matches Layer 13
    preserves_plurality=True,
)
```

**Validation Checks:**
1. ✅ Constitutional evaluation passes
2. ✅ Authority check passes
3. ✅ Legitimacy score > 0.85
4. ✅ No violations
5. ✅ Audit event logged
6. ✅ Decision executed

---

### Scenario 7: Audit Ledger Integrity

**Purpose:** Validate GP-5 (Immutable Audit)

**Setup:**
- 100 governance events recorded
- Attempt to modify historical event
- Attempt to insert fake event in middle

**Expected Result:**
```
IntegrityReport.verified = True (before tampering)
IntegrityReport.verified = False (after tampering)
IntegrityReport.violations detected
Tampering prevented or detected
```

**Test Data:**
```python
events = [
    GovernanceEvent(
        record_id=f"REC_{i:03d}",
        timestamp=datetime.utcnow() + timedelta(seconds=i),
        event_type=GovernanceEventType.DECISION_EVALUATED,
        previous_hash=events[i-1].record_hash if i > 0 else GENESIS_HASH,
    )
    for i in range(100)
]

# Tampering attempt
events[50].decision_id = "FAKE_DECISION"
```

**Validation Checks:**
1. ✅ Original chain verifies
2. ✅ Tampered chain fails verification
3. ✅ Violation location identified
4. ✅ Cannot append without breaking chain

---

### Scenario 8: Legitimacy Threshold Edge Cases

**Purpose:** Validate legitimacy scoring at threshold boundaries

**Setup:**
- Decision with legitimacy score exactly at threshold (0.70)
- Decision with legitimacy score just below threshold (0.69)
- Decision with legitimacy score just above threshold (0.71)

**Expected Result:**
```
Score 0.70: passes = True (boundary inclusive)
Score 0.69: passes = False
Score 0.71: passes = True
```

**Test Data:**
```python
boundary_cases = [
    (0.70, True),   # Exactly at threshold
    (0.69, False),  # Just below
    (0.71, True),   # Just above
]
```

**Validation Checks:**
1. ✅ Threshold behavior is inclusive (>=)
2. ✅ Small differences flip pass/fail correctly
3. ✅ No floating point precision issues

---

## Scenario Summary Table

| # | Scenario | Principle Tested | Expected Outcome | Complexity |
|---|----------|------------------|------------------|------------|
| 1 | Self-Approval Violation | GP-1 | Rejection | Low |
| 2 | Authority Boundary | GP-4 | Blocked | Low |
| 3 | Plurality Suppression | GP-3 | Violation flagged | Medium |
| 4 | Economic Override | GP-2 | Rejection | Medium |
| 5 | Authority Capture | Detection | Critical alert | High |
| 6 | Legitimate Decision | All | Pass | Low |
| 7 | Audit Integrity | GP-5 | Tampering detected | High |
| 8 | Threshold Boundaries | Accuracy | Correct behavior | Low |

---

## Test Data Models

### DecisionPacket

```python
class DecisionPacket(BaseModel):
    decision_id: str
    proposing_agent: str
    approving_agent: str
    action: str
    funded_missions: list[str]
    total_budget: float
    timestamp: datetime
    metadata: dict[str, Any]
```

### AuthorityScope

```python
class AuthorityScope(BaseModel):
    agent_type: str
    can_approve: list[str]
    cannot_approve: list[str]
    resource_limits: dict[str, float]
```

### Claim

```python
class Claim(BaseModel):
    id: str
    content: str
    confidence: float
    proposing_agent: str
```

### FederationResult

```python
class FederationResult(BaseModel):
    claim_id: str
    conflicting_claims: list[Claim]
    suppression_attempted: bool
    plurality_index: float
```

---

## Validation Execution

### Running All Scenarios

```bash
python -m torq_console.layer14.governance.run_validation --verbose
```

### Running Single Scenario

```bash
python -m torq_console.layer14.governance.run_validation --scenario self_approval_violation
```

### Expected Output

```
============================================================
Layer 14 Validation Results
============================================================

Total Scenarios: 8
Passed: 8
Failed: 0
Success Rate: 100.0%

[PASS] Scenario 1: Self-Approval Violation
[PASS] Scenario 2: Authority Boundary Violation
[PASS] Scenario 3: Plurality Suppression
[PASS] Scenario 4: Economic Override Attempt
[PASS] Scenario 5: Authority Capture Simulation
[PASS] Scenario 6: Legitimate Decision
[PASS] Scenario 7: Audit Ledger Integrity
[PASS] Scenario 8: Threshold Boundaries

============================================================
SUCCESS: All governance validation scenarios passed!
============================================================
```

---

## Success Criteria

Layer 14 validation is complete when:

1. ✅ All 8 scenarios passing
2. ✅ All governance principles tested
3. ✅ Edge cases covered
4. ✅ Audit integrity verified
5. ✅ Capture detection functional
6. ✅ Threshold behavior correct

---

**Document Status:** DRAFT
**Next:** VALIDATION_RULES.md
