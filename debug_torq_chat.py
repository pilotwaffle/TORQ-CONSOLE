#!/usr/bin/env python3
"""
Debug version of TORQ Console focused on isolating the /api/chat endpoint issue
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

# Simplified DirectChatRequest model
class DirectChatRequest(BaseModel):
    message: str
    include_context: bool = True
    generate_response: bool = True
    model: Optional[str] = None

class SimplifiedTorqWebUI:
    """Simplified TORQ WebUI for debugging chat endpoint issues"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # FastAPI app setup
        self.app = FastAPI(
            title="Debug TORQ CONSOLE Web UI",
            description="Simplified version for debugging chat endpoint",
            version="0.70.0-debug"
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup routes
        self._setup_basic_routes()
        self._setup_chat_routes()

    def _setup_basic_routes(self):
        """Setup basic routes"""

        @self.app.get("/")
        async def root():
            return {"message": "Debug TORQ Console", "version": "0.70.0-debug"}

        @self.app.get("/debug/routes")
        async def debug_routes():
            """List all registered routes"""
            routes = []
            for route in self.app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    routes.append(f"{route.methods} {route.path}")
            return {"routes": sorted(routes), "total": len(routes)}

    def _setup_chat_routes(self):
        """Setup chat routes - simplified version"""

        @self.app.post("/api/chat")
        async def direct_chat(request: DirectChatRequest):
            """
            DEBUG: Simplified direct chat endpoint
            """
            try:
                self.logger.info(f"Direct chat request: {request.message}")

                # Simple response without external dependencies
                response_content = f"DEBUG: Received message '{request.message}'. This is a simplified response for testing the endpoint registration."

                return {
                    "success": True,
                    "response": response_content,
                    "agent": "Debug Agent",
                    "message_received": request.message,
                    "timestamp": "2025-09-24T20:45:00Z",
                    "debug": True
                }

            except Exception as e:
                self.logger.error(f"Direct chat error: {e}")
                return {
                    "success": False,
                    "error": f"Error processing your request: {str(e)}",
                    "response": f"Debug error: {str(e)}",
                    "debug": True
                }

    async def start_server(self, host="127.0.0.1", port=8901):
        """Start the debug server"""
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

async def main():
    """Start debug TORQ Console"""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    print("DEBUG TORQ CONSOLE - Chat Endpoint Testing")
    print("=" * 50)
    print("Starting simplified version to isolate /api/chat endpoint issues")
    print("Server: http://127.0.0.1:8901")
    print("Routes: http://127.0.0.1:8901/debug/routes")
    print("Chat: POST http://127.0.0.1:8901/api/chat")
    print()

    try:
        # Initialize simplified WebUI
        web_ui = SimplifiedTorqWebUI()

        # Start server
        await web_ui.start_server(host="127.0.0.1", port=8901)

    except KeyboardInterrupt:
        print("\nShutting down debug server...")
    except Exception as e:
        logger.error(f"Debug server error: {e}")
        print(f"Failed to start debug server: {e}")

if __name__ == "__main__":
    asyncio.run(main())