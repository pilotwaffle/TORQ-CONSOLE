#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

echo "== Firebase Expert Review Evidence =="
echo "Repo: ${ROOT}"
echo

echo "## 1) Firebase project files"
echo "- Searching for firebase.json, .firebaserc, firestore.rules, storage.rules, functions/..."

for f in firebase.json .firebaserc firestore.rules firestore.indexes.json storage.rules remoteconfig.template.json; do
  FOUND=$(find "$ROOT" -maxdepth 3 -name "$f" 2>/dev/null | head -5)
  if [[ -n "$FOUND" ]]; then
    echo "  Found: $FOUND"
  fi
done

echo
echo "## 2) Firebase SDK / service usage patterns"
rg -n --hidden --glob '!**/node_modules/**' --glob '!**/.git/**' \
  "firebase|firestore|initializeApp|getAuth|getFirestore|getStorage|getFunctions|getMessaging|firebase-admin" \
  "$ROOT" 2>/dev/null | head -50 || echo "  No Firebase SDK patterns found."

echo
echo "## 3) Security rules files"
for RULES_FILE in $(find "$ROOT" -maxdepth 3 \( -name "firestore.rules" -o -name "storage.rules" \) 2>/dev/null); do
  echo "  --- $RULES_FILE ---"
  cat "$RULES_FILE" 2>/dev/null | head -100
  echo
done

echo
echo "## 4) Cloud Functions (if present)"
FUNCTIONS_DIR=$(find "$ROOT" -maxdepth 2 -type d -name "functions" 2>/dev/null | head -1)
if [[ -n "$FUNCTIONS_DIR" ]]; then
  echo "  Functions directory: $FUNCTIONS_DIR"
  ls -la "$FUNCTIONS_DIR" 2>/dev/null | head -20
  if [[ -f "$FUNCTIONS_DIR/package.json" ]]; then
    echo "  --- package.json ---"
    cat "$FUNCTIONS_DIR/package.json" 2>/dev/null | head -40
  fi
  if [[ -f "$FUNCTIONS_DIR/index.js" || -f "$FUNCTIONS_DIR/index.ts" || -f "$FUNCTIONS_DIR/src/index.ts" ]]; then
    echo "  --- Entry point ---"
    cat "$FUNCTIONS_DIR/index.js" "$FUNCTIONS_DIR/index.ts" "$FUNCTIONS_DIR/src/index.ts" 2>/dev/null | head -80
  fi
else
  echo "  No functions directory found."
fi

echo
echo "## 5) Dangerous patterns scan"
echo "  Checking for 'allow read, write: if true', exposed API keys, admin SDK misuse..."
rg -n --hidden --glob '!**/node_modules/**' --glob '!**/.git/**' \
  "allow read, write: if true|allow read: if true|allow write: if true|AIza[0-9A-Za-z_-]{35}|firebase-admin.*credential" \
  "$ROOT" 2>/dev/null | head -30 || echo "  No dangerous patterns found."

echo
echo "## 6) Environment files"
for ENV_FILE in $(find "$ROOT" -maxdepth 2 -name ".env*" -not -name ".env.example" 2>/dev/null); do
  echo "  WARNING: Found env file: $ENV_FILE (should not be committed)"
done

echo
echo "## 7) Firebase MCP check"
if command -v npx >/dev/null 2>&1; then
  echo "  npx available. Firebase MCP can be invoked with:"
  echo "  npx firebase-tools@latest mcp --generate-tool-list"
  echo "  npx firebase-tools@latest mcp --generate-prompt-list"
else
  echo "  npx not available. Install Node.js for Firebase MCP access."
fi

echo
echo "== Review evidence collection complete =="
echo "== Use /firebase-review in Claude Code for the full structured report =="
