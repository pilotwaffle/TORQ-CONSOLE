"""
Middleware for TORQ Console API authentication.

Provides:
- ProxySecretMiddleware: Validates requests from Vercel proxy
- AdminTokenMiddleware: Validates admin tokens for sensitive operations
"""

import os
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class ProxySecretMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates the X-TORQ-PROXY-SECRET header.

    This ensures that sensitive endpoints (chat, learning, telemetry) can only
    be called from authorized proxies (Vercel) or clients with the shared secret.
    """

    # Paths that require proxy secret authentication
    PROTECTED_PATHS = {
        "/api/chat",
        "/api/learning",
        "/api/telemetry",
    }

    async def dispatch(self, request: Request, call_next):
        # Check if path requires authentication
        path = request.url.path

        # Check if any protected path is a prefix of current path
        requires_auth = any(
            path.startswith(protected_path)
            for protected_path in self.PROTECTED_PATHS
        )

        if requires_auth:
            # Get expected secret from environment
            expected_secret = os.environ.get("TORQ_PROXY_SHARED_SECRET")

            # If no secret configured, allow all (for development)
            if not expected_secret:
                return await call_next(request)

            # Validate proxy secret header
            provided_secret = request.headers.get("x-torq-proxy-secret")

            if not provided_secret:
                raise HTTPException(
                    status_code=401,
                    detail="Missing proxy secret header",
                )

            if provided_secret != expected_secret:
                raise HTTPException(
                    status_code=403,
                    detail="Forbidden: Invalid proxy secret",
                )

        response = await call_next(request)
        return response


class AdminTokenMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates admin tokens for sensitive operations.

    Used for:
    - /api/learning/policy/approve
    - /api/learning/policy/rollback
    - Admin-only operations
    """

    # Paths that require admin token
    ADMIN_PATHS = {
        "/api/learning/policy/approve",
        "/api/learning/policy/rollback",
    }

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Check if path requires admin authentication
        requires_admin = any(
            path.startswith(admin_path)
            for admin_path in self.ADMIN_PATHS
        )

        if requires_admin:
            # Get expected token from environment
            expected_token = os.environ.get("TORQ_ADMIN_TOKEN")

            if not expected_token:
                raise HTTPException(
                    status_code=500,
                    detail="Admin token not configured",
                )

            # Check Authorization header or query param
            auth_header = request.headers.get("authorization", "")

            # Support both "Bearer token" and plain token
            provided_token = None
            if auth_header.startswith("Bearer "):
                provided_token = auth_header[7:]
            else:
                provided_token = auth_header

            # Also check query parameter
            if not provided_token:
                provided_token = request.query_params.get("token")

            if not provided_token or provided_token != expected_token:
                raise HTTPException(
                    status_code=403,
                    detail="Forbidden: Invalid admin token",
                )

        response = await call_next(request)
        return response
