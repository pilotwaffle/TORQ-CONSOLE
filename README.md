# TORQ Console v1.0.0

[![GitHub stars](https://img.shields.io/github/stars/pilotwaffle/TORQ-CONSOLE?style=social)](https://github.com/pilotwaffle/TORQ-CONSOLE/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Last Commit](https://img.shields.io/github/last-commit/pilotwaffle/TORQ-CONSOLE)](https://github.com/pilotwaffle/TORQ-CONSOLE/commits/main)
[![Issues](https://img.shields.io/github/issues/pilotwaffle/TORQ-CONSOLE)](https://github.com/pilotwaffle/TORQ-CONSOLE/issues)
[![Tests](https://img.shields.io/github/actions/workflow/status/pilotwaffle/TORQ-CONSOLE/evaluation.yml)](https://github.com/pilotwaffle/TORQ-CONSOLE/actions)

> **Version:** 1.0.0 (ML Systems Hardening + Marvin 3.0 Complete)
> **Author:** B Flowers
> **Status:** **Production Ready** – Enterprise AI Platform
> **License:** MIT

TORQ Console is an enterprise AI development platform combining the speed of Aider with the polish of Cursor, enhanced with Model Context Protocol (MCP) for agentic workflows and comprehensive ML observability.

---

## v1.0.0 Release Highlights

### What's New in v1.0.0

#### Enhanced Prince Flowers Agent v2.0
- **Advanced Memory System** - Persistent conversation memory with session tracking
- **Meta-Learning Engine** - MAML-based fast adaptation for new tasks
- **Multi-Agent Debate** - Collaborative reasoning across specialized agents
- **Self-Evaluation System** - Confidence scoring and quality assessment
- **Hierarchical Task Planning** - Complex task decomposition with coordination
- **Adaptive Quality Manager** - Dynamic quality control and error pattern learning

#### Marvin 3.0 Integration
- **Structured Outputs** - Type-safe data extraction with Pydantic
- **Spec-Kit Enhancement** - AI-powered specification analysis
- **Intelligent Query Routing** - Automatic agent selection based on intent
- **5 Specialized Workflow Agents** - Code, Debug, Docs, Testing, Architecture
- **MarvinAgentOrchestrator** - Multi-agent coordination with 4 execution modes

#### ML Systems Hardening
- **Telemetry System** - Structured event tracking with canonical schema
- **Distributed Tracing** - Request flow monitoring across services
- **Evaluation Sets** - v1.0 with 10 comprehensive tasks
- **Policy-Driven Routing** - YAML-based routing with zero-code updates
- **Performance Benchmarks** - SLO enforcement and regression detection

#### Web Search Integration
- **Multi-Provider Support** - Google Custom Search, Brave, DuckDuckGo
- **Intelligent Fallback** - Automatic provider switching on failure
- **Content Synthesis** - Multi-document result aggregation
- **Plugin Architecture** - Reddit, HackerNews, ArXiv built-in sources

---

## Quick Start

### Prerequisites
- Python 3.10+
- Git
- (Optional) API keys for web search features

### Installation

```bash
# Clone repository
git clone https://github.com/pilotwaffle/TORQ-CONSOLE.git
cd TORQ-CONSOLE

# Install dependencies
pip install -e .

# Start with web interface
torq-console --web
```

### Environment Setup

```bash
# Create .env file for API keys
cat > .env << EOF
# Anthropic Claude (recommended for agents)
ANTHROPIC_API_KEY=your_key_here

# Web Search (optional - Brave fallback available)
GOOGLE_API_KEY=your_key_here
GOOGLE_CSE_ID=your_cse_id_here

# OpenAI (optional)
OPENAI_API_KEY=your_key_here
EOF
```

### Verify Installation

```bash
# Test package import
python -c "import torq_console; print(f'TORQ Console v{torq_console.__version__} installed')"

# Run evaluation set
torq-console eval --set v1.0 --seed 42

# View available commands
torq-console --help
```

---

## Core Commands

### Enhanced Prince Flowers Agent

```bash
# Interactive chat with memory
torq-console agent chat "Explain async/await patterns"

# Generate code with specialized agent
torq-console agent code "Binary search tree implementation" --language=python

# Debug with analysis
torq-console agent debug "def calc(x): return x/0" "ZeroDivisionError" --language=python

# Generate documentation
torq-console agent docs "def add(a, b): return a + b" --type=api --language=python

# Multi-agent orchestration
torq-console agent orchestrate "Build authentication system" --mode=multi_agent
```

### Evaluation System

```bash
# Run v1.0 evaluation set
torq-console eval --set v1.0

# With specific seed for reproducibility
torq-console eval --set v1.0 --seed 42

# Save results to file
torq-console eval --set v1.0 --output results.json

# View evaluation status
torq-console eval --status
```

### Web Interface

```bash
# Start web server (default: http://localhost:8888)
torq-console --web

# Production mode
torq-console --web --production

# Custom port
torq-console --web --port 9000
```

### Telemetry & Tracing

```bash
# View telemetry events
torq-console telemetry --last 1h

# Trace specific execution
torq-console trace <run_id>

# Performance benchmarks
torq-console benchmark --suite v1.0
```

---

## Architecture

### v1.0.0 System Components

```
TORQ Console v1.0.0
├── Core ML Systems
│   ├── Telemetry & Trace          # Structured event tracking
│   ├── Evaluation Engine          # Deterministic scoring (10 tasks)
│   ├── Policy Framework           # YAML-based routing
│   ├── Benchmark System           # SLO enforcement
│   └── Security Sandbox           # Tool access control
├── Agent System
│   ├── Enhanced Prince Flowers v2.0
│   │   ├── Advanced Memory System
│   │   ├── Meta-Learning Engine (MAML)
│   │   ├── Multi-Agent Debate
│   │   ├── Self-Evaluation System
│   │   └── Hierarchical Task Planner
│   ├── Marvin 3.0 Integration
│   │   ├── Query Router (Intent-based)
│   │   ├── 5 Specialized Agents
│   │   ├── Agent Orchestrator
│   │   └── Agent Memory System
│   └── Policy-Driven Router       # Zero-code updates
├── Web Search Integration
│   ├── Multi-Provider Support       # Google, Brave, DDG
│   ├── Intelligent Fallback
│   ├── Plugin Architecture          # Reddit, HN, ArXiv
│   └── Content Synthesis
└── Interfaces
    ├── CLI Tools                  # Full command suite
    ├── Web Interface             # Browser-based UI
    └── Python API                # Programmatic access
```

### Enhanced Prince Flowers Agent Architecture

```
EnhancedPrinceFlowers (v2.0)
├── Memory Systems
│   ├── EnhancedMemorySystem       # Vector + episodic memory
│   ├── ConversationSession        # Multi-turn tracking
│   └── Agent Memory (Marvin)     # Preference learning
├── Learning Systems
│   ├── MetaLearningEngine         # MAML fast adaptation
│   ├── PreferenceLearning         # User pattern learning
│   ├── FeedbackLearning           # Performance optimization
│   └── ActionLearning             # Success pattern extraction
├── Reasoning Systems
│   ├── MultiAgentDebate           # Collaborative reasoning
│   ├── HierarchicalTaskPlanner    # Task decomposition
│   └── SelfEvaluationSystem       # Confidence scoring
└── Quality Systems
    ├── AdaptiveQualityManager       # Dynamic quality control
    ├── ImprovedDebateActivation   # Intelligent debate triggering
    └── HandoffOptimizer           # Agent selection optimization
```

---

## Features

### Verified Working Features v1.0.0

| Feature | Status | Description |
|---------|--------|-------------|
| **Package Installation** | Complete | `pip install -e .` works |
| **CLI Framework** | Complete | Full help system and commands |
| **Evaluation System** | Complete | 10 tasks in v1.0 eval set |
| **Web Interface** | Complete | Browser-based UI server |
| **Configuration Management** | Complete | YAML/env config support |
| **MCP Integration** | Complete | Server connection framework |
| **Enhanced Prince Flowers v2.0** | Complete | All 5 AI systems working |
| **Marvin 3.0 Integration** | Complete | Spec analysis + agents |
| **Web Search (Brave)** | Complete | Fallback provider working |
| **Telemetry System** | Complete | Event tracking infrastructure |
| **Policy Routing** | Complete | YAML-based routing |

### Agent Capabilities

#### Enhanced Prince Flowers v2.0 Methods
- `chat_with_memory(query)` - Interactive conversation with memory
- `get_session_summary()` - Session analytics and metrics
- `get_stats()` - Performance statistics
- `get_user_preferences()` - Retrieve learned preferences
- `record_feedback()` - Submit performance feedback
- `clear_session()` - Reset conversation state

#### Marvin Workflow Agents
- **CodeGenerationAgent** - Clean, documented code with examples
- **DebuggingAgent** - Root cause analysis and fixes
- **DocumentationAgent** - API docs and guides
- **TestingAgent** - Comprehensive test suites
- **ArchitectureAgent** - System design with trade-off analysis

---

## Configuration

### Environment Variables

```bash
# Required for AI features
ANTHROPIC_API_KEY=sk-ant-xxx          # Anthropic Claude (recommended)
OPENAI_API_KEY=sk-xxx                   # OpenAI (alternative)

# Web Search (optional - Brave works without these)
GOOGLE_API_KEY=xxx
GOOGLE_CSE_ID=xxx
BRAVE_API_KEY=xxx                        # Brave Search API

# MCP Configuration
MCP_SERVER_URL=localhost:3100
```

### Configuration Files

```bash
# Service Level Objectives
slo.yml:
  response_time_p95: 2000ms
  error_rate_budget: 0.01

# Routing Policies
policies/routing/v1.yaml:
  agent: enhanced_prince_flowers
  fallback: marvin_orchestrator

# Evaluation Sets
eval_sets/v1.0/tasks.json:
  - name: code_generation
  - weight: 1.0
```

---

## Documentation

### Available Documentation
- [CLAUDE.md](CLAUDE.md) - Complete integration guide with Marvin 3.0
- [docs/](docs/) - Additional documentation and guides
- [eval_sets/v1.0/](eval_sets/v1.0/) - Evaluation task definitions
- [policies/](policies/) - Routing policy examples

### CLI Command Reference

```bash
# View all commands
torq-console --help

# Agent commands
torq-console agent --help

# Evaluation commands
torq-console eval --help

# Telemetry commands
torq-console telemetry --help
```

---

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

EXPOSE 8888
CMD ["python", "-m", "torq_console.cli", "serve", "--production"]
```

### Running with Docker

```bash
# Build image
docker build -t torq-console:1.0.0 .

# Run container
docker run -p 8888:8888 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  torq-console:1.0.0
```

### Railway Deployment

```bash
# Deploy to Railway
railway up

# View logs
railway logs
```

---

## Development

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_ml_systems/ -v
pytest tests/test_marvin/ -v
pytest tests/test_agents/ -v
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

## Roadmap

### Completed v1.0.0
- ML Systems Hardening (5 milestones)
- Enhanced Prince Flowers Agent v2.0
- Marvin 3.0 Integration
- Web Search with Fallback
- Telemetry and Tracing
- Policy-Driven Routing

### Planned Future Releases
- Improved test coverage (target: 95%+)
- Observability dashboard
- Load testing framework
- Plugin architecture
- Multi-tenancy support
- Real-time collaboration

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Running Tests Before Contributing

```bash
pytest tests/ -v --cov=torq_console
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Status

**TORQ Console v1.0.0 is production ready** with comprehensive agent capabilities, ML observability, and enterprise-grade features.

### Version History
- **v1.0.0**: ML Systems Hardening + Enhanced Prince Flowers v2.0 + Marvin 3.0 (Current)
- **v0.80.0**: Enhanced capabilities with Marvin integration
- **v0.70.0**: Complete 4-phase integration
- **v0.60.0**: Initial MCP integration

**Ready for production use.**

---

*Built with ❤️ by the open-source community.*
