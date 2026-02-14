#!/usr/bin/env python3
"""
Simple web server for TORQ Console - minimal initialization
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Create simple FastAPI app
app = FastAPI(
    title="TORQ Console Web UI",
    description="TORQ Console Web Interface",
    version="0.80.0"
)

# Add CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path("torq_console/ui/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Homepage with simple HTML"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TORQ Console</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <div class="container">
        <h1>TORQ Console Web UI</h1>
        <p>Welcome to TORQ Console! The web server is running.</p>
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/api/health">API Health</a></li>
        </ul>
    </div>
</body>
</html>
    """)

@app.get("/dashboard")
async def dashboard():
    """Simple dashboard"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>TORQ Console Dashboard</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <h1>TORQ Console Dashboard</h1>
    <div id="metrics">
        <h2>System Metrics</h2>
        <p>Status: Running</p>
        <p>Uptime: Active</p>
    </div>
</body>
</html>
    """)

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "0.80.0",
        "service": "TORQ Console Web UI"
    }

@app.get("/offline")
async def offline():
    """PWA offline page"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Offline - TORQ Console</title>
</head>
<body>
    <h1>You're Offline</h1>
    <p>TORQ Console requires an internet connection for full functionality.</p>
</body>
</html>
    """)

if __name__ == "__main__":
    print("=" * 60)
    print("  TORQ Console Web Server")
    print("=" * 60)
    print()
    print("Starting server on http://127.0.0.1:8081")
    print("Press Ctrl+C to stop")
    print()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8081,
        log_level="info"
    )
