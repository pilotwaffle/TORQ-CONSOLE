# Marvin Quick Start Guide for TORQ Console

**Get started with Marvin integration in 15 minutes**

---

## Prerequisites

```bash
# Install Marvin
pip install marvin

# Set your API key (choose one)
export OPENAI_API_KEY="your-key-here"
# or
export ANTHROPIC_API_KEY="your-key-here"

# Verify installation
python -c "import marvin; print(f'Marvin installed successfully')"
```

---

## 1. Structured Outputs (5 minutes)

### Extract Data

```python
import marvin

# Extract numbers from text
prices = marvin.extract(
    "The laptop costs $1299 and the mouse is $29",
    int,
    instructions="extract USD amounts"
)
print(prices)  # [1299, 29]

# Extract emails
emails = marvin.extract(
    "Contact john@example.com or sales@company.com",
    str,
    instructions="extract email addresses"
)
print(emails)  # ['john@example.com', 'sales@company.com']
```

### Cast to Structured Types

```python
from pydantic import BaseModel
import marvin

class Address(BaseModel):
    street: str
    city: str
    zip_code: str

# Natural language → Structured data
address = marvin.cast(
    "I live at 123 Main Street in Springfield, 12345",
    Address
)
print(address)
# Address(street='123 Main Street', city='Springfield', zip_code='12345')
```

### Classify

```python
from enum import Enum
import marvin

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# Classify text into predefined categories
priority = marvin.classify(
    "The server is down and customers can't access the site!",
    Priority
)
print(priority)  # Priority.URGENT
```

### Generate

```python
import marvin

# Generate structured data
cities = marvin.generate(
    str,
    5,
    "major cities in California"
)
print(cities)
# ['Los Angeles', 'San Francisco', 'San Diego', 'San Jose', 'Sacramento']
```

---

## 2. Simple Tasks (3 minutes)

### Basic Task

```python
import marvin

# Run a simple task
poem = marvin.run("Write a haiku about programming")
print(poem)
```

### Task with Structured Output

```python
import marvin

# Get structured result
answer = marvin.run(
    "What is the answer to life, the universe, and everything?",
    result_type=int
)
print(answer)  # 42
```

### Task with Context

```python
import marvin

result = marvin.run(
    "Summarize the key points",
    context={"document": "Long document text here..."}
)
```

---

## 3. Specialized Agents (3 minutes)

### Create an Agent

```python
from marvin import Agent

# Create a specialized agent
poet = Agent(
    name="Poetry Master",
    instructions="Write creative, evocative poetry in various styles"
)

# Use the agent
haiku = poet.run("Write a haiku about AI")
print(haiku)
```

### Agent with Specific Model

```python
from marvin import Agent
from pydantic_ai.models.anthropic import AnthropicModel
import os

# Create agent with specific model
code_expert = Agent(
    name="Code Expert",
    instructions="Provide detailed code reviews and suggestions",
    model=AnthropicModel(
        model_name="claude-3-5-sonnet-latest",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
)

review = code_expert.run("Review this code: def foo(): pass")
```

---

## 4. Threads for Context (2 minutes)

### Basic Thread

```python
import marvin

# Maintain context across multiple tasks
with marvin.Thread() as thread:
    # Task 1
    topic = marvin.run("Suggest a topic for a blog post about AI")

    # Task 2 - has access to Task 1's context
    outline = marvin.run("Create an outline for that topic")

    # Task 3 - has access to both previous tasks
    intro = marvin.run("Write the introduction")

print(intro)
```

### Named Thread (for persistence)

```python
import marvin

# Create a named thread that can be recovered
with marvin.Thread(id="my-research-session"):
    marvin.run("Research AI safety")
    marvin.run("Summarize findings")

# Later, recover the same thread
with marvin.Thread(id="my-research-session"):
    # Has access to previous conversation
    marvin.run("Expand on the key risks")
```

---

## 5. Tools & Custom Functions (2 minutes)

### Add Tools to Tasks

```python
import subprocess
from pydantic import IPvAnyAddress
import marvin

def run_shell_command(command: list[str]) -> str:
    """Execute a shell command"""
    return subprocess.check_output(command).decode()

# Task with tools
task = marvin.Task(
    instructions="Find my current IP address",
    result_type=IPvAnyAddress,
    tools=[run_shell_command]
)

ip = task.run()
print(f"Your IP: {ip}")
```

---

## 6. TORQ Console Integration Examples

### Example 1: Structured Spec Analysis

```python
from pydantic import BaseModel
from typing import List
import marvin

class SpecAnalysis(BaseModel):
    clarity_score: float
    completeness_score: float
    missing_requirements: List[str]
    recommendations: List[str]

# Analyze specification
spec_text = """
User Authentication System:
- Users should be able to login
- Passwords should be secure
"""

analysis = marvin.cast(
    spec_text,
    SpecAnalysis,
    instructions="Analyze this software specification for quality"
)

print(f"Clarity: {analysis.clarity_score}")
print(f"Missing: {', '.join(analysis.missing_requirements)}")
```

### Example 2: Intent Classification

```python
from enum import Enum
import marvin

class UserIntent(Enum):
    CREATE_SPEC = "create_specification"
    ANALYZE_CODE = "analyze_code"
    WEB_SEARCH = "web_search"
    CHAT = "chat"

# Classify user intent
user_query = "Can you help me write a specification for a REST API?"
intent = marvin.classify(user_query, UserIntent)

print(intent)  # UserIntent.CREATE_SPEC

# Route based on intent
if intent == UserIntent.CREATE_SPEC:
    # Handle spec creation
    pass
elif intent == UserIntent.ANALYZE_CODE:
    # Handle code analysis
    pass
```

### Example 3: Extract Requirements

```python
import marvin

spec_text = """
The system must:
1. Support user authentication with JWT tokens
2. Provide RESTful API endpoints
3. Store data in PostgreSQL
4. Handle 1000 requests per second
5. Implement rate limiting
"""

# Extract specific requirements
requirements = marvin.extract(
    spec_text,
    str,
    instructions="Extract all functional requirements"
)

for i, req in enumerate(requirements, 1):
    print(f"{i}. {req}")
```

### Example 4: Code Review with Structured Output

```python
from pydantic import BaseModel
from typing import List
import marvin

class CodeIssue(BaseModel):
    severity: str  # "error", "warning", "info"
    description: str
    suggestion: str

class CodeReview(BaseModel):
    quality_score: float
    issues: List[CodeIssue]
    summary: str

code = """
def calculate(x, y):
    return x / y
"""

code_reviewer = marvin.Agent(
    name="Code Reviewer",
    instructions="Provide thorough code reviews"
)

review = code_reviewer.run(
    f"Review this code:\n\n{code}",
    result_type=CodeReview
)

print(f"Quality: {review.quality_score}/10")
for issue in review.issues:
    print(f"[{issue.severity}] {issue.description}")
```

---

## 7. Common Patterns

### Pattern 1: Extract → Validate → Process

```python
from pydantic import BaseModel, validator
import marvin

class GitCommit(BaseModel):
    message: str
    files: list[str]

    @validator('message')
    def message_must_be_present(cls, v):
        if not v:
            raise ValueError('Commit message cannot be empty')
        return v

# Extract structured data from natural language
user_input = "Commit auth.py and users.py with message 'fix login bug'"

commit = marvin.cast(user_input, GitCommit)

# Now safely use validated data
print(f"Committing {len(commit.files)} files: {commit.message}")
```

### Pattern 2: Classify → Route → Execute

```python
from enum import Enum
import marvin

class ActionType(Enum):
    FILE_OPERATION = "file_operation"
    GIT_OPERATION = "git_operation"
    WEB_SEARCH = "web_search"

# Classify action
action = marvin.classify("Search for Python tutorials", ActionType)

# Route to handler
handlers = {
    ActionType.FILE_OPERATION: handle_file_op,
    ActionType.GIT_OPERATION: handle_git_op,
    ActionType.WEB_SEARCH: handle_search,
}

result = handlers[action](query)
```

### Pattern 3: Research → Analyze → Report

```python
from pydantic import BaseModel
from typing import List
import marvin

class ResearchReport(BaseModel):
    topic: str
    key_findings: List[str]
    sources: List[str]
    summary: str

# Multi-step workflow with thread context
with marvin.Thread():
    # Step 1: Research
    research = marvin.run(
        "Research latest developments in AI agents",
        result_type=dict
    )

    # Step 2: Analyze (has access to research context)
    analysis = marvin.run(
        "Analyze the key trends from the research",
        result_type=List[str]
    )

    # Step 3: Generate report (has access to all previous context)
    report = marvin.run(
        "Generate a structured report",
        result_type=ResearchReport
    )

print(f"Report on: {report.topic}")
print(f"Key findings: {len(report.key_findings)}")
```

---

## 8. Best Practices

### ✅ DO:
- Use Pydantic models for structured outputs
- Leverage type safety wherever possible
- Create specialized agents for specific tasks
- Use threads to maintain context
- Add clear instructions to tasks
- Validate outputs with Pydantic validators

### ❌ DON'T:
- Parse string outputs manually when you can use structured types
- Create one generic agent for everything
- Ignore type safety - use `result_type` parameter
- Forget to handle validation errors
- Over-complicate - Marvin makes things simple!

---

## 9. Troubleshooting

### Issue: "No API key found"

```bash
# Set your API key
export OPENAI_API_KEY="your-key"
# or
export ANTHROPIC_API_KEY="your-key"

# Verify it's set
echo $OPENAI_API_KEY
```

### Issue: Import errors

```bash
# Reinstall Marvin
pip install --upgrade marvin

# Check version
python -c "import marvin; print(marvin.__version__)"
```

### Issue: Type validation errors

```python
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    # Add constraints
    score: float = Field(ge=0.0, le=1.0)

    # Add validators
    @validator('score')
    def validate_score(cls, v):
        if v < 0:
            return 0.0
        if v > 1.0:
            return 1.0
        return v
```

---

## 10. Next Steps

### Learn More
- **Comprehensive Analysis**: `docs/MARVIN_INTEGRATION_ANALYSIS.md`
- **Marvin Docs**: https://askmarvin.ai/
- **Pydantic AI**: https://ai.pydantic.dev/
- **Examples**: https://github.com/PrefectHQ/marvin/tree/main/examples

### Try These

1. **Structured Spec Analysis**
   - Create Pydantic models for specifications
   - Use `marvin.cast` for type-safe analysis
   - Extract requirements automatically

2. **Intelligent Query Routing**
   - Define intent enum
   - Use `marvin.classify` for routing
   - Create handlers for each intent

3. **Code Review Bot**
   - Create specialized code review agent
   - Define structured code review model
   - Integrate with git workflows

4. **Research Assistant**
   - Use threads for multi-step research
   - Extract structured findings
   - Generate formatted reports

---

## 11. Integration with TORQ Console

```python
# torq_console/marvin_integration/__init__.py
"""
Quick integration example for TORQ Console
"""

import marvin
from pydantic import BaseModel
from typing import List
from enum import Enum

# Configure Marvin for TORQ
marvin.settings.default_model = "anthropic/claude-sonnet-4-20250514"

# Define TORQ-specific models
class TorqSpecAnalysis(BaseModel):
    clarity: float
    completeness: float
    recommendations: List[str]

class TorqIntent(Enum):
    SPEC_CREATE = "spec_create"
    SPEC_ANALYZE = "spec_analyze"
    CODE_REVIEW = "code_review"
    RESEARCH = "research"

# Create TORQ-specific agents
spec_analyzer = marvin.Agent(
    name="TORQ Spec Analyzer",
    instructions="Analyze software specifications for TORQ Console users"
)

code_reviewer = marvin.Agent(
    name="TORQ Code Reviewer",
    instructions="Review code for TORQ Console users"
)

# Export for use in TORQ
__all__ = [
    'marvin',
    'TorqSpecAnalysis',
    'TorqIntent',
    'spec_analyzer',
    'code_reviewer'
]
```

---

**You're ready to use Marvin in TORQ Console!** 🚀

See `docs/MARVIN_INTEGRATION_ANALYSIS.md` for comprehensive integration architecture and detailed implementation plans.
