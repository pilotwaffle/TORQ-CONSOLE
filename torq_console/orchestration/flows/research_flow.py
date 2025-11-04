"""
Research Workflow for TORQ Console ControlFlow Integration

Provides structured research workflows using ControlFlow.
"""

import logging
from typing import List, Dict, Any, Optional
import controlflow as cf

from ..agents.base_agents import (
    create_web_search_agent,
    create_analyst_agent,
    create_writer_agent
)
from ..tasks.base_tasks import SearchResult, AnalysisResult, ReportResult

logger = logging.getLogger(__name__)


@cf.flow(name="research_workflow")
def research_workflow(
    query: str,
    model: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> ReportResult:
    """
    Comprehensive research workflow using ControlFlow orchestration.

    This flow demonstrates:
    - Multiple specialized agents
    - Task dependencies
    - Type-safe results
    - Observable execution

    Args:
        query: Research query
        model: LLM model to use (optional)
        context: Additional context (optional)

    Returns:
        ReportResult with comprehensive research findings
    """
    context = context or {}
    logger.info(f"Starting research workflow for query: {query}")

    # Create specialized agents
    web_search_agent = create_web_search_agent(model)
    analyst_agent = create_analyst_agent(model)
    writer_agent = create_writer_agent(model)

    # Task 1: Web Search
    # Note: ControlFlow will handle the actual execution
    # We're defining what needs to be done, not how
    search_task = cf.Task(
        objective=f"Search the web for comprehensive information about: {query}",
        instructions="""
        1. Formulate effective search queries
        2. Search using available providers
        3. Retrieve top 5-10 relevant results
        4. Return results with titles, URLs, and snippets
        """,
        agents=[web_search_agent],
        result_type=SearchResult,
        context={"query": query, "max_results": context.get("max_results", 10)}
    )

    # Task 2: Content Analysis (depends on search)
    analysis_task = cf.Task(
        objective="Analyze the search results and extract key insights, themes, and assess source quality",
        instructions="""
        1. Review all search results
        2. Extract key themes and concepts
        3. Identify important insights
        4. Assess source quality and credibility
        5. Provide confidence score for your analysis
        """,
        agents=[analyst_agent],
        depends_on=[search_task],
        result_type=AnalysisResult,
        context={
            "search_results": search_task,
            "query": query
        }
    )

    # Task 3: Report Generation (depends on analysis)
    report_task = cf.Task(
        objective="Generate a comprehensive research report synthesizing all findings",
        instructions="""
        1. Create a well-structured report with clear sections
        2. Include an executive summary
        3. Synthesize information from all sources
        4. Cite sources appropriately
        5. Maintain objectivity and note uncertainties
        6. Format in markdown for readability
        """,
        agents=[writer_agent],
        depends_on=[analysis_task],
        result_type=ReportResult,
        context={
            "query": query,
            "search_results": search_task,
            "analysis": analysis_task
        }
    )

    # ControlFlow handles execution, dependencies, and error handling
    logger.info(f"Research workflow completed for query: {query}")
    return report_task.result


@cf.flow(name="parallel_research_workflow")
def parallel_research_workflow(
    queries: List[str],
    model: Optional[str] = None
) -> List[ReportResult]:
    """
    Execute multiple research workflows in parallel.

    Demonstrates ControlFlow's ability to parallelize independent tasks.

    Args:
        queries: List of research queries
        model: LLM model to use (optional)

    Returns:
        List of ReportResult for each query
    """
    logger.info(f"Starting parallel research for {len(queries)} queries")

    # Create agents (reused across all tasks)
    web_search_agent = create_web_search_agent(model)
    analyst_agent = create_analyst_agent(model)
    writer_agent = create_writer_agent(model)

    # Create independent research tasks for each query
    # ControlFlow automatically parallelizes these
    research_tasks = []

    for query in queries:
        # For each query, create the 3-task pipeline
        search_task = cf.Task(
            objective=f"Search for: {query}",
            agents=[web_search_agent],
            result_type=SearchResult,
            context={"query": query}
        )

        analysis_task = cf.Task(
            objective=f"Analyze results for: {query}",
            agents=[analyst_agent],
            depends_on=[search_task],
            result_type=AnalysisResult
        )

        report_task = cf.Task(
            objective=f"Generate report for: {query}",
            agents=[writer_agent],
            depends_on=[analysis_task],
            result_type=ReportResult
        )

        research_tasks.append(report_task)

    # ControlFlow automatically parallelizes independent task pipelines
    # No manual asyncio.gather needed!
    results = [task.result for task in research_tasks]

    logger.info(f"Parallel research completed for {len(queries)} queries")
    return results


@cf.flow(name="simple_research")
def simple_research_workflow(
    query: str,
    model: Optional[str] = None
) -> str:
    """
    Simplified research workflow that returns a single string result.

    Useful for quick research tasks that don't need structured output.

    Args:
        query: Research query
        model: LLM model to use (optional)

    Returns:
        String with research findings
    """
    logger.info(f"Starting simple research for query: {query}")

    # Create agents
    web_search_agent = create_web_search_agent(model)
    analyst_agent = create_analyst_agent(model)

    # Single task that handles search and analysis
    research_task = cf.Task(
        objective=f"Research and provide a concise summary about: {query}",
        instructions="""
        1. Search for relevant information
        2. Analyze key findings
        3. Provide a clear, concise summary (2-3 paragraphs)
        4. Include key facts and sources
        """,
        agents=[web_search_agent, analyst_agent],
        result_type=str
    )

    logger.info(f"Simple research completed for query: {query}")
    return research_task.result
