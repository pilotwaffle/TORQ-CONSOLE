#!/usr/bin/env bash
# verify_deploy_contract.sh
# Usage: ./scripts/verify_deploy_contract.sh <base_url>
# Validates /api/debug/deploy conforms to torq-deploy-v1 contract.
# See docs/ops/deploy-identity.md for the full spec.

set -euo pipefail
BASE_URL="${1:?Usage: $0 <base_url>}"
ENDPOINT="$BASE_URL/api/debug/deploy"

echo "Checking: $ENDPOINT"
RESP1=$(curl -sf "$ENDPOINT")
RESP2=$(curl -sf "$ENDPOINT")

pykey() {
  python3 - "$1" <<'PY'
  import sys, json
  key = sys.argv[1]
  d = json.load(sys.stdin)
  print(d.get(key, ""))
  PY
  }

  r1key() { pykey "$1" <<< "$RESP1"; }
  r2key() { pykey "$1" <<< "$RESP2"; }

  check() {
    local label="$1" value="$2" expected="$3"
      if [ "$value" != "$expected" ]; then
          echo "FAIL [$label]: expected '$expected', got '$value'" && exit 1
            fi
              echo "OK   [$label]: $value"
              }

              nonempty() {
                local label="$1" value="$2"
                  if [ -z "$value" ] || [ "$value" = "null" ]; then
                      echo "FAIL [$label]: empty or null" && exit 1
                        fi
                          echo "OK   [$label]: $value"
                          }

                          echo ""
                          echo "=== Contract Validation: torq-deploy-v1 ==="

                          check    "schema"               "$(r1key _schema)"               "torq-deploy-v1"
                          check    "schema_version"       "$(r1key _schema_version)"       "1"
                          nonempty "schema_updated"       "$(r1key _schema_updated)"
                          nonempty "platform"             "$(r1key platform)"
                          nonempty "service"              "$(r1key service)"
                          nonempty "app_version"          "$(r1key app_version)"
                          nonempty "version"              "$(r1key version)"
                          nonempty "version_source"       "$(r1key version_source)"
                          nonempty "git_sha"              "$(r1key git_sha)"
                          nonempty "container_start_time" "$(r1key container_start_time)"
                          nonempty "timestamp"            "$(r1key timestamp)"
                          nonempty "request_id"           "$(r1key request_id)"

                          APP_V="$(r1key app_version)"
                          VER="$(r1key version)"
                          if [ "$APP_V" != "$VER" ]; then
                            echo "FAIL [version==app_version]: '$VER' != '$APP_V'" && exit 1
                            fi
                            echo "OK   [version==app_version]: $VER"

                            RID1=$(r1key request_id)
                            RID2=$(r2key request_id)
                            if [ "$RID1" = "$RID2" ]; then
                              echo "FAIL [request_id uniqueness]: same ID on two calls - cached: $RID1" && exit 1
                              fi
                              echo "OK   [request_id uniqueness]: unique"

                              PLATFORM="$(r1key platform)"
                              GIT_SHA="$(r1key git_sha)"
                              APP_VERSION="$(r1key app_version)"
                              VERSION_SOURCE="$(r1key version_source)"

                              echo ""
                              echo "=== Result ==="
                              echo "Contract VALID: torq-deploy-v1"
                              echo "  platform:     $PLATFORM"
                              echo "  git_sha:      $GIT_SHA"
                              echo "  app_version:  $APP_VERSION ($VERSION_SOURCE)"
                              echo ""
