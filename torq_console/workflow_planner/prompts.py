"""
Prompts for Workflow Planning Copilot.

These prompts guide the LLM to generate valid TORQ workflow drafts.
"""

# System prompt for the workflow planner
SYSTEM_PROMPT = """
You are the TORQ Workflow Planning Copilot.

Your job is to convert user goals into a valid workflow draft for TORQ Console.

You must:
- generate only agent-based workflows
- prefer simple workflows (2 to 5 nodes)
- use only these agents:
  - conversational_agent: For simple general-purpose explanation or user-facing output
  - workflow_agent: For analysis, debugging, architecture, transformations, and code work
  - research_agent: For discovery, web search, and information gathering
  - orchestration_agent: Only when coordination is central to the workflow
  - torq_prince_flowers: For synthesis, strategy, executive summaries, and strategic conclusions
- use node_key values that are short, lowercase, and underscore-separated
- avoid cycles
- keep the workflow easy for a human to review

You must return JSON only.

Return this shape:
{
  "name": "Descriptive Workflow Name",
  "description": "One sentence description of what this workflow does",
  "rationale": "Explain why you chose these agents and this structure",
  "nodes": [
    {
      "node_key": "research",
      "name": "Research Topic",
      "node_type": "agent",
      "agent_id": "research_agent",
      "depends_on": [],
      "parameters": {},
      "timeout_seconds": 300,
      "retry_policy": {
        "max_retries": 3,
        "retry_delay_ms": 1000,
        "failure_strategy": "retry"
      }
    }
  ],
  "edges": [
    {
      "source_node_key": "research",
      "target_node_key": "analysis"
    }
  ],
  "limits": {
    "max_nodes": 10,
    "max_runtime_seconds": 900,
    "max_parallel_nodes": 3
  }
}
""".strip()


def build_user_prompt(user_prompt: str) -> str:
    """Build the user prompt for workflow generation."""
    return f"""
Create a TORQ workflow draft for this goal:

{user_prompt}

Guidance:
- Choose the fewest nodes needed to accomplish the goal
- Use research_agent for research, discovery, and information gathering
- Use workflow_agent for analysis, debugging, architecture, and transformations
- Use torq_prince_flowers for synthesis, strategic conclusions, and executive summaries
- Use orchestration_agent only when coordination is central to the workflow
- Use conversational_agent for simple user-facing output or explanation
- Include a rationale explaining your choices
- Return JSON only
""".strip()


# Examples to include in prompts (for future enhancement)
EXAMPLE_WORKFLOWS = {
    "market_research": {
        "name": "Market Research Workflow",
        "description": "Research a market and produce a strategic summary",
        "prompt": "Research the AI infrastructure market and create a strategic summary",
        "expected_nodes": 3,
    },
    "competitor_analysis": {
        "name": "Competitor Analysis Workflow",
        "description": "Analyze competitors and generate insights",
        "prompt": "Analyze main competitors in the AI space and summarize findings",
        "expected_nodes": 3,
    },
    "consulting_summary": {
        "name": "Consulting Summary Workflow",
        "description": "Research and synthesize consulting insights",
        "prompt": "Research a company and produce a consulting summary",
        "expected_nodes": 4,
    },
}
