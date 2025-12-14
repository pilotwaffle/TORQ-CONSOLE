# TORQ Console

[![GitHub stars](https://img.shields.io/github/stars/pilotwaffle/TORQ-CONSOLE?style=social)](https://github.com/pilotwaffle/TORQ-CONSOLE/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Last Commit](https://img.shields.io/github/last-commit/pilotwaffle/TORQ-CONSOLE)](https://github.com/pilotwaffle/TORQ-CONSOLE/commits/main)
[![Issues](https://img.shields.io/github/issues/pilotwaffle/TORQ-CONSOLE)](https://github.com/pilotwaffle/TORQ-CONSOLE/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/pilotwaffle/TORQ-CONSOLE)](https://github.com/pilotwaffle/TORQ-CONSOLE/pulls)
[![Tests](https://img.shields.io/github/actions/workflow/status/pilotwaffle/TORQ-CONSOLE/evaluation.yml)](https://github.com/pilotwaffle/TORQ-CONSOLE/actions)

> **Version:** 1.0.0+ (ML Systems Hardening Complete)
> **Author:** B Flowers
> **Status:** **Production Ready** – AI Platform with ML Observability
> **License:** MIT

TORQ Console is an AI development platform that transforms agent systems into measurable, reproducible ML systems with comprehensive observability, policy-driven routing, and deterministic evaluation.

## 🎉 **ML Systems Hardening - Complete**

**December 2025:** Successfully implemented comprehensive ML Systems Hardening with 5 milestones:

### ✅ **Implemented Features**

**Milestone 1: Telemetry + Trace**
- Structured event tracking with canonical schema
- Distributed tracing for request flows
- CLI commands: `torq telemetry`, `torq trace <run_id>`

**Milestone 2: Eval Sets + Gate**
- v1.0 evaluation set with 10 comprehensive tasks
- Deterministic scoring with regression detection
- CLI command: `torq eval run --set v1.0 --seed 42`

**Milestone 3: Policy-Driven Routing**
- YAML-based routing policies
- Intent-based agent selection
- Zero-code policy updates

**Milestone 4: Benchmarks + SLOs**
- Performance monitoring with percentiles
- Service Level Objectives definition
- SLO enforcement system

**Milestone 5: Tool Sandbox + Confirmations**
- Security policies with deny-by-default
- Path validation for file operations
- Prompt injection protection

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/pilotwaffle/TORQ-CONSOLE.git
cd TORQ-CONSOLE

# Install dependencies
pip install -e .

# Start with web interface
torq-console --web
```

### Verify Installation

```bash
# Run evaluation set
torq eval run --set v1.0 --seed 42

# Check telemetry compliance
torq telemetry --compliance

# View system status
torq status
```

---

## 🎯 Core Commands

### Evaluation System
```bash
# Run deterministic evaluation
torq eval run --set v1.0 --seed 42

# Compare with baseline
torq eval compare --baseline v1.0

# Generate report
torq eval report --format json
```

### Telemetry & Tracing
```bash
# View telemetry compliance
torq telemetry --compliance

# Trace specific request
torq trace <run_id>

# Monitor live metrics
torq monitor
```

### Performance Benchmarks
```bash
# Run performance benchmarks
torq bench run

# Check SLO status
torq bench slo --status
```

### Policy Management
```bash
# Test routing policies
torq policy test --policy v1.yaml

# Validate policy syntax
torq policy validate <policy_file>
```

---

## 📊 System Status

### Test Results
```bash
# Run full test suite
pytest tests/ -v

# Current status: 54/62 tests passing (87.1%)
# ML Systems tests: All passing
# Known issues: Content Safety fixture errors, Prince Flowers variable scope
# Fixes available: test_content_safety_fixed.py, marvin_query_router_fixed.py
```

### Evaluation Results
Latest evaluation results are stored in:
- `evaluation_results/` - Historical evaluation outputs
- `eval_sets/v1.0/` - Evaluation task definitions
- `demo_evaluation_results.json` - Sample results

Run `torq eval report` for latest metrics.

### Data Storage
- **Telemetry events**: Stored in local telemetry store
- **Evaluation results**: `evaluation_results/` directory
- **Benchmarks**: Generated on-demand with `torq bench run`
- **Policies**: `policies/` directory

---

## 🏗️ Architecture

```
TORQ Console v1.0
├── Core ML Systems
│   ├── Telemetry & Trace          # Structured event tracking
│   ├── Evaluation Engine          # Deterministic scoring
│   ├── Policy Framework           # YAML-based routing
│   ├── Benchmark System           # Performance monitoring
│   └── Security Sandbox           # Tool access control
├── Agent System
│   ├── Policy-Driven Router       # Intent-based routing
│   ├── Multi-Agent Coordination  # Agent orchestration
│   └── Query Analysis Engine     # Intent classification
└── Interfaces
    ├── CLI Tools                  # Command-line interface
    ├── Web Interface             # Browser-based UI
    └── Python API                # Programmatic access
```

---

## 📚 Documentation

### Available Documentation
- [CLAUDE.md](CLAUDE.md) - Claude Code integration guide
- [docs/](docs/) - Additional documentation and guides
- [eval_sets/v1.0/](eval_sets/v1.0/) - Evaluation task definitions
- [policies/](policies/) - Routing policy examples

### Configuration
Configuration files:
- `slo.yml` - Service Level Objectives
- `policies/routing/` - Routing policies
- Environment variables for API keys

---

## 🚀 Production Deployment

### Basic Deployment
```bash
# Production mode
torq-console --web --production

# With custom config
torq-console --web --config config.json
```

### Docker Support
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

EXPOSE 8899
CMD ["python", "-m", "torq_console.cli", "serve", "--production"]
```

---

## 🔧 Development

### Development Setup
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_ml_systems/ -v
```

### Code Quality
```bash
# Format code
black torq_console/
ruff check torq_console/

# Type checking
mypy torq_console/
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Ensure tests pass
4. Submit a pull request

### Running Tests
Before contributing, please run:
```bash
pytest tests/ -v --cov=torq_console
```

---

## 📈 Roadmap

### Completed
- ✅ ML Systems Hardening (5 milestones)
- ✅ Telemetry and tracing
- ✅ Deterministic evaluation
- ✅ Policy-driven routing
- ✅ Security sandbox

### Planned
- 🔄 Improved test coverage (target: 95%+)
- 📋 Observability dashboard
- 📋 Load testing framework
- 📋 Plugin architecture
- 📋 Multi-tenancy support

---

## 📜 License

MIT License – Open source and community-driven.

---

## 📌 Status

**TORQ Console v1.0 is production ready** with ML observability features implemented.

### Version History
- **v1.0.0**: ML Systems Hardening Complete (Current)
- **v0.80.0**: Enhanced capabilities with Marvin integration
- **v0.70.0**: Complete 4-phase integration
- **v0.60.0**: Initial MCP integration

**Ready for production use with comprehensive evaluation and monitoring.** 🚀

---

*Built with ❤️ by the open-source community.*