"""
Planning Tools for TORQ Console - Claude Code Compatible ExitPlanMode.

Provides planning mode workflow and ExitPlanMode functionality for
structured task planning and user approval workflow integration.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PlanningPhase(Enum):
    """Planning workflow phases."""
    INITIAL = "initial"
    PLANNING = "planning"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"


@dataclass
class PlanStep:
    """Represents a single step in a plan."""
    step_id: str
    title: str
    description: str
    estimated_time: Optional[int] = None  # in minutes
    dependencies: List[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    confidence: float = 0.8
    risk_level: str = "low"  # low, medium, high
    tools_required: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tools_required is None:
            self.tools_required = []


@dataclass
class TaskPlan:
    """Represents a complete task plan."""
    plan_id: str
    task_description: str
    steps: List[PlanStep]
    phase: PlanningPhase = PlanningPhase.INITIAL
    created_at: datetime = None
    estimated_total_time: Optional[int] = None
    complexity_score: float = 0.5
    success_probability: float = 0.8
    risks: List[str] = None
    prerequisites: List[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.risks is None:
            self.risks = []
        if self.prerequisites is None:
            self.prerequisites = []


class PlanningTool:
    """
    Planning workflow tool with Claude Code ExitPlanMode compatibility.

    Features:
    - Structured task breakdown and planning
    - Risk assessment and complexity analysis
    - User approval workflow integration
    - Plan execution tracking and monitoring
    - Compatible with Claude Code planning patterns
    """

    def __init__(self, code_agent=None):
        self.logger = logging.getLogger(__name__)
        self.code_agent = code_agent

        # Planning state management
        self.active_plans: Dict[str, TaskPlan] = {}
        self.plan_counter = 0

        # Planning configuration
        self.default_confidence = 0.8
        self.complexity_thresholds = {
            'simple': 0.3,
            'moderate': 0.6,
            'complex': 0.8
        }

    async def create_plan(
        self,
        task_description: str,
        auto_breakdown: bool = True,
        include_risk_assessment: bool = True
    ) -> Dict[str, Any]:
        """
        Create a structured plan for a given task.

        Args:
            task_description: Description of the task to plan
            auto_breakdown: Whether to automatically break down the task
            include_risk_assessment: Whether to include risk analysis

        Returns:
            Dict with plan creation results
        """
        start_time = time.time()

        try:
            self.plan_counter += 1
            plan_id = f"plan_{self.plan_counter}_{int(time.time())}"

            # Create initial plan structure
            plan = TaskPlan(
                plan_id=plan_id,
                task_description=task_description,
                steps=[],
                phase=PlanningPhase.PLANNING
            )

            # Analyze task complexity
            complexity_analysis = await self._analyze_task_complexity(task_description)
            plan.complexity_score = complexity_analysis['complexity_score']
            plan.estimated_total_time = complexity_analysis['estimated_time']

            # Auto-breakdown if requested
            if auto_breakdown:
                breakdown_result = await self._breakdown_task(task_description)
                plan.steps = breakdown_result['steps']
                plan.prerequisites = breakdown_result.get('prerequisites', [])

            # Risk assessment
            if include_risk_assessment:
                risk_analysis = await self._assess_risks(plan)
                plan.risks = risk_analysis['risks']
                plan.success_probability = risk_analysis['success_probability']

            # Store the plan
            self.active_plans[plan_id] = plan

            processing_time = time.time() - start_time

            return {
                'success': True,
                'plan_id': plan_id,
                'task_description': task_description,
                'phase': plan.phase.value,
                'steps_count': len(plan.steps),
                'estimated_time_minutes': plan.estimated_total_time,
                'complexity_score': plan.complexity_score,
                'success_probability': plan.success_probability,
                'risks_identified': len(plan.risks),
                'processing_time_ms': round(processing_time * 1000, 2),
                'plan_summary': await self._generate_plan_summary(plan)
            }

        except Exception as e:
            self.logger.error(f"Plan creation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'task_description': task_description
            }

    async def _analyze_task_complexity(self, task_description: str) -> Dict[str, Any]:
        """Analyze the complexity of a task."""

        # Simple heuristic-based complexity analysis
        complexity_indicators = {
            'multiple_files': len([w for w in task_description.lower().split()
                                 if w in ['files', 'components', 'modules']]),
            'integration_keywords': len([w for w in task_description.lower().split()
                                       if w in ['integrate', 'connect', 'link', 'combine']]),
            'new_implementation': len([w for w in task_description.lower().split()
                                     if w in ['create', 'implement', 'build', 'develop']]),
            'testing_required': len([w for w in task_description.lower().split()
                                   if w in ['test', 'verify', 'validate', 'check']]),
            'dependencies': len([w for w in task_description.lower().split()
                               if w in ['database', 'api', 'external', 'library']])
        }

        # Calculate complexity score (0-1)
        total_indicators = sum(complexity_indicators.values())
        base_complexity = min(total_indicators * 0.15, 1.0)

        # Adjust based on task length and specific keywords
        length_factor = min(len(task_description.split()) / 50, 0.3)
        complexity_score = min(base_complexity + length_factor, 1.0)

        # Estimate time based on complexity
        if complexity_score < 0.3:
            estimated_time = 15  # 15 minutes for simple tasks
        elif complexity_score < 0.6:
            estimated_time = 45  # 45 minutes for moderate tasks
        elif complexity_score < 0.8:
            estimated_time = 120  # 2 hours for complex tasks
        else:
            estimated_time = 240  # 4+ hours for very complex tasks

        return {
            'complexity_score': round(complexity_score, 2),
            'estimated_time': estimated_time,
            'indicators': complexity_indicators
        }

    async def _breakdown_task(self, task_description: str) -> Dict[str, Any]:
        """Break down a task into discrete steps."""

        steps = []
        prerequisites = []

        # Common task patterns and their typical breakdowns
        task_lower = task_description.lower()

        if 'implement' in task_lower or 'create' in task_lower:
            steps.extend([
                PlanStep(
                    step_id="analyze",
                    title="Analyze Requirements",
                    description="Analyze the task requirements and existing codebase",
                    estimated_time=10,
                    tools_required=["file_search", "code_search"]
                ),
                PlanStep(
                    step_id="design",
                    title="Design Solution",
                    description="Design the implementation approach and architecture",
                    estimated_time=15,
                    dependencies=["analyze"]
                ),
                PlanStep(
                    step_id="implement",
                    title="Implement Solution",
                    description="Write and implement the code changes",
                    estimated_time=30,
                    dependencies=["design"],
                    tools_required=["code_editing", "file_operations"]
                )
            ])

        if 'test' in task_lower or 'verify' in task_lower:
            steps.append(
                PlanStep(
                    step_id="test",
                    title="Test Implementation",
                    description="Test the implementation to ensure it works correctly",
                    estimated_time=15,
                    dependencies=["implement"] if steps else [],
                    tools_required=["testing_tools"]
                )
            )

        if 'integrate' in task_lower:
            steps.append(
                PlanStep(
                    step_id="integrate",
                    title="Integration Testing",
                    description="Test integration with existing systems",
                    estimated_time=20,
                    dependencies=["implement", "test"],
                    risk_level="medium"
                )
            )

        if 'document' in task_lower or 'doc' in task_lower:
            steps.append(
                PlanStep(
                    step_id="document",
                    title="Update Documentation",
                    description="Update relevant documentation and usage guides",
                    estimated_time=10,
                    dependencies=["implement"]
                )
            )

        # If no specific patterns matched, create generic steps
        if not steps:
            steps = [
                PlanStep(
                    step_id="research",
                    title="Research and Planning",
                    description="Research the task requirements and plan the approach",
                    estimated_time=15
                ),
                PlanStep(
                    step_id="execute",
                    title="Execute Task",
                    description="Execute the main task implementation",
                    estimated_time=30,
                    dependencies=["research"]
                ),
                PlanStep(
                    step_id="verify",
                    title="Verify Results",
                    description="Verify that the task has been completed successfully",
                    estimated_time=10,
                    dependencies=["execute"]
                )
            ]

        # Identify prerequisites
        if 'database' in task_lower:
            prerequisites.append("Database access and permissions")
        if 'api' in task_lower:
            prerequisites.append("API credentials and documentation")
        if 'external' in task_lower:
            prerequisites.append("External service connectivity")

        return {
            'steps': steps,
            'prerequisites': prerequisites
        }

    async def _assess_risks(self, plan: TaskPlan) -> Dict[str, Any]:
        """Assess risks for the given plan."""

        risks = []
        success_probability = 0.9  # Start optimistic

        # Assess based on complexity
        if plan.complexity_score > 0.8:
            risks.append("High complexity may lead to unexpected challenges")
            success_probability -= 0.2

        # Assess based on dependencies
        dependency_count = sum(len(step.dependencies) for step in plan.steps)
        if dependency_count > len(plan.steps):
            risks.append("Complex step dependencies may cause execution delays")
            success_probability -= 0.1

        # Assess based on external requirements
        if plan.prerequisites:
            risks.append("External prerequisites may not be available")
            success_probability -= 0.1

        # Assess based on estimated time
        if plan.estimated_total_time and plan.estimated_total_time > 180:  # 3+ hours
            risks.append("Long execution time increases chance of interruption")
            success_probability -= 0.1

        # Tool availability risks
        required_tools = set()
        for step in plan.steps:
            required_tools.update(step.tools_required)

        if len(required_tools) > 5:
            risks.append("Multiple tool dependencies may cause integration issues")
            success_probability -= 0.1

        # Ensure probability stays within bounds
        success_probability = max(0.1, min(0.95, success_probability))

        return {
            'risks': risks,
            'success_probability': round(success_probability, 2)
        }

    async def _generate_plan_summary(self, plan: TaskPlan) -> str:
        """Generate a human-readable plan summary."""

        summary_lines = [
            f"Plan for: {plan.task_description}",
            f"Complexity: {'High' if plan.complexity_score > 0.7 else 'Medium' if plan.complexity_score > 0.4 else 'Low'}",
            f"Estimated time: {plan.estimated_total_time} minutes",
            f"Success probability: {int(plan.success_probability * 100)}%",
            "",
            "Steps:"
        ]

        for i, step in enumerate(plan.steps, 1):
            summary_lines.append(f"{i}. {step.title} ({step.estimated_time}min)")
            if step.dependencies:
                summary_lines.append(f"   Dependencies: {', '.join(step.dependencies)}")

        if plan.risks:
            summary_lines.extend(["", "Identified risks:"])
            summary_lines.extend([f"- {risk}" for risk in plan.risks])

        return "\n".join(summary_lines)

    async def exit_plan_mode(
        self,
        plan_id: str,
        user_approved: bool = True,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exit planning mode - Claude Code compatible ExitPlanMode functionality.

        Args:
            plan_id: ID of the plan to approve/reject
            user_approved: Whether the user approved the plan
            feedback: Optional user feedback on the plan

        Returns:
            Dict with exit plan mode results
        """
        try:
            if plan_id not in self.active_plans:
                return {
                    'success': False,
                    'error': f'Plan {plan_id} not found',
                    'available_plans': list(self.active_plans.keys())
                }

            plan = self.active_plans[plan_id]

            if user_approved:
                plan.phase = PlanningPhase.APPROVED

                return {
                    'success': True,
                    'plan_id': plan_id,
                    'action': 'approved',
                    'message': 'Plan approved and ready for execution',
                    'next_step': 'Begin plan execution',
                    'plan_summary': await self._generate_plan_summary(plan),
                    'execution_ready': True,
                    'estimated_time': plan.estimated_total_time,
                    'steps_count': len(plan.steps)
                }
            else:
                plan.phase = PlanningPhase.REJECTED

                return {
                    'success': True,
                    'plan_id': plan_id,
                    'action': 'rejected',
                    'message': 'Plan rejected by user',
                    'feedback': feedback or 'No feedback provided',
                    'execution_ready': False,
                    'requires_revision': True
                }

        except Exception as e:
            self.logger.error(f"Exit plan mode failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'plan_id': plan_id
            }

    async def get_plan_status(self, plan_id: str) -> Dict[str, Any]:
        """Get the current status of a plan."""

        if plan_id not in self.active_plans:
            return {
                'success': False,
                'error': f'Plan {plan_id} not found'
            }

        plan = self.active_plans[plan_id]

        completed_steps = [step for step in plan.steps if step.status == 'completed']
        in_progress_steps = [step for step in plan.steps if step.status == 'in_progress']

        return {
            'success': True,
            'plan_id': plan_id,
            'phase': plan.phase.value,
            'task_description': plan.task_description,
            'total_steps': len(plan.steps),
            'completed_steps': len(completed_steps),
            'in_progress_steps': len(in_progress_steps),
            'progress_percentage': round((len(completed_steps) / len(plan.steps)) * 100, 1) if plan.steps else 0,
            'estimated_remaining_time': sum(step.estimated_time or 0
                                          for step in plan.steps
                                          if step.status not in ['completed']),
            'success_probability': plan.success_probability,
            'complexity_score': plan.complexity_score
        }

    async def update_step_status(
        self,
        plan_id: str,
        step_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update the status of a specific plan step."""

        if plan_id not in self.active_plans:
            return {
                'success': False,
                'error': f'Plan {plan_id} not found'
            }

        plan = self.active_plans[plan_id]

        # Find the step
        target_step = None
        for step in plan.steps:
            if step.step_id == step_id:
                target_step = step
                break

        if not target_step:
            return {
                'success': False,
                'error': f'Step {step_id} not found in plan {plan_id}',
                'available_steps': [step.step_id for step in plan.steps]
            }

        # Update status
        old_status = target_step.status
        target_step.status = status

        # Check if plan is completed
        if all(step.status == 'completed' for step in plan.steps):
            plan.phase = PlanningPhase.COMPLETED
        elif any(step.status == 'in_progress' for step in plan.steps):
            plan.phase = PlanningPhase.EXECUTING

        return {
            'success': True,
            'plan_id': plan_id,
            'step_id': step_id,
            'old_status': old_status,
            'new_status': status,
            'plan_phase': plan.phase.value,
            'notes': notes
        }

    async def list_active_plans(self) -> Dict[str, Any]:
        """List all active plans and their status."""

        plans_summary = []

        for plan_id, plan in self.active_plans.items():
            completed_steps = sum(1 for step in plan.steps if step.status == 'completed')

            plans_summary.append({
                'plan_id': plan_id,
                'task_description': plan.task_description[:100] + '...' if len(plan.task_description) > 100 else plan.task_description,
                'phase': plan.phase.value,
                'progress': f"{completed_steps}/{len(plan.steps)} steps",
                'complexity': plan.complexity_score,
                'success_probability': plan.success_probability,
                'created_at': plan.created_at.isoformat()
            })

        return {
            'success': True,
            'active_plans_count': len(self.active_plans),
            'plans': plans_summary
        }


# Export planning tools
planning_tool = PlanningTool()

async def create_task_plan(
    task_description: str,
    auto_breakdown: bool = True,
    include_risk_assessment: bool = True
) -> Dict[str, Any]:
    """
    Claude Code compatible task planning function.

    Args:
        task_description: Description of the task to plan
        auto_breakdown: Whether to automatically break down the task
        include_risk_assessment: Whether to include risk analysis

    Returns:
        Plan creation results
    """
    return await planning_tool.create_plan(task_description, auto_breakdown, include_risk_assessment)

async def exit_plan_mode(
    plan_id: str,
    user_approved: bool = True,
    feedback: Optional[str] = None
) -> Dict[str, Any]:
    """
    Claude Code compatible ExitPlanMode function.

    Args:
        plan_id: ID of the plan to approve/reject
        user_approved: Whether the user approved the plan
        feedback: Optional user feedback

    Returns:
        Exit plan mode results
    """
    return await planning_tool.exit_plan_mode(plan_id, user_approved, feedback)

async def get_plan_status(plan_id: str) -> Dict[str, Any]:
    """
    Get status of a specific plan.

    Args:
        plan_id: ID of the plan to check

    Returns:
        Plan status information
    """
    return await planning_tool.get_plan_status(plan_id)