"""
Railway entry point for TORQ Console Web UI.
Creates a standalone FastAPI app instance for uvicorn without full TorqConsole.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Create a standalone FastAPI app for Railway
app = FastAPI(
    title="TORQ CONSOLE Web UI - Railway",
    description="Enhanced AI pair programming interface (standalone mode)",
    version="0.80.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "TORQ CONSOLE Web UI",
        "version": "0.80.0",
        "status": "running",
        "mode": "standalone",
        "message": "TORQ Console Web UI is running on Railway!"
    }

@app.get("/api/health")
async def health():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "service": "torq-console-web-ui"}

@app.get("/api/console/info")
async def console_info():
    """Console information endpoint"""
    return {
        "title": "TORQ CONSOLE",
        "version": "0.80.0",
        "mode": "standalone",
        "features": [
            "FastAPI Web Server",
            "REST API",
            "Railway Deployment"
        ]
    }
