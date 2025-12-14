# TORQ CONSOLE - Comprehensive System Analysis Report

**Generated:** 2025-12-12
**Repository:** https://github.com/pilotwaffle/TORQ-CONSOLE

---

## Executive Summary

**TORQ CONSOLE** is a sophisticated AI-powered development platform that evolved from [Aider](https://github.com/Aider-AI/aider) (37k+ stars). It combines CLI speed with the Model Context Protocol (MCP) for agentic workflows, featuring an advanced multi-agent architecture centered around the "Prince Flowers" AI agent.

| Metric | Value |
|--------|-------|
| **Version** | 0.80.0+ |
| **Total Python Files** | 408 |
| **Core Package Lines** | 82,971 |
| **Test Files** | 107 |
| **License** | MIT |
| **Python Version** | 3.10+ |

---

## 1. Repository Structure

```
TORQ-CONSOLE/
├── torq_console/           # Main package (82,971 lines)
│   ├── agents/             # AI agent system (45+ files, ~700KB)
│   ├── api/                # FastAPI server & routes
│   ├── core/               # Core utilities
│   ├── indexer/            # Code scanning/indexing
│   ├── integrations/       # External service integrations
│   ├── llm/                # LLM provider abstraction
│   ├── marvin_integration/ # Marvin 3.x AI framework
│   ├── mcp/                # Model Context Protocol
│   ├── memory/             # Memory systems (Letta)
│   ├── orchestration/      # Workflow orchestration
│   ├── reasoning/          # Chain-of-thought reasoning
│   ├── spec_kit/           # Specification-driven development
│   ├── swarm/              # Multi-agent swarm system
│   ├── ui/                 # Web UI & CLI components
│   └── utils/              # Shared utilities
├── frontend/               # React/Vite frontend
├── docs/                   # Documentation
├── tests/                  # Test suite
└── 150+ documentation .md files
```

---

## 2. Agent Architecture

### 2.1 Prince Flowers Agent Family

The core AI agent with **multiple variants**:

| Variant | File | Lines | Purpose |
|---------|------|-------|---------|
| **TorqPrinceFlowers** | `torq_prince_flowers.py` | 4,535 | Full-featured production agent |
| **EnhancedPrinceFlowersV2** | `enhanced_prince_flowers_v2.py` | 1,200+ | Advanced RL learning |
| **MarvinPrinceFlowers** | `marvin_prince_flowers.py` | 400+ | Marvin-powered variant |
| **GLMPrinceFlowers** | `glm_prince_flowers.py` | 200+ | GLM-4 integration |
| **PrinceFlowersAgent** | `prince_flowers_agent.py` | 750+ | Base RL agent |

### 2.2 Agent Capabilities

**TorqPrinceFlowers** (main agent) includes:
- **ARTIST RL Learning System** - Learns from experience
- **Strategy Selection**: `direct_response`, `research_workflow`, `analysis_synthesis`, `multi_tool_composition`
- **12+ Integrated Tools** (see Section 5)
- **Multi-provider LLM Support** (Claude, OpenAI, DeepSeek, GLM, Ollama)
- **Conversation Memory** with semantic search
- **Browser Automation** via Playwright
- **n8n Workflow Integration**

### 2.3 Marvin Agent Orchestration

| Component | File | Purpose |
|-----------|------|---------|
| **MarvinQueryRouter** | `marvin_query_router.py` | Intelligent query routing |
| **MarvinAgentOrchestrator** | `marvin_orchestrator.py` | Multi-agent coordination |
| **MarvinAgentMemory** | `marvin_memory.py` | Persistent memory & learning |
| **MarvinWorkflowAgents** | `marvin_workflow_agents.py` | 5 specialized agents |

**Specialized Workflow Agents:**
1. CodeGenerationAgent
2. DebuggingAgent
3. DocumentationAgent
4. TestingAgent
5. ArchitectureAgent

### 2.4 Swarm Multi-Agent System

```
torq_console/swarm/
├── orchestrator.py           # Basic orchestration
├── orchestrator_advanced.py  # Advanced multi-agent coordination
├── memory_system.py          # Shared swarm memory
├── message_system.py         # Inter-agent messaging
├── communication_tools.py    # Communication protocols
└── agents/
    ├── analysis_agent.py     # Data analysis
    ├── code_agent.py         # Code generation (28KB)
    ├── documentation_agent.py # Docs generation (24KB)
    ├── performance_agent.py  # Performance optimization (25KB)
    ├── search_agent.py       # Web search
    ├── synthesis_agent.py    # Result synthesis
    ├── testing_agent.py      # Test generation (25KB)
    └── response_agent.py     # Response formatting
```

---

## 3. Spec-Kit System

**Specification-Driven Development** with RL-powered analysis:

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| **SpecEngine** | `spec_engine.py` | 1,000+ | Core specification management |
| **RLSpecAnalyzer** | `rl_spec_analyzer.py` | 500+ | RL-powered quality analysis |
| **MarvinSpecAnalyzer** | `marvin_spec_analyzer.py` | 350+ | AI-powered analysis |
| **MarvinQualityEngine** | `marvin_quality_engine.py` | 400+ | Multi-dimensional scoring |
| **AdaptiveIntelligence** | `adaptive_intelligence.py` | 750+ | Real-time suggestions |
| **EcosystemIntelligence** | `ecosystem_intelligence.py` | 900+ | GitHub/GitLab integration |
| **CollaborationServer** | `collaboration_server.py` | 500+ | WebSocket collaboration |
| **RealtimeEditor** | `realtime_editor.py` | 650+ | Live editing assistance |
| **SpecCommands** | `spec_commands.py` | 1,000+ | CLI commands |

**Workflow:** `/constitution` → `/specify` → `/plan` → `/tasks` → `/implement`

**Quality Dimensions:**
- Clarity Score (0.0 - 1.0)
- Completeness Score
- Feasibility Score
- Testability Score
- Maintainability Score

---

## 4. LLM Provider System

### 4.1 Supported Providers

```
torq_console/llm/providers/
├── claude.py           # Anthropic Claude
├── deepseek.py         # DeepSeek
├── glm.py              # GLM-4
├── ollama.py           # Local Ollama
├── llama_cpp_provider.py # llama.cpp
├── websearch.py        # Web search (54KB!)
└── content_safety.py   # Content moderation
```

### 4.2 LLM Manager

**File:** `llm/manager.py` (25KB)
- Intelligent routing across 20+ model types
- Usage analytics and cost tracking
- Automatic fallback handling
- Rate limiting and caching

---

## 5. Agent Tools

**12 Specialized Tools:**

| Tool | File | Size | Capabilities |
|------|------|------|--------------|
| **BrowserAutomation** | `browser_automation_tool.py` | 29KB | Playwright-based web automation |
| **CodeGeneration** | `code_generation_tool.py` | 23KB | Multi-language code generation |
| **FileOperations** | `file_operations_tool.py` | 21KB | Read/write/edit files |
| **MCPClient** | `mcp_client_tool.py` | 38KB | Model Context Protocol |
| **MultiToolComposition** | `multi_tool_composition_tool.py` | 38KB | Tool chaining/orchestration |
| **N8NWorkflow** | `n8n_workflow_tool.py` | 27KB | n8n automation integration |
| **TerminalCommands** | `terminal_commands_tool.py` | 20KB | Shell command execution |
| **ImageGeneration** | `image_generation_tool.py` | 10KB | AI image generation |
| **LandingPageGenerator** | `landing_page_generator.py` | 14KB | Website scaffolding |
| **TwitterPosting** | `twitter_posting_tool.py` | 12KB | Twitter/X automation |
| **LinkedInPosting** | `linkedin_posting_tool.py` | 12KB | LinkedIn automation |

---

## 6. RL Learning Systems

### 6.1 Core RL Components

| Component | File | Purpose |
|-----------|------|---------|
| **RLLearningSystem** | `rl_learning_system.py` | Base reinforcement learning |
| **EnhancedRLSystem** | `enhanced_rl_system.py` | Advanced RL with memory |
| **ActionLearning** | `action_learning.py` | Action pattern learning |
| **FeedbackLearning** | `feedback_learning.py` | User feedback integration |
| **PreferenceLearning** | `preference_learning.py` | User preference modeling |
| **MetaLearningEngine** | `meta_learning_engine.py` | Cross-task meta-learning |
| **SelfEvaluationSystem** | `self_evaluation_system.py` | Agent self-assessment |

### 6.2 RL Modules

```
torq_console/agents/rl_modules/
├── modular_agent.py      # Modular RL architecture
├── async_training.py     # Async training pipeline
└── dynamic_actions.py    # Dynamic action space
```

### 6.3 Advanced Features

- **ARTIST Algorithm** - Adaptive Response & Strategy for Intelligent Task Selection
- **MIT MBTL** - Meta-Batch Transfer Learning implementation
- **EvoAgentX** - Self-evolving architecture with genetic optimization
- **Zep Temporal Memory** - Cross-session learning (97.4% performance)

---

## 7. MCP Integration

**Model Context Protocol** for agentic workflows:

| Component | File | Purpose |
|-----------|------|---------|
| **MCPClient** | `client.py` | Core MCP client |
| **EnhancedClient** | `enhanced_client.py` | Extended capabilities |
| **ClaudeCodeBridge** | `claude_code_bridge.py` | Claude Code compatibility |
| **MCPManager** | `mcp_manager.py` | Server management |
| **MCPCommands** | `mcp_commands.py` | CLI commands |

**Supported MCP Servers:**
- GitHub
- PostgreSQL
- Jenkins
- Custom endpoints

---

## 8. UI Components

### 8.1 Web Interface

| Component | File | Size | Purpose |
|-----------|------|------|---------|
| **Web Server** | `web.py` | 97KB | Main FastAPI application |
| **CommandPalette** | `command_palette.py` | 70KB | VSCode-like command system |
| **InlineEditor** | `inline_editor.py` | 47KB | Ghost text suggestions |
| **IntentDetector** | `intent_detector.py` | 20KB | User intent classification |
| **LearningSystem** | `learning_system.py` | 20KB | UI-level learning |

### 8.2 Frontend (React/Vite)

```
frontend/
├── src/              # React components
├── package.json      # Dependencies
├── tailwind.config.js
├── vite.config.ts
└── tsconfig.json
```

---

## 9. Reasoning System

**Chain-of-Thought Reasoning:**

| Component | File | Size | Purpose |
|-----------|------|------|---------|
| **Core** | `reasoning/core.py` | 14KB | Base reasoning engine |
| **Enhancers** | `reasoning/enhancers.py` | 24KB | Reasoning enhancements |
| **Templates** | `reasoning/templates.py` | 31KB | CoT templates |
| **Validator** | `reasoning/validator.py` | 22KB | Output validation |

---

## 10. Memory Systems

### 10.1 Agent Memory

- **MarvinAgentMemory** - Persistent interaction tracking
- **AdvancedMemorySystem** - Semantic search + embedding
- **ConversationSession** - Session-based context

### 10.2 External Integration

- **Letta Integration** (`memory/letta_integration.py`)
- **Zep Temporal Memory** (97.4% performance improvement)

---

## 11. API & Deployment

### 11.1 API Server

```
torq_console/api/
├── server.py           # FastAPI server
├── routes.py           # API endpoints
└── socketio_handler.py # Real-time WebSocket
```

### 11.2 Deployment Options

- **Railway** (configured: `railway.toml`, `railway.json`)
- **Render** (`render.yaml`)
- **Vercel** (`vercel.json`)
- **Docker** (`.dockerignore`, `.railwayignore`)
- **Local** (`start_torq.bat`, `launch_torq_console.bat`)

---

## 12. Dependencies

### Core Dependencies

```toml
click>=8.0.0           # CLI framework
rich>=13.0.0           # Terminal formatting
fastapi>=0.100.0       # Web framework
uvicorn>=0.20.0        # ASGI server
websockets>=11.0.0     # WebSocket support
pydantic>=2.8.0        # Data validation
openai>=1.0.0          # OpenAI API
anthropic>=0.20.0      # Anthropic API
sentence-transformers>=2.2.0  # Embeddings
numpy>=1.24.0          # Numerical computing
scikit-learn>=1.3.0    # ML utilities
```

### Optional Dependencies

```toml
[marvin]   # Marvin 3.x integration
[voice]    # Speech recognition
[visual]   # Image processing
[context]  # Tree-sitter parsing
[dev]      # Development tools
```

---

## 13. Key Statistics

| Category | Count |
|----------|-------|
| Total Python files | 408 |
| Core package lines | 82,971 |
| Test files | 107 |
| Documentation files | 150+ |
| Agent tools | 12 |
| Swarm agents | 8 |
| LLM providers | 6 |
| Spec-Kit components | 10 |

### Largest Files

| File | Lines | Purpose |
|------|-------|---------|
| `torq_prince_flowers.py` | 4,535 | Main production agent |
| `web.py` | ~2,500 | Web interface |
| `command_palette.py` | ~1,800 | Command system |
| `websearch.py` | ~1,400 | Search provider |
| `enhanced_prince_flowers_v2.py` | ~1,200 | Enhanced agent |

---

## 14. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           TORQ CONSOLE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │   Web UI        │    │   CLI           │    │   API Server    │     │
│  │  (React/Vite)   │    │  (Click/Typer)  │    │  (FastAPI)      │     │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘     │
│           │                      │                      │               │
│           └──────────────────────┼──────────────────────┘               │
│                                  │                                       │
│  ┌───────────────────────────────▼───────────────────────────────────┐  │
│  │                    AGENT ORCHESTRATION LAYER                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │  │
│  │  │ QueryRouter │  │ Orchestrator│  │ Swarm Coord │                │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │  │
│  └─────────┼────────────────┼────────────────┼───────────────────────┘  │
│            │                │                │                          │
│  ┌─────────▼────────────────▼────────────────▼───────────────────────┐  │
│  │                      PRINCE FLOWERS AGENTS                         │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐      │  │
│  │  │   Torq     │ │  Enhanced  │ │   Marvin   │ │    GLM     │      │  │
│  │  │  Prince    │ │  Prince V2 │ │   Prince   │ │   Prince   │      │  │
│  │  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘      │  │
│  └────────┼──────────────┼──────────────┼──────────────┼─────────────┘  │
│           │              │              │              │                │
│  ┌────────▼──────────────▼──────────────▼──────────────▼─────────────┐  │
│  │                         TOOL LAYER                                 │  │
│  │  Browser | Code | File | MCP | N8N | Terminal | Social | Search   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                  │                                       │
│  ┌───────────────────────────────▼───────────────────────────────────┐  │
│  │                      LLM PROVIDER LAYER                            │  │
│  │  Claude | OpenAI | DeepSeek | GLM-4 | Ollama | Llama.cpp          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                  │                                       │
│  ┌───────────────────────────────▼───────────────────────────────────┐  │
│  │                      LEARNING & MEMORY                             │  │
│  │  RL System | Meta-Learning | Preference | Zep Memory | Feedback   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 15. Conclusion

**TORQ CONSOLE** is a comprehensive, production-ready AI development platform with:

1. **Multi-Agent Architecture** - Prince Flowers family with 5+ variants
2. **Intelligent Orchestration** - Marvin-powered routing and coordination
3. **12 Specialized Tools** - From browser automation to n8n workflows
4. **Advanced RL Learning** - ARTIST, Meta-Learning, Zep Memory
5. **Spec-Driven Development** - Complete specification-to-implementation workflow
6. **Multi-LLM Support** - 6+ providers with intelligent routing
7. **Production Deployment** - Railway, Render, Vercel, Docker ready
8. **Extensive Testing** - 107 test files, 100% phase completion

The system represents ~83,000 lines of production Python code with sophisticated AI agent capabilities suitable for enterprise development workflows.

---

## Related Documents

- [PRD: Plan-Approve-Execute Pattern](./PRD-Plan-Approve-Execute.md)
- [CLAUDE.md](../CLAUDE.md) - Claude Code integration guide
- [README.md](../README.md) - Main project documentation
