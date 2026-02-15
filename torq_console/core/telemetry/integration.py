"""
TORQ Console Telemetry Integration.

Integration layer for adding telemetry to existing TORQ Console components
without breaking existing functionality.
"""

import asyncio
import uuid
import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List
import logging

from .collector import TelemetryCollector, TelemetryConfig, get_telemetry_collector
from .trace import get_trace_manager, trace_agent_run, trace_tool_execution, trace_model_interaction
from .event import (
    TorqEvent, create_agent_run_event, create_tool_execution_event,
    create_model_interaction_event, create_memory_operation_event,
    create_routing_decision_event, create_system_event,
    TorqEventType, AgentStatus, ToolType, ModelProvider, MemoryOperationType
)


class TelemetryIntegration:
    """Integration layer for TORQ Console telemetry."""

    def __init__(self, config: Optional[TelemetryConfig] = None):
        self.config = config or TelemetryConfig()
        self.collector = get_telemetry_collector(self.config)
        self.trace_manager = get_trace_manager()
        self.session_id = str(uuid.uuid4())
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize the telemetry system."""
        if self.config.enabled:
            await self.collector.start()
            self.logger.info(f"Telemetry integration initialized with session_id: {self.session_id}")
        else:
            self.logger.info("Telemetry integration disabled")

    async def shutdown(self):
        """Shutdown the telemetry system."""
        if self.config.enabled:
            await self.collector.stop()
            self.logger.info("Telemetry integration shutdown")

    def create_instrumented_method(
        self,
        original_method: Callable,
        component_name: str,
        method_name: str,
        event_type: Optional[TorqEventType] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Callable:
        """Create an instrumented version of a method with automatic telemetry."""
        if not self.config.enabled:
            return original_method

        async def async_wrapper(*args, **kwargs):
            # Extract context from kwargs or create new
            run_id = kwargs.get('_telemetry_run_id') or str(uuid.uuid4())
            trace_context = kwargs.get('_trace_context')

            # Create event based on type or use generic system event
            if event_type:
                event = self._create_event_from_type(event_type, component_name, method_name, run_id, additional_context)
            else:
                event = create_system_event(
                    session_id=self.session_id,
                    component=component_name,
                    operation=method_name,
                    run_id=run_id,
                    data=additional_context or {}
                )

            # Record start
            start_time = time.time()
            await self.collector.collect_event(event)

            try:
                # Execute original method
                result = await original_method(*args, **kwargs)

                # Record success
                duration_ms = int((time.time() - start_time) * 1000)
                success_event = self._create_completion_event(
                    event_type, component_name, method_name, run_id, True, duration_ms, additional_context
                )
                await self.collector.collect_event(success_event)

                return result

            except Exception as e:
                # Record error
                duration_ms = int((time.time() - start_time) * 1000)
                error_event = self._create_completion_event(
                    event_type, component_name, method_name, run_id, False, duration_ms,
                    {**additional_context, 'error': str(e)} if additional_context else {'error': str(e)}
                )
                await self.collector.collect_event(error_event)
                raise

        def sync_wrapper(*args, **kwargs):
            # For sync methods, use simple timing
            run_id = kwargs.get('_telemetry_run_id') or str(uuid.uuid4())

            event = create_system_event(
                session_id=self.session_id,
                component=component_name,
                operation=method_name,
                run_id=run_id,
                data=additional_context or {}
            )

            start_time = time.time()

            try:
                result = original_method(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)

                success_event = self._create_completion_event(
                    event_type, component_name, method_name, run_id, True, duration_ms, additional_context
                )

                # Collect events asynchronously
                asyncio.create_task(self.collector.collect_event(event))
                asyncio.create_task(self.collector.collect_event(success_event))

                return result

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                error_context = {**additional_context, 'error': str(e)} if additional_context else {'error': str(e)}
                error_event = self._create_completion_event(
                    event_type, component_name, method_name, run_id, False, duration_ms, error_context
                )

                asyncio.create_task(self.collector.collect_event(event))
                asyncio.create_task(self.collector.collect_event(error_event))
                raise

        return async_wrapper if asyncio.iscoroutinefunction(original_method) else sync_wrapper

    def _create_event_from_type(
        self,
        event_type: TorqEventType,
        component_name: str,
        method_name: str,
        run_id: str,
        additional_context: Optional[Dict[str, Any]]
    ) -> TorqEvent:
        """Create an event based on the specified type."""
        if event_type == TorqEventType.AGENT_RUN:
            return create_agent_run_event(
                session_id=self.session_id,
                agent_name=component_name,
                agent_type=additional_context.get('agent_type', 'unknown') if additional_context else 'unknown',
                status=AgentStatus.STARTED,
                run_id=run_id,
                data=additional_context or {}
            )
        elif event_type == TorqEventType.TOOL_EXECUTION:
            return create_tool_execution_event(
                session_id=self.session_id,
                tool_name=component_name,
                tool_type=ToolType.CUSTOM,
                status='started',
                run_id=run_id,
                data=additional_context or {}
            )
        elif event_type == TorqEventType.MODEL_INTERACTION:
            return create_model_interaction_event(
                session_id=self.session_id,
                model_provider=ModelProvider.CUSTOM,
                model_name=component_name,
                prompt_tokens=0,  # Will be updated later
                response_time_ms=0,  # Will be updated later
                run_id=run_id,
                data=additional_context or {}
            )
        else:
            return create_system_event(
                session_id=self.session_id,
                component=component_name,
                operation=method_name,
                run_id=run_id,
                data=additional_context or {}
            )

    def _create_completion_event(
        self,
        event_type: Optional[TorqEventType],
        component_name: str,
        method_name: str,
        run_id: str,
        success: bool,
        duration_ms: int,
        context: Optional[Dict[str, Any]]
    ) -> TorqEvent:
        """Create a completion event."""
        data = context or {}
        data.update({
            'success': success,
            'duration_ms': duration_ms,
            'component': component_name,
            'method': method_name
        })

        return create_system_event(
            session_id=self.session_id,
            component=component_name,
            operation=f"{method_name}_{'completed' if success else 'failed'}",
            run_id=run_id,
            data=data,
            duration_ms=duration_ms
        )

    async def record_agent_run(
        self,
        agent_name: str,
        agent_type: str,
        status: AgentStatus,
        user_query: Optional[str] = None,
        tools_used: Optional[List[str]] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        error_message: Optional[str] = None,
        run_id: Optional[str] = None,
        **kwargs
    ):
        """Record an agent run event."""
        if not self.config.enabled:
            return

        run_id = run_id or str(uuid.uuid4())

        event = create_agent_run_event(
            session_id=self.session_id,
            agent_name=agent_name,
            agent_type=agent_type,
            status=status,
            user_query=user_query,
            tools_used=tools_used or [],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            error_message=error_message,
            run_id=run_id,
            **kwargs
        )

        await self.collector.collect_event(event)
        return run_id

    async def record_tool_execution(
        self,
        tool_name: str,
        tool_type: ToolType,
        status: str,
        input_parameters: Optional[Dict[str, Any]] = None,
        output_result: Optional[Any] = None,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        run_id: Optional[str] = None,
        **kwargs
    ):
        """Record a tool execution event."""
        if not self.config.enabled:
            return

        event = create_tool_execution_event(
            session_id=self.session_id,
            tool_name=tool_name,
            tool_type=tool_type,
            status=status,
            input_parameters=input_parameters or {},
            output_result=output_result,
            execution_time_ms=execution_time_ms,
            error_message=error_message,
            run_id=run_id,
            **kwargs
        )

        await self.collector.collect_event(event)

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
        run_id: Optional[str] = None,
        **kwargs
    ):
        """Record a model interaction event."""
        if not self.config.enabled:
            return

        event = create_model_interaction_event(
            session_id=self.session_id,
            model_provider=model_provider,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            response_time_ms=response_time_ms,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            error_message=error_message,
            run_id=run_id,
            **kwargs
        )

        await self.collector.collect_event(event)

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
        run_id: Optional[str] = None,
        **kwargs
    ):
        """Record a memory operation event."""
        if not self.config.enabled:
            return

        event = create_memory_operation_event(
            session_id=self.session_id,
            memory_type=memory_type,
            memory_backend=memory_backend,
            operation_type=operation_type,
            operation_time_ms=operation_time_ms,
            key=key,
            keys=keys or [],
            data_size_bytes=data_size_bytes,
            run_id=run_id,
            **kwargs
        )

        await self.collector.collect_event(event)

    async def get_session_statistics(self) -> Dict[str, Any]:
        """Get statistics for the current session."""
        if not self.config.enabled:
            return {'telemetry_enabled': False}

        stats = await self.collector.get_statistics()
        stats['session_id'] = self.session_id
        return stats

    async def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """Get a summary of a specific run."""
        if not self.config.enabled:
            return {'telemetry_enabled': False}

        return await self.collector.get_run_summary(run_id)


# Global telemetry integration instance
_global_telemetry_integration: Optional[TelemetryIntegration] = None


def get_telemetry_integration(config: Optional[TelemetryConfig] = None) -> TelemetryIntegration:
    """Get the global telemetry integration instance."""
    global _global_telemetry_integration
    if _global_telemetry_integration is None:
        _global_telemetry_integration = TelemetryIntegration(config)
    return _global_telemetry_integration


# Decorator for easy method instrumentation
def instrument_method(
    component_name: str,
    method_name: Optional[str] = None,
    event_type: Optional[TorqEventType] = None,
    additional_context: Optional[Dict[str, Any]] = None
):
    """Decorator to automatically instrument methods with telemetry."""
    def decorator(func: Callable) -> Callable:
        integration = get_telemetry_integration()
        name = method_name or func.__name__
        return integration.create_instrumented_method(
            func, component_name, name, event_type, additional_context
        )
    return decorator


# Context manager for run tracking
class RunContext:
    """Context manager for tracking a specific run."""

    def __init__(
        self,
        integration: TelemetryIntegration,
        run_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        agent_type: Optional[str] = None,
        **context
    ):
        self.integration = integration
        self.run_id = run_id or str(uuid.uuid4())
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.context = context
        self.start_time = None

    async def __aenter__(self):
        self.start_time = time.time()

        # Record run start
        if self.agent_name and self.agent_type:
            await self.integration.record_agent_run(
                agent_name=self.agent_name,
                agent_type=self.agent_type,
                status=AgentStatus.STARTED,
                run_id=self.run_id,
                **self.context
            )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration_ms = int((time.time() - self.start_time) * 1000)

        # Record run completion
        if self.agent_name and self.agent_type:
            status = AgentStatus.COMPLETED if exc_type is None else AgentStatus.FAILED
            error_message = str(exc_val) if exc_val else None

            await self.integration.record_agent_run(
                agent_name=self.agent_name,
                agent_type=self.agent_type,
                status=status,
                error_message=error_message,
                duration_ms=duration_ms,
                run_id=self.run_id,
                **self.context
            )