# Supabase Next 7 Days Plan

- [ ] Lock down any public read/write policies on sensitive tables
- [ ] Add indexes for columns used in RLS predicates (user_id, org_id, team_id)
- [ ] Verify user-context access using a real JWT (no service role on client)
- [ ] Remove any service_role key references from client-side code
- [ ] Review storage bucket access rules and signed URL usage
- [ ] Add rate limiting + auth verification to edge functions
- [ ] Create baseline migration + CI check for drift
- [ ] Enable email confirmations and consider MFA for sensitive operations
- [ ] Configure connection pooling (PgBouncer/Supavisor) for production scale
- [ ] Add monitoring/alerts for auth anomalies and query cost spikes
- [ ] Review Realtime channel subscriptions for data leakage risks
- [ ] Document rollback procedure for migrations and edge function deployments
