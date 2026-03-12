"""
TORQ Control Plane - State Manager

L7-M1: Core state management for the Operator Control Plane.

Provides centralized state management for all control plane
components including navigation, user sessions, and system state.
"""

from __future__ import annotations

import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Control Plane State Models
# ============================================================================

class NavigationState(BaseModel):
    """
    Current navigation state within the control plane.
    """
    current_route: str = "/dashboard"
    previous_route: Optional[str] = None
    route_params: Dict[str, Any] = Field(default_factory=dict)
    breadcrumb_history: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class UserSession(BaseModel):
    """
    Active user session information.
    """
    session_id: UUID = Field(default_factory=uuid4)
    user_id: Optional[str] = None
    username: Optional[str] = None
    connected_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    active_views: Set[str] = Field(default_factory=set)
    permissions: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class SystemAlert(BaseModel):
    """
    System-wide alert or notification.
    """
    id: UUID = Field(default_factory=uuid4)
    level: str  # info, warning, error, critical
    title: str
    message: str
    source: str
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_read: bool = False
    action_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class ControlPlaneState(BaseModel):
    """
    Centralized state for the Operator Control Plane.

    Manages navigation, user sessions, system alerts,
    and overall control plane status.
    """
    state_id: UUID = Field(default_factory=uuid4)
    initialized_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

    # Navigation
    navigation: NavigationState = Field(default_factory=NavigationState)

    # Active sessions
    active_sessions: Dict[UUID, UserSession] = Field(default_factory=dict)

    # System alerts
    alerts: List[SystemAlert] = Field(default_factory=list)
    unread_alert_count: int = 0

    # System status
    is_operational: bool = True
    maintenance_mode: bool = False
    feature_flags: Dict[str, bool] = Field(default_factory=dict)

    # Connected services status
    services_status: Dict[str, str] = Field(
        default_factory=lambda: {
            "readiness": "unknown",
            "missions": "unknown",
            "patterns": "unknown",
            "insights": "unknown",
            "memory": "unknown",
        }
    )

    # Metrics cache
    metrics_cache: Dict[str, Any] = Field(default_factory=dict)
    metrics_last_updated: Optional[datetime] = None

    class Config:
        use_enum_values = True


# ============================================================================
# State Manager
# ============================================================================

class ControlPlaneStateManager:
    """
    Manages control plane state with change notification.

    Provides reactive state management for all control plane
    components with subscription-based updates.
    """

    def __init__(self):
        """Initialize the state manager."""
        self._state = ControlPlaneState()
        self._subscribers: Dict[str, List[callable]] = {}
        self._lock = asyncio.Lock()

    def get_state(self) -> ControlPlaneState:
        """
        Get current control plane state.

        Returns:
            Current ControlPlaneState
        """
        return self._state

    async def update_state(
        self,
        updates: Dict[str, Any],
        source: Optional[str] = None,
    ) -> ControlPlaneState:
        """
        Update control plane state and notify subscribers.

        Args:
            updates: Dictionary of state updates
            source: Optional source of the update

        Returns:
            Updated ControlPlaneState
        """
        async with self._lock:
            # Apply updates
            for key, value in updates.items():
                if hasattr(self._state, key):
                    setattr(self._state, key, value)

            self._state.last_updated = datetime.now()

            # Notify subscribers
            await self._notify_subscribers(updates)

            return self._state

    async def navigate_to(
        self,
        route: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> ControlPlaneState:
        """
        Navigate to a new route.

        Args:
            route: Target route
            params: Optional route parameters

        Returns:
            Updated ControlPlaneState
        """
        async with self._lock:
            # Update navigation state
            old_route = self._state.navigation.current_route
            self._state.navigation.previous_route = old_route
            self._state.navigation.current_route = route
            self._state.navigation.route_params = params or {}

            # Add to breadcrumb
            if route not in self._state.navigation.breadcrumb_history:
                self._state.navigation.breadcrumb_history.append(route)
                # Limit breadcrumb size
                if len(self._state.navigation.breadcrumb_history) > 10:
                    self._state.navigation.breadcrumb_history.pop(0)

            self._state.last_updated = datetime.now()

            # Notify subscribers
            await self._notify_subscribers(
                {"navigation": self._state.navigation},
                "navigation"
            )

            return self._state

    async def add_alert(
        self,
        level: str,
        title: str,
        message: str,
        source: str,
        action_url: Optional[str] = None,
        expires_after: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SystemAlert:
        """
        Add a system alert.

        Args:
            level: Alert level (info, warning, error, critical)
            title: Alert title
            message: Alert message
            source: Alert source
            action_url: Optional action URL
            expires_after: Optional seconds until expiration
            metadata: Optional metadata

        Returns:
            Created SystemAlert
        """
        async with self._lock:
            from datetime import timedelta

            expires_at = None
            if expires_after:
                expires_at = datetime.now() + timedelta(seconds=expires_after)

            alert = SystemAlert(
                level=level,
                title=title,
                message=message,
                source=source,
                action_url=action_url,
                expires_at=expires_at,
                metadata=metadata or {},
            )

            self._state.alerts.append(alert)
            self._state.unread_alert_count += 1

            # Clean up expired alerts
            await self._cleanup_expired_alerts()

            # Notify subscribers
            await self._notify_subscribers(
                {"alerts": self._state.alerts},
                "alerts"
            )

            return alert

    async def mark_alert_read(self, alert_id: UUID) -> bool:
        """
        Mark an alert as read.

        Args:
            alert_id: ID of the alert

        Returns:
            True if alert was marked read, False if not found
        """
        async with self._lock:
            for alert in self._state.alerts:
                if alert.id == alert_id and not alert.is_read:
                    alert.is_read = True
                    self._state.unread_alert_count -= 1

                    await self._notify_subscribers(
                        {"alerts": self._state.alerts},
                        "alerts"
                    )
                    return True

            return False

    async def clear_alert(self, alert_id: UUID) -> bool:
        """
        Remove an alert.

        Args:
            alert_id: ID of the alert to remove

        Returns:
            True if alert was removed, False if not found
        """
        async with self._lock:
            for i, alert in enumerate(self._state.alerts):
                if alert.id == alert_id:
                    if not alert.is_read:
                        self._state.unread_alert_count -= 1
                    self._state.alerts.pop(i)

                    await self._notify_subscribers(
                        {"alerts": self._state.alerts},
                        "alerts"
                    )
                    return True

            return False

    async def update_service_status(
        self,
        service: str,
        status: str,
    ) -> ControlPlaneState:
        """
        Update status of a connected service.

        Args:
            service: Service name
            status: Service status (unknown, healthy, degraded, down)

        Returns:
            Updated ControlPlaneState
        """
        async with self._lock:
            self._state.services_status[service] = status
            self._state.last_updated = datetime.now()

            await self._notify_subscribers(
                {"services_status": self._state.services_status},
                "services"
            )

            return self._state

    def subscribe(
        self,
        event_type: str,
        callback: callable,
    ) -> str:
        """
        Subscribe to state change notifications.

        Args:
            event_type: Type of event to subscribe to
            callback: Callback function

        Returns:
            Subscription ID
        """
        import uuid
        sub_id = str(uuid.uuid4())

        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append((sub_id, callback))

        logger.debug(
            f"[StateManager] New subscription to {event_type}: {sub_id}"
        )

        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from state change notifications.

        Args:
            subscription_id: Subscription ID

        Returns:
            True if subscription was removed
        """
        for event_type, subs in self._subscribers.items():
            for i, (sub_id, _) in enumerate(subs):
                if sub_id == subscription_id:
                    subs.pop(i)
                    logger.debug(
                        f"[StateManager] Removed subscription {subscription_id} from {event_type}"
                    )
                    return True

        return False

    async def _notify_subscribers(
        self,
        updates: Dict[str, Any],
        source: Optional[str] = None,
    ):
        """Notify subscribers of state changes."""
        for event_type, event_updates in self._get_event_updates(updates):
            if event_type in self._subscribers:
                for sub_id, callback in self._subscribers[event_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event_updates, source)
                        else:
                            callback(event_updates, source)
                    except Exception as e:
                        logger.error(
                            f"[StateManager] Error in subscriber {sub_id}: {e}"
                        )

    def _get_event_updates(
        self,
        updates: Dict[str, Any],
    ) -> List[tuple]:
        """Map state updates to event types."""
        result = []

        # Navigation events
        if "navigation" in updates:
            result.append(("navigation", updates))

        # Alert events
        if "alerts" in updates:
            result.append(("alerts", updates))

        # Service events
        if "services_status" in updates:
            result.append(("services", updates))

        # Metrics events
        if "metrics" in updates:
            result.append(("metrics", updates))

        # Send to all subscribers
        result.append(("*", updates))

        return result

    async def _cleanup_expired_alerts(self):
        """Remove expired alerts."""
        now = datetime.now()
        active_alerts = []

        for alert in self._state.alerts:
            if alert.expires_at is None or alert.expires_at > now:
                active_alerts.append(alert)
            elif not alert.is_read:
                # Expired unread alerts reduce count
                self._state.unread_alert_count -= 1

        self._state.alerts = active_alerts

    async def refresh_metrics(self, metrics: Dict[str, Any]):
        """
        Update cached metrics.

        Args:
            metrics: New metrics data
        """
        async with self._lock:
            self._state.metrics_cache = metrics
            self._state.metrics_last_updated = datetime.now()

            await self._notify_subscribers(
                {"metrics": metrics},
                "metrics"
            )


# Global state manager instance
_state_manager: Optional[ControlPlaneStateManager] = None


def get_control_plane_state() -> ControlPlaneStateManager:
    """Get the global control plane state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = ControlPlaneStateManager()
    return _state_manager
