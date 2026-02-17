# TORQ Console Dashboard — Product Requirements Document v5.1.0

**Document:** PRD-TORQ-DASHBOARD-v5.1.0
**Author:** Ground-Truth Analysis from Source Code
**Date:** February 16, 2026
**Status:** APPROVED — Ready for Implementation
**Supersedes:** PRD v5.0.0

---

## 1. Executive Summary

This PRD defines the TORQ Console Dashboard UI, grounded in verified source code analysis of the **full `torq_console` Python package** (~200+ files across 20+ subpackages), **55 Claude Code agent definitions** (markdown/JSON), and the **existing FastAPI backend with 7 working API endpoints**. It supersedes PRD v5.0.0 with complete ground-truth discovery from the actual repository.

**Key discovery from source code:**
1. The TORQ system operates as two distinct agent layers — a Python backend orchestration layer AND a Claude Code sub-agent layer
2. A **working FastAPI backend already exists** with chat, agents, sessions, and status endpoints in `torq_console/api/routes.py`
3. The `torq_console` package is **4x larger** than initially analyzed — ~200+ Python files including LLM provider management, safety/rate-limiting, MCP integration, benchmarking, and more
4. The Vercel entry point (`api/index.py`) imports from `torq_console.ui.railway_app`, which wraps the FastAPI server

---

## 2. Architecture Discovery: The Dual-Layer Agent System

### 2.1 Layer 1: Python Backend Agents (Runtime Orchestration)

These are Python classes that execute at runtime via the MarvinAgentOrchestrator. They process queries, route to specialists, and return responses.

**Verified Python agent classes (38 files, 19,511 lines):**

| Module | Key Classes | Lines | Status |
|--------|-------------|-------|--------|
| marvin_orchestrator.py | MarvinAgentOrchestrator | 500 | Active — 2 registered agents |
| marvin_query_router.py | MarvinQueryRouter | 723 | Active — 5 agent registry entries |
| marvin_query_router_fixed.py | MarvinQueryRouter (fixed) | 472 | Active — 6 registry entries |
| marvin_prince_flowers.py | MarvinPrinceFlowers | 456 | Active — primary conversational agent |
| enhanced_prince_flowers_v2.py | EnhancedPrinceFlowers | 1,122 | Active — integrates 5 AI subsystems |
| marvin_workflow_agents.py | CodeGeneration, Debugging, Documentation, Testing, Architecture agents | 585 | Active — 5 specialized workflow agents |
| torq_search_master.py | TORQSearchMaster | 1,071 | Active — multi-API search (CoinGecko, Tavily, Perplexity, Brave, Google) |
| intent_detector.py | IntentDetector | 591 | Active — Sentence Transformer semantic routing to 12 tool categories |
| n8n_architect_agent.py | N8NWorkflowArchitectAgent | 525 | Active — 3-phase workflow design/generation |
| orchestrator.py | SwarmOrchestrator | 296 | Active — 4-agent chain (search→analysis→synthesis→response) |
| orchestrator_advanced.py | AdvancedSwarmOrchestrator | 658 | Active — 8 agents, real parallel execution |
| policy_driven_router.py | PolicyDrivenRouter | 494 | Active — policy enforcement layer over MarvinQueryRouter |
| policy_framework.py | PolicyFramework, RoutingPolicy | 568 | Active — YAML-based routing policy loading |
| hierarchical_task_planner.py | SearchSpecialist, AnalysisSpecialist, SynthesisSpecialist, CodeGenerationSpecialist, HighLevelStrategyAgent | 576 | Active — HRL task planning |
| multi_agent_debate.py | MultiAgentDebate | 494 | Active — 5 debate roles |
| meta_learning_engine.py | MetaLearningEngine | 570 | Active — MAML algorithm |
| self_evaluation_system.py | SelfEvaluationSystem | 605 | Active — confidence + quality assessment |
| test_generation_agent.py | TestGenerationAgent | 511 | Active — automated test generation |
| advanced_memory_system.py | EnhancedMemorySystem | 514 | Active — Zep + RAG + consolidation |
| memory_integration.py | MemoryIntegration | 445 | Active — Supabase RAG, pgvector |
| marvin_memory.py | MarvinAgentMemory | 406 | Active — interaction tracking, 8 types |
| agent_system_enhancements.py | CrossAgentLearning, AgentPerformanceMonitor | 557 | Active — cross-agent learning |
| rl_learning_system.py | ARTISTRLSystem | 386 | Active — GRPO RL with error correction |
| enhanced_rl_system.py | EnhancedRLSystem | 504 | Active — extended RL |
| action_learning.py | ActionOrientedLearning | ~350 | Active — action vs clarification decisions |
| adaptive_quality_manager.py | AdaptiveQualityManager | ~400 | Active — adaptive quality thresholds |
| conversation_session.py | ConversationSession, SessionManager | ~350 | Active — session management |
| feedback_learning.py | FeedbackLearning | ~400 | Active — feedback capture + correction |
| preference_learning.py | PreferenceLearning | 367 | Active — user preference detection |
| handoff_context.py | HandoffPreservationTracker | ~350 | Active — context preservation |
| handoff_optimizer.py | (HandoffOptimizer) | 691 | Active — handoff optimization |
| improved_debate_activation.py | ImprovedDebateActivation | ~400 | Active — debate trigger system |
| marvin_commands.py | MarvinCommands | 686 | Active — CLI interface |
| search_formatters.py | SimpleFormatter, StandardFormatter, DetailedFormatter, TechnicalFormatter | 236 | Active — 4 output modes |
| prince_flowers_agent.py | PrinceFlowersAgent | 681 | Active — TORQ Console integration |
| prince_flowers_enhanced_integration.py | (Enhanced integration) | 692 | Active |
| prince_flowers_enhanced_integration_new.py | PrinceFlowersAgent (new) | 253 | Active — ARTIST RL integration |
| torq_prince_flowers.py | Backward compatibility shim | 41 | Active — import redirect |
| torq_prince_flowers/ (package) | TORQPrinceFlowers, TORQPrinceFlowersInterface — core/agent.py, core/state.py, capabilities/{execution,learning,planning,reasoning}.py, tools/{file_ops,websearch}.py, interface.py | ~89KB (11 files) | Active — primary agent package (NOT YET UPLOADED, structure verified from directory listing) |

### 2.2 Layer 2: Claude Code Sub-Agents (Prompt Definitions)

These are markdown/JSON files in `E:\.claude\agents\` that define specialized agents for Claude Code to invoke. They are NOT loaded by the Python backend — they are prompt templates with tool permissions, trigger conditions, and response formats for Claude Code's agent system.

**Complete Claude Code Agent Registry (55 files: 51 markdown + 4 JSON):**

Note: Some agents have both .md and .json variants (e.g., cybersecurity-expert, frontend-architect). The actual unique agent count is ~47 distinct agents, with the remainder being alternate prompt versions, coordination plans, and config files.

**Development Agents (12):**

| Agent | Format | Description |
|-------|--------|-------------|
| backend-engineer | .md | Production backend APIs, databases, auth, microservices |
| BACKEND_ENGINEER | .md | Elite backend engineer v2 (alternate prompt) |
| Elite_Code_Writer | .md | Elite senior software engineer, all languages |
| expert-software-engineer | .md | 10+ years production, code-first delivery |
| frontend-architect | .md + .json | Modern web technologies, RSC, micro-frontends |
| frontend-Engineer (v2.2) | .md | Frontend Architect with RSC, edge-first, AI workflows |
| fullstack-orchestrator | .md | End-to-end feature delivery across all layers |
| python-expert | .md | Python Expert Agent v2.0, elite production code |
| VS_Code_writer_agent | .md | VS Code configuration file management |
| code-reviewer | .md | CodeScan — static analysis, security, schema validation |
| prompt-library-builder | .md | NextJS + Supabase prompt library application |
| prd-generator | .md | Product requirements document generation |

**Data & Research Agents (4):**

| Agent | Format | Description |
|-------|--------|-------------|
| data-researcher | .md | Automated data discovery, collection, analysis |
| data-scientist | .md | Statistical analysis, ML, business insights |
| market-researcher | .md | Market analysis, consumer insights, competitive intel |
| research-expert | .md | In-depth research using Gemini headless mode |

**Finance & Trading Agents (4):**

| Agent | Format | Description |
|-------|--------|-------------|
| fintech-engineer | .md | Financial systems, regulatory compliance, secure transactions |
| quant-analyst | .md | Quantitative analysis, algorithmic trading, risk analytics |
| risk-manager | .md | Risk assessment, mitigation, compliance frameworks |
| trading-bot-specialist | .md | Python trading algorithms, crypto systems |

**Security Agents (4):**

| Agent | Format | Description |
|-------|--------|-------------|
| cybersecurity-expert | .md + .json | Threat detection, MITRE ATT&CK, NIST CSF |
| cybersecurity-strategist | .json | Strategic security posture, Zero Trust |
| security-compliance-agent | .md | Vulnerability fixes, XSS/CSRF prevention |
| credential-security-agent | .md | API key rotation, credential management |

**N8N & Workflow Agents (5):**

| Agent | Format | Description |
|-------|--------|-------------|
| n8n-backend-developer | .md | N8N workflow building, AI/API/DB integration |
| n8n-workflow-expert | .md | FlowForge — workflow architect + automation |
| workflow-architect-agent | .md | Complex n8n workflow architecture design |
| workflow-testing-agent | .md | Workflow validation, integration testing, QA |
| content-intelligence-agent | .md | Content aggregation, analysis, newsletter generation |

**DevOps & Deployment Agents (3):**

| Agent | Format | Description |
|-------|--------|-------------|
| deployment-expert | .md | Vercel, Coolify, Docker deployments, CI/CD |
| deployment-orchestrator-agent | .md | Staging/production deployments, rollback |
| database-specialist | .md | Supabase operations, schema design, optimization |

**PDF AI Swarm (6 — complete 5-agent team + coordination plan):**

| Agent | Format | Description |
|-------|--------|-------------|
| pdf-ai-component-developer | .md | React components, state management, file upload |
| pdf-ai-content-strategist | .md | Marketing copy, SEO, conversion optimization |
| pdf-ai-integration-specialist | .md | API connections, analytics, form handling |
| pdf-ai-quality-assurance | .md | Testing, performance, cross-browser, accessibility |
| pdf-ai-uiux-designer | .md | Responsive layouts, design system, animations |
| pdf-ai-swarm-coordination-plan | .md | 5-agent swarm coordination blueprint |

**Automation & Browser Agents (3):**

| Agent | Format | Description |
|-------|--------|-------------|
| browser-automation-specialist | .md | Kapture browser automation, web testing |
| file-organizer-agent | .md | Project file organization, directory structures |
| scheduling-assistant | .md | Calendar management, appointment handling |

**Performance & Monitoring Agents (3):**

| Agent | Format | Description |
|-------|--------|-------------|
| performance-engineer | .md | Systematic performance optimization |
| performance-monitor | .md | TokenGuard — token usage, response times, costs |
| performance-optimization-agent | .md | React Error Boundary, dark mode, calendar optimization |

**TTS & Voice Agents (4):**

| Agent | Format | Description |
|-------|--------|-------------|
| hume-tts-agent | .md | Hume AI Octave TTS API |
| minimax-tts-agent | .md | Minimax Speech-02 API, voice cloning |
| tts-completion-agent | .md | Audio completion notifications |
| tts-summary-agent | .md | Voice summary and audio feedback |

**Specialist Agents (5):**

| Agent | Format | Description |
|-------|--------|-------------|
| tbs-website-specialist | .md | TBS website (Vercel + Firebase), JAMstack |
| system-administrator-expert | .md | System administration, high availability |
| viral-content-strategist | .md | Viral content using 2025 psychology + algorithms |
| search-specialist | .md | SearchMaster v3.5-Ultimate |
| project-analyzer-agent | .md | Project structure analysis, codebase understanding |

**Meta & Utility Agents (3):**

| Agent | Format | Description |
|-------|--------|-------------|
| meta-agent | .md | Agent builder — creates new sub-agents |
| hello-world-agent | .md | Simple greeting + tech news |
| deployment-summary | .md | Agent deployment summary/docs |

**Config Files (3):**

| File | Format | Description |
|------|--------|-------------|
| checklists | .json | Security, performance, maintainability, workflow checklists |
| frontend-architect | .json | Frontend architect configuration |
| cybersecurity-expert | .json | Cybersecurity expert structured config |

---

## 3. Critical Architecture Gaps (Backend → Dashboard)

### 3.1 What EXISTS and works

| Capability | Backend Module | Status |
|------------|---------------|--------|
| Query routing with AI classification | marvin_query_router.py + policy_driven_router.py | Working |
| Semantic intent detection (12 tools) | intent_detector.py | Working |
| Conversational agent with history | marvin_prince_flowers.py + enhanced_prince_flowers_v2.py | Working |
| 5 workflow specialist agents | marvin_workflow_agents.py | Working |
| 4-agent swarm chain | orchestrator.py | Working |
| 8-agent swarm with real parallel | orchestrator_advanced.py | Working |
| Multi-API search (5 providers) | torq_search_master.py | Working |
| Multi-agent debate (5 roles) | multi_agent_debate.py | Working |
| Memory + RAG + pgvector | memory_integration.py + advanced_memory_system.py | Working (requires Supabase) |
| RL learning (ARTIST/GRPO) | rl_learning_system.py | Working |
| Session management | conversation_session.py | Working |
| Feedback + preference learning | feedback_learning.py + preference_learning.py | Working |
| N8N workflow architect | n8n_architect_agent.py | Working |
| Quality + self-evaluation | adaptive_quality_manager.py + self_evaluation_system.py | Working |
| WebSocket via Socket.IO | agentStore.ts + coordinationStore.ts | Working |

### 3.2 Enhanced Prince Flowers v2 — Subsystem Flow

The primary agent (`enhanced_prince_flowers_v2.py`) integrates 5 AI subsystems in this processing order:

```
User Query
  → 1. Advanced Memory (Zep + RAG + Consolidation) — retrieves relevant context
  → 2. Hierarchical Task Planning (HRL with 4 specialists) — breaks into subtasks
  → 3. Meta-Learning Engine (MAML algorithm) — adapts strategy from past tasks
  → 4. Multi-Agent Debate (5 roles: proposer/questioner/creative/fact_checker/synthesizer)
  → 5. Self-Evaluation System (confidence scoring + quality assessment)
  → Response with metadata
```

### 3.3 Now-Verified Components (from repo analysis)

| Component | Location | Contents |
|-----------|----------|----------|
| torq_prince_flowers/integrations/ | Package subfolder | `mcp.py` — MCP integration for the agent |
| torq_prince_flowers/utils/ | Package subfolder | `context.py` — context management; `performance.py` — performance tracking |
| core/state.py enums | torq_prince_flowers/core/state.py | `ReasoningMode` (5 values: direct, research, analysis, composition, meta_planning); `AgenticAction`, `ReasoningTrajectory`, `TORQAgentResult` are dataclasses |
| torq_console/api/ | Internal API package | `server.py` (FastAPI app), `routes.py` (7 existing endpoints), `socketio_handler.py` (Socket.IO), `crypto_price.py` |
| policies/ folder | Root directory | EXISTS — YAML routing policy files, not yet read |
| capabilities.yaml | Root directory | EXISTS — agent capability definitions, not yet read |

### 3.4 Existing Test Infrastructure

The project contains **100+ test files** in the root directory plus a `tests/` folder. Key test categories: prince flowers integration, search routing, RL learning, policy routing, handoff improvements, phase validation (1-5), telemetry, and tool safety. The dashboard's QA phase can leverage this existing test infrastructure for backend endpoint validation.

### 3.5 What does NOT exist (must build for dashboard)

| Capability | What's Needed | Priority | Notes |
|------------|--------------|----------|-------|
| SSE streaming endpoint | `POST /api/agents/{id}/chat/stream` wrapping orchestrator.process_query() with StreamingResponse | P0 | Existing non-streaming chat works; this adds streaming |
| REST API for providers | `GET /api/providers` listing configured LLM providers from `torq_console.llm.manager` | P1 | Provider system exists in llm/providers/; needs HTTP surface |
| REST API for routing logs | `GET /api/routing/history` exposing router.routing_history | P1 | MarvinQueryRouter tracks history internally |
| REST API for search | `POST /api/search` wrapping TORQSearchMaster.search() | P1 | TORQSearchMaster exists; needs HTTP surface |
| REST API for memory | `GET/POST /api/memory` wrapping MemoryIntegration methods | P2 | Memory system exists; needs HTTP surface |
| REST API for n8n workflows | `POST /api/workflows` wrapping n8n_architect_agent | P2 | N8N architect exists; needs HTTP surface |
| Claude Code agent registry API | `GET /api/agents/claude-code` reading agent .md files | P2 | mcp/claude_code_bridge.py may help |
| Swarm team configuration API | `GET /api/swarms` reading swarms.json | P3 | swarms.json exists; needs HTTP surface |

**Already exists (no work needed):**
- `POST /api/agents/{id}/chat` — working chat endpoint with orchestrator routing
- `GET /api/agents` — lists 3 agents with live metrics
- `GET /api/status` — system status with comprehensive metrics
- `GET/POST /api/sessions` — session management
- `GET /health` — health check
- Socket.IO WebSocket integration
- CORS configuration
- SPA static file serving

---

## 4. Verified Enum Alignment

All dashboard UI enums MUST match these exact Python values:

### 4.1 Orchestration Modes (MarvinAgentOrchestrator)
```python
"single_agent" | "multi_agent" | "pipeline" | "parallel"
```

### 4.2 Complexity Levels (MarvinQueryRouter)
```python
class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"
```

### 4.3 Agent Capabilities (MarvinQueryRouter)
```python
class AgentCapability(str, Enum):
    SPEC_ANALYSIS = "spec_analysis"
    CODE_REVIEW = "code_review"
    WEB_SEARCH = "web_search"
    RESEARCH = "research"
    TASK_PLANNING = "task_planning"
    GENERAL_CHAT = "general_chat"
    CODE_GENERATION = "code_generation"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
```

### 4.4 Intent Classifications (IntentDetector tool categories)
```python
"web_search" | "image_generation" | "social_media" | "landing_page_generator" |
"file_operations" | "code_generation" | "code_analyzer" | "n8n_workflow" |
"browser_automation" | "terminal_commands" | "mcp_client" | "multi_tool_composition"
```

### 4.5 Interaction Types (MarvinAgentMemory)
```python
class InteractionType(str, Enum):
    QUERY = "query"
    RESEARCH = "research"
    IDEATION = "ideation"
    CODE_GENERATION = "code_generation"
    DEBUG = "debug"
    DOCUMENTATION = "documentation"
    SPEC_ANALYSIS = "spec_analysis"
    GENERAL_CHAT = "general_chat"
```

### 4.6 Workflow Types (marvin_workflow_agents.py)
```python
class WorkflowType(str, Enum):
    CODE_GENERATION = "code_generation"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    REFACTORING = "refactoring"
    N8N_WORKFLOW_ARCHITECT = "n8n_workflow_architect"
```

### 4.7 Search Output Modes (torq_search_master.py)
```python
class OutputMode(Enum):
    SIMPLE = "simple"
    STANDARD = "standard"
    DETAILED = "detailed"
    TECHNICAL = "technical"
```

### 4.8 Debate Protocols (improved_debate_activation.py)
```python
class DebateProtocol(Enum):
    NONE = "none"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    JUDGE = "judge"
    CRITIQUE = "critique"
```

### 4.9 Debate Roles (multi_agent_debate.py)
```python
class DebateRole(Enum):
    PROPOSER = "proposer"
    QUESTIONER = "questioner"
    CREATIVE = "creative"
    FACT_CHECKER = "fact_checker"
    SYNTHESIZER = "synthesizer"
```

### 4.10 Memory Types (advanced_memory_system.py)
```python
class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    WORKING = "working"
    PROCEDURAL = "procedural"
```

### 4.11 Agent Roles (agent_system_enhancements.py)
```python
class AgentRole(Enum):
    GENERALIST = "generalist"
    SPECIALIST_CODE = "specialist_code"
    SPECIALIST_DEBUG = "specialist_debug"
    SPECIALIST_ARCH = "specialist_arch"
    SPECIALIST_TEST = "specialist_test"
    COORDINATOR = "coordinator"
    MONITOR = "monitor"
```

### 4.12 Confidence Levels (self_evaluation_system.py)
```python
class ConfidenceLevel(Enum):
    VERY_HIGH = "very_high"   # > 0.9
    HIGH = "high"             # 0.7 - 0.9
    MEDIUM = "medium"         # 0.5 - 0.7
    LOW = "low"               # 0.3 - 0.5
    VERY_LOW = "very_low"     # < 0.3
```

### 4.13 Test Types (test_generation_agent.py)
```python
class TestType(Enum):
    EDGE_CASE = "edge_case"
    ADVERSARIAL = "adversarial"
    FAILURE_DERIVED = "failure_derived"
    PATTERN_VARIATION = "pattern_variation"
    BOUNDARY_CONDITION = "boundary_condition"
```

### 4.14 Feedback Types (feedback_learning.py)
```python
class FeedbackType(Enum):
    ACCEPTED = "accepted"
    MODIFIED = "modified"
    REJECTED = "rejected"
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    CORRECTION = "correction"
```

### 4.15 Handoff Types (handoff_context.py)
```python
class HandoffType(Enum):
    MEMORY_TO_PLANNING = "memory_to_planning"
    PLANNING_TO_DEBATE = "planning_to_debate"
    DEBATE_TO_EVALUATION = "debate_to_evaluation"
    EVALUATION_TO_MEMORY = "evaluation_to_memory"
```

### 4.16 Action Decisions (action_learning.py)
```python
class ActionDecision(str, Enum):
    IMMEDIATE_ACTION = "immediate_action"
    ASK_CLARIFICATION = "ask_clarification"
    PROVIDE_OPTIONS = "provide_options"
```

### 4.17 Policy Compliance Status (policy_framework.py)
```python
class PolicyComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    VIOLATION = "violation"
    ESCALATION = "escalation"
    FALLBACK = "fallback"
```

### 4.18 Quality Dimensions (self_evaluation_system.py)
```python
class QualityDimension(Enum):
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    RELEVANCE = "relevance"
    COHERENCE = "coherence"
```

### 4.19 Memory Importance (advanced_memory_system.py)
```python
class MemoryImportance(Enum):
    CRITICAL = 1.0
    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4
    TRIVIAL = 0.2
```

### 4.20 N8N Workflow Triggers (n8n_architect_agent.py)
```python
class WorkflowTriggerType(str, Enum):
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    SUB_WORKFLOW = "sub_workflow"
```

### 4.21 N8N Error Handling (n8n_architect_agent.py)
```python
class ErrorHandlingStrategy(str, Enum):
    HARD_FAIL = "hard_fail"       # Stop + Alert
    SOFT_FAIL = "soft_fail"       # Log + Continue
    RETRY_BACKOFF = "retry_backoff"  # Retry with exponential backoff
```

### 4.22 Request Patterns (action_learning.py)
```python
class RequestPattern(str, Enum):
    RESEARCH_REQUEST = "research"
    IDEATION_REQUEST = "ideation"
    BUILD_REQUEST = "build"
    EXPLAIN_REQUEST = "explain"
    DEBUG_REQUEST = "debug"
```

### 4.23 ReasoningMode (torq_prince_flowers/core/state.py) — VERIFIED
```python
class ReasoningMode(Enum):
    DIRECT = "direct"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    COMPOSITION = "composition"
    META_PLANNING = "meta_planning"
```

**Note:** `AgenticAction`, `ReasoningTrajectory`, and `TORQAgentResult` are **dataclasses**, not enums. Key fields:

- `AgenticAction`: action_type (str), parameters (dict), success (bool), execution_time (float), tool_used (str?)
- `ReasoningTrajectory`: trajectory_id, query, mode (ReasoningMode), actions (list[AgenticAction]), confidence_score (float), self_corrections (int)
- `TORQAgentResult`: success (bool), response (str), trajectory?, metadata (dict), tools_used (list[str]), confidence (float), execution_time (float)

---

## 4b. Existing Deployment Infrastructure

The project root contains deployment configs for multiple platforms — the dashboard should leverage the existing Vercel configuration:

| File | Platform | Status | Dashboard Relevance |
|------|----------|--------|-------------------|
| `vercel.json` | Vercel | EXISTS (not yet read) | P0 — dashboard will deploy here; may have route/function configs |
| `railway.json` + `railway.toml` | Railway | EXISTS | Backend may run on Railway; dashboard API calls may target Railway URL |
| `Dockerfile` + `Dockerfile.vercel` | Docker | EXISTS | Container deployment option |
| `policies/` | Routing policies | EXISTS (YAML files) | PolicyDrivenRouter loads these; dashboard should display active policy version |
| `slo.yml` | SLO definitions | EXISTS | Could feed into analytics dashboard |
| `capabilities.yaml` | Agent capabilities | EXISTS | Could populate agent directory |
| `api/index.py` | Vercel serverless | EXISTS (single file) | Current API entry point — needs expansion |

---

## 5. API Contract

### 5.1 Chat Request
```typescript
interface ChatRequest {
  message: string;
  session_id?: string;
  provider?: "anthropic" | "openai" | "deepseek" | "ollama";
  model_id?: string;
  mode?: "single_agent" | "multi_agent" | "pipeline" | "parallel";
  search_enabled?: boolean;
  capability_hint?: AgentCapability;
  search_output_mode?: "simple" | "standard" | "detailed" | "technical";
}
```

### 5.2 Chat Response (SSE events)
```
event: token       → { text: string }
event: status      → { agent: string, status: string }
event: routing     → { intent, complexity, capabilities_needed, confidence, reasoning }
event: handoff     → { from_agent, to_agent, step_number, total_steps }
event: search      → { query, sources_used, results_count, confidence_level }
event: debate      → { protocol, rounds, consensus_score, synthesis }
event: artifact    → { type: "code"|"document"|"diff", language, content, filename }
event: final       → { message_id, response, metadata }
event: error       → { code, message }
```

### 5.3 Metadata in Final Response
```typescript
interface ResponseMetadata {
  agent_name: string;
  model_used: string;
  provider: string;
  routing: {
    intent: string;
    complexity: "simple" | "moderate" | "complex" | "very_complex";
    capabilities_needed: AgentCapability[];
    confidence: number;
    reasoning: string;
  };
  search?: {
    query_type: string;
    sources_used: string[];
    confidence_level: string;
    results_count: number;
  };
  debate?: {
    protocol: DebateProtocol;
    rounds: number;
    consensus_score: number;
  };
  learning?: {
    rl_patterns_learned: number;
    corrections_applied: number;
    feedback_score?: number;
  };
  handoffs?: {
    count: number;
    chain: Array<{ from: string; to: string; step: number }>;
  };
  tokens_used: number;
  response_time_ms: number;
}
```

### 5.4 Existing REST Endpoint Contracts (FROM SOURCE — torq_console/api/routes.py)

**These endpoints already exist and work. TypeScript interfaces below match the actual Pydantic models.**

```typescript
// EXISTING: GET /api/agents → AgentInfo[]
interface AgentInfo {
  id: string;              // "prince_flowers" | "orchestrator" | "query_router"
  name: string;            // "Prince Flowers" | "Agent Orchestrator" | "Query Router"
  description: string;
  capabilities: string[];  // e.g. ["general_chat", "code_generation", "task_planning"]
  status: string;          // "active"
  metrics: Record<string, any>;  // from agent.get_metrics()
}

// EXISTING: POST /api/agents/{id}/chat
interface ChatMessage {
  message: string;                    // min_length=1
  context?: Record<string, any>;      // optional
  mode?: "single_agent" | "multi_agent" | "pipeline" | "parallel";  // default: "single_agent"
}
interface ChatResponse {
  response: string;          // Agent response text
  agent_id: string;          // Which agent responded
  timestamp: string;         // ISO timestamp
  metadata: {
    mode: string;
    routing_decision: {
      primary_agent: string;
      capabilities: string[];  // AgentCapability.value strings
    } | null;
    success: boolean;
    [key: string]: any;       // additional metadata from OrchestrationResult
  };
}

// EXISTING: GET /api/status
interface SystemStatus {
  status: string;            // "healthy"
  agents_active: number;     // currently hardcoded to 3
  sessions_active: number;
  uptime_seconds: number;
  metrics: Record<string, any>;  // from orchestrator.get_comprehensive_metrics()
}

// EXISTING: POST /api/sessions
interface CreateSessionRequest {
  agent_id: string;
  metadata?: Record<string, any>;
}
interface SessionInfo {
  session_id: string;
  created_at: string;
  agent_id: string;
  message_count: number;
  status: string;           // "active"
}

// EXISTING: GET /health (on server.py, not routes.py)
interface HealthResponse {
  status: "healthy";
  service: "torq-console-api";
}
```

### 5.5 NEW Endpoints to Add (Phase 1-4)

```typescript
// Phase 1: POST /api/agents/{id}/chat/stream — SSE streaming variant
// Same ChatMessage input, but returns SSE event stream instead of JSON
// See Section 6g for SSE event format

// Phase 1: GET /api/providers — LLM provider listing
interface ProvidersResponse {
  providers: Array<{
    id: string;              // "anthropic" | "openai" | "deepseek" | "ollama" | "glm" | "xai"
    configured: boolean;
    models: Array<{ id: string; name: string }>;
  }>;
}

// Phase 2: POST /api/search — wraps TORQSearchMaster
interface SearchRequest {
  query: string;
  output_mode?: "simple" | "standard" | "detailed" | "technical";
  providers?: string[];
}
interface SearchResponse {
  results: Array<{ title: string; url: string; snippet: string; provider: string; confidence: number }>;
  total_results: number;
}

// Phase 3: GET /api/swarms — reads swarms.json
interface SwarmsResponse {
  swarms: Array<{
    id: string; name: string; tier: 1 | 2 | 3;
    agents: string[]; triggers: string[]; estimated_tokens: number;
  }>;
}

// Phase 4: GET/POST /api/memory — wraps MemoryIntegration
// Phase 4: POST /api/workflows — wraps N8NWorkflowArchitectAgent
```

---

## 6a. Existing Frontend Component Inventory

**22 components already built** across 9 component categories. This significantly reduces Phase 1 frontend work — chat components exist and need enhancement, not creation from scratch.

### Existing Components (modify/extend)

| Path | Component | Status | Phase 1 Action |
|------|-----------|--------|----------------|
| `components/chat/ChatInput.tsx` | Chat input | EXISTS | Extend: add model/mode dropdowns |
| `components/chat/ChatMessage.tsx` | Message display | EXISTS | Extend: add RoutingBadge |
| `components/chat/ChatWindow.tsx` | Chat container | EXISTS | Extend: SSE integration |
| `components/chat/CodeBlock.tsx` | Code blocks | EXISTS | Keep as-is |
| `components/chat/DiffMessage.tsx` | Diff display | EXISTS | Keep as-is |
| `components/command/CommandPalette.tsx` | Ctrl+K palette | EXISTS | Extend in Phase 2 |
| `components/command/CommandItem.tsx` | Palette items | EXISTS | Keep as-is |
| `components/coordination/AgentCard.tsx` | Agent cards | EXISTS | Extend: real metrics |
| `components/coordination/CoordinationPanel.tsx` | Coordination view | EXISTS | Extend: live swarm status |
| `components/coordination/WorkflowGraph.tsx` | Workflow viz | EXISTS | Extend: real handoff data |
| `components/diff/DiffViewer.tsx` | Diff viewer | EXISTS | Keep as-is |
| `components/diff/DiffStats.tsx` | Diff statistics | EXISTS | Keep as-is |
| `components/diff/DiffExample.tsx` | Diff examples | EXISTS | Keep as-is |
| `components/editor/MonacoEditor.tsx` | Monaco editor | EXISTS | Keep as-is (lazy-load) |
| `components/editor/CodeViewer.tsx` | Code viewer | EXISTS | Keep as-is |
| `components/layout/AgentSidebar.tsx` | Agent sidebar | EXISTS | Extend: swarm teams |
| `components/layout/TopNav.tsx` | Top navigation | EXISTS | Extend: provider indicator |
| `components/ui/Badge.tsx` | Badge component | EXISTS | Keep as-is |
| `components/ui/Button.tsx` | Button component | EXISTS | Keep as-is |
| `components/ui/Card.tsx` | Card component | EXISTS | Keep as-is |
| `components/ui/TorqLogo.tsx` | Logo | EXISTS | Keep as-is |
| `hooks/useKeyboardShortcuts.ts` | Keyboard hooks | EXISTS | Keep as-is |

### Existing Services & Stores

| Path | Purpose | Status |
|------|---------|--------|
| `services/api.ts` | HTTP client | EXISTS — verify base URL |
| `services/agentService.ts` | Agent API calls | EXISTS — verify endpoints |
| `services/websocket.ts` | WebSocket client | EXISTS — add SSE fallback |
| `stores/agentStore.ts` | Agent state (Zustand) | EXISTS (224 lines, analyzed) |
| `stores/coordinationStore.ts` | Workflow state (Zustand) | EXISTS (281 lines, analyzed) |
| `lib/types.ts` | TypeScript types | EXISTS — extend with API contract types |

### Components to CREATE (new)

| Component | Phase | Purpose |
|-----------|-------|---------|
| `components/chat/RoutingBadge.tsx` | 1 | Per-message routing transparency |
| `components/chat/StreamingIndicator.tsx` | 1 | SSE connection status |
| `lib/sse.ts` | 1 | SSE client with reconnection |
| `stores/chatStore.ts` | 1 | Chat message state (may extend agentStore) |
| `components/search/SwarmChainProgress.tsx` | 2 | 4-step progress visualization |
| `components/search/SearchResults.tsx` | 2 | Search result cards |
| `pages/AgentsPage.tsx` | 3 | Dual-layer agent directory |
| `pages/SwarmsPage.tsx` | 3 | 14-swarm team directory |
| `pages/AnalyticsPage.tsx` | 3 | Metrics dashboard |
| `components/swarms/SwarmCard.tsx` | 3 | Swarm team card |
| `pages/MemoryPage.tsx` | 4 | Memory management |
| `pages/WorkflowsPage.tsx` | 4 | N8N workflow architect UI |
| `pages/SettingsPage.tsx` | 4 | Provider configuration |

### Placeholder Folders (empty, awaiting implementation)
- `components/agents/` — Phase 3 agent directory components
- `components/code/` — Future code-specific components
- `styles/` — Additional style files
- `types/` — Additional TypeScript type definitions

## 6b. API & Backend Discovery (FROM SOURCE CODE)

### Vercel Entry Point
`api/index.py` imports `from torq_console.ui.railway_app import app` and exposes it as `asgi_app = app`. All Vercel routes (catch-all `/(.*))`) go to this single file.

### Actual FastAPI Application
`torq_console/api/server.py` is the real FastAPI app with:
- CORS configured (allow all origins)
- Socket.IO server integrated via `socketio.ASGIApp` wrapper
- Static file serving from `frontend/dist/` (SPA routing)
- `/health` endpoint
- All `/api/*` routes from `torq_console/api/routes.py`
- Startup/shutdown event hooks initializing SocketIOHandler
- Default port: 8899

### EXISTING API Endpoints (torq_console/api/routes.py)
These endpoints **already work** — Phase 1 extends them, not replaces them:

| Endpoint | Method | Pydantic Models | What It Does |
|----------|--------|-----------------|--------------|
| `/api/agents` | GET | → `list[AgentInfo]` | Lists 3 agents: prince_flowers, orchestrator, query_router |
| `/api/agents/{id}` | GET | → `AgentInfo` | Agent info + live metrics from `.get_metrics()` |
| `/api/agents/{id}/chat` | POST | `ChatMessage` → `ChatResponse` | **THE CHAT ENDPOINT** — routes through `orchestrator.process_query()` |
| `/api/sessions` | GET | → `list[SessionInfo]` | Lists all active sessions |
| `/api/sessions` | POST | `CreateSessionRequest` → `SessionInfo` | Creates new session |
| `/api/sessions/{id}` | GET | → `SessionInfo` | Gets session details |
| `/api/status` | GET | → `SystemStatus` | System health + `orchestrator.get_comprehensive_metrics()` |
| `/health` | GET | → `dict` | `{"status": "healthy"}` |

### Existing Pydantic Models (routes.py)
```python
class ChatMessage(BaseModel):
    message: str                    # User message (min_length=1)
    context: Optional[dict] = None  # Optional context
    mode: Optional[str] = "single_agent"  # single_agent|multi_agent|pipeline|parallel

class ChatResponse(BaseModel):
    response: str          # Agent response text
    agent_id: str          # Which agent responded
    timestamp: str         # ISO timestamp
    metadata: dict = {}    # routing_decision, success, etc.

class AgentInfo(BaseModel):
    id: str
    name: str
    description: str
    capabilities: list[str]
    status: str = "active"
    metrics: dict = {}

class SystemStatus(BaseModel):
    status: str
    agents_active: int
    sessions_active: int
    uptime_seconds: float
    metrics: dict = {}
```

### Orchestrator Call Chain (VERIFIED)
```python
# In routes.py AgentManager.process_chat():
result = await self.orchestrator.process_query(
    message,                    # str
    context=context,            # Optional[dict]
    mode=OrchestrationMode.SINGLE_AGENT  # enum
)
# result.primary_response → str
# result.routing_decision.primary_agent → str
# result.routing_decision.capabilities_needed → list[AgentCapability]
# result.success → bool
# result.metadata → dict
```

### AgentManager (Singleton in routes.py)
Already instantiates on import:
```python
agent_manager = AgentManager()  # creates orchestrator, router, prince_flowers
```

### Full torq_console/ Package Structure (~200+ Python files)
```
torq_console/
├── __init__.py, __main__.py, cli.py, startup_simple.py
├── agents/              ← 44 files (PRD Section 2.1) + subpackages:
│   ├── core/            ← 8 files: base_agent, capabilities, interfaces, registry, etc.
│   ├── pae/             ← 4 files: Plan-Act-Evaluate orchestrator
│   ├── rl_modules/      ← 4 files: async_training, dynamic_actions, modular_agent
│   ├── tools/           ← 18 files: browser, code_gen, file_ops, image_gen, mcp, n8n, terminal, etc.
│   └── torq_prince_flowers/ ← 15 files (verified above)
├── api/                 ← 5 files: server.py, routes.py, socketio_handler.py, crypto_price.py
├── benchmarking/        ← 8 files: runner, reporting, SLO config, storage
├── core/                ← 8 files + evaluation/ + telemetry/ subpackages
├── dashboard/           ← 4 files: collector, dashboard, exporter
├── indexer/             ← 5 files: code_scanner, embeddings, semantic_search, vector_store
├── integrations/        ← 8 files: github, huggingface, n8n, perplexity, image/video gen
├── llm/                 ← 3 files + providers/ (20+ files: claude, deepseek, ollama, glm, websearch, content_synthesis/, export/, search_plugins/)
├── marvin_integration/  ← 4 files: agents, core, models
├── mcp/                 ← 7 files: claude_code_bridge, client, enhanced_client, mcp_manager
├── memory/              ← 2 files: letta_integration
├── orchestration/       ← agents/, flows/, tasks/ subpackages
├── plugins/             ← 5 files + builtin/
├── pwa/                 ← 4 files: manifest, service_worker
├── reasoning/           ← 5 files: core, enhancers, templates, validator
├── safety/              ← 9 files: audit_logger, rate_limiter, sandbox, security, policy_engine
├── spec_kit/            ← 11 files: adaptive_intelligence, ecosystem_intelligence, etc.
├── swarm/               ← 7 files + agents/ (9 swarm agent files)
├── ui/                  ← 13 files: web.py, railway_app.py, shell.py, command_palette.py
└── utils/               ← 14 files: web_search, ai_integration, app_builder, git_manager
```

**This package is the primary agent** that `api/index.py` wraps for the dashboard.

## 6c. Implementation Phases

### Phase 0: Discovery — COMPLETED

All discovery questions answered from source code:

| Question | Answer |
|----------|--------|
| Framework? | **FastAPI** with Socket.IO (ASGI) |
| Entry point? | `api/index.py` → `torq_console.ui.railway_app` → **WebUI.app** (NOT server.py!) |
| Import paths? | `from torq_console.agents.marvin_orchestrator import MarvinAgentOrchestrator, get_orchestrator` |
| process_query()? | `async process_query(query: str, context: dict?, mode: OrchestrationMode) → OrchestrationResult` |
| Streaming? | **NO** — returns complete response string, not async generator |
| Deployment? | Same-origin Vercel, catch-all to api/index.py |
| Default model? | `anthropic/claude-sonnet-4-20250514` (via `get_orchestrator()` singleton) |

**⚠ CRITICAL FINDING: Two different FastAPI apps exist**

| App | File | Used By | Chat Endpoint |
|-----|------|---------|---------------|
| **WebUI.app** | `torq_console.ui.web.WebUI` | **Vercel + Railway** (via railway_app.py) | `/api/chat` |
| **server.py** | `torq_console.api.server` | **Local dev** only | `/api/agents/{id}/chat` |

`railway_app.py` creates `WebUI(console=TorqConsole(config=TorqConfig()))` and exposes `web_ui.app`. It does **NOT** import routes from `torq_console/api/routes.py`. The 7 REST endpoints (GET /api/agents, POST /api/agents/{id}/chat, etc.) documented in this PRD are only available when running `server.py` locally — they may **not** be available on Vercel.

**Phase 1 must resolve this by either:**
1. **Preferred:** Modify `railway_app.py` to include: `from torq_console.api.routes import router; web_ui.app.include_router(router, prefix="/api")`
2. **Or:** Change `api/index.py` to import from `torq_console.api.server` instead of `railway_app`
3. **Or:** Build frontend against WebUI's own `/api/chat` endpoint

**⚠ STREAMING NOT AVAILABLE**

`process_query()` calls `prince_flowers.chat(query, context)` which returns a complete `str`. There is no `yield`, no `AsyncIterator`, no token-by-token streaming anywhere in the call chain.

**SSE strategy for Phase 1:**
- **Phase 1a (immediate):** Non-streaming — use existing endpoints, show loading spinner, display complete response
- **Phase 1b (follow-up):** "Fake SSE" — emit `routing` event immediately (from RoutingDecision), then emit `final` event with complete response after process_query() returns
- **Phase 2+:** True token streaming — requires modifying the LLM provider layer to use streaming API calls (Anthropic and OpenAI both support `stream=True`)

**Remaining discovery (1 file):**
1. Read `torq_console/ui/web.py` — verify what routes WebUI.app exposes and whether it includes `/api/chat`

---

## 6d. Backend Call Chain (VERIFIED FROM SOURCE CODE)

**Two app paths exist — must be unified in Phase 1:**

```
PATH A — Vercel/Railway (current):
  api/index.py → railway_app.py → WebUI(TorqConsole(TorqConfig())).app
    └─► /api/chat (WebUI's own endpoint — needs verification)
    └─► /health (added by railway_app.py)

PATH B — Local dev (server.py):
  torq_console.api.server → FastAPI app + Socket.IO
    └─► /api/agents          GET    (list agents)
    └─► /api/agents/{id}     GET    (agent info + metrics)
    └─► /api/agents/{id}/chat POST  (chat via orchestrator)
    └─► /api/sessions         GET/POST
    └─► /api/status           GET    (system metrics)
    └─► /health               GET
    └─► /socket.io            WebSocket
    └─► /*                    SPA (frontend/dist)
```

**Phase 1 unifies these** by adding routes.py endpoints to WebUI.app.

**Orchestrator call chain (both paths use this):**
```
AgentManager.process_chat(agent_id, message, context, mode)
  └─► orchestrator.process_query(message, context, OrchestrationMode)
        ├─► router.route_query(query, context) → RoutingDecision
        │     Returns: primary_agent, capabilities_needed, confidence
        │
        ├─► SINGLE_AGENT mode:
        │     if needs_search → TorqPrinceFlowers.process_query(query) [with tools]
        │     else           → MarvinPrinceFlowers.chat(query, context) [conversational]
        │
        └─► Returns OrchestrationResult:
              .primary_response: str (complete response, NOT streaming)
              .routing_decision: RoutingDecision
              .success: bool
              .metadata: dict (agent_used, capabilities, used_tools)
```

---

## 6e. Deployment Architecture (VERIFIED)

**Current setup (from vercel.json + api/index.py + server.py):**

```
Vercel (Production):
  api/index.py ──imports──► torq_console.ui.railway_app ──► FastAPI ASGI app
  vercel.json:
    - Catch-all route: /(.*) → api/index.py
    - Build: pip install fastapi uvicorn pydantic anthropic openai ...
    - Runtime: @vercel/python (Python 3.11)
    - No maxDuration set (default 10s Hobby / 60s Pro)
  
  FastAPI app (server.py):
    - CORS: allow all origins
    - Routes: /api/* from routes.py
    - Socket.IO: /socket.io via socketio.ASGIApp wrapper
    - Static: frontend/dist/ served as SPA
    - Health: GET /health
    - Docs: /api/docs (Swagger), /api/redoc

Local development (start_web.py):
  python -u torq_console --web → uvicorn on 127.0.0.1:8899
```

**SSE streaming consideration:** Vercel's default 10s timeout will kill SSE streams. Options:
1. Add `"functions": { "api/index.py": { "maxDuration": 60 } }` to vercel.json (Pro plan)
2. Use Vercel Edge Runtime (no timeout for streaming)
3. Keep SSE on Railway backend only; Vercel serves frontend + non-streaming API

**Recommendation:** Start with option 1 for Phase 1. If timeout is insufficient, migrate streaming endpoint to Railway.

---

## 6f. Environment Variables (FROM .env.example)

```bash
# === Phase 1 (Core LLM) ===
ANTHROPIC_API_KEY=          # Primary LLM provider
OPENAI_API_KEY=             # Secondary provider
DEEPSEEK_API_KEY=           # DeepSeek provider
XAI_API_KEY=                # X.AI/Grok provider
XAI_MODEL=grok-beta         # Grok model name
XAI_API_BASE_URL=https://api.x.ai/v1

# === Phase 2 (Search) ===
BRAVE_SEARCH_API_KEY=       # Brave search (2,000 free/month)
GOOGLE_SEARCH_API_KEY=      # Google Custom Search
GOOGLE_SEARCH_ENGINE_ID=    # Google CSE ID
NEWS_API_KEY=               # News API

# === Phase 3 (Financial/Data) ===
ALPHA_VANTAGE_API_KEY=      # Financial data
FRED_API_KEY=               # Federal Reserve data

# === Phase 4 (Integrations) ===
TWITTER_API_KEY=            # Twitter/X posting
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
TWITTER_BEARER_TOKEN=

# === Service Config ===
ENVIRONMENT=development     # development | production
DEBUG_MODE=true
LOG_LEVEL=INFO
MCP_SERVER_PORT=3100
RATE_LIMITING_ENABLED=true
MAX_REQUESTS_PER_MINUTE=60

# === GPU/Local LLM (optional) ===
LLAMA_CPP_MODEL_PATH=       # Local GGUF model path
LLAMA_CPP_N_GPU_LAYERS=28
LLAMA_CPP_N_CTX=2048

# === Vercel Production Overrides ===
TORQ_CONSOLE_PRODUCTION=true
TORQ_DISABLE_LOCAL_LLM=true
TORQ_DISABLE_GPU=true
```

**⚠ SECURITY ALERT:** `vercel.json` currently has real Anthropic and OpenAI API keys hardcoded in the `env` block. These should be moved to Vercel Environment Variables (dashboard settings) and the keys in vercel.json should be rotated immediately.

**Not in .env.example but used in code:** TAVILY_API_KEY (torq_search_master.py), PERPLEXITY_API_KEY (integrations/perplexity_search.py), SUPABASE_URL/SUPABASE_KEY (memory_integration.py), COINGECKO_API_KEY (api/crypto_price.py).

---

## 6g. SSE Event Format Specification

All SSE events use standard format with JSON data:

```
event: routing
data: {"intent":"web_search","complexity":"moderate","capabilities_needed":["web_search","research"],"confidence":0.87,"reasoning":"Query asks about current events"}
id: msg-abc123-routing

event: token
data: {"text":"Based on my "}
id: msg-abc123-tok-1

event: handoff
data: {"from_agent":"search_agent","to_agent":"analysis_agent","step_number":2,"total_steps":4}
id: msg-abc123-handoff-2

event: final
data: {"message_id":"msg-abc123","response":"Based on my research...","metadata":{...}}
id: msg-abc123-final

```

**Client-side parsing pattern (lib/sse.ts):**
```typescript
const evtSource = new EventSource('/api/stream?session_id=xxx');
evtSource.addEventListener('token', (e) => {
  const { text } = JSON.parse(e.data);
  appendToMessage(text);
});
evtSource.addEventListener('routing', (e) => {
  setRoutingBadge(JSON.parse(e.data));
});
evtSource.addEventListener('final', (e) => {
  const { response, metadata } = JSON.parse(e.data);
  finalizeMessage(response, metadata);
  evtSource.close();
});
// Reconnect with exponential backoff: 1s, 2s, 4s, 8s, max 30s
```

Note: SSE uses GET by default. For POST with message body, use `fetch()` with `ReadableStream` instead of `EventSource`. The implementer must decide based on the backend framework.

---

## 6h. UI Layout Specifications

**Phase 1 Layout:**
```
┌───────────────────────────────────────────────────┐
│ TopNav: [TORQ Logo]  [StreamingDot]  [Settings ⚙] │
├──────────┬────────────────────────────────────────┤
│          │                                        │
│  Agent   │  ChatWindow                            │
│  Sidebar │    ┌──────────────────────────────┐    │
│          │    │ User: "search for AI news"   │    │
│ ┌──────┐ │    └──────────────────────────────┘    │
│ │Model▾│ │    ┌──────────────────────────────┐    │
│ └──────┘ │    │ Assistant: "Here are the..." │    │
│ ┌──────┐ │    │ ┌─RoutingBadge (collapsed)─┐ │    │
│ │Mode ▾│ │    │ │ ▸ prince_flowers │ 0.87   │ │    │
│ └──────┘ │    │ └──────────────────────────┘ │    │
│          │    └──────────────────────────────┘    │
│ Sessions │    ┌──────────────────────────────┐    │
│  • Chat 1│    │ [Type message...       Send] │    │
│  • Chat 2│    └──────────────────────────────┘    │
└──────────┴────────────────────────────────────────┘
```

**RoutingBadge:** Below each assistant message. Collapsed: `[▸ agent_name │ confidence]`. Expanded: shows intent, complexity, capabilities, reasoning, model, tokens, response_time_ms.

**Model/Mode selectors:** In AgentSidebar, above session list. Compact dropdowns.

**Phase 2:** SwarmChainProgress bar appears above ChatWindow when active. SearchResults render inline as collapsible cards.

**Phase 3:** TopNav gains tabs: Chat │ Agents │ Swarms │ Analytics — each loads a full-page view via react-router.

---

## 6i. State Management Recommendation

**Extend `agentStore.ts`** rather than creating a separate chatStore. The existing store already has agents, sessions, messages, and WebSocket management. Add SSE connection state and routing metadata to it. If the store exceeds ~400 lines, then extract a chatStore.

---

### Phase 1: Chat + Routing Transparency (Foundation)

**Prerequisite:** Phase 0 Discovery complete (see above). Verify `railway_app.py` includes routes.

**What ALREADY EXISTS (no work needed):**
- FastAPI app with CORS (`torq_console/api/server.py`)
- Chat endpoint: `POST /api/agents/{id}/chat` with orchestrator routing
- Agent listing: `GET /api/agents` returning 3 agents with metrics
- System status: `GET /api/status` with comprehensive metrics
- Sessions CRUD: `GET/POST /api/sessions`
- Health check: `GET /health`
- Socket.IO integration for WebSocket
- AgentManager singleton with orchestrator, router, prince_flowers

**Backend work (EXTEND existing routes.py):**

**Step 0 — Unify the FastAPI apps (PREREQUISITE):**
- Modify `torq_console/ui/railway_app.py` to include routes.py endpoints:
  ```python
  from torq_console.api.routes import router
  web_ui.app.include_router(router, prefix="/api")
  ```
- This makes GET /api/agents, POST /api/agents/{id}/chat, GET /api/status available on Vercel
- Test locally to verify no route conflicts with WebUI's existing routes

**Step 1a — Connect frontend to existing (non-streaming) chat:**
- Use `POST /api/agents/prince_flowers/chat` — it already works
- Frontend sends `{ message, mode }` and receives `{ response, metadata }`
- Display complete response after loading (no streaming yet)
- Show routing metadata from `metadata.routing_decision`

**Step 1b — Add "fake SSE" endpoint (optional, improves UX):**
- Add `POST /api/agents/{id}/chat/stream` to `torq_console/api/routes.py`
- Calls `router.route_query()` first → emits `routing` SSE event immediately
- Then calls `orchestrator.process_query()` → emits `final` SSE event with complete response
- This gives the user instant feedback (routing info) while waiting for the LLM

**Step 2 — Add provider listing endpoint:**
- Add `GET /api/providers` to routes.py
- Import from `torq_console.llm.manager` to list configured providers
- Return provider IDs, configured status, available models

**Step 3 — Add routing log endpoint:**
- Add `GET /api/routing/history` to routes.py
- Expose `router.routing_history` from MarvinQueryRouter

**Frontend work:**

**Step 4 — SSE client:**
- Create `lib/sse.ts` — SSE client with reconnection (see Section 6g)
- Extend `stores/agentStore.ts` — add SSE state, routing metadata

**Step 5 — Chat integration:**
- EXTEND `components/chat/ChatWindow.tsx` — add SSE streaming option alongside existing WebSocket
- EXTEND `services/api.ts` — add SSE endpoint URL + provider/routing endpoints

**Step 6 — Routing transparency:**
- CREATE `components/chat/RoutingBadge.tsx` — collapsible per-message badge (see Section 6h)
- CREATE `components/chat/StreamingIndicator.tsx` — pulsing dot in TopNav
- EXTEND `components/chat/ChatMessage.tsx` — render RoutingBadge below assistant messages

**Step 7 — Sidebar selectors:**
- EXTEND `components/layout/AgentSidebar.tsx` — add model dropdown and mode dropdown
- EXTEND `components/layout/TopNav.tsx` — add provider status indicator

**UI shows:** Chat input, model/mode selection, streaming tokens, RoutingBadge per response (agent, model, confidence, intent, complexity, reasoning), session list

**UI does NOT show:** Swarm team selector, Claude Code agent selector (not backend-connected), token budget meter, pipeline/parallel progress visualization

**Success criteria:** 50 messages without crash, SSE streaming <3s first token, routing data matches backend QueryAnalysis, 0 TypeScript errors, Lighthouse ≥85

### Phase 2: Search + Swarm Chain Visibility

**Backend work:**
- SSE handoff events in SwarmOrchestrator
- POST /api/search endpoint wrapping TORQSearchMaster.search()
- Search output mode selection (simple/standard/detailed/technical)

**Frontend work:**
- `components/search/SwarmChainProgress.tsx` — 4-step progress (Search→Analysis→Synthesis→Response)
- `components/search/SearchResults.tsx` — Formatted search results
- `components/chat/CommandPalette.tsx` — EXTEND: add search commands to existing palette

**UI shows:** Search toggle, swarm chain progress bar, handoff counter (X/10), elapsed time, search result cards with confidence levels, output mode selector

**Success criteria:** Search returns results from ≥2 providers, swarm chain progress updates in real-time, handoff events match backend SwarmOrchestrator step count, output mode selector changes result formatting

### Phase 3: Analytics + Agent & Swarm Directory

**Prerequisites:**
- Install `react-router-dom` — frontend currently has no routing/pages infrastructure; all pages/* components require router setup in App.tsx

**Backend work:**
- GET /api/metrics wrapping get_comprehensive_metrics()
- GET /api/agents/registry — both Python agents and Claude Code agent definitions
- GET /api/swarms — reads swarms.json, returns 14 swarm team compositions with agent details
- Cost estimation endpoints

**Frontend work:**
- Install recharts
- `pages/AgentsPage.tsx` — Dual-layer agent directory (Python runtime + Claude Code definitions)
- `pages/SwarmsPage.tsx` — 14 swarm teams, grouped by tier, showing agent composition, trigger words, token budgets
- `pages/AnalyticsPage.tsx` — Real metrics from backend
- `components/analytics/MetricCards.tsx`
- `components/agents/AgentCard.tsx` — Shows capabilities, status, metrics
- `components/swarms/SwarmCard.tsx` — Shows tier badge, agent list, trigger keywords, estimated tokens

**Success criteria:** Agent directory displays both Python (38) and Claude Code (~47) agents, swarm directory shows all 14 swarms grouped by tier, analytics page renders real metrics from GET /api/metrics, react-router navigation works across all pages without full-page reload

### Phase 4: Memory + N8N + Polish

**Backend work:**
- REST endpoints wrapping MemoryIntegration
- REST endpoints wrapping N8NWorkflowArchitectAgent
- Export endpoints for conversation history

**Frontend work:**
- `pages/MemoryPage.tsx` — Memory search and management
- `pages/WorkflowsPage.tsx` — N8N workflow architect UI (3-phase: requirements→blueprint→JSON)
- `pages/SettingsPage.tsx` — Provider configuration, preferences

**Success criteria:** Memory search returns results from Supabase (or degrades gracefully), N8N workflow architect generates valid workflow JSON in 3 phases, settings page persists provider/preference changes

---

## 7. Verified Swarm Configuration (swarms.json)

**14 swarms** (not 13 as originally estimated) organized across 3 tiers, referencing 38 unique Claude Code agents. These swarms define team compositions for Claude Code — they are NOT connected to the Python backend orchestrator.

### 7.1 Tier 1 — Fast Execution (4 swarms)

| Swarm ID | Name | Agents | Token Budget | Triggers |
|----------|------|--------|-------------|----------|
| `rapid-feature` (DEFAULT) | Rapid Feature Development | fullstack-orchestrator, backend-engineer, frontend-architect, expert-software-engineer, code-reviewer | 25,000 | "add feature", "implement", "build new" |
| `bug-fixing` | Bug Fixing & Optimization | expert-software-engineer, code-reviewer, performance-engineer, database-specialist | 22,000 | "fix bug", "optimize", "debug", "error" |
| `quick-updates` | Quick Updates & Refactoring | expert-software-engineer, code-reviewer, python-expert | 15,000 | "refactor", "clean up", "small change" |
| `backend-systems` | Backend Systems & APIs | backend-engineer, database-specialist, cybersecurity-expert, api-integration-agent | 35,000 | "backend api", "database design", "microservice" |

### 7.2 Tier 2 — Full Projects (7 swarms)

| Swarm ID | Name | Agents | Token Budget | Triggers |
|----------|------|--------|-------------|----------|
| `full-stack-web` | Full-Stack Web Development | fullstack-orchestrator, backend-engineer, expert-software-engineer, frontend-architect, n8n-backend-developer, database-specialist, deployment-expert | 50,000 | "web application", "full-stack", "saas" |
| `data-science` | Data Science & Analysis | data-scientist, data-researcher, quant-analyst, python-expert | 45,000 | "analyze data", "machine learning", "ML model" |
| `security-compliance` | Security & Compliance | cybersecurity-expert, cybersecurity-strategist, credential-security-agent, risk-manager | 48,000 | "security", "vulnerability", "compliance", "audit" |
| `fintech-trading` | Fintech & Trading | trading-bot-specialist, fintech-engineer, quant-analyst, risk-manager | 46,000 | "trading", "fintech", "portfolio", "market analysis" |
| `content-marketing` | Content & Marketing Tech | content-intelligence-agent, viral-content-strategist, market-researcher, tbs-website-specialist | 44,000 | "content", "marketing", "seo", "viral" |
| `meta-orchestration` | Meta Orchestration & Planning | meta-agent, fullstack-orchestrator, expert-software-engineer, project-analyzer-agent, workflow-architect-agent | 48,000 | "complex project", "orchestrate", "plan project" |
| `pdf-ai-complete` | PDF AI Complete Project | pdf-ai-content-strategist, pdf-ai-uiux-designer, pdf-ai-component-developer, pdf-ai-integration-specialist, pdf-ai-quality-assurance | 52,000 | "pdf ai project" |

### 7.3 Tier 3 — Specialist Operations (3 swarms)

| Swarm ID | Name | Agents | Token Budget | Triggers |
|----------|------|--------|-------------|----------|
| `devops-deployment` | DevOps & Deployment | backend-engineer, deployment-orchestrator-agent, system-administrator-expert, performance-monitor | 28,000 | "deploy", "ci/cd", "docker", "kubernetes" |
| `api-integration` | Integration & APIs | backend-engineer, api-integration-agent, n8n-workflow-expert, workflow-architect-agent | 26,000 | "api", "integrate", "webhook", "automation" |
| `browser-automation` | Browser Automation | browser-automation-specialist, workflow-testing-agent | 20,000 | "scrape", "automate browser", "e2e test" |

### 7.4 Swarm Rules
```json
{
  "max_concurrent_swarms": 2,
  "auto_expand": true,
  "context_sharing": "summary_only",
  "fallback_swarm": "rapid-feature"
}
```

### 7.5 Dynamic Expansion Rules
When complexity exceeds 0.7, the system can auto-add specialist agents from a pool: cybersecurity-expert, performance-engineer, database-specialist, deployment-expert. Triggers include "security concerns detected", "performance bottleneck found", "database design needed", "deployment required".

### 7.6 Missing Agent Reference
`api-integration-agent.md` is referenced in 2 swarms but was not found in the uploaded agent files. This agent definition needs to be created, or the swarms need to reference an existing agent.

### 7.7 Dashboard Implications
Because swarms.json references Claude Code agents (not Python backend agents), a swarm team selector in the dashboard would need to:
1. Read swarms.json to populate the dropdown
2. Display team composition with agent descriptions
3. Send the swarm_id with chat requests
4. BUT the Python backend has no swarm routing by team — it would pass through to Claude Code, or a bridge API would need to be built

**Recommendation:** Phase 3 can include a read-only "Swarm Directory" showing team compositions. Active swarm routing requires either a Claude Code CLI bridge or backend refactoring to load swarm configs.

---

## 8. Deliberately Excluded (Require Significant Backend Work)

1. **Active swarm team routing** — swarms.json defines Claude Code teams, but Python backend has no `swarm_id` routing. Requires bridge API.
2. **53-agent selection UI** — Claude Code agents are NOT loaded by Python backend. Would require a bridge API that reads `E:\.claude\agents\` and invokes Claude Code CLI.
3. **Per-agent token budget meters** — No budget tracking system exists. swarms.json has `estimated_tokens` per swarm but no runtime enforcement.
4. **Real pipeline visualization** — MarvinAgentOrchestrator._execute_pipeline() is a stub.
5. **Custom pipeline builder** — No pipeline configuration system.
6. **Semantic code search** — pgvector search requires Supabase env vars.
7. **Debate visualization** — Multi-agent debate results are internal; no SSE events for debate rounds.
8. **RL learning dashboard** — ARTISTRLSystem operates internally; no HTTP API surface.

---

## 9. Color Theme

```typescript
const TORQ_THEME = {
  bg: "#0f1220",
  panel: "#151a2e",
  card: "#1b2140",
  surface: "#212845",
  border: "rgba(141,153,174,0.22)",
  text: "#edf2f4",
  muted: "rgba(237,242,244,0.72)",
  accent: "#ef233c",
  accent2: "#d90429",
  success: "#10b981",
  warning: "#f59e0b",
  error: "#ef4444",
  info: "#3b82f6",
  fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  fontMono: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
};
```

---

## 10. Success Metrics

| Metric | Target |
|--------|--------|
| First token latency | <3s |
| SSE stability | 0 disconnects per 50 messages |
| Routing accuracy | 100% match to backend QueryAnalysis |
| TypeScript errors | 0 |
| Bundle size | <400KB gzipped |
| Lighthouse | ≥85 |
| Enum correctness | 100% match to Python enums |

---

## 11. Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| **railway_app.py uses WebUI.app, NOT server.py routes** | **HIGH** | **Phase 1 Step 0: Add `include_router(router, prefix="/api")` to railway_app.py** |
| SSE on Vercel 10s/60s timeout | HIGH | Add `maxDuration: 60` to vercel.json; fall back to Railway for streaming if needed |
| **process_query() has no streaming support** | **HIGH** | **Phase 1a: non-streaming first; Phase 1b: fake SSE (routing event + final event); Phase 2+: true token streaming** |
| Backend pipeline/parallel modes are stubs | HIGH | UI shows "experimental" label; only single_agent and multi_agent are production-ready |
| **API keys hardcoded in vercel.json** | **CRITICAL** | **Rotate Anthropic + OpenAI keys immediately; move to Vercel env vars dashboard** |
| Socket.IO→SSE migration complexity | MEDIUM | Keep Socket.IO as fallback; SSE is additive, not a replacement |
| Claude Code agents not backend-connected | MEDIUM | Show as "Directory" view; mcp/claude_code_bridge.py may enable future integration |
| Swarm team routing not in Python backend | MEDIUM | Show swarms.json as read-only directory; active routing deferred |
| api/index.py imports railway_app not server.py | MEDIUM | Verify railway_app.py includes same routes; may need to update import |
| 1 missing agent ref (api-integration-agent) | LOW | Create agent definition or update swarms.json reference |
| Monaco editor bundle size | MEDIUM | Lazy-load on code blocks |
| Supabase memory requires env vars not in .env.example | LOW | Add SUPABASE_URL/KEY to .env.example; degrade gracefully |
| AgentManager hardcodes 3 agents | LOW | Extend agents_map dict when adding new agents to the API |
| vercel.json buildCommand doesn't install all deps | MEDIUM | Missing: sentence-transformers, zep-python, supabase; add to requirements-vercel.txt |

---

## 12. Appendix: File Counts Summary

| Category | Count | Notes |
|----------|-------|-------|
| **torq_console/ Python files (full package)** | **~200+** | **20+ subpackages — see Section 6b for full tree** |
| ├── agents/ (uploaded, content-analyzed) | 44 | Includes core/, pae/, rl_modules/ subfolders |
| ├── agents/tools/ | 18 | Tool implementations for IntentDetector routing |
| ├── agents/torq_prince_flowers/ | 15 | Primary agent package (fully verified) |
| ├── api/ | 5 | FastAPI server, routes, Socket.IO handler |
| ├── llm/ + providers/ | 20+ | LLM manager, 7 providers, content_synthesis, export, search_plugins |
| ├── swarm/ + agents/ | 16 | Orchestrators + 9 swarm agents |
| ├── safety/ | 9 | Rate limiting, sandbox, audit, security |
| ├── ui/ | 13 | Web, CLI, railway_app, terminal UI |
| └── Other subpackages | ~60 | benchmarking, core, dashboard, indexer, integrations, mcp, memory, orchestration, plugins, pwa, reasoning, spec_kit, utils |
| Claude Code agent .md files | 51 | ~16,000+ lines |
| Claude Code agent .json files | 4 | ~800+ lines |
| Swarm configuration (swarms.json) | 1 | 14 swarms, 38 unique agents |
| Frontend components (.tsx/.ts) | 22 | + 6 service/store/hooks files |
| Root-level Python files | ~50+ | Tests, demos, scripts, integration files |
| Config files | 8 | vercel.json, railway.json, Dockerfile, etc. |
| **Total source files** | **~400+** | Previous estimate of 110 was based on partial analysis |
