# TORQ Console

**Adaptive Multi-Agent Reasoning Platform with Mission Execution**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/Version-v0.9.0--beta-orange.svg)](https://github.com/pilotwaffle/TORQ-CONSOLE)
[![Status](https://img.shields.io/badge/Status-Validated%20Beta-green.svg)](https://github.com/pilotwaffle/TORQ-CONSOLE)

---

## Overview

TORQ Console v0.9.0-beta provides a **validated beta architecture** for mission-structured multi-agent reasoning, featuring Mission Graph Planning and a hardened Execution Fabric with idempotent coordination.

> **Honest Positioning**: TORQ v0.9.0-beta ships with validated Mission Graph Planning and Hardened Execution Fabric. It also includes implemented strategic memory and synthesis layers. Additional capabilities such as Agent Teams, Organizational Learning, and Firm-Scale Operations are defined in the [roadmap](docs/architecture/ARCHITECTURE_ROADMAP.md) and [PRDs](docs/prd/) but are **not yet implemented**.

### What TORQ Provides

| Capability | Description |
|------------|-------------|
| **Mission Graph Planning** | Dependency-aware execution with 5 node types and decision gates |
| **Execution Fabric** | Idempotent coordination with event bus and structured handoffs |
| **Institutional Memory** | Strategic memory that shapes reasoning across sessions |
| **Adaptive Cognition** | Learning loop that improves from outcomes |
| **Observability** | Full execution trace with rollback capability |

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/pilotwaffle/TORQ-CONSOLE.git
cd TORQ-CONSOLE

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys (Claude, Supabase)

# Initialize database
python -m torq_console.cli migrate

# Start the server
python -m torq_console.cli start
```

### Basic Usage

```python
from torq_console.mission_graph import MissionGraphScheduler
from torq_console.dependencies import get_supabase_client

# Initialize
supabase = get_supabase_client()
scheduler = MissionGraphScheduler(supabase)

# Create and execute a mission
mission = await create_mission(
    objective="Assess market opportunity for Product X",
    context={"market": "Europe", "product": "Product X"}
)

result = await scheduler.execute_graph(mission, mission.graph)
```

---

## Architecture

TORQ is organized into four layers with seven major phases:

### Execution Layer (Phase 5, 5.1) — **Validated Beta**

**Mission Graph Planning**
- Dependency graphs with 5 node types (objective, task, decision, evidence, deliverable)
- Decision gates with conditional branching
- Template missions for common patterns

**Execution Fabric** (v0.9.0 — Hardened)
- **Context Bus** — Event-driven coordination (20+ event types)
- **Handoff Manager** — Structured collaboration packets
- **Workstream State Manager** — Health tracking across parallel work
- **Hardened Scheduler** — Idempotent execution with duplicate prevention

### Intelligence Layer (Phase 4F, 4G, 4H) — **Beta**

**Adaptive Cognition Loop**
- Signal collection from evaluations
- A/B testing framework
- Readiness checker for safe auto-promotion

**Strategic Memory**
- Long-term memory injection
- Cross-session learning
- Memory quality scoring

### Reasoning Layer (Phase 3) — **Production**

**Multi-Agent Orchestration**
- Agent selection and routing
- Specialized agents (analysis, research, synthesis)
- Collaboration protocols

### Foundation (Phase 1-2) — **Production**

**Core Infrastructure**
- Supabase-backed persistence
- Claude API integration
- Configuration management

---

## Validation Status

**v0.9.0-beta** — March 8, 2026

The hardened execution path is validated across multiple mission shapes:

| Check | Status | Evidence |
|-------|--------|----------|
| Duplicate event prevention | ✅ Pass | 0 duplicates across 3 missions |
| Idempotent node execution | ✅ Pass | Safe retry, no side effects |
| Idempotent mission completion | ✅ Pass | Single completion event |
| Rich handoff standardization | ✅ Pass | 100% rich format, no minimal |
| Cross-mission generalization | ✅ Pass | Linear, decision-gate, risk-first missions |

**Validation Report**: See [docs/current/PHASE_5_1_VALIDATION_REPORT.md](docs/current/PHASE_5_1_VALIDATION_REPORT.md)

---

## Component Maturity

| Component | Maturity | Notes |
|-----------|----------|-------|
| Mission Graph Planning | **Validated Beta** | Hardened scheduler integrated |
| Execution Fabric | **Validated Beta** | Idempotent coordination proven |
| Context Bus | **Beta** | Event-driven coordination working |
| Handoff Manager | **Validated Beta** | Rich format standardized |
| Workstream State Manager | **Beta** | Health tracking functional |
| Strategic Memory | **Beta** | Memory injection working |
| Adaptive Cognition Loop | **Beta** | Learning loop operational |
| Replanning Engine | **Experimental** | Framework in place |
| Checkpoint Manager | **Experimental** | Rollback capability planned |

---

## Documentation

- [Documentation Index](docs/index.md) — Complete documentation hub
- [Architecture Index](docs/architecture/ARCHITECTURE_INDEX.md) — Complete system overview
- [Phase 5.1 Validation Report](docs/current/PHASE_5_1_VALIDATION_REPORT.md) — Hardened execution validation
- [Strategic Memory](docs/architecture/PHASE_4H_STRATEGIC_MEMORY.md) — Memory architecture
- [Mission Graph Planning](docs/architecture/PHASE_5_MISSION_GRAPH_PLANNING.md) — Dependency execution

---

## Development

### Project Structure

```
torq_console/
├── mission_graph/          # Mission planning and execution
│   ├── models.py           # Graph and node definitions
│   ├── scheduler.py        # Hardened execution scheduler
│   ├── executor.py         # Idempotent node executor
│   ├── context_bus.py      # Event coordination
│   ├── handoffs.py         # Collaboration packets
│   └── workstream_state.py # Parallel work tracking
├── adaptive_cognition/     # Learning and improvement
│   ├── signal_engine.py    # Outcome collection
│   ├── evaluation_engine.py# Quality assessment
│   └── adaptation_policy.py# Policy management
├── strategic_memory/       # Long-term memory
│   ├── memory_store.py     # Memory persistence
│   └── memory_router.py    # Memory retrieval
└── agents/                 # Multi-agent orchestration
    ├── router.py           # Agent selection
    └── specialists/        # Domain experts
```

### Running Tests

```bash
# Run all tests
pytest

# Run validation suite
python scripts/validate_hardened_scheduler_integration.py

# Run mission validation
python scripts/mission_3_hardened_scheduler_validation.py
```

---

## Configuration

Required environment variables:

```bash
# Claude API
ANTHROPIC_API_KEY=your_key_here

# Supabase (PostgreSQL database)
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_key

# Optional
OLLAMA_BASE_URL=http://localhost:11434  # For local models
```

---

## Contributing

Contributions welcome! Please see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

TORQ Console builds on excellent work by:
- Anthropic (Claude API)
- Supabase (PostgreSQL + real-time)
- Ollama (Local model inference)
- The open-source AI community
