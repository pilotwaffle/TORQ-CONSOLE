"""
Confirmation Manager for User Confirmation Workflows

Handles user confirmation requirements for high-risk operations
"""

import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import logging

from .models import (
    ConfirmationRequest, ToolRequest, RiskLevel,
    OperationType, Decision
)

logger = logging.getLogger(__name__)


class ConfirmationMethod(str, Enum):
    """Methods for user confirmation"""
    CLI_PROMPT = "cli_prompt"
    WEB_DIALOG = "web_dialog"
    EMAIL = "email"
    SMS = "sms"
    EXTERNAL_APPROVAL = "external_approval"


class ConfirmationStatus(str, Enum):
    """Confirmation request status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DENIED = "denied"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ConfirmationManager:
    """Manages user confirmation workflows for tool operations"""

    def __init__(self, default_timeout: int = 300):
        """
        Initialize confirmation manager

        Args:
            default_timeout: Default timeout for confirmations in seconds
        """
        self.default_timeout = default_timeout
        self.pending_confirmations: Dict[str, ConfirmationRequest] = {}
        self.confirmation_history: Dict[str, Dict[str, Any]] = {}
        self.confirmation_handlers: Dict[ConfirmationMethod, Callable] = {
            ConfirmationMethod.CLI_PROMPT: self._handle_cli_confirmation,
            ConfirmationMethod.WEB_DIALOG: self._handle_web_confirmation,
            ConfirmationMethod.EMAIL: self._handle_email_confirmation,
            ConfirmationMethod.SMS: self._handle_sms_confirmation,
            ConfirmationMethod.EXTERNAL_APPROVAL: self._handle_external_approval,
        }

    def request_confirmation(
        self,
        request: ToolRequest,
        risk_level: RiskLevel,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        method: ConfirmationMethod = ConfirmationMethod.CLI_PROMPT,
        user_id: Optional[str] = None
    ) -> ConfirmationRequest:
        """
        Request user confirmation for a tool operation

        Args:
            request: Original tool request
            risk_level: Risk level of the operation
            message: Confirmation message to display
            details: Additional details about the operation
            timeout: Confirmation timeout in seconds
            method: Confirmation method to use
            user_id: User identifier

        Returns:
            Confirmation request object
        """
        confirmation_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(seconds=timeout or self.default_timeout)

        confirmation = ConfirmationRequest(
            request_id=confirmation_id,
            tool_name=request.tool_name,
            operation=request.operation,
            risk_level=risk_level,
            message=message,
            details=details or {},
            expires_at=expires_at
        )

        # Store confirmation request
        self.pending_confirmations[confirmation_id] = confirmation

        # Add to history
        self.confirmation_history[confirmation_id] = {
            "request": request.dict(),
            "confirmation": confirmation.dict(),
            "method": method.value,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": ConfirmationStatus.PENDING.value
        }

        # Trigger confirmation handler
        try:
            handler = self.confirmation_handlers[method]
            handler(confirmation, user_id=user_id)
        except Exception as e:
            logger.error(f"Error in confirmation handler for {method}: {e}")
            # Fallback to CLI prompt
            self._handle_cli_confirmation(confirmation, user_id=user_id)

        logger.info(f"Requested confirmation {confirmation_id} for tool {request.tool_name}")
        return confirmation

    def confirm_operation(self, confirmation_id: str, confirmed: bool, user_id: Optional[str] = None) -> bool:
        """
        Process user confirmation response

        Args:
            confirmation_id: Confirmation request ID
            confirmed: Whether user confirmed (True) or denied (False)
            user_id: User identifier

        Returns:
            True if confirmation was processed successfully
        """
        if confirmation_id not in self.pending_confirmations:
            logger.warning(f"Confirmation not found: {confirmation_id}")
            return False

        confirmation = self.pending_confirmations[confirmation_id]

        # Check if confirmation has expired
        if datetime.utcnow() > confirmation.expires_at:
            logger.info(f"Confirmation {confirmation_id} expired")
            self._update_confirmation_status(confirmation_id, ConfirmationStatus.EXPIRED)
            del self.pending_confirmations[confirmation_id]
            return False

        # Update confirmation status
        confirmation.confirmed = confirmed
        status = ConfirmationStatus.CONFIRMED if confirmed else ConfirmationStatus.DENIED

        # Update history
        if confirmation_id in self.confirmation_history:
            self.confirmation_history[confirmation_id].update({
                "status": status.value,
                "confirmed_by": user_id,
                "resolved_at": datetime.utcnow().isoformat()
            })

        # Remove from pending
        del self.pending_confirmations[confirmation_id]

        logger.info(f"Confirmation {confirmation_id} {status.value} by user {user_id}")
        return True

    def cancel_confirmation(self, confirmation_id: str, reason: Optional[str] = None) -> bool:
        """
        Cancel a pending confirmation

        Args:
            confirmation_id: Confirmation request ID
            reason: Reason for cancellation

        Returns:
            True if cancellation was successful
        """
        if confirmation_id not in self.pending_confirmations:
            return False

        # Update history
        if confirmation_id in self.confirmation_history:
            self.confirmation_history[confirmation_id].update({
                "status": ConfirmationStatus.CANCELLED.value,
                "cancellation_reason": reason,
                "resolved_at": datetime.utcnow().isoformat()
            })

        # Remove from pending
        del self.pending_confirmations[confirmation_id]

        logger.info(f"Confirmation {confirmation_id} cancelled: {reason}")
        return True

    def get_confirmation_status(self, confirmation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a confirmation request

        Args:
            confirmation_id: Confirmation request ID

        Returns:
            Confirmation status dictionary
        """
        if confirmation_id in self.pending_confirmations:
            confirmation = self.pending_confirmations[confirmation_id]
            return {
                "id": confirmation_id,
                "status": ConfirmationStatus.PENDING.value,
                "expires_at": confirmation.expires_at.isoformat(),
                "message": confirmation.message,
                "confirmed": confirmation.confirmed
            }

        elif confirmation_id in self.confirmation_history:
            return self.confirmation_history[confirmation_id]

        return None

    def cleanup_expired_confirmations(self) -> int:
        """
        Clean up expired confirmation requests

        Returns:
            Number of expired confirmations cleaned up
        """
        current_time = datetime.utcnow()
        expired_ids = []

        for confirmation_id, confirmation in self.pending_confirmations.items():
            if current_time > confirmation.expires_at:
                expired_ids.append(confirmation_id)

        for confirmation_id in expired_ids:
            self._update_confirmation_status(confirmation_id, ConfirmationStatus.EXPIRED)
            del self.pending_confirmations[confirmation_id]

        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired confirmations")

        return len(expired_ids)

    def get_pending_confirmations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of pending confirmations

        Args:
            user_id: Filter by user ID

        Returns:
            List of pending confirmation requests
        """
        pending = []

        for confirmation_id, confirmation in self.pending_confirmations.items():
            if user_id is None or self.confirmation_history.get(confirmation_id, {}).get("user_id") == user_id:
                pending.append({
                    "id": confirmation_id,
                    "tool_name": confirmation.tool_name,
                    "operation": confirmation.operation.value,
                    "risk_level": confirmation.risk_level.value,
                    "message": confirmation.message,
                    "expires_at": confirmation.expires_at.isoformat(),
                    "created_at": confirmation.timestamp.isoformat()
                })

        return pending

    def _update_confirmation_status(self, confirmation_id: str, status: ConfirmationStatus):
        """Update confirmation status in history"""
        if confirmation_id in self.confirmation_history:
            self.confirmation_history[confirmation_id].update({
                "status": status.value,
                "resolved_at": datetime.utcnow().isoformat()
            })

    # Confirmation handlers

    def _handle_cli_confirmation(self, confirmation: ConfirmationRequest, user_id: Optional[str] = None):
        """Handle CLI prompt confirmation"""
        try:
            import sys

            # Build confirmation prompt
            prompt = self._build_cli_prompt(confirmation)

            # Print to stderr to avoid interfering with tool output
            print(prompt, file=sys.stderr, flush=True)

            # For non-interactive environments, we'll just log it
            if not sys.stdin.isatty():
                logger.info(f"CLI confirmation requested for {confirmation.tool_name} (non-interactive mode)")

        except Exception as e:
            logger.error(f"Error in CLI confirmation handler: {e}")

    def _handle_web_confirmation(self, confirmation: ConfirmationRequest, user_id: Optional[str] = None):
        """Handle web dialog confirmation"""
        # This would integrate with a web UI
        logger.info(f"Web confirmation requested for {confirmation.tool_name}")
        # Implementation would depend on web framework being used

    def _handle_email_confirmation(self, confirmation: ConfirmationRequest, user_id: Optional[str] = None):
        """Handle email confirmation"""
        logger.info(f"Email confirmation requested for {confirmation.tool_name}")
        # Implementation would send email with confirmation link

    def _handle_sms_confirmation(self, confirmation: ConfirmationRequest, user_id: Optional[str] = None):
        """Handle SMS confirmation"""
        logger.info(f"SMS confirmation requested for {confirmation.tool_name}")
        # Implementation would send SMS with confirmation code

    def _handle_external_approval(self, confirmation: ConfirmationRequest, user_id: Optional[str] = None):
        """Handle external approval system"""
        logger.info(f"External approval requested for {confirmation.tool_name}")
        # Implementation would integrate with external approval system

    def _build_cli_prompt(self, confirmation: ConfirmationRequest) -> str:
        """Build CLI prompt for confirmation"""
        risk_symbols = {
            RiskLevel.LOW: "ℹ️",
            RiskLevel.MEDIUM: "⚠️",
            RiskLevel.HIGH: "🚨",
            RiskLevel.CRITICAL: "💀"
        }

        symbol = risk_symbols.get(confirmation.risk_level, "❓")
        prompt = f"\n{symbol} CONFIRMATION REQUIRED\n"
        prompt += "=" * 50 + "\n"
        prompt += f"Tool: {confirmation.tool_name}\n"
        prompt += f"Operation: {confirmation.operation.value}\n"
        prompt += f"Risk Level: {confirmation.risk_level.value.upper()}\n\n"
        prompt += f"{confirmation.message}\n\n"

        if confirmation.details:
            prompt += "Additional Details:\n"
            for key, value in confirmation.details.items():
                prompt += f"  {key}: {value}\n"
            prompt += "\n"

        prompt += f"Expires at: {confirmation.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        prompt += "=" * 50 + "\n"

        return prompt

    def add_confirmation_handler(self, method: ConfirmationMethod, handler: Callable):
        """
        Add a custom confirmation handler

        Args:
            method: Confirmation method
            handler: Handler function
        """
        self.confirmation_handlers[method] = handler

    def get_confirmation_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about confirmations

        Returns:
            Statistics dictionary
        """
        stats = {
            "pending_count": len(self.pending_confirmations),
            "total_confirmations": len(self.confirmation_history),
            "status_counts": {},
            "risk_level_counts": {},
            "method_counts": {}
        }

        # Count by status
        for confirmation_data in self.confirmation_history.values():
            status = confirmation_data.get("status", "unknown")
            stats["status_counts"][status] = stats["status_counts"].get(status, 0) + 1

            method = confirmation_data.get("method", "unknown")
            stats["method_counts"][method] = stats["method_counts"].get(method, 0) + 1

            confirmation = confirmation_data.get("confirmation", {})
            risk_level = confirmation.get("risk_level", "unknown")
            stats["risk_level_counts"][risk_level] = stats["risk_level_counts"].get(risk_level, 0) + 1

        return stats