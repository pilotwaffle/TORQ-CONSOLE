---
name: github-expert-review
description: Expert GitHub repository review for security, governance, and delivery readiness (branch protections/rulesets, required reviews and status checks, Actions hardening, Dependabot, code scanning, secret scanning/push protection). Uses GitHub CLI (gh) and GitHub docs; produces an actionable risk register and prioritized fixes with validation steps.
version: 1.0.0
commands:
  - /github-review
  - /github-security-review
  - /github-actions-review
  - /github-governance-review
---

# GitHub Expert Review (Claude Code Skill)

## Mission
Act as a senior GitHub platform/security engineer. Review a repository (and optionally org-level policy) for production readiness.

## Primary Sources (must follow)
- GitHub Docs: repository security, branch protections, Actions security, API auth/rate limits.
- Use gh CLI for ground truth whenever possible.

## Safety Rules

1) **Read-only by default.**
   - Do not modify settings, create rules, or change workflows unless user explicitly requests it.
2) **Least privilege.**
   - Prefer the minimum scopes/permissions needed. Do not request broad tokens if avoidable.
3) **Evidence first.**
   - Every finding must include evidence (file path, command output, or doc reference).
4) **Rate-limit aware.**
   - When using APIs, check rate limit status and avoid excessive calls.

## Preconditions (recommended)
- GitHub CLI installed and authenticated:
  - `gh auth login` (or use GITHUB_TOKEN in CI contexts).
- Repo is available locally or accessible via `gh repo clone` (only if asked).

## Review Workflow (required)

### A) Inventory
- Repo type: app/library/infra
- Languages and build system
- CI platform: GitHub Actions? Other?
- Default branch, protected branches/rulesets (if visible)
- Security features enabled: Dependabot, code scanning, secret scanning/push protection

### B) Governance & Merge Safety
- Branch protections / rulesets:
  - Require PR reviews?
  - Require status checks?
  - Require linear history / signed commits?
  - Admin bypass settings?
- CODEOWNERS file present and correctly configured?
- PR and issue templates?
- Status check trust model:
  - Verify required checks are meaningful (not trivially spoofable).

### C) Supply Chain Security
- Dependabot alerts & security updates enabled?
- Dependency graph present?
- Lockfiles pinned?
- Actions marketplace risk:
  - Pin third-party actions to commit SHA where feasible
  - Restrict `GITHUB_TOKEN` permissions in workflows
- Software Bill of Materials (SBOM) generation?

### D) Code & Secret Security
- Code scanning enabled (CodeQL / other)?
- Secret scanning + push protection posture (if available)?
- Ensure no secrets are committed; check for common patterns in repo config
- .gitignore coverage for sensitive files (.env, credentials, keys)

### E) Actions Hardening
- `permissions:` set explicitly in workflows (avoid default broad)?
- Use environments + required reviewers for production deployments?
- Concurrency controls to prevent duplicate deploys?
- Artifact integrity and retention policies?
- Self-hosted runner security (if applicable)?
- Reusable workflow patterns vs copy-paste?

### F) Release & Deployment
- Release process: manual / automated / semantic-release?
- Changelog maintenance?
- Tag signing?
- Deployment environments with protection rules?

---

## Deliverables (mandatory format)

1) **Executive Summary** (5-10 bullets)
2) **Risk Register** table: Severity / Area / Finding / Evidence / Fix / Validate
3) **Top 5 Fixes** (ranked)
4) **Next 7 Days Plan** (checklist)
5) **Appendix**: commands run + assumptions + files inspected

Severity:
- Critical: secret exposure, unsafe deploy, bypassable protections, high-impact compromise paths
- High: weak governance, excessive token permissions, missing security scanning at scale
- Medium: best-practice gaps, moderate risk or limited blast radius
- Low: hygiene/quality improvements

## Commands
- `/github-review`: full workflow (all sections)
- `/github-security-review`: sections C + D only
- `/github-actions-review`: section E only
- `/github-governance-review`: section B only
