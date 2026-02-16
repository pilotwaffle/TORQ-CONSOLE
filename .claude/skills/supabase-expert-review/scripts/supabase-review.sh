#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

echo "== Supabase Expert Review Evidence =="
echo "Repo: ${ROOT}"
echo

echo "## 1) Repo inventory"
echo "- Searching for Supabase client init, migrations, policies, storage rules, edge functions..."

rg -n --hidden --glob '!**/node_modules/**' --glob '!**/.git/**' \
  "createClient\(|supabase\.co|SUPABASE_URL|SUPABASE_ANON_KEY|service_role|\.rls\(|row.level.security|auth\.uid\(\)|security definer|supabase/supabase-js" \
  "$ROOT" 2>/dev/null | head -80 || echo "  No Supabase patterns found."

echo
echo "## 2) Supabase project structure"
for DIR_NAME in supabase migrations sql db; do
  FOUND=$(find "$ROOT" -maxdepth 4 -type d -name "$DIR_NAME" 2>/dev/null | head -5)
  if [[ -n "$FOUND" ]]; then
    echo "  Found directory: $FOUND"
  fi
done

# Check for supabase config
for f in supabase/config.toml supabase/.env supabase/seed.sql; do
  if [[ -f "$ROOT/$f" ]]; then
    echo "  Found config: $ROOT/$f"
  fi
done

echo
echo "## 3) Migration files"
MIGRATIONS_DIR=$(find "$ROOT" -maxdepth 4 -type d -name "migrations" 2>/dev/null | head -1)
if [[ -n "$MIGRATIONS_DIR" ]]; then
  echo "  Migrations directory: $MIGRATIONS_DIR"
  ls -la "$MIGRATIONS_DIR" 2>/dev/null | head -30

  echo
  echo "  RLS patterns in migrations:"
  rg -n "enable row level security|create policy|alter table.*enable rls|force row level security|security definer" \
    "$MIGRATIONS_DIR" 2>/dev/null | head -40 || echo "  No RLS patterns in migrations."

  echo
  echo "  Dangerous patterns in migrations:"
  rg -n "security definer|grant.*all|public\.\*|anon.*select|anon.*insert|anon.*update|anon.*delete" \
    "$MIGRATIONS_DIR" 2>/dev/null | head -20 || echo "  No dangerous patterns found."
else
  echo "  No migrations directory found."
fi

echo
echo "## 4) Edge Functions (if present)"
EDGE_DIR=$(find "$ROOT" -maxdepth 3 -type d -name "functions" -path "*/supabase/*" 2>/dev/null | head -1)
if [[ -n "$EDGE_DIR" ]]; then
  echo "  Edge Functions directory: $EDGE_DIR"
  ls -la "$EDGE_DIR" 2>/dev/null | head -20

  echo
  echo "  Secret/env patterns in edge functions:"
  rg -n "Deno\.env|SUPABASE_SERVICE_ROLE|service_role|SUPABASE_DB_URL" \
    "$EDGE_DIR" 2>/dev/null | head -20 || echo "  No secret patterns found."
else
  echo "  No edge functions directory found."
fi

echo
echo "## 5) Client-side key exposure check"
echo "  Checking if service_role key is exposed in client code..."
rg -n --hidden --glob '!**/node_modules/**' --glob '!**/.git/**' --glob '!**/*.sh' \
  "service.role|SUPABASE_SERVICE_ROLE" \
  "$ROOT" 2>/dev/null | grep -v "\.env\|\.example\|test\|spec\|mock" | head -10 || echo "  No client-side service_role exposure found."

echo
echo "## 6) Environment files"
for ENV_FILE in $(find "$ROOT" -maxdepth 3 -name ".env*" -not -name ".env.example" -not -name ".env.sample" 2>/dev/null); do
  echo "  WARNING: Found env file: $ENV_FILE (should not be committed)"
done

echo
echo "## 7) Supabase CLI check"
if command -v supabase >/dev/null 2>&1; then
  echo "  Supabase CLI available: $(supabase --version 2>/dev/null || echo 'version unknown')"
  echo "  Linked project status:"
  supabase status 2>/dev/null || echo "  (not linked to a project)"
else
  echo "  Supabase CLI not installed. Install with: npm i -g supabase"
fi

echo
echo "## 8) Optional live checks (requires env vars)"
if [[ -n "${SUPABASE_URL:-}" && -n "${SUPABASE_ANON_KEY:-}" ]]; then
  echo "  Live checks enabled (anon context)."
  echo "  NOTE: Only minimal safe GETs will be performed."
else
  echo "  Live checks skipped (SUPABASE_URL / SUPABASE_ANON_KEY not set)."
fi

echo
echo "== Review evidence collection complete =="
echo "== Use /supabase-review in Claude Code for the full structured report =="
