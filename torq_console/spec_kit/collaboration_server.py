#!/usr/bin/env python3
"""
Phase 3: Real-time Collaboration Server
WebSocket server for real-time specification collaboration
"""

import asyncio
import json
import logging
import websockets
from typing import Dict, Set, Any, Optional
from datetime import datetime
from dataclasses import asdict

from .ecosystem_intelligence import TeamMember, TeamCollaboration

logger = logging.getLogger(__name__)


class CollaborationServer:
    """WebSocket server for real-time collaboration"""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None
        self.connected_clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.client_sessions: Dict[str, Dict[str, Any]] = {}
        self.collaboration = TeamCollaboration()

    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting collaboration server on {self.host}:{self.port}")

        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        )

        logger.info(f"Collaboration server started on ws://{self.host}:{self.port}")

    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Collaboration server stopped")

    async def handle_client(self, websocket, path):
        """Handle individual client connections"""
        client_id = None
        try:
            # Wait for authentication message
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)

            if auth_data.get("type") != "auth":
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Authentication required"
                }))
                return

            # Authenticate user
            user_data = auth_data.get("user", {})
            client_id = user_data.get("id")

            if not client_id:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "User ID required"
                }))
                return

            # Register client
            self.connected_clients[client_id] = websocket
            self.client_sessions[client_id] = {
                "user": user_data,
                "connected_at": datetime.now(),
                "active_sessions": set(),
                "current_spec": None
            }

            # Update collaboration system
            self.collaboration.websocket_connections[client_id] = websocket

            # Send authentication success
            await websocket.send(json.dumps({
                "type": "auth_success",
                "client_id": client_id,
                "server_time": datetime.now().isoformat()
            }))

            logger.info(f"Client {client_id} connected")

            # Handle messages
            async for message in websocket:
                await self.handle_message(client_id, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            # Clean up client
            if client_id:
                await self.cleanup_client(client_id)

    async def handle_message(self, client_id: str, message: str):
        """Handle incoming messages from clients"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "ping":
                await self.send_to_client(client_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

            elif message_type == "join_session":
                await self.handle_join_session(client_id, data)

            elif message_type == "leave_session":
                await self.handle_leave_session(client_id, data)

            elif message_type == "edit_specification":
                await self.handle_edit_specification(client_id, data)

            elif message_type == "lock_section":
                await self.handle_lock_section(client_id, data)

            elif message_type == "unlock_section":
                await self.handle_unlock_section(client_id, data)

            elif message_type == "cursor_position":
                await self.handle_cursor_position(client_id, data)

            elif message_type == "user_typing":
                await self.handle_user_typing(client_id, data)

            elif message_type == "get_session_info":
                await self.handle_get_session_info(client_id, data)

            else:
                await self.send_to_client(client_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })

        except json.JSONDecodeError:
            await self.send_to_client(client_id, {
                "type": "error",
                "message": "Invalid JSON message"
            })
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
            await self.send_to_client(client_id, {
                "type": "error",
                "message": "Internal server error"
            })

    async def handle_join_session(self, client_id: str, data: Dict[str, Any]):
        """Handle client joining collaboration session"""
        session_id = data.get("session_id")
        spec_id = data.get("specification_id")

        if not session_id or not spec_id:
            await self.send_to_client(client_id, {
                "type": "error",
                "message": "Session ID and specification ID required"
            })
            return

        # Get user info
        user_data = self.client_sessions[client_id]["user"]
        member = TeamMember(
            id=client_id,
            name=user_data.get("name", "Unknown"),
            email=user_data.get("email", ""),
            role=user_data.get("role", "member")
        )

        # Check if session exists, create if not
        if session_id not in self.collaboration.active_sessions:
            await self.collaboration.start_collaboration_session(spec_id, member)
        else:
            success = await self.collaboration.join_collaboration_session(session_id, member)
            if not success:
                await self.send_to_client(client_id, {
                    "type": "error",
                    "message": "Failed to join session"
                })
                return

        # Update client session
        self.client_sessions[client_id]["active_sessions"].add(session_id)
        self.client_sessions[client_id]["current_spec"] = spec_id

        # Send session info
        session = self.collaboration.active_sessions[session_id]
        await self.send_to_client(client_id, {
            "type": "session_joined",
            "session_id": session_id,
            "specification_id": spec_id,
            "participants": [asdict(p) for p in session.participants],
            "lock_holders": session.lock_holders,
            "concurrent_editors": session.concurrent_editors
        })

    async def handle_leave_session(self, client_id: str, data: Dict[str, Any]):
        """Handle client leaving collaboration session"""
        session_id = data.get("session_id")

        if session_id in self.client_sessions[client_id]["active_sessions"]:
            self.client_sessions[client_id]["active_sessions"].remove(session_id)

            # Update collaboration session
            if session_id in self.collaboration.active_sessions:
                session = self.collaboration.active_sessions[session_id]
                session.participants = [
                    p for p in session.participants if p.id != client_id
                ]
                session.concurrent_editors = len(session.participants)

                # Broadcast leave event
                await self.collaboration._broadcast_session_event(session_id, {
                    "type": "member_left",
                    "member_id": client_id,
                    "concurrent_editors": session.concurrent_editors,
                    "timestamp": datetime.now().isoformat()
                })

            await self.send_to_client(client_id, {
                "type": "session_left",
                "session_id": session_id
            })

    async def handle_edit_specification(self, client_id: str, data: Dict[str, Any]):
        """Handle specification edit from client"""
        session_id = data.get("session_id")
        edit_data = data.get("edit_data", {})

        if session_id not in self.client_sessions[client_id]["active_sessions"]:
            await self.send_to_client(client_id, {
                "type": "error",
                "message": "Not in collaboration session"
            })
            return

        # Process edit through collaboration system
        result = await self.collaboration.handle_collaborative_edit(
            session_id, client_id, edit_data
        )

        await self.send_to_client(client_id, {
            "type": "edit_result",
            "session_id": session_id,
            "result": result
        })

    async def handle_lock_section(self, client_id: str, data: Dict[str, Any]):
        """Handle section lock request"""
        session_id = data.get("session_id")
        section = data.get("section")

        if session_id not in self.client_sessions[client_id]["active_sessions"]:
            await self.send_to_client(client_id, {
                "type": "error",
                "message": "Not in collaboration session"
            })
            return

        success = await self.collaboration.lock_specification_section(
            session_id, client_id, section
        )

        await self.send_to_client(client_id, {
            "type": "lock_result",
            "session_id": session_id,
            "section": section,
            "success": success
        })

    async def handle_unlock_section(self, client_id: str, data: Dict[str, Any]):
        """Handle section unlock request"""
        session_id = data.get("session_id")
        section = data.get("section")

        success = await self.collaboration.unlock_specification_section(
            session_id, client_id, section
        )

        await self.send_to_client(client_id, {
            "type": "unlock_result",
            "session_id": session_id,
            "section": section,
            "success": success
        })

    async def handle_cursor_position(self, client_id: str, data: Dict[str, Any]):
        """Handle cursor position update"""
        session_id = data.get("session_id")
        position = data.get("position", {})

        if session_id in self.collaboration.active_sessions:
            # Broadcast cursor position to other participants
            await self.collaboration._broadcast_session_event(session_id, {
                "type": "cursor_update",
                "user_id": client_id,
                "position": position,
                "timestamp": datetime.now().isoformat()
            })

    async def handle_user_typing(self, client_id: str, data: Dict[str, Any]):
        """Handle user typing indicator"""
        session_id = data.get("session_id")
        section = data.get("section")
        is_typing = data.get("is_typing", False)

        if session_id in self.collaboration.active_sessions:
            # Broadcast typing indicator
            await self.collaboration._broadcast_session_event(session_id, {
                "type": "typing_indicator",
                "user_id": client_id,
                "section": section,
                "is_typing": is_typing,
                "timestamp": datetime.now().isoformat()
            })

    async def handle_get_session_info(self, client_id: str, data: Dict[str, Any]):
        """Handle request for session information"""
        session_id = data.get("session_id")

        if session_id in self.collaboration.active_sessions:
            session = self.collaboration.active_sessions[session_id]
            await self.send_to_client(client_id, {
                "type": "session_info",
                "session_id": session_id,
                "specification_id": session.specification_id,
                "participants": [asdict(p) for p in session.participants],
                "lock_holders": session.lock_holders,
                "concurrent_editors": session.concurrent_editors,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "total_changes": len(session.changes)
            })
        else:
            await self.send_to_client(client_id, {
                "type": "error",
                "message": "Session not found"
            })

    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if client_id in self.connected_clients:
            try:
                await self.connected_clients[client_id].send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Client {client_id} connection closed")
                await self.cleanup_client(client_id)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")

    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any], exclude: str = None):
        """Broadcast message to all clients in a session"""
        if session_id in self.collaboration.active_sessions:
            session = self.collaboration.active_sessions[session_id]
            for participant in session.participants:
                if participant.id != exclude and participant.id in self.connected_clients:
                    await self.send_to_client(participant.id, message)

    async def cleanup_client(self, client_id: str):
        """Clean up client connection"""
        # Remove from connected clients
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]

        # Remove from collaboration system
        if client_id in self.collaboration.websocket_connections:
            del self.collaboration.websocket_connections[client_id]

        # Leave all sessions
        if client_id in self.client_sessions:
            active_sessions = self.client_sessions[client_id]["active_sessions"].copy()
            for session_id in active_sessions:
                await self.handle_leave_session(client_id, {"session_id": session_id})

            del self.client_sessions[client_id]

        logger.info(f"Cleaned up client {client_id}")

    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            "connected_clients": len(self.connected_clients),
            "active_sessions": len(self.collaboration.active_sessions),
            "total_participants": sum(
                len(session.participants)
                for session in self.collaboration.active_sessions.values()
            ),
            "server_uptime": (datetime.now() - getattr(self, 'start_time', datetime.now())).total_seconds(),
            "timestamp": datetime.now().isoformat()
        }


class CollaborationManager:
    """Manager for collaboration server lifecycle"""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.server = CollaborationServer(host, port)
        self.running = False

    async def start(self):
        """Start collaboration manager"""
        if not self.running:
            self.server.start_time = datetime.now()
            await self.server.start_server()
            self.running = True
            logger.info("Collaboration manager started")

    async def stop(self):
        """Stop collaboration manager"""
        if self.running:
            await self.server.stop_server()
            self.running = False
            logger.info("Collaboration manager stopped")

    async def run_forever(self):
        """Run collaboration server indefinitely"""
        if not self.running:
            await self.start()

        try:
            # Keep server running
            await self.server.server.wait_closed()
        except KeyboardInterrupt:
            logger.info("Collaboration server interrupted")
        finally:
            await self.stop()

    def get_stats(self) -> Dict[str, Any]:
        """Get collaboration manager statistics"""
        return {
            "running": self.running,
            "server_stats": self.server.get_server_stats() if self.running else None
        }


# Standalone server runner
async def run_collaboration_server(host: str = "localhost", port: int = 8765):
    """Run collaboration server as standalone application"""
    manager = CollaborationManager(host, port)

    try:
        logger.info(f"Starting standalone collaboration server on {host}:{port}")
        await manager.run_forever()
    except Exception as e:
        logger.error(f"Collaboration server error: {e}")
    finally:
        await manager.stop()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TORQ Console Collaboration Server")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run server
    asyncio.run(run_collaboration_server(args.host, args.port))