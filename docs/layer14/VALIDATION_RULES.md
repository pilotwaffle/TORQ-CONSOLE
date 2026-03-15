# Layer 14 Validation Rules
## Constitutional Governance System

**Version:** 0.14.0-planning
**Status:** DRAFT
**Author:** Agent 2
**Date:** 2026-03-14

---

## Overview

This document defines validation rules for Layer 14 constitutional governance. Each rule has specific pass/fail criteria that must be met for the system to be considered working correctly.

Rules are organized by:
- General Rules (system-wide)
- Component Rules (per engine)
- Scenario Rules (per test scenario)
- Performance Rules (latency/throughput)
- Security Rules (tampering/attacks)

---

## General Rules

### GR-1: No Self-Approval

**Rule:** An agent cannot approve its own proposal.

| Condition | Expected | Tolerance |
|-----------|----------|-----------|
| Proposer == Approver | REJECT | Exact |
| Proposer != Approver | MAY PASS | — |

**Pass Criteria:**
```python
assert decision.proposing_agent != decision.approving_agent
```

**Fail Conditions:**
- Self-approval not detected
- Self-approval detected but not blocked
- Self-approval not logged as violation

---

### GR-2: Economic Budgets Respected

**Rule:** Layer 14 cannot override Layer 13 economic decisions.

| Condition | Expected | Tolerance |
|-----------|----------|-----------|
| Funded missions match Layer 13 | Full respect | 100% |
| Budget within Layer 13 limit | Full respect | 100% |

**Pass Criteria:**
```python
# Check funded mission alignment
layer13_missions = set(allocation.funded_mission_ids)
layer14_missions = set(decision.funded_missions)

assert layer14_missions.issubset(layer13_missions)

# Check budget
assert decision.total_budget <= allocation.total_budget
```

**Fail Conditions:**
- Layer 13 allocation modified
- Budget exceeded without Layer 13 approval
- Economic respect score < 1.0 for critical decisions

---

### GR-3: Plurality Preserved

**Rule:** Disagreement and conflicting claims must not be suppressed.

| Metric | Expected | Threshold |
|--------|----------|-----------|
| Plurality index | Maintained or increased | >= before |
| Conflicting claims count | Preserved | 100% |

**Pass Criteria:**
```python
assert current_plurality_index >= original_plurality_index
assert len(conflicting_claims) == len(original_claims)
```

**Fail Conditions:**
- Claims removed without justification
- Plurality index decreased
- Suppression not flagged as violation

---

### GR-4: Authority Boundaries Enforced

**Rule:** Agents cannot act outside their defined scope.

| Agent Type | Forbidden Actions |
|------------|-------------------|
| Planner | Resource allocation, governance changes |
| Executor | Governance rules, constitutional amendments |
| Economist | Constitutional amendments |

**Pass Criteria:**
```python
authority_check = authority_enforcer.check_authority(
    agent_id=agent.id,
    action=action.type
)

if action.type in agent.cannot_approve:
    assert authority_check.authorized == False
```

**Fail Conditions:**
- Unauthorized action not blocked
- Authority scope not checked
- Scope violation not logged

---

### GR-5: Audit Ledger Immutable

**Rule:** Governance audit trail cannot be modified retrospectively.

| Condition | Expected |
|-----------|----------|
| Append-only write | Success |
| Modify historical record | FAIL |
| Insert middle record | FAIL |
| Cryptographic verification | PASS |

**Pass Criteria:**
```python
# Verify chain integrity
for record in ledger:
    if record.previous_hash:
        expected_hash = hash(previous_record)
        assert record.previous_hash == expected_hash

# Verify signatures
for record in ledger:
    assert verify_signature(record.signature, record.data)
```

**Fail Conditions:**
- Chain integrity broken
- Signature verification fails
- Record modified without detection

---

## Component Rules

### CR-1: ConstitutionalFrameworkEngine

#### Rule CR-1-1: Rule Evaluation

**Condition:** Decision evaluated against all rules.

**Expected:** All rules checked, violations collected.

**Pass Criteria:**
```python
evaluation = await engine.evaluate_decision(decision)

assert len(evaluation.rule_scores) > 0
assert all(0.0 <= score <= 1.0 for score in evaluation.rule_scores.values())
```

#### Rule CR-1-2: Violation Detection

**Condition:** Decision violates constitutional rule.

**Expected:** Violation detected and reported.

**Pass Criteria:**
```python
if decision.violates_rule("self_approval"):
    assert evaluation.compliant == False
    assert "self_approval" in evaluation.violated_rules
```

---

### CR-2: AuthorityBoundaryEnforcer

#### Rule CR-2-1: Authority Check

**Condition:** Agent attempts action.

**Expected:** Authority verified before execution.

**Pass Criteria:**
```python
check = enforcer.check_authority(agent_id, action)

if action.type in agent.forbidden_actions:
    assert check.authorized == False
    assert check.reason is not None
```

#### Rule CR-2-2: Scope Definition

**Condition:** Agent authority scope defined.

**Expected:** All agent types have scopes.

**Pass Criteria:**
```python
for agent_type in ["planner", "executor", "economist", "governor"]:
    scope = enforcer.get_scope(agent_type)
    assert scope is not None
    assert scope.can_approve is not None
    assert scope.cannot_approve is not None
```

---

### CR-3: LegitimacyScoringEngine

#### Rule CR-3-1: Score Range

**Condition:** Legitimacy score computed.

**Expected:** Score in [0.0, 1.0].

**Pass Criteria:**
```python
score = await engine.compute_legitimacy(decision, constitution, authority)

assert 0.0 <= score.score <= 1.0
assert 0.0 <= score.breakdown.rule_compliance <= 1.0
assert 0.0 <= score.breakdown.authority_validity <= 1.0
assert 0.0 <= score.breakdown.plurality_integrity <= 1.0
assert 0.0 <= score.breakdown.economic_respect <= 1.0
assert 0.0 <= score.breakdown.audit_completeness <= 1.0
```

#### Rule CR-3-2: Threshold Enforcement

**Condition:** Score compared to threshold.

**Expected:** Below threshold = rejected.

**Pass Criteria:**
```python
THRESHOLD = 0.70

score = await engine.compute_legitimacy(...)

if score.score >= THRESHOLD:
    assert score.passes == True
else:
    assert score.passes == False
    assert len(score.violations) > 0
```

#### Rule CR-3-3: Score Composition

**Condition:** Score is weighted sum of components.

**Expected:** Components sum correctly.

**Pass Criteria:**
```python
score = await engine.compute_legitimacy(...)

expected = (
    0.30 * score.breakdown.rule_compliance +
    0.25 * score.breakdown.authority_validity +
    0.20 * score.breakdown.plurality_integrity +
    0.15 * score.breakdown.economic_respect +
    0.10 * score.breakdown.audit_completeness
)

assert abs(score.score - expected) < 0.001
```

---

### CR-4: AuthorityCaptureDetector

#### Rule CR-4-1: Concentration Detection

**Condition:** Single agent dominates decisions.

**Expected:** High risk level flagged.

**Pass Criteria:**
```python
# Agent makes 80% of decisions
analysis = await detector.analyze_capture(timedelta(hours=1))

assert analysis.risk_level in [CaptureRiskLevel.HIGH, CaptureRiskLevel.CRITICAL]
assert any("concentration" in w.lower() for w in analysis.warnings)
```

#### Rule CR-4-2: Herfindahl Index

**Condition:** Market concentration calculated.

**Expected:** Index in [0.0, 1.0].

**Pass Criteria:**
```python
analysis = await detector.analyze_capture(timedelta(hours=1))

assert 0.0 <= analysis.metrics.herfindahl_index <= 1.0

# Higher index = more concentration
if analysis.metrics.herfindahl_index > 0.40:
    assert analysis.risk_level == CaptureRiskLevel.CRITICAL
```

#### Rule CR-4-3: Share Calculation

**Condition:** Decision share per agent calculated.

**Expected:** Shares sum to 1.0.

**Pass Criteria:**
```python
analysis = await detector.analyze_capture(timedelta(hours=1))

shares = analysis.metrics.decision_share.values()
assert abs(sum(shares) - 1.0) < 0.001
```

---

### CR-5: GovernanceAuditLedger

#### Rule CR-5-1: Append-Only

**Condition:** New event appended.

**Expected:** Record added, previous records unchanged.

**Pass Criteria:**
```python
record_count_before = len(ledger.events)

record_id = await ledger.record_event(event)

assert len(ledger.events) == record_count_before + 1
assert ledger.events[-1].record_id == record_id
```

#### Rule CR-5-2: Cryptographic Integrity

**Condition:** Ledger integrity verified.

**Expected:** All records valid.

**Pass Criteria:**
```python
report = await ledger.verify_integrity()

assert report.verified == True
assert report.total_records == len(ledger.events)
assert len(report.violations) == 0
```

#### Rule CR-5-3: Chain Hashing

**Condition:** Each record links to previous.

**Expected:** Chain unbroken.

**Pass Criteria:**
```python
for i, record in enumerate(ledger.events[1:], start=1):
    expected_hash = hash(ledger.events[i-1])
    assert record.previous_hash == expected_hash
```

---

## Performance Rules

### PR-1: Constitution Evaluation Latency

**Rule:** Single decision constitution check must be fast.

**Pass Criteria:**
```python
elapsed = time_elapsed(
    constitutional_engine.evaluate_decision,
    decision
)
assert elapsed < 0.005  # < 5ms
```

---

### PR-2: Authority Check Latency

**Rule:** Authority verification must be fast.

**Pass Criteria:**
```python
elapsed = time_elapsed(
    authority_enforcer.check_authority,
    agent_id,
    action
)
assert elapsed < 0.002  # < 2ms
```

---

### PR-3: Legitimacy Scoring Latency

**Rule:** Legitimacy score computation must be fast.

**Pass Criteria:**
```python
elapsed = time_elapsed(
    legitimacy_engine.compute_legitimacy,
    decision,
    constitution_eval,
    authority_check
)
assert elapsed < 0.010  # < 10ms
```

---

### PR-4: Capture Detection Latency

**Rule:** Time window analysis must be reasonable.

**Pass Criteria:**
```python
elapsed = time_elapsed(
    capture_detector.analyze_capture,
    timedelta(hours=1)
)
assert elapsed < 0.100  # < 100ms
```

---

### PR-5: Audit Write Latency

**Rule:** Audit event write must be fast.

**Pass Criteria:**
```python
elapsed = time_elapsed(
    audit_ledger.record_event,
    event
)
assert elapsed < 0.005  # < 5ms
```

---

### PR-6: Audit Query Latency

**Rule:** Audit query must be responsive.

**Pass Criteria:**
```python
elapsed = time_elapsed(
    audit_ledger.query_events,
    EventFilter(time_range=timedelta(days=1))
)
assert elapsed < 0.050  # < 50ms
```

---

## Security Rules

### SR-1: Constitution Tampering Detection

**Condition:** Constitution file modified.

**Expected:** Tampering detected.

**Pass Criteria:**
```python
# Modify constitution
original_hash = hash(constitution)
constitution.rules[0].text = "MODIFIED"

# Detection
assert constitution_engine.verify_integrity() == False
assert constitution_engine.current_hash != original_hash
```

---

### SR-2: Audit Spoofing Prevention

**Condition:** Fake event inserted.

**Expected:** Verification fails.

**Pass Criteria:**
```python
# Try to insert fake event
fake_event = GovernanceEvent(
    record_id="FAKE",
    timestamp=datetime.utcnow(),
    signature="FAKE_SIGNATURE"
)

ledger.events.insert(50, fake_event)

# Verification should fail
report = await ledger.verify_integrity()
assert report.verified == False
assert len(report.violations) > 0
```

---

### SR-3: Signature Verification

**Condition:** Event signature verified.

**Expected:** Invalid signatures rejected.

**Pass Criteria:**
```python
# Event with invalid signature
invalid_event = GovernanceEvent(
    signature="INVALID"
)

# Should not accept
assert ledger.verify_signature(invalid_event) == False
```

---

## Scenario Rules

### SRV-1: Self-Approval Scenario

**Pass Criteria:**
- Legitimacy score < 0.5
- "self_approval" in violations
- Decision rejected
- Audit event logged

### SRV-2: Authority Boundary Scenario

**Pass Criteria:**
- Authority check returns unauthorized
- Action blocked
- Reason provided
- Audit event logged

### SRV-3: Plurality Suppression Scenario

**Pass Criteria:**
- Suppression detected
- Plurality violation flagged
- Constitution evaluation fails
- Audit event logged

### SRV-4: Economic Override Scenario

**Pass Criteria:**
- Economic respect < 1.0
- Legitimacy score < threshold
- Decision rejected
- References Layer 13 allocation

### SRV-5: Authority Capture Scenario

**Pass Criteria:**
- Risk level = CRITICAL
- Herfindahl index > 0.40
- Concentration warnings
- Alert generated

### SRV-6: Legitimate Decision Scenario

**Pass Criteria:**
- All checks pass
- Legitimacy score > 0.85
- No violations
- Decision executes
- Clean audit event

### SRV-7: Audit Integrity Scenario

**Pass Criteria:**
- Original chain verifies
- Tampered chain fails
- Violation located
- Tampering prevented/detected

### SRV-8: Threshold Boundary Scenario

**Pass Criteria:**
- 0.70 passes (inclusive)
- 0.69 fails
- 0.71 passes
- No floating point issues

---

## Test Matrix

| Scenario | Rules | Priority | Automated |
|----------|-------|----------|-----------|
| S1: Self-Approval | GR-1, CR-1, CR-3 | P0 | Yes |
| S2: Authority Boundary | GR-4, CR-2, CR-3 | P0 | Yes |
| S3: Plurality Suppression | GR-3, CR-1, CR-3 | P0 | Yes |
| S4: Economic Override | GR-2, CR-1, CR-3 | P0 | Yes |
| S5: Authority Capture | CR-4 | P1 | Yes |
| S6: Legitimate Decision | All GR | P0 | Yes |
| S7: Audit Integrity | GR-5, CR-5, SR-2 | P0 | Yes |
| S8: Threshold Boundaries | CR-3 | P1 | Yes |
| Performance | PR-1 to PR-6 | P1 | Yes |
| Security | SR-1 to SR-3 | P0 | Yes |

---

## Continuous Validation

### Regression Tests

Each rule must have an automated test that runs on every commit.

**Pass Rate Target:** 100%

**CI Pipeline:**
```yaml
test_layer14:
  script:
    - python -m pytest tests/layer14/ -v
  coverage:
    - torq_console/layer14/
  requirements:
    - All scenarios passing
    - All rules passing
    - Performance within thresholds
    - Security tests passing
```

---

## Validation Workflow

```
1. IMPLEMENTATION
   Agent 1 implements governance engines
   ↓
2. SCENARIO DEFINITION
   Agent 2 defines test scenarios
   ↓
3. VALIDATION
   Both run validation suite
   ↓
4. FAILURE ANALYSIS
   If failures: Agent 1 fixes, Agent 2 verifies
   ↓
5. APPROVAL
   All scenarios passing → Layer 14 complete
```

---

**Document Status:** DRAFT
**Next:** CLI_SPEC.md
