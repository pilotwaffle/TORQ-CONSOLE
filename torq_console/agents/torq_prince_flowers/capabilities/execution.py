"""
Execution engine for TORQ Prince Flowers agent.

This module provides task execution capabilities including:
- Tool orchestration
- Parallel execution
- Error handling
- Progress tracking
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime


class ExecutionEngine:
    """Advanced execution engine for tool orchestration and task execution."""

    def __init__(self):
        """Initialize the execution engine."""
        self.logger = logging.getLogger("ExecutionEngine")
        self.active_executions = {}
        self.execution_history = []

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task with the specified configuration.

        Args:
            task: Task configuration with type, parameters, and requirements

        Returns:
            Execution result with status, output, and metadata
        """
        try:
            execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task.get('type', 'unknown')}"

            execution_context = {
                "execution_id": execution_id,
                "task": task,
                "start_time": datetime.now(),
                "status": "running"
            }

            self.active_executions[execution_id] = execution_context

            result = await self._execute_task_by_type(task, execution_context)

            # Update execution context
            execution_context.update({
                "status": "completed" if result.get("success", False) else "failed",
                "end_time": datetime.now(),
                "result": result
            })

            # Move to history
            self.execution_history.append(execution_context)
            del self.active_executions[execution_id]

            return result

        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_id": execution_context.get("execution_id", "unknown")
            }

    async def _execute_task_by_type(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task based on its type."""
        task_type = task.get("type")

        if task_type == "tool_execution":
            return await self._execute_tools(task.get("tools", []), context)
        elif task_type == "parallel_execution":
            return await self._execute_parallel(task.get("subtasks", []), context)
        elif task_type == "sequential_execution":
            return await self._execute_sequential(task.get("subtasks", []), context)
        elif task_type == "conditional_execution":
            return await self._execute_conditional(task, context)
        else:
            return {
                "success": False,
                "error": f"Unknown task type: {task_type}"
            }

    async def _execute_tools(self, tools: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a list of tools."""
        results = []
        tools_used = []

        for tool_config in tools:
            try:
                tool_result = await self._execute_single_tool(tool_config, context)
                results.append(tool_result)
                tools_used.append(tool_config.get("tool_name"))

                # If tool execution failed and it's critical, stop execution
                if not tool_result.get("success", False) and tool_config.get("critical", False):
                    return {
                        "success": False,
                        "error": f"Critical tool {tool_config.get('tool_name')} failed",
                        "partial_results": results
                    }

            except Exception as e:
                self.logger.error(f"Error executing tool {tool_config.get('tool_name')}: {e}")
                results.append({
                    "tool_name": tool_config.get("tool_name"),
                    "success": False,
                    "error": str(e)
                })

        success_count = sum(1 for r in results if r.get("success", False))
        overall_success = success_count == len(tools)

        return {
            "success": overall_success,
            "tools_used": tools_used,
            "results": results,
            "summary": f"Executed {success_count}/{len(tools)} tools successfully"
        }

    async def _execute_parallel(self, subtasks: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute subtasks in parallel."""
        try:
            # Create execution tasks
            tasks = [
                self._execute_task_by_type(subtask, context)
                for subtask in subtasks
            ]

            # Execute in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "subtask_id": i,
                        "success": False,
                        "error": str(result)
                    })
                else:
                    processed_results.append({
                        "subtask_id": i,
                        **result
                    })

            success_count = sum(1 for r in processed_results if r.get("success", False))
            overall_success = success_count == len(subtasks)

            return {
                "success": overall_success,
                "parallel_results": processed_results,
                "summary": f"Parallel execution: {success_count}/{len(subtasks)} subtasks successful"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Parallel execution failed: {str(e)}"
            }

    async def _execute_sequential(self, subtasks: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute subtasks sequentially."""
        results = []

        for i, subtask in enumerate(subtasks):
            try:
                result = await self._execute_task_by_type(subtask, context)
                results.append({
                    "subtask_id": i,
                    **result
                })

                # If subtask failed and it's critical, stop execution
                if not result.get("success", False) and subtask.get("critical", False):
                    return {
                        "success": False,
                        "error": f"Critical subtask {i} failed: {result.get('error')}",
                        "partial_results": results
                    }

            except Exception as e:
                self.logger.error(f"Error executing subtask {i}: {e}")
                results.append({
                    "subtask_id": i,
                    "success": False,
                    "error": str(e)
                })

                # Stop on critical failures
                if subtask.get("critical", False):
                    break

        success_count = sum(1 for r in results if r.get("success", False))
        overall_success = success_count == len(subtasks)

        return {
            "success": overall_success,
            "sequential_results": results,
            "summary": f"Sequential execution: {success_count}/{len(subtasks)} subtasks successful"
        }

    async def _execute_conditional(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conditional task logic."""
        try:
            condition = task.get("condition")
            true_task = task.get("true_task")
            false_task = task.get("false_task")

            # Evaluate condition
            condition_result = await self._evaluate_condition(condition, context)

            # Execute based on condition result
            if condition_result:
                if true_task:
                    return await self._execute_task_by_type(true_task, context)
                else:
                    return {"success": True, "message": "Condition true, no true task specified"}
            else:
                if false_task:
                    return await self._execute_task_by_type(false_task, context)
                else:
                    return {"success": True, "message": "Condition false, no false task specified"}

        except Exception as e:
            return {
                "success": False,
                "error": f"Conditional execution failed: {str(e)}"
            }

    async def _execute_single_tool(self, tool_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single tool."""
        tool_name = tool_config.get("tool_name")
        tool_params = tool_config.get("parameters", {})

        # This is a placeholder - actual tool execution would be handled
        # by the specific tool implementations
        return {
            "tool_name": tool_name,
            "success": True,
            "result": f"Executed {tool_name} with params {tool_params}",
            "execution_time": 1.0
        }

    async def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a condition for conditional execution."""
        condition_type = condition.get("type")

        if condition_type == "success_rate":
            threshold = condition.get("threshold", 0.5)
            # In a real implementation, this would check actual success rates
            return True
        elif condition_type == "tool_available":
            tool_name = condition.get("tool_name")
            # Check if tool is available
            return True
        elif condition_type == "context_value":
            key = condition.get("key")
            expected_value = condition.get("value")
            actual_value = context.get(key)
            return actual_value == expected_value
        else:
            # Default to true for unknown condition types
            return True

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the execution engine."""
        try:
            return {
                "healthy": True,
                "active_executions": len(self.active_executions),
                "execution_history": len(self.execution_history),
                "components": {
                    "tool_executor": True,
                    "parallel_executor": True,
                    "sequential_executor": True,
                    "conditional_executor": True
                }
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }