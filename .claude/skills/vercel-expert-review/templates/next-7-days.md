# Vercel Next 7 Days Plan

- [ ] Remove all hardcoded secrets from vercel.json and source code
- [ ] Move sensitive env vars to Vercel Dashboard (encrypted, properly scoped)
- [ ] Enable deployment protection on all preview deployments
- [ ] Configure security headers (CSP, HSTS, X-Frame-Options) via vercel.json or middleware
- [ ] Verify no secrets leak to client via NEXT_PUBLIC_ prefix audit
- [ ] Enable Vercel Speed Insights or Web Vitals tracking
- [ ] Add error monitoring (Sentry, LogRocket, or equivalent)
- [ ] Configure Log Drains for production observability
- [ ] Review and optimize caching headers on API routes and static assets
- [ ] Set up spending limits and usage alerts in Vercel Dashboard
- [ ] Ensure .env.local and .vercel are in .gitignore
- [ ] Document deployment and rollback procedures
