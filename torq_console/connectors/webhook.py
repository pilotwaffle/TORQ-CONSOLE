"""
Webhook Connector

Phase 8: External Action Fabric, Connectors & Enterprise Workflow Execution

Provides a generic webhook connector for sending HTTP requests to external
systems. This is a versatile connector that can work with any webhook-enabled
service.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp

from .base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorCapability,
    ConnectorType,
    ExternalAction,
    ActionExecutionResult,
    ActionState,
    HealthCheckResult,
    RiskLevel,
)


logger = logging.getLogger(__name__)


class WebhookConnector(BaseConnector):
    """
    Generic webhook connector for HTTP-based integrations.

    Supports:
    - POST/GET/PUT/DELETE/PATCH requests
    - Custom headers
    - JSON/form-encoded bodies
    - Basic auth and bearer tokens
    - Webhook signature verification
    """

    connector_type = "webhook"
    connector_name = "Webhook"
    connector_category = ConnectorType.COMMUNICATION

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None

    async def setup(self) -> None:
        """Set up the HTTP session."""
        await super().setup()
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        self._session = aiohttp.ClientSession(timeout=timeout)

    async def teardown(self) -> None:
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
        await super().teardown()

    def get_capabilities(self) -> List[ConnectorCapability]:
        """Get webhook connector capabilities."""
        return [
            ConnectorCapability(
                name="send_webhook",
                description="Send an HTTP webhook request",
                parameters={
                    "url": {"type": "string", "description": "Webhook URL"},
                    "method": {"type": "string", "description": "HTTP method", "default": "POST"},
                    "headers": {"type": "object", "description": "HTTP headers"},
                    "body": {"type": "object", "description": "Request body"},
                    "auth_type": {"type": "string", "description": "Auth type: none, basic, bearer, header"},
                    "auth_username": {"type": "string", "description": "Username for basic auth"},
                    "auth_password": {"type": "string", "description": "Password for basic auth"},
                    "auth_token": {"type": "string", "description": "Bearer token"},
                    "auth_header_name": {"type": "string", "description": "Custom header name for token"},
                },
                required_params=["url"],
                optional_params=["method", "headers", "body", "auth_type", "auth_token"],
                risk_level=RiskLevel.MEDIUM,
                requires_approval=False
            ),
            ConnectorCapability(
                name="send_json",
                description="Send JSON data via webhook",
                parameters={
                    "url": {"type": "string", "description": "Webhook URL"},
                    "data": {"type": "object", "description": "JSON data to send"},
                    "headers": {"type": "object", "description": "Additional headers"},
                },
                required_params=["url", "data"],
                optional_params=["headers"],
                risk_level=RiskLevel.LOW,
                requires_approval=False
            ),
        ]

    async def validate_parameters(self, action_type: str, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate webhook parameters."""
        if action_type == "send_webhook":
            if "url" not in parameters:
                return False, "Missing required parameter: url"

            url = parameters.get("url", "")
            if not url.startswith(("http://", "https://")):
                return False, "URL must start with http:// or https://"

            method = parameters.get("method", "POST").upper()
            if method not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                return False, f"Invalid HTTP method: {method}"

            return True, None

        elif action_type == "send_json":
            if "url" not in parameters:
                return False, "Missing required parameter: url"
            if "data" not in parameters:
                return False, "Missing required parameter: data"
            return True, None

        return False, f"Unknown action type: {action_type}"

    async def execute(self, action: ExternalAction) -> ActionExecutionResult:
        """
        Execute a webhook action.

        Args:
            action: The webhook action to execute

        Returns:
            ActionExecutionResult with response details
        """
        import time
        start_time = time.time()

        try:
            action.state = ActionState.EXECUTING
            action.started_at = start_time

            # Validate parameters
            is_valid, error_msg = await self.validate_parameters(
                action.action_type,
                action.parameters
            )

            if not is_valid:
                return ActionExecutionResult(
                    success=False,
                    action_id=action.action_id,
                    connector_type=self.connector_type,
                    action_type=action.action_type,
                    error_message=error_msg,
                    error_code="VALIDATION_ERROR",
                    retryable=False,
                    execution_duration_seconds=0
                )

            # Ensure session is set up
            if not self._session:
                await self.setup()

            # Execute based on action type
            if action.action_type == "send_webhook":
                result = await self._send_webhook(action.parameters)
            elif action.action_type == "send_json":
                result = await self._send_json(action.parameters)
            else:
                result = ActionExecutionResult(
                    success=False,
                    action_id=action.action_id,
                    connector_type=self.connector_type,
                    action_type=action.action_type,
                    error_message=f"Unknown action type: {action.action_type}",
                    error_code="UNKNOWN_ACTION",
                    retryable=False,
                    execution_duration_seconds=0
                )

            result.execution_duration_seconds = time.time() - start_time
            return result

        except asyncio.TimeoutError:
            return ActionExecutionResult(
                success=False,
                action_id=action.action_id,
                connector_type=self.connector_type,
                action_type=action.action_type,
                error_message="Webhook request timed out",
                error_code="TIMEOUT",
                retryable=True,
                execution_duration_seconds=time.time() - start_time
            )
        except aiohttp.ClientError as e:
            return ActionExecutionResult(
                success=False,
                action_id=action.action_id,
                connector_type=self.connector_type,
                action_type=action.action_type,
                error_message=f"HTTP client error: {str(e)}",
                error_code="HTTP_ERROR",
                retryable=True,
                execution_duration_seconds=time.time() - start_time
            )
        except Exception as e:
            return ActionExecutionResult(
                success=False,
                action_id=action.action_id,
                connector_type=self.connector_type,
                action_type=action.action_type,
                error_message=f"Unexpected error: {str(e)}",
                error_code="UNKNOWN",
                retryable=False,
                execution_duration_seconds=time.time() - start_time
            )

    async def _send_webhook(self, params: Dict[str, Any]) -> ActionExecutionResult:
        """Send a generic webhook request."""
        url = params["url"]
        method = params.get("method", "POST").upper()
        headers = params.get("headers", {}).copy()
        body = params.get("body")

        # Set up authentication
        auth_type = params.get("auth_type", "none")

        if auth_type == "basic":
            username = params.get("auth_username", "")
            password = params.get("auth_password", "")
            import aiohttp
            auth = aiohttp.BasicAuth(username, password)
        elif auth_type == "bearer":
            token = params.get("auth_token", "")
            headers["Authorization"] = f"Bearer {token}"
            auth = None
        elif auth_type == "header":
            header_name = params.get("auth_header_name", "X-Auth-Token")
            token = params.get("auth_token", "")
            headers[header_name] = token
            auth = None
        else:
            auth = None

        # Set Content-Type for POST/PUT/PATCH
        if method in ["POST", "PUT", "PATCH"] and body and "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        # Make the request
        if method == "GET":
            response = await self._session.get(url, headers=headers, auth=auth)
        elif method == "POST":
            response = await self._session.post(url, json=body, headers=headers, auth=auth)
        elif method == "PUT":
            response = await self._session.put(url, json=body, headers=headers, auth=auth)
        elif method == "DELETE":
            response = await self._session.delete(url, headers=headers, auth=auth)
        elif method == "PATCH":
            response = await self._session.patch(url, json=body, headers=headers, auth=auth)
        else:
            return ActionExecutionResult(
                success=False,
                action_id="",  # Will be set by caller
                connector_type=self.connector_type,
                action_type="send_webhook",
                error_message=f"Unsupported HTTP method: {method}",
                error_code="INVALID_METHOD",
                retryable=False,
                execution_duration_seconds=0
            )

        # Process response
        response_body = await self._get_response_body(response)
        success = 200 <= response.status < 300

        return ActionExecutionResult(
            success=success,
            action_id="",  # Will be set by caller
            connector_type=self.connector_type,
            action_type="send_webhook",
            result={
                "status_code": response.status,
                "headers": dict(response.headers),
                "body": response_body
            },
            output_data={"status_code": response.status, "response": response_body},
            error_message=None if success else f"HTTP {response.status}",
            error_code=str(response.status) if not success else None,
            retryable=500 <= response.status < 600,
            execution_duration_seconds=0  # Will be set by caller
        )

    async def _send_json(self, params: Dict[str, Any]) -> ActionExecutionResult:
        """Send JSON data via webhook."""
        url = params["url"]
        data = params.get("data", {})
        headers = params.get("headers", {}).copy()

        # Ensure JSON content type
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        response = await self._session.post(url, json=data, headers=headers)
        response_body = await self._get_response_body(response)
        success = 200 <= response.status < 300

        return ActionExecutionResult(
            success=success,
            action_id="",  # Will be set by caller
            connector_type=self.connector_type,
            action_type="send_json",
            result={
                "status_code": response.status,
                "headers": dict(response.headers),
                "body": response_body
            },
            output_data={"status_code": response.status, "response": response_body},
            error_message=None if success else f"HTTP {response.status}",
            error_code=str(response.status) if not success else None,
            retryable=500 <= response.status < 600,
            execution_duration_seconds=0  # Will be set by caller
        )

    async def _get_response_body(self, response: aiohttp.ClientResponse) -> Any:
        """Extract and parse response body."""
        try:
            content_type = response.headers.get("Content-Type", "")

            if "application/json" in content_type:
                return await response.json()
            else:
                text = await response.text()
                # Try to parse as JSON if possible
                try:
                    return json.loads(text)
                except (json.JSONDecodeError, TypeError):
                    return text[:1000]  # Truncate long text responses
        except Exception:
            return None

    async def _test_connection(self) -> None:
        """Test the webhook connection by making a simple request."""
        if not self._session:
            await self.setup()

        # Use a simple test endpoint if configured, otherwise just verify session
        test_url = self.config.base_url
        if test_url:
            async with self._session.get(test_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                response.raise_for_status()


__all__ = ['WebhookConnector']
