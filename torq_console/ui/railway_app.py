"""
Railway-optimized FastAPI app entry point with FULL WebUI.

This module provides the complete TORQ Console WebUI with:
- Static file serving (CSS, JS, images)
- Chat endpoints (/api/chat)
- Template rendering
- All web features working identically to local

CRITICAL FIX: Use full WebUI instead of minimal app for Railway deployment.
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
    Create the full TORQ Console WebUI app for Railway deployment.

    This ensures static files, chat endpoints, and all web features
    work identically to local development.
    """
    try:
        # Import full WebUI - NOT minimal app
        from torq_console.ui.web import WebUI
        from torq_console.core.console import TorqConsole
        from torq_console.core.config import TorqConfig

        logger.info("Creating full TORQ Console WebUI for Railway...")

        # Initialize console and web UI
        config = TorqConfig()
        console = TorqConsole(config=config)
        web_ui = WebUI(console=console)

        logger.info("✅ Full WebUI created successfully")
        logger.info(f"Static files mounted at: /static")
        logger.info(f"Chat endpoint available: /api/chat")
        logger.info(f"Health check: /health")

        # Return the full FastAPI app with all routes
        return web_ui.app

    except Exception as e:
        logger.error(f"Failed to create full WebUI: {e}")
        logger.info("Falling back to minimal app...")

        # Fallback to minimal app (original behavior)
        from torq_console.ui.railway_main import create_minimal_app
        return create_minimal_app()


# Create app at module level for Railway uvicorn startup
# This is the PRIMARY entry point - use full WebUI
app = create_railway_app()

# Export for Railway
__all__ = ["app"]
