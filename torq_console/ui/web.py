"""
Web UI for TORQ CONSOLE using FastAPI and HTMX.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from ..core.config import TorqConfig


logger = logging.getLogger(__name__)


class WebUI:
    """Web UI server for TORQ CONSOLE."""
    
    def __init__(self, config: TorqConfig):
        self.config = config
        self.app = FastAPI(title="TORQ CONSOLE", version="0.60.0")
        self.server: Optional[uvicorn.Server] = None
        self.active_connections: list[WebSocket] = []
        
        # Setup templates and static files
        self.templates = Jinja2Templates(directory="templates")
        
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            """Home page."""
            return self.templates.TemplateResponse("index.html", {
                "request": request,
                "title": "TORQ CONSOLE",
                "version": "0.60.0"
            })
        
        @self.app.get("/api/status")
        async def get_status():
            """Get system status."""
            return JSONResponse({
                "status": "running",
                "version": "0.60.0",
                "connections": len(self.active_connections),
            })
        
        @self.app.get("/api/tools")
        async def get_tools():
            """Get available MCP tools."""
            # TODO: Integrate with TORQ Console
            return JSONResponse([])
        
        @self.app.get("/api/files")
        async def get_files():
            """Get project files."""
            # TODO: Integrate with TORQ Console
            return JSONResponse([])
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time communication."""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    # Wait for messages from client
                    data = await websocket.receive_text()
                    
                    # Echo back for now
                    await websocket.send_text(f"Echo: {data}")
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
    
    async def start(self) -> None:
        """Start the web UI server."""
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.config.ui.web_ui_port,
            log_level="info",
        )
        self.server = uvicorn.Server(config)
        
        # Start server in background
        asyncio.create_task(self.server.serve())
        logger.info(f"Web UI started on port {self.config.ui.web_ui_port}")
    
    async def stop(self) -> None:
        """Stop the web UI server."""
        if self.server:
            self.server.should_exit = True
            await self.server.shutdown()
        logger.info("Web UI stopped")
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        if self.active_connections:
            for connection in self.active_connections.copy():
                try:
                    await connection.send_json(message)
                except Exception:
                    # Remove disconnected clients
                    if connection in self.active_connections:
                        self.active_connections.remove(connection)