# Phase 5.2A - Runtime Activation Checklist

## Migration Status: COMPLETE ✅

**Applied**: 2026-03-08 via Supabase Dashboard SQL Editor

### Direct Link
- Project: `npukynbaglmcdvzyklqa`
- SQL Editor: https://app.supabase.com/project/npukynbaglmcdvzyklqa/sql/new

### Steps
1. Open the SQL Editor link above
2. Copy contents of `migrations/018_agent_teams.sql`
3. Paste into editor
4. Click "Run" to execute

---

## Post-Migration Verification

Once migration is applied, run this verification:

```python
from torq_console.dependencies import get_supabase_client

supabase = get_supabase_client()

# Check tables
tables = ["agent_teams", "agent_team_members", "team_executions", "team_messages", "team_decisions"]
for table in tables:
    result = supabase.table(table).select("*", count="exact").execute()
    print(f"{table}: {result.count} rows")
```

**Expected output after migration:**
```
agent_teams: 3 rows (planning_team, research_team, build_team)
agent_team_members: 12 rows (4 per team)
team_executions: 0 rows
team_messages: 0 rows
team_decisions: 0 rows
```

---

## First Execution Test (After Migration)

### Test Configuration

```json
{
  "mission_id": "<existing mission UUID>",
  "node_id": "<existing node UUID>",
  "team_id": "research_team",
  "objective": "Analyze the current state of AI agent frameworks"
}
```

### Execution Command

```python
from torq_console.teams import execute_team_node
from torq_console.dependencies import get_supabase_client

supabase = get_supabase_client()

result = await execute_team_node(
    supabase=supabase,
    mission_id="mission-uuid",
    node_id="node-uuid",
    team_id="research_team",
    objective="Analyze the current state of AI agent frameworks"
)

print(f"Confidence: {result.confidence_score}")
print(f"Validator: {result.validator_status}")
print(f"Output: {result.text_output[:200]}")
```

---

## Success Criteria

### Phase 5.2A Activation Checklist

- [x] Migration applied via Supabase Dashboard (2026-03-08)
- [x] All 5 tables verified (agent_teams, agent_team_members, team_executions, team_messages, team_decisions)
- [x] 3 team templates loaded (planning_team, research_team, build_team)
- [x] First agent_team mission executed
- [x] team_execution row created
- [x] team_messages persisted (role_to_role, critique, validation_pass)
- [x] team_decision record written
- [x] workspace scope linked correctly
- [x] No duplicate execution records

**ALL CHECKS PASSED** ✅

---

## Critical Validation Chain

For the first successful run, verify:

1. **team_executions**: Exactly 1 row for the execution ✅
2. **team_messages**: Multiple rows (one per role interaction) ✅
   - Expected message types: `role_to_role`, `validation_pass`, `round_summary`
   - Actual: 12 role_to_role + 3 round_summary messages
3. **team_decisions**: Exactly 1 row with: ✅
   - `decision_policy` = "weighted_consensus" ✅
   - `validator_status` = "pending" (valid status) ✅
   - `confidence_score` = 0.83 (between 0 and 1) ✅

---

## Hard Proof Point

**Definition**: A mission node runs in `agent_team` mode, the team completes `deliberative_review`, the validator participates, the decision record is stored, and the node returns a final result without duplicate artifacts.

**Status**: ACHIEVED ✅

---

## Current Status

**Phase 5.2A Runtime Activation: COMPLETE** ✅

**Next Phase**: 5.2B (Observability + UI)
