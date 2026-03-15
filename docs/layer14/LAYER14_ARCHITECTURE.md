# TORQ Layer 14 - Constitutional Governance Architecture

**Version:** 0.14.0-planning
**Status:** GOVERNANCE SCAFFOLD
**Depends On:** Layer 13 (Economic Intelligence) - v0.13.0

---

## Executive Summary

Layer 14 introduces **constitutional governance** to TORQ, completing the system's transition from a coordination system to a **self-governing distributed intelligence infrastructure**.

With Layer 14, TORQ now has:
- **Distributed reasoning** (Layers 1-7)
- **Federated knowledge exchange** (Layer 12)
- **Economic resource allocation** (Layer 13)
- **Constitutional governance** (Layer 14) ← NEW

---

## Architecture Position

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 14: Governance                     │
│            Constitutional Rules + Legitimacy Gate             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   LAYER 13: Economics                       │
│              Value-Aware Resource Allocation                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   LAYER 12: Federation                      │
│               Collective Intelligence Exchange                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   LAYERS 6-11: Fabric                       │
│              Distributed Execution Infrastructure              │
└─────────────────────────────────────────────────────────────┘
```

**Layer 14 is the final legitimacy gate** between economic prioritization and execution.

---

## Core Components

### 1. ConstitutionalFrameworkEngine

**Purpose:** Define and enforce the TORQ system constitution.

**Responsibilities:**
- Load constitutional rules
- Evaluate decisions against rules
- Identify rule violations
- Flag critical violations

**Rule Types:**
| Rule | Description |
|------|-------------|
| NO_SELF_APPROVAL | Agents cannot approve their own proposals |
| PLURALITY_REQUIRED | Major actions require multiple approvals |
| AUTHORITY_BOUNDARY | Agents must stay within authority level |
| BUDGET_LIMIT | Cannot exceed allocated budget |
| SEPARATION_OF_POWERS | Planning and execution roles separated |
| GOVERNANCE_CHANGE_PROTECTION | Constitution changes require special approval |

**Output:** `ConstitutionEvaluation { compliant, violated_rules, violations }`

### 2. AuthorityBoundaryEnforcer

**Purpose:** Ensure agents operate within authorized domains.

**Responsibilities:**
- Register agent authority profiles
- Check action permissions
- Validate resource access
- Track authority expiration

**Authority Hierarchy:**
```
NONE < READ < PROPOSE < ADVISE < EXECUTE < APPROVE < GOVERN < ROOT
```

**Output:** `AuthorityCheck { permitted, violation_reason, required_level, actual_level }`

### 3. LegitimacyScoringEngine

**Purpose:** Compute legitimacy scores for governance decisions.

**Formula:**
```
legitimacy_score = rule_compliance * 0.4
                + authority_validity * 0.3
                + plurality_integrity * 0.2
                + transparency * 0.1
```

**Threshold:** Default 0.7 (configurable)

**Output:** `LegitimacyScore { score, threshold, is_legitimate, warnings, violations }`

### 4. AuthorityCaptureDetector

**Purpose:** Detect excessive influence concentration.

**Metrics Tracked:**
- `decision_share`: Share of total decisions
- `approval_share`: Share of total approvals
- `resource_concentration`: Control over resources
- `self_approval_rate`: Self-approvals (should be 0)

**Risk Levels:** LOW, MEDIUM, HIGH, CRITICAL

**Output:** `AuthorityRisk { influence_score, capture_risk_level, warnings }`

### 5. GovernanceAuditLedger

**Purpose:** Immutable log of all governance events.

**Records:**
- Decision evaluations
- Rule changes
- Authority changes
- Violations

**Features:**
- Append-only (immutable)
- Queryable by agent, event type, severity
- Exportable (dict, JSON, CSV)
- Statistics generation

**Output:** `GovernanceRecord { record_id, timestamp, agent_id, legitimacy_score, violations }`

---

## Execution Flow

### Governance Pipeline

```
Layer 13 Economic Prioritization
        │
        ├─→ EconomicScore { value, efficiency, cost }
        │
        ↓
Layer 14 Governance Evaluation
        │
        ├─→ ConstitutionalFrameworkEngine.evaluate_decision()
        │       └─→ ConstitutionEvaluation
        │
        ├─→ AuthorityBoundaryEnforcer.check_decision_authority()
        │       └─→ AuthorityCheck (proposer), AuthorityCheck (approver)
        │
        ├─→ AuthorityCaptureDetector.track_decision()
        │       └─→ InfluenceMetrics updated
        │
        ├─→ LegitimacyScoringEngine.compute_legitimacy()
        │       └─→ LegitimacyScore
        │
        ├─→ GovernanceAuditLedger.record_decision()
        │       └─→ GovernanceRecord
        │
        ↓
GovernanceResult
        │
        ├─→ execution_authorized: bool
        ├─→ legitimacy_score: float
        ├─→ blocking_violations: list
        └─→ audit_record_id: str
        │
        ↓
    IF execution_authorized:
            → Proceed to Execution Fabric (L6-11)
    ELSE:
            → Block execution, log violations
```

---

## Data Models

### GovernanceDecisionPacket (Input)

```python
{
    "decision_id": str
    "proposal_id": str | None
    "proposing_agent_id": str
    "approving_agent_id": str | None
    "approval_chain": list[str]
    "economic_priority_score": float  # From Layer 13
    "estimated_cost": float
    "budget_remaining": float
    "action_type": str
    "action_description": str
    "target_resources": list[str]
    "requires_human_approval": bool
    "is_governance_change": bool
    "is_budget_change": bool
}
```

### GovernanceResult (Output)

```python
{
    "decision_id": str
    "legitimacy_score": float  # 0.0 to 1.0
    "legitimacy_threshold": float  # Default 0.7
    "execution_authorized": bool
    "blocking_violations": list[GovernanceViolation]
    "warning_violations": list[GovernanceViolation]
    "constitutional_compliant": bool
    "authority_compliant": bool
    "plurality_compliant": bool
    "authority_risk_score": float
    "transparency_score": float
    "audit_record_id": str | None
}
```

---

## File Structure

```
torq_console/layer14/
├── governance/
│   ├── __init__.py                    # Package exports
│   ├── models.py                      # Core data models
│   ├── constitutional_framework_engine.py
│   ├── authority_boundary_enforcer.py
│   ├── legitimacy_scoring_engine.py
│   ├── authority_capture_detector.py
│   ├── governance_audit_ledger.py
│   └── governance_service.py          # Main service interface
└── __init__.py                         # Layer 14 package
```

---

## API Usage

```python
from torq_console.layer14.governance import (
    create_governance_service,
    GovernanceDecisionPacket,
    AuthorityLevel,
)

# Create governance service
governance = create_governance_service(legitimacy_threshold=0.7)

# Register agent authorities
governance.register_agent_authority(
    agent_id="planner_agent",
    authority_level=AuthorityLevel.PROPOSE,
    role="planner",
)

governance.register_agent_authority(
    agent_id="governor_agent",
    authority_level=AuthorityLevel.APPROVE,
    role="governor",
)

# Create decision packet (from Layer 13 output)
decision = GovernanceDecisionPacket(
    decision_id="decision_001",
    proposing_agent_id="planner_agent",
    approving_agent_id="governor_agent",
    economic_priority_score=0.85,
    estimated_cost=500.0,
    budget_remaining=1000.0,
    action_type="execute_mission",
    action_description="Deploy data pipeline",
    approval_chain=["governor_agent"],
)

# Evaluate through governance
result = await governance.evaluate_decision(decision)

# Check if execution is authorized
if result.execution_authorized:
    print(f"Decision authorized with legitimacy {result.legitimacy_score:.2f}")
else:
    print(f"Decision blocked: {[v.description for v in result.blocking_violations]}")
```

---

## Key Principles

### 1. No Self-Approval

Agents cannot approve their own proposals. This prevents single-point
authority abuse.

### 2. Plurality Required

Major decisions (high-cost, governance changes) require approval
from multiple agents.

### 3. Authority Boundaries

Each agent operates within a defined authority domain. Exceeding
authority is detected and blocked.

### 4. Budget Limits

Decisions cannot exceed allocated budgets. Economic prioritization
from Layer 13 is respected.

### 5. Immutable Audit

All governance decisions are logged in an append-only ledger for
complete system transparency.

---

## Integration with Other Layers

### Layer 13 → Layer 14

**Input:** Layer 13 `AllocationResult` (funded missions)
**Transform:** `GovernanceDecisionPacket`
**Processing:** Constitutional + Authority + Legitimacy checks
**Output:** `GovernanceResult` (authorized or blocked)

### Layer 14 → Execution Fabric

**Authorized:** Forward to Layers 6-11 for execution
**Blocked:** Log violations, return to Layer 13 for reconsideration

---

## Constitutional Rules

### Default Rule Set

1. **NO_SELF_APPROVAL**
   - Agents cannot approve their own proposals
   - Severity: CRITICAL

2. **PLURALITY_REQUIRED**
   - High-cost decisions (>1000) require plural approval
   - Governance changes require plural approval
   - Severity: HIGH

3. **AUTHORITY_BOUNDARY**
   - Agents must stay within authority level
   - Budget changes require explicit approval
   - Severity: CRITICAL

4. **BUDGET_LIMIT**
   - Cannot exceed remaining budget
   - Severity: CRITICAL

5. **SEPARATION_OF_POWERS**
   - High-value actions require proposal/approval separation
   - Severity: HIGH

6. **GOVERNANCE_CHANGE_PROTECTION**
   - Governance changes require plural approval
   - Should be flagged for human review
   - Severity: CRITICAL

---

## Authority Capture Detection

### Risk Thresholds

| Metric | High Risk |
|--------|-----------|
| Decision Share | >50% |
| Approval Share | >60% |
| Resource Concentration | >70% |
| Influence Score | >80% |

### Warning Indicators

- Agent controls >40% of decisions
- Agent controls >50% of approvals
- Self-approvals detected
- High influence with low authority level

---

## Audit Ledger

### Record Types

- `decision`: Standard governance decision
- `rule_add`: New constitutional rule
- `rule_modify`: Modified constitutional rule
- `rule_remove`: Removed constitutional rule
- `authority_grant`: Authority granted to agent
- `authority_revoke`: Authority revoked from agent
- `authority_modify`: Authority level changed

### Query Capabilities

- By agent ID
- By event type
- By violation severity
- By time range
- Export to dict/JSON/CSV

---

## Status

| Component | Status |
|-----------|--------|
| ConstitutionalFrameworkEngine | ✅ Implemented |
| AuthorityBoundaryEnforcer | ✅ Implemented |
| LegitimacyScoringEngine | ✅ Implemented |
| AuthorityCaptureDetector | ✅ Implemented |
| GovernanceAuditLedger | ✅ Implemented |
| GovernanceService | ✅ Implemented |
| Core Models | ✅ Implemented |
| Documentation | ✅ Implemented |

---

## Next Steps

1. **Agent 2:** Implement PRD and validation scenarios
2. **Integration:** Wire Layer 14 into TORQ main pipeline
3. **Testing:** Run validation scenarios
4. **Documentation:** Complete CLI and API docs

---

## References

- Layer 13: Economic Intelligence (v0.13.0)
- Layer 12: Collective Intelligence Exchange
- TORQ Constitution: System governance rules

---

**Architect:** Agent 1 (Platform & Architecture Owner)
**Date:** 2026-03-14
**Status:** SCAFFOLD COMPLETE - Ready for PRD and Validation
