# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- None yet

## [0.9.0-beta] - 2026-03-08

### Architecture Evolution

**New Positioning**: TORQ Console is now positioned as an **Adaptive Multi-Agent Reasoning Platform** with mission execution capabilities. This release represents a complete architectural evolution from the previous Marvin-based integration approach.

### Added

**Execution Fabric (Phase 5.1) — Hardened Runtime**
- `MissionNodeExecutor` — Idempotent node execution with duplicate prevention
  - Atomic state transitions via check-and-set database operations
  - Safe retry with no side effects
  - Terminal state detection (completed, failed, skipped)
- `MissionCompleter` — Idempotent mission completion
  - Single `mission.completed` event emission
  - Atomic transition to completed status
- `MissionNodeExecutor._emit_event_if_not_exists()` — Deduplicated event emission
- `MissionNodeExecutor._create_handoff_if_not_exists()` — Deduplicated handoff creation
- `MissionNodeExecutor._try_transition_to_running()` — Atomic transition guard
- `MissionNodeExecutor._try_transition_to_completed()` — Atomic completion guard

**Mission Graph Planning (Phase 5)**
- Dependency-aware mission execution with 5 node types:
  - `objective` — Top-level goals
  - `task` — Concrete work items
  - `decision` — Branch points with gate evaluation
  - `evidence` — Required data/artifacts
  - `deliverable` — Expected outputs
- Five edge types for graph composition:
  - `depends_on` — Dependency (blocking)
  - `informs` — Information flow (non-blocking)
  - `blocks` — Execution blocking
  - `branches_to` — Conditional branching
  - `produces` — Output artifact

**Strategic Memory (Phase 4H)**
- Long-term memory injection system
- Cross-session learning from mission outcomes
- Memory quality scoring (0.0–1.0)

**Adaptive Cognition Loop (Phase 4F)**
- Signal collection from mission evaluations
- Quality assessment engine
- Adaptation policy management
- A/B testing framework for execution strategies

**Documentation**
- `docs/ARCHITECTURE_INDEX.md` — Canonical architecture map
- `docs/PHASE_5_1_VALIDATION_REPORT.md` — Evidence-backed validation
- `docs/PHASE_5_MISSION_GRAPH_PLANNING.md` — Mission graph documentation
- `docs/PHASE_5_1_EXECUTION_FABRIC.md` — Execution fabric documentation
- `docs/PHASE_4H_STRATEGIC_MEMORY.md` — Strategic memory documentation

**Database Migrations**
- `migrations/018_mission_graphs.sql` — Mission graph schema
- `migrations/019_execution_fabric.sql` — Execution fabric schema
- `migrations/020_validation_telemetry.sql` — Validation telemetry
- `migrations/apply_phase_5_1_to_supabase.sql` — Combined Phase 5.1 schema

**Validation Scripts**
- `scripts/validate_hardened_scheduler_integration.py` — Scheduler integration tests
- `scripts/mission_3_hardened_scheduler_validation.py` — Mission 3 validation

### Changed

**Default Runtime Path — Now Uses Hardened Executor**
- `MissionGraphScheduler` now uses `MissionNodeExecutor` by default
- `MissionGraphScheduler` now uses `MissionCompleter` by default
- Old execution path deprecated (no longer used)
- All node execution goes through hardened path with idempotency guards

**Handoff Format Standardization**
- All handoffs now use canonical rich format (minimal format eliminated)
- Consistent structure: `handoff_summary`, `confidence`, `artifacts`, `risks`, `assumptions`
- 100% rich format adoption in hardened missions

**Event Emission**
- Duplicate event prevention via `_emit_event_if_not_exists()`
- Event count now predictable: (nodes × 3) + mission events
- No duplicate `node.started`, `node.completed`, or `mission.completed` events

**API Surface**
- `torq_console.mission_graph.__init__.py` now exports:
  - `MissionNodeExecutor`
  - `MissionCompleter`
  - `NodeExecutionError`
  - `IdempotencyViolationError`

**README.md**
- Complete rewrite with new positioning
- v0.9.0-beta badge
- Validation section with evidence table
- Component maturity table

### Fixed

**Context Bus Dataclass Field Ordering**
- Fixed `TypeError: non-default argument follows default argument`
- Moved required `mission_id` field before fields with default values in `MissionEvent` dataclass

**Scheduler Path Fragmentation**
- Unified execution paths — hardened executor is now default
- Eliminated dual execution paths that caused inconsistent behavior

### Validation Results

| Check | Mission 1 (Baseline) | Mission 2 (Hardened) | Mission 3 (Scheduler) |
|-------|---------------------|----------------------|------------------------|
| Duplicate Events | 33 | 0 | 0 |
| Rich Handoffs | 9/14 (64%) | 5/5 (100%) | 7/7 (100%) |
| Mission.completed Events | 2 | 1 | 1 |

**Improvement**: 33 duplicate events → 0 duplicate events
**Handoff Quality**: 64% rich → 100% rich

### Component Maturity

| Component | Status |
|-----------|--------|
| Mission Graph Planning | Validated Beta |
| Execution Fabric | Validated Beta |
| Hardened Scheduler | Validated Beta (default path) |
| Context Bus | Beta |
| Handoff Manager | Validated Beta |
| Workstream State Manager | Beta |
| Strategic Memory | Beta |
| Adaptive Cognition Loop | Beta |
| Replanning Engine | Experimental |
| Checkpoint Manager | Experimental |

### Migration Notes

**Upgrading from v0.8.x to v0.9.0-beta:**

1. **Database Migration Required**
   ```bash
   python -m torq_console.cli migrate
   ```

2. **API Changes — Breaking**
   - `MissionGraphScheduler` constructor signature changed
   - Hardened executor is now default (no longer opt-in)
   - Mission completion behavior is now idempotent

3. **Handoff Format**
   - Minimal `{"done": "..."}` format no longer supported
   - All handoffs must use rich format

4. **Event Behavior**
   - Duplicate events automatically prevented
   - No code changes required — automatic via hardened executor

### Known Limitations

- Replanning engine is experimental (framework exists, needs implementation)
- Checkpoint manager is experimental (rollback capability planned)
- Operator control surface needs refinement
- Additional mission type validation needed

---

## [0.8.0] - 2025-11-XX

### Added
- Comprehensive improvement recommendations document (IMPROVEMENT_RECOMMENDATIONS.md)
- LICENSE file (MIT License)
- CONTRIBUTING.md with detailed contribution guidelines
- CHANGELOG.md to track version history

### Changed
- None

### Fixed
- None

### Security
- Identified security issues to be addressed in upcoming releases:
  - MD5 hash usage (6 instances) - will add usedforsecurity=False flag
  - SQL injection risks in template generation
  - Server binding to all interfaces by default
  - Unsafe pickle deserialization

---

## Version History Summary

| Version | Date | Key Features |
|---------|------|--------------|
| 0.9.0-beta | 2026-03 | Mission Graph Planning, Hardened Execution Fabric, Strategic Memory |
| 0.8.0 | 2025-11 | Marvin 3.2.3, Enhanced Prince Flowers, Spec-Kit |
| 0.7.0 | 2025-XX | 4-phase integration, Windows features, GPU acceleration |
| 0.6.0 | 2025-XX | MCP integration, Web GUI, Interactive shell |
| 0.5.0 | 2025-XX | Initial release, Basic CLI |

---

## Migration Guides

### Upgrading to 0.9.0-beta

1. **Database Migration**
   ```bash
   python -m torq_console.cli migrate
   ```

2. **API Changes**
   - `MissionGraphScheduler` now uses hardened executor by default
   - Old execution path deprecated
   - Handoff format now rich-only

3. **New Features to Explore**
   ```python
   from torq_console.mission_graph import (
       MissionGraphScheduler,
       MissionNodeExecutor,
       MissionCompleter
   )

   # Scheduler now uses hardened executor by default
   scheduler = MissionGraphScheduler(supabase_client)

   # Or use hardened components directly
   executor = MissionNodeExecutor(supabase_client)
   completer = MissionCompleter(supabase_client)
   ```

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Support

- **Issues:** https://github.com/pilotwaffle/TORQ-CONSOLE/issues
- **Discussions:** https://github.com/pilotwaffle/TORQ-CONSOLE/discussions
- **Documentation:** https://github.com/pilotwaffle/TORQ-CONSOLE/wiki

---

*For detailed changes in each release, see the commit history on GitHub.*
