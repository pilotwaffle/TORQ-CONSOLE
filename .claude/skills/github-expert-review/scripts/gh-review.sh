#!/usr/bin/env bash
set -euo pipefail

# GitHub Expert Review Evidence Gatherer
# Collects evidence for Claude to produce the structured audit report.
#
# Usage: ./scripts/gh-review.sh OWNER/REPO [--local-path /path/to/repo]

REPO="${1:-}"
LOCAL_PATH=""

shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --local-path) LOCAL_PATH="${2:-}"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ -z "$REPO" ]]; then
  echo "Usage: $0 OWNER/REPO [--local-path /path/to/repo]" >&2
  exit 1
fi

echo "== GitHub Expert Review Evidence =="
echo "Repo: $REPO"
echo

# --- A) Inventory ---
echo "## A) Repo Overview"
gh repo view "$REPO" --json nameWithOwner,defaultBranchRef,isPrivate,visibility,description,url,primaryLanguage,languages,isArchived,isFork,hasIssuesEnabled,hasWikiEnabled 2>/dev/null || echo "(Could not fetch repo info)"

echo
echo "## A.1) Languages"
gh api "/repos/${REPO}/languages" 2>/dev/null || echo "(Could not fetch languages)"

echo
echo "## A.2) Topics/Tags"
gh api "/repos/${REPO}/topics" -H "Accept: application/vnd.github.mercy-preview+json" 2>/dev/null || echo "(Could not fetch topics)"

# --- B) Governance ---
echo
echo "## B) Branch Protections / Rulesets"
DEFAULT_BRANCH="$(gh repo view "$REPO" --json defaultBranchRef -q '.defaultBranchRef.name' 2>/dev/null || echo 'main')"
echo "Default branch: $DEFAULT_BRANCH"

echo
echo "### B.1) Branch Protection Rules"
gh api "/repos/${REPO}/branches/${DEFAULT_BRANCH}/protection" 2>/dev/null || echo "(No branch protection configured or insufficient permissions)"

echo
echo "### B.2) Repository Rulesets"
gh api "/repos/${REPO}/rulesets" 2>/dev/null || echo "(No rulesets or not available)"

echo
echo "### B.3) CODEOWNERS"
for CODEOWNERS_PATH in ".github/CODEOWNERS" "CODEOWNERS" "docs/CODEOWNERS"; do
  gh api "/repos/${REPO}/contents/${CODEOWNERS_PATH}" 2>/dev/null && echo "  Found: $CODEOWNERS_PATH" && break
done || echo "(No CODEOWNERS file found)"

echo
echo "### B.4) PR/Issue Templates"
gh api "/repos/${REPO}/contents/.github/pull_request_template.md" 2>/dev/null && echo "  PR template found" || echo "  No PR template"
gh api "/repos/${REPO}/contents/.github/ISSUE_TEMPLATE" 2>/dev/null && echo "  Issue templates found" || echo "  No issue templates"

# --- C) Supply Chain Security ---
echo
echo "## C) Supply Chain Security"

echo
echo "### C.1) Dependabot Alerts (first 10)"
gh api "/repos/${REPO}/dependabot/alerts?per_page=10&state=open" 2>/dev/null || echo "(Dependabot alerts not accessible)"

echo
echo "### C.2) Dependabot Config"
gh api "/repos/${REPO}/contents/.github/dependabot.yml" 2>/dev/null && echo "  dependabot.yml found" || echo "  No dependabot.yml"

# --- D) Code & Secret Security ---
echo
echo "## D) Code & Secret Security"

echo
echo "### D.1) Code Scanning Alerts (first 10)"
gh api "/repos/${REPO}/code-scanning/alerts?per_page=10&state=open" 2>/dev/null || echo "(Code scanning not enabled or not accessible)"

echo
echo "### D.2) Secret Scanning Alerts (first 10)"
gh api "/repos/${REPO}/secret-scanning/alerts?per_page=10&state=open" 2>/dev/null || echo "(Secret scanning not enabled or not accessible)"

# --- E) Actions / Workflows ---
echo
echo "## E) GitHub Actions"

echo
echo "### E.1) Workflow Files"
gh api "/repos/${REPO}/contents/.github/workflows" 2>/dev/null | jq -r '.[].name' 2>/dev/null || echo "(No workflows or not accessible)"

# If we have local access, do deeper inspection
INSPECT_DIR=""
if [[ -n "$LOCAL_PATH" && -d "$LOCAL_PATH/.github/workflows" ]]; then
  INSPECT_DIR="$LOCAL_PATH"
else
  # Try a shallow clone to temp dir for inspection
  TMPDIR="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR"' EXIT
  if gh repo clone "$REPO" "$TMPDIR/repo" -- --depth=1 >/dev/null 2>&1; then
    INSPECT_DIR="$TMPDIR/repo"
  fi
fi

if [[ -n "$INSPECT_DIR" && -d "$INSPECT_DIR/.github/workflows" ]]; then
  echo
  echo "### E.2) Workflow Permission Blocks"
  rg -n "^\s*permissions\s*:" "$INSPECT_DIR/.github/workflows" 2>/dev/null || echo "  No explicit permissions blocks found (review needed)"

  echo
  echo "### E.3) Unpinned Actions (using version tags instead of SHA)"
  rg -n "uses:\s*.+@v[0-9]" "$INSPECT_DIR/.github/workflows" 2>/dev/null | head -20 || echo "  No unpinned-by-tag actions found (good or no actions)"

  echo
  echo "### E.4) Self-Hosted Runners"
  rg -n "runs-on:\s*\[?self-hosted" "$INSPECT_DIR/.github/workflows" 2>/dev/null || echo "  No self-hosted runners found"

  echo
  echo "### E.5) Secret Patterns in Repo"
  rg -n --hidden --glob '!**/node_modules/**' --glob '!**/.git/**' \
    "(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9_]{20,}|xox[baprs]-|BEGIN RSA PRIVATE KEY|PRIVATE KEY-----)" \
    "$INSPECT_DIR" 2>/dev/null | head -10 || echo "  No obvious secret patterns found"

  echo
  echo "### E.6) .gitignore Coverage"
  if [[ -f "$INSPECT_DIR/.gitignore" ]]; then
    echo "  .gitignore exists. Checking for sensitive patterns..."
    for PATTERN in ".env" "*.pem" "*.key" "credentials" "secrets"; do
      if grep -q "$PATTERN" "$INSPECT_DIR/.gitignore" 2>/dev/null; then
        echo "    Covered: $PATTERN"
      else
        echo "    MISSING: $PATTERN"
      fi
    done
  else
    echo "  WARNING: No .gitignore file found"
  fi
fi

# --- F) Release ---
echo
echo "## F) Releases"
gh api "/repos/${REPO}/releases?per_page=5" 2>/dev/null | jq -r '.[] | "\(.tag_name) - \(.published_at) - \(.name)"' 2>/dev/null | head -5 || echo "(No releases found)"

# --- Rate Limits ---
echo
echo "## Rate Limits Snapshot"
gh api /rate_limit 2>/dev/null | jq '.resources.core' 2>/dev/null || echo "(Could not fetch rate limits)"

echo
echo "== Evidence collection complete =="
echo "== Use /github-review in Claude Code for the full structured report =="
