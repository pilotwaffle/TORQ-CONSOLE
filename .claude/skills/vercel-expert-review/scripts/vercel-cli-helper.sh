#!/usr/bin/env bash
set -euo pipefail

# Vercel CLI Helper - Safe wrapper for Vercel CLI operations
# Used by the Vercel Expert Review skill for evidence gathering.
#
# Usage:
#   ./scripts/vercel-cli-helper.sh whoami
#   ./scripts/vercel-cli-helper.sh projects
#   ./scripts/vercel-cli-helper.sh inspect <deployment-url>
#   ./scripts/vercel-cli-helper.sh env [project-name]
#   ./scripts/vercel-cli-helper.sh domains [project-name]

COMMAND="${1:-}"
shift || true

if ! command -v vercel >/dev/null 2>&1; then
  echo "Vercel CLI not installed. Install with: npm i -g vercel" >&2
  echo "Then authenticate with: vercel login" >&2
  exit 1
fi

case "$COMMAND" in
  whoami)
    echo "## Vercel Account"
    vercel whoami "$@" 2>/dev/null || echo "(Not authenticated. Run: vercel login)"
    ;;
  projects)
    echo "## Vercel Projects"
    vercel projects ls "$@" 2>/dev/null || echo "(Could not list projects)"
    ;;
  inspect)
    DEPLOYMENT="${1:-}"
    if [[ -z "$DEPLOYMENT" ]]; then
      echo "Usage: $0 inspect <deployment-url>" >&2
      exit 1
    fi
    echo "## Deployment Inspection: $DEPLOYMENT"
    vercel inspect "$DEPLOYMENT" 2>/dev/null || echo "(Could not inspect deployment)"
    ;;
  env)
    echo "## Environment Variables"
    vercel env ls "$@" 2>/dev/null || echo "(Could not list env vars. Are you in a linked project?)"
    ;;
  domains)
    echo "## Domains"
    vercel domains ls "$@" 2>/dev/null || echo "(Could not list domains)"
    ;;
  link-status)
    echo "## Project Link Status"
    if [[ -f ".vercel/project.json" ]]; then
      echo "  Project is linked:"
      cat .vercel/project.json 2>/dev/null
    else
      echo "  Not linked. Run: vercel link"
    fi
    ;;
  *)
    echo "Unknown command: $COMMAND" >&2
    echo "Valid commands: whoami | projects | inspect | env | domains | link-status" >&2
    exit 1
    ;;
esac
