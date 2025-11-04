# Marvin Integration Analysis for TORQ Console

**Author:** Claude Code Assistant
**Date:** 2025-11-04
**Version:** 1.0
**Status:** Comprehensive Analysis & Recommendations

---

## Executive Summary

This document analyzes [PrefectHQ's Marvin 3.0](https://github.com/PrefectHQ/marvin) framework and proposes strategic integration with TORQ Console to enhance its AI capabilities. Marvin 3.0 combines structured output utilities with agentic workflows, superseding ControlFlow and providing a simpler, more practical approach to AI integration.

**Key Recommendation:** Integrate Marvin as TORQ Console's primary AI framework for structured outputs, data extraction, and agentic workflows.

**Why Marvin over ControlFlow:** Marvin 3.0 supersedes ControlFlow by combining Marvin 2.0's excellent DX with ControlFlow's agentic engine, offering a simpler, more unified API.

---

## 1. What is Marvin 3.0?

### 1.1 Core Philosophy

> **"A Python framework for producing structured outputs and building agentic AI workflows"**

Marvin provides an intuitive API for:
- ✅ **Cast, classify, extract, and generate** structured data from any inputs
- ✅ **Create discrete, observable tasks** that describe your objectives
- ✅ **Assign specialized AI agents** to each task
- ✅ **Combine tasks into threads** to orchestrate complex behaviors

### 1.2 Key Differentiators

**vs. ControlFlow:**
- **Simpler API**: Marvin has a more streamlined, practical interface
- **Supersedes ControlFlow**: Marvin 3.0 incorporates ControlFlow's best features
- **Better structured outputs**: Native support for extract/cast/classify/generate
- **Unified framework**: One framework for both structured outputs AND agentic workflows

**vs. LangChain:**
- **Type-safe**: Leverages Pydantic for type-safe results
- **Simpler**: Less abstraction, more direct
- **Better observability**: Built-in monitoring and debugging

### 1.3 Technology Stack

- **LLM Backend**: Pydantic AI (supports OpenAI, Anthropic, Gemini, etc.)
- **Storage**: SQLite for thread/message history
- **Type Safety**: Pydantic models throughout
- **Python**: Requires Python 3.10+

---

## 2. Core Capabilities

### 2.1 Structured Output Utilities

Marvin excels at transforming unstructured data into structured formats:

#### **`marvin.extract`** - Extract specific data types

```python
import marvin

# Extract numbers from text
result = marvin.extract(
    "i found $30 on the ground and bought 5 bagels for $10",
    int,
    instructions="only USD"
)
print(result)  # [30, 10]
```

#### **`marvin.cast`** - Transform data into structured types

```python
from typing import TypedDict
import marvin

class Location(TypedDict):
    lat: float
    lon: float

result = marvin.cast("the place with the best bagels", Location)
print(result)  # {'lat': 40.712776, 'lon': -74.005974}
```

#### **`marvin.classify`** - Categorize into predefined labels

```python
from enum import Enum
import marvin

class SupportDepartment(Enum):
    ACCOUNTING = "accounting"
    HR = "hr"
    IT = "it"
    SALES = "sales"

result = marvin.classify("shut up and take my money", SupportDepartment)
print(result)  # SupportDepartment.SALES
```

#### **`marvin.generate`** - Generate structured objects

```python
import marvin

primes = marvin.generate(int, 10, "odd primes")
print(primes)  # [3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
```

### 2.2 Agentic Workflows

Marvin 3.0 brings ControlFlow's agentic capabilities:

#### **Tasks** - Fundamental unit of work

```python
import marvin

# Simple task
poem = marvin.run("Write a short poem about AI")

# Structured task with type safety
answer = marvin.run("the answer to the universe", result_type=int)
print(answer)  # 42
```

#### **Agents** - Specialized AI workers

```python
from marvin import Agent

writer = Agent(
    name="Poet",
    instructions="Write creative, evocative poetry"
)
poem = writer.run("Write a haiku about coding")
```

#### **Threads** - Context management

```python
import marvin

with marvin.Thread() as thread:
    topic = marvin.run("Ask the user for a topic", cli=True)
    research = marvin.run(f"Research {topic}", result_type=list[str])
    article = marvin.run("Write article", context={"research": research})
```

#### **Tools** - Extend agent capabilities

```python
import platform
import subprocess
from pydantic import IPvAnyAddress
import marvin

def run_shell_command(command: list[str]) -> str:
    """Execute shell commands"""
    return subprocess.check_output(command).decode()

task = marvin.Task(
    instructions="find the current ip address",
    result_type=IPvAnyAddress,
    tools=[run_shell_command],
    context={"os": platform.system()},
)

result = task.run()
```

---

## 3. Current TORQ Console Architecture

### 3.1 Existing Systems

**Agent Layer:**
- Prince Flowers Agent (monolithic)
- Enhanced RL System
- ARTIST RL Learning

**Output Systems:**
- Basic string responses
- No structured output validation
- Manual JSON parsing

**Workflow Systems:**
- Hardcoded workflows
- No task abstraction
- Limited observability

**Spec-Kit System:**
- Specification analysis
- Task planning
- Implementation tracking

### 3.2 Current Limitations

1. **No Structured Outputs**
   - Responses are unstructured strings
   - Manual validation and parsing required
   - No type safety

2. **Limited Data Extraction**
   - No built-in extraction capabilities
   - Can't easily extract structured info from text
   - Manual regex/parsing patterns

3. **No Classification System**
   - Can't categorize user queries automatically
   - No intent classification
   - Manual routing logic

4. **Basic Agent System**
   - Single monolithic agent
   - No easy agent specialization
   - Limited tool integration

---

## 4. Integration Opportunities

### 4.1 Strategic Integration Points

#### **A. Add Structured Output Layer**

**Current State:**
```python
# TORQ Console current approach
response = await agent.process_query("Extract prices from this invoice")
# Response is unstructured string, need to parse manually
```

**With Marvin:**
```python
# Marvin-enhanced TORQ Console
from pydantic import BaseModel

class Invoice(BaseModel):
    items: list[str]
    prices: list[float]
    total: float

invoice = marvin.cast(invoice_text, Invoice)
# Type-safe, validated Invoice object
```

#### **B. Enhanced Spec-Kit Analysis**

**Current State:**
```python
# Manual analysis with hardcoded scoring
analysis = {
    'clarity_score': calculate_clarity(spec),
    'completeness_score': calculate_completeness(spec),
    # Manual calculations...
}
```

**With Marvin:**
```python
# Type-safe, AI-powered analysis
class SpecAnalysis(BaseModel):
    clarity_score: float
    completeness_score: float
    missing_requirements: list[str]
    ambiguous_sections: list[str]
    recommendations: list[str]

analysis = marvin.cast(specification_text, SpecAnalysis,
    instructions="Analyze this software specification for quality"
)
```

#### **C. Intelligent Query Routing**

**Current State:**
```python
# Manual routing logic
if 'search' in query.lower():
    return await research_workflow(query)
elif 'code' in query.lower():
    return await code_workflow(query)
# Many manual conditions...
```

**With Marvin:**
```python
# Automatic classification
class QueryType(Enum):
    RESEARCH = "research"
    CODE_ANALYSIS = "code_analysis"
    SPEC_CREATION = "spec_creation"
    GENERAL = "general"

query_type = marvin.classify(user_query, QueryType)

# Route based on classification
workflows = {
    QueryType.RESEARCH: research_workflow,
    QueryType.CODE_ANALYSIS: code_workflow,
    QueryType.SPEC_CREATION: spec_workflow,
}
return await workflows[query_type](user_query)
```

#### **D. Data Extraction for Tools**

```python
# Extract structured data from natural language
class GitCommit(BaseModel):
    message: str
    files: list[str]
    issue_refs: list[int]

# User: "Commit the changes to auth.py and users.py with message 'fix login bug' refs #123"
commit = marvin.extract(user_input, GitCommit)

# Now we have structured, type-safe data for git operations
await git_manager.commit(
    files=commit.files,
    message=commit.message,
    issue_refs=commit.issue_refs
)
```

#### **E. Specialized Agents**

```python
# Create specialized agents for different tasks
spec_analyzer = marvin.Agent(
    name="Specification Analyzer",
    instructions="""Analyze software specifications for:
    - Clarity and completeness
    - Technical feasibility
    - Missing requirements
    - Potential risks
    Provide detailed, actionable feedback."""
)

code_reviewer = marvin.Agent(
    name="Code Reviewer",
    instructions="""Review code for:
    - Code quality and style
    - Potential bugs
    - Security issues
    - Performance concerns
    Provide constructive, specific feedback."""
)

# Use in TORQ workflows
spec_review = spec_analyzer.run(
    f"Review this specification: {spec_text}",
    result_type=SpecReview
)
```

---

## 5. Proposed Integration Architecture

### 5.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   TORQ Console UI Layer                      │
│  (Command Palette, Chat, Inline Editor, Web Interface)      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Marvin Integration Layer (NEW!)                 │
│  • Structured Outputs (extract, cast, classify, generate)   │
│  • Agent Management (specialized agents)                     │
│  • Task Orchestration (marvin.run, marvin.Task)             │
│  • Thread Management (context across conversations)         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               Enhanced TORQ Agent Layer                      │
│  • Prince Flowers Agent (enhanced with Marvin)              │
│  • Spec-Kit Agent (structured analysis)                     │
│  • Code Review Agent (structured feedback)                  │
│  • Research Agent (structured outputs)                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Tool & Integration Layer                   │
│  • Web Search     • Browser Automation   • File Operations  │
│  • MCP Servers    • Database Access      • API Integrations  │
│  • N8N Workflows  • HuggingFace Models   • Custom Tools      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            RL Learning & Optimization Layer                  │
│  • ARTIST RL System                                          │
│  • Enhanced RL (Pearl-inspired Architecture)                 │
│  • Dynamic Action Spaces                                     │
│  • Marvin Performance Metrics                                │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Implementation Modules

```
torq_console/
├── marvin_integration/
│   ├── __init__.py
│   ├── structured_outputs.py      # extract, cast, classify, generate
│   ├── agents.py                   # Specialized Marvin agents
│   ├── tasks.py                    # Task definitions
│   ├── threads.py                  # Thread management
│   ├── tools.py                    # TORQ-specific tools for Marvin
│   └── models.py                   # Pydantic models for structured outputs
├── spec_kit/
│   ├── marvin_analyzer.py          # Marvin-powered spec analysis
│   └── marvin_planner.py           # Marvin-powered task planning
└── agents/
    └── marvin_prince_flowers.py    # Prince Flowers enhanced with Marvin
```

---

## 6. Specific Use Cases

### 6.1 Enhanced Spec-Kit Analysis

**Before (Current):**
```python
# Manual heuristic analysis
def analyze_specification(spec_text):
    # Manual scoring
    clarity = calculate_clarity_score(spec_text)
    completeness = calculate_completeness_score(spec_text)
    # etc...
```

**After (With Marvin):**
```python
from pydantic import BaseModel, Field
import marvin

class SpecificationAnalysis(BaseModel):
    clarity_score: float = Field(ge=0.0, le=1.0)
    completeness_score: float = Field(ge=0.0, le=1.0)
    feasibility_score: float = Field(ge=0.0, le=1.0)

    missing_requirements: list[str]
    ambiguous_sections: list[str]
    technical_risks: list[str]
    recommendations: list[str]

    estimated_complexity: str  # "low", "medium", "high"
    estimated_timeline: str

    confidence: float = Field(ge=0.0, le=1.0)

# AI-powered, type-safe analysis
analysis = marvin.cast(
    specification_text,
    SpecificationAnalysis,
    instructions="""Analyze this software specification thoroughly:
    1. Score clarity, completeness, and feasibility (0.0-1.0)
    2. Identify missing requirements and ambiguities
    3. Assess technical risks
    4. Provide actionable recommendations
    5. Estimate complexity and timeline
    """
)

# Now we have structured, validated analysis
print(f"Clarity: {analysis.clarity_score:.2f}")
print(f"Missing: {', '.join(analysis.missing_requirements)}")
```

### 6.2 Intelligent Query Classification

```python
from enum import Enum
import marvin

class UserIntent(Enum):
    # Spec-Kit intents
    CREATE_SPECIFICATION = "create_specification"
    ANALYZE_SPECIFICATION = "analyze_specification"
    GENERATE_TASKS = "generate_tasks"

    # Code intents
    WRITE_CODE = "write_code"
    REVIEW_CODE = "review_code"
    DEBUG_CODE = "debug_code"

    # Research intents
    WEB_SEARCH = "web_search"
    TECHNICAL_RESEARCH = "technical_research"

    # General
    CHAT = "chat"
    HELP = "help"

async def handle_user_query(query: str):
    # Classify intent
    intent = marvin.classify(query, UserIntent)

    # Route to appropriate handler
    handlers = {
        UserIntent.CREATE_SPECIFICATION: create_spec_handler,
        UserIntent.ANALYZE_SPECIFICATION: analyze_spec_handler,
        UserIntent.WEB_SEARCH: web_search_handler,
        # ... more handlers
    }

    return await handlers[intent](query)
```

### 6.3 Structured Code Review

```python
from pydantic import BaseModel
import marvin

class CodeIssue(BaseModel):
    line: int
    severity: str  # "error", "warning", "info"
    category: str  # "bug", "style", "security", "performance"
    description: str
    suggestion: str

class CodeReview(BaseModel):
    overall_quality: float  # 0.0-1.0
    issues: list[CodeIssue]
    strengths: list[str]
    refactoring_suggestions: list[str]
    security_concerns: list[str]

# Structured code review
code_reviewer = marvin.Agent(
    name="Code Reviewer",
    instructions="Provide detailed, actionable code reviews"
)

review = code_reviewer.run(
    f"Review this code:\n\n{code_text}",
    result_type=CodeReview
)

# Type-safe review results
for issue in review.issues:
    print(f"Line {issue.line} [{issue.severity}]: {issue.description}")
```

### 6.4 Data Extraction from Natural Language

```python
from pydantic import BaseModel
import marvin

class TaskBreakdown(BaseModel):
    title: str
    description: str
    subtasks: list[str]
    dependencies: list[str]
    estimated_hours: float
    priority: str  # "low", "medium", "high"

# User: "Create a user authentication system with login, logout, and password
# reset. Should take about 40 hours and depends on the database module. High priority."

task = marvin.extract(
    user_input,
    TaskBreakdown,
    instructions="Extract task details from natural language"
)

# Automatically create structured task in Spec-Kit
await spec_kit.create_task(
    title=task.title,
    description=task.description,
    subtasks=task.subtasks,
    dependencies=task.dependencies,
    estimated_hours=task.estimated_hours,
    priority=task.priority
)
```

### 6.5 Research with Structured Outputs

```python
from pydantic import BaseModel, HttpUrl
import marvin

class ResearchFindings(BaseModel):
    topic: str
    key_points: list[str]
    sources: list[HttpUrl]
    summary: str
    confidence: float
    related_topics: list[str]

# Research with structured output
research_agent = marvin.Agent(
    name="Research Specialist",
    instructions="Conduct thorough research and provide structured findings"
)

findings = research_agent.run(
    "Research the latest developments in AI agent orchestration",
    result_type=ResearchFindings,
    tools=[web_search_tool, web_fetch_tool]
)

# Type-safe research results
print(f"Summary: {findings.summary}")
print(f"Sources: {len(findings.sources)}")
print(f"Confidence: {findings.confidence:.2%}")
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

**Objectives:**
- Install Marvin
- Create integration layer
- Test basic functionality

**Deliverables:**
```python
# torq_console/marvin_integration/__init__.py
from marvin_integration import TorqMarvinIntegration

# Basic usage
marvin_integration = TorqMarvinIntegration()

# Test structured outputs
result = marvin_integration.extract_data(text, target_type=int)
classified = marvin_integration.classify(text, labels=MyEnum)
```

**Tasks:**
1. Install Marvin: `pip install marvin`
2. Create `torq_console/marvin_integration/` module
3. Implement basic wrapper classes
4. Write integration tests
5. Document API

### Phase 2: Spec-Kit Enhancement (Week 3-4)

**Objectives:**
- Enhance Spec-Kit with Marvin
- Add structured specification analysis
- Implement type-safe task planning

**Deliverables:**
```python
# Enhanced Spec-Kit with Marvin
class MarvinSpecAnalyzer:
    async def analyze_specification(self, spec_text: str) -> SpecificationAnalysis:
        """AI-powered spec analysis with structured output"""
        return marvin.cast(spec_text, SpecificationAnalysis)

    async def extract_requirements(self, spec_text: str) -> list[Requirement]:
        """Extract structured requirements"""
        return marvin.extract(spec_text, Requirement)
```

**Tasks:**
1. Define Pydantic models for specifications
2. Create Marvin-powered analyzer
3. Integrate with existing Spec-Kit
4. Add structured task planning
5. Test with real specifications

### Phase 3: Agent Enhancement (Week 5-6)

**Objectives:**
- Create specialized Marvin agents
- Enhance Prince Flowers with Marvin
- Add intelligent query routing

**Deliverables:**
```python
# Specialized agents
spec_analyzer = marvin.Agent(
    name="Spec Analyzer",
    instructions="Analyze specifications thoroughly"
)

code_reviewer = marvin.Agent(
    name="Code Reviewer",
    instructions="Review code for quality and security"
)

# Enhanced Prince Flowers
class MarvinPrinceFlowers:
    def __init__(self):
        self.classifier = marvin.classify
        self.spec_agent = spec_analyzer
        self.code_agent = code_reviewer
```

**Tasks:**
1. Create specialized Marvin agents
2. Integrate agents with TORQ workflows
3. Add query classification
4. Implement intelligent routing
5. Test agent coordination

### Phase 4: Production Optimization (Week 7-8)

**Objectives:**
- Performance tuning
- Comprehensive testing
- Documentation

**Deliverables:**
- Production-ready Marvin integration
- Full test coverage
- User documentation
- Migration guide

**Tasks:**
1. Performance optimization
2. Error handling edge cases
3. Comprehensive test suite
4. API documentation
5. User guides and examples

---

## 8. Benefits Analysis

### 8.1 Immediate Benefits

**1. Structured Outputs**
- Type-safe results from AI operations
- Automatic validation with Pydantic
- No manual parsing required

**2. Better Data Extraction**
- Extract structured info from unstructured text
- Native support for complex types
- Reliable, repeatable extractions

**3. Intelligent Classification**
- Automatic query/intent classification
- Smart routing to appropriate handlers
- Reduced manual condition logic

**4. Enhanced Spec-Kit**
- AI-powered specification analysis
- Structured requirement extraction
- Type-safe task planning

**5. Simpler Code**
- Less boilerplate
- More declarative
- Easier to maintain

### 8.2 Long-Term Benefits

**1. Better User Experience**
- More accurate responses
- Consistent output format
- Predictable behavior

**2. Improved Reliability**
- Type safety catches errors early
- Validation prevents bad data
- Easier debugging

**3. Faster Development**
- Less code to write
- Reusable agents and tasks
- Clear patterns

**4. Better Integration**
- Pydantic AI supports all LLM providers
- Easy to switch models
- Compatible with existing tools

**5. Future-Proof**
- Marvin is actively developed
- Backed by Prefect
- Strong community

---

## 9. Comparison: Current vs. With Marvin

| Aspect | Current TORQ | With Marvin | Improvement |
|--------|-------------|-------------|-------------|
| **Structured Outputs** | Manual parsing | Native Pydantic | ⭐⭐⭐⭐⭐ |
| **Data Extraction** | Regex/manual | `marvin.extract` | ⭐⭐⭐⭐⭐ |
| **Classification** | Manual logic | `marvin.classify` | ⭐⭐⭐⭐⭐ |
| **Type Safety** | None | Full Pydantic | ⭐⭐⭐⭐⭐ |
| **Agent System** | Monolithic | Specialized | ⭐⭐⭐⭐ |
| **Code Complexity** | High | Low | ⭐⭐⭐⭐⭐ |
| **Maintainability** | Moderate | High | ⭐⭐⭐⭐⭐ |
| **LLM Support** | Limited | All Pydantic AI | ⭐⭐⭐⭐⭐ |
| **Observability** | Basic | Built-in | ⭐⭐⭐⭐ |
| **Learning Curve** | Medium | Low | ⭐⭐⭐⭐ |

**Overall Recommendation:** ⭐⭐⭐⭐⭐ **Strongly Recommended**

---

## 10. Risk Assessment

### 10.1 Potential Risks

**1. Additional Dependency**
- **Risk**: New dependency on Marvin
- **Mitigation**: Marvin is well-maintained, backed by Prefect, has strong community

**2. Learning Curve**
- **Risk**: Team needs to learn Marvin API
- **Mitigation**: Marvin has excellent docs, simple API, clear examples

**3. Migration Effort**
- **Risk**: Existing code needs updating
- **Mitigation**: Gradual migration, maintain backward compatibility, phased rollout

**4. Performance Impact**
- **Risk**: Additional processing overhead
- **Mitigation**: Benchmark before/after, optimize as needed, Marvin is lightweight

**5. LLM Provider Changes**
- **Risk**: Marvin uses Pydantic AI
- **Mitigation**: Pydantic AI supports all major providers, easy to configure

### 10.2 Risk Mitigation Strategy

1. **Start Small**: Begin with non-critical features
2. **Parallel Development**: Keep existing system while building Marvin integration
3. **Comprehensive Testing**: Test thoroughly before production
4. **Documentation**: Document everything for team
5. **Rollback Plan**: Maintain ability to rollback if needed

---

## 11. Code Examples

### 11.1 Basic Integration

```python
# torq_console/marvin_integration/__init__.py
"""
Marvin Integration for TORQ Console

Provides structured outputs, data extraction, classification,
and agentic workflows using Marvin 3.0.
"""

import marvin
from typing import Type, TypeVar, List, Any
from enum import Enum
from pydantic import BaseModel

T = TypeVar('T')

class TorqMarvinIntegration:
    """Main integration point for Marvin in TORQ Console."""

    def __init__(self, model: str = "anthropic/claude-sonnet-4-20250514"):
        """Initialize with default model."""
        self.model = model
        marvin.settings.default_model = model

    def extract(self, text: str, target_type: Type[T],
                instructions: str = None) -> List[T]:
        """Extract structured data from text."""
        return marvin.extract(text, target_type, instructions=instructions)

    def cast(self, text: str, target_type: Type[T],
             instructions: str = None) -> T:
        """Cast unstructured text to structured type."""
        return marvin.cast(text, target_type, instructions=instructions)

    def classify(self, text: str, labels: Type[Enum]) -> Enum:
        """Classify text into one of the predefined labels."""
        return marvin.classify(text, labels)

    def generate(self, target_type: Type[T], n: int,
                 instructions: str) -> List[T]:
        """Generate n instances of target_type."""
        return marvin.generate(target_type, n, instructions)

    def create_agent(self, name: str, instructions: str,
                     tools: List = None):
        """Create a specialized Marvin agent."""
        return marvin.Agent(
            name=name,
            instructions=instructions,
            tools=tools or [],
            model=self.model
        )
```

### 11.2 Enhanced Spec-Kit

```python
# torq_console/spec_kit/marvin_analyzer.py
"""
Marvin-powered Specification Analyzer

Uses Marvin for structured, type-safe specification analysis.
"""

from pydantic import BaseModel, Field
from typing import List
import marvin

class SpecificationAnalysis(BaseModel):
    """Structured specification analysis result."""
    clarity_score: float = Field(ge=0.0, le=1.0)
    completeness_score: float = Field(ge=0.0, le=1.0)
    feasibility_score: float = Field(ge=0.0, le=1.0)
    complexity_score: float = Field(ge=0.0, le=1.0)

    missing_requirements: List[str]
    ambiguous_sections: List[str]
    technical_risks: List[str]
    recommendations: List[str]

    confidence: float = Field(ge=0.0, le=1.0)

class MarvinSpecAnalyzer:
    """Analyze specifications using Marvin."""

    def __init__(self):
        self.analyzer_agent = marvin.Agent(
            name="Specification Analyzer",
            instructions="""You are an expert at analyzing software specifications.
            Provide thorough, actionable analysis focusing on:
            - Clarity: How well-defined are the requirements?
            - Completeness: Are all necessary aspects covered?
            - Feasibility: Is this technically achievable?
            - Complexity: How complex is the implementation?

            Identify specific issues and provide concrete recommendations."""
        )

    async def analyze(self, specification_text: str) -> SpecificationAnalysis:
        """Analyze specification and return structured results."""
        analysis = self.analyzer_agent.run(
            f"Analyze this specification:\n\n{specification_text}",
            result_type=SpecificationAnalysis
        )
        return analysis

    async def extract_requirements(self, specification_text: str) -> List[str]:
        """Extract specific requirements from specification."""
        requirements = marvin.extract(
            specification_text,
            str,
            instructions="Extract all specific requirements (must/should/shall statements)"
        )
        return requirements
```

### 11.3 Intelligent Query Router

```python
# torq_console/core/marvin_router.py
"""
Intelligent Query Router using Marvin classification.
"""

from enum import Enum
from typing import Callable, Dict
import marvin

class QueryIntent(Enum):
    """User query intents."""
    CREATE_SPECIFICATION = "create_specification"
    ANALYZE_SPECIFICATION = "analyze_specification"
    GENERATE_TASKS = "generate_tasks"
    WRITE_CODE = "write_code"
    REVIEW_CODE = "review_code"
    WEB_SEARCH = "web_search"
    CHAT = "chat"
    HELP = "help"

class MarvinQueryRouter:
    """Route queries using Marvin classification."""

    def __init__(self):
        self.handlers: Dict[QueryIntent, Callable] = {}

    def register_handler(self, intent: QueryIntent, handler: Callable):
        """Register a handler for an intent."""
        self.handlers[intent] = handler

    async def route(self, query: str) -> Any:
        """Classify query and route to appropriate handler."""
        # Classify query intent
        intent = marvin.classify(query, QueryIntent)

        # Get handler
        handler = self.handlers.get(intent)
        if not handler:
            raise ValueError(f"No handler registered for intent: {intent}")

        # Execute handler
        return await handler(query)
```

---

## 12. Success Metrics

### Performance Metrics
- ✅ Response accuracy: >90%
- ✅ Type safety: 100% (Pydantic validation)
- ✅ Extraction accuracy: >85%
- ✅ Classification accuracy: >90%

### Developer Experience Metrics
- ✅ Code reduction: 40-60% less boilerplate
- ✅ Development speed: 30% faster
- ✅ Bug reduction: 50% fewer parsing errors

### User Satisfaction Metrics
- ✅ Consistent output format
- ✅ Predictable behavior
- ✅ Better error messages

---

## 13. Conclusion

### Summary

Marvin 3.0 represents a **strategic opportunity** to transform TORQ Console's AI capabilities:

- **From**: Manual parsing, unstructured outputs, complex agent code
- **To**: Type-safe, structured outputs, simple, declarative code

### Key Takeaways

1. **Perfect Fit for TORQ**: Marvin's structured outputs and agentic workflows align perfectly with TORQ's needs
2. **Simpler than ControlFlow**: Marvin supersedes ControlFlow with a cleaner API
3. **Production Ready**: Marvin is mature, well-documented, actively developed
4. **Low Risk**: Gradual migration path, strong community support, maintained by Prefect

### Recommendation

**Proceed with Marvin integration using the 4-phase approach outlined above.**

Start with a 1-week proof of concept:
1. Install Marvin
2. Test structured outputs (extract/cast/classify/generate)
3. Test basic agent creation
4. Benchmark vs. current system

If POC is successful (expected), proceed with full integration.

**The combination of TORQ Console's Spec-Kit methodology, Enhanced RL systems, and Marvin's structured AI capabilities would create a uniquely powerful development tool.**

---

## 14. References

- **Marvin GitHub**: https://github.com/PrefectHQ/marvin
- **Marvin Docs**: https://askmarvin.ai/
- **Pydantic AI**: https://ai.pydantic.dev/
- **TORQ Console**: https://github.com/pilotwaffle/TORQ-CONSOLE

---

## Appendix A: Quick Start

```bash
# Install Marvin
pip install marvin

# Set API key
export OPENAI_API_KEY=your-key
# or
export ANTHROPIC_API_KEY=your-key

# Test basic functionality
python -c "
import marvin
result = marvin.extract('I have 10 apples and 5 oranges', int)
print(result)  # [10, 5]
"
```

---

## Appendix B: Dependencies

Marvin core dependencies:
- pydantic-ai >= 1.9.0
- pydantic[email] >= 2.10.6
- sqlalchemy[asyncio] >= 2.0.36
- rich >= 13.9.4
- aiosqlite >= 0.20.0

All compatible with TORQ Console's existing stack.

---

**End of Document**
