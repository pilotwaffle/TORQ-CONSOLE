"""
Railway entry point for TORQ Console Web UI.
Creates a module-level FastAPI app instance for uvicorn.
"""

from .web import WebUI

# Create WebUI instance
web_ui = WebUI(console=None)

# Export the FastAPI app for uvicorn
app = web_ui.app
