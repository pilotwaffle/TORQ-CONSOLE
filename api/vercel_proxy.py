"""
TORQ Console - Vercel Serverless Proxy to Railway

This module proxies chat requests from Vercel to Railway,
where the full agent runtime + learning hook executes.

Environment Variables (set in Vercel Dashboard):
- TORQ_BACKEND_URL: Railway service URL (e.g., https://torq-console.up.railway.app)
- TORQ_PROXY_SHARED_SECRET: Shared secret for authenticating proxy requests
- TORQ_PROXY_TIMEOUT_MS: Optional timeout in milliseconds (default: 30000)
"""

import os
import json
import logging
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger("torq-vercel-proxy")

# Environment configuration
BACKEND_URL = os.environ.get("TORQ_BACKEND_URL", "").rstrip("/")
PROXY_SECRET = os.environ.get("TORQ_PROXY_SHARED_SECRET", "")
TIMEOUT_MS = int(os.environ.get("TORQ_PROXY_TIMEOUT_MS", "30000"))


def proxy_request_to_railway(
    method: str,
    path: str,
    payload: dict | None = None,
    headers: dict | None = None,
) -> dict:
    """
    Proxy a request to Railway backend.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: API path (e.g., "/api/chat")
        payload: Request body as dict
        headers: Additional headers to forward

    Returns:
        Response dict parsed from JSON
    """
    if not BACKEND_URL:
        raise RuntimeError("TORQ_BACKEND_URL not configured")

    url = f"{BACKEND_URL}{path}"

    # Prepare request body
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    # Prepare headers
    req_headers = {
        "Content-Type": "application/json",
        "User-Agent": "TORQ-Vercel-Proxy/1.0",
    }

    # Add proxy authentication header
    if PROXY_SECRET:
        req_headers["X-TORQ-PROXY-SECRET"] = PROXY_SECRET

    # Forward trace ID if present
    if headers and "x-trace-id" in headers:
        req_headers["X-TRACE-ID"] = headers["x-trace-id"]

    # Create request
    req = Request(
        url,
        data=data,
        method=method,
        headers=req_headers,
    )

    # Set timeout
    timeout = TIMEOUT_MS / 1000.0

    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            if body:
                return json.loads(body)
            return {}
    except HTTPError as e:
        logger.error(f"Railway HTTP error: {e.code} - {e.reason}")
        raise
    except URLError as e:
        logger.error(f"Railway connection error: {e.reason}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected proxy error: {e}")
        raise


# ============================================================================
# FastAPI Integration (for api/index.py)
# ============================================================================

def create_proxy_chat_endpoint():
    """
    Returns a FastAPI route handler that proxies /api/chat to Railway.

    Add to api/index.py like:

    from torq_console.vercel_proxy import create_proxy_chat_endpoint
    app.post("/api/chat")(create_proxy_chat_endpoint())
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse, StreamingResponse

    async def proxy_chat(request: Request):
        """Proxy chat request to Railway backend."""
        try:
            # Parse incoming request
            payload = await request.json()

            # Extract trace metadata for telemetry
            trace_id = payload.get("trace_id") or payload.get("session_id")
            proxy_headers = {}
            if trace_id:
                proxy_headers["x-trace-id"] = trace_id

            # Forward to Railway
            response = proxy_request_to_railway(
                method="POST",
                path="/api/chat",
                payload=payload,
                headers=proxy_headers,
            )

            # Check if response is streaming
            # (For now, return as JSON - add streaming support later)
            return JSONResponse(
                content=response,
                status_code=200,
                headers={
                    "X-TORQ-PROXIED": "true",
                    "X-BACKEND": BACKEND_URL or "unknown",
                },
            )

        except Exception as e:
            logger.exception("Chat proxy error")
            return JSONResponse(
                content={
                    "error": "proxy_error",
                    "message": str(e),
                    "backend_available": bool(BACKEND_URL),
                },
                status_code=500,
            )

    return proxy_chat


# ============================================================================
# Standalone test (run locally to verify Railway connectivity)
# ============================================================================

if __name__ == "__main__":
    import sys

    print("TORQ Console - Vercel Proxy Test")
    print("=" * 60)

    print(f"BACKEND_URL: {BACKEND_URL or 'NOT SET'}")
    print(f"PROXY_SECRET: {'SET' if PROXY_SECRET else 'NOT SET'}")
    print(f"TIMEOUT_MS: {TIMEOUT_MS}")

    if not BACKEND_URL:
        print("\nERROR: TORQ_BACKEND_URL environment variable not set")
        sys.exit(1)

    # Test connectivity
    print("\nTesting Railway connectivity...")

    try:
        # Test health endpoint
        response = proxy_request_to_railway("GET", "/health")
        print(f"Health check: {response}")
    except Exception as e:
        print(f"Health check FAILED: {e}")
        sys.exit(1)

    # Test chat endpoint (if message provided)
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        print(f"\nTesting chat with message: '{message}'")

        try:
            response = proxy_request_to_railway(
                "POST",
                "/api/chat",
                {"message": message, "session_id": "proxy-test"},
            )
            print(f"Response: {json.dumps(response, indent=2)}")
        except Exception as e:
            print(f"Chat test FAILED: {e}")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("All tests passed!")
