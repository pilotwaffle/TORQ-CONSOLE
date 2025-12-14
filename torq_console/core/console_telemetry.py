"""
TORQ Console Core Telemetry Integration.

Integrates telemetry into the core console functionality without
breaking existing behavior.
"""

import asyncio
import uuid
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

from .telemetry.integration import (
    TelemetryIntegration, get_telemetry_integration, RunContext,
    instrument_method
)
from .telemetry.event import (
    TorqEventType, AgentStatus, ToolType, ModelProvider, MemoryOperationType
)
from .telemetry.trace import trace_agent_run, trace_tool_execution, trace_model_interaction


class ConsoleTelemetryMixin:
    """Mixin class to add telemetry to console components."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._telemetry_integration: Optional[TelemetryIntegration] = None
        self._current_run_id: Optional[str] = None
        self._session_id: str = str(uuid.uuid4())

    async def initialize_telemetry(self, config=None):
        """Initialize telemetry system."""
        try:
            self._telemetry_integration = get_telemetry_integration(config)
            await self._telemetry_integration.initialize()
            self.logger.info("Console telemetry initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize telemetry: {e}")
            self._telemetry_integration = None

    async def shutdown_telemetry(self):
        """Shutdown telemetry system."""
        if self._telemetry_integration:
            await self._telemetry_integration.shutdown()

    def _is_telemetry_enabled(self) -> bool:
        """Check if telemetry is enabled."""
        return self._telemetry_integration is not None

    async def start_agent_run(
        self,
        agent_name: str,
        agent_type: str,
        user_query: Optional[str] = None,
        **context
    ) -> str:
        """Start tracking an agent run."""
        if not self._is_telemetry_enabled():
            return str(uuid.uuid4())

        self._current_run_id = str(uuid.uuid4())

        await self._telemetry_integration.record_agent_run(
            agent_name=agent_name,
            agent_type=agent_type,
            status=AgentStatus.STARTED,
            user_query=user_query,
            run_id=self._current_run_id,
            **context
        )

        return self._current_run_id

    async def complete_agent_run(
        self,
        success: bool = True,
        error_message: Optional[str] = None,
        tools_used: Optional[List[str]] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        **additional_context
    ):
        """Complete the current agent run."""
        if not self._is_telemetry_enabled() or not self._current_run_id:
            return

        status = AgentStatus.COMPLETED if success else AgentStatus.FAILED

        await self._telemetry_integration.record_agent_run(
            agent_name="",  # Will be filled from previous event
            agent_type="",  # Will be filled from previous event
            status=status,
            success=success,
            error_message=error_message,
            tools_used=tools_used or [],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            run_id=self._current_run_id,
            **additional_context
        )

        self._current_run_id = None

    async def record_tool_execution(
        self,
        tool_name: str,
        tool_type: ToolType,
        status: str,
        input_parameters: Optional[Dict[str, Any]] = None,
        output_result: Optional[Any] = None,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        **context
    ):
        """Record a tool execution event."""
        if not self._is_telemetry_enabled():
            return

        await self._telemetry_integration.record_tool_execution(
            tool_name=tool_name,
            tool_type=tool_type,
            status=status,
            input_parameters=input_parameters,
            output_result=output_result,
            execution_time_ms=execution_time_ms,
            error_message=error_message,
            run_id=self._current_run_id,
            **context
        )

    async def record_model_interaction(
        self,
        model_provider: ModelProvider,
        model_name: str,
        prompt_tokens: int,
        response_time_ms: int,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        cost_usd: Optional[float] = None,
        error_message: Optional[str] = None,
        **context
    ):
        """Record a model interaction event."""
        if not self._is_telemetry_enabled():
            return

        await self._telemetry_integration.record_model_interaction(
            model_provider=model_provider,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            response_time_ms=response_time_ms,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            error_message=error_message,
            run_id=self._current_run_id,
            **context
        )

    async def record_memory_operation(
        self,
        memory_type: str,
        memory_backend: str,
        operation_type: MemoryOperationType,
        operation_time_ms: int,
        key: Optional[str] = None,
        keys: Optional[List[str]] = None,
        data_size_bytes: Optional[int] = None,
        error_message: Optional[str] = None,
        **context
    ):
        """Record a memory operation event."""
        if not self._is_telemetry_enabled():
            return

        await self._telemetry_integration.record_memory_operation(
            memory_type=memory_type,
            memory_backend=memory_backend,
            operation_type=operation_type,
            operation_time_ms=operation_time_ms,
            key=key,
            keys=keys,
            data_size_bytes=data_size_bytes,
            error_message=error_message,
            run_id=self._current_run_id,
            **context
        )

    def get_run_context(self) -> Dict[str, Any]:
        """Get current run context for telemetry."""
        return {
            'session_id': self._session_id,
            'run_id': self._current_run_id,
            'telemetry_enabled': self._is_telemetry_enabled()
        }

    async def get_telemetry_statistics(self) -> Dict[str, Any]:
        """Get telemetry statistics for current session."""
        if not self._is_telemetry_enabled():
            return {'telemetry_enabled': False}

        return await self._telemetry_integration.get_session_statistics()

    async def get_run_summary(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary for a specific run."""
        if not self._is_telemetry_enabled():
            return {'telemetry_enabled': False}

        target_run_id = run_id or self._current_run_id
        if not target_run_id:
            return {'error': 'No run ID specified or available'}

        return await self._telemetry_integration.get_run_summary(target_run_id)


def instrument_console_method(method_name: str, event_type: Optional[TorqEventType] = None):
    """Decorator to instrument console methods."""
    def decorator(func):
        if not hasattr(func, '__self__'):  # Not a bound method
            return func

        async def async_wrapper(self, *args, **kwargs):
            # Add telemetry context
            if hasattr(self, '_telemetry_integration') and self._telemetry_integration:
                kwargs['_telemetry_run_id'] = getattr(self, '_current_run_id', None)
                kwargs['_session_id'] = getattr(self, '_session_id', None)

            start_time = time.time()
            try:
                result = await func(self, *args, **kwargs)

                # Record success if telemetry is enabled
                if hasattr(self, '_telemetry_integration') and self._telemetry_integration:
                    duration_ms = int((time.time() - start_time) * 1000)
                    await self._telemetry_integration.collector.collect_event(
                        self._telemetry_integration.create_system_event(
                            session_id=self._session_id,
                            component='console',
                            operation=f"{method_name}_completed",
                            run_id=getattr(self, '_current_run_id', None),
                            data={
                                'duration_ms': duration_ms,
                                'success': True,
                                'method': method_name
                            }
                        )
                    )

                return result

            except Exception as e:
                # Record error if telemetry is enabled
                if hasattr(self, '_telemetry_integration') and self._telemetry_integration:
                    duration_ms = int((time.time() - start_time) * 1000)
                    await self._telemetry_integration.collector.collect_event(
                        self._telemetry_integration.create_system_event(
                            session_id=self._session_id,
                            component='console',
                            operation=f"{method_name}_failed",
                            run_id=getattr(self, '_current_run_id', None),
                            data={
                                'duration_ms': duration_ms,
                                'success': False,
                                'error': str(e),
                                'method': method_name
                            }
                        )
                    )
                raise

        def sync_wrapper(self, *args, **kwargs):
            # Add telemetry context
            if hasattr(self, '_telemetry_integration') and self._telemetry_integration:
                kwargs['_telemetry_run_id'] = getattr(self, '_current_run_id', None)
                kwargs['_session_id'] = getattr(self, '_session_id', None)

            start_time = time.time()
            try:
                result = func(self, *args, **kwargs)

                # Record success if telemetry is enabled (async)
                if hasattr(self, '_telemetry_integration') and self._telemetry_integration:
                    duration_ms = int((time.time() - start_time) * 1000)
                    asyncio.create_task(
                        self._telemetry_integration.collector.collect_event(
                            self._telemetry_integration.create_system_event(
                                session_id=self._session_id,
                                component='console',
                                operation=f"{method_name}_completed",
                                run_id=getattr(self, '_current_run_id', None),
                                data={
                                    'duration_ms': duration_ms,
                                    'success': True,
                                    'method': method_name
                                }
                            )
                        )
                    )

                return result

            except Exception as e:
                # Record error if telemetry is enabled (async)
                if hasattr(self, '_telemetry_integration') and self._telemetry_integration:
                    duration_ms = int((time.time() - start_time) * 1000)
                    asyncio.create_task(
                        self._telemetry_integration.collector.collect_event(
                            self._telemetry_integration.create_system_event(
                                session_id=self._session_id,
                                component='console',
                                operation=f"{method_name}_failed",
                                run_id=getattr(self, '_current_run_id', None),
                                data={
                                    'duration_ms': duration_ms,
                                    'success': False,
                                    'error': str(e),
                                    'method': method_name
                                }
                            )
                        )
                    )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator