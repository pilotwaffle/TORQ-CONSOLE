"""
TORQ Control Plane - Router

L7-M1: URL routing and navigation for the Operator Control Plane.

Provides client-side routing for single-page application
navigation within the control plane.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# ============================================================================
# Route Models
# ============================================================================

@dataclass
class Route:
    """
    A route definition for the control plane.
    """
    path: str
    name: str
    title: str
    component: str
    icon: Optional[str] = None
    required_permission: Optional[str] = None
    parent: Optional[str] = None
    children: List["Route"] = None
    meta: Dict[str, Any] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.meta is None:
            self.meta = {}


class RouteMatch(BaseModel):
    """
    Result of route matching.
    """
    route: Route
    params: Dict[str, str] = {}
    query: Dict[str, str] = {}
    is_exact: bool = True


# ============================================================================
# Route Definitions
# ============================================================================

# Core routes
CORE_ROUTES = [
    Route(
        path="/",
        name="home",
        title="Dashboard",
        component="Dashboard",
        icon="dashboard",
    ),
    Route(
        path="/readiness",
        name="readiness",
        title="Readiness Governance",
        component="ReadinessDashboard",
        icon="shield-check",
    ),
    Route(
        path="/readiness/candidates",
        name="readiness_candidates",
        title="Candidates",
        component="CandidateList",
        icon="users",
        parent="readiness",
    ),
    Route(
        path="/readiness/candidates/:id",
        name="candidate_detail",
        title="Candidate Details",
        component="CandidateDetail",
        parent="readiness",
    ),
    Route(
        path="/readiness/promotions",
        name="promotions",
        title="Promotions",
        component="PromotionQueue",
        icon="arrow-up-circle",
        parent="readiness",
    ),
    Route(
        path="/missions",
        name="missions",
        title="Mission Command",
        component="MissionDashboard",
        icon="target",
    ),
    Route(
        path="/missions/active",
        name="active_missions",
        title="Active Missions",
        component="ActiveMissionList",
        parent="missions",
    ),
    Route(
        path="/missions/agents",
        name="agent_monitor",
        title="Agent Monitor",
        component="AgentMonitor",
        parent="missions",
    ),
    Route(
        path="/patterns",
        name="patterns",
        title="Pattern Intelligence",
        component="PatternDashboard",
        icon="pattern",
    ),
    Route(
        path="/patterns/discovered",
        name="discovered_patterns",
        title="Discovered",
        component="DiscoveredPatterns",
        parent="patterns",
    ),
    Route(
        path="/patterns/validated",
        name="validated_patterns",
        title="Validated",
        component="ValidatedPatterns",
        parent="patterns",
    ),
    Route(
        path="/intelligence",
        name="intelligence",
        title="Operational Intelligence",
        component="IntelligenceDashboard",
        icon="brain",
    ),
    Route(
        path="/intelligence/insights",
        name="insights",
        title="Insights",
        component="InsightView",
        parent="intelligence",
    ),
    Route(
        path="/intelligence/memory",
        name="memory",
        title="Governed Memory",
        component="MemoryView",
        parent="intelligence",
    ),
    Route(
        path="/governance",
        name="governance",
        title="Governance Actions",
        component="GovernanceDashboard",
        icon="gavel",
    ),
    Route(
        path="/governance/queue",
        name="action_queue",
        title="Action Queue",
        component="ActionQueue",
        parent="governance",
    ),
    Route(
        path="/governance/overrides",
        name="overrides",
        title="Overrides",
        component="OverrideHistory",
        parent="governance",
    ),
    Route(
        path="/settings",
        name="settings",
        title="Settings",
        component="Settings",
        icon="settings",
        required_permission="admin",
    ),
    Route(
        path="/alerts",
        name="alerts",
        title="System Alerts",
        component="AlertCenter",
        icon="alert",
    ),
]


# ============================================================================
# Router
# ============================================================================

class ControlPlaneRouter:
    """
    Client-side router for the control plane.

    Handles route matching, navigation, and browser history.
    """

    def __init__(self, routes: Optional[List[Route]] = None):
        """
        Initialize the router.

        Args:
            routes: Optional list of routes (defaults to CORE_ROUTES)
        """
        self.routes = routes or CORE_ROUTES
        self.current_path: str = "/"
        self.current_route: Optional[Route] = None
        self._navigation_hooks: List[Callable] = []

        # Build route lookup
        self._route_map: Dict[str, Route] = {}
        self._build_route_map()

    def _build_route_map(self):
        """Build a lookup map for routes."""
        for route in self.routes:
            self._route_map[route.path] = route
            for child in route.children:
                self._route_map[child.path] = child

    def match_route(
        self,
        path: str,
        query: Optional[Dict[str, str]] = None,
    ) -> Optional[RouteMatch]:
        """
        Match a path to a route.

        Args:
            path: URL path to match
            query: Optional query parameters

        Returns:
            RouteMatch if found, None otherwise
        """
        query = query or {}

        # Try exact match first
        if path in self._route_map:
            return RouteMatch(
                route=self._route_map[path],
                params={},
                query=query,
                is_exact=True,
            )

        # Try parameterized match
        for route_path, route in self._route_map.items():
            params = self._match_params(route_path, path)
            if params is not None:
                return RouteMatch(
                    route=route,
                    params=params,
                    query=query,
                    is_exact=True,
                )

        # Try prefix match for nested routes
        for route_path, route in self._route_map.items():
            if path.startswith(route_path + "/"):
                return RouteMatch(
                    route=route,
                    params={},
                    query=query,
                    is_exact=False,
                )

        return None

    def _match_params(self, route_path: str, actual_path: str) -> Optional[Dict[str, str]]:
        """
        Extract parameters from a path match.

        Args:
            route_path: Route path with :param notation
            actual_path: Actual path to match against

        Returns:
            Dictionary of parameters if match, None otherwise
        """
        route_parts = route_path.split("/")
        actual_parts = actual_path.split("/")

        if len(route_parts) != len(actual_parts):
            return None

        params = {}
        for route_part, actual_part in zip(route_parts, actual_parts):
            if route_part.startswith(":"):
                param_name = route_part[1:]
                params[param_name] = actual_part
            elif route_part != actual_part:
                return None

        return params

    async def navigate(
        self,
        path: str,
        query: Optional[Dict[str, str]] = None,
        replace: bool = False,
    ) -> Optional[RouteMatch]:
        """
        Navigate to a path.

        Args:
            path: Target path
            query: Optional query parameters
            replace: Replace current history entry

        Returns:
            RouteMatch if navigation succeeded, None otherwise
        """
        # Run navigation hooks
        for hook in self._navigation_hooks:
            result = hook(self.current_path, path)
            if result is False:
                logger.info(f"[Router] Navigation blocked by hook: {path}")
                return None

        # Match route
        match = self.match_route(path, query)

        if match is None:
            logger.warning(f"[Router] No route found for path: {path}")
            return None

        # Update state
        self.current_path = path
        self.current_route = match.route

        logger.info(f"[Router] Navigated to: {path}")

        return match

    def back(self) -> Optional[str]:
        """
        Navigate back in history.

        Returns:
            Path navigated to, or None if no history
        """
        # This would integrate with browser history
        # For now, return None
        return None

    def add_navigation_hook(self, hook: Callable) -> str:
        """
        Add a navigation guard hook.

        Args:
            hook: Function that receives (from, to) and returns False to block

        Returns:
            Hook ID
        """
        import uuid
        hook_id = str(uuid.uuid4())
        self._navigation_hooks.append(hook)
        return hook_id

    def remove_navigation_hook(self, hook_id: str):
        """
        Remove a navigation hook.

        Args:
            hook_id: ID of hook to remove
        """
        # In a real implementation, we'd track hook IDs
        pass

    def get_breadcrumbs(self, path: Optional[str] = None) -> List[Route]:
        """
        Get breadcrumb trail for a path.

        Args:
            path: Optional path (defaults to current path)

        Returns:
            List of routes forming breadcrumb trail
        """
        path = path or self.current_path
        breadcrumbs: List[Route] = []

        # Find matching route
        match = self.match_route(path)
        if match:
            # Add parent routes
            if match.route.parent:
                parent_route = self._route_map.get(f"/{match.route.parent}")
                if parent_route:
                    breadcrumbs.append(parent_route)

            # Add current route
            breadcrumbs.append(match.route)

        return breadcrumbs

    def get_child_routes(self, parent_name: str) -> List[Route]:
        """
        Get child routes for a parent route.

        Args:
            parent_name: Name of parent route

        Returns:
            List of child routes
        """
        children = []
        for route in self.routes:
            if route.parent == parent_name:
                children.append(route)
            # Also check nested children
            for child in route.children:
                if child.parent == parent_name:
                    children.append(child)

        return children

    def get_routes_by_permission(self, permission: str) -> List[Route]:
        """
        Get routes that require a specific permission.

        Args:
            permission: Required permission

        Returns:
            List of routes requiring that permission
        """
        return [
            route for route in self.routes
            if route.required_permission == permission
        ]

    def generate_path(
        self,
        route_name: str,
        params: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Generate a path from route name and parameters.

        Args:
            route_name: Name of the route
            params: Optional route parameters

        Returns:
            Generated path or None if route not found
        """
        for route in self.routes:
            if route.name == route_name:
                path = route.path
                if params:
                    for key, value in params.items():
                        path = path.replace(f":{key}", value)
                return path

            # Check children
            for child in route.children:
                if child.name == route_name:
                    path = child.path
                    if params:
                        for key, value in params.items():
                            path = path.replace(f":{key}", value)
                    return path

        return None


# Global router instance
_router: Optional[ControlPlaneRouter] = None


def get_control_plane_router() -> ControlPlaneRouter:
    """Get the global control plane router instance."""
    global _router
    if _router is None:
        _router = ControlPlaneRouter()
    return _router
