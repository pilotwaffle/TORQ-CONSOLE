"""
Railway-optimized FastAPI app entry point with FULL WebUI.

This module provides the complete TORQ Console WebUI with:
- Static file serving (CSS, JS, images)
- Chat endpoints (/api/chat)
- Template rendering
- All web features working identically to local

Railway startup command: uvicorn torq_console.ui.railway_app:app --host 0.0.0.0 --port $PORT
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set production environment variables
os.environ.setdefault('TORQ_CONSOLE_PRODUCTION', 'true')
os.environ.setdefault('TORQ_DISABLE_LOCAL_LLM', 'true')
os.environ.setdefault('TORQ_DISABLE_GPU', 'true')


def create_railway_app():
    """
    Create FastAPI app for Railway deployment.

    Returns a FastAPI app instance that Railway can run with:
    uvicorn torq_console.ui.railway_app:app --host 0.0.0.0 --port $PORT
    """
    try:
        # Import full WebUI - NOT minimal app
        from torq_console.ui.web import WebUI
        from torq_console.core.console import TorqConsole
        from torq_console.core.config import TorqConfig

        logger.info("=" * 60)
        logger.info("TORQ Console - Railway Deployment")
        logger.info("=" * 60)
        logger.info("Initializing full WebUI with all routes...")

        # Initialize console and web UI
        config = TorqConfig()
        console = TorqConsole(config=config)
        web_ui = WebUI(console=console)

        logger.info(f"WebUI instance created: {type(web_ui).__name__}")
        logger.info(f"Total routes: {len(web_ui.app.routes)}")
        logger.info(f"FastAPI app: {type(web_ui.app).__name__}")

        # Get the FastAPI app instance
        app = web_ui.app

        # Add health check endpoint for Railway
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "torq-console"}

        logger.info("=" * 60)
        logger.info("Ready for Railway deployment")
        logger.info(f"Static files: /static")
        logger.info(f"Chat endpoint: /api/chat")
        logger.info(f"Health check: /health")
        logger.info("=" * 60)

        return app

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Failed to create Railway app: {e}")
        logger.error("Creating fallback minimal app...")
        logger.error("=" * 60)

        # Fallback to minimal app
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse

        app = FastAPI(title="TORQ Console")

        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "torq-console-minimal"}

        @app.get("/")
        async def root():
            return JSONResponse({
                "message": "TORQ Console - Minimal deployment",
                "full_webui_unavailable": str(e)
            })

        return app


# Create app at module level for Railway uvicorn startup
# Railway runs: uvicorn torq_console.ui.railway_app:app
app = create_railway_app()

# Export for Railway
__all__ = ["app"]
