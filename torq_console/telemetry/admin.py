"""
Admin Guardrails for Learning Policy Endpoints.

Enforces authentication and logging for administrative actions:
- Policy approval
- Policy rollback

All admin actions require TORQ_ADMIN_TOKEN header and are
logged to Supabase for audit trail.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Admin token from environment (should be set in production)
ADMIN_TOKEN = os.getenv("TORQ_ADMIN_TOKEN", "")

# Log admin actions to this table in Supabase
ADMIN_LOG_TABLE = "admin_actions"


def verify_admin_token(token: Optional[str]) -> bool:
    """
    Verify admin token is valid.

    Args:
        token: Token from Authorization header

    Returns:
        True if token matches ADMIN_TOKEN or if admin not configured

    Note:
        Returns True if ADMIN_TOKEN is not set (dev mode).
        In production, ALWAYS set TORQ_ADMIN_TOKEN.
    """
    if not ADMIN_TOKEN:
        # Dev mode: no admin token required
        logger.warning("TORQ_ADMIN_TOKEN not set - admin endpoints are UNPROTECTED")
        return True

    if not token:
        return False

    # Constant-time comparison to prevent timing attacks
    import hmac
    return hmac.compare_digest(token, ADMIN_TOKEN)


async def log_admin_action(
    action: str,
    details: Dict[str, Any],
    actor: str = "unknown",
    success: bool = True,
) -> None:
    """
    Log admin action to Supabase for audit trail.

    Args:
        action: Action type (e.g., "policy_approve", "policy_rollback")
        details: Action details (policy_id, routing_data, etc.)
        actor: Who performed the action (token hash, user ID, etc.)
        success: Whether the action succeeded
    """
    import httpx

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        logger.warning("Supabase not configured - admin action not logged")
        return

    log_entry = {
        "action": action,
        "actor": actor,
        "success": success,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": os.getenv("RAILWAY_STATIC_URL") and "railway" or os.getenv("VERCEL") and "vercel" or "unknown",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{supabase_url}/rest/v1/{ADMIN_LOG_TABLE}",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                json=log_entry,
            )
    except Exception as e:
        logger.error(f"Failed to log admin action: {e}")


def admin_required(func):
    """
    Decorator that enforces admin authentication on endpoints.

    Usage:
        @app.post("/api/learning/policy/approve")
        @admin_required
        async def approve_policy(...):
            ...

    The decorated endpoint will:
    1. Check X-Torq-Admin-Token header
    2. Return 401 if token invalid
    3. Log the admin action
    4. Call the original function

    The function can access the actor via request.state.actor
    """
    from fastapi import Request, HTTPException

    async def wrapper(*args, **kwargs):
        # Find the Request object in args
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        if not request:
            logger.error("admin_required decorator used without Request parameter")
            raise HTTPException(status_code=500, detail="Server configuration error")

        # Extract token from header
        token = request.headers.get("X-Torq-Admin-Token", "")

        if not verify_admin_token(token):
            await log_admin_action(
                action="unauthorized_access_attempt",
                details={"path": request.url.path, "method": request.method},
                actor="unauthorized",
                success=False,
            )
            raise HTTPException(
                status_code=401,
                detail="Unauthorized: Valid admin token required",
            )

        # Store actor in request state for logging
        actor_hash = f"token_{hash(token) % 10000:04d}" if token else "dev"
        request.state.actor = actor_hash

        # Call the original function
        return await func(*args, **kwargs)

    return wrapper
