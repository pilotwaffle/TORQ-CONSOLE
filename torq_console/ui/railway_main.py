#!/usr/bin/env python3
"""
Railway-optimized entry point for TORQ Console Web UI.

This module provides a production-ready startup that handles missing
local resources gracefully (no GPU, no local LLM models, etc.)
"""

import sys
import os
import asyncio
import argparse
import logging
from pathlib import Path

# Set environment variables for Railway/production before imports
os.environ.setdefault('TORQ_CONSOLE_PRODUCTION', 'true')
os.environ.setdefault('TORQ_DISABLE_LOCAL_LLM', 'true')
os.environ.setdefault('TORQ_DISABLE_GPU', 'true')

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_minimal_app():
    """Create a minimal FastAPI app that always works."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates

    app = FastAPI(
        title="TORQ CONSOLE",
        description="AI-powered development console",
        version="0.80.0"
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Health check endpoint (CRITICAL for Railway)
    @app.get("/health")
    async def health():
        return {"status": "healthy", "version": "0.80.0"}

    @app.get("/api/health")
    async def api_health():
        return {"status": "healthy", "version": "0.80.0", "providers": []}

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": "TORQ CONSOLE",
            "version": "0.80.0",
            "status": "running",
            "docs": "/docs"
        }

    return app


async def main():
    """Main entry point optimized for Railway deployment."""
    import uvicorn

    parser = argparse.ArgumentParser(description='TORQ Console Web Interface (Railway)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    port = int(os.environ.get('PORT', args.port))

    logger.info(f"Starting TORQ Console on {args.host}:{port}")

    try:
        # Try full initialization first
        try:
            from torq_console.ui.web import WebUI
            from torq_console.core.console import TorqConsole
            from torq_console.core.config import TorqConfig

            logger.info("Attempting full TORQ Console initialization...")
            config = TorqConfig()
            console = TorqConsole(config=config)
            web_ui = WebUI(console)

            logger.info(f"Full initialization successful. Starting server on port {port}")
            await web_ui.start_server(host=args.host, port=port)

        except Exception as init_error:
            logger.warning(f"Full initialization failed: {init_error}")
            logger.info("Falling back to minimal app...")

            # Fallback to minimal app
            app = create_minimal_app()
            logger.info(f"Minimal app created. Starting server on port {port}")
            config = uvicorn.Config(
                app,
                host=args.host,
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()

    except KeyboardInterrupt:
        logger.info("TORQ Console shutting down...")
    except Exception as e:
        logger.error(f"Error starting TORQ Console: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
