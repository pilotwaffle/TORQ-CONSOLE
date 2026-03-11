# GitHub Sync Audit - v0.9.0-beta Release

**Date**: March 8, 2026
**Purpose**: Clean repository sync for validated architecture release

---

## Part 1: Files to INCLUDE

### Core Documentation ✅

| File | Purpose |
|------|---------|
| `README.md` | Main product page (v0.9.0-beta) |
| `docs/ARCHITECTURE_INDEX.md` | Canonical architecture map |
| `docs/PHASE_5_1_VALIDATION_REPORT.md` | Evidence-backed validation |
| `docs/PHASE_5_MISSION_GRAPH_PLANNING.md` | Mission graph docs |
| `docs/PHASE_5_1_EXECUTION_FABRIC.md` | Execution fabric docs |
| `docs/PHASE_4H_STRATEGIC_MEMORY.md` | Strategic memory docs |

### Core Code ✅

| Directory/File | Purpose |
|---------------|---------|
| `torq_console/mission_graph/` | Hardened scheduler (validated) |
| `torq_console/strategic_memory/` | Memory system |
| `torq_console/adaptive_cognition/` | Learning loop |
| `torq_console/synthesis/` | Multi-output synthesis |
| `torq_console/evaluation/` | Quality assessment |

### Migrations ✅

| File | Purpose |
|------|---------|
| `migrations/018_mission_graphs.sql` | Mission graph schema |
| `migrations/019_execution_fabric.sql` | Execution fabric schema |
| `migrations/020_validation_telemetry.sql` | Validation telemetry |
| `migrations/apply_phase_5_1_to_supabase.sql` | Combined 5.1 schema |

### Validation Scripts ✅

| File | Purpose |
|------|---------|
| `scripts/validate_hardened_scheduler_integration.py` | Scheduler validation |
| `scripts/mission_3_hardened_scheduler_validation.py` | Mission 3 validation |

---

## Part 2: Files to EXCLUDE

### Local Artifacts ❌

| Pattern | Reason |
|--------|--------|
| `logs/validation_snapshots/` | Local testing artifacts |
| `*_snapshot.json` | Local mission snapshots |
| `*_report.json` (root level) | Local validation reports |
| `*_VALIDATION_*.md` (root) | Duplicates of docs/ |
| `GITHUB_SYNC_*.md` | Sync planning docs |

### Environment/Config ❌

| Pattern | Reason |
|--------|--------|
| `.env.validation` | Local environment |
| `.env.local` | Local environment |
| `.env.backup` | Backup files |
| `.env.production` | Production config |
| `.env.vercel` | Vercel config |
| `.env.n8n-mcp` | MCP config |

### Database Files ❌

| Pattern | Reason |
|--------|--------|
| `*.db` | Local databases |
| `*.sqlite` | Local databases |
| `*.sqlite-shm` | SQLite shared memory |
| `*.sqlite-wal` | SQLite write-ahead log |
| `telemetry*.db` | Telemetry databases |
| `*_database.sqlite` | Runtime databases |

### Runtime State ❌

| Pattern | Reason |
|--------|--------|
| `.torq/` | Local TORQ state |
| `.torq_console/` | Local console state |
| `workspace/` | Local workspace state |

### Temporary Files ❌

| Pattern | Reason |
|--------|--------|
| `*.bak` | Backup files |
| `*.backup` | Backup files |
| `*_OLD.*` | Archived files |
| `*_ARCHIVE.*` | Archived files |
| `nul` | Windows null device artifact |

---

## Part 3: Modified Files to Review

### High Priority (v0.9.0-beta Core Changes)

1. **README.md** — Complete rewrite
   - New positioning: "Adaptive Multi-Agent Reasoning Platform"
   - v0.9.0-beta badge
   - Validation section with evidence table

2. **torq_console/mission_graph/scheduler.py**
   - Integrated hardened executor
   - Uses MissionNodeExecutor by default
   - Uses MissionCompleter for completion

3. **torq_console/mission_graph/executor.py**
   - NEW: Hardened executor with idempotency
   - MissionNodeExecutor class
   - MissionCompleter class

4. **torq_console/mission_graph/context_bus.py**
   - Fixed dataclass field ordering

5. **torq_console/mission_graph/__init__.py**
   - Export hardened executor classes

6. **torq_console/mission_graph/models.py**
   - Fixed depends_on field alias

7. **.gitignore**
   - Added exclusions for validation artifacts
   - Added exclusions for local state

---

## Part 4: Recommended Git Add Commands

### For Documentation-First Release (Recommended)

```bash
# Core documentation
git add README.md
git add docs/ARCHITECTURE_INDEX.md
git add docs/PHASE_5_1_VALIDATION_REPORT.md
git add docs/PHASE_5_MISSION_GRAPH_PLANNING.md
git add docs/PHASE_5_1_EXECUTION_FABRIC.md
git add docs/PHASE_4H_STRATEGIC_MEMORY.md

# Core code
git add torq_console/mission_graph/
git add torq_console/mission_graph/__init__.py

# Migrations
git add migrations/018_mission_graphs.sql
git add migrations/019_execution_fabric.sql
git add migrations/020_validation_telemetry.sql
git add migrations/apply_phase_5_1_to_supabase.sql

# Validation scripts
git add scripts/validate_hardened_scheduler_integration.py
git add scripts/mission_3_hardened_scheduler_validation.py

# Git hygiene
git add .gitignore
```

### Full Release (If Including All Changes)

Add the above plus:
- All other `torq_console/` subsystems
- All migrations 004-020
- Frontend changes
- Other modified files

---

## Part 5: Pre-Commit Checklist

### File Content Review ✅

- [x] No secrets in modified files
- [x] No hardcoded API keys in code
- [x] README.md has honest v0.9.0-beta positioning
- [x] ARCHITECTURE_INDEX.md is accurate
- [x] Validation report has evidence-backed claims
- [x] .gitignore excludes local artifacts

### Validation Evidence ✅

- [x] Mission 1 completed (baseline)
- [x] Mission 2 completed (hardened executor)
- [x] Mission 3 completed (hardened scheduler)
- [x] 0 duplicate events in hardened missions
- [x] 100% rich handoff format in hardened missions
- [x] Single mission.completed event in hardened missions

### Component Maturity Labels ✅

- [x] Mission Graph Planning: Validated Beta
- [x] Execution Fabric: Validated Beta
- [x] Context Bus: Beta
- [x] Handoff Manager: Validated Beta
- [x] Workstream State: Beta
- [x] Strategic Memory: Beta
- [x] Adaptive Cognition: Beta
- [x] Replanning Engine: Experimental
- [x] Checkpoint Manager: Experimental

---

## Part 6: Current Git Status Summary

### Modified Files (Core)
- README.md
- .gitignore
- torq_console/mission_graph/scheduler.py
- torq_console/mission_graph/executor.py
- torq_console/mission_graph/context_bus.py
- torq_console/mission_graph/__init__.py

### New Files (Documentation)
- docs/ARCHITECTURE_INDEX.md
- docs/PHASE_5_1_VALIDATION_REPORT.md

### Untracked Files (Excluded from sync)
- logs/ (validation artifacts)
- workspace/ (local state)
- *_snapshot.json (local artifacts)
- *_report.json (local artifacts, except docs/)
- .env.* (environment files)
- *.db, *.sqlite (databases)

---

## Part 7: CHANGELOG.md (To be created)

See next section for CHANGELOG.md draft.
