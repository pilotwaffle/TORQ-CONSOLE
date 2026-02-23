# TORQ Console v2 — Vercel → Railway Deployment Guide

## Architecture
```
Browser → Vercel (UI + proxy) → Railway (full agent brain) → Supabase (learning DB)
```

## Quick Start
1. Create Supabase tables (SQL in `supabase_learning.py`)
2. Create Railway project from `pilotwaffle/TORQ-CONSOLE` GitHub repo
3. Set env vars on Railway: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, ANTHROPIC_API_KEY, TORQ_PROXY_SHARED_SECRET
4. Set env vars on Vercel: TORQ_BACKEND_URL, TORQ_PROXY_SHARED_SECRET
5. Push to main → Vercel auto-deploys proxy, Railway auto-deploys backend

See full guide: `vercel_railway_deployment_guide.md` in outputs
