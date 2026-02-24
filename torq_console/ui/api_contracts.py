"""
Versioned API Response Contracts

Defines stable response schemas for HTTP endpoints.
This enables frontend/backend independent evolution.

Schema versions:
- torq-chat-response-v1: Initial stable chat response format
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DeployInfo(BaseModel):
    """Deploy identity information for trace correlation."""
    platform: str = Field(..., description="Deployment platform: railway, vercel, local")
    git_sha: str = Field(..., description="Git commit SHA (abbreviated)")
    app_version: str = Field(..., description="App version string")
    environment: str = Field(..., description="Environment: production, staging, development")


class ErrorDetail(BaseModel):
    """Structured error information."""
    type: str = Field(..., description="Error type/class name")
    message: str = Field(..., description="Error message (user-safe)")
    code: Optional[str] = Field(None, description="Error code if available")


class ChatResponseV1(BaseModel):
    """
    Versioned chat API response schema.

    Schema: torq-chat-response-v1

    This contract should not be changed. New versions should
    extend this with a new schema version (e.g., ChatResponseV2).
    """
    # Schema version for forward compatibility
    _schema: str = Field("torq-chat-response-v1", description="Response schema version")

    # Request correlation
    request_id: str = Field(..., description="Unique request identifier for trace correlation")
    trace_id: str = Field(..., description="Telemetry trace ID if available")

    # Response status
    ok: bool = Field(..., description="True if request succeeded, False if error")

    # Deploy info for trace correlation
    deploy: DeployInfo = Field(..., description="Deployment identity for logs correlation")

    # Response data (success case)
    response: Optional[str] = Field(None, description="Agent's text response")
    agent: Optional[str] = Field(None, description="Agent name that handled request")
    duration_ms: int = Field(..., description="Request processing time in milliseconds")

    # Error data (failure case)
    error: Optional[ErrorDetail] = Field(None, description="Error details if ok=False")

    # Metadata
    session_id: Optional[str] = Field(None, description="Session identifier if available")
    learning_recorded: bool = Field(False, description="Whether learning event was recorded")

    # Agent metadata (for debugging/development)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional agent metadata")

    class Config:
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
                "response": "Hello! How can I help you today?",
                "agent": "prince_flowers",
                "duration_ms": 1500,
                "session_id": "sess_456",
                "learning_recorded": True
            }
        }


class ErrorResponseV1(BaseModel):
    """
    Error-only response for cleaner error handling.

    Schema: torq-error-v1
    """
    _schema: str = Field("torq-error-v1", description="Error schema version")

    request_id: str = Field(..., description="Unique request identifier")
    trace_id: str = Field(..., description="Telemetry trace ID")

    ok: bool = Field(False, description="Always False for error responses")

    deploy: DeployInfo = Field(..., description="Deploy identity for correlation")

    error: ErrorDetail = Field(..., description="Error details")

    class Config:
        json_schema_extra = {
            "example": {
                "_schema": "torq-error-v1",
                "request_id": "req_123456",
                "trace_id": "trace_789",
                "ok": False,
                "deploy": {
                    "platform": "railway",
                    "git_sha": "abc1234",
                    "app_version": "1.0.10",
                    "environment": "production"
                },
                "error": {
                    "type": "ValueError",
                    "message": "Invalid parameter",
                    "code": "400"
                }
            }
        }


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
        app_version=get_app_version_with_source().split()[0],  # Take version part
        environment=os.environ.get("RAILWAY_ENVIRONMENT", "development"),
    )
