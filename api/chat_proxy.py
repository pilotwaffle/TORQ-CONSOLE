"""
Vercel Serverless Function: API Proxy to Railway

This function handles all /api/chat/* requests and forwards them to Railway
with the TORQ_PROXY_SHARED_SECRET header injected server-side.
"""

import os
import json
import logging
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger("torq-vercel-proxy")

# Environment configuration
BACKEND_URL = os.environ.get("TORQ_BACKEND_URL", "https://web-production-74ed0.up.railway.app").rstrip("/")
PROXY_SECRET = os.environ.get("TORQ_PROXY_SHARED_SECRET", "")
TIMEOUT_MS = int(os.environ.get("TORQ_PROXY_TIMEOUT_MS", "30000"))


def handler(request):
    """
    Vercel serverless function handler.

    Args:
        request: Vercel request object with method, body, headers, path properties

    Returns:
        Response dict with status, headers, and body
    """
    # Get request details
    method = request.method or "GET"
    path = request.path or ""

    # Build full URL to Railway
    url = f"{BACKEND_URL}{path}"

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "TORQ-Vercel-Proxy/1.0",
    }

    # Forward headers from request (excluding host)
    if hasattr(request, "headers") and request.headers:
        for key, value in request.headers.items():
            if key.lower() not in ["host", "content-length"]:
                headers[key] = value

    # Add proxy authentication
    if PROXY_SECRET:
        headers["X-TORQ-PROXY-SECRET"] = PROXY_SECRET

    # Prepare body
    body_data = None
    if hasattr(request, "body") and request.body:
        if isinstance(request.body, str):
            body_data = request.body.encode("utf-8")
        elif isinstance(request.body, dict):
            body_data = json.dumps(request.body).encode("utf-8")
        else:
            body_data = request.body

    # Create HTTP request
    req = Request(url, data=body_data, method=method, headers=headers)

    # Set timeout
    timeout = TIMEOUT_MS / 1000.0

    try:
        with urlopen(req, timeout=timeout) as resp:
            response_body = resp.read().decode("utf-8")

            # Build response headers
            response_headers = {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            }

            # Copy headers from Railway response
            for key, value in resp.headers.items():
                if key.lower() not in ["content-length", "transfer-encoding"]:
                    response_headers[key] = value

            return {
                "status": resp.status,
                "headers": response_headers,
                "body": response_body,
            }

    except HTTPError as e:
        logger.error(f"Railway HTTP error: {e.code} - {e.reason}")
        return {
            "status": e.code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "proxy_error",
                "message": f"Railway returned {e.code}: {e.reason}",
            }),
        }

    except URLError as e:
        logger.error(f"Railway connection error: {e.reason}")
        return {
            "status": 502,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "proxy_error",
                "message": f"Cannot reach Railway: {e.reason}",
            }),
        }

    except Exception as e:
        logger.exception(f"Unexpected proxy error: {e}")
        return {
            "status": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "proxy_error",
                "message": str(e),
            }),
        }
