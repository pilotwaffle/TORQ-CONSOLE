# Phase 5.1 Validation — Migration Prerequisites

## Critical Finding: Migrations Not Applied

The remote Supabase database does not have the Phase 5.1 tables (missions, mission_nodes, mission_edges, etc.) because migrations 018-020 have not been applied.

## Required Actions Before Validation

### Option A: Apply Migrations to Remote Supabase (Recommended for Production)

**If you want to validate against the production database:**

1. **Get database connection string:**
   ```bash
   # From Supabase dashboard
   # Project Settings > Database > Connection String
   # Format: postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

2. **Apply migrations using psql:**
   ```bash
   # Set connection string
   export DATABASE_URL="postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres"

   # Apply all migrations
   bash scripts/apply_all_migrations.sh
   ```

3. **Verify:**
   ```bash
   psql $DATABASE_URL -c "SELECT version FROM schema_migrations ORDER BY version;"
   ```

### Option B: Use Local Database for Validation (Recommended for Testing)

**If you want to validate locally first:**

1. **Install PostgreSQL locally:**
   ```bash
   # Windows: Download from https://www.postgresql.org/download/
   # Or use Docker:
   docker run --name torq-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:15
   ```

2. **Create local database:**
   ```bash
   psql -U postgres -c "CREATE DATABASE torq_console;"
   ```

3. **Update .env.local:**
   ```bash
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/torq_console
   ```

4. **Apply migrations:**
   ```bash
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/torq_console"
   bash scripts/apply_all_migrations.sh
   ```

### Option C: Use Supabase CLI (Best for Development)

**If you have Supabase CLI installed:**

1. **Link to project:**
   ```bash
   supabase link --project-ref [your-project-ref]
   ```

2. **Apply migrations:**
   ```bash
   supabase db push
   ```

## Migration Order

Migrations must be applied in this order:

| Version | File | Purpose |
|---------|------|---------|
| 001-003 | Earlier migrations | Base schema |
| 004 | shared_cognitive_workspace | Workspace memory |
| 005-009 | Workspace integration | Task/Task graph workspace IDs |
| 010-013 | Adaptive loop | Learning signals, experiments |
| 014-017 | Strategic memory | Memory tables |
| 018 | mission_graphs | Mission graph planning |
| 019 | execution_fabric | Handoffs, workstreams |
| 020 | validation_telemetry | Validation tracking |

## After Migrations Are Applied

### 1. Verify schema

```bash
python -c "
from torq_console.dependencies import get_supabase_client
sb = get_supabase_client()
result = sb.table('missions').select('*', count='exact').limit(0).execute()
print(f'Missions table: {result.count} rows')
"
```

### 2. Run validation environment setup

```bash
bash scripts/prepare_validation_env.sql
```

### 3. Start validation

```bash
python -m torq_console.cli server
```

## Decision Matrix

| Option | Pros | Cons | Recommended For |
|--------|------|------|-----------------|
| Remote Supabase | Tests production env | Affects production data | Final validation only |
| Local PostgreSQL | Safe, fast | Different from prod | Initial validation |
| Supabase CLI | Best of both | Requires setup | Development |

## Recommendation

**Start with local database validation (Option B), then do final validation on remote (Option A).**

This ensures:
- Safe testing environment
- Fast iteration
- No production impact
- Final validation matches production

## Next Steps

1. **Choose your database option** (A, B, or C)
2. **Apply migrations** using the appropriate method
3. **Verify tables exist** using SQL queries below
4. **Proceed with Day 1-2 validation**

---

## Verification Queries

```sql
-- Check all Phase 5.1 tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_name IN (
    'missions',
    'mission_nodes',
    'mission_edges',
    'mission_events',
    'mission_handoffs',
    'workstream_states',
    'validation_telemetry',
    'validation_results'
)
ORDER BY table_name;

-- Expected result: 8 tables
