"""
Planning engine for TORQ Prince Flowers agent.

This module provides strategic planning capabilities including:
- Task decomposition
- Multi-step planning
- Resource allocation
- Progress tracking
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class PlanningEngine:
    """Strategic planning engine for complex task execution."""

    def __init__(self):
        """Initialize the planning engine."""
        self.logger = logging.getLogger("PlanningEngine")
        self.active_plans = {}
        self.completed_plans = []

    async def create_plan(self, query: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a strategic plan for query execution.

        Args:
            query: The user's query
            analysis: Query analysis results

        Returns:
            Execution plan with steps and timeline
        """
        try:
            plan = {
                "plan_id": f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "query": query,
                "created_at": datetime.now(),
                "steps": self._decompose_task(query, analysis),
                "estimated_duration": self._estimate_plan_duration(analysis),
                "required_tools": analysis.get("tools_needed", []),
                "success_criteria": self._define_success_criteria(query),
                "risk_factors": self._identify_risks(query, analysis)
            }

            self.active_plans[plan["plan_id"]] = plan
            self.logger.info(f"Created plan {plan['plan_id']} with {len(plan['steps'])} steps")

            return plan

        except Exception as e:
            self.logger.error(f"Error creating plan: {e}")
            return {
                "plan_id": "fallback_plan",
                "steps": [{"step_id": "direct_execution", "description": "Execute directly", "estimated_time": 5.0}],
                "error": str(e)
            }

    def _decompose_task(self, query: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose a complex query into executable steps."""
        complexity = analysis.get("complexity", "medium")
        tools_needed = analysis.get("tools_needed", [])

        if complexity in ["low", "medium"]:
            return [
                {
                    "step_id": "direct_response",
                    "description": "Generate direct response",
                    "estimated_time": 5.0,
                    "tools": [],
                    "dependencies": []
                }
            ]

        # High complexity task decomposition
        steps = []
        step_counter = 1

        # Information gathering step (if research needed)
        if "web_search" in tools_needed:
            steps.append({
                "step_id": f"step_{step_counter}",
                "description": "Gather information from multiple sources",
                "estimated_time": 10.0,
                "tools": ["web_search"],
                "dependencies": []
            })
            step_counter += 1

        # Analysis step
        steps.append({
            "step_id": f"step_{step_counter}",
            "description": "Analyze gathered information and requirements",
            "estimated_time": 8.0,
            "tools": [],
            "dependencies": [f"step_{step_counter-1}"] if step_counter > 1 else []
        })
        step_counter += 1

        # Execution steps based on tools
        for tool in tools_needed:
            if tool not in ["web_search"]:
                steps.append({
                    "step_id": f"step_{step_counter}",
                    "description": f"Execute {tool} operation",
                    "estimated_time": self._get_tool_estimated_time(tool),
                    "tools": [tool],
                    "dependencies": []
                })
                step_counter += 1

        # Synthesis step
        steps.append({
            "step_id": f"step_{step_counter}",
            "description": "Synthesize results and generate final response",
            "estimated_time": 5.0,
            "tools": [],
            "dependencies": [s["step_id"] for s in steps[:-1]]
        })

        return steps

    def _estimate_plan_duration(self, analysis: Dict[str, Any]) -> float:
        """Estimate the total duration of the plan."""
        complexity = analysis.get("complexity", "medium")
        tools_needed = analysis.get("tools_needed", [])

        base_duration = {
            "low": 5.0,
            "medium": 15.0,
            "high": 30.0,
            "very_high": 60.0
        }.get(complexity, 15.0)

        # Add time for tools
        tool_durations = {
            "web_search": 10.0,
            "image_generation": 15.0,
            "file_operations": 5.0,
            "code_generation": 10.0,
            "browser_automation": 20.0
        }

        for tool in tools_needed:
            base_duration += tool_durations.get(tool, 5.0)

        return base_duration

    def _define_success_criteria(self, query: str) -> List[str]:
        """Define success criteria for the query."""
        return [
            "Response directly addresses the query",
            "Information is accurate and up-to-date",
            "Response is well-structured and clear",
            "User can take action based on the response"
        ]

    def _identify_risks(self, query: str, analysis: Dict[str, Any]) -> List[str]:
        """Identify potential risks in execution."""
        risks = []

        if analysis.get("requires_approval", False):
            risks.append("Operation requires user approval")

        if "terminal_commands" in analysis.get("tools_needed", []):
            risks.append("Terminal command execution carries security risks")

        if "file_operations" in analysis.get("tools_needed", []):
            risks.append("File operations may affect system state")

        return risks

    def _get_tool_estimated_time(self, tool: str) -> float:
        """Get estimated execution time for a specific tool."""
        tool_times = {
            "web_search": 10.0,
            "image_generation": 15.0,
            "file_operations": 5.0,
            "code_generation": 10.0,
            "browser_automation": 20.0,
            "terminal_commands": 8.0,
            "n8n_workflow": 12.0,
            "twitter_posting": 5.0,
            "linkedin_posting": 6.0,
            "landing_page_generator": 10.0
        }
        return tool_times.get(tool, 5.0)

    async def execute_plan_step(self, plan_id: str, step_id: str) -> Dict[str, Any]:
        """Execute a specific step in a plan."""
        try:
            if plan_id not in self.active_plans:
                raise ValueError(f"Plan {plan_id} not found")

            plan = self.active_plans[plan_id]
            step = None
            for s in plan["steps"]:
                if s["step_id"] == step_id:
                    step = s
                    break

            if not step:
                raise ValueError(f"Step {step_id} not found in plan {plan_id}")

            # Check dependencies
            if step["dependencies"]:
                for dep_id in step["dependencies"]:
                    # In a real implementation, we'd check if dependencies are complete
                    pass

            # Execute step (placeholder - actual execution would be handled by the main agent)
            result = {
                "step_id": step_id,
                "plan_id": plan_id,
                "status": "completed",
                "execution_time": step["estimated_time"],
                "tools_used": step["tools"],
                "result": f"Executed step: {step['description']}"
            }

            self.logger.info(f"Completed step {step_id} in plan {plan_id}")
            return result

        except Exception as e:
            self.logger.error(f"Error executing plan step {step_id}: {e}")
            return {
                "step_id": step_id,
                "plan_id": plan_id,
                "status": "failed",
                "error": str(e)
            }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the planning engine."""
        try:
            return {
                "healthy": True,
                "active_plans": len(self.active_plans),
                "completed_plans": len(self.completed_plans),
                "components": {
                    "task_decomposer": True,
                    "duration_estimator": True,
                    "risk_analyzer": True
                }
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }