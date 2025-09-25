#!/usr/bin/env python3
"""
Minimal test to verify /api/chat endpoint registration
"""

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import asyncio
from typing import Optional

class DirectChatRequest(BaseModel):
    message: str
    include_context: bool = True
    generate_response: bool = True
    model: Optional[str] = None

# Create minimal FastAPI app
app = FastAPI(title="Minimal Chat Test")

@app.post("/api/chat")
async def direct_chat(request: DirectChatRequest):
    """Minimal chat endpoint for testing"""
    return {
        "success": True,
        "response": f"Echo: {request.message}",
        "agent": "Test Agent",
        "timestamp": "2025-09-24T20:40:00Z"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Minimal Chat Test Server"}

@app.get("/test-routes")
async def test_routes():
    """List all registered routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append(f"{route.methods} {route.path}")
    return {"routes": sorted(routes)}

async def main():
    """Run the minimal test server"""
    print("Starting Minimal Chat Test Server...")
    print("Testing /api/chat endpoint registration")
    print("URL: http://127.0.0.1:8900")
    print("Routes: http://127.0.0.1:8900/test-routes")

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8900,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())