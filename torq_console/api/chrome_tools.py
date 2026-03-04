"""
TORQ Console - Chrome Tools API Router

FastAPI endpoints for Prince Flowers Agent to invoke browser operations.

Endpoints:
    POST /api/tools/chrome/health - Check bridge health
    POST /api/tools/chrome/session - Create browser session
    POST /api/tools/chrome/act - Execute browser actions
    POST /api/tools/chrome/observe - Observe browser state
    POST /api/tools/chrome/verify - Convenience endpoint for deployment verification
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from torq_console.tools.chrome_operator import (
    ChromeOperator,
    ChromeConnectionError,
    ChromeExecutionError,
    ChromeApprovalRequired,
    ActionOp,
)


# =============================================================================
# Router
# =============================================================================

router = APIRouter(
    prefix="/api/tools/chrome",
    tags=["chrome"],
    responses={404: {"description": "Not found"}},
)


# =============================================================================
# Request/Response Models
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    active_sessions: int


class SessionCreateRequest(BaseModel):
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionCreateResponse(BaseModel):
    ok: bool
    session_id: str
    message: str


class ActRequest(BaseModel):
    session_id: str
    actions: List[Dict[str, Any]]
    require_approval: bool = False


class ActResponse(BaseModel):
    ok: bool
    session_id: str
    needs_approval: bool = False
    results: List[Dict[str, Any]] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    message: Optional[str] = None


class ObserveRequest(BaseModel):
    session_id: str
    what: List[str] = Field(default_factory=lambda: ["console_logs"])


class VerifyDeploymentRequest(BaseModel):
    url: str
    expected_sha: Optional[str] = None
    expected_text: Optional[str] = None
    screenshot: bool = True
    require_approval: bool = False


class VerifyDeploymentResponse(BaseModel):
    ok: bool
    url: str
    has_screenshot: bool = False
    verification_passed: bool
    errors: List[str] = Field(default_factory=list)


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/health", response_model=HealthResponse)
async def chrome_health():
    """
    Check if the Chrome Bridge service is healthy.

    This endpoint pings the local Chrome Bridge service to verify:
    - Service is running
    - API key is valid
    - Active session count
    """
    chrome = ChromeOperator()
    try:
        health = await chrome.health_check()
        return HealthResponse(**health)
    except ChromeConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    finally:
        await chrome.close()


@router.post("/session", response_model=SessionCreateResponse)
async def chrome_create_session(req: SessionCreateRequest):
    """
    Create a new browser session.

    Returns a session_id that must be approved in the Chrome extension
    before any actions can execute.

    Example metadata:
        {"agent": "prince_flowers", "task": "verify_deployment"}
    """
    chrome = ChromeOperator()
    try:
        session = await chrome.create_session(metadata=req.metadata)
        return SessionCreateResponse(**session.__dict__)
    except ChromeConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    finally:
        await chrome.close()


@router.post("/act", response_model=ActResponse)
async def chrome_act(req: ActRequest):
    """
    Execute browser actions in a session.

    Supported actions:
        {"op": "navigate", "url": "..."}
        {"op": "click", "selector": "...", "by": "css"}
        {"op": "type", "selector": "...", "text": "..."}
        {"op": "extract", "selector": "...", "mode": "text"}
        {"op": "screenshot"}
        {"op": "wait", "ms": 1000}
        {"op": "wait", "selector": "..."}
        {"op": "get_title"}
        {"op": "get_url"}

    If require_approval=False and session not approved, returns
    needs_approval=True with approval_message.

    All actions are logged to Supabase telemetry for audit.
    """
    chrome = ChromeOperator()
    try:
        result = await chrome.act(
            session_id=req.session_id,
            actions=req.actions,
            require_approval=req.require_approval,
        )

        return ActResponse(
            ok=result.ok,
            session_id=result.session_id,
            needs_approval=result.needs_approval,
            results=[r.__dict__ for r in result.results],
            artifacts=result.artifacts,
            errors=result.errors,
            message=result.approval_message,
        )

    except ChromeApprovalRequired as e:
        # Session needs approval
        return ActResponse(
            ok=False,
            session_id=e.session_id,
            needs_approval=True,
            message="Session requires approval in Chrome extension popup",
            results=[],
        )

    except ChromeExecutionError as e:
        raise HTTPException(status_code=500, detail=str(e))

    except ChromeConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))

    finally:
        await chrome.close()


@router.post("/observe")
async def chrome_observe(req: ObserveRequest):
    """
    Observe browser state (console logs, network events, etc.).

    Parameters:
        session_id: Browser session ID
        what: List of data types to collect

    Example:
        POST /api/tools/chrome/observe
        {
            "session_id": "abc-123",
            "what": ["console_logs", "network_events"]
        }
    """
    chrome = ChromeOperator()
    try:
        data = await chrome.observe(session_id=req.session_id, what=req.what)
        return data
    except ChromeConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    finally:
        await chrome.close()


@router.post("/verify", response_model=VerifyDeploymentResponse)
async def chrome_verify_deployment(req: VerifyDeploymentRequest, background_tasks: BackgroundTasks):
    """
    Verify a web deployment (convenience endpoint).

    This endpoint handles common deployment verification tasks:
    1. Navigate to URL
    2. Wait for page load
    3. Optionally capture screenshot
    4. Check for expected SHA/text
    5. Return verification result

    Example usage:
        POST /api/tools/chrome/verify
        {
            "url": "https://web-production-74ed0.up.railway.app/health",
            "expected_sha": "c12b9f86",
            "screenshot": true
        }
    """
    from torq_console.tools.chrome_operator import verify_deployment

    try:
        result = await verify_deployment(
            url=req.url,
            expected_sha=req.expected_sha,
            expected_text=req.expected_text,
            screenshot=req.screenshot,
        )

        return VerifyDeploymentResponse(
            ok=result.ok,
            url=req.url,
            has_screenshot="screenshot_png_data_url" in result.artifacts,
            verification_passed=len(result.errors) == 0,
            errors=result.errors,
        )

    except ChromeConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))

    except ChromeExecutionError as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Utility Endpoints
# =============================================================================

@router.get("/actions")
async def list_supported_actions():
    """
    List all supported browser actions.

    Returns a catalog of actions that can be used with /act endpoint.
    """
    return {
        "actions": [
            {
                "op": "navigate",
                "description": "Navigate to a URL",
                "params": {"url": "string (required)"}
            },
            {
                "op": "click",
                "description": "Click an element",
                "params": {
                    "selector": "string (required)",
                    "by": "css | id | name | xpath (default: css)"
                }
            },
            {
                "op": "type",
                "description": "Type text into an input field",
                "params": {
                    "selector": "string (required)",
                    "text": "string (required)",
                    "by": "css | id | name | xpath (default: css)"
                }
            },
            {
                "op": "extract",
                "description": "Extract data from an element",
                "params": {
                    "selector": "string (required)",
                    "mode": "text | html | value | href | src | attr (default: text)",
                    "attr": "string (required if mode=attr)"
                }
            },
            {
                "op": "screenshot",
                "description": "Capture visible tab screenshot",
                "params": {}
            },
            {
                "op": "wait",
                "description": "Wait for time or element",
                "params": {
                    "ms": "number (milliseconds, optional)",
                    "selector": "string (optional, wait for element)",
                    "timeout_ms": "number (default: 5000, for selector wait)"
                }
            },
            {
                "op": "get_title",
                "description": "Get page title",
                "params": {}
            },
            {
                "op": "get_url",
                "description": "Get current page URL",
                "params": {}
            },
            {
                "op": "reload",
                "description": "Reload the current page",
                "params": {}
            },
            {
                "op": "go_back",
                "description": "Navigate back in history",
                "params": {}
            },
            {
                "op": "go_forward",
                "description": "Navigate forward in history",
                "params": {}
            },
        ],
        "safety_notes": [
            "Password fields always require approval",
            "Financial/payment domains require approval",
            "Destructive actions (delete, purchase) require approval",
            "All actions are logged for audit"
        ]
    }


# =============================================================================
# Setup for integration with main app
# =============================================================================

def setup_chrome_router(app):
    """
    Register the Chrome tools router with a FastAPI app.

    Usage in main.py:
        from torq_console.api.chrome_tools import setup_chrome_router
        setup_chrome_router(app)
    """
    app.include_router(router)
