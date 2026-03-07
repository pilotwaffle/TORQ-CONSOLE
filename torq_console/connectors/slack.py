"""
Slack Connector

Phase 8: External Action Fabric, Connectors & Enterprise Workflow Execution

Provides integration with Slack for sending messages, notifications, and
interacting with channels.
"""

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


class SlackConnector(BaseConnector):
    """
    Slack connector for sending messages and notifications.

    Supports:
    - Sending channel messages
    - Sending direct messages
    - Posting messages with blocks/attachments
    - Thread replies
    """

    connector_type = "slack"
    connector_name = "Slack"
    connector_category = ConnectorType.SAAS

    SLACK_API_BASE = "https://slack.com/api"

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._bot_token: Optional[str] = None
        self._webhook_url: Optional[str] = None

    def get_capabilities(self) -> List[ConnectorCapability]:
        """Get Slack connector capabilities."""
        return [
            ConnectorCapability(
                name="send_message",
                description="Send a message to a Slack channel",
                parameters={
                    "channel": {"type": "string", "description": "Channel ID or name (e.g., #general)"},
                    "text": {"type": "string", "description": "Message text"},
                    "blocks": {"type": "array", "description": "Array of block kit blocks"},
                    "thread_ts": {"type": "string", "description": "Thread timestamp for replies"},
                },
                required_params=["channel", "text"],
                optional_params=["blocks", "thread_ts"],
                risk_level=RiskLevel.LOW,
                requires_approval=False
            ),
            ConnectorCapability(
                name="send_webhook",
                description="Send a message via Slack webhook",
                parameters={
                    "webhook_url": {"type": "string", "description": "Slack webhook URL"},
                    "text": {"type": "string", "description": "Message text"},
                    "blocks": {"type": "array", "description": "Array of block kit blocks"},
                    "username": {"type": "string", "description": "Bot username"},
                    "icon_emoji": {"type": "string", "description": "Bot icon emoji"},
                },
                required_params=["webhook_url", "text"],
                optional_params=["blocks", "username", "icon_emoji"],
                risk_level=RiskLevel.LOW,
                requires_approval=False
            ),
            ConnectorCapability(
                name="send_alert",
                description="Send an alert message with formatting",
                parameters={
                    "channel": {"type": "string", "description": "Channel to send alert to"},
                    "title": {"type": "string", "description": "Alert title"},
                    "message": {"type": "string", "description": "Alert message"},
                    "color": {"type": "string", "description": "Attachment color (good, warning, danger)"},
                    "priority": {"type": "string", "description": "Priority level"},
                },
                required_params=["channel", "title", "message"],
                optional_params=["color", "priority"],
                risk_level=RiskLevel.MEDIUM,
                requires_approval=False
            ),
        ]

    async def validate_parameters(self, action_type: str, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate Slack parameters."""
        if action_type == "send_message":
            if "channel" not in parameters:
                return False, "Missing required parameter: channel"
            if "text" not in parameters and "blocks" not in parameters:
                return False, "Either 'text' or 'blocks' parameter is required"
            return True, None

        elif action_type == "send_webhook":
            if "webhook_url" not in parameters:
                return False, "Missing required parameter: webhook_url"
            if "text" not in parameters and "blocks" not in parameters:
                return False, "Either 'text' or 'blocks' parameter is required"
            return True, None

        elif action_type == "send_alert":
            if "channel" not in parameters:
                return False, "Missing required parameter: channel"
            if "title" not in parameters:
                return False, "Missing required parameter: title"
            if "message" not in parameters:
                return False, "Missing required parameter: message"
            return True, None

        return False, f"Unknown action type: {action_type}"

    async def execute(self, action: ExternalAction) -> ActionExecutionResult:
        """Execute a Slack action."""
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

            # Execute based on action type
            if action.action_type == "send_message":
                result = await self._send_message_api(action.parameters)
            elif action.action_type == "send_webhook":
                result = await self._send_webhook(action.parameters)
            elif action.action_type == "send_alert":
                result = await self._send_alert(action.parameters)
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

        except Exception as e:
            return ActionExecutionResult(
                success=False,
                action_id=action.action_id,
                connector_type=self.connector_type,
                action_type=action.action_type,
                error_message=f"Slack error: {str(e)}",
                error_code="SLACK_ERROR",
                retryable=True,
                execution_duration_seconds=time.time() - start_time
            )

    async def _send_message_api(self, params: Dict[str, Any]) -> ActionExecutionResult:
        """Send message using Slack API."""
        token = self._get_bot_token()
        if not token:
            return ActionExecutionResult(
                success=False,
                action_id="",
                connector_type=self.connector_type,
                action_type="send_message",
                error_message="Slack bot token not configured",
                error_code="AUTH_ERROR",
                retryable=False,
                execution_duration_seconds=0
            )

        url = f"{self.SLACK_API_BASE}/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "channel": params["channel"],
            "text": params.get("text", ""),
        }

        if "blocks" in params:
            payload["blocks"] = params["blocks"]

        if "thread_ts" in params:
            payload["thread_ts"] = params["thread_ts"]

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()

                if not data.get("ok"):
                    return ActionExecutionResult(
                        success=False,
                        action_id="",
                        connector_type=self.connector_type,
                        action_type="send_message",
                        error_message=data.get("error", "Unknown error"),
                        error_code="SLACK_API_ERROR",
                        retryable=True,
                        execution_duration_seconds=0
                    )

                return ActionExecutionResult(
                    success=True,
                    action_id="",
                    connector_type=self.connector_type,
                    action_type="send_message",
                    result={
                        "channel": data.get("channel"),
                        "ts": data.get("ts"),
                        "message": data.get("message")
                    },
                    output_data={"timestamp": data.get("ts")},
                    verified=True,
                    verification_message="Message sent successfully",
                    execution_duration_seconds=0
                )

    async def _send_webhook(self, params: Dict[str, Any]) -> ActionExecutionResult:
        """Send message using Slack webhook."""
        webhook_url = params.get("webhook_url") or self._webhook_url
        if not webhook_url:
            return ActionExecutionResult(
                success=False,
                action_id="",
                connector_type=self.connector_type,
                action_type="send_webhook",
                error_message="Webhook URL not configured",
                error_code="CONFIG_ERROR",
                retryable=False,
                execution_duration_seconds=0
            )

        payload = {"text": params.get("text", "")}

        if "blocks" in params:
            payload["blocks"] = params["blocks"]

        if "username" in params:
            payload["username"] = params["username"]

        if "icon_emoji" in params:
            payload["icon_emoji"] = params["icon_emoji"]

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                body = await response.text()
                success = response.status == 200

                return ActionExecutionResult(
                    success=success,
                    action_id="",
                    connector_type=self.connector_type,
                    action_type="send_webhook",
                    result={"status": response.status, "body": body},
                    verified=success,
                    verification_message="Webhook sent" if success else "Webhook failed",
                    execution_duration_seconds=0
                )

    async def _send_alert(self, params: Dict[str, Any]) -> ActionExecutionResult:
        """Send a formatted alert message."""
        color = params.get("color", "warning")
        priority = params.get("priority", "MEDIUM").upper()

        # Map priority to colors if not specified
        if color == "warning":
            color_map = {"LOW": "good", "MEDIUM": "warning", "HIGH": "danger", "CRITICAL": "#FF0000"}
            color = color_map.get(priority, "warning")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f":rotating_light: {params['title']}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Priority:*\n{priority}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": params["message"]
                }
            }
        ]

        # Add footer with timestamp
        import time
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Sent by TORQ Console | {time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        })

        message_params = {
            "channel": params["channel"],
            "text": f":rotating_light: {params['title']}",
            "blocks": blocks
        }

        return await self._send_message_api(message_params)

    def _get_bot_token(self) -> Optional[str]:
        """Get the bot token from config or credentials."""
        if self._bot_token:
            return self._bot_token

        # Token would be loaded from secure storage in production
        # For now, check if it's in the config
        if hasattr(self.config, 'credentials_ref'):
            # In production, this would fetch from secret manager
            pass

        return None

    async def _test_connection(self) -> None:
        """Test Slack API connection."""
        token = self._get_bot_token()
        if not token:
            raise ValueError("Slack bot token not configured")

        url = f"{self.SLACK_API_BASE}/auth.test"
        headers = {"Authorization": f"Bearer {token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if not data.get("ok"):
                    raise ValueError(f"Slack auth failed: {data.get('error')}")


__all__ = ['SlackConnector']
