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

        # === Dashboard Phase 1: Include REST API routes ===
        # Makes GET /api/agents, POST /api/agents/{id}/chat, GET /api/status,
        # GET/POST /api/sessions available on Vercel/Railway deployments
        try:
            from torq_console.api.routes import router as api_router
            app.include_router(api_router, prefix="/api")
            logger.info("REST API routes from torq_console.api.routes mounted at /api")
        except ImportError as e:
            logger.warning(f"Could not import API routes: {e}")
        except Exception as e:
            logger.warning(f"Could not mount API routes (may conflict with WebUI routes): {e}")

        # Add CORS for dashboard frontend
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add proxy secret middleware (protects chat/learning/telemetry endpoints)
        try:
            from torq_console.api.middleware import ProxySecretMiddleware, AdminTokenMiddleware
            app.add_middleware(ProxySecretMiddleware)
            app.add_middleware(AdminTokenMiddleware)
            logger.info("Security middleware installed: ProxySecretMiddleware + AdminTokenMiddleware")
        except ImportError as e:
            logger.warning(f"Could not import security middleware: {e}")

        # Add health check endpoint for Railway
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "torq-console-railway"}

        # Deployment fingerprint (never guess which code is serving)
        @app.get("/api/debug/deploy")
        async def deploy_fingerprint():
            import subprocess
            try:
                sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()[:8]
            except Exception:
                sha = os.environ.get("RAILWAY_GIT_COMMIT_SHA", "unknown")
            return {
                "service": "railway-agent",
                "version": "0.91.0",
                "git_sha": sha,
                "env": "production" if os.environ.get("RAILWAY_ENVIRONMENT") else "development",
                "railway_service": os.environ.get("RAILWAY_SERVICE_NAME", "unknown"),
                "learning_hook": "mandatory",
                "supabase_configured": bool(os.environ.get("SUPABASE_URL")),
            }

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
