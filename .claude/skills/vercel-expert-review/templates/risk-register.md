# Vercel Risk Register

| Severity | Area | Finding | Evidence | Fix | Validate |
|---|---|---|---|---|---|
| Critical | Secrets | Example: API keys hardcoded in vercel.json | `vercel.json` line 8 contains `ANTHROPIC_API_KEY=sk-...` | Move to Vercel Dashboard > Environment Variables (encrypted) | `grep -r "sk-" vercel.json` returns empty |
| Critical | Env | Example: Service key exposed via NEXT_PUBLIC_ | `NEXT_PUBLIC_SUPABASE_SERVICE_KEY` in .env | Rename without NEXT_PUBLIC_ prefix; use server-side only | Client bundle does not contain service key |
| High | Protection | Example: Preview deployments publicly accessible | No deployment protection configured | Enable Standard Protection in Project Settings | Preview URLs require Vercel auth |
| High | Headers | Example: No Content-Security-Policy | No CSP in vercel.json or middleware | Add CSP header via vercel.json headers or middleware | Response includes CSP header |
| Medium | Observability | Example: No error tracking | No Sentry/monitoring integration found | Add @sentry/nextjs or @vercel/analytics | Error tracking captures test exception |
| Medium | Caching | Example: No cache-control headers on API routes | API routes return no Cache-Control | Add appropriate s-maxage and stale-while-revalidate | curl -I shows correct cache headers |
| Low | Images | Example: Not using Vercel Image Optimization | Raw img tags instead of next/image | Replace with next/image component | Lighthouse image audit passes |
