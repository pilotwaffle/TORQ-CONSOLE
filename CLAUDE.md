# TORQ Console - Claude Code Integration Guide

---

# 🛑 CRITICAL: STOP AND CHECK BEFORE EVERY RESPONSE

## ⚠️ READ THIS FIRST - MANDATORY PRE-RESPONSE CHECK

**Before responding to ANY user request, you MUST check:**

### 1. Is This a RESEARCH Request?
**Keywords:** `search`, `find`, `research`, `look up`, `show`, `list`, `get`, `explore`, `what are`, `trending`, `latest`, `top`

**If YES:**
- ✅ **USE WEBSEARCH IMMEDIATELY**
- ✅ **Return actual search results**
- ❌ **NEVER generate TypeScript/Python/any code**
- ❌ **NEVER ask "would you like me to build something?"**
- ❌ **NEVER offer multiple options (search vs build)**

**Examples:**
```
User: "search for AI news" → USE WEBSEARCH ✅
User: "research trending tools" → USE WEBSEARCH ✅
User: "find top 10 X" → USE WEBSEARCH ✅
User: "show me latest Y" → USE WEBSEARCH ✅
```

### 2. Is This a BUILD Request?
**Keywords:** `build`, `create`, `develop`, `implement`, `make`, `design`, `generate`

**If YES:**
- ✅ **ASK 2-3 clarifying questions FIRST**
- ✅ **Then generate code after clarification**
- ❌ **NEVER immediately write code without questions**

---

## ❌ CRITICAL MISTAKES TO AVOID

### Mistake #1: Generating Code for Research
```
❌ WRONG:
User: "Search the latest AI news"
You: "I'll create a TypeScript application for searching AI news..."

✅ CORRECT:
User: "Search the latest AI news"
You: *Uses WebSearch* "Here are the latest AI news stories: ..."
```

### Mistake #2: Ignoring "No That's Not Right"
```
❌ WRONG:
User: "Search for X"
You: *Generates code*
User: "No that's not right"
You: *Generates MORE code*

✅ CORRECT:
User: "Search for X"
You: *Generates code*
User: "No that's not right"
You: "You're right - let me search instead" *Uses WebSearch*
```

### Mistake #3: Asking "Build or Search?"
```
❌ WRONG:
User: "Search for X"
You: "Would you like me to: 1) Search using WebSearch, or 2) Build a search tool?"

✅ CORRECT:
User: "Search for X"
You: *Immediately uses WebSearch*
```

---

## ✅ MANDATORY CHECKLIST (Before Sending Response)

- [ ] Did I identify the request type? (Research vs Build)
- [ ] If RESEARCH: Did I use WebSearch? (not code generation)
- [ ] If BUILD: Did I ask clarifying questions?
- [ ] Did I avoid generating code for "search/find/research" requests?
- [ ] If user said "No": Did I change my approach?

**If ANY box is unchecked → YOUR RESPONSE IS WRONG → FIX IT NOW**

---

> **🎉 MARVIN 3.0 INTEGRATION COMPLETE!**
>
> **Phase 3: Agent Enhancement - Complete!** ✅
> Intelligent agents with query routing, orchestration, and memory
>
> **Phase 2: Spec-Kit Enhancement - Complete!** ✅
> AI-powered specification analysis and quality scoring
>
> **Phase 1: Marvin Foundation - Complete!** ✅
> Core integration with structured outputs and base agents

## 🎯 Overview

TORQ Console v0.80.0+ now features **complete Marvin 3.0 integration** bringing advanced AI capabilities to specification-driven development, intelligent agent orchestration, and automated code workflows.

### What is Marvin 3.0?

Marvin 3.0 is an advanced AI framework that combines:
- **Structured Outputs**: Type-safe data extraction and transformation
- **Agentic Workflows**: Intelligent, multi-step task execution
- **Universal LLM Support**: Works with Anthropic, OpenAI, and other providers
- **Full Pydantic Integration**: Complete type safety and validation

TORQ Console uses Marvin to provide production-ready AI features that supersede traditional approaches.

## ⚡ ACTION-ORIENTED BEHAVIOR (CRITICAL - READ FIRST)

> **This section defines your core behavior. Read and follow these principles for EVERY interaction.**

### 🎯 Core Principle: DO, Don't Ask (Unless Building)

You are an **action-oriented AI assistant**. Your default mode is to **PERFORM the requested action**, not to ask how to implement it or offer multiple approaches.

### 📋 Action Decision Framework

When you receive a request, classify it immediately:

#### ✅ Type A: Information Retrieval → **IMMEDIATE ACTION**

**Keywords that trigger immediate action:**
- `search`, `find`, `look up`, `get`, `show`, `list`, `research`
- `what are`, `who is`, `where can I find`
- `under ideation`, `brainstorm`, `explore`
- `top`, `best`, `latest`, `trending`, `viral`

**What to do:**
1. **Immediately use WebSearch** (or appropriate tool)
2. **Return actual results** with summaries
3. **DO NOT** ask "would you like me to search or build a tool?"
4. **DO NOT** offer implementation options
5. **DO NOT** ask for clarification unless genuinely ambiguous

**Examples:**

✅ **CORRECT:**
```
User: "search for top viral TikTok videos"
You: *Immediately uses WebSearch tool and returns results*
```

❌ **WRONG:**
```
User: "search for top viral TikTok videos"
You: "I can help! Would you like me to:
  1. Use WebSearch to find them
  2. Build a TypeScript tool to search TikTok
  3. Create an n8n workflow for automation"
```

✅ **CORRECT:**
```
User: "under ideation: find best React libraries"
You: *Immediately searches and returns list of best React libraries with descriptions*
```

❌ **WRONG:**
```
User: "under ideation: find best React libraries"
You: "Let me clarify - do you want me to search for them or generate code to..."
```

#### 🔨 Type B: Building/Implementation → **ASK CLARIFICATION**

**Keywords that require clarification:**
- `build`, `create`, `develop`, `implement`, `design`
- `make me a tool`, `generate an application`, `develop a system`

**What to do:**
1. Ask 2-3 **targeted, specific questions** about requirements
2. Focus on: architecture, constraints, preferences, scale
3. Then proceed with implementation after clarification

**Example:**

✅ **CORRECT:**
```
User: "build a tool to search TikTok"
You: "I'll help build that. Quick questions:
  1. What data do you need (views, likes, comments, hashtags)?
  2. Scheduled or on-demand searches?
  3. Output format (JSON, CSV, dashboard)?

Then I'll implement it."
```

#### 🤔 Type C: Genuinely Ambiguous → **PROVIDE OPTIONS** (Rare!)

Only use this when the request is **truly unclear** and could mean multiple completely different things.

**This should be RARE** - most requests are Type A or Type B.

### 🚫 Common Mistakes to AVOID

1. **DON'T** offer to "search OR build" for research requests
   - If they say "search", they want search results, not code

2. **DON'T** ask "would you like me to use WebSearch?"
   - Just use it!

3. **DON'T** generate TypeScript applications for simple searches
   - WebSearch is for information, code is for building

4. **DON'T** ask clarifying questions for obvious research
   - "Find top X" = search and return results
   - "What are the best Y" = search and return results

### 📚 Learned Patterns (Applied Automatically)

These patterns are from real user feedback and should be **strictly followed**:

#### Pattern 1: "Under Ideation" + "Search/Find/Explore"
- **Trigger:** "under ideation", "brainstorm", "explore ideas" + "search", "find", "look up"
- **Action:** IMMEDIATE_ACTION (confidence: 95%)
- **Lesson:** User is brainstorming and wants research data, not implementation discussion
- **Example:** "Under ideation: search for top 2 viral TikTok videos" → WebSearch immediately

#### Pattern 2: Research/Discovery Requests
- **Trigger:** "search", "find", "top", "best", "latest", "trending"
- **Action:** IMMEDIATE_ACTION (confidence: 90%)
- **Lesson:** These are information retrieval requests, not build requests
- **Example:** "Find trending AI agents" → WebSearch immediately

#### Pattern 3: Build/Implementation Requests
- **Trigger:** "build", "create", "develop", "implement"
- **Action:** ASK_CLARIFICATION (confidence: 85%)
- **Lesson:** Building requires understanding requirements
- **Example:** "Build a monitoring dashboard" → Ask 2-3 questions first

### 🎓 Learning from Feedback

If you make a mistake:
1. **Acknowledge it immediately**
2. **Correct by taking the right action**
3. **Remember the pattern for next time**

User feedback examples:
- "I wanted you to search, not ask how to build" → You should have done Type A
- "Just do it!" → You should have done Type A
- "I need more details before we start" → Type B was correct

### ⏱️ User's Time is Valuable

Every time you ask "how would you like me to..." for a search request, you're:
- ❌ Wasting the user's time
- ❌ Adding unnecessary friction
- ❌ Not being helpful

Instead:
- ✅ Act decisively on clear requests
- ✅ Show initiative and proactivity
- ✅ Be the assistant they need, not the one that over-asks

### 🎯 Summary: Your Action Mandate

**For Research/Information Requests:**
→ **USE TOOLS IMMEDIATELY** (WebSearch, Read, Grep, etc.)
→ **RETURN RESULTS**
→ **NO QUESTIONS** (unless genuinely ambiguous)

**For Build/Implementation Requests:**
→ **ASK 2-3 TARGETED QUESTIONS**
→ **THEN IMPLEMENT**

**Remember:** You are here to **DO**, not just to **discuss doing**.

---

## 🤖 Marvin 3.0 Integration Features

### Phase 1: Foundation (Complete ✅)
- **TorqMarvinIntegration**: Core integration layer with structured output methods
  - `extract()`: Extract structured data from unstructured text
  - `cast()`: Cast text to Pydantic types with validation
  - `classify()`: Classify text into predefined categories
  - `generate()`: Generate structured data from descriptions
  - `run()`: Execute simple AI tasks with type safety
- **Base Agents**: Specialized agents for spec analysis, code review, and research
- **Pydantic Models**: Type-safe models for all AI operations
- **Multi-LLM Support**: Anthropic Claude, OpenAI, and other providers

### Phase 2: Spec-Kit Enhancement (Complete ✅)
- **MarvinSpecAnalyzer**: AI-powered specification analysis
  - Quality assessment (clarity, completeness, feasibility)
  - Intelligent requirement extraction
  - Intent and complexity classification
  - Acceptance criteria generation
- **MarvinQualityEngine**: Multi-dimensional quality scoring
  - 5 quality dimensions (clarity, completeness, feasibility, testability, maintainability)
  - Quality levels (excellent → good → adequate → needs_work → poor)
  - Specification validation with errors/warnings
  - AI-powered improvement suggestions
- **MarvinSpecKitBridge**: Seamless integration with existing Spec-Kit workflow

### Phase 3: Agent Enhancement (Complete ✅)
- **MarvinQueryRouter**: Intelligent query routing
  - AI-powered intent classification
  - Automatic agent selection based on capabilities
  - Context-aware routing decisions
  - Performance metrics tracking
- **MarvinPrinceFlowers**: Enhanced conversational agent
  - Multi-turn conversation tracking
  - Task management integration
  - Code assistance capabilities
  - Agent state management
- **Specialized Workflow Agents**:
  - **CodeGenerationAgent**: Clean, documented code with examples
  - **DebuggingAgent**: Root cause analysis and fixes
  - **DocumentationAgent**: API docs and guides
  - **TestingAgent**: Comprehensive test suites
  - **ArchitectureAgent**: System design with trade-off analysis
- **MarvinAgentOrchestrator**: Multi-agent coordination
  - Single/Multi/Pipeline/Parallel execution modes
  - Workflow request handling
  - Comprehensive metrics aggregation
- **MarvinAgentMemory**: Persistent memory and learning
  - Interaction history tracking
  - User preferences and patterns
  - Feedback integration for learning
  - Context provision for agents

## 🚀 Spec-Kit Original Features (Phases 1-3)

### Phase 3: Ecosystem Intelligence

### 🌐 GitHub/GitLab Integration
- **Repository Synchronization**: Automatic sync of specifications to GitHub/GitLab
- **Version Control Integration**: Track specification changes with Git history
- **Collaborative Development**: Team-based specification management
- **Multi-Repository Support**: Connect and manage multiple code repositories

### 👥 Real-time Team Collaboration
- **WebSocket Server**: Live collaborative editing with conflict resolution
- **Section Locking**: Prevent edit conflicts during collaborative sessions
- **Real-time Cursors**: See team member cursor positions and typing indicators
- **Session Management**: Create, join, and leave collaborative editing sessions

### 🏢 Multi-Project Workspace Management
- **Workspace Creation**: Organize specifications across multiple projects
- **Team Member Management**: Role-based access and permissions
- **Cross-Project Analytics**: Comprehensive reporting across workspaces
- **Centralized Dashboard**: Single view for all projects and specifications

### 📈 Advanced Analytics & Reporting
- **Collaboration Metrics**: Track team productivity and engagement
- **Specification Quality Trends**: Monitor improvement over time
- **Usage Analytics**: Detailed insights into team collaboration patterns
- **Export Capabilities**: Generate reports for stakeholders and management

## 🚀 New in Phase 2: Adaptive Intelligence Layer

### 🧠 Adaptive Intelligence Layer
- **Real-time Specification Analysis** with live feedback as you type
- **Intelligent Completion Suggestions** based on context and patterns
- **Context-aware Risk Prediction** with automated mitigation strategies
- **Automated Dependency Detection** from specification content
- **Adaptive Learning** from user feedback to improve over time
- **Real-time Editing Assistance** with auto-corrections and enhancements

### ⚡ Performance Optimizations
- **Sub-second Analysis**: Real-time analysis in <2s for complex specifications
- **Debounced Processing**: Intelligent delays to reduce computational overhead
- **Pattern Caching**: Pre-computed suggestions for common patterns
- **Concurrent Sessions**: Support for multiple simultaneous editing sessions

### 📊 Learning & Analytics
- **User Feedback Integration**: Continuous improvement from user interactions
- **Performance Metrics**: Detailed analytics on suggestion accuracy and adoption
- **Adaptive Weights**: Dynamic adjustment of analysis algorithms based on usage
- **Session Analytics**: Comprehensive tracking of editing sessions and outcomes

## 🚀 New in Phase 1

### ✨ GitHub Spec-Kit Integration
- **Complete workflow**: `/constitution` → `/specify` → `/plan` → `/tasks` → `/implement`
- **RL-powered analysis** of specifications for clarity, completeness, feasibility, and complexity
- **Automated task planning** with milestones and resource estimation
- **Risk assessment** with intelligent mitigation strategies
- **Persistent storage** with JSON serialization

### 🧠 RL-Powered Specification Analyzer
- **Heuristic analysis** when RL system unavailable
- **Learning from feedback** to improve analysis accuracy over time
- **Context-aware evaluation** based on domain, tech stack, and project size
- **Confidence scoring** for analysis reliability

### 📋 Intelligent Task Planning
- **Automated task generation** from specifications
- **Smart milestone creation** with target dates
- **Resource estimation** (hours, team size, budget)
- **Dependency tracking** and risk mitigation strategies

## 🎮 Command Reference

### Core Spec-Kit Commands

```bash
# 1. Create Project Constitution
/torq-spec constitution create "MyApp" "Build amazing software" \
  --principles="Quality,Speed,Security" \
  --constraints="Time,Budget" \
  --criteria="Performance,Usability"

# 2. Create Specification with RL Analysis
/torq-spec specify create "User Auth" "Secure authentication system" \
  --requirements="Login,Logout,Password reset" \
  --tech="python,jwt,database" \
  --complexity="medium" \
  --priority="high"

# 3. Generate Implementation Plan
/torq-spec plan generate spec_0001

# 4. Start Implementation
/torq-spec implement start spec_0001

# 5. Track Progress
/torq-spec status
/torq-spec tasks list spec_0001
```

### Management Commands

```bash
# List all items
/torq-spec constitution list
/torq-spec specify list
/torq-spec plan list

# Search specifications
/torq-spec search "authentication"
/torq-spec search "api" --status=active

# Show detailed information
/torq-spec constitution show "MyApp"
/torq-spec specify show spec_0001
/torq-spec plan show spec_0001
```

### Phase 3: Ecosystem Intelligence Commands

```bash
# GitHub/GitLab Integration
/torq-spec connect github https://github.com/user/repo --token YOUR_GITHUB_TOKEN
/torq-spec sync spec_0001 github
/torq-spec repo status

# Team Collaboration
/torq-spec collab start spec_0001 --members "alice@dev.com,bob@dev.com"
/torq-spec collab join session_001
/torq-spec collab server start --port 8765

# Workspace Management
/torq-spec workspace create "MyProject" "Project description"
/torq-spec workspace list
/torq-spec workspace show "MyProject"

# Advanced Analytics
/torq-spec analytics team --workspace "MyProject"
/torq-spec analytics specs --timeframe "30days"
/torq-spec metrics collaboration
```

### Marvin AI Agent Commands (CLI)

```bash
# Intelligent Query Routing
/torq-agent query "How do I implement JWT authentication in Python?"
/torq-agent query "What's the best way to structure a FastAPI project?"

# Conversational Agent (Prince Flowers)
/torq-agent chat "Can you explain async/await patterns?"
/torq-agent chat "Help me understand database indexing strategies"

# Code Generation
/torq-agent code "Create a binary search tree with insert and search methods" --language=python
/torq-agent code "Implement rate limiting middleware" --language=python
/torq-agent code "JWT authentication system" --language=python

# Debugging Assistance
/torq-agent debug "def calc(x): return x/0" "ZeroDivisionError: division by zero" --language=python
/torq-agent debug "<problematic_code>" "<error_message>" --language=python

# Documentation Generation
/torq-agent docs "def add(a, b): return a + b" --type=api --language=python
/torq-agent docs "<your_code>" --type=guide --language=python
/torq-agent docs "<your_code>" --type=reference --language=python

# Test Generation
/torq-agent test "def add(a, b): return a + b" --framework=pytest --language=python
/torq-agent test "<your_code>" --framework=unittest --language=python

# Architecture Design
/torq-agent arch "E-commerce platform with user management and payment processing" --type=web_application
/torq-agent arch "Real-time chat system with presence and notifications" --type=microservice

# Multi-Agent Orchestration
/torq-agent orchestrate "Build authentication system with tests and documentation" --mode=multi_agent
/torq-agent orchestrate "Create API endpoints with validation and error handling" --mode=pipeline

# Agent Memory Management
/torq-agent memory snapshot                    # Show memory snapshot
/torq-agent memory history prince_flowers      # Show interaction history
/torq-agent memory preferences                 # Show user preferences
/torq-agent memory set code_style "google"     # Set preference
/torq-agent memory clear 30                    # Clear old interactions

# Performance Metrics
/torq-agent metrics                            # Show comprehensive metrics
/torq-agent status                             # Show agent system status
```

### Marvin-Enhanced Spec Commands (CLI)

```bash
# Create Specification with Marvin Analysis (automatic if available)
/torq-spec specify create "User Authentication" "Secure authentication system" \
  --requirements="Login,Logout,Password reset" \
  --tech="python,jwt,database" \
  --complexity="medium" \
  --priority="high"

# Force Marvin Analysis
/torq-spec specify create "API Gateway" "Central API gateway for microservices" \
  --tech="node,express,redis" \
  --use-marvin

# Disable Marvin (use RL only)
/torq-spec specify create "Reporting Module" "Generate reports from data" \
  --tech="python,pandas" \
  --no-marvin

# Re-analyze Existing Specification with Marvin
/torq-spec specify analyze spec_0001
/torq-spec specify analyze spec_0001 --use-marvin
/torq-spec specify analyze spec_0001 --no-marvin

# Update Specification
/torq-spec specify update spec_0001 --status="in_progress" --priority="high"
/torq-spec specify update spec_0001 --title="New Title" --description="Updated description"

# Update Constitution
/torq-spec constitution update "MyApp" --purpose="Updated purpose"
/torq-spec constitution update "MyApp" --add-principle="Security first"
```

### Marvin AI Integration API (Python)

```python
# Python API (programmatic access to all Marvin features)

# 1. Analyze Specification with Marvin
from torq_console.spec_kit import marvin_analyze_spec
from torq_console.spec_kit.rl_spec_analyzer import SpecificationContext

context = SpecificationContext(
    domain="authentication",
    tech_stack=["python", "fastapi", "postgresql"],
    project_size="medium",
    team_size=3,
    timeline="4-weeks",
    constraints=["security-critical"]
)

result = await marvin_analyze_spec(spec_text, context)
# Returns: quality score, recommendations, extracted requirements

# 2. Route Query to Appropriate Agent
from torq_console.agents import create_query_router

router = create_query_router()
routing = await router.route_query("Help me write a validation function")
# Returns: best agent, capabilities needed, routing reasoning

# 3. Use Enhanced Prince Flowers Agent
from torq_console.agents import create_prince_flowers_agent

agent = create_prince_flowers_agent()
response = await agent.chat("How do I implement OAuth?")
# Returns: intelligent response with conversation tracking

# 4. Generate Code with Specialized Agent
from torq_console.agents import get_workflow_agent, WorkflowType

code_agent = get_workflow_agent(WorkflowType.CODE_GENERATION)
result = await code_agent.generate_code(
    requirements="Email validation function",
    language="python"
)
# Returns: code, explanation, usage example, recommendations

# 5. Debug Code Issues
debug_agent = get_workflow_agent(WorkflowType.DEBUGGING)
result = await debug_agent.debug_issue(
    code=buggy_code,
    error_message="ZeroDivisionError",
    language="python"
)
# Returns: root cause, fix, explanation, prevention tips

# 6. Orchestrate Multiple Agents
from torq_console.agents import get_orchestrator, OrchestrationMode

orchestrator = get_orchestrator()
result = await orchestrator.process_query(
    "Generate a sorting function with tests",
    mode=OrchestrationMode.MULTI_AGENT
)
# Returns: coordinated response from multiple agents

# 7. Track Agent Interactions
from torq_console.agents import get_agent_memory, InteractionType

memory = get_agent_memory()
interaction_id = memory.record_interaction(
    user_input="How do I use decorators?",
    agent_response="Decorators modify functions...",
    agent_name="prince_flowers",
    interaction_type=InteractionType.GENERAL_CHAT,
    success=True
)

memory.add_feedback(interaction_id, score=0.9)  # Learn from feedback
snapshot = memory.get_memory_snapshot()  # Get memory stats
```

## 📁 File Structure

TORQ Console Spec-Kit creates a comprehensive `.torq-specs` directory in your workspace:

```
.torq-specs/
├── constitutions.json     # Project constitutions
├── specifications.json   # Specifications with RL/Marvin analysis
├── task_plans.json      # Implementation plans
└── ecosystem/           # Ecosystem Intelligence
    ├── repositories/    # Connected Git repositories
    ├── workspaces/     # Multi-project workspaces
    ├── sessions/       # Active collaboration sessions
    ├── versions/       # Specification version history
    └── analytics/      # Usage and collaboration metrics

~/.torq/agent_memory/     # Marvin Agent Memory (persistent)
├── interactions.json    # Agent interaction history
├── preferences.json    # User preferences
└── patterns.json       # Learned patterns

torq_console/
├── marvin_integration/  # Marvin Phase 1: Foundation
│   ├── __init__.py
│   ├── core.py         # TorqMarvinIntegration
│   ├── models.py       # Pydantic models
│   └── agents.py       # Base Marvin agents
├── spec_kit/           # Spec-Kit + Marvin Phase 2
│   ├── marvin_spec_analyzer.py      # AI-powered spec analysis
│   ├── marvin_quality_engine.py     # Quality scoring
│   ├── marvin_integration.py        # Integration bridge
│   └── spec_commands.py             # CLI commands (Marvin-enhanced)
├── agents/             # Marvin Phase 3: Agent Enhancement
│   ├── marvin_query_router.py       # Intelligent routing
│   ├── marvin_prince_flowers.py     # Enhanced Prince Flowers
│   ├── marvin_workflow_agents.py    # Specialized agents
│   ├── marvin_orchestrator.py       # Multi-agent coordination
│   ├── marvin_memory.py             # Memory & learning
│   └── marvin_commands.py           # CLI commands (agent system)
└── cli.py              # Main CLI with agent command integration
```

## 🔬 RL Analysis Features

### Specification Analysis Scores
- **Clarity Score** (0.0 - 1.0): How well-defined the requirements are
- **Completeness Score** (0.0 - 1.0): Coverage of all necessary components
- **Feasibility Score** (0.0 - 1.0): Technical and resource feasibility
- **Complexity Score** (0.0 - 1.0): Implementation complexity level

### Risk Assessment Categories
- **Technical Risk**: Technology complexity and integration challenges
- **Scope Risk**: Requirements clarity and scope creep potential
- **Timeline Risk**: Schedule feasibility and deadline pressure
- **Quality Risk**: Quality assurance and testing adequacy

### Intelligent Recommendations
- **Ambiguity reduction** suggestions
- **Missing requirement** identification
- **Technical feasibility** warnings
- **Scope management** advice

## 🏗 Implementation Workflow

### 1. Project Setup
```bash
# Define project constitution
/torq-spec constitution create "ECommerceApp" "Build scalable e-commerce platform" \
  --principles="User-first,Scalable,Secure" \
  --constraints="6-month timeline,Team of 8,Cloud-native"
```

### 2. Specification Creation
```bash
# Create detailed specifications
/torq-spec specify create "User Management" "Complete user account system" \
  --requirements="Registration,Login,Profile,Preferences" \
  --acceptance="All tests pass,Security audit,Performance benchmarks" \
  --tech="python,fastapi,postgresql,redis" \
  --timeline="4-weeks" \
  --complexity="large"
```

### 3. Plan Generation
```bash
# Generate implementation plan
/torq-spec plan generate spec_0001

# Review generated tasks and milestones
/torq-spec tasks list spec_0001
```

### 4. Implementation Tracking
```bash
# Start implementation
/torq-spec implement start spec_0001

# Track progress
/torq-spec tasks update spec_0001 task_001 completed
/torq-spec status
```

## 📊 Analysis Examples

### High-Quality Specification
```
Specification: User Authentication System

RL Analysis:
  Clarity Score: 0.92
  Completeness Score: 0.88
  Feasibility Score: 0.85
  Complexity Score: 0.70
  Confidence: 0.85

Recommendations:
  • Add more specific security requirements
  • Define performance benchmarks
  • Specify error handling requirements

Risk Assessment:
  • Technical Risk: 0.30 (Low)
  • Scope Risk: 0.25 (Low)
  • Timeline Risk: 0.40 (Medium)
  • Quality Risk: 0.35 (Medium)
```

### Needs Improvement
```
Specification: Build some features

RL Analysis:
  Clarity Score: 0.15
  Completeness Score: 0.20
  Feasibility Score: 0.40
  Complexity Score: 0.80
  Confidence: 0.25

Recommendations:
  • Define specific requirements and acceptance criteria
  • Add technical implementation details
  • Specify timeline and resource constraints
  • Break down into smaller, manageable components

Risk Assessment:
  • Technical Risk: 0.85 (High)
  • Scope Risk: 0.90 (High)
  • Timeline Risk: 0.95 (Critical)
  • Quality Risk: 0.80 (High)
```

## ⚡ Phase 2: Real-time Editing Workflow

### Real-time Specification Editing
The Phase 2 Adaptive Intelligence Layer provides intelligent assistance as you write specifications:

```bash
# 1. Start real-time editing session (automatic when using /torq-spec specify create)
# Real-time analysis begins immediately as you type

# 2. Get live suggestions and analysis
# - Intelligent completion suggestions based on context
# - Auto-correction of technical terms and typos
# - Risk warnings and mitigation suggestions
# - Dependency detection and recommendations

# 3. Interactive feedback system
# Accept helpful suggestions: Improves learning algorithm
# Reject irrelevant suggestions: Adapts to your preferences
# Rate overall experience: Continuous improvement
```

### AI-Powered Writing Assistance

```bash
# Real-time Pattern Detection
✓ User story format suggestions
✓ Technical stack recommendations
✓ Security requirement prompts
✓ Performance criteria reminders

# Intelligent Auto-Corrections
✓ Technical term standardization (nodejs → Node.js)
✓ Common typo corrections
✓ Consistent formatting

# Context-Aware Suggestions
✓ OAuth integration for authentication specs
✓ Database considerations for data requirements
✓ Scalability suggestions for performance specs
✓ Testing requirements for feature specifications
```

### Performance Metrics & Learning

```bash
# View real-time editing metrics
/torq-spec metrics realtime

# Check adaptive intelligence status
/torq-spec ai-status

# Export learning analytics
/torq-spec analytics export
```

### Example: Smart Specification Creation

```bash
# Start creating a specification
/torq-spec specify create "User Authentication" "Build secure user auth system"

# As you type, get intelligent suggestions:
#
# Typing: "Users can login with email and password"
# → Suggestion: "Consider adding OAuth integration (Google, GitHub)"
# → Risk Warning: "Password-only auth has security risks - suggest MFA"
# → Dependency: "Email verification service required"
#
# Typing: "System must be fast"
# → Suggestion: "Specify exact performance criteria (e.g., <2s login time)"
#
# Auto-correction: "jwt" → "JWT"
# Auto-correction: "oauth" → "OAuth"
```

## 🔧 Integration with Existing Features

### MCP Integration
- Spec-Kit works alongside existing MCP servers
- GitHub MCP server can sync specifications to repositories
- Database MCP servers can store specification data

### Enhanced RL System
- Integrates with existing Enhanced RL System when available
- Falls back to heuristic analysis when RL unavailable
- Learns from project outcomes to improve analysis

### Command Palette
- All Spec-Kit commands available via `Ctrl+Shift+P`
- Fuzzy search across specifications and constitutions
- Quick access to status and progress information

## 🎯 Best Practices

### Constitution Design
1. **Clear Purpose**: Define why the project exists
2. **Actionable Principles**: Specific, measurable guidelines
3. **Realistic Constraints**: Honest assessment of limitations
4. **Measurable Success**: Quantifiable success criteria

### Specification Writing
1. **Specific Requirements**: Use "must", "should", "shall" language
2. **Complete Acceptance Criteria**: Define "done" clearly
3. **Technical Details**: Include architecture and tech choices
4. **Risk Awareness**: Acknowledge known challenges

### Implementation Planning
1. **Review RL Analysis**: Address recommendations before starting
2. **Iterative Development**: Break large specs into phases
3. **Regular Updates**: Track progress and update status
4. **Learn from Outcomes**: Provide feedback for RL improvement

## 📈 Success Metrics & Status

### 🎉 Marvin 3.0 Integration (Complete!)

#### Phase 3: Agent Enhancement ✅ COMPLETE
- **10/10 validation tests** passing (100% success rate)
- **2,319 lines** of production code
- **21 classes** and **72 functions** implemented
- **5 specialized workflow agents**: Code, Debug, Docs, Testing, Architecture
- **MarvinQueryRouter**: Intelligent query classification and routing
- **MarvinPrinceFlowers**: Enhanced conversational agent with memory
- **MarvinAgentOrchestrator**: 4 execution modes (Single/Multi/Pipeline/Parallel)
- **MarvinAgentMemory**: Persistent interaction tracking and learning
- **18 async methods** for efficient LLM operations

#### Phase 2: Spec-Kit Enhancement ✅ COMPLETE
- **8/8 validation tests** passing (100% success rate)
- **1,164 lines** of production code
- **6 classes** and **41 functions** implemented
- **MarvinSpecAnalyzer**: AI-powered specification analysis
- **MarvinQualityEngine**: 5-dimensional quality scoring
- **Multi-dimensional scoring**: Clarity, Completeness, Feasibility, Testability, Maintainability
- **Quality levels**: Excellent → Good → Adequate → Needs Work → Poor
- **Specification validation** with structured errors and warnings

#### Phase 1: Marvin Foundation ✅ COMPLETE
- **7/7 validation tests** passing (100% success rate)
- **1,986 lines** of production code
- **TorqMarvinIntegration**: Complete structured output API
- **Base agents**: Spec analyzer, code reviewer, research specialist
- **Pydantic models**: Full type safety for all AI operations
- **Multi-LLM support**: Anthropic Claude, OpenAI, and others

#### CLI Integration ✅ COMPLETE  (NEW!)
- **6/6 validation tests** passing (100% success rate)
- **746 lines** of CLI command code
- **11 agent commands**: query, chat, code, debug, docs, test, arch, orchestrate, memory, metrics, status
- **Enhanced spec commands**: --use-marvin, --no-marvin flags, analyze subcommand
- **Complete help systems**: Usage, examples, and documentation for all commands
- **Error handling**: Graceful fallback when Marvin unavailable
- **torq-console agent**: New CLI command for all Marvin agents
- **Marvin-enhanced /torq-spec**: Automatic AI analysis when available

#### Total Marvin Integration
- **✅ 31/31 tests passing** (100% success rate)
- **6,215 lines** of production code
- **Full integration** across foundation, spec-kit, agents, and CLI
- **Production-ready** for immediate use with both CLI and Python API

### Spec-Kit Original Features (Also Complete)

#### Spec-Kit Phase 3: Ecosystem Intelligence ✅
- **10/10 core components** implemented for team collaboration
- **WebSocket server** for real-time collaborative editing
- **GitHub/GitLab integration** with full synchronization
- **Multi-project workspace management** system
- **Advanced analytics** and reporting capabilities

#### Spec-Kit Phase 2: Adaptive Intelligence Layer ✅
- **6/6 test suite components** passing (100% success rate)
- **Real-time analysis** with <2s response time
- **Pattern-based suggestions** with 50+ built-in patterns
- **Adaptive learning** with user feedback integration

#### Spec-Kit Phase 1: Intelligent Spec-Driven Foundation ✅
- **6/6 test suite components** passing (100% after bug fixes)
- **RL-powered analysis** for specification quality assessment
- **Automated task planning** with resource estimation
- **Complete GitHub Spec-Kit workflow** implementation

## 🎉 Get Started

### Marvin Integration Quick Start

1. **Set your API key**:
   ```bash
   # For Anthropic Claude (recommended)
   export ANTHROPIC_API_KEY=your_key_here

   # Or for OpenAI
   export OPENAI_API_KEY=your_key_here
   ```

2. **Try the CLI commands** (NEW!):
   ```bash
   # Get help on agent commands
   torq-console agent

   # Ask a question with intelligent routing
   torq-console agent query "How do I implement JWT authentication?"

   # Generate code
   torq-console agent code "Binary search tree implementation" --language=python

   # Create specification with Marvin analysis
   torq-console /torq-spec specify create "User Auth" "Authentication system"
   ```

3. **Run the examples** (Python API):
   ```bash
   python examples/marvin_integration_examples.py
   ```

4. **Read the quick start guide**:
   ```bash
   cat examples/QUICKSTART.md
   ```

5. **Try specification analysis** (Python):
   ```python
   import asyncio
   from torq_console.spec_kit import marvin_analyze_spec
   from torq_console.spec_kit.rl_spec_analyzer import SpecificationContext

   # See examples/ for complete usage
   ```

### Traditional Spec-Kit Workflow

1. **Initialize your project**:
   ```bash
   /torq-spec constitution create "MyProject" "Project purpose here"
   ```

2. **Create your first specification**:
   ```bash
   /torq-spec specify create "Core Feature" "Detailed description"
   ```

3. **Generate implementation plan**:
   ```bash
   /torq-spec plan generate spec_0001
   ```

4. **Start building**:
   ```bash
   /torq-spec implement start spec_0001
   ```

## ✨ What's Available Now

### Marvin 3.0 Integration ✅
- **Complete CLI Integration** with `torq-console agent` commands (NEW!)
- **Marvin-Enhanced /torq-spec** with automatic AI analysis (NEW!)
- **AI-Powered Specification Analysis** with quality scoring
- **Intelligent Query Routing** to appropriate agents
- **Enhanced Prince Flowers Agent** with conversation memory
- **5 Specialized Workflow Agents** for code, debugging, docs, testing, architecture
- **Multi-Agent Orchestration** with 4 execution modes
- **Persistent Memory & Learning** from user interactions

### Original Spec-Kit Features ✅
- **Complete GitHub Spec-Kit workflow** with RL-powered analysis
- **Real-time collaborative editing** with intelligent suggestions
- **Team-based specification management** with WebSocket collaboration
- **Multi-project workspace organization** with advanced analytics
- **Full ecosystem intelligence** for enterprise-grade development

### Resources
- **Examples**: `examples/marvin_integration_examples.py`
- **Quick Start**: `examples/QUICKSTART.md`
- **This Guide**: `CLAUDE.md` (you're reading it!)
- **Tests**: `test_phase*.py` for usage patterns

---

**🎉 All integration phases complete!** TORQ Console v0.80.0+ is production-ready with:
- ✅ **Marvin 3.0 Integration**: Foundation + Spec-Kit + Agents + CLI (6,215 lines, 31/31 tests passing)
- ✅ **Complete CLI Access**: Both `torq-console agent` and Marvin-enhanced `/torq-spec` commands
- ✅ **Original Spec-Kit**: Ecosystem Intelligence + Adaptive Layer + RL Foundation

*TORQ Console - Where AI meets industrial-grade software development methodology.*
*Now featuring complete Marvin 3.0 integration with full CLI access for intelligent agent orchestration.*