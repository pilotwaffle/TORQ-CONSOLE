# Phase 5.2 - Database Migration Instructions

## Status: Migration Pending

The Phase 5.2 Agent Teams schema has been implemented but not yet applied to the database.

## Step-by-Step Migration

### Option 1: Via Supabase CLI (Recommended)

```bash
cd E:/TORQ-CONSOLE
supabase db push migrations/018_agent_teams.sql
```

### Option 2: Via Supabase Dashboard

1. Go to https://app.supabase.com/project/npukynbaglmcdvzyklqa/sql/new
2. Copy contents of `migrations/018_agent_teams.sql`
3. Paste and run

### Option 3: Via psql (if you have direct access)

```bash
psql $DATABASE_URL -f migrations/018_agent_teams.sql
```

## Tables to be Created

| Table | Purpose | Rows (Initial) |
|-------|---------|----------------|
| `agent_teams` | Team definitions | 3 (planning, research, build) |
| `agent_team_members` | Role configurations | 12 (4 per team) |
| `team_executions` | Execution tracking | 0 |
| `team_messages` | Collaboration events | 0 |
| `team_decisions` | Final decisions | 0 |

## Views Created

- `v_active_teams_with_members` - Teams with member details
- `v_team_execution_summary` - Execution summaries

## RLS Policies

All tables have Row Level Security enabled:
- `authenticated` role: Read-only access
- `service_role`: Full access

## Migration Verification

After running migration, verify:

```sql
-- Check tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE 'agent_team%'
OR table_name LIKE 'team_%';

-- Expected: 5 tables
```

## Rollback (If Needed)

```sql
DROP TABLE IF EXISTS public.team_decisions CASCADE;
DROP TABLE IF EXISTS public.team_messages CASCADE;
DROP TABLE IF EXISTS public.team_executions CASCADE;
DROP TABLE IF EXISTS public.agent_team_members CASCADE;
DROP TABLE IF EXISTS public.agent_teams CASCADE;
```

## Post-Migration Steps

After migration is applied:

1. Verify API routes load: http://localhost:8000/docs
2. Run regression suite: `python scripts/regression_phase_5_2.py`
3. Test team execution: `POST /api/teams/missions/{id}/nodes/{id}/run-team`
