"""
Workflow Agent - Unified workflow execution capability.

Consolidates all workflow-focused agents (coding, debugging, documentation,
testing, architecture agents) into a single, modular agent with multiple capabilities.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from .base_agent import BaseAgent, AgentCapability, AgentContext, AgentResult
from .interfaces import IWorkflowAgent, WorkflowType
from .capabilities import (
    CodeGenerationCapability, DebuggingCapability,
    DocumentationCapability, TestingCapability, ArchitectureCapability,
    CapabilityFactory
)
from ..registry import register_agent


class WorkflowAgent(BaseAgent, IWorkflowAgent):
    """
    Unified workflow agent that consolidates all workflow-focused functionality.

    Replaces multiple scattered workflow agents:
    - Code generation agents
    - Debugging agents
    - Documentation agents
    - Testing agents
    - Architecture agents
    - Specialized workflow systems

    Features:
    - Multiple workflow types in single agent
    - Capability-based execution
    - Consistent interface for all workflows
    - Resource sharing between capabilities
    - Workflow composition and chaining
    """

    def __init__(
        self,
        llm_provider=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize workflow agent."""
        super().__init__(
            agent_id="workflow_agent",
            agent_name="Workflow Agent",
            capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.DEBUGGING,
                AgentCapability.DOCUMENTATION,
                AgentCapability.TESTING,
                AgentCapability.ARCHITECTURE,
                AgentCapability.CODE_REVIEW,
                AgentCapability.WORKFLOW_AUTOMATION
            ],
            llm_provider=llm_provider,
            config=config
        )

        # Initialize workflow capabilities
        self._capabilities: Dict[str, Any] = {}
        self._init_capabilities()

        # Workflow execution state
        self._active_workflows: Dict[str, Dict[str, Any]] = {}
        self._workflow_history: List[Dict[str, Any]] = []
        self._max_history_size = self.config.get("max_history_size", 100)

        # Workflow settings
        self._default_language = self.config.get("default_language", "python")
        self._max_execution_time = self.config.get("max_execution_time", 300)  # 5 minutes

        self.logger.info("WorkflowAgent initialized with multiple workflow capabilities")

    def _init_capabilities(self) -> None:
        """Initialize workflow capabilities."""
        capability_configs = self.config.get("capability_configs", {})

        for capability in self.capabilities:
            try:
                cap_config = capability_configs.get(capability, {})
                if capability in CapabilityFactory.get_available_capabilities():
                    self._capabilities[capability] = CapabilityFactory.create_capability(
                        capability, cap_config
                    )
                    self.logger.debug(f"Initialized capability: {capability}")
            except Exception as e:
                self.logger.error(f"Failed to initialize capability {capability}: {e}")

    async def _execute_request(
        self,
        request: str,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute workflow request."""
        # Try to infer workflow type from request
        workflow_type = await self._infer_workflow_type(request)

        if not workflow_type:
            return AgentResult(
                success=False,
                content="Could not determine the appropriate workflow type for your request. "
                       "Please specify what type of workflow you need (e.g., 'generate code', "
                       "'debug this', 'document this', 'test this', 'design architecture').",
                error="Unknown workflow type"
            )

        # Execute the inferred workflow
        return await self.execute_workflow(
            workflow_type=workflow_type,
            parameters={
                "request": request,
                "context": context
            },
            context=context
        )

    async def execute_workflow(
        self,
        workflow_type: Union[str, WorkflowType],
        parameters: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """
        Execute a specific workflow.

        Args:
            workflow_type: Type of workflow to execute
            parameters: Workflow parameters
            context: Optional execution context

        Returns:
            AgentResult with workflow output
        """
        if isinstance(workflow_type, str):
            try:
                workflow_type = WorkflowType(workflow_type)
            except ValueError:
                return AgentResult(
                    success=False,
                    content=f"Unknown workflow type: {workflow_type}",
                    error="Invalid workflow type"
                )

        # Create workflow execution context
        workflow_id = f"{workflow_type}_{asyncio.get_event_loop().time()}"
        start_time = asyncio.get_event_loop().time()

        self._active_workflows[workflow_id] = {
            "type": workflow_type,
            "start_time": start_time,
            "parameters": parameters,
            "status": "running"
        }

        try:
            # Execute workflow based on type
            result = await self._execute_workflow_by_type(
                workflow_type, parameters, context
            )

            # Update workflow status
            self._active_workflows[workflow_id]["status"] = "completed"
            self._active_workflows[workflow_id]["end_time"] = asyncio.get_event_loop().time()
            self._active_workflows[workflow_id]["success"] = result.success

            # Add to history
            workflow_record = {
                "id": workflow_id,
                "type": workflow_type,
                "success": result.success,
                "execution_time": result.execution_time,
                "timestamp": start_time
            }
            self._add_to_workflow_history(workflow_record)

            # Add workflow metadata to result
            result.metadata["workflow_id"] = workflow_id
            result.metadata["workflow_type"] = workflow_type.value

            self.logger.info(f"Completed workflow {workflow_type} in {result.execution_time:.2f}s")
            return result

        except Exception as e:
            # Update workflow status with error
            self._active_workflows[workflow_id]["status"] = "error"
            self._active_workflows[workflow_id]["error"] = str(e)

            self.logger.error(f"Workflow {workflow_type} failed: {e}", exc_info=True)

            return AgentResult(
                success=False,
                content=f"Workflow execution failed: {str(e)}",
                error=str(e),
                metadata={"workflow_id": workflow_id, "workflow_type": workflow_type.value}
            )

        finally:
            # Clean up active workflow after some time
            await asyncio.sleep(60)  # Keep for 1 minute for monitoring
            self._active_workflows.pop(workflow_id, None)

    async def _execute_workflow_by_type(
        self,
        workflow_type: WorkflowType,
        parameters: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute workflow based on its type."""
        request = parameters.get("request", "")

        if workflow_type == WorkflowType.CODE_GENERATION:
            return await self._execute_code_generation(request, parameters, context)

        elif workflow_type == WorkflowType.DEBUGGING:
            return await self._execute_debugging(request, parameters, context)

        elif workflow_type == WorkflowType.DOCUMENTATION:
            return await self._execute_documentation(request, parameters, context)

        elif workflow_type == WorkflowType.TESTING:
            return await self._execute_testing(request, parameters, context)

        elif workflow_type == WorkflowType.ARCHITECTURE:
            return await self._execute_architecture(request, parameters, context)

        elif workflow_type == WorkflowType.REFACTORING:
            return await self._execute_refactoring(request, parameters, context)

        elif workflow_type == WorkflowType.ANALYSIS:
            return await self._execute_analysis(request, parameters, context)

        else:
            return AgentResult(
                success=False,
                content=f"Workflow type {workflow_type} is not yet implemented",
                error="Unsupported workflow type"
            )

    async def _execute_code_generation(
        self,
        request: str,
        parameters: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute code generation workflow."""
        if AgentCapability.CODE_GENERATION not in self._capabilities:
            return AgentResult(
                success=False,
                content="Code generation capability not available",
                error="Missing capability"
            )

        language = parameters.get("language", self._default_language)
        framework = parameters.get("framework")

        return await self._capabilities[AgentCapability.CODE_GENERATION].execute(
            requirements=request,
            language=language,
            framework=framework,
            context=context
        )

    async def _execute_debugging(
        self,
        request: str,
        parameters: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute debugging workflow."""
        if AgentCapability.DEBUGGING not in self._capabilities:
            return AgentResult(
                success=False,
                content="Debugging capability not available",
                error="Missing capability"
            )

        code = parameters.get("code", request)
        error_message = parameters.get("error_message", "")
        language = parameters.get("language", self._default_language)

        return await self._capabilities[AgentCapability.DEBUGGING].execute(
            code=code,
            error_message=error_message,
            language=language,
            context=context
        )

    async def _execute_documentation(
        self,
        request: str,
        parameters: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute documentation workflow."""
        if AgentCapability.DOCUMENTATION not in self._capabilities:
            return AgentResult(
                success=False,
                content="Documentation capability not available",
                error="Missing capability"
            )

        doc_type = parameters.get("doc_type", "api")
        audience = parameters.get("audience", "developers")
        format_type = parameters.get("format", "markdown")

        return await self._capabilities[AgentCapability.DOCUMENTATION].execute(
            content=request,
            doc_type=doc_type,
            audience=audience,
            format=format_type,
            context=context
        )

    async def _execute_testing(
        self,
        request: str,
        parameters: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute testing workflow."""
        if AgentCapability.TESTING not in self._capabilities:
            return AgentResult(
                success=False,
                content="Testing capability not available",
                error="Missing capability"
            )

        # This is a placeholder implementation
        return await self._capabilities[AgentCapability.TESTING].execute(
            request,
            context=context
        )

    async def _execute_architecture(
        self,
        request: str,
        parameters: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute architecture workflow."""
        if AgentCapability.ARCHITECTURE not in self._capabilities:
            return AgentResult(
                success=False,
                content="Architecture capability not available",
                error="Missing capability"
            )

        # This is a placeholder implementation
        return await self._capabilities[AgentCapability.ARCHITECTURE].execute(
            request,
            context=context
        )

    async def _execute_refactoring(
        self,
        request: str,
        parameters: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute refactoring workflow."""
        # This would typically combine code analysis and generation capabilities
        code = parameters.get("code", request)
        refactoring_goals = parameters.get("goals", ["improve_readability", "optimize_performance"])

        # Placeholder implementation
        return AgentResult(
            success=True,
            content=f"Refactoring workflow not yet fully implemented. Would refactor code with goals: {refactoring_goals}",
            confidence=0.6,
            metadata={"goals": refactoring_goals}
        )

    async def _execute_analysis(
        self,
        request: str,
        parameters: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute analysis workflow."""
        # This would analyze code, requirements, or other artifacts
        analysis_type = parameters.get("analysis_type", "general")

        # Placeholder implementation
        return AgentResult(
            success=True,
            content=f"Analysis workflow not yet fully implemented. Would perform {analysis_type} analysis.",
            confidence=0.6,
            metadata={"analysis_type": analysis_type}
        )

    async def _infer_workflow_type(self, request: str) -> Optional[WorkflowType]:
        """Infer workflow type from request text."""
        request_lower = request.lower()

        # Simple keyword-based inference
        if any(keyword in request_lower for keyword in ["generate", "create", "write", "implement", "code"]):
            return WorkflowType.CODE_GENERATION
        elif any(keyword in request_lower for keyword in ["debug", "fix", "error", "bug", "issue"]):
            return WorkflowType.DEBUGGING
        elif any(keyword in request_lower for keyword in ["document", "docs", "readme", "guide"]):
            return WorkflowType.DOCUMENTATION
        elif any(keyword in request_lower for keyword in ["test", "testing", "unit test", "coverage"]):
            return WorkflowType.TESTING
        elif any(keyword in request_lower for keyword in ["architecture", "design", "structure", "system"]):
            return WorkflowType.ARCHITECTURE
        elif any(keyword in request_lower for keyword in ["refactor", "improve", "optimize", "cleanup"]):
            return WorkflowType.REFACTORING
        elif any(keyword in request_lower for keyword in ["analyze", "review", "examine", "inspect"]):
            return WorkflowType.ANALYSIS

        return None

    def get_supported_workflows(self) -> List[WorkflowType]:
        """Get list of supported workflow types."""
        return list(WorkflowType)

    async def get_workflow_template(
        self,
        workflow_type: WorkflowType
    ) -> Optional[Dict[str, Any]]:
        """Get template for a workflow type."""
        templates = {
            WorkflowType.CODE_GENERATION: {
                "description": "Generate code from requirements",
                "parameters": {
                    "requirements": "string (required)",
                    "language": "string (optional, default: python)",
                    "framework": "string (optional)",
                    "style_guide": "string (optional)"
                },
                "example": "Generate a function to validate email addresses"
            },
            WorkflowType.DEBUGGING: {
                "description": "Debug code issues",
                "parameters": {
                    "code": "string (required)",
                    "error_message": "string (optional)",
                    "language": "string (optional)"
                },
                "example": "Debug this code that throws TypeError"
            },
            WorkflowType.DOCUMENTATION: {
                "description": "Generate documentation",
                "parameters": {
                    "content": "string (required)",
                    "doc_type": "string (optional, default: api)",
                    "audience": "string (optional, default: developers)",
                    "format": "string (optional, default: markdown)"
                },
                "example": "Document this function with API docs"
            }
        }

        return templates.get(workflow_type)

    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get list of currently active workflows."""
        current_time = asyncio.get_event_loop().time()
        active = []

        for workflow_id, workflow in self._active_workflows.items():
            workflow_info = {
                "id": workflow_id,
                "type": workflow["type"].value,
                "status": workflow["status"],
                "start_time": workflow["start_time"],
                "duration": current_time - workflow["start_time"]
            }
            if "error" in workflow:
                workflow_info["error"] = workflow["error"]
            active.append(workflow_info)

        return active

    def get_workflow_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get workflow execution history."""
        history = self._workflow_history.copy()
        if limit:
            return history[-limit:]
        return history

    def _add_to_workflow_history(self, workflow_record: Dict[str, Any]) -> None:
        """Add workflow record to history."""
        self._workflow_history.append(workflow_record)

        # Maintain history size limit
        if len(self._workflow_history) > self._max_history_size:
            self._workflow_history = self._workflow_history[-self._max_history_size:]

    async def _health_check_impl(self) -> bool:
        """Agent-specific health check."""
        try:
            # Test a simple workflow
            result = await self.execute_workflow(
                workflow_type=WorkflowType.ANALYSIS,
                parameters={"request": "Health check test", "analysis_type": "general"}
            )
            return result.success

        except Exception as e:
            self.logger.error(f"Workflow agent health check failed: {e}")
            return False

    async def _reset_impl(self) -> None:
        """Reset agent-specific state."""
        # Clear active workflows
        self._active_workflows.clear()

        # Clear history
        self._workflow_history.clear()

        # Reset capabilities if they have reset methods
        for capability in self._capabilities.values():
            if hasattr(capability, 'reset'):
                try:
                    if asyncio.iscoroutinefunction(capability.reset):
                        await capability.reset()
                    else:
                        capability.reset()
                except Exception as e:
                    self.logger.error(f"Failed to reset capability: {e}")

    def get_agent_info(self) -> Dict[str, Any]:
        """Get detailed agent information."""
        base_info = super().get_agent_info() if hasattr(super(), 'get_agent_info') else {}

        workflow_info = {
            "active_workflows": len(self._active_workflows),
            "workflow_history_size": len(self._workflow_history),
            "available_capabilities": list(self._capabilities.keys()),
            "default_language": self._default_language,
            "max_execution_time": self._max_execution_time
        }

        if base_info:
            base_info.update(workflow_info)
            return base_info

        return workflow_info


# Register the agent
register_agent(
    WorkflowAgent,
    "workflow_agent",
    "Workflow Agent",
    [
        AgentCapability.CODE_GENERATION,
        AgentCapability.DEBUGGING,
        AgentCapability.DOCUMENTATION,
        AgentCapability.TESTING,
        AgentCapability.ARCHITECTURE,
        AgentCapability.CODE_REVIEW,
        AgentCapability.WORKFLOW_AUTOMATION
    ],
    config={
        "default_language": "python",
        "max_execution_time": 300,
        "max_history_size": 100,
        "capability_configs": {
            AgentCapability.CODE_GENERATION: {
                "languages": ["python", "javascript", "typescript"],
                "default_language": "python"
            },
            AgentCapability.DOCUMENTATION: {
                "default_format": "markdown"
            }
        }
    },
    metadata={
        "description": "Unified workflow agent that consolidates all workflow-focused functionality",
        "replaces": [
            "marvin_workflow_agents",
            "code_generation_agent",
            "debugging_agent",
            "documentation_agent",
            "testing_agent",
            "architecture_agent",
            "n8n_architect_agent"
        ],
        "features": [
            "Multiple workflow types",
            "Capability-based execution",
            "Workflow composition",
            "Resource sharing",
            "Consistent interfaces"
        ]
    }
)