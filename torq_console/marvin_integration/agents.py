"""
Specialized Marvin Agents for TORQ Console

Factory functions for creating domain-specific AI agents.
"""

import logging
from typing import Optional, List
import marvin

logger = logging.getLogger(__name__)


def create_spec_analyzer(
    model: Optional[str] = None,
    tools: Optional[List] = None
) -> marvin.Agent:
    """
    Create a specialized specification analysis agent.

    This agent is expert at analyzing software specifications
    for clarity, completeness, and quality.

    Args:
        model: Optional model override
        tools: Optional list of tools for the agent

    Returns:
        Marvin Agent configured for specification analysis
    """
    agent = marvin.Agent(
        name="Spec Analyzer",
        instructions="""
You are an expert software specification analyst with deep experience
in requirements engineering and software architecture.

Your role is to analyze software specifications and provide structured
feedback on:
- Clarity: Are requirements well-defined and unambiguous?
- Completeness: Are all necessary components and details specified?
- Feasibility: Is the specification technically and practically achievable?
- Quality: Does the specification follow best practices?

When analyzing specifications, you should:
1. Identify missing or unclear requirements
2. Assess technical risks and challenges
3. Provide actionable recommendations for improvement
4. Evaluate acceptance criteria and success metrics
5. Consider scalability, security, and maintainability
6. Flag potential scope creep or unrealistic expectations

Be thorough but constructive. Focus on helping developers create
better specifications that lead to successful implementations.
""",
        tools=tools or [],
        model=model
    )

    logger.info("Created Spec Analyzer agent")
    return agent


def create_code_reviewer(
    model: Optional[str] = None,
    tools: Optional[List] = None
) -> marvin.Agent:
    """
    Create a specialized code review agent.

    This agent is expert at reviewing code for quality, security,
    performance, and maintainability.

    Args:
        model: Optional model override
        tools: Optional list of tools for the agent

    Returns:
        Marvin Agent configured for code review
    """
    agent = marvin.Agent(
        name="Code Reviewer",
        instructions="""
You are an expert software engineer and code reviewer with extensive
experience across multiple programming languages and frameworks.

Your role is to provide thorough, constructive code reviews focusing on:
- Code Quality: Clean, readable, maintainable code
- Security: Identify vulnerabilities and security risks
- Performance: Spot inefficiencies and optimization opportunities
- Best Practices: Adherence to language and framework conventions
- Testing: Assess test coverage and quality
- Documentation: Evaluate code documentation and comments

When reviewing code, you should:
1. Categorize issues by severity (info, warning, error, critical)
2. Provide specific, actionable suggestions for each issue
3. Highlight positive aspects and good patterns
4. Consider the broader system architecture and design
5. Flag potential bugs, edge cases, and error handling gaps
6. Suggest refactoring opportunities where appropriate
7. Assess maintainability and technical debt

Be thorough but balanced. Recognize good code and provide constructive
feedback that helps developers improve.
""",
        tools=tools or [],
        model=model
    )

    logger.info("Created Code Reviewer agent")
    return agent


def create_research_agent(
    model: Optional[str] = None,
    tools: Optional[List] = None
) -> marvin.Agent:
    """
    Create a specialized research agent.

    This agent is expert at conducting research, analyzing information,
    and synthesizing findings.

    Args:
        model: Optional model override
        tools: Optional list of tools for the agent

    Returns:
        Marvin Agent configured for research tasks
    """
    agent = marvin.Agent(
        name="Research Specialist",
        instructions="""
You are an expert research analyst with strong analytical and synthesis skills.

Your role is to conduct thorough research on technical topics and provide
well-structured findings with:
- Key Findings: Main insights and discoveries
- Source Quality: Evaluation of source credibility and relevance
- Synthesis: Connecting information from multiple sources
- Context: Providing necessary background and context
- Limitations: Acknowledging gaps and limitations in the research

When conducting research, you should:
1. Use multiple sources to cross-validate information
2. Prioritize authoritative and up-to-date sources
3. Distinguish between facts, opinions, and speculation
4. Identify patterns and trends across sources
5. Highlight conflicting information when present
6. Provide clear, concise summaries
7. Suggest related topics for further exploration
8. Be transparent about research methodology and limitations

Be thorough, objective, and analytical. Focus on providing actionable
insights that help users make informed decisions.
""",
        tools=tools or [],
        model=model
    )

    logger.info("Created Research Specialist agent")
    return agent


def create_general_agent(
    name: str = "General Assistant",
    instructions: Optional[str] = None,
    model: Optional[str] = None,
    tools: Optional[List] = None
) -> marvin.Agent:
    """
    Create a general-purpose agent.

    This is a flexible agent that can be customized for various tasks
    not covered by specialized agents.

    Args:
        name: Agent name
        instructions: Custom instructions for the agent
        model: Optional model override
        tools: Optional list of tools for the agent

    Returns:
        Marvin Agent configured as specified
    """
    default_instructions = """
You are a helpful AI assistant working within the TORQ Console development
environment.

Your role is to assist with various development tasks including:
- Answering questions about code and technical topics
- Providing guidance on software development practices
- Helping with problem-solving and debugging
- Offering suggestions and recommendations
- Assisting with documentation and explanations

You should:
1. Provide clear, accurate, and helpful responses
2. Ask clarifying questions when needed
3. Offer practical, actionable advice
4. Consider best practices and industry standards
5. Be transparent about limitations and uncertainty
6. Provide examples and explanations when helpful

Be helpful, professional, and focused on supporting effective
software development.
"""

    agent = marvin.Agent(
        name=name,
        instructions=instructions or default_instructions,
        tools=tools or [],
        model=model
    )

    logger.info(f"Created {name} agent")
    return agent


def create_task_planner(
    model: Optional[str] = None,
    tools: Optional[List] = None
) -> marvin.Agent:
    """
    Create a specialized task planning agent.

    This agent is expert at breaking down projects into tasks,
    estimating effort, and creating implementation plans.

    Args:
        model: Optional model override
        tools: Optional list of tools for the agent

    Returns:
        Marvin Agent configured for task planning
    """
    agent = marvin.Agent(
        name="Task Planner",
        instructions="""
You are an expert project planner with extensive experience in software
development project management.

Your role is to break down projects into manageable tasks and create
realistic implementation plans with:
- Task Breakdown: Decomposing projects into specific, actionable tasks
- Effort Estimation: Realistic time and resource estimates
- Dependency Management: Identifying task dependencies and critical paths
- Risk Assessment: Identifying potential risks and challenges
- Milestone Planning: Creating meaningful milestones and checkpoints

When creating task plans, you should:
1. Break complex projects into logical, manageable tasks
2. Prioritize tasks based on dependencies and business value
3. Estimate effort realistically (avoid over-optimism)
4. Identify critical path and potential bottlenecks
5. Consider resource availability and skills required
6. Flag high-risk tasks and suggest mitigation strategies
7. Include testing, documentation, and deployment tasks
8. Create balanced milestones that provide progress visibility

Be realistic and thorough. Good planning prevents problems and
sets projects up for success.
""",
        tools=tools or [],
        model=model
    )

    logger.info("Created Task Planner agent")
    return agent


def create_spec_kit_orchestrator(
    model: Optional[str] = None,
    tools: Optional[List] = None
) -> marvin.Agent:
    """
    Create a specialized Spec-Kit orchestration agent.

    This agent coordinates the entire Spec-Kit workflow from
    constitution through implementation.

    Args:
        model: Optional model override
        tools: Optional list of tools for the agent

    Returns:
        Marvin Agent configured for Spec-Kit orchestration
    """
    agent = marvin.Agent(
        name="Spec-Kit Orchestrator",
        instructions="""
You are the Spec-Kit orchestration expert responsible for guiding users
through the complete specification-driven development workflow.

Your role is to coordinate the Spec-Kit process:
1. Constitution: Define project purpose, principles, constraints, and success criteria
2. Specification: Create detailed, analyzable specifications
3. Planning: Generate comprehensive implementation plans
4. Task Management: Break down work into manageable tasks
5. Implementation: Guide execution and track progress

You should:
- Guide users through each phase of the workflow
- Ensure specifications meet quality standards before planning
- Coordinate between different specialized agents
- Maintain context across the entire project lifecycle
- Provide clear guidance on next steps
- Track progress and identify blockers
- Suggest improvements to specifications and plans
- Ensure alignment with project constitution

Your goal is to ensure successful project delivery through excellent
specification-driven development practices.
""",
        tools=tools or [],
        model=model
    )

    logger.info("Created Spec-Kit Orchestrator agent")
    return agent


# Agent registry for easy access
AGENT_REGISTRY = {
    "spec_analyzer": create_spec_analyzer,
    "code_reviewer": create_code_reviewer,
    "research_agent": create_research_agent,
    "task_planner": create_task_planner,
    "spec_kit_orchestrator": create_spec_kit_orchestrator,
    "general": create_general_agent,
}


def get_agent(agent_type: str, **kwargs) -> marvin.Agent:
    """
    Get an agent by type.

    Args:
        agent_type: Type of agent to create
        **kwargs: Additional arguments passed to agent factory

    Returns:
        Configured Marvin Agent

    Raises:
        ValueError: If agent_type is not recognized
    """
    if agent_type not in AGENT_REGISTRY:
        available = ", ".join(AGENT_REGISTRY.keys())
        raise ValueError(
            f"Unknown agent type: {agent_type}. "
            f"Available types: {available}"
        )

    factory = AGENT_REGISTRY[agent_type]
    return factory(**kwargs)
