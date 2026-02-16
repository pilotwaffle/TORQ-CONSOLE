# PRD: Fix TORQ Console Vercel Deployment Failures

**Document:** Product Requirements Document
**Version:** 1.0
**Date:** 2026-02-16
**Author:** Claude Code (GitHub + Vercel Expert Review)
**Priority:** P0 (Critical) / P1 (High)
**Status:** Draft

---

## 1. Executive Summary

TORQ Console cannot deploy on Vercel. A combined GitHub Expert Review and Vercel Expert Review identified **8 blocking issues** across security, dependency management, import architecture, and configuration. This PRD defines the root causes, required fixes, implementation plan, and acceptance criteria to achieve a successful Vercel deployment.

### Key Findings

| # | Issue | Severity | Category |
|---|-------|----------|----------|
| 1 | Hardcoded API keys in `vercel.json` (Anthropic + OpenAI) | **CRITICAL** | Security |
| 2 | Heavy ML dependencies exceed Vercel's 250MB function limit | **CRITICAL** | Architecture |
| 3 | Eager import chain loads numpy/sklearn/sentence-transformers at startup | **CRITICAL** | Architecture |
| 4 | `buildCommand` in vercel.json ignores `requirements-vercel.txt` | **CRITICAL** | Configuration |
| 5 | Missing dependencies in `requirements-vercel.txt` | **HIGH** | Dependencies |
| 6 | Broken `handler()` function in `api/index.py` | **HIGH** | Implementation |
| 7 | No GitHub branch protection / governance | **HIGH** | Governance |
| 8 | Frontend build not configured for Vercel | **MEDIUM** | Configuration |

---

## 2. Problem Statement

### 2.1 What Happens When You Deploy

When Vercel attempts to deploy TORQ Console, the following failure cascade occurs:

```
Step 1: Vercel reads vercel.json
  └─ buildCommand installs only 13 packages (misses ~10 required packages)
  └─ @vercel/python builds api/index.py as serverless function

Step 2: api/index.py executes at cold start
  └─ Line 18: `from torq_console.ui.railway_app import app`
      └─ railway_app.py line 107: `app = create_railway_app()`
          └─ Line 45: `from torq_console.core.console import TorqConsole`
              └─ console.py line 31: `from ..llm.manager import LLMManager`
                  └─ manager.py line 27: `from torq_console.indexer.semantic_search import SemanticSearch`
                      └─ semantic_search.py line 17: `from .vector_store import VectorStore`
                          └─ vector_store.py line 11: `import numpy as np`
                              └─ FAILURE: numpy not installed (not in buildCommand)
                              └─ Even if installed: numpy + sklearn + sentence-transformers > 850MB
                              └─ Vercel function size limit: 250MB
```

### 2.2 Why the Fallback Doesn't Work

`railway_app.py` has a `try/except` fallback (line 79-102) that creates a minimal FastAPI app if initialization fails. However, the import of `TorqConsole` fails **during module-level imports** (not during `__init__`), which means Python raises `ModuleNotFoundError` before the `try` block can catch it. Additionally, the `buildCommand` doesn't install all required packages, so even the fallback's FastAPI imports may fail for transitive dependencies.

---

## 3. Root Cause Analysis

### 3.1 CRITICAL: Hardcoded API Keys (Security Breach)

**File:** `vercel.json` lines 23-24

```json
"ANTHROPIC_API_KEY": "sk-ant-api03-...",
"OPENAI_API_KEY": "sk-proj-..."
```

**Impact:**
- Both keys are committed to a public repository
- Keys are in git history across 5+ commits
- Keys must be considered **compromised** and rotated immediately

**Root Cause:** Developer hardcoded keys to work around Vercel env var configuration, then committed the file.

### 3.2 CRITICAL: ML Dependency Size Exceeds Vercel Limits

**Vercel Serverless Function Limit:** 250MB (unzipped)

**Current transitive dependency chain:**

| Package | Approximate Size | Required By |
|---------|-----------------|-------------|
| numpy | ~100MB | vector_store, embeddings, 13 other modules |
| scikit-learn | ~50MB | embeddings.py (TfidfVectorizer) |
| sentence-transformers | ~500MB | embeddings.py (SentenceTransformer) |
| torch (transitive) | ~800MB | sentence-transformers dependency |
| faiss-cpu | ~50MB | vector_store.py |
| **Total** | **~1,500MB** | **6x over Vercel limit** |

**Root Cause:** The application was designed for Railway/Docker (no size limits) and the Vercel entry point imports the same monolithic code path.

### 3.3 CRITICAL: Eager Import Chain

The import chain from `api/index.py` to numpy is only 6 levels deep with **zero** lazy loading:

```
api/index.py → railway_app → console.py → llm/manager.py → semantic_search.py → embeddings.py → numpy
```

Every import is top-level (`import X` at module scope), so Python resolves the entire chain at cold start. There are no conditional imports gated by `TORQ_DISABLE_LOCAL_LLM` or `TORQ_DISABLE_GPU` environment variables, despite those being set.

**Root Cause:** Environment variables are set but never checked in the import chain. The `TORQ_DISABLE_LOCAL_LLM` flag is unused by `LLMManager` or `SemanticSearch`.

### 3.4 CRITICAL: buildCommand Ignores requirements-vercel.txt

**File:** `vercel.json` line 5

```json
"buildCommand": "pip install fastapi uvicorn python-multipart pydantic jinja2 python-dotenv aiofiles httpx anthropic openai pyyaml click rich"
```

This hardcodes 13 specific packages inline instead of using `requirements-vercel.txt` (which has 15 packages). The `@vercel/python` builder normally auto-detects `requirements.txt`, but the explicit `buildCommand` overrides that behavior.

**Root Cause:** Developer added buildCommand to control which packages are installed (avoiding ML deps), but this disconnects from the requirements file.

### 3.5 HIGH: Missing Dependencies in requirements-vercel.txt

Even if `requirements-vercel.txt` were used, it's missing packages required by the import chain:

| Missing Package | Required By |
|-----------------|------------|
| `gitpython>=3.1.0` | `torq_console.utils.git_manager` (imported by console.py) |
| `typer>=0.9.0` | `torq_console.cli` (imported transitively) |
| `python-socketio>=5.9.0` | `torq_console.ui.web` (imported by railway_app.py) |
| `psutil>=5.9.0` | `torq_console.core` (imported by various modules) |
| `watchdog>=3.0.0` | `torq_console.utils.file_monitor` (imported by console.py) |

### 3.6 HIGH: Broken handler() in api/index.py

**File:** `api/index.py` lines 21-50

The `handler()` function:
1. Constructs an ASGI scope manually (incomplete — missing body, client address)
2. Creates an `async def asgi_handler()` but never calls it
3. Returns a static JSON response regardless of the request
4. Is redundant because `asgi_app = app` on line 53 is the correct Vercel pattern

**Root Cause:** Mixed two approaches — Vercel's ASGI adapter (`asgi_app`) and a manual handler function — without completing either.

### 3.7 HIGH: No GitHub Governance

From the GitHub Expert Review:

| Missing | Risk |
|---------|------|
| No branch protection on `main` | Anyone can push directly, including secrets |
| No CODEOWNERS | No automatic review requirements |
| No PR templates | Inconsistent PR quality |
| No Dependabot | Dependencies never auto-updated |
| No code scanning | Vulnerabilities not auto-detected |
| Non-blocking linting | ruff/mypy run with `|| true`, issues hidden |

This governance gap is **how the API keys got committed** — no review was required.

### 3.8 MEDIUM: Frontend Not Configured for Vercel

The `frontend/` directory contains a React 18 + Vite + TypeScript app, but `vercel.json` only configures the Python API. The frontend is never built or served.

---

## 4. Requirements

### 4.1 P0 — Must Fix (Deployment Blockers)

#### REQ-1: Remove Hardcoded Secrets from vercel.json
- Remove `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` values from `vercel.json`
- Replace with placeholder references: `"@anthropic_api_key"` or empty strings
- Add comment directing users to set via Vercel Dashboard > Settings > Environment Variables
- **Acceptance:** `grep -r "sk-ant\|sk-proj" vercel.json` returns empty

#### REQ-2: Create Vercel-Specific Lightweight Entry Point
- Create `api/index.py` that does NOT import `torq_console.ui.railway_app`
- The entry point must only import FastAPI and lightweight packages
- ML/AI features must be excluded entirely from the Vercel function
- Provide API-only endpoints: `/health`, `/api/chat` (proxying to Anthropic/OpenAI directly), `/api/status`
- **Acceptance:** `api/index.py` imports resolve in <2 seconds with only packages from `requirements-vercel.txt`

#### REQ-3: Fix vercel.json Build Configuration
- Remove `buildCommand` override (let `@vercel/python` auto-detect `requirements.txt`)
- Add `requirements-vercel.txt` as the pip requirements source via Vercel's Python builder config
- OR: Rename `requirements-vercel.txt` to `api/requirements.txt` (Vercel auto-detects per-directory requirements)
- **Acceptance:** Vercel build installs all packages from requirements file without manual buildCommand

#### REQ-4: Ensure requirements-vercel.txt Is Complete
- Add all missing packages needed by the lightweight entry point
- Exclude ALL ML packages (numpy, scikit-learn, sentence-transformers, torch, faiss)
- Total installed size must be under 200MB
- **Acceptance:** `pip install -r requirements-vercel.txt` succeeds; total size < 200MB

### 4.2 P1 — Should Fix (Security + Governance)

#### REQ-5: Rotate Compromised API Keys
- Rotate Anthropic API key via Anthropic Console
- Rotate OpenAI API key via OpenAI Dashboard
- Set new keys ONLY in Vercel Dashboard (encrypted environment variables)
- **Acceptance:** Old keys return 401; new keys only exist in Vercel Dashboard

#### REQ-6: Enable GitHub Branch Protection
- Require PR reviews (minimum 1 reviewer) on `main`
- Require CI status checks to pass before merge
- Disable direct push to `main`
- **Acceptance:** Direct `git push origin main` is rejected

#### REQ-7: Add Dependabot Configuration
- Create `.github/dependabot.yml` for pip, npm, and github-actions ecosystems
- **Acceptance:** Dependabot PRs appear within 24 hours

#### REQ-8: Add CODEOWNERS
- Create `.github/CODEOWNERS` with maintainer assignments
- At minimum: `* @pilotwaffle`
- **Acceptance:** PRs auto-request review from code owners

#### REQ-9: Make CI Checks Blocking
- Remove `|| true` from ruff and mypy steps in `ci.yml`
- Failing lint/type checks should block merge
- **Acceptance:** CI fails on lint errors (not silently passes)

### 4.3 P2 — Nice to Have (Improvements)

#### REQ-10: Add PR and Issue Templates
- `.github/pull_request_template.md` with checklist
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`

#### REQ-11: Configure Frontend Deployment
- Either: Deploy frontend separately (Vercel static site)
- Or: Bundle frontend build into Python API static file serving
- Or: Use Vercel monorepo support with separate build targets

#### REQ-12: Add .gitignore Patterns for Deployment Credentials
- Add patterns: `*.key`, `*.pem`, `credentials.json`, `secrets.json`
- Ensure `.vercel/` directory is gitignored

---

## 5. Technical Design

### 5.1 New Vercel Entry Point (REQ-2)

Replace `api/index.py` with a lightweight FastAPI app that does NOT import the monolithic `TorqConsole`:

```python
"""
Vercel serverless function entry point for TORQ Console.
Lightweight API-only deployment — no ML/GPU dependencies.
"""
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

os.environ.setdefault('TORQ_CONSOLE_PRODUCTION', 'true')
os.environ.setdefault('TORQ_DISABLE_LOCAL_LLM', 'true')
os.environ.setdefault('TORQ_DISABLE_GPU', 'true')

app = FastAPI(
    title="TORQ Console API",
    version="0.80.0",
    description="TORQ Console - Vercel Serverless Deployment"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"service": "torq-console", "status": "running", "platform": "vercel"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/chat")
async def chat(request: Request):
    """Chat endpoint that proxies to Anthropic/OpenAI directly."""
    import anthropic
    body = await request.json()
    message = body.get("message", "")

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": message}]
    )
    return {"response": response.content[0].text}

# Vercel ASGI export
app = app
```

### 5.2 Fixed vercel.json (REQ-1, REQ-3)

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "version": 2,
  "name": "torq-console",
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ],
  "env": {
    "TORQ_CONSOLE_PRODUCTION": "true",
    "TORQ_DISABLE_LOCAL_LLM": "true",
    "TORQ_DISABLE_GPU": "true",
    "PYTHON_VERSION": "3.11"
  }
}
```

Key changes:
- **Removed** `buildCommand` (let @vercel/python auto-detect requirements)
- **Removed** hardcoded API keys
- **Removed** `outputDirectory` (not needed for Python)
- API keys set via Vercel Dashboard only

### 5.3 Fixed requirements-vercel.txt (REQ-4)

```
# Lightweight requirements for Vercel deployment
# NO ML/GPU packages (numpy, sklearn, torch, sentence-transformers, faiss)
fastapi>=0.100.0
uvicorn>=0.20.0
python-multipart>=0.0.6
pydantic>=2.8.0,<3.0.0
python-dotenv>=1.0.0
aiofiles>=23.0.0
httpx>=0.24.0
anthropic>=0.20.0
openai>=1.0.0
pyyaml>=6.0.0
click>=8.0.0
rich>=13.0.0
jinja2>=3.1.0
```

Key changes:
- **Removed** `uvicorn[standard]` (extras pull in heavy deps; use base uvicorn)
- **Removed** `websockets`, `prompt_toolkit` (not needed for API-only)
- **Kept** only what the lightweight entry point actually imports
- Total estimated size: ~80MB (well under 250MB limit)

### 5.4 Dependabot Configuration (REQ-7)

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## 6. Implementation Plan

### Phase 1: Emergency Security Fix (Day 1)

| Step | Task | Files Changed |
|------|------|---------------|
| 1.1 | Remove hardcoded API keys from vercel.json | `vercel.json` |
| 1.2 | Rotate both API keys on provider dashboards | External |
| 1.3 | Set new keys in Vercel Dashboard env vars | External |

### Phase 2: Fix Vercel Deployment (Days 2-3)

| Step | Task | Files Changed |
|------|------|---------------|
| 2.1 | Rewrite `api/index.py` as lightweight entry point | `api/index.py` |
| 2.2 | Fix `vercel.json` (remove buildCommand, remove secrets) | `vercel.json` |
| 2.3 | Fix `requirements-vercel.txt` (complete + lightweight) | `requirements-vercel.txt` |
| 2.4 | Add `api/requirements.txt` symlink or copy | `api/requirements.txt` |
| 2.5 | Test Vercel deployment | Vercel Dashboard |

### Phase 3: GitHub Governance (Days 4-5)

| Step | Task | Files Changed |
|------|------|---------------|
| 3.1 | Enable branch protection on `main` | GitHub Settings |
| 3.2 | Create `.github/CODEOWNERS` | `.github/CODEOWNERS` |
| 3.3 | Create `.github/dependabot.yml` | `.github/dependabot.yml` |
| 3.4 | Make CI checks blocking (remove `\|\| true`) | `.github/workflows/ci.yml` |
| 3.5 | Add PR template | `.github/pull_request_template.md` |
| 3.6 | Add issue templates | `.github/ISSUE_TEMPLATE/` |
| 3.7 | Update `.gitignore` with credential patterns | `.gitignore` |

### Phase 4: Frontend Deployment (Day 6-7, Optional)

| Step | Task | Files Changed |
|------|------|---------------|
| 4.1 | Decide deployment strategy (separate Vercel project or monorepo) | Architecture decision |
| 4.2 | Configure frontend build for Vercel | `vercel.json` or separate project |
| 4.3 | Test end-to-end with frontend + API | Integration test |

---

## 7. Risk Register (Combined GitHub + Vercel Review)

| Severity | Area | Finding | Evidence | Fix | Validate |
|---|---|---|---|---|---|
| **CRITICAL** | Security | Hardcoded Anthropic + OpenAI API keys in vercel.json | `vercel.json:23-24` contains `sk-ant-...` and `sk-proj-...` | Remove from file; rotate keys; use Vercel Dashboard | `grep -r "sk-ant\|sk-proj" .` returns empty |
| **CRITICAL** | Deployment | ML deps (numpy, torch, sklearn) exceed 250MB Vercel limit | `pyproject.toml:49-51`; import chain: `api/index.py → railway_app → console → llm/manager → semantic_search → embeddings → numpy` | Create lightweight entry point that doesn't import ML chain | `pip install -r requirements-vercel.txt` size < 200MB |
| **CRITICAL** | Deployment | buildCommand overrides requirements file detection | `vercel.json:5` hardcodes 13 packages inline | Remove buildCommand; let @vercel/python auto-detect | Vercel build log shows requirements file used |
| **CRITICAL** | Architecture | Eager imports load all 561 Python modules at cold start | `railway_app.py:107` calls `create_railway_app()` at module level → imports entire TorqConsole | Vercel entry point imports only FastAPI + direct deps | Cold start < 5 seconds |
| **HIGH** | Dependencies | requirements-vercel.txt missing gitpython, typer, psutil, watchdog, socketio | Import chain requires these but they're not listed | Either add them OR rewrite entry point to not need them | All imports resolve without error |
| **HIGH** | Implementation | handler() in api/index.py never calls ASGI app, returns static JSON | `api/index.py:42-50` creates async handler but returns JSONResponse instead | Remove handler(); rely on `app` export for @vercel/python ASGI | All routes return dynamic responses |
| **HIGH** | Governance | No branch protection on main branch | No protection rules in GitHub settings | Enable required reviews + status checks | Direct push to main is rejected |
| **HIGH** | Governance | CI lint/type checks non-blocking | `ci.yml` uses `ruff check . \|\| true` and `mypy . \|\| true` | Remove `\|\| true` suffix | CI fails when lint errors exist |
| **MEDIUM** | Security | No Dependabot configuration | No `.github/dependabot.yml` | Add dependabot.yml for pip, npm, github-actions | Dependabot PRs appear within 24h |
| **MEDIUM** | Governance | No CODEOWNERS file | No `.github/CODEOWNERS` | Create with `* @pilotwaffle` | PRs auto-request review |
| **MEDIUM** | Governance | No PR/issue templates | No `.github/pull_request_template.md` or `ISSUE_TEMPLATE/` | Add templates with checklists | New PRs show template |
| **MEDIUM** | Deployment | Frontend not configured for Vercel | `frontend/` exists with React+Vite but vercel.json only targets Python API | Configure separate build or monorepo support | Frontend accessible at deployed URL |
| **LOW** | Security | .gitignore missing credential patterns | No `*.key`, `*.pem`, `credentials.json` patterns | Add patterns to .gitignore | Sensitive file types are ignored |

---

## 8. Acceptance Criteria

### Deployment Success
- [ ] `vercel deploy` completes without errors
- [ ] `/health` endpoint returns `{"status": "healthy"}`
- [ ] `/api/chat` endpoint accepts POST with message and returns AI response
- [ ] Function size is under 250MB
- [ ] Cold start is under 10 seconds
- [ ] No secrets in repository files (verified by `grep`)

### Security
- [ ] Old API keys are rotated and return 401
- [ ] New keys exist ONLY in Vercel Dashboard (encrypted)
- [ ] `vercel.json` contains no secret values
- [ ] Branch protection prevents direct push to main

### Governance
- [ ] PRs require at least 1 review
- [ ] CI status checks must pass before merge
- [ ] Dependabot is active for pip, npm, and github-actions
- [ ] CODEOWNERS assigns reviewers automatically

---

## 9. Out of Scope

- Migrating the full TorqConsole (ML features) to Vercel — Railway/Docker remains the full-feature deployment target
- Rewriting the SemanticSearch system for lazy loading (desirable but not required for Vercel)
- Git history rewriting to remove exposed keys (high-risk operation; key rotation is sufficient)
- Org-level GitHub security policies (single-repo scope for now)

---

## 10. Dependencies

| Dependency | Owner | Status |
|-----------|-------|--------|
| Anthropic API key rotation | Project maintainer | Required before production |
| OpenAI API key rotation | Project maintainer | Required before production |
| Vercel Dashboard access | Project maintainer | Required for env var setup |
| GitHub repo admin access | Project maintainer | Required for branch protection |

---

## 11. Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Vercel deployment success | 100% | 0% (all deploys fail) |
| Function size | < 200MB | > 1,500MB (estimated) |
| Cold start time | < 10s | N/A (fails to start) |
| Exposed secrets | 0 | 2 (Anthropic + OpenAI keys) |
| CI checks blocking | Yes | No (|| true) |
| Branch protection | Enabled | Disabled |

---

*Generated by Claude Code using GitHub Expert Review + Vercel Expert Review skills on 2026-02-16.*
