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
    host: str = "0.0.0.0",
    port: int = 8899,
    reload: bool = False,
    log_level: str = "info",
) -> None:
    """
    Run the FastAPI server with uvicorn.

    Args:
        host: Host address to bind to.
        port: Port number to bind to.
        reload: Enable auto-reload for development.
        log_level: Logging level (debug, info, warning, error).

    Example:
        >>> run_server(host="localhost", port=8899, reload=True)
    """
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
