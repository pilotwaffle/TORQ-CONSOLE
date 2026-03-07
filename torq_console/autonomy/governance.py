"""
Multi-Tenant Governance - Workspace isolation, RBAC, and enterprise audit.

Phase 6: Multi-Tenant Governance & Enterprise Control Plane

This module provides:
- Role-Based Access Control (RBAC)
- Workspace isolation and scoping
- Policy inheritance hierarchies
- Enterprise audit capabilities
- Resource quotas and limits
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from .models import (
    Monitor, AutonomousTask, ExecutionMode,
    ActionRisk, PolicyLevel
)
from .state_store import StateStore


logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================

class ResourceType(str, Enum):
    """Types of resources that can be governed."""
    MONITOR = "monitor"
    TASK = "task"
    PLAN = "plan"
    APPROVAL = "approval"
    POLICY = "policy"
    WORKSPACE = "workspace"
    AGENT = "agent"

class Permission(str, Enum):
    """Permissions for RBAC."""
    # Monitor permissions
    VIEW_MONITORS = "view_monitors"
    CREATE_MONITORS = "create_monitors"
    EDIT_MONITORS = "edit_monitors"
    DELETE_MONITORS = "delete_monitors"
    ENABLE_MONITORS = "enable_monitors"

    # Task permissions
    VIEW_TASKS = "view_tasks"
    CREATE_TASKS = "create_tasks"
    EXECUTE_TASKS = "execute_tasks"
    CANCEL_TASKS = "cancel_tasks"

    # Plan permissions
    VIEW_PLANS = "view_plans"
    CREATE_PLANS = "create_plans"
    REVIEW_PLANS = "review_plans"
    APPROVE_PLANS = "approve_plans"
    EXECUTE_PLANS = "execute_plans"

    # Approval permissions
    VIEW_APPROVALS = "view_approvals"
    GRANT_APPROVALS = "grant_approvals"

    # Policy permissions
    VIEW_POLICIES = "view_policies"
    CREATE_POLICIES = "create_policies"
    EDIT_POLICIES = "edit_policies"

    # Workspace permissions
    VIEW_WORKSPACE = "view_workspace"
    EDIT_WORKSPACE = "edit_workspace"
    DELETE_WORKSPACE = "delete_workspace"
    MANAGE_MEMBERS = "manage_members"

    # Admin permissions
    ADMIN = "admin"  # Full access
    AUDIT = "audit"   # Read-only audit access


class RoleType(str, Enum):
    """Built-in role types."""
    OWNER = "owner"           # Full control of workspace
    ADMIN = "admin"           # Administrative access
    OPERATOR = "operator"     # Can operate but not manage
    VIEWER = "viewer"         # Read-only access
    AUDITOR = "auditor"       # Audit-only access
    CUSTOM = "custom"         # Custom role


class AuditEventType(str, Enum):
    """Types of audit events."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"

    RESOURCE_CREATED = "resource_created"
    RESOURCE_UPDATED = "resource_updated"
    RESOURCE_DELETED = "resource_deleted"
    RESOURCE_ACCESSED = "resource_accessed"

    POLICY_CREATED = "policy_created"
    POLICY_UPDATED = "policy_updated"
    POLICY_DELETED = "policy_deleted"
    POLICY_VIOLATION = "policy_violation"

    WORKSPACE_CREATED = "workspace_created"
    WORKSPACE_UPDATED = "workspace_updated"
    WORKSPACE_DELETED = "workspace_deleted"

    TASK_EXECUTED = "task_executed"
    PLAN_APPROVED = "plan_approved"
    PLAN_DENIED = "plan_denied"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"


class QuotaType(str, Enum):
    """Types of resource quotas."""
    MAX_MONITORS = "max_monitors"
    MAX_TASKS_PER_DAY = "max_tasks_per_day"
    MAX_CONCURRENT_TASKS = "max_concurrent_tasks"
    MAX_STORAGE_GB = "max_storage_gb"
    MAX_API_CALLS_PER_DAY = "max_api_calls_per_day"
    MAX_AGENTS = "max_agents"


# ============================================================================
# Models
# ============================================================================

class PermissionSet(BaseModel):
    """Set of permissions for a role."""
    permissions: List[Permission] = Field(default_factory=list)

    # Resource constraints
    resource_type: Optional[ResourceType] = None  # If set, permissions apply only to this type
    workspace_scope: Optional[str] = None  # If set, permissions apply only to this workspace

    def has_permission(self, permission: Permission) -> bool:
        """Check if this permission set includes a permission."""
        return permission in self.permissions

    def add_permission(self, permission: Permission) -> None:
        """Add a permission."""
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission: Permission) -> bool:
        """Remove a permission."""
        if permission in self.permissions:
            self.permissions.remove(permission)
            return True
        return False


class Role(BaseModel):
    """A role defining permissions for users."""
    role_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    role_type: RoleType = RoleType.CUSTOM

    # Permissions
    permissions: PermissionSet = Field(default_factory=PermissionSet)

    # Hierarchy
    inherits_from: Optional[str] = None  # Parent role ID

    # Metadata
    workspace_id: Optional[str] = None  # None = global role
    created_at: float = Field(default_factory=time.time)
    created_by: Optional[str] = None
    is_system_role: bool = False  # System roles cannot be deleted

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }

    def has_permission(self, permission: Permission) -> bool:
        """Check if this role grants a permission."""
        # ADMIN permission grants all other permissions
        if Permission.ADMIN in self.permissions.permissions:
            return True
        return self.permissions.has_permission(permission)


class User(BaseModel):
    """A user in the system."""
    user_id: str
    username: str
    email: Optional[str] = None
    display_name: Optional[str] = None

    # Authentication
    auth_provider: Optional[str] = None  # e.g., "oauth", "saml", "local"
    external_id: Optional[str] = None  # ID from external provider

    # Status
    is_active: bool = True
    is_superuser: bool = False

    # Metadata
    created_at: float = Field(default_factory=time.time)
    last_login: Optional[float] = None
    last_activity: Optional[float] = None

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


class WorkspaceMember(BaseModel):
    """A user's membership in a workspace."""
    membership_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: str

    # Role
    role_id: str

    # Membership details
    invited_by: Optional[str] = None
    invited_at: float = Field(default_factory=time.time)
    joined_at: Optional[float] = None

    # Status
    status: str = "pending"  # pending, active, disabled, removed

    # Metadata
    is_owner: bool = False  # Original creator of workspace

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


class Workspace(BaseModel):
    """A workspace for multi-tenant isolation."""
    workspace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None

    # Owner
    owner_id: str

    # Settings
    is_active: bool = True
    is_default: bool = False

    # Quotas
    quotas: Dict[str, int] = Field(default_factory=dict)

    # Metadata
    created_at: float = Field(default_factory=time.time)
    created_by: Optional[str] = None
    updated_at: Optional[float] = None

    # Statistics
    member_count: int = 0
    monitor_count: int = 0
    task_count: int = 0

    # Environment isolation
    environments: List[str] = Field(default_factory=lambda: ["dev", "staging", "production"])

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


class QuotaLimit(BaseModel):
    """A quota limit for a workspace."""
    quota_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    quota_type: QuotaType
    limit: int
    current_usage: int = 0

    # Time window for periodic quotas
    period_seconds: Optional[int] = None  # None = lifetime quota
    reset_at: Optional[float] = None

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }

    @property
    def is_exceeded(self) -> bool:
        """Check if quota is exceeded."""
        return self.current_usage >= self.limit

    @property
    def remaining(self) -> int:
        """Get remaining quota."""
        return max(0, self.limit - self.current_usage)

    @property
    def utilization_percent(self) -> float:
        """Get utilization as percentage."""
        if self.limit == 0:
            return 100.0
        return (self.current_usage / self.limit) * 100


class AuditEvent(BaseModel):
    """An audit event for compliance and security."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType

    # Who
    user_id: Optional[str] = None
    username: Optional[str] = None

    # What
    resource_type: Optional[ResourceType] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None

    # Where
    workspace_id: Optional[str] = None
    environment: Optional[str] = None

    # Details
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Result
    success: bool = True
    error_message: Optional[str] = None

    # Timestamp
    timestamp: float = Field(default_factory=time.time)

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


class PolicyHierarchy(BaseModel):
    """A policy hierarchy node for inheritance."""
    policy_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None

    # Hierarchy
    parent_id: Optional[str] = None  # Parent policy for inheritance
    children: List[str] = Field(default_factory=list)  # Child policy IDs

    # Priority (higher = more priority)
    priority: int = 0

    # Scope
    workspace_id: Optional[str] = None  # None = global policy
    environment: Optional[str] = None   # None = all environments

    # Policy content
    rules: Dict[str, Any] = Field(default_factory=dict)

    # Status
    enabled: bool = True
    created_at: float = Field(default_factory=time.time)
    created_by: Optional[str] = None

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


# ============================================================================
# Governance Engine
# ============================================================================

class GovernanceEngine:
    """
    Engine for multi-tenant governance.

    Provides:
    - Role-Based Access Control (RBAC)
    - Workspace isolation
    - Resource quotas
    - Audit logging
    - Policy inheritance
    """

    def __init__(self, state_store: Optional[StateStore] = None):
        self.state_store = state_store
        self.logger = logging.getLogger(__name__)

        # In-memory storage
        self._workspaces: Dict[str, Workspace] = {}
        self._roles: Dict[str, Role] = {}
        self._members: Dict[str, WorkspaceMember] = {}
        self._users: Dict[str, User] = {}
        self._quotas: Dict[str, QuotaLimit] = {}
        self._audit_events: List[AuditEvent] = []

        # Load default roles
        self._load_default_roles()

    def _load_default_roles(self) -> None:
        """Load default system roles."""
        # Owner role - full access
        owner_role = Role(
            name="Owner",
            description="Full access to workspace",
            role_type=RoleType.OWNER,
            permissions=PermissionSet(permissions=[
                Permission.ADMIN
            ]),
            is_system_role=True
        )
        self._roles[owner_role.role_id] = owner_role

        # Admin role - administrative access
        admin_role = Role(
            name="Admin",
            description="Administrative access",
            role_type=RoleType.ADMIN,
            permissions=PermissionSet(permissions=[
                Permission.VIEW_MONITORS,
                Permission.CREATE_MONITORS,
                Permission.EDIT_MONITORS,
                Permission.DELETE_MONITORS,
                Permission.ENABLE_MONITORS,
                Permission.VIEW_TASKS,
                Permission.CREATE_TASKS,
                Permission.EXECUTE_TASKS,
                Permission.CANCEL_TASKS,
                Permission.VIEW_PLANS,
                Permission.CREATE_PLANS,
                Permission.REVIEW_PLANS,
                Permission.APPROVE_PLANS,
                Permission.EXECUTE_PLANS,
                Permission.VIEW_APPROVALS,
                Permission.GRANT_APPROVALS,
                Permission.VIEW_POLICIES,
                Permission.EDIT_WORKSPACE,
                Permission.MANAGE_MEMBERS,
            ]),
            is_system_role=True
        )
        self._roles[admin_role.role_id] = admin_role

        # Operator role - can operate but not manage
        operator_role = Role(
            name="Operator",
            description="Can operate resources",
            role_type=RoleType.OPERATOR,
            permissions=PermissionSet(permissions=[
                Permission.VIEW_MONITORS,
                Permission.VIEW_TASKS,
                Permission.CREATE_TASKS,
                Permission.EXECUTE_TASKS,
                Permission.CANCEL_TASKS,
                Permission.VIEW_PLANS,
                Permission.CREATE_PLANS,
                Permission.VIEW_APPROVALS,
            ]),
            is_system_role=True
        )
        self._roles[operator_role.role_id] = operator_role

        # Viewer role - read-only
        viewer_role = Role(
            name="Viewer",
            description="Read-only access",
            role_type=RoleType.VIEWER,
            permissions=PermissionSet(permissions=[
                Permission.VIEW_MONITORS,
                Permission.VIEW_TASKS,
                Permission.VIEW_PLANS,
                Permission.VIEW_APPROVALS,
                Permission.VIEW_POLICIES,
                Permission.VIEW_WORKSPACE,
            ]),
            is_system_role=True
        )
        self._roles[viewer_role.role_id] = viewer_role

        # Auditor role - audit access
        auditor_role = Role(
            name="Auditor",
            description="Audit log access",
            role_type=RoleType.AUDITOR,
            permissions=PermissionSet(permissions=[
                Permission.AUDIT,
                Permission.VIEW_WORKSPACE,
            ]),
            is_system_role=True
        )
        self._roles[auditor_role.role_id] = auditor_role

    # ========================================================================
    # Workspace Management
    # ========================================================================

    async def create_workspace(
        self,
        name: str,
        owner_id: str,
        description: Optional[str] = None,
        quotas: Optional[Dict[str, int]] = None
    ) -> Workspace:
        """Create a new workspace."""
        workspace = Workspace(
            name=name,
            description=description,
            owner_id=owner_id,
            created_by=owner_id,
            quotas=quotas or self._default_quotas()
        )

        self._workspaces[workspace.workspace_id] = workspace

        # Add owner as member with owner role
        owner_role = self._get_role_by_type(RoleType.OWNER)
        if owner_role:
            await self.add_member(
                workspace.workspace_id,
                owner_id,
                owner_role.role_id,
                is_owner=True
            )

        # Log audit event
        await self._log_audit_event(
            AuditEventType.WORKSPACE_CREATED,
            user_id=owner_id,
            resource_type=ResourceType.WORKSPACE,
            resource_id=workspace.workspace_id,
            resource_name=name,
            workspace_id=workspace.workspace_id,
            details={"description": description}
        )

        return workspace

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get a workspace by ID."""
        return self._workspaces.get(workspace_id)

    def list_workspaces(
        self,
        user_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Workspace]:
        """List workspaces."""
        workspaces = list(self._workspaces.values())

        # Filter by user membership
        if user_id:
            member_workspace_ids = {
                m.workspace_id
                for m in self._members.values()
                if m.user_id == user_id and m.status == "active"
            }
            workspaces = [w for w in workspaces if w.workspace_id in member_workspace_ids]

        # Filter by active status
        if is_active is not None:
            workspaces = [w for w in workspaces if w.is_active == is_active]

        return workspaces

    async def update_workspace(
        self,
        workspace_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """Update a workspace."""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False

        if name is not None:
            workspace.name = name
        if description is not None:
            workspace.description = description
        if is_active is not None:
            workspace.is_active = is_active

        workspace.updated_at = time.time()

        return True

    # ========================================================================
    # Role Management
    # ========================================================================

    def create_role(
        self,
        name: str,
        permissions: List[Permission],
        workspace_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Role:
        """Create a custom role."""
        role = Role(
            name=name,
            description=description,
            role_type=RoleType.CUSTOM,
            permissions=PermissionSet(permissions=permissions),
            workspace_id=workspace_id
        )

        self._roles[role.role_id] = role
        return role

    def get_role(self, role_id: str) -> Optional[Role]:
        """Get a role by ID."""
        return self._roles.get(role_id)

    def list_roles(
        self,
        workspace_id: Optional[str] = None
    ) -> List[Role]:
        """List roles."""
        roles = list(self._roles.values())

        if workspace_id:
            roles = [r for r in roles if r.workspace_id == workspace_id or r.workspace_id is None]

        return roles

    def _get_role_by_type(self, role_type: RoleType) -> Optional[Role]:
        """Get a system role by type."""
        for role in self._roles.values():
            if role.role_type == role_type and role.is_system_role:
                return role
        return None

    # ========================================================================
    # Member Management
    # ========================================================================

    async def add_member(
        self,
        workspace_id: str,
        user_id: str,
        role_id: str,
        invited_by: Optional[str] = None,
        is_owner: bool = False
    ) -> WorkspaceMember:
        """Add a member to a workspace."""
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user_id,
            role_id=role_id,
            invited_by=invited_by,
            is_owner=is_owner,
            status="active" if is_owner else "pending"
        )

        self._members[member.membership_id] = member

        # Update workspace member count
        workspace = self.get_workspace(workspace_id)
        if workspace:
            workspace.member_count += 1

        return member

    async def update_member_role(
        self,
        workspace_id: str,
        user_id: str,
        new_role_id: str
    ) -> bool:
        """Update a member's role."""
        # Find membership
        for member in self._members.values():
            if member.workspace_id == workspace_id and member.user_id == user_id:
                member.role_id = new_role_id
                return True
        return False

    def get_member(
        self,
        workspace_id: str,
        user_id: str
    ) -> Optional[WorkspaceMember]:
        """Get a user's membership in a workspace."""
        for member in self._members.values():
            if member.workspace_id == workspace_id and member.user_id == user_id:
                return member
        return None

    def list_members(
        self,
        workspace_id: str,
        status: Optional[str] = None
    ) -> List[WorkspaceMember]:
        """List members of a workspace."""
        members = [
            m for m in self._members.values()
            if m.workspace_id == workspace_id
        ]

        if status:
            members = [m for m in members if m.status == status]

        return members

    # ========================================================================
    # Permission Checking
    # ========================================================================

    def has_permission(
        self,
        user_id: str,
        workspace_id: str,
        permission: Permission
    ) -> bool:
        """
        Check if a user has a permission in a workspace.

        This is the core RBAC check.
        """
        # Check superuser
        user = self._users.get(user_id)
        if user and user.is_superuser:
            return True

        # Get membership
        member = self.get_member(workspace_id, user_id)
        if not member or member.status != "active":
            return False

        # Get role
        role = self.get_role(member.role_id)
        if not role:
            return False

        # Check permission
        return role.has_permission(permission)

    def check_permissions(
        self,
        user_id: str,
        workspace_id: str,
        permissions: List[Permission],
        require_all: bool = True
    ) -> bool:
        """
        Check multiple permissions.

        Args:
            user_id: User to check
            workspace_id: Workspace context
            permissions: List of permissions to check
            require_all: True = all permissions required, False = any permission sufficient

        Returns:
            True if permission check passes
        """
        results = [
            self.has_permission(user_id, workspace_id, p)
            for p in permissions
        ]

        if require_all:
            return all(results)
        else:
            return any(results)

    # ========================================================================
    # Quota Management
    # ========================================================================

    def set_quota(
        self,
        workspace_id: str,
        quota_type: QuotaType,
        limit: int,
        period_seconds: Optional[int] = None
    ) -> QuotaLimit:
        """Set a quota for a workspace."""
        quota = QuotaLimit(
            workspace_id=workspace_id,
            quota_type=quota_type,
            limit=limit,
            period_seconds=period_seconds
        )

        self._quotas[quota.quota_id] = quota
        return quota

    def get_quota(
        self,
        workspace_id: str,
        quota_type: QuotaType
    ) -> Optional[QuotaLimit]:
        """Get a quota for a workspace."""
        for quota in self._quotas.values():
            if quota.workspace_id == workspace_id and quota.quota_type == quota_type:
                return quota
        return None

    def check_quota(
        self,
        workspace_id: str,
        quota_type: QuotaType,
        amount: int = 1
    ) -> tuple[bool, Optional[QuotaLimit]]:
        """
        Check if a quota allows an action.

        Returns:
            (allowed, quota) - quota is None if not set
        """
        quota = self.get_quota(workspace_id, quota_type)
        if not quota:
            return True, None  # No quota set

        allowed = (quota.current_usage + amount) <= quota.limit
        return allowed, quota

    def consume_quota(
        self,
        workspace_id: str,
        quota_type: QuotaType,
        amount: int = 1
    ) -> bool:
        """Consume quota for an action."""
        quota = self.get_quota(workspace_id, quota_type)
        if not quota:
            return True  # No quota to consume

        allowed = (quota.current_usage + amount) <= quota.limit
        if allowed:
            quota.current_usage += amount

        return allowed

    def _default_quotas(self) -> Dict[str, int]:
        """Get default quotas for new workspaces."""
        return {
            QuotaType.MAX_MONITORS: 100,
            QuotaType.MAX_TASKS_PER_DAY: 1000,
            QuotaType.MAX_CONCURRENT_TASKS: 10,
            QuotaType.MAX_STORAGE_GB: 10,
            QuotaType.MAX_API_CALLS_PER_DAY: 10000,
            QuotaType.MAX_AGENTS: 5,
        }

    # ========================================================================
    # Audit Logging
    # ========================================================================

    async def _log_audit_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        workspace_id: Optional[str] = None,
        environment: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditEvent:
        """Log an audit event."""
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            workspace_id=workspace_id,
            environment=environment,
            details=details or {},
            success=success,
            error_message=error_message
        )

        self._audit_events.append(event)

        # Persist if state store available
        if self.state_store:
            try:
                from .models import TaskStateRecord, TaskState
                record = TaskStateRecord(
                    task_id=f"audit_{event.event_id}",
                    state=TaskState.SUCCEEDED,
                    timestamp=time.time(),
                    data={"audit_event": event.model_dump()}
                )
                await self.state_store.save_task_state(record)
            except Exception as e:
                self.logger.error(f"Error saving audit event: {e}")

        return event

    async def log_resource_access(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        workspace_id: Optional[str] = None,
        success: bool = True
    ) -> AuditEvent:
        """Log a resource access event."""
        return await self._log_audit_event(
            AuditEventType.RESOURCE_ACCESSED,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            workspace_id=workspace_id,
            success=success
        )

    async def log_resource_action(
        self,
        user_id: str,
        event_type: AuditEventType,
        resource_type: ResourceType,
        resource_id: str,
        resource_name: Optional[str] = None,
        workspace_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Log a resource action (create/update/delete)."""
        return await self._log_audit_event(
            event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            workspace_id=workspace_id,
            details=details
        )

    def get_audit_events(
        self,
        workspace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get audit events with optional filtering."""
        events = self._audit_events

        # Apply filters
        if workspace_id:
            events = [e for e in events if e.workspace_id == workspace_id]
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        # Sort by timestamp (newest first) and limit
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    # ========================================================================
    # User Management
    # ========================================================================

    def get_or_create_user(
        self,
        user_id: str,
        username: Optional[str] = None,
        email: Optional[str] = None
    ) -> User:
        """Get or create a user."""
        user = self._users.get(user_id)
        if not user:
            user = User(
                user_id=user_id,
                username=username or user_id,
                email=email
            )
            self._users[user_id] = user
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return self._users.get(user_id)

    # ========================================================================
    # Metrics
    # ========================================================================

    def get_metrics(self) -> Dict[str, Any]:
        """Get governance metrics."""
        return {
            "total_workspaces": len(self._workspaces),
            "active_workspaces": sum(1 for w in self._workspaces.values() if w.is_active),
            "total_users": len(self._users),
            "total_roles": len(self._roles),
            "total_members": len(self._members),
            "audit_events_logged": len(self._audit_events),
            "quotas_defined": len(self._quotas),
        }


# Singleton instance
_governance_engine: Optional[GovernanceEngine] = None


def get_governance_engine(
    state_store: Optional[StateStore] = None
) -> GovernanceEngine:
    """Get the singleton governance engine instance."""
    global _governance_engine
    if _governance_engine is None:
        _governance_engine = GovernanceEngine(state_store=state_store)
    return _governance_engine
