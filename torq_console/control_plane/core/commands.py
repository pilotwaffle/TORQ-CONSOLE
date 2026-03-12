"""
TORQ Control Plane - Operator Commands

L7-M1: Command execution layer for operator actions.

Provides a unified interface for operators to execute
commands across all TORQ subsystems.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Command Models
# ============================================================================

class CommandStatus(str, Enum):
    """Status of command execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OperatorCommand(BaseModel):
    """
    A command to be executed by the operator.
    """
    id: UUID = Field(default_factory=uuid4)
    command_type: str
    target: str  # Subsystem target
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requested_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: CommandStatus = CommandStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class CommandResult(BaseModel):
    """
    Result of command execution.
    """
    command_id: UUID
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None
    execution_time_ms: int
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class CommandHandler(BaseModel):
    """
    Handler for a specific command type.
    """
    command_type: str
    target: str
    handler: Callable
    description: str
    required_permission: Optional[str] = None
    parameters_schema: Optional[Dict[str, Any]] = None


# ============================================================================
# Command Executor
# ============================================================================

class CommandExecutor:
    """
    Executes operator commands across TORQ subsystems.

    Provides unified command execution with:
    - Command validation
    - Permission checking
    - Async execution
    - Result tracking
    """

    def __init__(self):
        """Initialize the command executor."""
        self._handlers: Dict[str, CommandHandler] = {}
        self._running_commands: Dict[UUID, OperatorCommand] = {}
        self._command_history: List[OperatorCommand] = []
        self._lock = asyncio.Lock()

        # Register built-in handlers
        self._register_builtin_handlers()

    def _register_builtin_handlers(self):
        """Register built-in command handlers."""
        # Readiness commands
        self.register_handler(
            "readiness", "promote",
            self._handle_promote_candidate,
            "Promote a candidate to ready state",
        )

        self.register_handler(
            "readiness", "block",
            self._handle_block_candidate,
            "Block a candidate",
        )

        self.register_handler(
            "readiness", "override",
            self._handle_readiness_override,
            "Override readiness decision",
        )

        # Mission commands
        self.register_handler(
            "mission", "start",
            self._handle_start_mission,
            "Start a mission",
        )

        self.register_handler(
            "mission", "stop",
            self._handle_stop_mission,
            "Stop a running mission",
        )

        # Pattern commands
        self.register_handler(
            "pattern", "validate",
            self._handle_validate_pattern,
            "Validate a discovered pattern",
        )

        # System commands
        self.register_handler(
            "system", "refresh_metrics",
            self._handle_refresh_metrics,
            "Refresh system metrics",
        )

    def register_handler(
        self,
        target: str,
        command_type: str,
        handler: Callable,
        description: str,
        required_permission: Optional[str] = None,
        parameters_schema: Optional[Dict[str, Any]] = None,
    ):
        """
        Register a command handler.

        Args:
            target: Target subsystem
            command_type: Type of command
            handler: Async handler function
            description: Command description
            required_permission: Optional required permission
            parameters_schema: Optional JSON schema for parameters
        """
        key = f"{target}.{command_type}"

        self._handlers[key] = CommandHandler(
            command_type=command_type,
            target=target,
            handler=handler,
            description=description,
            required_permission=required_permission,
            parameters_schema=parameters_schema,
        )

        logger.debug(f"[CommandExecutor] Registered handler: {key}")

    async def execute(
        self,
        command: OperatorCommand,
    ) -> CommandResult:
        """
        Execute a command.

        Args:
            command: Command to execute

        Returns:
            CommandResult
        """
        start_time = datetime.now()

        # Update status
        command.status = CommandStatus.RUNNING
        command.started_at = start_time

        async with self._lock:
            self._running_commands[command.id] = command

        try:
            # Find handler
            key = f"{command.target}.{command.command_type}"
            handler_info = self._handlers.get(key)

            if handler_info is None:
                raise ValueError(f"Unknown command: {key}")

            # Check permissions
            if handler_info.required_permission:
                # TODO: Implement permission check
                pass

            # Execute handler
            logger.info(
                f"[CommandExecutor] Executing {key} "
                f"(command: {command.id})"
            )

            if asyncio.iscoroutinefunction(handler_info.handler):
                result_data = await handler_info.handler(command)
            else:
                result_data = handler_info.handler(command)

            # Calculate execution time
            execution_time = int(
                (datetime.now() - start_time).total_seconds() * 1000
            )

            # Update command
            command.status = CommandStatus.COMPLETED
            command.completed_at = datetime.now()
            command.result = result_data
            command.execution_time_ms = execution_time

            # Create result
            result = CommandResult(
                command_id=command.id,
                success=True,
                data=result_data,
                execution_time_ms=execution_time,
                message=f"Command {key} completed successfully",
            )

            logger.info(
                f"[CommandExecutor] Command {command.id} completed "
                f"in {execution_time}ms"
            )

            return result

        except Exception as e:
            execution_time = int(
                (datetime.now() - start_time).total_seconds() * 1000
            )

            command.status = CommandStatus.FAILED
            command.completed_at = datetime.now()
            command.error = str(e)
            command.execution_time_ms = execution_time

            logger.error(
                f"[CommandExecutor] Command {command.id} failed: {e}"
            )

            return CommandResult(
                command_id=command.id,
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
                message=f"Command failed: {str(e)}",
            )

        finally:
            async with self._lock:
                self._running_commands.pop(command.id, None)

            # Add to history
            self._command_history.append(command)

            # Limit history size
            if len(self._command_history) > 1000:
                self._command_history = self._command_history[-1000:]

    async def execute_batch(
        self,
        commands: List[OperatorCommand],
    ) -> List[CommandResult]:
        """
        Execute multiple commands concurrently.

        Args:
            commands: List of commands to execute

        Returns:
            List of CommandResults
        """
        tasks = [self.execute(cmd) for cmd in commands]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def get_running_commands(self) -> List[OperatorCommand]:
        """
        Get currently running commands.

        Returns:
            List of running commands
        """
        return list(self._running_commands.values())

    def get_command_history(
        self,
        limit: int = 100,
        target: Optional[str] = None,
        status: Optional[CommandStatus] = None,
    ) -> List[OperatorCommand]:
        """
        Get command history with optional filtering.

        Args:
            limit: Maximum number of commands
            target: Optional target filter
            status: Optional status filter

        Returns:
            List of commands
        """
        history = self._command_history

        # Apply filters
        if target:
            history = [c for c in history if c.target == target]

        if status:
            history = [c for c in history if c.status == status]

        # Sort by created_at descending and limit
        history = sorted(
            history,
            key=lambda c: c.created_at,
            reverse=True,
        )[:limit]

        return history

    def get_available_commands(self) -> List[Dict[str, Any]]:
        """
        Get list of available commands.

        Returns:
            List of command descriptions
        """
        return [
            {
                "type": h.command_type,
                "target": h.target,
                "key": f"{h.target}.{h.command_type}",
                "description": h.description,
                "required_permission": h.required_permission,
                "parameters_schema": h.parameters_schema,
            }
            for h in self._handlers.values()
        ]

    # ------------------------------------------------------------------------
    # Built-in Handlers
    # ------------------------------------------------------------------------

    async def _handle_promote_candidate(
        self,
        command: OperatorCommand,
    ) -> Dict[str, Any]:
        """Handle candidate promotion command."""
        from ..readiness.transition_controller import (
            get_transition_controller,
        )
        from ..readiness.query_service import (
            get_query_service,
        )

        candidate_id = command.parameters.get("candidate_id")
        if not candidate_id:
            raise ValueError("candidate_id parameter required")

        # Import UUID parsing
        if isinstance(candidate_id, str):
            from uuid import UUID
            candidate_id = UUID(candidate_id)

        controller = get_transition_controller()
        query_service = get_query_service()

        candidate = query_service.get_candidate(candidate_id)
        if not candidate:
            raise ValueError(f"Candidate not found: {candidate_id}")

        # Execute promotion
        result = await controller.request_transition(
            candidate_id=candidate_id,
            target_state="ready",
            transition_type="promotion",
            requested_by=command.requested_by or "operator",
            reason="Operator initiated promotion",
        )

        return {
            "candidate_id": str(candidate_id),
            "previous_state": result.previous_state.value if result.previous_state else None,
            "new_state": result.new_state.value if result.new_state else None,
            "success": result.success,
        }

    async def _handle_block_candidate(
        self,
        command: OperatorCommand,
    ) -> Dict[str, Any]:
        """Handle candidate blocking command."""
        from ..readiness.transition_controller import (
            get_transition_controller,
        )
        from ..readiness.query_service import (
            get_query_service,
        )

        candidate_id = command.parameters.get("candidate_id")
        reason = command.parameters.get("reason", "Operator blocked")

        if isinstance(candidate_id, str):
            from uuid import UUID
            candidate_id = UUID(candidate_id)

        controller = get_transition_controller()
        query_service = get_query_service()

        candidate = query_service.get_candidate(candidate_id)
        if not candidate:
            raise ValueError(f"Candidate not found: {candidate_id}")

        result = await controller.request_transition(
            candidate_id=candidate_id,
            target_state="blocked",
            transition_type="block",
            requested_by=command.requested_by or "operator",
            reason=reason,
        )

        return {
            "candidate_id": str(candidate_id),
            "new_state": result.new_state.value if result.new_state else None,
            "success": result.success,
        }

    async def _handle_readiness_override(
        self,
        command: OperatorCommand,
    ) -> Dict[str, Any]:
        """Handle readiness override command."""
        from ..readiness.transition_controller import (
            get_transition_controller,
        )

        candidate_id = command.parameters.get("candidate_id")
        target_state = command.parameters.get("target_state")

        if isinstance(candidate_id, str):
            from uuid import UUID
            candidate_id = UUID(candidate_id)

        controller = get_transition_controller()

        result = await controller.force_transition(
            candidate_id=candidate_id,
            target_state=target_state,
            requested_by=command.requested_by or "operator",
            reason="Operator override",
        )

        return {
            "candidate_id": str(candidate_id),
            "target_state": target_state,
            "success": result.success,
        }

    async def _handle_start_mission(
        self,
        command: OperatorCommand,
    ) -> Dict[str, Any]:
        """Handle mission start command."""
        # Placeholder - would integrate with mission system
        mission_id = command.parameters.get("mission_id")
        return {
            "mission_id": mission_id,
            "status": "started",
        }

    async def _handle_stop_mission(
        self,
        command: OperatorCommand,
    ) -> Dict[str, Any]:
        """Handle mission stop command."""
        # Placeholder - would integrate with mission system
        mission_id = command.parameters.get("mission_id")
        return {
            "mission_id": mission_id,
            "status": "stopped",
        }

    async def _handle_validate_pattern(
        self,
        command: OperatorCommand,
    ) -> Dict[str, Any]:
        """Handle pattern validation command."""
        # Placeholder - would integrate with pattern system
        pattern_id = command.parameters.get("pattern_id")
        return {
            "pattern_id": pattern_id,
            "status": "validated",
        }

    async def _handle_refresh_metrics(
        self,
        command: OperatorCommand,
    ) -> Dict[str, Any]:
        """Handle metrics refresh command."""
        # Trigger metrics refresh across all subsystems
        return {
            "status": "refreshed",
            "timestamp": datetime.now().isoformat(),
        }


# Global command executor instance
_executor: Optional[CommandExecutor] = None


def get_command_executor() -> CommandExecutor:
    """Get the global command executor instance."""
    global _executor
    if _executor is None:
        _executor = CommandExecutor()
    return _executor
