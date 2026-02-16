# Supabase Risk Register

| Severity | Area | Finding | Evidence | Fix | Validate |
|---|---|---|---|---|---|
| Critical | RLS | Example: Public read on `profiles` table | Policy allows `select` for anon role without restrictions | Restrict to `auth.uid() = user_id` ownership check | Anon GET to `/rest/v1/profiles` returns 401/empty |
| Critical | Keys | Example: service_role key in client bundle | Found in `src/lib/supabase.ts` line 5 | Replace with anon key; move service_role to server only | Build output does not contain service_role string |
| High | Auth | Example: No email confirmation required | Auth config `enable_confirmations = false` | Enable email confirmations in dashboard | Sign-up requires email verification click |
| Medium | Perf | Example: Missing index on RLS predicate column | `user_id` used in RLS policy but no index | `CREATE INDEX idx_posts_user_id ON posts(user_id)` | EXPLAIN shows index scan, not seq scan |
| Low | Schema | Example: No migration baseline | No initial migration file | Run `supabase db diff` to create baseline | Migration history starts from known state |
