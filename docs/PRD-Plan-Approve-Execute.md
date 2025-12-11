# PRD: Plan-Approve-Execute Pattern for Prince Flowers Agent

**Version:** 2.0
**Author:** TORQ Console Team
**Date:** 2025-12-11
**Status:** Final Draft
**Based on:** Marina Wyss's Production Agent Architecture

---

## 1. Executive Summary

This PRD defines the implementation of the **Plan-Approve-Execute (PAE)** pattern into Prince Flowers Agent, transforming it from a direct-execution agent into a **production-grade, human-in-the-loop (HITL) agent**.

### Why This Matters

| Problem | Impact | Solution |
|---------|--------|----------|
| Agent executes immediately without review | Risky actions cannot be stopped | **Plan phase** - generate reviewable plan first |
| No state persistence | Context lost if interrupted | **Checkpoint system** - resume anytime |
| No audit trail | Compliance impossible | **Audit logging** - full traceability |
| All actions treated equally | Low-risk actions blocked | **Risk-based routing** - auto-approve safe actions |

### Scope

- **In Scope:** Core PAE workflow, state persistence, CLI commands, risk assessment
- **Out of Scope (v1):** Web UI dashboard, multi-tenant support, advanced analytics

---

## 2. Concrete Workflow Example

### 2.1 Full Example: Code Generation with Approval

```
USER: "Create a Python script that connects to our PostgreSQL database
       and exports user data to CSV"

┌────────────────────────────────────────────────────────────────────────┐
│ STEP 1: PLANNING (Automatic)                                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Prince Flowers analyzes query and generates:                          │
│                                                                         │
│  ActionPlan {                                                          │
│    plan_id: "plan_abc123"                                              │
│    intent: "Generate database export script"                           │
│    overall_risk: HIGH (database + PII)                                 │
│    steps: [                                                            │
│      {1: "Generate Python script", risk: MEDIUM, tool: code_gen}       │
│      {2: "Create DB connection code", risk: HIGH, tool: code_gen}      │
│      {3: "Add CSV export logic", risk: LOW, tool: code_gen}            │
│      {4: "Write to filesystem", risk: MEDIUM, tool: file_write}        │
│    ]                                                                   │
│    estimated_cost: $0.05                                               │
│    requires_approval: TRUE (HIGH risk)                                 │
│  }                                                                     │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 2: APPROVAL (Human-in-the-Loop)                                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [CONSOLE OUTPUT]                                                      │
│  ╔═══════════════════════════════════════════════════════════════════╗ │
│  ║  🔍 PLAN REVIEW REQUIRED                                          ║ │
│  ║                                                                   ║ │
│  ║  Workflow: wf_abc123                                              ║ │
│  ║  Risk Level: ⚠️  HIGH                                              ║ │
│  ║                                                                   ║ │
│  ║  PROPOSED ACTIONS:                                                ║ │
│  ║  1. [MEDIUM] Generate Python script structure                     ║ │
│  ║  2. [HIGH]   Create PostgreSQL connection code                    ║ │
│  ║  3. [LOW]    Add CSV export logic                                 ║ │
│  ║  4. [MEDIUM] Write file to ./exports/users.csv                    ║ │
│  ║                                                                   ║ │
│  ║  Estimated cost: $0.05                                            ║ │
│  ║                                                                   ║ │
│  ║  ⚠️  RISK FACTORS:                                                 ║ │
│  ║  • Database connection (credentials exposure risk)                ║ │
│  ║  • User data export (PII handling required)                       ║ │
│  ║                                                                   ║ │
│  ║  [A]pprove  [R]eject  [M]odify  [?]Details                       ║ │
│  ╚═══════════════════════════════════════════════════════════════════╝ │
│                                                                         │
│  State: CHECKPOINTED → Can resume in hours/days                        │
│  Notification: Sent to #dev-approvals Slack channel                    │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                           User types: A (Approve)
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 3: EXECUTION (Automated after approval)                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [EXECUTION LOG]                                                       │
│  ✓ Step 1/4: Generated script structure (0.8s)                         │
│  ✓ Step 2/4: Created DB connection with env vars (1.2s)                │
│  ✓ Step 3/4: Added CSV export logic (0.6s)                             │
│  ✓ Step 4/4: Wrote to ./exports/db_export.py (0.1s)                    │
│                                                                         │
│  EXECUTION COMPLETE                                                    │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 4: ARTIFACTS & AUDIT                                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Generated Artifacts:                                                  │
│  • File: ./exports/db_export.py                                        │
│  • Audit Log: ~/.torq/audit/wf_abc123.json                             │
│                                                                         │
│  Audit Entry:                                                          │
│  {                                                                     │
│    "workflow_id": "wf_abc123",                                         │
│    "user_query": "Create a Python script...",                          │
│    "plan_risk": "HIGH",                                                │
│    "approved_by": "user@company.com",                                  │
│    "approved_at": "2025-12-11T14:32:00Z",                              │
│    "execution_time_ms": 2700,                                          │
│    "artifacts": ["./exports/db_export.py"],                            │
│    "status": "COMPLETED"                                               │
│  }                                                                     │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Low-Risk Auto-Approve Example

```
USER: "Search for the latest Python 3.13 features"

┌─────────────────────────────────────────────────────────────┐
│ PLANNING                                                     │
│ ActionPlan { risk: LOW, steps: [web_search] }               │
│ auto_approve_eligible: TRUE                                  │
└─────────────────────────────────────────────────────────────┘
                           │
                    (Auto-approved)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ EXECUTION (Immediate)                                        │
│ ✓ Web search executed                                        │
│ Results returned to user                                     │
└─────────────────────────────────────────────────────────────┘

No user interaction required - LOW risk actions flow through.
```

---

## 3. Integration with Existing Code

### 3.1 Exact Integration Points

```python
# torq_console/agents/marvin_orchestrator.py - MODIFIED

class MarvinAgentOrchestrator:
    def __init__(self, model: Optional[str] = None):
        # ... existing init ...

        # NEW: Initialize PAE components
        self.planner = ActionPlanner(model=model)
        self.risk_assessor = RiskAssessor()
        self.approval_gate = ApprovalGate(
            state_store=WorkflowStateStore()
        )
        self.workflow_executor = WorkflowExecutor(
            torq_prince=self.torq_prince,
            prince_flowers=self.prince_flowers
        )

    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        mode: OrchestrationMode = OrchestrationMode.SINGLE_AGENT,
        # NEW: Optional PAE mode
        use_approval_workflow: bool = False,
        approval_config: Optional[ApprovalConfig] = None
    ) -> Union[OrchestrationResult, WorkflowHandle]:
        """
        Process query - backwards compatible.

        If use_approval_workflow=False (default): Original behavior
        If use_approval_workflow=True: New PAE workflow
        """
        if not use_approval_workflow:
            # EXISTING BEHAVIOR - unchanged
            return await self._process_query_direct(query, context, mode)

        # NEW PAE WORKFLOW
        return await self._process_query_with_approval(
            query, context, approval_config
        )

    async def _process_query_with_approval(
        self,
        query: str,
        context: Optional[Dict[str, Any]],
        config: Optional[ApprovalConfig]
    ) -> WorkflowHandle:
        """New PAE workflow."""
        config = config or ApprovalConfig()

        # 1. PLAN
        routing = await self.router.route_query(query, context)
        plan = await self.planner.create_plan(query, routing, context)

        # 2. ASSESS RISK
        plan = self.risk_assessor.assess(plan, context)

        # 3. APPROVAL GATE
        if plan.auto_approve_eligible and config.auto_approve_low_risk:
            # Auto-approve and execute immediately
            approval = ApprovalDecision(
                approved=True,
                approver_id="system:auto",
                approver_name="Auto-Approval"
            )
        else:
            # Checkpoint and await human approval
            checkpoint = await self.approval_gate.checkpoint(plan)
            await self._notify_approvers(plan, config)

            # Return handle - caller can poll or await
            return WorkflowHandle(
                workflow_id=plan.workflow_id,
                status=WorkflowStatus.AWAITING_APPROVAL,
                checkpoint_id=checkpoint.checkpoint_id
            )

        # 4. EXECUTE (if auto-approved)
        result = await self.workflow_executor.execute(plan, approval)

        # 5. GENERATE ARTIFACTS
        artifacts = await self._generate_artifacts(plan, result)

        return WorkflowHandle(
            workflow_id=plan.workflow_id,
            status=WorkflowStatus.COMPLETED,
            result=result,
            artifacts=artifacts
        )
```

### 3.2 Backwards Compatibility Guarantee

```python
# EXISTING CODE - CONTINUES TO WORK UNCHANGED
orchestrator = get_orchestrator()
result = await orchestrator.process_query("search for AI news")
# ^ Works exactly as before

# NEW CODE - OPT-IN TO PAE
result = await orchestrator.process_query(
    "modify database schema",
    use_approval_workflow=True,
    approval_config=ApprovalConfig(
        auto_approve_low_risk=True,
        notification_channels=["slack"]
    )
)
```

---

## 4. Error Handling & Recovery

### 4.1 Error Scenarios

| Scenario | Detection | Recovery |
|----------|-----------|----------|
| **Approval Timeout** | `checkpoint.expiry` exceeded | Auto-reject + notify user |
| **Execution Failure Mid-Step** | Exception in executor | Rollback completed steps if possible |
| **State Corruption** | Checksum mismatch on load | Restore from backup or mark failed |
| **Network Failure** | Connection timeout | Retry with exponential backoff |
| **Approval During Execution** | Race condition | Lock workflow during execution |

### 4.2 Rollback Strategy

```python
@dataclass
class ActionStep:
    # ... existing fields ...
    rollback_command: Optional[str] = None  # Command to undo this step
    rollback_possible: bool = True

class WorkflowExecutor:
    async def execute(self, plan: ActionPlan, approval: ApprovalDecision):
        completed_steps = []

        try:
            for step in plan.steps:
                result = await self._execute_step(step)
                completed_steps.append((step, result))

        except ExecutionError as e:
            # ROLLBACK completed steps in reverse order
            for step, result in reversed(completed_steps):
                if step.rollback_possible and step.rollback_command:
                    await self._execute_rollback(step)

            raise WorkflowFailedError(
                failed_step=step,
                completed_steps=completed_steps,
                error=e
            )
```

### 4.3 Timeout Handling

```python
class ApprovalGate:
    async def check_expired_workflows(self):
        """Run periodically to handle timeouts."""
        expired = await self.state_store.get_expired_checkpoints()

        for checkpoint in expired:
            await self._handle_timeout(checkpoint)

    async def _handle_timeout(self, checkpoint: WorkflowCheckpoint):
        # 1. Mark as timed out
        checkpoint.status = WorkflowStatus.REJECTED
        checkpoint.rejection_reason = "Approval timeout exceeded"

        # 2. Notify user
        await self._notify_timeout(checkpoint)

        # 3. Log for audit
        await self._audit_log(checkpoint, "TIMEOUT")
```

---

## 5. Security Model

### 5.1 Authorization

```python
class ApprovalAuthorization:
    """Who can approve what."""

    # Risk level → required role
    APPROVAL_ROLES = {
        RiskLevel.LOW: ["developer", "lead", "admin"],
        RiskLevel.MEDIUM: ["developer", "lead", "admin"],
        RiskLevel.HIGH: ["lead", "admin"],
        RiskLevel.CRITICAL: ["admin"],  # May require 2 approvers
    }

    def can_approve(
        self,
        user: User,
        plan: ActionPlan
    ) -> Tuple[bool, str]:
        required_roles = self.APPROVAL_ROLES[plan.overall_risk]

        if user.role not in required_roles:
            return False, f"Requires role: {required_roles}"

        # Critical actions may need multiple approvers
        if plan.overall_risk == RiskLevel.CRITICAL:
            if not self._has_multi_approval(plan):
                return False, "Critical actions require 2 approvers"

        return True, "Authorized"
```

### 5.2 Secrets Handling

```python
class ActionPlanner:
    # Never include secrets in plans
    REDACT_PATTERNS = [
        r'password\s*=\s*["\'][^"\']+["\']',
        r'api_key\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']',
        r'token\s*=\s*["\'][^"\']+["\']',
    ]

    def _sanitize_plan(self, plan: ActionPlan) -> ActionPlan:
        """Remove any secrets from plan display."""
        for step in plan.steps:
            for pattern in self.REDACT_PATTERNS:
                step.description = re.sub(
                    pattern, '[REDACTED]', step.description
                )
        return plan
```

---

## 6. File Structure

```
torq_console/
├── agents/
│   ├── pae/                          # NEW: Plan-Approve-Execute module
│   │   ├── __init__.py
│   │   ├── models.py                 # ActionPlan, WorkflowCheckpoint, etc.
│   │   ├── planner.py                # ActionPlanner
│   │   ├── risk_assessor.py          # RiskAssessor
│   │   ├── approval_gate.py          # ApprovalGate with interrupt logic
│   │   ├── workflow_executor.py      # WorkflowExecutor
│   │   ├── state_store.py            # WorkflowStateStore (SQLite)
│   │   ├── artifact_generator.py     # ArtifactGenerator
│   │   ├── notifications.py          # Slack/Email notifications
│   │   └── cli_commands.py           # CLI commands for approvals
│   │
│   ├── marvin_orchestrator.py        # MODIFIED: Add PAE integration
│   └── ... (existing files unchanged)
│
├── storage/
│   └── pae/                          # NEW: PAE storage
│       ├── workflows.db              # SQLite database
│       └── checkpoints/              # Serialized checkpoints
│
└── cli.py                            # MODIFIED: Add approval commands

~/.torq/
├── audit/                            # Audit logs
│   └── wf_*.json
└── pae_config.json                   # User's PAE configuration
```

---

## 7. Dependencies

### 7.1 New Dependencies

```toml
# pyproject.toml additions

[project.dependencies]
# State persistence
sqlalchemy = "^2.0"        # Database ORM for state store
aiosqlite = "^0.19"        # Async SQLite support

# Serialization
pydantic = "^2.0"          # Already present, but ensure v2

# Notifications (optional)
slack-sdk = "^3.0"         # Slack notifications
httpx = "^0.25"            # HTTP client for webhooks

# Checksums
xxhash = "^3.0"            # Fast hashing for integrity checks
```

### 7.2 Optional Dependencies

```toml
[project.optional-dependencies]
pae-redis = ["redis>=5.0"]           # Redis backend option
pae-postgres = ["asyncpg>=0.29"]     # PostgreSQL backend option
pae-notifications = ["slack-sdk>=3.0", "sendgrid>=6.0"]
```

---

## 8. Observability & Metrics

### 8.1 Metrics to Track

```python
class PAEMetrics:
    """Prometheus-style metrics for PAE system."""

    # Counters
    workflows_created_total: Counter
    workflows_approved_total: Counter
    workflows_rejected_total: Counter
    workflows_auto_approved_total: Counter
    workflows_timed_out_total: Counter

    # Histograms
    approval_latency_seconds: Histogram      # Time to approve
    execution_duration_seconds: Histogram    # Time to execute
    plan_generation_duration_seconds: Histogram

    # Gauges
    workflows_pending_approval: Gauge        # Currently awaiting
    checkpoints_stored: Gauge                # Total stored
```

### 8.2 Logging

```python
# Structured logging for all PAE operations
logger.info(
    "workflow_state_change",
    extra={
        "workflow_id": workflow.id,
        "from_state": "PLANNED",
        "to_state": "AWAITING_APPROVAL",
        "risk_level": plan.overall_risk.value,
        "step_count": len(plan.steps),
    }
)
```

---

## 9. Migration Path

### 9.1 For Existing Users

```python
# Phase 1: Opt-in (Week 1-2 after release)
# Users can try PAE explicitly
result = await orchestrator.process_query(
    query,
    use_approval_workflow=True
)

# Phase 2: Configuration-based default (Week 3-4)
# Users can set default in config
# ~/.torq/config.json
{
    "pae": {
        "enabled_by_default": true,
        "auto_approve_low_risk": true
    }
}

# Phase 3: Default for high-risk only (Week 5+)
# PAE automatically enabled for HIGH/CRITICAL risk
# Can be disabled with use_approval_workflow=False
```

### 9.2 Breaking Changes

**None.** All changes are additive. Existing code continues to work.

---

## 10. Implementation Phases

| Phase | Duration | Deliverables | Success Criteria |
|-------|----------|--------------|------------------|
| **P1: Foundation** | 1 week | Models, StateStore, basic tests | 100% model tests pass |
| **P2: Planner** | 1 week | ActionPlanner, RiskAssessor | Plans generate correctly for 10 test queries |
| **P3: Approval** | 1 week | ApprovalGate, CLI commands | Can approve/reject via CLI |
| **P4: Execution** | 1 week | Executor, rollback, artifacts | End-to-end workflow completes |
| **P5: Notifications** | 3 days | Slack integration | Approvals appear in Slack |
| **P6: Polish** | 4 days | Docs, examples, edge cases | README complete, 0 known bugs |

**Total: ~5 weeks**

---

## 11. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Workflow completion rate | >95% | Completed / Created |
| Approval latency (p50) | <10 min | Time from plan → approval |
| Auto-approve accuracy | >99% | No false auto-approves for HIGH risk |
| State resume success | >99.9% | Successful resumes / attempts |
| Zero unreviewed high-risk executions | 100% | Audit log validation |

---

## 12. Open Questions (Resolved)

| Question | Decision | Rationale |
|----------|----------|-----------|
| Multiple approvers for CRITICAL? | Yes, require 2 | Safety for database/financial ops |
| Default checkpoint storage? | SQLite | Simple, no infra needed, upgrade path exists |
| Checkpoint retention? | 30 days completed, 7 days rejected | Balance storage vs audit needs |
| Re-assess risk after modification? | Yes, always | Modifications could increase risk |

---

## 13. References

- [Marina Wyss - AI Agents Complete Course](https://medium.com/data-science-collective/ai-agents-complete-course-f226aa4550a1)
- [LangGraph Interrupts](https://blog.langchain.com/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt/)
- [Amazon Bedrock HITL](https://aws.amazon.com/blogs/machine-learning/implement-human-in-the-loop-confirmation-with-amazon-bedrock-agents/)
- [OpenAI Agents SDK - Human in the Loop](https://openai.github.io/openai-agents-js/guides/human-in-the-loop/)

---

**Document History**

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-11 | Initial draft |
| 2.0 | 2025-12-11 | Added: integration code, error handling, security, file structure, dependencies, migration path, observability |
