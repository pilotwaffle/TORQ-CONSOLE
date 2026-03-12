# Phase 5.2 Agent Teams - Implementation Package

**Status**: Developer Package Complete
**Date**: March 8, 2026
**Phase**: 5.2 - Agent Teams

---

## Package Contents

This implementation package contains all core components for Phase 5.2 Agent Teams.

### Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `migrations/018_agent_teams.sql` | Database schema | 380+ |
| `torq_console/teams/models.py` | Data models & enums | 350+ |
| `torq_console/teams/registry.py` | Team definition registry | 200+ |
| `torq_console/teams/orchestrator.py` | Core orchestrator | 380+ |
| `torq_console/teams/role_runner.py` | Role execution | 330+ |
| `torq_console/teams/decision_engine.py` | Decision policies | 330+ |
| `torq_console/teams/persistence.py` | Database persistence | 280+ |
| `torq_console/teams/context.py` | Workspace context | 170+ |
| `torq_console/teams/api.py` | FastAPI routes | 360+ |
| `torq_console/teams/__init__.py` | Module exports | 100+ |

**Total**: ~2,880 lines of production code

---

## Database Schema

### New Tables

1. **agent_teams** - Reusable team definitions
2. **agent_team_members** - Role configurations
3. **team_executions** - Execution tracking
4. **team_messages** - Collaboration events
5. **team_decisions** - Final decisions

### Initial Team Templates

- **planning_team** - Mission decomposition and strategic planning
- **research_team** - Evidence gathering and analysis
- **build_team** - Execution and implementation

---

## API Endpoints

### Team Management
- `GET /api/teams` - List all teams
- `GET /api/teams/{team_id}` - Get team details
- `POST /api/teams` - Create new team

### Team Executions
- `GET /api/teams/executions` - List executions
- `GET /api/teams/executions/{id}` - Get execution details
- `GET /api/teams/executions/{id}/messages` - Get collaboration messages
- `GET /api/teams/executions/{id}/decision` - Get final decision
- `GET /api/teams/executions/{id}/events/stream` - SSE live updates

### Mission Integration
- `POST /api/teams/missions/{mission_id}/nodes/{node_id}/run-team` - Execute node as team
- `GET /api/teams/missions/{mission_id}/team-executions` - Get mission team executions

---

## Usage Example

```python
from torq_console.teams import execute_team_node
from uuid import UUID

# Execute a mission node using the research team
result = await execute_team_node(
    supabase=supabase_client,
    mission_id="mission-uuid",
    node_id="node-uuid",
    team_id="research_team",
    objective="Analyze market trends for AI agents in 2026",
    constraints=["Use only verified sources", "Focus on enterprise adoption"],
)

print(f"Final confidence: {result.confidence_score}")
print(f"Validator status: {result.validator_status}")
print(f"Output: {result.text_output}")
```

---

## Team Templates

### Planning Team
- **Roles**: Lead, Strategist, Critic, Validator
- **Pattern**: deliberative_review
- **Use**: Mission planning, architecture design

### Research Team
- **Roles**: Lead, Researcher, Critic, Validator
- **Pattern**: deliberative_review
- **Use**: Research, analysis, investigation

### Build Team
- **Roles**: Lead, Builder, Reviewer, Validator
- **Pattern**: deliberative_review
- **Use**: Implementation, code generation

---

## Collaboration Pattern (MVP)

### Deliberative Review Flow

1. **Lead** frames objective
2. **Researcher/Strategist/Builder** produces candidate response
3. **Critic/Reviewer** challenges weak points
4. **Validator** checks policy and structure
5. **Lead** synthesizes final answer
6. **Decision Engine** applies consensus policy

### Round Management

- Max rounds: 3
- Early exit if confidence >= 0.85
- Validator can block output
- Revision triggers additional round

---

## Decision Policies

### Weighted Consensus (Default)
- Each role has confidence weight
- Final score = weighted average
- Validator gate applies

### Unanimous
- All roles must approve
- High threshold (0.8)
- Dissent triggers escalation

### Validator Gate
- Validator has veto power
- All other inputs secondary
- Blocked outputs require revision

---

## Integration Points

### Existing Systems Used
- Mission Graph (node execution)
- Shared Cognitive Workspace (team context)
- Handoff System (internal collaboration)
- Event Stream (telemetry)
- Control Surface (observability)

### Execution Flow

```
Mission Graph Node
    ↓ (execution_mode = agent_team)
Execution Engine
    ↓ (delegates to)
AgentTeamOrchestrator
    ↓ (creates)
TeamExecution + Workspace
    ↓ (runs roles through)
RoleRunner
    ↓ (produces)
TeamMessages
    ↓ (evaluates)
DecisionEngine
    ↓ (returns)
TeamExecutionResult
    ↓ (updates)
Mission Node + Control Surface
```

---

## Milestone Status

| Milestone | Status | Notes |
|-----------|--------|-------|
| M1: Team Definitions & Data Layer | ✅ | Schema, models, registry complete |
| M2: Team Runtime | ✅ | Orchestrator, role runner complete |
| M3: Handoff Integration | ✅ | Message persistence complete |
| M4: Control Surface Integration | ⏳ | Frontend components pending |
| M5: Hardening & Tests | ⏳ | Regression suite pending |

---

## Next Steps

### Immediate (Milestone 4)
1. Create React components for team visualization
2. Add team execution panel to control surface
3. Implement collaboration stream UI
4. Add decision summary view

### Following (Milestone 5)
1. Create regression test suite
2. Add idempotency tests for team execution
3. Test validator blocking behavior
4. Test round limit enforcement

---

## Migration Instructions

### 1. Apply Database Migration

```bash
# Using Supabase CLI
supabase db push migrations/018_agent_teams.sql

# Or via psql
psql $DATABASE_URL -f migrations/018_agent_teams.sql
```

### 2. Update API Routes

```python
# In torq_console/api/server.py or routes.py
from torq_console.teams import router as teams_router

app.include_router(teams_router)
```

### 3. Initialize Registry

```python
# On application startup
from torq_console.teams import initialize_registry

await initialize_registry(supabase)
```

---

## Testing

### Unit Tests

```bash
# Test team registry
python -m pytest tests/teams/test_registry.py

# Test decision engine
python -m pytest tests/teams/test_decision_engine.py

# Test orchestrator
python -m pytest tests/teams/test_orchestrator.py
```

### Integration Tests

```bash
# Run full team execution
python scripts/test_agent_teams.py

# Run regression suite
python scripts/regression_phase_5_2.py
```

---

## File Structure

```
torq_console/teams/
├── __init__.py          # Module exports
├── models.py            # Data models & enums
├── registry.py          # Team definition registry
├── orchestrator.py      # Core orchestrator
├── role_runner.py       # Role execution
├── decision_engine.py   # Decision policies
├── persistence.py       # Database persistence
├── context.py           # Workspace context
└── api.py              # FastAPI routes
```

---

## Developer Notes

### MVP Limitations

- Only deliberative_review pattern implemented
- Simulated agent outputs (replace with real agent calls)
- No cross-team coordination
- No dynamic team formation

### Production Requirements

- Connect RoleRunner to actual agent framework
- Implement parallel_synthesis pattern
- Implement supervisor_workers pattern
- Add team performance metrics
- Add team optimization engine

---

*End of Implementation Package*
