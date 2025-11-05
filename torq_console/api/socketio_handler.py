"""
TORQ Console Socket.IO Handler

Real-time event handling for WebSocket communication with Cursor 2.0 UI.
Manages chat messages, agent status updates, and real-time notifications.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from datetime import datetime
import asyncio

import socketio

from torq_console.agents.marvin_prince_flowers import create_prince_flowers_agent
from torq_console.agents.marvin_orchestrator import (
    get_orchestrator,
    OrchestrationMode,
)
from torq_console.agents.marvin_query_router import create_query_router

# Configure logging
logger = logging.getLogger("TORQ.API.SocketIO")


class SocketIOHandler:
    """
    Handles Socket.IO events for real-time communication.

    Manages:
    - Client connections and disconnections
    - Chat message routing to agents
    - Agent status updates
    - Real-time response streaming
    - Error handling and recovery
    """

    def __init__(self, sio_server: socketio.AsyncServer) -> None:
        """
        Initialize Socket.IO handler.

        Args:
            sio_server: Socket.IO AsyncServer instance.
        """
        self.sio = sio_server
        self.connected_clients: dict[str, dict[str, Any]] = {}

        # Initialize agents
        self.orchestrator = get_orchestrator()
        self.query_router = create_query_router()
        self.prince_flowers = create_prince_flowers_agent()

        # Register event handlers
        self._register_handlers()

        logger.info("Socket.IO handler initialized")

    def _register_handlers(self) -> None:
        """Register all Socket.IO event handlers."""

        @self.sio.event
        async def connect(sid: str, environ: dict[str, Any]) -> None:
            """
            Handle client connection.

            Args:
                sid: Session ID for the connected client.
                environ: WSGI environment dictionary.
            """
            await self._handle_connect(sid, environ)

        @self.sio.event
        async def disconnect(sid: str) -> None:
            """
            Handle client disconnection.

            Args:
                sid: Session ID for the disconnected client.
            """
            await self._handle_disconnect(sid)

        @self.sio.event
        async def chat_message(sid: str, data: dict[str, Any]) -> None:
            """
            Handle incoming chat message.

            Args:
                sid: Session ID of the sender.
                data: Message data containing 'message', 'agent_id', etc.
            """
            await self._handle_chat_message(sid, data)

        @self.sio.event
        async def request_agent_status(sid: str, data: dict[str, Any]) -> None:
            """
            Handle agent status request.

            Args:
                sid: Session ID of the requester.
                data: Request data containing 'agent_id'.
            """
            await self._handle_agent_status_request(sid, data)

        @self.sio.event
        async def cancel_request(sid: str, data: dict[str, Any]) -> None:
            """
            Handle request cancellation.

            Args:
                sid: Session ID of the requester.
                data: Cancellation data containing 'request_id'.
            """
            await self._handle_cancel_request(sid, data)

        logger.info("Socket.IO event handlers registered")

    async def initialize(self) -> None:
        """Initialize handler resources on server startup."""
        logger.info("Socket.IO handler resources initialized")

    async def cleanup(self) -> None:
        """Cleanup handler resources on server shutdown."""
        # Disconnect all clients gracefully
        for sid in list(self.connected_clients.keys()):
            try:
                await self.sio.disconnect(sid)
            except Exception as e:
                logger.error(f"Error disconnecting client {sid}: {e}")

        self.connected_clients.clear()
        logger.info("Socket.IO handler cleanup complete")

    async def _handle_connect(self, sid: str, environ: dict[str, Any]) -> None:
        """
        Handle new client connection.

        Args:
            sid: Session ID.
            environ: Environment information.
        """
        try:
            # Store client information
            self.connected_clients[sid] = {
                "connected_at": datetime.now().isoformat(),
                "user_agent": environ.get("HTTP_USER_AGENT", "unknown"),
                "active_requests": [],
            }

            logger.info(f"Client connected: {sid}")

            # Send welcome message
            await self.sio.emit(
                "connected",
                {
                    "sid": sid,
                    "message": "Connected to TORQ Console",
                    "timestamp": datetime.now().isoformat(),
                    "available_agents": [
                        "prince_flowers",
                        "orchestrator",
                        "query_router",
                    ],
                },
                room=sid,
            )

            # Broadcast agent status
            await self._broadcast_agent_status()

        except Exception as e:
            logger.error(f"Error handling connection for {sid}: {e}", exc_info=True)
            await self._emit_error(sid, "connection_error", str(e))

    async def _handle_disconnect(self, sid: str) -> None:
        """
        Handle client disconnection.

        Args:
            sid: Session ID.
        """
        try:
            if sid in self.connected_clients:
                client_info = self.connected_clients.pop(sid)
                logger.info(
                    f"Client disconnected: {sid} "
                    f"(connected at {client_info['connected_at']})"
                )
            else:
                logger.warning(f"Unknown client disconnected: {sid}")

        except Exception as e:
            logger.error(f"Error handling disconnect for {sid}: {e}", exc_info=True)

    async def _handle_chat_message(self, sid: str, data: dict[str, Any]) -> None:
        """
        Handle incoming chat message and route to appropriate agent.

        Args:
            sid: Session ID.
            data: Message data.

        Expected data format:
            {
                "message": str,
                "agent_id": str (optional),
                "context": dict (optional),
                "mode": str (optional),
                "request_id": str (optional)
            }
        """
        try:
            # Validate message data
            message = data.get("message")
            if not message or not isinstance(message, str):
                await self._emit_error(
                    sid,
                    "invalid_message",
                    "Message text is required",
                )
                return

            agent_id = data.get("agent_id", "prince_flowers")
            context = data.get("context", {})
            mode = data.get("mode", "single_agent")
            request_id = data.get("request_id", f"req_{datetime.now().timestamp()}")

            logger.info(
                f"Chat message from {sid}: '{message[:50]}...' -> {agent_id} ({mode})"
            )

            # Track active request
            if sid in self.connected_clients:
                self.connected_clients[sid]["active_requests"].append(request_id)

            # Emit acknowledgment
            await self.sio.emit(
                "message_received",
                {
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat(),
                },
                room=sid,
            )

            # Emit agent typing indicator
            await self.sio.emit(
                "agent_typing",
                {
                    "agent_id": agent_id,
                    "request_id": request_id,
                },
                room=sid,
            )

            # Process message through orchestrator
            orchestration_modes = {
                "single_agent": OrchestrationMode.SINGLE_AGENT,
                "multi_agent": OrchestrationMode.MULTI_AGENT,
                "pipeline": OrchestrationMode.PIPELINE,
                "parallel": OrchestrationMode.PARALLEL,
            }

            selected_mode = orchestration_modes.get(
                mode,
                OrchestrationMode.SINGLE_AGENT,
            )

            result = await self.orchestrator.process_query(
                message,
                context=context,
                mode=selected_mode,
            )

            # Extract response
            if isinstance(result.primary_response, str):
                response_text = result.primary_response
            else:
                response_text = str(result.primary_response)

            # Remove from active requests
            if sid in self.connected_clients:
                active = self.connected_clients[sid]["active_requests"]
                if request_id in active:
                    active.remove(request_id)

            # Emit agent response
            await self.sio.emit(
                "agent_response",
                {
                    "request_id": request_id,
                    "agent_id": agent_id,
                    "response": response_text,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "mode": mode,
                        "success": result.success,
                        "routing_decision": (
                            {
                                "primary_agent": result.routing_decision.primary_agent,
                                "capabilities": [
                                    cap.value
                                    for cap in result.routing_decision.capabilities_needed
                                ],
                            }
                            if result.routing_decision
                            else None
                        ),
                        **result.metadata,
                    },
                },
                room=sid,
            )

            logger.info(f"Response sent to {sid} for request {request_id}")

        except Exception as e:
            logger.error(
                f"Error handling chat message from {sid}: {e}",
                exc_info=True,
            )

            # Remove from active requests
            if sid in self.connected_clients:
                active = self.connected_clients[sid]["active_requests"]
                request_id = data.get("request_id")
                if request_id and request_id in active:
                    active.remove(request_id)

            await self._emit_error(
                sid,
                "message_processing_error",
                str(e),
                {"request_id": data.get("request_id")},
            )

    async def _handle_agent_status_request(
        self,
        sid: str,
        data: dict[str, Any],
    ) -> None:
        """
        Handle request for agent status.

        Args:
            sid: Session ID.
            data: Request data with optional 'agent_id'.
        """
        try:
            agent_id = data.get("agent_id")

            if agent_id:
                # Get specific agent status
                status = await self._get_agent_status(agent_id)
            else:
                # Get all agents status
                status = {
                    "prince_flowers": await self._get_agent_status("prince_flowers"),
                    "orchestrator": await self._get_agent_status("orchestrator"),
                    "query_router": await self._get_agent_status("query_router"),
                }

            await self.sio.emit(
                "agent_status",
                {
                    "agent_id": agent_id,
                    "status": status,
                    "timestamp": datetime.now().isoformat(),
                },
                room=sid,
            )

        except Exception as e:
            logger.error(f"Error handling status request from {sid}: {e}")
            await self._emit_error(sid, "status_request_error", str(e))

    async def _handle_cancel_request(self, sid: str, data: dict[str, Any]) -> None:
        """
        Handle request cancellation.

        Args:
            sid: Session ID.
            data: Cancellation data.
        """
        try:
            request_id = data.get("request_id")

            if not request_id:
                await self._emit_error(sid, "invalid_cancellation", "Request ID required")
                return

            # Remove from active requests
            if sid in self.connected_clients:
                active = self.connected_clients[sid]["active_requests"]
                if request_id in active:
                    active.remove(request_id)

            logger.info(f"Request {request_id} cancelled by {sid}")

            await self.sio.emit(
                "request_cancelled",
                {
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat(),
                },
                room=sid,
            )

        except Exception as e:
            logger.error(f"Error handling cancellation from {sid}: {e}")
            await self._emit_error(sid, "cancellation_error", str(e))

    async def _get_agent_status(self, agent_id: str) -> dict[str, Any]:
        """
        Get status for a specific agent.

        Args:
            agent_id: Agent identifier.

        Returns:
            Status dictionary with agent metrics and state.
        """
        try:
            if agent_id == "prince_flowers":
                metrics = self.prince_flowers.get_metrics()
                return {
                    "id": agent_id,
                    "name": "Prince Flowers",
                    "status": "active",
                    "metrics": metrics,
                }
            elif agent_id == "orchestrator":
                metrics = self.orchestrator.get_comprehensive_metrics()
                return {
                    "id": agent_id,
                    "name": "Agent Orchestrator",
                    "status": "active",
                    "metrics": metrics,
                }
            elif agent_id == "query_router":
                metrics = self.query_router.get_metrics()
                return {
                    "id": agent_id,
                    "name": "Query Router",
                    "status": "active",
                    "metrics": metrics,
                }
            else:
                return {
                    "id": agent_id,
                    "name": "Unknown",
                    "status": "not_found",
                    "metrics": {},
                }

        except Exception as e:
            logger.error(f"Error getting status for {agent_id}: {e}")
            return {
                "id": agent_id,
                "name": "Unknown",
                "status": "error",
                "error": str(e),
                "metrics": {},
            }

    async def _broadcast_agent_status(self) -> None:
        """Broadcast agent status updates to all connected clients."""
        try:
            status_data = {
                "agents": {
                    "prince_flowers": await self._get_agent_status("prince_flowers"),
                    "orchestrator": await self._get_agent_status("orchestrator"),
                    "query_router": await self._get_agent_status("query_router"),
                },
                "timestamp": datetime.now().isoformat(),
            }

            await self.sio.emit("agent_status_change", status_data)
            logger.debug("Broadcasted agent status update")

        except Exception as e:
            logger.error(f"Error broadcasting agent status: {e}")

    async def _emit_error(
        self,
        sid: str,
        error_code: str,
        error_message: str,
        additional_data: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Emit error message to client.

        Args:
            sid: Session ID.
            error_code: Error code identifier.
            error_message: Human-readable error message.
            additional_data: Additional error context.
        """
        error_data = {
            "error_code": error_code,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
        }

        if additional_data:
            error_data.update(additional_data)

        await self.sio.emit("error", error_data, room=sid)

    async def broadcast_system_update(self, update_data: dict[str, Any]) -> None:
        """
        Broadcast system-wide update to all connected clients.

        Args:
            update_data: Update information to broadcast.

        Example:
            >>> await handler.broadcast_system_update({
            ...     "type": "agent_updated",
            ...     "agent_id": "prince_flowers",
            ...     "message": "Agent capabilities enhanced"
            ... })
        """
        try:
            await self.sio.emit(
                "system_update",
                {
                    **update_data,
                    "timestamp": datetime.now().isoformat(),
                },
            )
            logger.info(f"Broadcasted system update: {update_data.get('type')}")

        except Exception as e:
            logger.error(f"Error broadcasting system update: {e}")

    def get_connected_clients_count(self) -> int:
        """
        Get count of connected clients.

        Returns:
            Number of currently connected clients.
        """
        return len(self.connected_clients)

    def get_client_info(self, sid: str) -> Optional[dict[str, Any]]:
        """
        Get information about a connected client.

        Args:
            sid: Session ID.

        Returns:
            Client information dictionary or None if not found.
        """
        return self.connected_clients.get(sid)
