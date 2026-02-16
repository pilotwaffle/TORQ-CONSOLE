# GitHub Next 7 Days Plan

- [ ] Lock down default branch: require PR reviews + required status checks
- [ ] Enable/verify Dependabot alerts + security updates
- [ ] Enable/verify code scanning (CodeQL default setup if appropriate)
- [ ] Enable/verify secret scanning + push protection (if plan allows)
- [ ] Harden Actions: explicit permissions, pin actions to SHA, protect environments
- [ ] Add CODEOWNERS file with required review paths for critical folders
- [ ] Add PR template (`.github/pull_request_template.md`) with checklist
- [ ] Add issue templates (bug report + feature request)
- [ ] Remove any committed secrets and rotate affected credentials
- [ ] Ensure .gitignore covers .env, *.pem, *.key, credentials files
- [ ] Document release + rollback playbook in /docs
- [ ] Review and restrict GITHUB_TOKEN permissions across all workflows
