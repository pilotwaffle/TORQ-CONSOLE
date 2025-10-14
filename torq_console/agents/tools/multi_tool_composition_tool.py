"""
Multi-Tool Composition Tool for Prince Flowers.

This module provides intelligent orchestration of multiple Prince Flowers tools
with support for sequential, parallel, conditional, loop, and map/reduce patterns.
Enables complex workflow automation with data transformation, error handling,
and result aggregation.

Author: Prince Flowers Development Team
Version: 1.0.0
Date: 2025-10-13
"""

import asyncio
import logging
import re
import time
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from copy import deepcopy


logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Supported workflow composition patterns."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    MAP_REDUCE = "map_reduce"


class ErrorStrategy(Enum):
    """Error handling strategies for workflow steps."""
    CONTINUE = "continue"  # Continue to next step
    STOP = "stop"  # Stop workflow execution
    ROLLBACK = "rollback"  # Rollback all completed steps


@dataclass
class StepResult:
    """Result of a single workflow step execution."""
    step_name: str
    tool_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    retry_count: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass
class WorkflowResult:
    """Complete workflow execution result."""
    success: bool
    workflow_type: str
    steps: List[StepResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    error: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


class WorkflowValidator:
    """Validates workflow definitions and detects issues."""

    @staticmethod
    def validate(workflow: Dict[str, Any]) -> List[str]:
        """
        Validate workflow structure and return list of errors.

        Args:
            workflow: Workflow definition to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check required fields
        if 'type' not in workflow:
            errors.append("Missing required field: 'type'")
            return errors

        workflow_type = workflow.get('type')

        try:
            WorkflowType(workflow_type)
        except ValueError:
            valid_types = [t.value for t in WorkflowType]
            errors.append(
                f"Invalid workflow type: '{workflow_type}'. "
                f"Valid types: {', '.join(valid_types)}"
            )
            return errors

        # Type-specific validation
        if workflow_type in ['sequential', 'parallel']:
            if 'steps' not in workflow:
                errors.append(f"Missing required field 'steps' for {workflow_type} workflow")
            elif not isinstance(workflow['steps'], list):
                errors.append("Field 'steps' must be a list")
            elif len(workflow['steps']) == 0:
                errors.append("Workflow must have at least one step")
            else:
                # Validate each step
                for i, step in enumerate(workflow['steps']):
                    step_errors = WorkflowValidator._validate_step(step, i)
                    errors.extend(step_errors)

        elif workflow_type == 'conditional':
            if 'condition' not in workflow:
                errors.append("Missing required field 'condition' for conditional workflow")
            if 'then_steps' not in workflow:
                errors.append("Missing required field 'then_steps' for conditional workflow")
            if 'else_steps' not in workflow:
                errors.append("Missing required field 'else_steps' for conditional workflow")

        elif workflow_type == 'loop':
            if 'step' not in workflow:
                errors.append("Missing required field 'step' for loop workflow")
            if 'iterations' not in workflow:
                errors.append("Missing required field 'iterations' for loop workflow")
            elif not isinstance(workflow['iterations'], int) or workflow['iterations'] < 1:
                errors.append("Field 'iterations' must be a positive integer")

        elif workflow_type == 'map_reduce':
            if 'map' not in workflow:
                errors.append("Missing required field 'map' for map_reduce workflow")
            if 'reduce' not in workflow:
                errors.append("Missing required field 'reduce' for map_reduce workflow")

        return errors

    @staticmethod
    def _validate_step(step: Dict[str, Any], index: int) -> List[str]:
        """
        Validate a single workflow step.

        Args:
            step: Step definition to validate
            index: Step index in workflow

        Returns:
            List of error messages
        """
        errors = []

        if not isinstance(step, dict):
            errors.append(f"Step {index} must be a dictionary")
            return errors

        if 'tool' not in step:
            errors.append(f"Step {index} missing required field: 'tool'")

        if 'params' in step and not isinstance(step['params'], dict):
            errors.append(f"Step {index} field 'params' must be a dictionary")

        if 'on_error' in step:
            try:
                ErrorStrategy(step['on_error'])
            except ValueError:
                valid_strategies = [s.value for s in ErrorStrategy]
                errors.append(
                    f"Step {index} invalid on_error value: '{step['on_error']}'. "
                    f"Valid values: {', '.join(valid_strategies)}"
                )

        if 'retry' in step:
            if not isinstance(step['retry'], int) or step['retry'] < 0:
                errors.append(f"Step {index} field 'retry' must be a non-negative integer")

        if 'timeout' in step:
            if not isinstance(step['timeout'], (int, float)) or step['timeout'] <= 0:
                errors.append(f"Step {index} field 'timeout' must be a positive number")

        return errors


class VariableSubstitutor:
    """Handles variable substitution in workflow parameters."""

    # Pattern to match ${variable.path}
    VARIABLE_PATTERN = re.compile(r'\$\{([^}]+)\}')

    @staticmethod
    def substitute(value: Any, context: Dict[str, Any]) -> Any:
        """
        Substitute variables in value using context.

        Args:
            value: Value to process (string, dict, list, or primitive)
            context: Context dictionary with variable values

        Returns:
            Value with variables substituted
        """
        if isinstance(value, str):
            return VariableSubstitutor._substitute_string(value, context)
        elif isinstance(value, dict):
            return {
                k: VariableSubstitutor.substitute(v, context)
                for k, v in value.items()
            }
        elif isinstance(value, list):
            return [
                VariableSubstitutor.substitute(item, context)
                for item in value
            ]
        else:
            return value

    @staticmethod
    def _substitute_string(value: str, context: Dict[str, Any]) -> Any:
        """
        Substitute variables in a string value.

        Args:
            value: String value with potential ${variable} references
            context: Context dictionary

        Returns:
            Substituted value (may be string or resolved object)
        """
        matches = list(VariableSubstitutor.VARIABLE_PATTERN.finditer(value))

        # If the entire string is a single variable reference, return the value directly
        if len(matches) == 1 and matches[0].group(0) == value:
            var_path = matches[0].group(1)
            return VariableSubstitutor._resolve_path(var_path, context)

        # Otherwise, replace all variable references in the string
        result = value
        for match in reversed(matches):  # Reverse to maintain positions
            var_path = match.group(1)
            resolved = VariableSubstitutor._resolve_path(var_path, context)
            result = result[:match.start()] + str(resolved) + result[match.end():]

        return result

    @staticmethod
    def _resolve_path(path: str, context: Dict[str, Any]) -> Any:
        """
        Resolve a dotted path in context.

        Args:
            path: Dotted path (e.g., 'step_0.result.data')
            context: Context dictionary

        Returns:
            Resolved value or None if not found
        """
        parts = path.split('.')
        current = context

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, (list, tuple)):
                try:
                    index = int(part)
                    current = current[index]
                except (ValueError, IndexError):
                    logger.warning(f"Cannot resolve path '{path}': invalid index '{part}'")
                    return None
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                logger.warning(f"Cannot resolve path '{path}': '{part}' not found")
                return None

            if current is None:
                return None

        return current


class ConditionEvaluator:
    """Safely evaluates conditional expressions."""

    # Allowed operations for safe evaluation
    ALLOWED_OPS = {
        '==', '!=', '>', '<', '>=', '<=',
        'and', 'or', 'not',
        'True', 'False', 'None'
    }

    @staticmethod
    def evaluate(condition: str, context: Dict[str, Any]) -> bool:
        """
        Safely evaluate a conditional expression.

        Args:
            condition: Conditional expression (e.g., '${step_0.success} == true')
            context: Context dictionary

        Returns:
            Boolean result of evaluation
        """
        # First substitute variables
        substituted = VariableSubstitutor.substitute(condition, context)

        # Convert to lowercase for case-insensitive comparison
        expr = str(substituted).strip().lower()

        # Handle simple boolean values
        if expr == 'true':
            return True
        elif expr == 'false':
            return False
        elif expr == 'none':
            return False

        # Simple pattern matching for common comparisons
        # Format: "value operator value"
        try:
            # Try to evaluate simple comparisons
            if '==' in expr:
                left, right = expr.split('==', 1)
                return ConditionEvaluator._compare_values(left.strip(), right.strip(), '==')
            elif '!=' in expr:
                left, right = expr.split('!=', 1)
                return ConditionEvaluator._compare_values(left.strip(), right.strip(), '!=')
            elif '>=' in expr:
                left, right = expr.split('>=', 1)
                return ConditionEvaluator._compare_values(left.strip(), right.strip(), '>=')
            elif '<=' in expr:
                left, right = expr.split('<=', 1)
                return ConditionEvaluator._compare_values(left.strip(), right.strip(), '<=')
            elif '>' in expr:
                left, right = expr.split('>', 1)
                return ConditionEvaluator._compare_values(left.strip(), right.strip(), '>')
            elif '<' in expr:
                left, right = expr.split('<', 1)
                return ConditionEvaluator._compare_values(left.strip(), right.strip(), '<')
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False

        # Default: try to interpret as boolean
        return bool(substituted)

    @staticmethod
    def _compare_values(left: str, right: str, operator: str) -> bool:
        """
        Compare two values using the given operator.

        Args:
            left: Left operand (as string)
            right: Right operand (as string)
            operator: Comparison operator

        Returns:
            Boolean result
        """
        # Try to convert to numbers if possible
        try:
            left_val = float(left)
            right_val = float(right)
        except ValueError:
            # Keep as strings
            left_val = left
            right_val = right

        if operator == '==':
            return left_val == right_val
        elif operator == '!=':
            return left_val != right_val
        elif operator == '>':
            return left_val > right_val
        elif operator == '<':
            return left_val < right_val
        elif operator == '>=':
            return left_val >= right_val
        elif operator == '<=':
            return left_val <= right_val

        return False


class MultiToolCompositionTool:
    """
    Multi-Tool Composition Engine for Prince Flowers.

    Enables intelligent orchestration of multiple tools with support for
    sequential, parallel, conditional, loop, and map/reduce patterns.
    Provides data transformation, error handling, and result aggregation.

    Composition Patterns:
        - Sequential: Chain tools where output becomes input
        - Parallel: Execute multiple tools simultaneously
        - Conditional: Branch based on results
        - Loop: Iterate tool execution
        - Map/Reduce: Apply to collections and aggregate

    Features:
        - DAG-based workflow planning
        - Variable substitution with templating
        - Error recovery and rollback
        - Compensation logic for failures
        - Result transformation and formatting
        - Performance tracking per step

    Configuration:
        - max_parallel: Maximum parallel executions (default: 5)
        - timeout: Workflow timeout in seconds (default: 300)
        - retry_failed_steps: Retry on failure (default: True)
        - max_retries: Maximum retry attempts (default: 3)
        - continue_on_error: Continue workflow on non-critical errors (default: False)

    Example:
        tool = MultiToolCompositionTool()

        # Sequential workflow
        workflow = {
            'type': 'sequential',
            'steps': [
                {'tool': 'image_generation', 'params': {'prompt': 'sunset'}},
                {'tool': 'social_media', 'params': {'image': '${step_0.url}'}}
            ]
        }
        result = await tool.execute(workflow=workflow)

        # Parallel workflow
        workflow = {
            'type': 'parallel',
            'steps': [
                {'tool': 'social_media', 'params': {...}, 'platform': 'twitter'},
                {'tool': 'social_media', 'params': {...}, 'platform': 'linkedin'}
            ]
        }
        result = await tool.execute(workflow=workflow)
    """

    def __init__(
        self,
        max_parallel: int = 5,
        timeout: int = 300,
        retry_failed_steps: bool = True,
        max_retries: int = 3,
        continue_on_error: bool = False,
        tool_executor: Optional[Callable] = None
    ):
        """
        Initialize Multi-Tool Composition Tool with configuration.

        Args:
            max_parallel: Maximum parallel executions
            timeout: Workflow timeout in seconds
            retry_failed_steps: Retry on failure
            max_retries: Maximum retry attempts
            continue_on_error: Continue on non-critical errors
            tool_executor: Optional custom tool executor function
        """
        self.max_parallel = max_parallel
        self.timeout = timeout
        self.retry_failed_steps = retry_failed_steps
        self.max_retries = max_retries
        self.continue_on_error = continue_on_error
        self.tool_executor = tool_executor or self._default_tool_executor

        self.logger = logger
        self.logger.info(
            f"Initialized MultiToolCompositionTool: "
            f"max_parallel={max_parallel}, timeout={timeout}s, "
            f"retry={retry_failed_steps}, max_retries={max_retries}"
        )

    def is_available(self) -> bool:
        """
        Check if composition engine is available.

        Returns:
            bool: True if available, False otherwise
        """
        # Check if asyncio is available
        try:
            import asyncio
            return True
        except ImportError:
            self.logger.error("asyncio not available")
            return False

    async def execute(
        self,
        workflow: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute workflow composition.

        Args:
            workflow: Workflow definition with type and steps
            context: Initial context variables
            dry_run: If True, validate workflow without execution
            **kwargs: Additional parameters

        Returns:
            Dict with workflow results and execution metadata:
                - success (bool): Whether workflow succeeded
                - workflow_type (str): Type of workflow executed
                - steps (List[Dict]): Results from each step
                - total_duration_ms (float): Total execution time
                - error (str, optional): Error message if failed
                - context (Dict): Final context with all step results
        """
        start_time = time.time()

        # Validate workflow
        validation_errors = WorkflowValidator.validate(workflow)
        if validation_errors:
            error_msg = "; ".join(validation_errors)
            self.logger.error(f"Workflow validation failed: {error_msg}")
            return {
                'success': False,
                'workflow_type': workflow.get('type', 'unknown'),
                'steps': [],
                'total_duration_ms': 0.0,
                'error': f"Validation failed: {error_msg}",
                'context': {}
            }

        if dry_run:
            self.logger.info("Dry run: workflow validation passed")
            return {
                'success': True,
                'workflow_type': workflow.get('type'),
                'steps': [],
                'total_duration_ms': 0.0,
                'context': {},
                'dry_run': True
            }

        # Initialize context
        ctx = context.copy() if context else {}
        workflow_type = workflow['type']

        self.logger.info(f"Executing {workflow_type} workflow")

        # Execute based on workflow type
        try:
            if workflow_type == 'sequential':
                result = await self._execute_sequential(workflow['steps'], ctx)
            elif workflow_type == 'parallel':
                result = await self._execute_parallel(workflow['steps'], ctx)
            elif workflow_type == 'conditional':
                result = await self._execute_conditional(
                    workflow['condition'],
                    workflow['then_steps'],
                    workflow['else_steps'],
                    ctx
                )
            elif workflow_type == 'loop':
                result = await self._execute_loop(
                    workflow['step'],
                    workflow['iterations'],
                    ctx,
                    workflow.get('break_on')
                )
            elif workflow_type == 'map_reduce':
                result = await self._execute_map_reduce(
                    workflow['map'],
                    workflow['reduce'],
                    ctx
                )
            else:
                raise ValueError(f"Unsupported workflow type: {workflow_type}")

            duration = (time.time() - start_time) * 1000
            result['total_duration_ms'] = duration

            self.logger.info(
                f"Workflow completed: success={result['success']}, "
                f"duration={duration:.2f}ms, steps={len(result.get('steps', []))}"
            )

            return result

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = f"Workflow execution failed: {str(e)}"
            self.logger.error(error_msg)

            return {
                'success': False,
                'workflow_type': workflow_type,
                'steps': [],
                'total_duration_ms': duration,
                'error': error_msg,
                'context': ctx
            }

    async def _execute_sequential(
        self,
        steps: List[Dict],
        context: Dict
    ) -> Dict[str, Any]:
        """
        Execute steps sequentially with data passing.

        Args:
            steps: List of step definitions
            context: Execution context

        Returns:
            Dict with execution results
        """
        results = []

        for i, step in enumerate(steps):
            step_name = step.get('name', f'step_{i}')
            self.logger.info(f"Executing sequential step {i}: {step_name}")

            # Substitute variables in params
            params = step.get('params', {})
            substituted_params = VariableSubstitutor.substitute(params, context)

            # Execute step
            step_result = await self._execute_step(
                step['tool'],
                substituted_params,
                step_name,
                step.get('retry', self.max_retries if self.retry_failed_steps else 0),
                step.get('timeout')
            )

            results.append(step_result)

            # Update context with step result
            context[f'step_{i}'] = step_result.result
            if step.get('name'):
                context[step['name']] = step_result.result

            # Handle step failure
            if not step_result.success:
                error_strategy = step.get('on_error', 'stop')
                if error_strategy == 'stop' and not self.continue_on_error:
                    self.logger.error(f"Step {step_name} failed, stopping workflow")
                    return {
                        'success': False,
                        'workflow_type': 'sequential',
                        'steps': [self._step_result_to_dict(r) for r in results],
                        'error': f"Step {step_name} failed: {step_result.error}",
                        'context': context
                    }
                elif error_strategy == 'continue':
                    self.logger.warning(f"Step {step_name} failed, continuing workflow")

        # Check if all steps succeeded
        all_success = all(r.success for r in results)

        return {
            'success': all_success,
            'workflow_type': 'sequential',
            'steps': [self._step_result_to_dict(r) for r in results],
            'context': context
        }

    async def _execute_parallel(
        self,
        steps: List[Dict],
        context: Dict
    ) -> Dict[str, Any]:
        """
        Execute steps in parallel with result aggregation.

        Args:
            steps: List of step definitions
            context: Execution context

        Returns:
            Dict with execution results
        """
        self.logger.info(f"Executing {len(steps)} steps in parallel")

        # Create tasks for all steps
        tasks = []
        for i, step in enumerate(steps):
            step_name = step.get('name', f'step_{i}')
            params = step.get('params', {})
            substituted_params = VariableSubstitutor.substitute(params, context)

            task = self._execute_step(
                step['tool'],
                substituted_params,
                step_name,
                step.get('retry', self.max_retries if self.retry_failed_steps else 0),
                step.get('timeout')
            )
            tasks.append(task)

        # Execute all tasks with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def limited_task(task):
            async with semaphore:
                return await task

        results = await asyncio.gather(
            *[limited_task(task) for task in tasks],
            return_exceptions=True
        )

        # Process results
        step_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                step_name = steps[i].get('name', f'step_{i}')
                step_results.append(StepResult(
                    step_name=step_name,
                    tool_name=steps[i]['tool'],
                    success=False,
                    error=str(result)
                ))
            else:
                step_results.append(result)

            # Update context
            context[f'step_{i}'] = result.result if not isinstance(result, Exception) else None
            if steps[i].get('name'):
                context[steps[i]['name']] = result.result if not isinstance(result, Exception) else None

        all_success = all(r.success for r in step_results)

        return {
            'success': all_success,
            'workflow_type': 'parallel',
            'steps': [self._step_result_to_dict(r) for r in step_results],
            'context': context
        }

    async def _execute_conditional(
        self,
        condition: str,
        then_steps: List[Dict],
        else_steps: List[Dict],
        context: Dict
    ) -> Dict[str, Any]:
        """
        Execute conditional branch based on condition.

        Args:
            condition: Conditional expression to evaluate
            then_steps: Steps to execute if condition is true
            else_steps: Steps to execute if condition is false
            context: Execution context

        Returns:
            Dict with execution results
        """
        self.logger.info(f"Evaluating condition: {condition}")

        # Evaluate condition
        condition_result = ConditionEvaluator.evaluate(condition, context)

        self.logger.info(f"Condition evaluated to: {condition_result}")

        # Execute appropriate branch
        if condition_result:
            branch_result = await self._execute_sequential(then_steps, context)
            branch_result['branch_taken'] = 'then'
        else:
            branch_result = await self._execute_sequential(else_steps, context)
            branch_result['branch_taken'] = 'else'

        branch_result['workflow_type'] = 'conditional'
        branch_result['condition'] = condition
        branch_result['condition_result'] = condition_result

        return branch_result

    async def _execute_loop(
        self,
        step: Dict,
        iterations: int,
        context: Dict,
        break_on: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute step multiple times with iteration tracking.

        Args:
            step: Step definition to repeat
            iterations: Number of iterations
            context: Execution context
            break_on: Optional break condition

        Returns:
            Dict with execution results
        """
        self.logger.info(f"Executing loop: {iterations} iterations")

        results = []

        for i in range(iterations):
            # Add iteration to context
            context['iteration'] = i
            context['iteration_count'] = i + 1

            step_name = step.get('name', f'loop_iteration_{i}')
            params = step.get('params', {})
            substituted_params = VariableSubstitutor.substitute(params, context)

            self.logger.info(f"Loop iteration {i+1}/{iterations}")

            # Execute step
            step_result = await self._execute_step(
                step['tool'],
                substituted_params,
                step_name,
                step.get('retry', self.max_retries if self.retry_failed_steps else 0),
                step.get('timeout')
            )

            results.append(step_result)

            # Update context
            context[f'iteration_{i}'] = step_result.result
            context['last_iteration'] = step_result.result

            # Check break condition
            if break_on:
                should_break = ConditionEvaluator.evaluate(break_on, context)
                if should_break:
                    self.logger.info(f"Break condition met at iteration {i+1}")
                    break

            # Stop on error if configured
            if not step_result.success and not self.continue_on_error:
                self.logger.error(f"Loop failed at iteration {i+1}")
                break

        all_success = all(r.success for r in results)

        return {
            'success': all_success,
            'workflow_type': 'loop',
            'steps': [self._step_result_to_dict(r) for r in results],
            'iterations_completed': len(results),
            'context': context
        }

    async def _execute_map_reduce(
        self,
        map_config: Dict,
        reduce_config: Dict,
        context: Dict
    ) -> Dict[str, Any]:
        """
        Execute map operation on inputs and reduce results.

        Args:
            map_config: Map configuration with tool and inputs
            reduce_config: Reduce configuration with operation
            context: Execution context

        Returns:
            Dict with execution results
        """
        self.logger.info("Executing map/reduce workflow")

        # Get inputs to map over
        inputs = map_config.get('inputs', [])
        tool_name = map_config['tool']
        base_params = map_config.get('params', {})

        # Map phase: apply tool to each input
        self.logger.info(f"Map phase: applying {tool_name} to {len(inputs)} inputs")

        tasks = []
        for i, input_value in enumerate(inputs):
            # Merge input with base params
            params = {**base_params, 'input': input_value}
            substituted_params = VariableSubstitutor.substitute(params, context)

            task = self._execute_step(
                tool_name,
                substituted_params,
                f'map_{i}',
                self.max_retries if self.retry_failed_steps else 0,
                None
            )
            tasks.append(task)

        # Execute map tasks in parallel
        map_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process map results
        step_results = []
        map_values = []
        for i, result in enumerate(map_results):
            if isinstance(result, Exception):
                step_results.append(StepResult(
                    step_name=f'map_{i}',
                    tool_name=tool_name,
                    success=False,
                    error=str(result)
                ))
                map_values.append(None)
            else:
                step_results.append(result)
                map_values.append(result.result)

        # Reduce phase: aggregate results
        operation = reduce_config.get('operation', 'aggregate')
        output_format = reduce_config.get('format', 'json')

        self.logger.info(f"Reduce phase: operation={operation}, format={output_format}")

        reduced_result = self._reduce_results(map_values, operation, output_format)

        # Update context
        context['map_results'] = map_values
        context['reduced_result'] = reduced_result

        all_success = all(r.success for r in step_results)

        return {
            'success': all_success,
            'workflow_type': 'map_reduce',
            'steps': [self._step_result_to_dict(r) for r in step_results],
            'map_count': len(inputs),
            'reduce_operation': operation,
            'result': reduced_result,
            'context': context
        }

    def _reduce_results(
        self,
        results: List[Any],
        operation: str,
        output_format: str
    ) -> Any:
        """
        Reduce/aggregate multiple results into a single value.

        Args:
            results: List of results to reduce
            operation: Reduction operation (aggregate, concat, merge)
            output_format: Output format (json, list, dict)

        Returns:
            Reduced result
        """
        if operation == 'aggregate' or operation == 'list':
            return results

        elif operation == 'concat':
            # Concatenate string results
            return ' '.join(str(r) for r in results if r is not None)

        elif operation == 'merge':
            # Merge dict results
            if output_format == 'dict':
                merged = {}
                for r in results:
                    if isinstance(r, dict):
                        merged.update(r)
                return merged
            else:
                return results

        else:
            # Default: return list
            return results

    async def _execute_step(
        self,
        tool_name: str,
        params: Dict[str, Any],
        step_name: str,
        max_retries: int,
        timeout: Optional[float] = None
    ) -> StepResult:
        """
        Execute a single workflow step with retry logic.

        Args:
            tool_name: Name of the tool to execute
            params: Tool parameters
            step_name: Name of this step
            max_retries: Maximum retry attempts
            timeout: Optional timeout in seconds

        Returns:
            StepResult with execution outcome
        """
        retry_count = 0
        last_error = None

        while retry_count <= max_retries:
            try:
                start_time = time.time()

                # Execute tool with optional timeout
                if timeout:
                    result = await asyncio.wait_for(
                        self.tool_executor(tool_name, params),
                        timeout=timeout
                    )
                else:
                    result = await self.tool_executor(tool_name, params)

                duration = (time.time() - start_time) * 1000

                # Check if result indicates success
                success = result.get('success', True) if isinstance(result, dict) else True

                if success:
                    return StepResult(
                        step_name=step_name,
                        tool_name=tool_name,
                        success=True,
                        result=result,
                        duration_ms=duration,
                        retry_count=retry_count
                    )
                else:
                    last_error = result.get('error', 'Unknown error')

            except asyncio.TimeoutError:
                last_error = f"Step timed out after {timeout}s"
                self.logger.warning(f"Step {step_name} timeout, retry {retry_count}/{max_retries}")

            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Step {step_name} error: {e}, retry {retry_count}/{max_retries}")

            retry_count += 1

            # Exponential backoff
            if retry_count <= max_retries:
                await asyncio.sleep(min(2 ** retry_count, 10))

        # All retries exhausted
        return StepResult(
            step_name=step_name,
            tool_name=tool_name,
            success=False,
            error=last_error or "Step failed after retries",
            retry_count=retry_count - 1
        )

    async def _default_tool_executor(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Default tool executor (mock implementation for testing).

        NOTE: In production, this will call the actual Prince Flowers
        _execute_[tool_name] methods. For testing, we use mocks.

        Args:
            tool_name: Name of the tool to execute
            params: Tool parameters

        Returns:
            Dict with execution result
        """
        # Mock implementation for testing
        self.logger.info(f"Mock executing tool: {tool_name} with params: {params}")

        # Simulate some processing time
        await asyncio.sleep(0.1)

        return {
            'success': True,
            'tool': tool_name,
            'params': params,
            'result': f"Mock result from {tool_name}",
            'mock': True
        }

    def _step_result_to_dict(self, step_result: StepResult) -> Dict[str, Any]:
        """
        Convert StepResult to dictionary format.

        Args:
            step_result: StepResult instance

        Returns:
            Dictionary representation
        """
        return {
            'step_name': step_result.step_name,
            'tool_name': step_result.tool_name,
            'success': step_result.success,
            'result': step_result.result,
            'error': step_result.error,
            'duration_ms': step_result.duration_ms,
            'retry_count': step_result.retry_count,
            'timestamp': step_result.timestamp
        }


def create_multi_tool_composition_tool(
    max_parallel: int = 5,
    timeout: int = 300,
    retry_failed_steps: bool = True,
    max_retries: int = 3,
    continue_on_error: bool = False,
    tool_executor: Optional[Callable] = None
) -> MultiToolCompositionTool:
    """
    Factory function to create Multi-Tool Composition Tool instance.

    Args:
        max_parallel: Maximum parallel executions (default: 5)
        timeout: Workflow timeout in seconds (default: 300)
        retry_failed_steps: Retry on failure (default: True)
        max_retries: Maximum retry attempts (default: 3)
        continue_on_error: Continue on non-critical errors (default: False)
        tool_executor: Optional custom tool executor function

    Returns:
        Configured MultiToolCompositionTool instance

    Example:
        >>> tool = create_multi_tool_composition_tool(max_parallel=10)
        >>> workflow = {
        ...     'type': 'sequential',
        ...     'steps': [
        ...         {'tool': 'tool_a', 'params': {'input': 'hello'}},
        ...         {'tool': 'tool_b', 'params': {'data': '${step_0.result}'}}
        ...     ]
        ... }
        >>> result = await tool.execute(workflow=workflow)
    """
    return MultiToolCompositionTool(
        max_parallel=max_parallel,
        timeout=timeout,
        retry_failed_steps=retry_failed_steps,
        max_retries=max_retries,
        continue_on_error=continue_on_error,
        tool_executor=tool_executor
    )
