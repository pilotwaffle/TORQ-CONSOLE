"""
Versioned API Response Contracts

Defines stable response schemas for HTTP endpoints.
This enables frontend/backend independent evolution.

Schema versions:
- torq-chat-response-v1: Single envelope for /api/chat (success + error)
- torq-error-v1: Nested error detail schema

FROZEN CONTRACT - Do not modify without incrementing schema version.
"""

from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Stable Error Categories (DO NOT CHANGE - these are public API)
# ============================================================================
# Use these stable types instead of raw exception class names.
# Raw exception goes in debug_type only when TORQ_DEBUG=true.
ErrorCategory = Literal[
    "invalid_request",   # 400: Bad request, validation failed
    "unauthorized",      # 401: Missing or invalid credentials
    "forbidden",         # 403: Valid credentials but insufficient permissions
    "not_found",         # 404: Resource not found
    "rate_limited",      # 429: Too many requests
    "provider_error",    # 502: External provider (API, LLM) failed
    "internal_error",    # 500: Unexpected server error
]


# ============================================================================
# Deploy Identity (always present)
# ============================================================================
class DeployInfo(BaseModel):
    """Deploy identity information for trace correlation.

    All fields are REQUIRED - always present in responses.
    """
    platform: str = Field(..., description="Deployment platform: railway, vercel, local")
    git_sha: str = Field(..., description="Git commit SHA (abbreviated, 8 chars)")
    app_version: str = Field(..., description="App version string (e.g., '1.0.10')")
    environment: str = Field(..., description="Environment: production, staging, development")


# ============================================================================
# Error Detail (nested inside error response)
# ============================================================================
class ErrorDetail(BaseModel):
    """
    Structured error information.

    Nested inside the error envelope when ok=False.
    Schema: torq-error-v1
    """
    # Schema version for this nested object (using alias for JSON serialization)
    schema_version: str = Field("torq-error-v1", description="Error detail schema version", alias="_schema")

    # Stable error category (required, stable across implementations)
    type: ErrorCategory = Field(
        ...,
        description="Stable error category for client handling"
    )

    # User-safe message (required)
    message: str = Field(
        ...,
        description="Error message (user-safe, sanitized)"
    )

    # HTTP status code (required, numeric)
    code: int = Field(
        ...,
        description="HTTP status code (numeric, e.g., 400, 401, 500)"
    )

    # Raw exception type (optional, debug only)
    debug_type: Optional[str] = Field(
        None,
        description="Raw exception class name (only when TORQ_DEBUG=true)"
    )

    class Config:
        populate_by_name = True  # Allow using schema_version in code, _schema in JSON


# ============================================================================
# Success Payload (nested inside data when ok=true)
# ============================================================================
class ChatData(BaseModel):
    """
    Successful chat response payload.

    Nested inside the 'data' field when ok=True.
    All fields are REQUIRED when present (data itself is optional).
    """
    response: str = Field(..., description="Agent's text response")
    agent: str = Field(..., description="Agent name that handled request")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent metadata (evidence_level, tools_used, etc.)"
    )


# ============================================================================
# Main Response Envelope (single schema for all /api/chat responses)
# ============================================================================
class ChatResponseV1(BaseModel):
    """
    Versioned chat API response envelope.

    Schema: torq-chat-response-v1

    This is the FROZEN contract for /api/chat responses.
    Both success and error responses use this same envelope.

    ALWAYS PRESENT fields (required):
    - _schema, request_id, trace_id, ok, deploy, duration_ms

    CONDITIONALLY PRESENT fields (nullable):
    - session_id (string | null)
    - learning_recorded (boolean | null)

    WHEN ok=true:
    - data (ChatData) is REQUIRED

    WHEN ok=false:
    - error (ErrorDetail) is REQUIRED

    === DO NOT MODIFY THIS STRUCTURE WITHOUT CREATING v2 ===
    """

    # ========================================================================
    # Always Present (required fields)
    # ========================================================================

    # Schema version for forward compatibility (using alias for JSON)
    schema_version: str = Field(
        "torq-chat-response-v1",
        description="Response envelope schema version (always torq-chat-response-v1)",
        alias="_schema"
    )

    # Request correlation
    request_id: str = Field(..., description="Unique request identifier for trace correlation")
    trace_id: str = Field(..., description="Telemetry trace ID")

    # Response status
    ok: bool = Field(..., description="True if request succeeded, False if error")

    # Deploy info for trace correlation
    deploy: DeployInfo = Field(..., description="Deployment identity for logs correlation")

    # Timing (always present)
    duration_ms: int = Field(..., description="Request processing time in milliseconds")

    # ========================================================================
    # Conditionally Present (nullable - always in response, may be null)
    # ========================================================================

    # Session ID (nullable - always present, null if no session)
    session_id: Optional[str] = Field(
        None,
        description="Session identifier (null if not applicable)"
    )

    # Learning status (nullable - always present, null if unknown)
    learning_recorded: Optional[bool] = Field(
        None,
        description="Whether learning event was recorded (null if unknown)"
    )

    # ========================================================================
    # Mutually Exclusive: one of these is present based on 'ok'
    # ========================================================================

    # Success payload (required when ok=true, null when ok=false)
    data: Optional[ChatData] = Field(
        None,
        description="Success payload (present when ok=true)"
    )

    # Error detail (required when ok=false, null when ok=true)
    error: Optional[ErrorDetail] = Field(
        None,
        description="Error detail (present when ok=false)"
    )

    class Config:
        populate_by_name = True  # Allow using schema_version in code, _schema in JSON
        json_schema_extra = {
            "example": {
                "_schema": "torq-chat-response-v1",
                "request_id": "req_123456",
                "trace_id": "trace_789",
                "ok": True,
                "deploy": {
                    "platform": "railway",
                    "git_sha": "abc1234",
                    "app_version": "1.0.10",
                    "environment": "production"
                },
                "duration_ms": 1500,
                "session_id": "sess_456",
                "learning_recorded": True,
                "data": {
                    "response": "Hello! How can I help you today?",
                    "agent": "prince_flowers",
                    "metadata": {
                        "evidence_level": "high",
                        "routing_success": True,
                        "tools_used": ["web_search"]
                    }
                },
                "error": None
            },
            "error_example": {
                "_schema": "torq-chat-response-v1",
                "request_id": "req_123456",
                "trace_id": "trace_789",
                "ok": False,
                "deploy": {
                    "platform": "railway",
                    "git_sha": "abc1234",
                    "app_version": "1.0.10",
                    "environment": "production"
                },
                "duration_ms": 12,
                "session_id": "sess_456",
                "learning_recorded": False,
                "data": None,
                "error": {
                    "_schema": "torq-error-v1",
                    "type": "invalid_request",
                    "message": "Invalid parameter",
                    "code": 400,
                    "debug_type": None
                }
            }
        }


# ============================================================================
# Response Factory Helpers (for constructing responses)
# ============================================================================
def get_deploy_info() -> DeployInfo:
    """
    Get current deploy identity from environment.

    This should be used in all API responses for trace correlation.
    """
    import os
    from torq_console.build_info import (
        get_git_sha,
        get_app_version_with_source,
        get_platform,
    )

    return DeployInfo(
        platform=get_platform(),
        git_sha=get_git_sha()[:8],
        app_version=get_app_version_with_source()[0],  # Returns tuple (version, source)
        environment=os.environ.get("RAILWAY_ENVIRONMENT", "development"),
    )


def success_response(
    request_id: str,
    trace_id: str,
    response: str,
    agent: str,
    duration_ms: int,
    metadata: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    learning_recorded: Optional[bool] = None,
) -> ChatResponseV1:
    """
    Construct a successful /api/chat response.

    Returns a frozen ChatResponseV1 with ok=True.
    """
    return ChatResponseV1(
        request_id=request_id,
        trace_id=trace_id,
        ok=True,
        deploy=get_deploy_info(),
        duration_ms=duration_ms,
        session_id=session_id,
        learning_recorded=learning_recorded,
        data=ChatData(
            response=response,
            agent=agent,
            metadata=metadata or {},
        ),
        error=None,
    )


def error_response(
    request_id: str,
    trace_id: str,
    error_type: ErrorCategory,
    message: str,
    code: int,
    duration_ms: int,
    debug_type: Optional[str] = None,
    session_id: Optional[str] = None,
) -> ChatResponseV1:
    """
    Construct an error /api/chat response.

    Returns a frozen ChatResponseV1 with ok=False.
    Uses stable error categories for client compatibility.
    """
    # Include debug_type only if TORQ_DEBUG is enabled
    import os
    include_debug = os.environ.get("TORQ_DEBUG", "false").lower() == "true"

    return ChatResponseV1(
        request_id=request_id,
        trace_id=trace_id,
        ok=False,
        deploy=get_deploy_info(),
        duration_ms=duration_ms,
        session_id=session_id,
        learning_recorded=None,  # Errors don't record learning
        data=None,
        error=ErrorDetail(
            type=error_type,
            message=message[:500],  # Truncate for safety
            code=code,
            debug_type=debug_type if include_debug else None,
        ),
    )


def map_exception_to_error_category(
    exc: Exception,
) -> tuple[ErrorCategory, int]:
    """
    Map Python exceptions to stable error categories.

    Returns (error_category, http_code) tuple.
    """
    exception_type = type(exc).__name__
    exception_msg = str(exc).lower()

    # Check for common patterns
    if isinstance(exc, (ValueError, TypeError, KeyError)):
        return "invalid_request", 400
    if isinstance(exc, PermissionError):
        return "forbidden", 403
    if "not found" in exception_msg or "does not exist" in exception_msg:
        return "not_found", 404
    if "unauthorized" in exception_msg or "authentication" in exception_msg:
        return "unauthorized", 401
    if "timeout" in exception_msg or "deadline" in exception_msg:
        return "provider_error", 502
    if "rate limit" in exception_msg or "too many" in exception_msg:
        return "rate_limited", 429

    # Default for unhandled exceptions
    return "internal_error", 500
