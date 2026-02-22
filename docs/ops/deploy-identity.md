# TORQ Console - Deploy Identity Contract
# Schema: torq-deploy-v1  |  Schema Version: 1  |  Updated: 2026-02-22

## Purpose

Every running instance of TORQ Console must answer:
- What code am I running? (git_sha, app_version)
- - How was I deployed? (platform, version_source)
  - - When was I built and when did I start? (build_time, container_start_time)
    - - What external services am I configured to use?
     
      - `/api/debug/deploy` is the canonical source of truth for all of these.
     
      - ## Invariants
     
      - - All fields always present. No field is ever null or absent.
        - - "unknown" and "serverless" are valid explicit values, not error states.
          - - `request_id` is unique per call and never cached.
            - - `version` is an alias for `app_version` and must always equal it until _schema_version is bumped.
              - - All timestamps are timezone-aware ISO 8601 with Z suffix.
                - - `_schema_version` must increment on any breaking change.
                 
                  - ## Field Specification
                 
                  - | Field | Type | Allowed Values | Notes |
                  - |---|---|---|---|
                  - | `_schema` | string | `"torq-deploy-v1"` | Fixed. Confirms contract. |
                  - | `_schema_version` | int | integer >= 1 | Increment on breaking changes only. |
                  - | `_schema_updated` | string | ISO 8601 date | Date schema version was published. |
                  - | `request_id` | string | UUID v4 | Per-request. Must differ across calls. |
                  - | `platform` | string | `"railway"`, `"vercel"`, `"docker"`, `"unknown"` | Detected from env. |
                  - | `service` | string | `"railway-backend"`, `"vercel-api"`, `"docker-local"`, `"unknown"` | Derived from platform. |
                  - | `env` | string | `"production"`, `"staging"`, `"dev"` | From TORQ_ENV. Default: production. |
                  - | `app_version` | string | semver or `"dev"` | Canonical version. Never null. |
                  - | `version` | string | same as app_version | Backward compat alias. |
                  - | `version_source` | string | `"package"`, `"env"`, `"default"` | How version was resolved. |
                  - | `package_installed` | bool | true/false | true iff version_source == "package". |
                  - | `git_sha` | string | `[0-9a-f]{7,40}` or `"unknown"` | Short SHA (12 chars by convention). |
                  - | `build_branch` | string | branch name or `"unknown"` | Branch at build time. |
                  - | `build_time` | string | ISO 8601Z or `"unknown"` | Written by Dockerfile. |
                  - | `container_start_time` | string | ISO 8601Z or `"serverless"` | Vercel: "serverless". Others: real start. |
                  - | `timestamp` | string | ISO 8601Z | Time this response was generated. |
                  - | `anthropic_model` | string | model identifier | From ANTHROPIC_MODEL env var. |
                  - | `anthropic_configured` | bool | true/false | true iff ANTHROPIC_API_KEY is set. |
                  - | `supabase_configured` | bool | true/false | true iff URL + at least one key set. |
                  - | `proxy_secret_configured` | bool | true/false | true iff TORQ_PROXY_SECRET is set. |
                  - | `proxy_secret_required` | bool | true/false | From TORQ_PROXY_SECRET_REQUIRED. Default: true. |
                 
                  - ## Platform Detection Rules
                 
                  - Evaluated in order (never hardcode platform):
                 
                  - 1. `RAILWAY_ENVIRONMENT` or `RAILWAY_PROJECT_ID` present -> `"railway"`
                    2. 2. `VERCEL` or `VERCEL_ENV` present -> `"vercel"`
                       3. 3. `DOCKER_CONTAINER` set or `/.dockerenv` exists -> `"docker"`
                          4. 4. None of the above -> `"unknown"`
                            
                             5. ## Version Resolution
                            
                             6. | Source | Meaning |
                             7. |---|---|
                             8. | `"package"` | importlib.metadata.version("torq-console") succeeded |
                             9. | `"env"` | APP_VERSION env var set; importlib raised PackageNotFoundError |
                             10. | `"default"` | Neither; returns "dev". Indicates misconfigured environment. |
                            
                             11. Railway and Docker: expect `"package"`. Vercel: expect `"env"` (set APP_VERSION in dashboard).
                            
                             12. ## Expected Values by Platform
                            
                             13. | Field | Railway | Vercel | Docker |
                             14. |---|---|---|---|
                             15. | platform | "railway" | "vercel" | "docker" |
                             16. | version_source | "package" | "env" | "package" |
                             17. | package_installed | true | false | true |
                             18. | git_sha | RAILWAY_GIT_COMMIT_SHA or build_meta.json | GIT_SHA env var | ARG GIT_SHA or build_meta.json |
                             19. | build_time | from build_meta.json | "unknown" | from build_meta.json |
                             20. | container_start_time | real process start | "serverless" | real process start |
                            
                             21. ## Example Response (Railway)
                            
                             22. ```json
                                 {
                                   "_schema": "torq-deploy-v1",
                                   "_schema_version": 1,
                                   "_schema_updated": "2026-02-22",
                                   "request_id": "a3f8c2d1-7b4e-4a1f-9e2c-0d5f6b8a3c1e",
                                   "platform": "railway",
                                   "service": "railway-backend",
                                   "env": "production",
                                   "app_version": "0.80.0",
                                   "version": "0.80.0",
                                   "version_source": "package",
                                   "package_installed": true,
                                   "git_sha": "614b786b4d2a",
                                   "build_branch": "api-railway-proxy",
                                   "build_time": "2026-02-22T01:57:33Z",
                                   "container_start_time": "2026-02-22T02:00:11Z",
                                   "timestamp": "2026-02-22T02:05:44Z",
                                   "anthropic_model": "claude-sonnet-4-6",
                                   "anthropic_configured": true,
                                   "supabase_configured": true,
                                   "proxy_secret_configured": true,
                                   "proxy_secret_required": true
                                 }
                                 ```

                                 ## Contract Change Policy

                                 - **Non-breaking** (no version bump): adding new fields, changing _schema_updated.
                                 - - **Breaking** (must bump _schema_version): renaming, removing, or changing semantics of existing fields.
                                  
                                   - ## Implementation Files
                                  
                                   - - `torq_console/build_info.py` - all helper functions
                                     - - `torq_console/ui/railway_app.py` - /api/debug/deploy handler
                                       - - `scripts/verify_deploy_contract.sh` - CI validation script
