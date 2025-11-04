# ControlFlow Quick Start Guide for TORQ Console

**Get started with ControlFlow integration in 30 minutes**

---

## Prerequisites

```bash
# Install ControlFlow and Prefect
pip install controlflow prefect

# Verify installation
python -c "import controlflow; print(f'ControlFlow {controlflow.__version__} installed')"
```

---

## Step 1: Hello World Flow (5 minutes)

Create `test_controlflow_basic.py`:

```python
"""
Basic ControlFlow test for TORQ Console
"""
import controlflow as cf

# Define a simple agent
assistant = cf.Agent(
    name="TORQ Assistant",
    description="Helpful assistant for TORQ Console",
    model="claude-sonnet-4"  # or "gpt-4", "anthropic/claude-3-opus-20240229"
)

# Define a simple flow
@cf.flow
def hello_world():
    """Test basic ControlFlow functionality."""

    task = cf.Task(
        objective="Say hello and explain what you can do in TORQ Console",
        agents=[assistant],
        result_type=str
    )

    return task.result

# Run it
if __name__ == "__main__":
    print("Testing ControlFlow integration...")
    result = hello_world()
    print(f"\nResult:\n{result}")
```

**Run it:**
```bash
python test_controlflow_basic.py
```

---

## Step 2: Multi-Task Flow (10 minutes)

Create `test_controlflow_multi_task.py`:

```python
"""
Multi-task workflow demonstration
"""
import controlflow as cf
from pydantic import BaseModel
from typing import List

# Type-safe result models
class SearchResult(BaseModel):
    query: str
    findings: List[str]
    source_count: int

class Analysis(BaseModel):
    key_points: List[str]
    summary: str

class Report(BaseModel):
    title: str
    content: str
    confidence: float

# Define specialized agents
researcher = cf.Agent(
    name="Researcher",
    description="Expert at finding and organizing information",
    model="claude-sonnet-4"
)

analyst = cf.Agent(
    name="Analyst",
    description="Expert at analyzing information and extracting insights",
    model="claude-sonnet-4"
)

writer = cf.Agent(
    name="Writer",
    description="Expert at creating clear, comprehensive reports",
    model="claude-sonnet-4"
)

@cf.flow
def research_flow(topic: str):
    """
    Demonstration of multi-agent, multi-task workflow.
    """

    # Task 1: Research
    search_task = cf.Task(
        objective=f"Research the topic: {topic}. List key findings.",
        agents=[researcher],
        result_type=SearchResult,
        context={"topic": topic}
    )

    # Task 2: Analysis (depends on search)
    analysis_task = cf.Task(
        objective="Analyze the research findings and extract key insights",
        agents=[analyst],
        depends_on=[search_task],
        result_type=Analysis,
        context={"search_results": search_task.result}
    )

    # Task 3: Report writing (depends on analysis)
    report_task = cf.Task(
        objective="Create a comprehensive report from the analysis",
        agents=[writer],
        depends_on=[analysis_task],
        result_type=Report,
        context={
            "topic": topic,
            "search_results": search_task.result,
            "analysis": analysis_task.result
        }
    )

    return report_task.result

# Run it
if __name__ == "__main__":
    topic = "ControlFlow AI agent orchestration"

    print(f"Researching: {topic}")
    print("This will run 3 tasks in sequence with task dependencies...\n")

    result = research_flow(topic)

    print(f"\n{'='*60}")
    print(f"Final Report:")
    print(f"{'='*60}")
    print(f"Title: {result.title}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"\nContent:\n{result.content}")
```

**Run it:**
```bash
python test_controlflow_multi_task.py
```

---

## Step 3: Integrate with Existing TORQ Agent (15 minutes)

Create `test_controlflow_torq_integration.py`:

```python
"""
Integration of ControlFlow with existing TORQ Console agents
"""
import controlflow as cf
import asyncio
from typing import Dict, Any

# Import existing TORQ components
import sys
sys.path.append('/home/user/TORQ-CONSOLE')

from torq_console.agents.prince_flowers_agent import PrinceFlowersAgent

# Create ControlFlow wrapper for Prince Flowers Agent
class PrinceFlowersCFAgent(cf.Agent):
    """ControlFlow wrapper for Prince Flowers Agent."""

    def __init__(self):
        super().__init__(
            name="Prince Flowers",
            description="Advanced agentic RL agent with web search and research capabilities",
            instructions="""
            You are the Prince Flowers agent from TORQ Console.
            You have access to:
            - Web search capabilities
            - Content analysis
            - Research synthesis
            - Memory and learning systems
            """,
            model="claude-sonnet-4"
        )
        self.prince_agent = PrinceFlowersAgent()

    async def execute_task(self, task_description: str) -> Dict[str, Any]:
        """Execute a task using the Prince Flowers agent."""
        result = await self.prince_agent.process_query(task_description)
        return {
            "success": result.success,
            "content": result.content,
            "confidence": result.confidence,
            "tools_used": result.tools_used,
            "execution_time": result.execution_time
        }

# Create integrated flow
prince_cf_agent = PrinceFlowersCFAgent()

@cf.flow
def torq_research_flow(query: str):
    """
    Research flow using TORQ's Prince Flowers agent through ControlFlow.
    """

    task = cf.Task(
        objective=f"Research and provide comprehensive information about: {query}",
        agents=[prince_cf_agent],
        result_type=str
    )

    return task.result

# Run it
async def main():
    query = "Latest developments in AI agent orchestration frameworks"

    print(f"Query: {query}")
    print("Running through ControlFlow + Prince Flowers integration...\n")

    result = torq_research_flow(query)

    print(f"\n{'='*60}")
    print(f"Result:")
    print(f"{'='*60}")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

**Run it:**
```bash
python test_controlflow_torq_integration.py
```

---

## Step 4: Parallel Execution Demo

Create `test_controlflow_parallel.py`:

```python
"""
Demonstrate parallel task execution with ControlFlow
"""
import controlflow as cf
from pydantic import BaseModel
from typing import List
import time

class ResearchResult(BaseModel):
    topic: str
    summary: str
    key_points: List[str]

researcher = cf.Agent(
    name="Researcher",
    description="Research specialist",
    model="claude-sonnet-4"
)

@cf.flow
def parallel_research(topics: List[str]):
    """
    Research multiple topics in parallel.

    ControlFlow automatically parallelizes independent tasks!
    """

    # Create independent research tasks for each topic
    research_tasks = [
        cf.Task(
            objective=f"Research topic: {topic}. Provide summary and key points.",
            agents=[researcher],
            result_type=ResearchResult,
            context={"topic": topic}
        )
        for topic in topics
    ]

    # ControlFlow automatically runs these in parallel
    # No need for manual asyncio.gather!
    return [task.result for task in research_tasks]

if __name__ == "__main__":
    topics = [
        "ControlFlow framework",
        "Prefect orchestration",
        "Multi-agent systems",
        "AI workflow automation"
    ]

    print(f"Researching {len(topics)} topics in parallel...")
    start_time = time.time()

    results = parallel_research(topics)

    elapsed = time.time() - start_time

    print(f"\n{'='*60}")
    print(f"Completed {len(topics)} research tasks in {elapsed:.2f} seconds")
    print(f"{'='*60}\n")

    for result in results:
        print(f"\n📚 Topic: {result.topic}")
        print(f"   Summary: {result.summary[:100]}...")
        print(f"   Key Points: {len(result.key_points)} items")
```

**Run it:**
```bash
python test_controlflow_parallel.py
```

---

## Step 5: Add Prefect Monitoring

```python
"""
Enable Prefect monitoring for your flows
"""
import controlflow as cf
from prefect import serve

# Your existing flow
@cf.flow
def monitored_flow(query: str):
    task = cf.Task(
        objective=query,
        agents=[cf.Agent(name="Assistant", model="claude-sonnet-4")],
        result_type=str
    )
    return task.result

if __name__ == "__main__":
    # Option 1: Run with local monitoring
    print("Starting Prefect server...")
    print("Visit http://localhost:4200 to see the Prefect UI")

    # In a separate terminal:
    # prefect server start

    # Then run your flow
    result = monitored_flow("What is ControlFlow?")
    print(result)

    # Option 2: Deploy as a service
    # serve(monitored_flow)
```

**Start Prefect UI:**
```bash
# Terminal 1: Start Prefect server
prefect server start

# Terminal 2: Run your flow
python test_controlflow_monitored.py

# Open browser to http://localhost:4200 to see execution
```

---

## Next Steps

### Learn More

1. **ControlFlow Documentation**: https://controlflow.ai/
2. **Prefect Documentation**: https://docs.prefect.io/
3. **TORQ Integration Analysis**: `docs/CONTROLFLOW_INTEGRATION_ANALYSIS.md`

### Try These Examples

1. **Error Handling**
   ```python
   @cf.task(retries=3, retry_delay=2.0, timeout=30.0)
   def resilient_task():
       # Your task code
       pass
   ```

2. **Conditional Flows**
   ```python
   @cf.flow
   def conditional_flow(input_type: str):
       if input_type == "research":
           return research_workflow()
       elif input_type == "code":
           return code_workflow()
       else:
           return default_workflow()
   ```

3. **Dynamic Agent Selection**
   ```python
   @cf.flow
   def smart_flow(query: str):
       # Analyze query to select best agent
       analysis = analyze_query(query)

       # Select agent based on analysis
       if analysis.requires_code:
           agent = code_specialist
       elif analysis.requires_research:
           agent = research_specialist
       else:
           agent = general_agent

       task = cf.Task(objective=query, agents=[agent])
       return task.result
   ```

### Integration with TORQ Spec-Kit

```python
"""
Example: Integrate ControlFlow with TORQ Spec-Kit
"""
import controlflow as cf
from pydantic import BaseModel

class SpecAnalysis(BaseModel):
    clarity_score: float
    completeness_score: float
    recommendations: List[str]

class ImplementationPlan(BaseModel):
    tasks: List[Dict[str, Any]]
    milestones: List[Dict[str, Any]]

@cf.flow
def spec_kit_flow(specification: Dict[str, Any]):
    """Enhanced Spec-Kit workflow with ControlFlow."""

    # Task 1: Analyze specification
    analysis_task = cf.Task(
        objective="Analyze specification for clarity and completeness",
        agents=[spec_analyzer_agent],
        result_type=SpecAnalysis
    )

    # Task 2: Generate plan (depends on analysis)
    plan_task = cf.Task(
        objective="Generate implementation plan",
        agents=[planner_agent],
        depends_on=[analysis_task],
        result_type=ImplementationPlan
    )

    # Task 3: Risk assessment (parallel with planning)
    risk_task = cf.Task(
        objective="Assess project risks",
        agents=[risk_agent],
        depends_on=[analysis_task],
        result_type=RiskAssessment
    )

    return {
        "analysis": analysis_task.result,
        "plan": plan_task.result,
        "risks": risk_task.result
    }
```

---

## Troubleshooting

### Issue: API Key Not Found

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Or for OpenAI
export OPENAI_API_KEY="your-key-here"
```

### Issue: Import Errors

```bash
# Reinstall ControlFlow
pip install --upgrade controlflow prefect

# Check installation
pip list | grep -E "controlflow|prefect"
```

### Issue: Tasks Not Running in Parallel

Make sure tasks are truly independent (no `depends_on` relationships):

```python
# ✅ Will run in parallel
task1 = cf.Task("Independent task 1")
task2 = cf.Task("Independent task 2")

# ❌ Will run sequentially
task1 = cf.Task("Task 1")
task2 = cf.Task("Task 2", depends_on=[task1])
```

---

## Performance Tips

1. **Task Granularity**: Don't make tasks too small (overhead) or too large (no parallelization benefit)

2. **Agent Reuse**: Reuse agent instances when possible

3. **Type Hints**: Use Pydantic models for type-safe results

4. **Context**: Pass only necessary context to tasks

5. **Caching**: Use Prefect caching for expensive operations

---

## Get Help

- **ControlFlow GitHub Issues**: https://github.com/PrefectHQ/ControlFlow/issues
- **TORQ Console GitHub**: https://github.com/pilotwaffle/TORQ-CONSOLE/issues
- **Prefect Community**: https://prefect.io/slack

---

**You're ready to integrate ControlFlow with TORQ Console!** 🚀

See `docs/CONTROLFLOW_INTEGRATION_ANALYSIS.md` for comprehensive integration architecture and recommendations.
