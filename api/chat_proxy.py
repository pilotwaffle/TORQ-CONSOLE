"""
Vercel Serverless Function: API Proxy to Railway

This function handles all /api/chat/* requests and forwards them to Railway
with the TORQ_PROXY_SHARED_SECRET header injected server-side.

Vercel Python Function documentation:
https://vercel.com/docs/functions/runtimes/python
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


def handler(event, context):
    """
    Vercel Python serverless function handler.

    Args:
        event: Dict with request data including method, body, headers, path
        context: Runtime context (not used but required)

    Returns:
        Dict with statusCode, headers, and body
    """
    # Get request details
    method = event.get("method", "GET")
    path = event.get("path", "")

    # Build full URL to Railway
    url = f"{BACKEND_URL}{path}"

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "TORQ-Vercel-Proxy/1.0",
    }

    # Forward headers from request
    request_headers = event.get("headers", {})
    if isinstance(request_headers, dict):
        for key, value in request_headers.items():
            if key.lower() not in ["host", "content-length"]:
                headers[key] = value

    # Add proxy authentication
    if PROXY_SECRET:
        headers["X-TORQ-PROXY-SECRET"] = PROXY_SECRET

    # Prepare body
    body_data = None
    body = event.get("body")
    if body:
        if isinstance(body, str):
            body_data = body.encode("utf-8")
        elif isinstance(body, dict):
            body_data = json.dumps(body).encode("utf-8")
        else:
            body_data = body

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
                "statusCode": resp.status,
                "headers": response_headers,
                "body": response_body,
            }

    except HTTPError as e:
        logger.error(f"Railway HTTP error: {e.code} - {e.reason}")
        return {
            "statusCode": e.code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "proxy_error",
                "message": f"Railway returned {e.code}: {e.reason}",
            }),
        }

    except URLError as e:
        logger.error(f"Railway connection error: {e.reason}")
        return {
            "statusCode": 502,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "proxy_error",
                "message": f"Cannot reach Railway: {e.reason}",
            }),
        }

    except Exception as e:
        logger.exception(f"Unexpected proxy error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "proxy_error",
                "message": str(e),
            }),
        }
