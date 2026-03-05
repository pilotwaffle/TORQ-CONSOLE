"""
Planner for the TORQ Agent Cognitive Loop.

Transforms reasoning into executable plans with structured steps.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from .models import (
    CognitiveLoopConfig,
    ExecutionPlan,
    ExecutionStep,
    IntentType,
    ReasoningPlan,
    SessionContext,
    StepStatus,
    ToolCategory,
)


logger = logging.getLogger(__name__)


class Planner:
    """
    Transforms reasoning plans into executable execution plans.

    The planner breaks down the intent into concrete steps, identifies
    required tools, and estimates execution time.
    """

    def __init__(self, config: CognitiveLoopConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.Planner")

        # Tool catalog for planning
        self._tool_catalog = self._build_tool_catalog()

    def _build_tool_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Build catalog of available tools for planning."""
        return {
            "web_search": {
                "description": "Search the web for information",
                "category": ToolCategory.WEB_SEARCH,
                "parameters": ["query", "num_results"],
                "estimated_duration": 2.0,
            },
            "database": {
                "description": "Query database for structured data",
                "category": ToolCategory.DATABASE,
                "parameters": ["query", "table"],
                "estimated_duration": 0.5,
            },
            "file_read": {
                "description": "Read file contents",
                "category": ToolCategory.FILE_OPERATIONS,
                "parameters": ["path"],
                "estimated_duration": 0.3,
            },
            "file_write": {
                "description": "Write content to a file",
                "category": ToolCategory.FILE_OPERATIONS,
                "parameters": ["path", "content"],
                "estimated_duration": 0.3,
            },
            "code_execution": {
                "description": "Execute code snippet",
                "category": ToolCategory.CODE_EXECUTION,
                "parameters": ["code", "language"],
                "estimated_duration": 1.0,
            },
            "api_call": {
                "description": "Make an HTTP API request",
                "category": ToolCategory.API_CALL,
                "parameters": ["url", "method"],
                "estimated_duration": 1.5,
            },
            "document_generation": {
                "description": "Generate a document or report",
                "category": ToolCategory.DOCUMENT_GENERATION,
                "parameters": ["content", "format"],
                "estimated_duration": 1.0,
            },
            "data_analysis": {
                "description": "Analyze data and generate insights",
                "category": ToolCategory.DATA_ANALYSIS,
                "parameters": ["data", "analysis_type"],
                "estimated_duration": 2.0,
            },
        }

    async def plan(
        self,
        reasoning_plan: ReasoningPlan,
        query: str,
        session_context: Optional[SessionContext] = None,
        **kwargs
    ) -> ExecutionPlan:
        """
        Create an execution plan based on the reasoning.

        Args:
            reasoning_plan: The output from the reasoning phase
            query: The original user query
            session_context: Current session context
            **kwargs: Additional context

        Returns:
            ExecutionPlan with structured steps
        """
        start_time = time.time()

        # Determine the goal
        goal = self._derive_goal(query, reasoning_plan)

        # Generate execution steps
        steps = await self._generate_steps(reasoning_plan, query, session_context)

        # Calculate execution order
        self._calculate_execution_order(steps)

        # Determine required tools
        required_tools = list(set(s.tool_name for s in steps if s.tool_name))

        # Estimate outputs
        expected_outputs = self._estimate_outputs(reasoning_plan, steps)

        # Calculate total estimated duration
        total_duration = sum(s.estimated_duration_seconds for s in steps)

        # Determine if parallel execution is beneficial
        requires_parallel = (
            self.config.enable_parallel_execution and
            len(steps) > 2 and
            self._can_parallelize(steps)
        )

        planning_time = time.time() - start_time

        execution_plan = ExecutionPlan(
            goal=goal,
            steps=steps,
            required_tools=required_tools,
            expected_outputs=expected_outputs,
            estimated_duration_seconds=total_duration,
            requires_parallel_execution=requires_parallel,
            metadata={
                "planning_time_seconds": planning_time,
                "num_steps": len(steps),
                "reasoning_intent": reasoning_plan.intent.value,
            }
        )

        self.logger.debug(
            f"Created execution plan with {len(steps)} steps, "
            f"estimated duration: {total_duration:.2f}s"
        )

        return execution_plan

    def _derive_goal(self, query: str, reasoning_plan: ReasoningPlan) -> str:
        """Derive a clear goal statement from the query and reasoning."""
        # Extract the main action/objective
        intent_goals = {
            IntentType.QUERY: "Provide accurate information",
            IntentType.TASK: "Complete the requested task",
            IntentType.ANALYSIS: "Analyze and provide insights",
            IntentType.GENERATION: "Generate requested content",
            IntentType.RESEARCH: "Research and present findings",
            IntentType.UNKNOWN: "Address the user's request",
        }

        base_goal = intent_goals.get(reasoning_plan.intent, "Fulfill the request")

        # Add specificity based on query
        if reasoning_plan.key_concepts:
            concepts_str = ", ".join(reasoning_plan.key_concepts[:3])
            return f"{base_goal} about {concepts_str}"

        return base_goal

    async def _generate_steps(
        self,
        reasoning_plan: ReasoningPlan,
        query: str,
        session_context: Optional[SessionContext]
    ) -> List[ExecutionStep]:
        """Generate execution steps based on reasoning."""
        steps = []

        # Add suggested tools from reasoning
        for tool_name in reasoning_plan.suggested_tools:
            step = await self._create_tool_step(tool_name, reasoning_plan, query)
            if step:
                steps.append(step)

        # Add intent-specific steps
        steps.extend(await self._generate_intent_steps(reasoning_plan, query))

        # Add a final synthesis step if needed
        if len(steps) > 1:
            steps.append(ExecutionStep(
                description="Synthesize results from all steps",
                tool_name="synthesis",
                tool_category=ToolCategory.CUSTOM,
                parameters={"query": query},
                execution_order=len(steps),
                estimated_duration_seconds=0.5,
            ))

        # Limit steps if needed
        if len(steps) > self.config.max_plan_steps:
            steps = steps[:self.config.max_plan_steps]

        return steps

    async def _create_tool_step(
        self,
        tool_name: str,
        reasoning_plan: ReasoningPlan,
        query: str
    ) -> Optional[ExecutionStep]:
        """Create an execution step for a tool."""
        if tool_name not in self._tool_catalog:
            return None

        tool_info = self._tool_catalog[tool_name]

        # Generate parameters based on reasoning
        parameters = self._generate_tool_parameters(
            tool_name, reasoning_plan, query
        )

        return ExecutionStep(
            description=tool_info["description"],
            tool_name=tool_name,
            tool_category=tool_info["category"],
            parameters=parameters,
            estimated_duration_seconds=tool_info["estimated_duration"],
        )

    def _generate_tool_parameters(
        self,
        tool_name: str,
        reasoning_plan: ReasoningPlan,
        query: str
    ) -> Dict[str, Any]:
        """Generate parameters for a tool based on reasoning."""
        parameters = {}

        if tool_name == "web_search":
            # Extract search query from original query
            search_query = query
            if reasoning_plan.key_entities:
                search_query = " ".join(reasoning_plan.key_entities[:3])
            parameters = {
                "query": search_query,
                "num_results": 5,
            }

        elif tool_name == "database":
            parameters = {
                "query": f"SELECT * FROM relevant_data WHERE topic LIKE '%{reasoning_plan.intent.value}%'",
                "table": "knowledge_base",
            }

        elif tool_name == "file_read":
            # Try to extract file path from entities
            file_path = next(
                (e for e in reasoning_plan.key_entities if e.endswith((".txt", ".md", ".json"))),
                "unknown.txt"
            )
            parameters = {"path": file_path}

        elif tool_name == "document_generation":
            parameters = {
                "content": query,
                "format": "markdown",
            }

        elif tool_name == "data_analysis":
            parameters = {
                "analysis_type": reasoning_plan.intent.value,
                "metrics": ["accuracy", "completeness", "relevance"],
            }

        return parameters

    async def _generate_intent_steps(
        self,
        reasoning_plan: ReasoningPlan,
        query: str
    ) -> List[ExecutionStep]:
        """Generate steps specific to the detected intent."""
        steps = []

        if reasoning_plan.intent == IntentType.QUERY:
            # Query might need information retrieval
            if "web_search" not in reasoning_plan.suggested_tools:
                steps.append(ExecutionStep(
                    description="Access knowledge base for query response",
                    tool_name="knowledge_query",
                    tool_category=ToolCategory.DATABASE,
                    parameters={"query": query},
                    estimated_duration_seconds=0.5,
                ))

        elif reasoning_plan.intent == IntentType.TASK:
            # Task needs execution tracking
            steps.append(ExecutionStep(
                description="Validate task requirements",
                tool_name="validation",
                tool_category=ToolCategory.CUSTOM,
                parameters={"task": query},
                estimated_duration_seconds=0.2,
            ))

        elif reasoning_plan.intent == IntentType.ANALYSIS:
            # Analysis needs data gathering first
            if "data_analysis" not in reasoning_plan.suggested_tools:
                steps.append(ExecutionStep(
                    description="Gather data for analysis",
                    tool_name="data_collection",
                    tool_category=ToolCategory.DATA_ANALYSIS,
                    parameters={"topic": query},
                    estimated_duration_seconds=1.0,
                ))

        elif reasoning_plan.intent == IntentType.RESEARCH:
            # Research needs comprehensive search
            if "web_search" not in reasoning_plan.suggested_tools:
                steps.append(ExecutionStep(
                    description="Conduct comprehensive research search",
                    tool_name="web_search",
                    tool_category=ToolCategory.WEB_SEARCH,
                    parameters={"query": query, "num_results": 10},
                    estimated_duration_seconds=3.0,
                ))

        return steps

    def _calculate_execution_order(self, steps: List[ExecutionStep]):
        """Calculate execution order and dependencies for steps."""
        for i, step in enumerate(steps):
            step.execution_order = i

            # Set dependencies based on step type
            if step.tool_name == "synthesis":
                # Synthesis depends on all previous steps
                step.dependencies = [s.id for s in steps if s != step]
            elif i > 0:
                # By default, each step depends on the previous one
                # This can be optimized for parallel execution
                previous_step = steps[i - 1]
                if previous_step.tool_category != step.tool_category:
                    step.dependencies.append(previous_step.id)

    def _can_parallelize(self, steps: List[ExecutionStep]) -> bool:
        """Check if steps can be executed in parallel."""
        # Steps can be parallelized if they don't depend on each other
        # and are in different categories
        categories = set(s.tool_category for s in steps)
        return len(categories) > 1

    def _estimate_outputs(
        self,
        reasoning_plan: ReasoningPlan,
        steps: List[ExecutionStep]
    ) -> List[str]:
        """Estimate what outputs the plan will produce."""
        outputs = []

        for step in steps:
            if step.tool_name == "web_search":
                outputs.append("Search results with relevant information")
            elif step.tool_name == "database":
                outputs.append("Structured data from database")
            elif step.tool_name == "document_generation":
                outputs.append("Generated document or report")
            elif step.tool_name == "data_analysis":
                outputs.append("Analysis results and insights")
            elif step.tool_name == "synthesis":
                outputs.append("Synthesized response combining all results")

        # Add intent-specific outputs
        if reasoning_plan.intent == IntentType.QUERY:
            outputs.append("Direct answer to the query")
        elif reasoning_plan.intent == IntentType.TASK:
            outputs.append("Task completion confirmation")

        return list(set(outputs))

    async def refine_plan(
        self,
        plan: ExecutionPlan,
        feedback: str
    ) -> ExecutionPlan:
        """
        Refine an execution plan based on feedback.

        Args:
            plan: The current execution plan
            feedback: Feedback for refinement

        Returns:
            Refined execution plan
        """
        # Create a copy of the plan
        refined_plan = ExecutionPlan(
            goal=plan.goal,
            steps=[s for s in plan.steps],  # Shallow copy
            required_tools=plan.required_tools.copy(),
            expected_outputs=plan.expected_outputs.copy(),
            estimated_duration_seconds=plan.estimated_duration_seconds,
            requires_parallel_execution=plan.requires_parallel_execution,
            metadata={**plan.metadata, "refined": True},
        )

        # Adjust based on feedback
        feedback_lower = feedback.lower()

        if "more detailed" in feedback_lower or "comprehensive" in feedback_lower:
            # Add more detail-oriented steps
            refined_plan.estimated_duration_seconds *= 1.5

        if "faster" in feedback_lower or "quick" in feedback_lower:
            # Reduce estimated time and maybe skip some steps
            refined_plan.estimated_duration_seconds *= 0.7

        if "use" in feedback_lower:
            # Try to add requested tool
            for tool_name in self._tool_catalog:
                if tool_name in feedback_lower and tool_name not in refined_plan.required_tools:
                    tool_info = self._tool_catalog[tool_name]
                    refined_plan.steps.append(ExecutionStep(
                        description=f"Use {tool_name} as requested",
                        tool_name=tool_name,
                        tool_category=tool_info["category"],
                        parameters={},
                        estimated_duration_seconds=tool_info["estimated_duration"],
                    ))
                    refined_plan.required_tools.append(tool_name)
                    break

        return refined_plan

    async def emit_telemetry(
        self,
        phase: str,
        data: Dict[str, Any],
        run_id: Optional[str] = None
    ):
        """Emit telemetry for the planning phase."""
        if not self.config.telemetry_enabled:
            return

        try:
            from torq_console.core.telemetry.event import create_system_event
            from torq_console.core.telemetry.integration import get_telemetry_integration

            integration = get_telemetry_integration()
            await integration.record_agent_run(
                agent_name="planner",
                agent_type="cognitive_loop",
                status="started",
                run_id=run_id,
                **{f"plan.{k}": v for k, v in data.items()}
            )
        except Exception as e:
            self.logger.warning(f"Failed to emit telemetry: {e}")
