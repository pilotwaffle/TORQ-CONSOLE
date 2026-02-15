"""
Railway-optimized FastAPI app entry point with FULL WebUI.

This module provides the complete TORQ Console WebUI with:
- Static file serving (CSS, JS, images)
- Chat endpoints (/api/chat)
- Template rendering
- All web features working identically to local

CRITICAL FIX: Export app as FastAPI instance, NOT as package name.
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

    CRITICAL: Must return web_ui.app (FastAPI instance), NOT a package name.
    Railway runs: uvicorn torq_console.ui.railway_app:app
    Python imports: from torq_console.ui.railway_app import app
    """
    try:
        # Import full WebUI - NOT minimal app
        from torq_console.ui.web import WebUI
        from torq_console.core.console import TorqConsole
        from torq_console.core.config import TorqConfig

        logger.info("Importing full TORQ Console WebUI for Railway...")
        logger.info("This creates complete WebUI with all routes and features")

        # Initialize console and web UI
        config = TorqConfig()
        console = TorqConsole(config=config)
        web_ui = WebUI(console=console)

        logger.info("WebUI instance created")
        logger.info(f"App type: {type(web_ui).__name__}")
        logger.info(f"Routes: {len(web_ui.app.routes)}")

        # CRITICAL: Return the FastAPI app instance directly
        # Railway will run: uvicorn torq_console.ui.railway_app:app --host ...
        # It needs to import app, so return web_ui.app
        app = web_ui.app
        
        logger.info("Exporting FastAPI app instance (not package name)")
        logger.info(f"Static files: /static")
        logger.info(f"Chat endpoint: /api/chat")
        logger.info(f"Health check: /health")
        
        return app

    except Exception as e:
        logger.error(f"Failed to create Railway app: {e}")
        logger.info("Falling back to minimal app...")
        
        # Fallback to minimal app (original behavior)
        from torq_console.ui.railway_main import create_minimal_app
        return create_minimal_app()


# Create app at module level for Railway uvicorn startup
# This is the PRIMARY entry point - use full WebUI
app = create_railway_app()

# Export for Railway - must be app instance, not package name
__all__ = ["app"]
