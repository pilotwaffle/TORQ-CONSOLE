"""
Vercel serverless function entry point for TORQ Console.
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set production environment variables
os.environ.setdefault('TORQ_CONSOLE_PRODUCTION', 'true')
os.environ.setdefault('TORQ_DISABLE_LOCAL_LLM', 'true')
os.environ.setdefault('TORQ_DISABLE_GPU', 'true')

# Create the FastAPI app
from torq_console.ui.railway_app import app

# Vercel expects a handler function
def handler(request):
    """
    Vercel serverless handler.
    """
    from fastapi.responses import JSONResponse
    from fastapi import Request

    # Convert Vercel request to ASGI scope
    scope = {
        'type': 'http',
        'asgi': {'version': '3.0'},
        'http_version': '1.1',
        'method': request.method,
        'scheme': 'https',
        'path': request.path,
        'query_string': request.query_string.decode(),
        'headers': dict(request.headers),
        'server': ('vercel', 443),
    }

    # Use the ASGI app
    async def asgi_handler(receive, send):
        await app(scope, receive, send)

    # Simple response for now
    return JSONResponse({
        "status": "ok",
        "service": "torq-console",
        "message": "TORQ Console is running on Vercel"
    })

# For direct ASGI use (preferred)
asgi_app = app
