"""
TORQ Console API Module

FastAPI backend with Socket.IO integration for Cursor 2.0 UI.
"""

from .server import app, sio
from .routes import router
from .socketio_handler import SocketIOHandler

__all__ = ["app", "sio", "router", "SocketIOHandler"]
