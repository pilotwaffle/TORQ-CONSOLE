# Layer 14 CLI Specification
## Governance Command-Line Interface

**Version:** 0.14.0-planning
**Status:** DRAFT
**Author:** Agent 2
**Date:** 2026-03-14

---

## Overview

This document specifies the command-line interface for Layer 14 constitutional governance. The CLI provides operators and developers with tools to inspect, analyze, and interact with the governance system.

**Command Namespace:** `torq governance`

---

## Global Options

```
torq governance [OPTIONS] <COMMAND> [ARGS]

Options:
  -v, --verbose              Enable verbose output
  -q, --quiet                Suppress non-error output
  --config PATH              Path to governance config file
  --output FORMAT            Output format: json, table, yaml [default: table]
  -h, --help                 Show help
```

---

## Commands

### 1. rules list

List all constitutional rules.

```bash
torq governance rules list [--active] [--inactive]
```

**Options:**
- `--active` - Show only active rules (default)
- `--inactive` - Show only inactive rules
- `--all` - Show all rules

**Output (table format):**
```
+------------------+-------------------------+----------+---------+
| Rule ID          | Description             | Active   | Version |
+------------------+-------------------------+----------+---------+
| GP_1             | No self-approval        | Yes      | 1.0     |
| GP_2             | Economic budgets respected| Yes      | 1.0     |
| GP_3             | Plurality preserved      | Yes      | 1.0     |
| GP_4             | Authority boundaries     | Yes      | 1.0     |
| GP_5             | Audit immutable          | Yes      | 1.0     |
+------------------+-------------------------+----------+---------+
```

**Output (json format):**
```json
{
  "rules": [
    {
      "id": "GP_1",
      "name": "No Self-Approval",
      "description": "An agent cannot approve its own proposal",
      "active": true,
      "version": "1.0",
      "last_modified": "2026-03-14T00:00:00Z"
    }
  ]
}
```

---

### 2. rules show

Display details of a specific rule.

```bash
torq governance rules show <RULE_ID>
```

**Arguments:**
- `RULE_ID` - Rule identifier (e.g., GP_1)

**Output:**
```
Rule: GP_1 - No Self-Approval
---------------------------------------------------------------------------
Description:    An agent cannot approve its own proposal
Version:        1.0
Status:         Active
Last Modified:  2026-03-14T00:00:00Z

Definition:
  An agent is prohibited from approving a decision that it proposed.
  This prevents concentration of power and ensures distributed oversight.

Parameters:
  - self_approval_penalty: 1.0 (automatic rejection)

Scope:
  - Applies to: All agents
  - Exceptions: None

Related Scenarios:
  - S1: Self-Approval Violation
```

---

### 3. audit inspect

Inspect governance audit records.

```bash
torq governance audit inspect [OPTIONS]
```

**Options:**
- `--decision-id ID` - Filter by decision ID
- `--agent-id ID` - Filter by agent ID
- `--start-time ISO8601` - Filter by start time
- `--end-time ISO8601` - Filter by end time
- `--limit N` - Limit number of records [default: 100]
- `--violations` - Show only violations
- `--output FILE` - Write to file

**Output (table format):**
```
+------------+-------------------------------+------------+----------+------------+
| Record ID  | Timestamp                     | Agent      | Decision  | Violations |
+------------+-------------------------------+------------+----------+------------+
| REC_0001   | 2026-03-14T10:00:00Z         | planner_001| DEC_001   |            |
| REC_0002   | 2026-03-14T10:01:00Z         | executor_001| DEC_001 |            |
| REC_0003   | 2026-03-14T10:02:00Z         | planner_001| DEC_002   | self_approval |
+------------+-------------------------------+------------+----------+------------+
```

**Output (json format):**
```json
{
  "records": [
    {
      "record_id": "REC_0001",
      "timestamp": "2026-03-14T10:00:00Z",
      "event_type": "decision_evaluated",
      "decision_id": "DEC_001",
      "agent_id": "planner_001",
      "legitimacy_score": 0.85,
      "violations": [],
      "compliant": true
    }
  ],
  "total_count": 3
}
```

---

### 4. audit verify

Verify cryptographic integrity of audit ledger.

```bash
torq governance audit verify [--full]
```

**Options:**
- `--full` - Perform full verification (all records)

**Output:**
```
Verifying audit ledger integrity...
------------------------------------------------------------------------------
Verified: 1,247 records
Violations: 0
Status: VERIFIED ✓

Chain Integrity: PASS
Signature Verification: PASS
Hash Consistency: PASS

Last Verified: 2026-03-14T12:00:00Z
```

**If violations found:**
```
Verifying audit ledger integrity...
------------------------------------------------------------------------------
Verified: 1,247 records
Violations: 2
Status: FAILED ✗

VIOLATION #1:
  Record: REC_0500
  Type: CHAIN_BREAK
  Details: Previous hash does not match record REC_0499

VIOLATION #2:
  Record: REC_0501
  Type: INVALID_SIGNATURE
  Details: Signature verification failed
```

---

### 5. legitimacy check

Check legitimacy of a decision.

```bash
torq governance legitimacy check <DECISION_ID> [--explain]
```

**Arguments:**
- `DECISION_ID` - Decision identifier to check

**Options:**
- `--explain` - Show detailed breakdown

**Output:**
```
Decision: DEC_001
---------------------------------------------------------------------------
Legitimacy Score: 0.85
Threshold: 0.70
Status: PASS ✓

Breakdown:
  Rule Compliance:     0.90 ████████████████████
  Authority Validity:  0.80 ██████████████████
  Plurality Integrity:  0.85 █████████████████████
  Economic Respect:     1.00 ██████████████████████████
  Audit Completeness:   0.80 ██████████████████

Violations: []
Warnings: []

Governance Status: COMPLIANT
```

**With --explain:**
```
Decision: DEC_001
---------------------------------------------------------------------------
Legitimacy Score: 0.85
Threshold: 0.70
Status: PASS ✓

Breakdown:
  Rule Compliance:     0.90 (90%)
    - GP_1 (No Self-Approval): PASS
    - GP_2 (Economic Budgets): PASS
    - GP_3 (Plurality): PASS
    - GP_4 (Authority): PASS
    - GP_5 (Audit): PASS

  Authority Validity:  0.80 (80%)
    - Agent scope: VALID
    - Action authorized: YES

  Plurality Integrity:  0.85 (85%)
    - Claims preserved: 3/3
    - No suppression detected

  Economic Respect:     1.00 (100%)
    - Funded missions match Layer 13: YES
    - Budget within limit: YES

  Audit Completeness:   0.80 (80%)
    - All required fields: YES
    - Signature valid: YES

Violations: []
Warnings: []

Recommendation: Decision is legitimate and may proceed with execution.
```

**If decision fails:**
```
Decision: DEC_002
---------------------------------------------------------------------------
Legitimacy Score: 0.45
Threshold: 0.70
Status: FAIL ✗

Breakdown:
  Rule Compliance:     0.00 (0%)
  Authority Validity:  0.80 (80%)
  Plurality Integrity:  0.85 (85%)
  Economic Respect:     1.00 (100%)
  Audit Completeness:   0.80 (80%)

Violations:
  ✗ GP_1: Self-approval detected (planner_001 approved own proposal)

Warnings:
  ! Low legitimacy score may indicate governance issue

Recommendation: Decision REJECTED - Self-approval violates constitution.
```

---

### 6. legitimacy history

Show legitimacy score history over time.

```bash
torq governance legitimacy history [OPTIONS]
```

**Options:**
- `--agent-id ID` - Filter by agent
- `--start-time ISO8601` - Start of time range
- `--end-time ISO8601` - End of time range
- `--bucket BUCKET` - Time bucket: minute, hour, day [default: hour]
- `--threshold T` - Highlight scores below threshold

**Output:**
```
Legitimacy Score History (Last 24 Hours)
---------------------------------------------------------------------------
Time        | Mean  | Min   | Max   | Below Threshold | Total Decisions
------------+-------+-------+-------+-----------------+-----------------
00:00       | 0.85  | 0.72  | 0.95  | 0               | 12
01:00       | 0.82  | 0.45  | 0.93  | 1               | 15
02:00       | 0.88  | 0.78  | 0.98  | 0               | 10
...
23:00       | 0.86  | 0.70  | 0.96  | 0               | 18

Overall Summary:
  Mean Legitimacy: 0.84
  Total Decisions: 342
  Below Threshold: 8 (2.3%)
```

---

### 7. authority report

Generate authority distribution report.

```bash
torq governance authority report [OPTIONS]
```

**Options:**
- `--time-window DURATION` - Analysis window [default: 24h]
- `--format FORMAT` - Output format: text, json, csv
- `--output FILE` - Write to file

**Output:**
```
Authority Distribution Report
Last 24 Hours
---------------------------------------------------------------------------

Decision Distribution:
  Agent              | Decisions | Share | Cumulative
  -------------------+-----------+-------+------------
  planner_001        | 85        | 24.9% | 24.9%
  executor_001       | 92        | 26.9% | 51.8%
  economist_001      | 78        | 22.8% | 74.6%
  governor_001        | 87        | 25.4% | 100.0%

Approval Distribution:
  Agent              | Approvals | Share | Cumulative
  -------------------+-----------+-------+------------
  planner_001        | 45        | 13.2% | 13.2%
  executor_001       | 98        | 28.7% | 41.8%
  economist_001      | 89        | 26.0% | 67.8%
  governor_001        | 110       | 32.2% | 100.0%

Concentration Metrics:
  Herfindahl Index: 0.256 (MODERATE concentration)
  Max Decision Share: 26.9% (executor_001)
  Max Approval Share: 32.2% (governor_001)

Capture Risk Assessment:
  Decision Concentration: MODERATE
  Approval Concentration: MODERATE
  Overall Risk Level: MODERATE ⚠

Recommendations:
  - No immediate action required
  - Monitor for increasing concentration
  - Consider rebalancing if shares exceed 40%
```

---

### 8. authority scopes

Show authority scopes for agent types.

```bash
torq governance authority scopes [--agent-type TYPE]
```

**Options:**
- `--agent-type TYPE` - Show specific agent type only

**Output:**
```
Authority Scopes
---------------------------------------------------------------------------

Agent Type: planner
  Can Approve:
    - execution_plan
    - mission_proposal
  Cannot Approve:
    - resource_allocation
    - governance_rules
    - constitutional_amendment
  Resource Limits:
    - Max budget approval: None (requires economist)
    - Max mission count: None

Agent Type: executor
  Can Approve:
    - task_execution
    - execution_status
  Cannot Approve:
    - governance_rules
    - constitutional_amendment
    - resource_allocation
  Resource Limits:
    - Max budget approval: None
    - Max mission count: None

Agent Type: economist
  Can Approve:
    - resource_allocation
    - budget_proposal
  Cannot Approve:
    - constitutional_amendment
  Resource Limits:
    - Max budget approval: 1000000.0
    - Max mission count: None

Agent Type: governor
  Can Approve:
    - governance_rules
    - constitutional_amendment
  Cannot Approve:
    - None (governor has final authority)
  Resource Limits:
    - Max budget approval: None
    - Max mission count: None
```

---

### 9. constitution export

Export constitution to file.

```bash
torq governance constitution export <OUTPUT_FILE> [OPTIONS]
```

**Arguments:**
- `OUTPUT_FILE` - Output file path

**Options:**
- `--format FORMAT` - Export format: json, yaml [default: yaml]
- `--include-inactive` - Include inactive rules
- `--sign` - Sign exported constitution

**Output:**
```yaml
# Constitution Export
# Generated: 2026-03-14T12:00:00Z
# Version: 1.0

constitution:
  version: "1.0"
  last_modified: "2026-03-14T00:00:00Z"

rules:
  - id: "GP_1"
    name: "No Self-Approval"
    description: "An agent cannot approve its own proposal"
    active: true
    version: "1.0"
    parameters:
      self_approval_penalty: 1.0

  - id: "GP_2"
    name: "Economic Budgets Respected"
    description: "Layer 13 decisions cannot be overridden"
    active: true
    version: "1.0"
    parameters:
      economic_respect_weight: 0.15

signature: "SIGNATURE_HERE"
```

---

### 10. constitution validate

Validate constitution file.

```bash
torq governance constitution validate <FILE>
```

**Arguments:**
- `FILE` - Constitution file to validate

**Output:**
```
Validating constitution: constitution.yaml
---------------------------------------------------------------------------

Schema Validation: PASS ✓

Rule Validation:
  GP_1 - No Self-Approval: VALID ✓
  GP_2 - Economic Budgets: VALID ✓
  GP_3 - Plurality Preserved: VALID ✓
  GP_4 - Authority Boundaries: VALID ✓
  GP_5 - Audit Immutable: VALID ✓

Signature Verification: PASS ✓

Overall Status: VALID ✓

The constitution is valid and can be loaded.
```

---

## Interactive Mode

```bash
torq governance interactive
```

**Features:**
- Auto-refresh audit log
- Real-time legitimacy monitoring
- Interactive rule inspection
- Live authority capture alerts

**Exit:** Ctrl+D or `exit`

---

## Configuration File

**Location:** `~/.torq/governance/config.yaml`

```yaml
# Governance CLI Configuration

defaults:
  output: table
  verbose: false
  legitimacy_threshold: 0.70

audit:
  default_limit: 100
  max_limit: 10000

reports:
  time_window: 24h
  capture_warning_threshold: 0.30
  capture_critical_threshold: 0.40
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid input |
| 3 | Verification failed |
| 4 | Constitution invalid |
| 5 | Permission denied |

---

## Examples

### Check a specific decision
```bash
torq governance legitimacy check DEC_001 --explain
```

### Find all violations in last hour
```bash
torq governance audit inspect --violations --start-time "$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)"
```

### Export audit log to JSON
```bash
torq governance audit inspect --limit 1000 --output audit.json
```

### Generate daily authority report
```bash
torq governance authority report --time-window 24h --output report.txt
```

### Verify audit integrity
```bash
torq governance audit verify --full
```

### List all rules (including inactive)
```bash
torq governance rules list --all
```

---

**Document Status:** DRAFT
**Layer 14 Status:** Planning Phase
**Next:** Agent 1 scaffold implementation
