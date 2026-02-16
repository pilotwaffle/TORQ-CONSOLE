#!/usr/bin/env bash
set -euo pipefail

# Vercel Expert Review Evidence Gatherer
# Collects evidence from local project + Vercel CLI for the audit report.
#
# Usage: ./scripts/vercel-audit.sh [project-root]

ROOT="${1:-.}"

echo "== Vercel Expert Review Evidence =="
echo "Project root: ${ROOT}"
echo

# --- A) Inventory ---
echo "## A) Project Inventory"

echo
echo "### A.1) Vercel CLI Status"
if command -v vercel >/dev/null 2>&1; then
  echo "  CLI installed: $(vercel --version 2>/dev/null || echo 'version unknown')"
  vercel whoami 2>/dev/null || echo "  (Not authenticated)"
else
  echo "  Vercel CLI not installed"
fi

echo
echo "### A.2) Project Link"
if [[ -f "$ROOT/.vercel/project.json" ]]; then
  echo "  Linked project:"
  cat "$ROOT/.vercel/project.json" 2>/dev/null
else
  echo "  Not linked to Vercel project"
fi

echo
echo "### A.3) Framework Detection"
for CONFIG in "next.config.js" "next.config.mjs" "next.config.ts" "nuxt.config.ts" "vite.config.ts" "vite.config.js" "astro.config.mjs" "svelte.config.js" "remix.config.js" "gatsby-config.js"; do
  if [[ -f "$ROOT/$CONFIG" ]]; then
    echo "  Framework config found: $CONFIG"
  fi
done

if [[ -f "$ROOT/package.json" ]]; then
  echo
  echo "  Package.json scripts:"
  jq -r '.scripts // {} | to_entries[] | "    \(.key): \(.value)"' "$ROOT/package.json" 2>/dev/null | head -15
fi

# --- B) Security ---
echo
echo "## B) Security Configuration"

echo
echo "### B.1) vercel.json"
if [[ -f "$ROOT/vercel.json" ]]; then
  echo "  Found vercel.json:"
  cat "$ROOT/vercel.json" 2>/dev/null

  echo
  echo "  Checking for hardcoded secrets in vercel.json..."
  rg -n "(sk-|AKIA|ghp_|xox|password|secret|token|key)" "$ROOT/vercel.json" 2>/dev/null | head -10 || echo "  No obvious secret patterns found"
else
  echo "  No vercel.json found"
fi

echo
echo "### B.2) Security Headers"
echo "  Checking for header configuration..."
# Check vercel.json headers
if [[ -f "$ROOT/vercel.json" ]]; then
  jq -r '.headers // empty' "$ROOT/vercel.json" 2>/dev/null || true
fi

# Check next.config headers
for NEXT_CONFIG in "next.config.js" "next.config.mjs" "next.config.ts"; do
  if [[ -f "$ROOT/$NEXT_CONFIG" ]]; then
    rg -n "headers|Content-Security-Policy|Strict-Transport|X-Frame-Options|X-Content-Type" "$ROOT/$NEXT_CONFIG" 2>/dev/null | head -10 || true
  fi
done

# Check middleware for headers
if [[ -f "$ROOT/middleware.ts" || -f "$ROOT/middleware.js" || -f "$ROOT/src/middleware.ts" ]]; then
  echo "  Middleware file found (may contain header logic)"
fi

# --- C) Environment Variables ---
echo
echo "## C) Environment Variables"

echo
echo "### C.1) NEXT_PUBLIC_ exposure check"
rg -rn --hidden --glob '!**/node_modules/**' --glob '!**/.git/**' --glob '!**/.next/**' \
  "NEXT_PUBLIC_" "$ROOT" 2>/dev/null | head -20 || echo "  No NEXT_PUBLIC_ vars found"

echo
echo "### C.2) .env files"
for ENV_FILE in $(find "$ROOT" -maxdepth 2 -name ".env*" 2>/dev/null | sort); do
  BASENAME=$(basename "$ENV_FILE")
  case "$BASENAME" in
    .env.example|.env.sample|.env.template)
      echo "  Template: $ENV_FILE (OK)"
      ;;
    .env.local|.env.development.local|.env.production.local)
      echo "  Local file: $ENV_FILE (should be gitignored)"
      ;;
    *)
      echo "  WARNING: $ENV_FILE (check if gitignored)"
      ;;
  esac
done

echo
echo "### C.3) .gitignore env coverage"
if [[ -f "$ROOT/.gitignore" ]]; then
  for PATTERN in ".env" ".env.local" ".env*.local" ".vercel"; do
    if grep -q "$PATTERN" "$ROOT/.gitignore" 2>/dev/null; then
      echo "  Covered: $PATTERN"
    else
      echo "  MISSING: $PATTERN"
    fi
  done
else
  echo "  WARNING: No .gitignore file"
fi

echo
echo "### C.4) Vercel env vars (if CLI available and linked)"
if command -v vercel >/dev/null 2>&1 && [[ -f "$ROOT/.vercel/project.json" ]]; then
  vercel env ls 2>/dev/null || echo "  (Could not list env vars)"
else
  echo "  (Skipped - CLI not available or project not linked)"
fi

# --- D) Configuration ---
echo
echo "## D) Build Configuration"

echo
echo "### D.1) Routes & Rewrites"
if [[ -f "$ROOT/vercel.json" ]]; then
  jq -r '.routes // .rewrites // .redirects // empty' "$ROOT/vercel.json" 2>/dev/null || true
fi

echo
echo "### D.2) Functions Configuration"
if [[ -f "$ROOT/vercel.json" ]]; then
  jq -r '.functions // empty' "$ROOT/vercel.json" 2>/dev/null || echo "  No function config in vercel.json"
fi

echo
echo "### D.3) API Routes / Serverless Functions"
for API_DIR in "api" "pages/api" "app/api" "src/app/api" "src/pages/api"; do
  if [[ -d "$ROOT/$API_DIR" ]]; then
    echo "  Found: $API_DIR"
    find "$ROOT/$API_DIR" -type f \( -name "*.ts" -o -name "*.js" -o -name "*.py" \) 2>/dev/null | head -20
  fi
done

echo
echo "### D.4) Edge Functions / Middleware"
for EDGE_FILE in "middleware.ts" "middleware.js" "src/middleware.ts" "src/middleware.js"; do
  if [[ -f "$ROOT/$EDGE_FILE" ]]; then
    echo "  Found: $EDGE_FILE"
    head -30 "$ROOT/$EDGE_FILE" 2>/dev/null
  fi
done

# --- E) Observability ---
echo
echo "## E) Observability"
echo "  Checking for monitoring integrations..."

rg -rn --hidden --glob '!**/node_modules/**' --glob '!**/.git/**' \
  "@vercel/analytics|@vercel/speed-insights|@sentry/nextjs|sentry\.init|LogRocket|datadogRum|newrelic" \
  "$ROOT" 2>/dev/null | head -10 || echo "  No monitoring integrations found"

# --- F) Performance ---
echo
echo "## F) Performance Indicators"

echo
echo "### F.1) Image Optimization"
rg -rn --hidden --glob '!**/node_modules/**' --glob '!**/.git/**' \
  "next/image|Image.*src=|images.*domains|remotePatterns" \
  "$ROOT" 2>/dev/null | head -10 || echo "  No Next.js Image usage found"

echo
echo "### F.2) Bundle Analysis Tools"
rg -rn --hidden --glob '!**/node_modules/**' --glob '!**/.git/**' \
  "@next/bundle-analyzer|webpack-bundle-analyzer|source-map-explorer" \
  "$ROOT" 2>/dev/null | head -5 || echo "  No bundle analysis tools found"

echo
echo "== Evidence collection complete =="
echo "== Use /vercel-review in Claude Code for the full structured report =="
