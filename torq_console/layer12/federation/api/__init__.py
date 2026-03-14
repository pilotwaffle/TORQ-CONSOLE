"""
Federation API Module

Phase 1B - FastAPI endpoints for federation layer.
"""

from torq_console.layer12.federation.api.routes import router, get_router

__all__ = ["router", "get_router"]
