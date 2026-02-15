"""
Railway-optimized FastAPI app entry point.

This module provides a module-level 'app' variable that Railway can use directly.
"""

from torq_console.ui.railway_main import create_minimal_app

# Create app at module level for Railway uvicorn startup
app = create_minimal_app()

__all__ = ["app"]
