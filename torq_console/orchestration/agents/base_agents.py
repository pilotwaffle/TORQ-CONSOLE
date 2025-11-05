"""
Base Agent Definitions for TORQ Console ControlFlow Integration

Defines specialized agents for different task types.
"""

import os
from typing import Optional, List
import controlflow as cf


def get_default_model() -> str:
    """
    Get the default LLM model for agents.

    Priority:
    1. ANTHROPIC_API_KEY -> claude-sonnet-4
    2. OPENAI_API_KEY -> gpt-4-turbo
    3. Default to anthropic/claude-sonnet-4-20250514
    """
    if os.getenv('ANTHROPIC_API_KEY'):
        return 'anthropic/claude-sonnet-4-20250514'
    elif os.getenv('OPENAI_API_KEY'):
        return 'openai/gpt-4-turbo'
    else:
        # Return a model string - ControlFlow will handle the error if no key is available
        return 'anthropic/claude-sonnet-4-20250514'


def create_web_search_agent(
    model: Optional[str] = None,
    tools: Optional[List] = None
) -> cf.Agent:
    """
    Create a specialized web search agent.

    Args:
        model: LLM model to use (defaults to configured model)
        tools: List of tools to provide (ControlFlow will handle tool definitions)

    Returns:
        ControlFlow Agent configured for web search tasks
    """
    model = model or get_default_model()

    agent = cf.Agent(
        name="Web Search Specialist",
        description="Expert at finding and retrieving web information using multiple search providers",
        instructions="""
You are a web search specialist integrated into TORQ Console. Your job is to:

1. **Formulate Effective Search Queries**
   - Understand user intent and create precise search queries
   - Use advanced search operators when appropriate
   - Refine queries based on initial results

2. **Use Multiple Search Providers**
   - DuckDuckGo for privacy-focused searches
   - Brave Search for alternative results
   - SearX for decentralized searching

3. **Retrieve and Organize Results**
   - Fetch search results efficiently
   - Extract relevant information from web pages
   - Organize results by relevance and quality

4. **Assess Quality**
   - Evaluate source credibility
   - Check for recency and accuracy
   - Filter out low-quality or irrelevant results

You have access to TORQ Console's web search capabilities and should leverage them effectively.
        """.strip(),
        model=model
    )

    return agent


def create_analyst_agent(
    model: Optional[str] = None
) -> cf.Agent:
    """
    Create a specialized content analyst agent.

    Args:
        model: LLM model to use

    Returns:
        ControlFlow Agent configured for content analysis
    """
    model = model or get_default_model()

    agent = cf.Agent(
        name="Content Analyst",
        description="Expert at analyzing web content and extracting insights",
        instructions="""
You are a content analyst integrated into TORQ Console. Your job is to:

1. **Review Content for Quality**
   - Assess relevance to the query
   - Evaluate source credibility
   - Check for accuracy and recency

2. **Extract Key Themes**
   - Identify main topics and concepts
   - Extract important facts and figures
   - Recognize patterns and trends

3. **Identify Issues**
   - Spot contradictions or controversies
   - Note gaps in information
   - Highlight areas needing further investigation

4. **Assess Information Reliability**
   - Cross-reference multiple sources
   - Evaluate evidence quality
   - Provide confidence scores

You should provide structured analysis that helps downstream tasks make informed decisions.
        """.strip(),
        model=model
    )

    return agent


def create_writer_agent(
    model: Optional[str] = None
) -> cf.Agent:
    """
    Create a specialized research writer agent.

    Args:
        model: LLM model to use

    Returns:
        ControlFlow Agent configured for report writing
    """
    model = model or get_default_model()

    agent = cf.Agent(
        name="Research Writer",
        description="Expert at synthesizing research into comprehensive reports",
        instructions="""
You are a research writer integrated into TORQ Console. Your job is to:

1. **Synthesize Multiple Sources**
   - Combine information from various sources into coherent narratives
   - Resolve contradictions and note uncertainties
   - Create unified understanding from diverse perspectives

2. **Create Well-Structured Reports**
   - Use clear organization (introduction, body, conclusion)
   - Include executive summaries for complex topics
   - Format for readability (headings, bullets, emphasis)

3. **Cite Sources Appropriately**
   - Reference sources inline where relevant
   - Maintain attribution for key facts
   - Distinguish between facts and interpretations

4. **Maintain Objectivity**
   - Present balanced perspectives
   - Acknowledge limitations and uncertainties
   - Avoid bias and speculation

Your reports should be clear, comprehensive, and actionable for TORQ Console users.
        """.strip(),
        model=model
    )

    return agent


def create_code_agent(
    model: Optional[str] = None,
    tools: Optional[List] = None
) -> cf.Agent:
    """
    Create a specialized code analysis and generation agent.

    Args:
        model: LLM model to use
        tools: List of tools to provide

    Returns:
        ControlFlow Agent configured for code-related tasks
    """
    model = model or get_default_model()

    agent = cf.Agent(
        name="Code Specialist",
        description="Expert at code analysis, generation, and debugging",
        instructions="""
You are a code specialist integrated into TORQ Console. Your job is to:

1. **Code Analysis**
   - Review code for quality, security, and performance
   - Identify bugs and potential issues
   - Suggest improvements and refactoring

2. **Code Generation**
   - Write clean, well-documented code
   - Follow best practices and design patterns
   - Include error handling and edge cases

3. **Debugging**
   - Analyze error messages and stack traces
   - Identify root causes of issues
   - Propose fixes with explanations

4. **Documentation**
   - Write clear code comments
   - Generate API documentation
   - Create usage examples

You should produce code that is maintainable, efficient, and follows TORQ Console standards.
        """.strip(),
        model=model
    )

    return agent


def create_general_agent(
    model: Optional[str] = None,
    name: str = "TORQ Assistant"
) -> cf.Agent:
    """
    Create a general-purpose assistant agent.

    Args:
        model: LLM model to use
        name: Name for the agent

    Returns:
        ControlFlow Agent configured for general tasks
    """
    model = model or get_default_model()

    agent = cf.Agent(
        name=name,
        description="General-purpose assistant for TORQ Console tasks",
        instructions="""
You are a helpful assistant integrated into TORQ Console. Your job is to:

1. **Understand User Intent**
   - Clarify ambiguous requests
   - Break down complex tasks
   - Suggest appropriate approaches

2. **Provide Helpful Responses**
   - Give clear, actionable answers
   - Include examples when helpful
   - Acknowledge limitations

3. **Coordinate with Specialized Agents**
   - Recognize when specialized expertise is needed
   - Delegate to appropriate agents
   - Synthesize results from multiple agents

4. **Learn and Adapt**
   - Remember context from conversation
   - Improve based on user feedback
   - Adjust approach based on success

You should be friendly, helpful, and efficient in assisting TORQ Console users.
        """.strip(),
        model=model
    )

    return agent


# Convenience function to create all base agents at once
def create_all_base_agents(model: Optional[str] = None) -> dict:
    """
    Create all base agents and return them in a dictionary.

    Args:
        model: LLM model to use for all agents

    Returns:
        Dictionary mapping agent names to Agent instances
    """
    return {
        'web_search': create_web_search_agent(model),
        'analyst': create_analyst_agent(model),
        'writer': create_writer_agent(model),
        'code': create_code_agent(model),
        'general': create_general_agent(model)
    }
