# GitHub Risk Register

| Severity | Area | Finding | Evidence | Fix | Validate |
|---|---|---|---|---|---|
| Critical | Secrets | Example: Hardcoded API key in config | `vercel.json` line 12 contains `ANTHROPIC_API_KEY` | Move to GitHub Secrets / environment variables | `grep -r "sk-" .` returns no results |
| Critical | Actions | Example: Workflow uses broad default permissions | `deploy.yml` has no `permissions:` block | Add explicit `permissions: contents: read` | PR check shows restricted token scope |
| High | Governance | Example: No branch protection on main | `gh api .../protection` returns 404 | Enable require PR reviews + status checks | Direct push to main is blocked |
| High | Supply Chain | Example: Actions pinned to version tags | `uses: actions/checkout@v4` | Pin to full commit SHA | All `uses:` reference 40-char SHA |
| Medium | Scanning | Example: No Dependabot config | No `.github/dependabot.yml` | Add dependabot.yml for npm + pip ecosystems | `gh api .../dependabot/alerts` returns data |
| Medium | Templates | Example: No PR template | `.github/pull_request_template.md` missing | Add PR template with checklist | New PR shows template pre-filled |
| Low | Docs | Example: No CODEOWNERS | CODEOWNERS file not found | Add CODEOWNERS for critical paths | PR shows required reviewers auto-assigned |
