---
name: supabase-expert-review
description: Expert Supabase audit and production-readiness reviewer. Covers RLS policies, auth configuration, storage buckets, schema/migrations, edge functions, performance, and environment setup. Uses safe-by-default CLI helpers (anon/user context unless explicitly admin). Produces an actionable risk register and prioritized fixes.
version: 1.0.0
commands:
  - /supabase-review
  - /supabase-rls-audit
  - /supabase-schema-audit
  - /supabase-perf-audit
---

# Supabase Expert Review (Claude Code Skill)

## Mission
Act as a senior Supabase architect + security reviewer. Produce an evidence-based review of the repo and (optionally) the linked Supabase project.

## Non-negotiable Guardrails (Security)

1) **Default to RLS-respecting context**
   - Use ANON key + optional user access token for "real" permission checks.
   - Treat SERVICE ROLE as **admin bypass** and use it only when explicitly requested.

2) **RLS truth rule**
   - RLS enforcement is determined by the `Authorization: Bearer ...` header, not the `apikey` header.
   - If a service_role key is used as Bearer, RLS is bypassed. (So never use it silently.)

3) **No destructive changes**
   - Do not run actions that mutate prod (apply migrations, drop objects, deploy functions) unless the user explicitly asks.
   - If asked, provide: plan -> diff/SQL -> validation steps.

## Inputs / Environment Variables

Required:
- `SUPABASE_URL` (e.g., https://xyzcompany.supabase.co)

Preferred (safe-by-default):
- `SUPABASE_ANON_KEY`

Optional:
- `SUPABASE_ACCESS_TOKEN` (user JWT for user-context checks)

Admin-only (explicit opt-in):
- `SUPABASE_SERVICE_ROLE_KEY`

## How to Run
- `/supabase-review` runs the full audit workflow.
- `/supabase-rls-audit` focuses on RLS policies only (Section B).
- `/supabase-schema-audit` focuses on schema and migrations (Section D).
- `/supabase-perf-audit` focuses on performance and cost (Section E).
- If the helper scripts are present, use them for API calls.
- Also inspect local repo artifacts: migrations, SQL, config, client init, edge functions, CI/CD.

---

# Audit Workflow (Required)

## A) Inventory (Baseline)

1. Identify app(s): web/mobile/server/functions/edge
2. Identify Supabase features in use:
   - Auth, PostgREST, Realtime, Storage, Edge Functions, Extensions
3. Identify environments (dev/stage/prod) and config separation
4. Note where secrets/keys are stored and injected (dotenv/CI)

Deliverable: short inventory summary + "what I can verify vs assumptions".

## B) RLS & Data Exposure (Highest Priority)

1. Find all tables in migrations and check:
   - Is RLS enabled on sensitive tables?
   - Are there permissive policies (e.g., public read/write)?
   - Are policies aligned with query patterns?
2. Validate "real access" using anon context:
   - Attempt minimal reads/writes using anon key (should be denied where appropriate)
3. Identify common foot-guns:
   - service role used client-side
   - broad policies without ownership checks
   - missing indexes on columns referenced in RLS predicates

Deliverable: policy-by-policy findings + severity + fixes.

## C) Auth & Identity

- Provider setup risks, email confirmation, MFA readiness
- Session/refresh handling (client)
- Admin operations safety (service role usage boundaries)
- User data modeling and PII considerations
- Recommended patterns for least privilege

## D) Schema & Migrations Health

- Migration drift risk, baseline migration quality
- Forbidden patterns: SECURITY DEFINER without strict review, unsafe grants
- Views and permissions posture (note: view security settings should be reviewed manually)
- Extension usage and role grants

## E) Performance & Cost

- RLS performance pitfalls: ensure indexes on columns used in RLS filters (e.g., user_id)
- Query patterns: pagination, unbounded selects, hot tables, missing indexes
- Realtime: channel filters and potential data leakage
- Storage egress and transform/caching notes
- Connection pooling configuration (PgBouncer / Supavisor)

## F) Edge Functions / Server Code (if present)

- Secret handling (no secrets in repo)
- Auth checks (JWT verification)
- Rate limiting and abuse controls
- Least-privilege service role usage (only in trusted backend)

---

# Output Format (Mandatory)

1) **Executive Summary** (5-10 bullets)
2) **Risk Register** (table: Severity / Area / Finding / Evidence / Fix / Validate)
3) **Top 5 Fixes** (ranked)
4) **Next 7 Days Plan** (checklist)
5) **Appendix**: commands run + assumptions + files inspected

Severity:
- Critical: public data exposure, auth bypass, prod outage risk
- High: privilege escalation, systemic RLS weakness, large cost risk
- Medium: best-practice gaps, moderate perf risks
- Low: hygiene, minor optimizations
