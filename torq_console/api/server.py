"""
TORQ Console FastAPI Server

Main FastAPI application with Socket.IO integration for real-time
communication with Cursor 2.0 UI frontend.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from .routes import router
from .socketio_handler import SocketIOHandler

# Try to import workspace routes if available
try:
    from torq_console.workspace.api import router as workspace_router
    from torq_console.workspace.agent_tools_api import router as agent_tools_router
    WORKSPACE_AVAILABLE = True
except ImportError:
    WORKSPACE_AVAILABLE = False
    workspace_router = None
    agent_tools_router = None

# Try to import synthesis routes if available
try:
    from torq_console.synthesis.api import router as synthesis_router
    SYNTHESIS_AVAILABLE = True
except ImportError:
    SYNTHESIS_AVAILABLE = False
    synthesis_router = None

# Try to import evaluation routes if available
try:
    from torq_console.evaluation.api import router as evaluation_router
    EVALUATION_AVAILABLE = True
except ImportError:
    EVALUATION_AVAILABLE = False
    evaluation_router = None

# Try to import learning signal routes if available
try:
    from torq_console.learning.api import router as learning_router
    LEARNING_AVAILABLE = True
except ImportError:
    LEARNING_AVAILABLE = False
    learning_router = None

# Try to import adaptation proposal routes if available
try:
    from torq_console.adaptation.api import router as adaptation_router
    ADAPTATION_AVAILABLE = True
except ImportError:
    ADAPTATION_AVAILABLE = False
    adaptation_router = None

# Try to import behavior experiments routes if available
try:
    from torq_console.experiments.api import router as experiments_router
    EXPERIMENTS_AVAILABLE = True
except ImportError:
    EXPERIMENTS_AVAILABLE = False
    experiments_router = None

# Try to import adaptive telemetry routes if available
try:
    from torq_console.telemetry.api import router as adaptive_telemetry_router
    ADAPTIVE_TELEMETRY_AVAILABLE = True
except ImportError:
    ADAPTIVE_TELEMETRY_AVAILABLE = False
    adaptive_telemetry_router = None

# Try to import strategic memory routes if available
try:
    from torq_console.strategic_memory.api import router as strategic_memory_router
    STRATEGIC_MEMORY_AVAILABLE = True
except ImportError:
    STRATEGIC_MEMORY_AVAILABLE = False
    strategic_memory_router = None

# Try to import mission graph routes if available
try:
    from torq_console.mission_graph.api import router as mission_graph_router
    MISSION_GRAPH_AVAILABLE = True
except ImportError:
    MISSION_GRAPH_AVAILABLE = False
    mission_graph_router = None

# Try to import operator control surface routes if available
try:
    from torq_console.mission_graph.control_api import router as control_surface_router
    CONTROL_SURFACE_AVAILABLE = True
except ImportError:
    CONTROL_SURFACE_AVAILABLE = False
    control_surface_router = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("TORQ.API.Server")


# Create Socket.IO server with ASGI support
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
)

# Create FastAPI application
app = FastAPI(
    title="TORQ Console API",
    description="FastAPI backend for TORQ Console with Marvin AI agents",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Include workspace routes if available
if WORKSPACE_AVAILABLE and workspace_router:
    app.include_router(workspace_router, prefix="/api")
    logger.info("Shared Cognitive Workspace routes included")

# Include agent workspace tools routes if available
if WORKSPACE_AVAILABLE and agent_tools_router:
    app.include_router(agent_tools_router, prefix="/api")
    logger.info("Agent Workspace Tools routes included")

# Include synthesis routes if available
if SYNTHESIS_AVAILABLE and synthesis_router:
    app.include_router(synthesis_router, prefix="/api")
    logger.info("Synthesis Engine routes included")

# Include evaluation routes if available
if EVALUATION_AVAILABLE and evaluation_router:
    app.include_router(evaluation_router, prefix="/api")
    logger.info("Evaluation Engine routes included")

# Include learning signal routes if available
if LEARNING_AVAILABLE and learning_router:
    app.include_router(learning_router, prefix="/api")
    logger.info("Learning Signal Engine routes included")

# Include adaptation proposal routes if available
if ADAPTATION_AVAILABLE and adaptation_router:
    app.include_router(adaptation_router, prefix="/api")
    logger.info("Adaptation Policy Engine routes included")

# Include behavior experiments routes if available
if EXPERIMENTS_AVAILABLE and experiments_router:
    app.include_router(experiments_router, prefix="/api")
    logger.info("Behavior Experiment & Versioning Layer routes included")

# Include adaptive telemetry routes if available
if ADAPTIVE_TELEMETRY_AVAILABLE and adaptive_telemetry_router:
    app.include_router(adaptive_telemetry_router, prefix="/api")
    logger.info("Adaptive System Telemetry routes included")

# Include strategic memory routes if available
if STRATEGIC_MEMORY_AVAILABLE and strategic_memory_router:
    app.include_router(strategic_memory_router, prefix="/api")
    logger.info("Strategic Memory routes included")

# Include mission graph routes if available
if MISSION_GRAPH_AVAILABLE and mission_graph_router:
    app.include_router(mission_graph_router, prefix="/api")
    logger.info("Mission Graph Planning routes included")

# Include operator control surface routes if available
if CONTROL_SURFACE_AVAILABLE and control_surface_router:
    app.include_router(control_surface_router, prefix="/api")
    logger.info("Operator Control Surface routes included")

# Initialize Socket.IO handler
socketio_handler = SocketIOHandler(sio)


# Health check endpoint
@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Health status dictionary.
    """
    return {"status": "healthy", "service": "torq-console-api"}


# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint with API information.

    Returns:
        API information dictionary.
    """
    return {
        "name": "TORQ Console API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "socket_io": "/socket.io",
    }


# Serve static files from frontend/dist if it exists
frontend_dist_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist_path.exists():
    logger.info(f"Serving static files from: {frontend_dist_path}")

    # Mount static assets
    app.mount(
        "/assets",
        StaticFiles(directory=frontend_dist_path / "assets"),
        name="assets",
    )

    # Serve index.html for all non-API routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        """
        Serve Single Page Application.

        Serves index.html for all routes not matching API or static assets,
        enabling client-side routing for the SPA.

        Args:
            full_path: Requested path.

        Returns:
            FileResponse with index.html or 404 error.
        """
        # Don't intercept API, Socket.IO, or asset routes
        if (
            full_path.startswith("api/")
            or full_path.startswith("socket.io/")
            or full_path.startswith("assets/")
        ):
            return JSONResponse(
                {"error": "Not found"},
                status_code=404,
            )

        index_path = frontend_dist_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)

        return JSONResponse(
            {"error": "Frontend not built"},
            status_code=404,
        )
else:
    logger.warning(
        f"Frontend dist directory not found at: {frontend_dist_path}. "
        "Static file serving disabled."
    )


# Startup event
@app.on_event("startup")
async def startup_event() -> None:
    """Initialize application on startup."""
    logger.info("Starting TORQ Console API server...")
    logger.info("Socket.IO enabled at /socket.io")
    logger.info("API documentation available at /api/docs")
    await socketio_handler.initialize()
    logger.info("Server startup complete")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on application shutdown."""
    logger.info("Shutting down TORQ Console API server...")
    await socketio_handler.cleanup()
    logger.info("Server shutdown complete")


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Any, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled errors.

    Args:
        request: The request that caused the error.
        exc: The exception that was raised.

    Returns:
        JSONResponse with error details.
    """
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"path": str(request.url)},
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "type": type(exc).__name__,
        },
    )


# Wrap FastAPI with Socket.IO
socket_app = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=app,
    socketio_path="/socket.io",
)


def run_server(
    host: str = "127.0.0.1",  # Default to localhost only for security
    port: int = 8899,
    reload: bool = False,
    log_level: str = "info",
    bind_all: bool = False,  # Explicit flag to bind to all interfaces
) -> None:
    """
    Run the FastAPI server with uvicorn.

    Args:
        host: Host address to bind to (default: 127.0.0.1 for localhost only).
        port: Port number to bind to.
        reload: Enable auto-reload for development.
        log_level: Logging level (debug, info, warning, error).
        bind_all: If True, bind to all interfaces (0.0.0.0) - use with caution.
        
    Security Note:
        By default, the server binds to 127.0.0.1 (localhost only) for security.
        To expose the server on all network interfaces, use bind_all=True.
        When binding to all interfaces, ensure your firewall is properly configured.

    Example:
        >>> run_server(host="localhost", port=8899, reload=True)
        >>> run_server(bind_all=True)  # Expose on all interfaces
    """
    import logging
    
    # If bind_all is True, override host to bind to all interfaces
    if bind_all:
        host = "0.0.0.0"
        logging.warning(
            "⚠️  Security Warning: Server binding to all interfaces (0.0.0.0). "
            "Ensure your firewall is configured and only trusted clients can access this server."
        )
    else:
        logging.info(f"🔒 Server binding to localhost only ({host}). Use bind_all=True to expose on all interfaces.")
    import uvicorn

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "torq_console.api.server:socket_app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True,
    )


if __name__ == "__main__":
    run_server(reload=True)
