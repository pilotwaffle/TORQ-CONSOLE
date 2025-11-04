"""
Analysis Workflow for TORQ Console ControlFlow Integration

Provides structured analysis workflows using ControlFlow.
"""

import logging
from typing import Dict, Any, Optional
import controlflow as cf

from ..agents.base_agents import create_analyst_agent, create_code_agent
from ..tasks.base_tasks import AnalysisResult, CodeAnalysisResult

logger = logging.getLogger(__name__)


@cf.flow(name="analysis_workflow")
def analysis_workflow(
    content: str,
    analysis_type: str = "general",
    model: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> AnalysisResult:
    """
    General content analysis workflow.

    Args:
        content: Content to analyze
        analysis_type: Type of analysis (general, technical, business, etc.)
        model: LLM model to use (optional)
        context: Additional context (optional)

    Returns:
        AnalysisResult with structured analysis
    """
    context = context or {}
    logger.info(f"Starting {analysis_type} analysis workflow")

    # Create analyst agent
    analyst_agent = create_analyst_agent(model)

    # Analysis task
    analysis_task = cf.Task(
        objective=f"Perform {analysis_type} analysis on the provided content",
        instructions="""
        1. Review the content thoroughly
        2. Extract key themes and concepts
        3. Identify important insights
        4. Assess quality and credibility
        5. Provide confidence score for your analysis
        6. Summarize findings
        """,
        agents=[analyst_agent],
        result_type=AnalysisResult,
        context={
            "content": content,
            "analysis_type": analysis_type,
            **context
        }
    )

    logger.info(f"Analysis workflow completed")
    return analysis_task.result


@cf.flow(name="code_analysis_workflow")
def code_analysis_workflow(
    code: str,
    language: str = "python",
    model: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> CodeAnalysisResult:
    """
    Code analysis workflow using specialized code agent.

    Args:
        code: Code to analyze
        language: Programming language
        model: LLM model to use (optional)
        context: Additional context (optional)

    Returns:
        CodeAnalysisResult with structured code analysis
    """
    context = context or {}
    logger.info(f"Starting code analysis workflow for {language}")

    # Create code agent
    code_agent = create_code_agent(model)

    # Code analysis task
    code_analysis_task = cf.Task(
        objective=f"Analyze the provided {language} code for quality, issues, and improvements",
        instructions="""
        1. Review code structure and organization
        2. Identify bugs, issues, and potential problems
        3. Assess code quality (readability, maintainability, efficiency)
        4. Check for security issues
        5. Evaluate complexity
        6. Check for tests and documentation
        7. Provide actionable improvement suggestions
        8. Assign overall quality score
        """,
        agents=[code_agent],
        result_type=CodeAnalysisResult,
        context={
            "code": code,
            "language": language,
            **context
        }
    )

    logger.info(f"Code analysis workflow completed")
    return code_analysis_task.result


@cf.flow(name="comparative_analysis")
def comparative_analysis_workflow(
    item1: str,
    item2: str,
    comparison_type: str = "general",
    model: Optional[str] = None
) -> AnalysisResult:
    """
    Comparative analysis workflow for comparing two items.

    Args:
        item1: First item to compare
        item2: Second item to compare
        comparison_type: Type of comparison
        model: LLM model to use (optional)

    Returns:
        AnalysisResult with comparative analysis
    """
    logger.info(f"Starting comparative analysis: {comparison_type}")

    # Create analyst agent
    analyst_agent = create_analyst_agent(model)

    # Task 1: Analyze first item
    analysis1_task = cf.Task(
        objective=f"Analyze the first item: {item1[:50]}...",
        instructions="Analyze this item and extract key characteristics, strengths, and weaknesses.",
        agents=[analyst_agent],
        result_type=AnalysisResult,
        context={"item": item1}
    )

    # Task 2: Analyze second item (can run in parallel with task 1)
    analysis2_task = cf.Task(
        objective=f"Analyze the second item: {item2[:50]}...",
        instructions="Analyze this item and extract key characteristics, strengths, and weaknesses.",
        agents=[analyst_agent],
        result_type=AnalysisResult,
        context={"item": item2}
    )

    # Task 3: Compare both analyses (depends on both previous tasks)
    comparison_task = cf.Task(
        objective=f"Compare the two items and provide {comparison_type} comparative analysis",
        instructions="""
        1. Review both analyses
        2. Identify similarities and differences
        3. Compare strengths and weaknesses
        4. Provide overall comparison insights
        5. Make recommendations if applicable
        """,
        agents=[analyst_agent],
        depends_on=[analysis1_task, analysis2_task],
        result_type=AnalysisResult,
        context={
            "analysis1": analysis1_task,
            "analysis2": analysis2_task,
            "comparison_type": comparison_type
        }
    )

    logger.info(f"Comparative analysis completed")
    return comparison_task.result
