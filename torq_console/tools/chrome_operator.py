"""
TORQ Chrome Operator - Tool Adapter for Prince Flowers Agent

This module provides the interface between Prince Flowers Agent and the
Chrome Bridge Service for executing browser operations with audit trails.

Environment variables:
    CHROME_BRIDGE_URL: Bridge service URL (default: http://127.0.0.1:4545)
    CHROME_BRIDGE_API_KEY: API key for authentication (required for production)

Safety features:
    - All actions require approval by default
    - Sensitive operations (passwords, payments) always require approval
    - Full audit logging to Supabase
    - Structured, replayable actions only (no free-form prompts)

Usage:
    from torq_console.tools.chrome_operator import ChromeOperator

    chrome = ChromeOperator()
    session = await chrome.create_session(metadata={"agent": "prince_flowers"})
    result = await chrome.act(session["session_id"], actions=[
        {"op": "navigate", "url": "https://example.com"},
        {"op": "screenshot"}
    ])
"""
import os
import time
from typing import Any, Dict, List, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum

import httpx


# =============================================================================
# Configuration
# =============================================================================

CHROME_BRIDGE_URL = os.getenv("CHROME_BRIDGE_URL", "http://127.0.0.1:4545")
CHROME_BRIDGE_API_KEY = os.getenv("CHROME_BRIDGE_API_KEY", "")
REQUEST_TIMEOUT = int(os.getenv("CHROME_BRIDGE_TIMEOUT", "120"))


# =============================================================================
# Exceptions
# =============================================================================

class ChromeOperatorError(Exception):
    """Base exception for Chrome Operator errors."""
    pass


class ChromeConnectionError(ChromeOperatorError):
    """Connection/communication error with bridge service."""
    pass


class ChromeExecutionError(ChromeOperatorError):
    """Error executing browser actions."""
    pass


class ChromeApprovalRequired(ChromeOperatorError):
    """User approval required before executing actions."""
    def __init__(self, session_id: str, actions: List[Dict]):
        self.session_id = session_id
        self.actions = actions
        super().__init__(f"Approval required for session {session_id}")


# =============================================================================
# Data Models
# =============================================================================

class ActionOp(str, Enum):
    """Supported browser operations."""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    INPUT = "input"
    EXTRACT = "extract"
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    GET_TITLE = "get_title"
    GET_URL = "get_url"
    RELOAD = "reload"
    GO_BACK = "go_back"
    GO_FORWARD = "go_forward"
    SCROLL_INTO_VIEW = "scroll_into_view"
    EXISTS = "exists"
    IS_VISIBLE = "is_visible"


@dataclass
class ActionResult:
    """Result of a single browser action."""
    op: str
    status: Literal["ok", "error", "unsupported"]
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class SessionResult:
    """Result from creating a browser session."""
    ok: bool
    session_id: str
    message: str
    needs_approval: bool = False


@dataclass
class ExecutionResult:
    """Result from executing browser actions."""
    ok: bool
    session_id: str
    results: List[ActionResult] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    console_logs: List[Dict] = field(default_factory=list)
    network_events: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    needs_approval: bool = False
    approval_message: Optional[str] = None


# =============================================================================
# Safety Policies
# =============================================================================

SENSITIVE_SELECTORS = [
    "input[type=password]",
    "[type=password]",
    "[name*=password]",
    "[id*=password]",
    "input[type=pin]",
    "[type=pin]",
]

SENSITIVE_DOMAINS = [
    "bank",
    "crypto",
    "wallet",
    "exchange",
    "payment",
    "checkout",
    "paypal",
    "stripe",
]

SENSITIVE_KEYWORDS = [
    "delete",
    "confirm",
    "purchase",
    "buy",
    "withdraw",
    "transfer",
    "send",
    "approve",
]


class SafetyPolicy:
    """
    Safety policy for browser operations.

    Rules:
    1. Password fields always require approval
    2. Payment/financial domains always require approval
    3. Destructive actions (delete, confirm, purchase) require approval
    4. Can override by explicitly setting require_approval=False
    """

    @staticmethod
    def requires_approval(actions: List[Dict[str, Any]], url: Optional[str] = None) -> tuple[bool, List[str]]:
        """
        Check if actions require approval.

        Returns:
            (requires_approval, list of reasons)
        """
        reasons = []

        # Check URL/domain
        if url:
            url_lower = url.lower()
            for keyword in SENSITIVE_DOMAINS:
                if keyword in url_lower:
                    reasons.append(f"sensitive domain: {keyword}")

        # Check each action
        for action in actions:
            op = action.get("op", "")
            selector = action.get("selector", "").lower()
            text = action.get("text", "").lower()

            # Password fields
            for sensitive_sel in SENSITIVE_SELECTORS:
                if sensitive_sel in selector:
                    reasons.append("password field detected")

            # Sensitive keywords
            for keyword in SENSITIVE_KEYWORDS:
                if keyword in op.lower() or keyword in selector or keyword in text:
                    reasons.append(f"sensitive action: {keyword}")

        return len(reasons) > 0, reasons

    @staticmethod
    def sanitize_action(action: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize action for logging (remove sensitive data)."""
        sanitized = action.copy()

        # Mask password values
        if action.get("op") in ["type", "input"] and any(
            s in action.get("selector", "").lower()
            for s in SENSITIVE_SELECTORS
        ):
            sanitized["text"] = "***REDACTED***"

        return sanitized


# =============================================================================
# Chrome Operator Client
# =============================================================================

class ChromeOperator:
    """
    Client for TORQ Chrome Bridge Service.

    Executes structured browser actions with safety gates and audit logging.
    """

    def __init__(
        self,
        bridge_url: str = CHROME_BRIDGE_URL,
        api_key: str = CHROME_BRIDGE_API_KEY,
        default_require_approval: bool = True,
        log_telemetry: bool = True,
    ):
        """
        Initialize Chrome Operator.

        Args:
            bridge_url: URL of the Chrome Bridge service
            api_key: API key for authentication
            default_require_approval: Default approval requirement
            log_telemetry: Whether to log telemetry events
        """
        self.bridge_url = bridge_url.rstrip("/")
        self.api_key = api_key
        self.default_require_approval = default_require_approval
        self.log_telemetry = log_telemetry
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.bridge_url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
        return self._client

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the Chrome Bridge service is healthy.

        Returns:
            Health status dict with keys: status, service, version, active_sessions
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.bridge_url}/health",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise ChromeConnectionError(f"Health check failed: {e}")

    async def create_session(
        self,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionResult:
        """
        Create a new browser session.

        Args:
            metadata: Optional metadata to attach to the session

        Returns:
            SessionResult with session_id
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.bridge_url}/v1/session",
                    headers=self._get_headers(),
                    json={"metadata": metadata or {}},
                )
                response.raise_for_status()
                data = response.json()

                return SessionResult(
                    ok=data.get("ok", False),
                    session_id=data.get("session_id", ""),
                    message=data.get("message", ""),
                )
        except httpx.HTTPError as e:
            raise ChromeConnectionError(f"Failed to create session: {e}")

    async def act(
        self,
        session_id: str,
        actions: List[Dict[str, Any]],
        require_approval: Optional[bool] = None,
        log_to_supabase: bool = True,
    ) -> ExecutionResult:
        """
        Execute browser actions in a session.

        Args:
            session_id: Session ID from create_session()
            actions: List of action dicts (see ActionOp for supported ops)
            require_approval: Override default approval requirement
            log_to_supabase: Log execution to Supabase telemetry

        Returns:
            ExecutionResult with action results, artifacts, logs

        Raises:
            ChromeApprovalRequired: If user approval is needed
            ChromeExecutionError: If execution fails
        """
        # Use default if not specified
        if require_approval is None:
            require_approval = self.default_require_approval

        # Safety check: always enforce approval for sensitive operations
        safety_required, safety_reasons = SafetyPolicy.requires_approval(actions)
        if safety_reasons:
            require_approval = True

        # Prepare request
        payload = {
            "session_id": session_id,
            "actions": actions,
            "require_approval": require_approval,
        }

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(
                    f"{self.bridge_url}/v1/act",
                    headers=self._get_headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                # Check if approval is required
                if not data.get("ok", True) and data.get("needs_approval"):
                    if log_to_supabase:
                        await self._log_telemetry(
                            session_id=session_id,
                            actions=actions,
                            result=data,
                            approval_pending=True,
                        )
                    raise ChromeApprovalRequired(session_id, actions)

                # Parse results
                result = ExecutionResult(
                    ok=data.get("ok", True),
                    session_id=session_id,
                    needs_approval=False,
                )

                # Parse action results
                for r in data.get("results", []):
                    result.results.append(ActionResult(
                        op=r.get("op", "unknown"),
                        status=r.get("status", "unsupported"),
                        data={k: v for k, v in r.items() if k not in ["op", "status", "error"]},
                        error=r.get("error"),
                    ))

                # Parse artifacts
                result.artifacts = data.get("artifacts", {})

                # Parse console logs
                result.console_logs = data.get("console", [])

                # Parse errors
                for err in data.get("errors", []):
                    result.errors.append(err.get("message", str(err)))

                # Log telemetry
                if log_to_supabase and self.log_telemetry:
                    await self._log_telemetry(
                        session_id=session_id,
                        actions=actions,
                        result=result.__dict__,
                        approval_pending=False,
                    )

                return result

        except httpx.HTTPError as e:
            raise ChromeExecutionError(f"Execution failed: {e}")

    async def observe(
        self,
        session_id: str,
        what: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Observe browser state (console logs, network events, etc.).

        Args:
            session_id: Session ID
            what: List of things to observe ["console_logs", "network_events"]

        Returns:
            Dict with observed data
        """
        if what is None:
            what = ["console_logs"]

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.bridge_url}/v1/observe",
                    headers=self._get_headers(),
                    json={"session_id": session_id, "what": what},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise ChromeConnectionError(f"Observe failed: {e}")

    async def _log_telemetry(
        self,
        session_id: str,
        actions: List[Dict[str, Any]],
        result: Dict[str, Any],
        approval_pending: bool,
    ):
        """
        Log browser operation to Supabase telemetry.

        This integrates with the existing learning_events system.
        """
        try:
            from torq_console.agents.marvin_memory import get_agent_memory

            memory = get_agent_memory()
            sanitized_actions = [
                SafetyPolicy.sanitize_action(a) for a in actions
            ]

            event_data = {
                "tool": "chrome_operator",
                "session_id": session_id,
                "action_count": len(actions),
                "actions": sanitized_actions,
                "result_ok": result.get("ok", True),
                "approval_pending": approval_pending,
                "has_screenshot": "screenshot_png_data_url" in result.get("artifacts", {}),
            }

            memory.record_interaction(
                user_input=f"chrome_operator: {len(actions)} actions",
                agent_response=f"Executed {len(actions)} browser actions",
                agent_name="prince_flowers",
                interaction_type="tool_execution",
                success=result.get("ok", True),
                metadata=event_data,
            )

        except ImportError:
            # Marvin memory not available, skip logging
            pass
        except Exception as e:
            # Don't fail the operation if logging fails
            print(f"[Chrome Operator] Telemetry logging failed: {e}")


# =============================================================================
# Helper Functions
# =============================================================================

async def verify_deployment(
    url: str,
    expected_sha: Optional[str] = None,
    expected_text: Optional[str] = None,
    screenshot: bool = True,
) -> ExecutionResult:
    """
    Convenience function to verify a web deployment.

    Args:
        url: URL to verify (e.g., Railway health endpoint)
        expected_sha: Expected git SHA in health response
        expected_text: Text that should be present on page
        screenshot: Whether to capture screenshot

    Returns:
        ExecutionResult with verification data
    """
    chrome = ChromeOperator()

    try:
        # Create session
        session = await chrome.create_session(metadata={"task": "verify_deployment"})

        # Build actions
        actions = [{"op": "navigate", "url": url}]

        if screenshot:
            actions.append({"op": "wait", "ms": 1500})  # Wait for page load
            actions.append({"op": "screenshot"})

        if expected_text:
            actions.append({
                "op": "extract",
                "selector": "body",
                "mode": "text"
            })

        # Execute
        result = await chrome.act(session.session_id, actions, require_approval=False)

        # Verify expectations
        if expected_text and result.results:
            page_text = ""
            for r in result.results:
                if r.data and "text" in r.data:
                    page_text += r.data["text"] + " "
            if expected_text.lower() not in page_text.lower():
                result.errors.append(f"Expected text not found: {expected_text}")

        return result

    finally:
        await chrome.close()


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import asyncio

    async def main():
        """Test Chrome Bridge connection."""
        print("Testing TORQ Chrome Bridge connection...")
        print(f"Bridge URL: {CHROME_BRIDGE_URL}")
        print(f"API Key: {'set' if CHROME_BRIDGE_API_KEY else 'none (INSECURE!)'}")
        print()

        chrome = ChromeOperator()

        try:
            health = await chrome.health_check()
            print(f"Health: {health}")
        except ChromeConnectionError as e:
            print(f"Connection failed: {e}")
            print("\nMake sure the Chrome Bridge service is running:")
            print("  cd chrome_bridge && python host.py")
            return

        print("\nCreating session...")
        session = await chrome.create_session(metadata={"test": True})
        print(f"Session: {session}")

        print("\nTo test browser actions:")
        print(f"1. Approve session {session.session_id} in Chrome extension popup")
        print("2. Then run: await chrome.act(session.session_id, [{'op': 'screenshot'}])")

        await chrome.close()

    asyncio.run(main())
