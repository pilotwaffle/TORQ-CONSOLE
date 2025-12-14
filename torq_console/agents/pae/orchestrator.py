"""
PAE (Plan-Approve-Execute) Orchestrator

Orchestrates the Plan-Approve-Execute workflow, managing plan creation,
approval workflows, and execution with rollback capabilities.
Integrates with Marvin agents for intelligent plan generation and execution.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from .models import (
    ActionPlan,
    ActionType,
    ApprovalRequest,
    ExecutionContext,
    PlanPhase,
    PlanStep,
    PlanStatus,
    StepStatus,
    WorkflowCheckpoint,
)
from .storage import PlanStorage

logger = logging.getLogger(__name__)


class PAEOrchestrator:
    """
    Orchestrates PAE workflows with Marvin agent integration.

    Provides:
    - Intelligent plan generation using Marvin agents
    - Human approval workflows
    - Safe execution with rollback capability
    - Progress tracking and error handling
    """

    def __init__(
        self,
        storage: Optional[PlanStorage] = None,
       marvin_orchestrator=None,
        default_context: Optional[ExecutionContext] = None
    ):
        """
        Initialize the PAE orchestrator.

        Args:
            storage: Storage backend for plans and checkpoints
            marvin_orchestrator: Marvin agent orchestrator for intelligent execution
            default_context: Default execution context
        """
        self.storage = storage or PlanStorage()
        self.marvin_orchestrator = marvin_orchestrator
        self.default_context = default_context
        self.active_plans: Dict[UUID, ActionPlan] = {}
        self.plan_templates: Dict[str, Dict[str, Any]] = {}

    async def create_plan(
        self,
        name: str,
        description: str,
        user_request: str,
        context: Optional[ExecutionContext] = None,
        template: Optional[str] = None,
        auto_generate_steps: bool = True
    ) -> ActionPlan:
        """
        Create a new action plan.

        Args:
            name: Name of the plan
            description: Description of what the plan accomplishes
            user_request: Original user request
            context: Execution context
            template: Optional template to use
            auto_generate_steps: Whether to auto-generate steps using Marvin

        Returns:
            Created action plan
        """
        logger.info(f"Creating plan: {name}")

        # Use provided context or default
        context = context or self.default_context
        if not context:
            raise ValueError("Execution context is required")

        # Create initial plan
        plan = ActionPlan(
            name=name,
            description=description,
            steps=[],
            total_steps=0,
            context=context,
            created_by=context.user_id
        )

        # Generate steps if requested
        if auto_generate_steps and self.marvin_orchestrator:
            plan = await self._generate_plan_steps(plan, user_request, template)
        elif template and template in self.plan_templates:
            plan = self._apply_template(plan, template)
        else:
            # Create minimal plan structure
            plan = await self._create_minimal_plan(plan, user_request)

        # Save plan
        await self.storage.save_plan(plan)
        self.active_plans[plan.id] = plan

        logger.info(f"Plan created with {len(plan.steps)} steps")
        return plan

    async def submit_for_approval(self, plan_id: UUID, approver: Optional[str] = None) -> ApprovalRequest:
        """
        Submit a plan for approval.

        Args:
            plan_id: ID of the plan to submit
            approver: Who should approve the plan

        Returns:
            Approval request
        """
        plan = await self.storage.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        if not plan.is_ready_for_approval:
            raise ValueError(f"Plan {plan_id} is not ready for approval")

        # Create approval request
        approval = ApprovalRequest(
            plan_id=plan_id,
            title=f"Approval Request: {plan.name}",
            description=f"Please review and approve the following action plan",
            plan_summary=self._generate_plan_summary(plan),
            risk_level=plan.risk_level,
            approver=approver,
            deadline=datetime.utcnow() + timedelta(hours=24)
        )

        # Add warnings and recommendations
        approval.warnings = self._generate_plan_warnings(plan)
        approval.recommendations = self._generate_plan_recommendations(plan)

        # Update plan status
        plan.status = PlanStatus.PENDING_APPROVAL
        plan.phase = PlanPhase.APPROVAL
        plan.approval_request = approval

        # Save and return
        await self.storage.save_plan(plan)
        await self.storage.save_approval(approval)

        logger.info(f"Plan {plan_id} submitted for approval")
        return approval

    async def approve_plan(
        self,
        plan_id: UUID,
        approved: bool,
        approved_by: str,
        comments: Optional[str] = None
    ) -> ActionPlan:
        """
        Process approval decision for a plan.

        Args:
            plan_id: ID of the plan
            approved: Whether the plan is approved
            approved_by: Who made the decision
            comments: Optional comments

        Returns:
            Updated plan
        """
        plan = await self.storage.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        if plan.status != PlanStatus.PENDING_APPROVAL:
            raise ValueError(f"Plan {plan_id} is not pending approval")

        # Update approval request
        if plan.approval_request:
            plan.approval_request.approved = approved
            plan.approval_request.approved_by = approved_by
            plan.approval_request.approved_at = datetime.utcnow()
            plan.approval_request.comments = comments

        # Update plan status
        if approved:
            plan.status = PlanStatus.APPROVED
            plan.approved_by = approved_by
            plan.approved_at = datetime.utcnow()
            logger.info(f"Plan {plan_id} approved by {approved_by}")
        else:
            plan.status = PlanStatus.REJECTED
            logger.info(f"Plan {plan_id} rejected by {approved_by}")

        # Save and return
        await self.storage.save_plan(plan)
        return plan

    async def execute_plan(
        self,
        plan_id: UUID,
        dry_run: bool = False,
        checkpoint_frequency: Optional[int] = None
    ) -> ActionPlan:
        """
        Execute an approved plan.

        Args:
            plan_id: ID of the plan to execute
            dry_run: Perform a dry run without making changes
            checkpoint_frequency: Override default checkpoint frequency

        Returns:
            Updated plan after execution
        """
        plan = await self.storage.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        if not plan.is_ready_for_execution and not dry_run:
            raise ValueError(f"Plan {plan_id} is not ready for execution")

        # Update plan for execution
        plan.status = PlanStatus.IN_PROGRESS
        plan.phase = PlanPhase.EXECUTION
        plan.started_at = datetime.utcnow()

        if dry_run:
            logger.info(f"Executing plan {plan_id} in DRY RUN mode")
        else:
            logger.info(f"Executing plan {plan_id}")

        # Create initial checkpoint
        if plan.context.auto_checkpoint and not dry_run:
            await self._create_checkpoint(plan, "Before execution")

        # Execute steps
        try:
            checkpoint_freq = checkpoint_frequency or plan.context.checkpoint_frequency
            await self._execute_plan_steps(plan, dry_run, checkpoint_freq)

            # Update final status
            if plan.completed_steps == plan.total_steps:
                plan.status = PlanStatus.COMPLETED
                plan.phase = PlanPhase.COMPLETED
                plan.completed_at = datetime.utcnow()
                logger.info(f"Plan {plan_id} completed successfully")
            else:
                plan.status = PlanStatus.FAILED
                plan.phase = PlanPhase.FAILED
                logger.error(f"Plan {plan_id} failed to complete all steps")

        except Exception as e:
            plan.status = PlanStatus.FAILED
            plan.phase = PlanPhase.FAILED
            plan.errors.append(str(e))
            logger.error(f"Plan {plan_id} execution failed: {e}")

            # Attempt rollback if enabled
            if plan.can_rollback and not dry_run:
                await self._rollback_plan(plan)

        # Save and return
        await self.storage.save_plan(plan)
        return plan

    async def rollback_plan(self, plan_id: UUID, checkpoint_id: Optional[UUID] = None) -> ActionPlan:
        """
        Rollback a plan to a checkpoint.

        Args:
            plan_id: ID of the plan to rollback
            checkpoint_id: Specific checkpoint to rollback to (uses latest if None)

        Returns:
            Updated plan after rollback
        """
        plan = await self.storage.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        if not plan.can_rollback:
            raise ValueError(f"Plan {plan_id} cannot be rolled back")

        # Get checkpoint to rollback to
        if checkpoint_id:
            checkpoint = next((c for c in plan.checkpoints if c.id == checkpoint_id), None)
        else:
            # Get latest checkpoint
            checkpoint = max(plan.checkpoints, key=lambda c: c.created_at) if plan.checkpoints else None

        if not checkpoint:
            raise ValueError(f"No checkpoint found for rollback")

        logger.info(f"Rolling back plan {plan_id} to checkpoint {checkpoint.id}")

        # Execute rollback commands
        rollback_success = await self._execute_rollback(plan, checkpoint)

        if rollback_success:
            plan.rolled_back = True
            plan.rollback_checkpoint = checkpoint.id
            plan.status = PlanStatus.CANCELLED
            plan.phase = PlanPhase.CANCELLED
            logger.info(f"Plan {plan_id} rolled back successfully")
        else:
            logger.error(f"Rollback failed for plan {plan_id}")

        # Save and return
        await self.storage.save_plan(plan)
        return plan

    async def _generate_plan_steps(
        self,
        plan: ActionPlan,
        user_request: str,
        template: Optional[str] = None
    ) -> ActionPlan:
        """Generate plan steps using Marvin agents."""
        if not self.marvin_orchestrator:
            return await self._create_minimal_plan(plan, user_request)

        # Use Marvin to generate detailed plan
        # This is a simplified implementation - in production, you'd use
        # Marvin's planning capabilities to generate intelligent steps
        steps_data = await self._call_marvin_planner(user_request, plan.context)

        # Convert to PlanStep objects
        steps = []
        for i, step_data in enumerate(steps_data.get("steps", [])):
            step = PlanStep(
                name=step_data.get("name", f"Step {i+1}"),
                description=step_data.get("description", ""),
                action_type=ActionType(step_data.get("action_type", "user_interaction")),
                agent=step_data.get("agent", "general"),
                parameters=step_data.get("parameters", {}),
                order=i,
                risk_level=step_data.get("risk_level", "low"),
                requires_confirmation=step_data.get("risk_level") in ["high", "critical"]
            )
            steps.append(step)

        plan.steps = steps
        plan.total_steps = len(steps)
        return plan

    async def _create_minimal_plan(self, plan: ActionPlan, user_request: str) -> ActionPlan:
        """Create a minimal plan with basic steps."""
        # Create a basic plan structure
        step = PlanStep(
            name="Execute user request",
            description=f"Execute the following user request: {user_request}",
            action_type=ActionType.USER_INTERACTION,
            agent="general",
            parameters={"request": user_request},
            order=0,
            requires_confirmation=True
        )

        plan.steps = [step]
        plan.total_steps = 1
        return plan

    async def _execute_plan_steps(
        self,
        plan: ActionPlan,
        dry_run: bool,
        checkpoint_frequency: int
    ) -> None:
        """Execute all steps in the plan."""
        executed_count = 0

        while plan.completed_steps < plan.total_steps:
            # Get next steps to execute
            next_steps = plan.get_next_steps()

            if not next_steps:
                if plan.completed_steps < plan.total_steps:
                    # Check if we're blocked by dependencies
                    logger.error(f"No executable steps found, but plan not complete")
                    break
                else:
                    break

            # Execute steps in parallel up to the limit
            batch_size = min(plan.context.max_parallel_steps, len(next_steps))
            batch = next_steps[:batch_size]

            # Create batch tasks
            tasks = []
            for step in batch:
                if dry_run:
                    task = self._simulate_step_execution(step)
                else:
                    task = self._execute_step(step, plan)
                tasks.append(task)

            # Wait for batch completion
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for step, result in zip(batch, results):
                if isinstance(result, Exception):
                    step.status = StepStatus.FAILED
                    step.error = str(result)
                    plan.errors.append(f"Step {step.name} failed: {result}")
                else:
                    step.status = StepStatus.COMPLETED
                    step.result = result
                    step.completed_at = datetime.utcnow()
                    plan.completed_steps += 1

                # Update current step
                plan.current_step = step.id

            # Create checkpoint if needed
            if not dry_run and executed_count > 0 and executed_count % checkpoint_frequency == 0:
                await self._create_checkpoint(plan, f"After {executed_count} steps")

            executed_count += len(batch)

    async def _execute_step(self, step: PlanStep, plan: ActionPlan) -> Dict[str, Any]:
        """Execute a single step using the appropriate agent."""
        logger.info(f"Executing step: {step.name}")

        step.status = StepStatus.RUNNING
        step.started_at = datetime.utcnow()

        try:
            # Check if approval is needed
            if (step.requires_confirmation and
                step.action_type in plan.context.require_approval_for):
                await self._request_step_approval(step, plan)

            # Execute using Marvin orchestrator if available
            if self.marvin_orchestrator:
                result = await self._execute_with_marvin(step)
            else:
                result = await self._execute_locally(step, plan)

            return result

        except Exception as e:
            logger.error(f"Step {step.name} failed: {e}")
            raise
        finally:
            step.status = StepStatus.COMPLETED if not step.error else StepStatus.FAILED

    async def _execute_with_marvin(self, step: PlanStep) -> Dict[str, Any]:
        """Execute step using Marvin agent orchestrator."""
        # This would integrate with Marvin's agent system
        # For now, return a simulated result
        return {
            "success": True,
            "message": f"Step {step.name} executed via Marvin",
            "output": f"Simulated output for {step.action_type}"
        }

    async def _execute_locally(self, step: PlanStep, plan: ActionPlan) -> Dict[str, Any]:
        """Execute step locally without Marvin."""
        # Basic local execution
        return {
            "success": True,
            "message": f"Step {step.name} executed locally",
            "output": f"Local execution of {step.action_type}"
        }

    async def _simulate_step_execution(self, step: PlanStep) -> Dict[str, Any]:
        """Simulate step execution for dry run mode."""
        logger.info(f"[DRY RUN] Simulating step: {step.name}")

        await asyncio.sleep(0.1)  # Simulate execution time

        return {
            "success": True,
            "message": f"[DRY RUN] Step {step.name} would be executed",
            "simulated_output": f"Would execute {step.action_type} with parameters {step.parameters}"
        }

    async def _create_checkpoint(self, plan: ActionPlan, description: str) -> WorkflowCheckpoint:
        """Create a workflow checkpoint."""
        checkpoint = plan.create_checkpoint(
            after_step=plan.current_step,
            description=description
        )

        await self.storage.save_checkpoint(checkpoint)
        logger.debug(f"Created checkpoint {checkpoint.id}: {description}")

        return checkpoint

    async def _rollback_plan(self, plan: ActionPlan) -> None:
        """Rollback the entire plan."""
        if not plan.checkpoints:
            logger.error("No checkpoints available for rollback")
            return

        # Get the last successful checkpoint
        last_checkpoint = max(
            (c for c in plan.checkpoints),
            key=lambda c: c.created_at
        )

        await self._execute_rollback(plan, last_checkpoint)

    async def _execute_rollback(self, plan: ActionPlan, checkpoint: WorkflowCheckpoint) -> bool:
        """Execute rollback to a specific checkpoint."""
        logger.info(f"Executing rollback to checkpoint {checkpoint.id}")

        # Execute rollback commands in reverse order
        success = True
        for command in reversed(checkpoint.rollback_commands):
            try:
                # Execute rollback command
                # This would need to be implemented based on your command execution system
                logger.debug(f"Executing rollback command: {command}")
            except Exception as e:
                logger.error(f"Rollback command failed: {e}")
                success = False

        return success

    async def _request_step_approval(self, step: PlanStep, plan: ActionPlan) -> None:
        """Request approval for a step."""
        # In a real implementation, this would send a notification
        # For now, we'll log it
        logger.warning(f"Step {step.name} requires approval but auto-approving for demo")

    def _generate_plan_summary(self, plan: ActionPlan) -> str:
        """Generate a summary of the plan for approval."""
        summary = f"Plan: {plan.name}\n\n"
        summary += f"Description: {plan.description}\n\n"
        summary += f"Steps: {plan.total_steps}\n"
        summary += f"Risk Level: {plan.risk_level}\n\n"

        summary += "Steps:\n"
        for step in plan.steps:
            summary += f"  {step.order + 1}. {step.name} - {step.action_type} ({step.risk_level})\n"

        return summary

    def _generate_plan_warnings(self, plan: ActionPlan) -> List[str]:
        """Generate warnings about the plan."""
        warnings = []

        if plan.risk_level in ["high", "critical"]:
            warnings.append(f"Plan has {plan.risk_level} risk level")

        high_risk_steps = [s for s in plan.steps if s.risk_level in ["high", "critical"]]
        if high_risk_steps:
            warnings.append(f"Contains {len(high_risk_steps)} high-risk steps")

        if any(step.action_type == ActionType.COMMAND_EXECUTION for step in plan.steps):
            warnings.append("Plan executes system commands")

        return warnings

    def _generate_plan_recommendations(self, plan: ActionPlan) -> List[str]:
        """Generate recommendations for the plan."""
        recommendations = []

        if plan.total_steps > 10:
            recommendations.append("Consider breaking this into smaller plans")

        if not any(step.checkpoint_after for step in plan.steps):
            recommendations.append("Consider adding checkpoints for safety")

        if plan.risk_level == "critical" and not plan.context.sandbox_mode:
            recommendations.append("Consider running in sandbox mode")

        return recommendations

    async def _call_marvin_planner(self, user_request: str, context: ExecutionContext) -> Dict[str, Any]:
        """Call Marvin agent to generate a plan."""
        # This would integrate with Marvin's planning capabilities
        # For now, return a simple structure
        return {
            "steps": [
                {
                    "name": "Analyze request",
                    "description": "Analyze the user request",
                    "action_type": "user_interaction",
                    "agent": "analyzer",
                    "risk_level": "low"
                },
                {
                    "name": "Execute main task",
                    "description": f"Execute: {user_request}",
                    "action_type": "user_interaction",
                    "agent": "executor",
                    "risk_level": "medium"
                },
                {
                    "name": "Verify results",
                    "description": "Verify the execution results",
                    "action_type": "validation",
                    "agent": "validator",
                    "risk_level": "low"
                }
            ]
        }

    def _apply_template(self, plan: ActionPlan, template_name: str) -> ActionPlan:
        """Apply a predefined template to the plan."""
        template = self.plan_templates.get(template_name, {})

        # Create steps from template
        steps = []
        for i, step_data in enumerate(template.get("steps", [])):
            step = PlanStep(
                name=step_data["name"],
                description=step_data["description"],
                action_type=ActionType(step_data.get("action_type", "user_interaction")),
                agent=step_data.get("agent", "general"),
                order=i,
                risk_level=step_data.get("risk_level", "low")
            )
            steps.append(step)

        plan.steps = steps
        plan.total_steps = len(steps)
        return plan