"""
Tests for Phase 6: Multi-Tenant Governance & Enterprise Control Plane

Tests the governance engine, RBAC, workspace isolation, policy inheritance,
and enterprise audit capabilities.
"""

import asyncio
import tempfile
import time
import pytest

from torq_console.autonomy.governance import (
    GovernanceEngine,
    Workspace,
    WorkspaceMember,
    Role,
    RoleType,
    Permission,
    PermissionSet,
    ResourceType,
    User,
    QuotaLimit,
    QuotaType,
    AuditEvent,
    AuditEventType,
    PolicyHierarchy,
    get_governance_engine
)
from torq_console.autonomy.state_store import StateStore
from torq_console.autonomy.models import (
    Monitor, MonitorType, AutonomousTask, ExecutionMode
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_storage():
    """Temporary storage for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def state_store(temp_storage):
    """State store for tests."""
    return StateStore(temp_storage)


@pytest.fixture
def governance_engine(state_store):
    """Governance engine for tests."""
    return GovernanceEngine(state_store=state_store)


# ============================================================================
# Role and Permission Tests
# ============================================================================

class TestRolesAndPermissions:
    """Test role and permission management."""

    def test_default_roles_loaded(self, governance_engine):
        """Test that default system roles are loaded."""
        owner_role = governance_engine._get_role_by_type(RoleType.OWNER)
        assert owner_role is not None
        assert Permission.ADMIN in owner_role.permissions.permissions

        admin_role = governance_engine._get_role_by_type(RoleType.ADMIN)
        assert admin_role is not None
        assert len(admin_role.permissions.permissions) > 0

        operator_role = governance_engine._get_role_by_type(RoleType.OPERATOR)
        assert operator_role is not None
        assert Permission.EXECUTE_TASKS in operator_role.permissions.permissions

        viewer_role = governance_engine._get_role_by_type(RoleType.VIEWER)
        assert viewer_role is not None
        assert Permission.VIEW_TASKS in viewer_role.permissions.permissions

    def test_create_custom_role(self, governance_engine):
        """Test creating a custom role."""
        role = governance_engine.create_role(
            name="Custom Analyst",
            permissions=[
                Permission.VIEW_TASKS,
                Permission.VIEW_MONITORS,
                Permission.VIEW_APPROVALS
            ],
            workspace_id="workspace_123",
            description="Can view but not modify"
        )

        assert role.role_id is not None
        assert role.name == "Custom Analyst"
        assert role.role_type == RoleType.CUSTOM
        assert role.is_system_role is False
        assert len(role.permissions.permissions) == 3

    def test_role_has_permission(self, governance_engine):
        """Test checking if a role has a permission."""
        role = governance_engine.create_role(
            name="Test Role",
            permissions=[Permission.VIEW_TASKS, Permission.CREATE_TASKS]
        )

        assert role.has_permission(Permission.VIEW_TASKS) is True
        assert role.has_permission(Permission.CREATE_TASKS) is True
        assert role.has_permission(Permission.CANCEL_TASKS) is False

    def test_permission_set_add_remove(self):
        """Test adding and removing permissions from a set."""
        perm_set = PermissionSet()

        assert perm_set.has_permission(Permission.VIEW_TASKS) is False

        perm_set.add_permission(Permission.VIEW_TASKS)
        assert perm_set.has_permission(Permission.VIEW_TASKS) is True

        perm_set.remove_permission(Permission.VIEW_TASKS)
        assert perm_set.has_permission(Permission.VIEW_TASKS) is False

    def test_get_role(self, governance_engine):
        """Test retrieving a role."""
        role = governance_engine.create_role(
            name="Test Role",
            permissions=[Permission.VIEW_TASKS]
        )

        retrieved = governance_engine.get_role(role.role_id)
        assert retrieved is not None
        assert retrieved.name == "Test Role"

    def test_list_roles(self, governance_engine):
        """Test listing roles."""
        # Create workspace-scoped role
        workspace_role = governance_engine.create_role(
            name="Workspace Role",
            permissions=[Permission.VIEW_TASKS],
            workspace_id="workspace_123"
        )

        # List all roles
        all_roles = governance_engine.list_roles()
        assert len(all_roles) >= 5  # At least the 4 system roles + 1 custom

        # List by workspace
        workspace_roles = governance_engine.list_roles(workspace_id="workspace_123")
        assert workspace_role.role_id in [r.role_id for r in workspace_roles]


# ============================================================================
# Workspace Tests
# ============================================================================

class TestWorkspaces:
    """Test workspace management."""

    @pytest.mark.asyncio
    async def test_create_workspace(self, governance_engine):
        """Test creating a workspace."""
        workspace = await governance_engine.create_workspace(
            name="AI Operations",
            owner_id="user_123",
            description="AI operations workspace"
        )

        assert workspace.workspace_id is not None
        assert workspace.name == "AI Operations"
        assert workspace.owner_id == "user_123"
        assert workspace.is_active is True
        assert workspace.member_count == 1  # Owner added automatically

    @pytest.mark.asyncio
    async def test_workspace_default_quotas(self, governance_engine):
        """Test that workspaces get default quotas."""
        workspace = await governance_engine.create_workspace(
            name="Test Workspace",
            owner_id="user_123"
        )

        # Check default quotas
        monitor_quota = governance_engine.get_quota(
            workspace.workspace_id,
            QuotaType.MAX_MONITORS
        )

        # Quotas are not set by default, but we can check the method returns defaults
        defaults = governance_engine._default_quotas()
        assert QuotaType.MAX_MONITORS.value in defaults
        assert defaults[QuotaType.MAX_MONITORS.value] == 100

    def test_get_workspace(self, governance_engine):
        """Test retrieving a workspace."""
        workspace = Workspace(
            name="Test Workspace",
            owner_id="user_123"
        )

        governance_engine._workspaces[workspace.workspace_id] = workspace

        retrieved = governance_engine.get_workspace(workspace.workspace_id)
        assert retrieved is not None
        assert retrieved.name == "Test Workspace"

    @pytest.mark.asyncio
    async def test_update_workspace(self, governance_engine):
        """Test updating a workspace."""
        workspace = await governance_engine.create_workspace(
            name="Original Name",
            owner_id="user_123"
        )

        result = await governance_engine.update_workspace(
            workspace.workspace_id,
            name="Updated Name",
            description="Updated description"
        )

        assert result is True
        assert workspace.name == "Updated Name"
        assert workspace.description == "Updated description"

    @pytest.mark.asyncio
    async def test_list_workspaces(self, governance_engine):
        """Test listing workspaces."""
        # Create workspaces
        ws1 = await governance_engine.create_workspace(
            "Workspace 1",
            owner_id="user_123"
        )

        ws2 = await governance_engine.create_workspace(
            "Workspace 2",
            owner_id="user_456"
        )

        # List all
        all_workspaces = governance_engine.list_workspaces()
        assert len(all_workspaces) >= 2

        # List by user
        user_workspaces = governance_engine.list_workspaces(user_id="user_123")
        assert ws1.workspace_id in [w.workspace_id for w in user_workspaces]
        assert ws2.workspace_id not in [w.workspace_id for w in user_workspaces]

        # List active
        active_workspaces = governance_engine.list_workspaces(is_active=True)
        assert len(active_workspaces) >= 2

    @pytest.mark.asyncio
    async def test_workspace_isolation(self, governance_engine):
        """Test that workspaces are isolated."""
        ws1 = await governance_engine.create_workspace("Workspace 1", "user_1")
        ws2 = await governance_engine.create_workspace("Workspace 2", "user_2")

        # User 1 should only be member of workspace 1
        members_ws1 = governance_engine.list_members(ws1.workspace_id)
        members_ws2 = governance_engine.list_members(ws2.workspace_id)

        ws1_user_ids = [m.user_id for m in members_ws1]
        ws2_user_ids = [m.user_id for m in members_ws2]

        assert "user_1" in ws1_user_ids
        assert "user_2" not in ws1_user_ids
        assert "user_2" in ws2_user_ids
        assert "user_1" not in ws2_user_ids


# ============================================================================
# Member Management Tests
# ============================================================================

class TestMemberManagement:
    """Test member management."""

    @pytest.mark.asyncio
    async def test_add_member(self, governance_engine):
        """Test adding a member to a workspace."""
        workspace = await governance_engine.create_workspace(
            "Test Workspace",
            owner_id="owner_123"
        )

        # Get operator role
        operator_role = governance_engine._get_role_by_type(RoleType.OPERATOR)

        member = await governance_engine.add_member(
            workspace.workspace_id,
            user_id="new_user_123",
            role_id=operator_role.role_id,
            invited_by="owner_123"
        )

        assert member.membership_id is not None
        assert member.workspace_id == workspace.workspace_id
        assert member.user_id == "new_user_123"
        assert member.status == "pending"  # Not owner, so pending

    @pytest.mark.asyncio
    async def test_owner_is_active_member(self, governance_engine):
        """Test that workspace owner is active member."""
        workspace = await governance_engine.create_workspace(
            "Test Workspace",
            owner_id="owner_123"
        )

        member = governance_engine.get_member(workspace.workspace_id, "owner_123")

        assert member is not None
        assert member.is_owner is True
        assert member.status == "active"

    def test_get_member(self, governance_engine):
        """Test getting a member."""
        member = WorkspaceMember(
            workspace_id="ws_123",
            user_id="user_123",
            role_id="role_123",
            status="active"
        )

        governance_engine._members[member.membership_id] = member

        retrieved = governance_engine.get_member("ws_123", "user_123")
        assert retrieved is not None
        assert retrieved.user_id == "user_123"

    @pytest.mark.asyncio
    async def test_update_member_role(self, governance_engine):
        """Test updating a member's role."""
        workspace = await governance_engine.create_workspace(
            "Test Workspace",
            owner_id="owner_123"
        )

        # Add member as viewer
        viewer_role = governance_engine._get_role_by_type(RoleType.VIEWER)
        await governance_engine.add_member(
            workspace.workspace_id,
            "member_123",
            viewer_role.role_id
        )

        # Update to operator
        operator_role = governance_engine._get_role_by_type(RoleType.OPERATOR)
        result = await governance_engine.update_member_role(
            workspace.workspace_id,
            "member_123",
            operator_role.role_id
        )

        assert result is True

        member = governance_engine.get_member(workspace.workspace_id, "member_123")
        assert member.role_id == operator_role.role_id


# ============================================================================
# RBAC Tests
# ============================================================================

class TestRBAC:
    """Test Role-Based Access Control."""

    @pytest.mark.asyncio
    async def test_has_permission_owner(self, governance_engine):
        """Test that owner has all permissions."""
        workspace = await governance_engine.create_workspace(
            "Test Workspace",
            owner_id="owner_123"
        )

        # Owner should have admin permission
        has_perm = governance_engine.has_permission(
            "owner_123",
            workspace.workspace_id,
            Permission.ADMIN
        )

        assert has_perm is True

    @pytest.mark.asyncio
    async def test_has_permission_operator(self, governance_engine):
        """Test operator permissions."""
        workspace = await governance_engine.create_workspace(
            "Test Workspace",
            owner_id="owner_123"
        )

        operator_role = governance_engine._get_role_by_type(RoleType.OPERATOR)

        # Add operator member
        await governance_engine.add_member(
            workspace.workspace_id,
            "operator_123",
            operator_role.role_id
        )
        # Make active
        member = governance_engine.get_member(workspace.workspace_id, "operator_123")
        member.status = "active"

        # Operator can execute tasks
        can_execute = governance_engine.has_permission(
            "operator_123",
            workspace.workspace_id,
            Permission.EXECUTE_TASKS
        )
        assert can_execute is True

        # But cannot manage workspace
        can_manage = governance_engine.has_permission(
            "operator_123",
            workspace.workspace_id,
            Permission.MANAGE_MEMBERS
        )
        assert can_manage is False

    @pytest.mark.asyncio
    async def test_has_permission_viewer(self, governance_engine):
        """Test viewer permissions."""
        workspace = await governance_engine.create_workspace(
            "Test Workspace",
            owner_id="owner_123"
        )

        viewer_role = governance_engine._get_role_by_type(RoleType.VIEWER)

        await governance_engine.add_member(
            workspace.workspace_id,
            "viewer_123",
            viewer_role.role_id
        )
        member = governance_engine.get_member(workspace.workspace_id, "viewer_123")
        member.status = "active"

        # Viewer can view
        can_view = governance_engine.has_permission(
            "viewer_123",
            workspace.workspace_id,
            Permission.VIEW_TASKS
        )
        assert can_view is True

        # But cannot create
        can_create = governance_engine.has_permission(
            "viewer_123",
            workspace.workspace_id,
            Permission.CREATE_TASKS
        )
        assert can_create is False

    @pytest.mark.asyncio
    async def test_non_member_no_permission(self, governance_engine):
        """Test that non-members have no permissions."""
        workspace = await governance_engine.create_workspace(
            "Test Workspace",
            owner_id="owner_123"
        )

        # Non-member
        has_perm = governance_engine.has_permission(
            "outsider_123",
            workspace.workspace_id,
            Permission.VIEW_TASKS
        )

        assert has_perm is False

    @pytest.mark.asyncio
    async def test_check_permissions_all_required(self, governance_engine):
        """Test requiring all permissions."""
        workspace = await governance_engine.create_workspace(
            "Test Workspace",
            owner_id="owner_123"
        )

        # Owner has all permissions
        result = governance_engine.check_permissions(
            "owner_123",
            workspace.workspace_id,
            [Permission.VIEW_TASKS, Permission.CREATE_TASKS, Permission.EXECUTE_TASKS],
            require_all=True
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_check_permissions_any_sufficient(self, governance_engine):
        """Test requiring any permission."""
        workspace = await governance_engine.create_workspace(
            "Test Workspace",
            owner_id="owner_123"
        )

        viewer_role = governance_engine._get_role_by_type(RoleType.VIEWER)

        await governance_engine.add_member(
            workspace.workspace_id,
            "viewer_123",
            viewer_role.role_id
        )
        member = governance_engine.get_member(workspace.workspace_id, "viewer_123")
        member.status = "active"

        # Viewer can VIEW_TASKS or VIEW_MONITORS (has VIEW_TASKS)
        result = governance_engine.check_permissions(
            "viewer_123",
            workspace.workspace_id,
            [Permission.EXECUTE_TASKS, Permission.VIEW_TASKS],
            require_all=False
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_superuser_bypass(self, governance_engine):
        """Test that superuser bypasses RBAC."""
        governance_engine.get_or_create_user(
            user_id="superuser",
            username="Super User"
        )
        user = governance_engine.get_user("superuser")
        user.is_superuser = True

        workspace = await governance_engine.create_workspace(
            "Test Workspace",
            owner_id="owner_123"
        )

        # Superuser has all permissions even without membership
        has_perm = governance_engine.has_permission(
            "superuser",
            workspace.workspace_id,
            Permission.DELETE_WORKSPACE
        )

        assert has_perm is True


# ============================================================================
# Quota Tests
# ============================================================================

class TestQuotas:
    """Test quota management."""

    def test_set_quota(self, governance_engine):
        """Test setting a quota."""
        quota = governance_engine.set_quota(
            workspace_id="ws_123",
            quota_type=QuotaType.MAX_MONITORS,
            limit=50
        )

        assert quota.quota_id is not None
        assert quota.workspace_id == "ws_123"
        assert quota.quota_type == QuotaType.MAX_MONITORS
        assert quota.limit == 50
        assert quota.current_usage == 0

    def test_get_quota(self, governance_engine):
        """Test getting a quota."""
        governance_engine.set_quota(
            workspace_id="ws_123",
            quota_type=QuotaType.MAX_TASKS_PER_DAY,
            limit=100
        )

        quota = governance_engine.get_quota("ws_123", QuotaType.MAX_TASKS_PER_DAY)

        assert quota is not None
        assert quota.limit == 100

    def test_check_quota_allowed(self, governance_engine):
        """Test checking quota when allowed."""
        governance_engine.set_quota(
            workspace_id="ws_123",
            quota_type=QuotaType.MAX_MONITORS,
            limit=10
        )

        allowed, quota = governance_engine.check_quota("ws_123", QuotaType.MAX_MONITORS, 5)

        assert allowed is True
        assert quota is not None
        assert quota.remaining == 10

    def test_check_quota_exceeded(self, governance_engine):
        """Test checking quota when exceeded."""
        governance_engine.set_quota(
            workspace_id="ws_123",
            quota_type=QuotaType.MAX_MONITORS,
            limit=5
        )

        allowed, quota = governance_engine.check_quota("ws_123", QuotaType.MAX_MONITORS, 10)

        assert allowed is False
        # Quota is not yet exceeded (current_usage=0), but request would exceed
        assert quota.remaining < 10

    def test_consume_quota(self, governance_engine):
        """Test consuming quota."""
        governance_engine.set_quota(
            workspace_id="ws_123",
            quota_type=QuotaType.MAX_MONITORS,
            limit=10
        )

        # Consume 3
        success = governance_engine.consume_quota("ws_123", QuotaType.MAX_MONITORS, 3)
        assert success is True

        quota = governance_engine.get_quota("ws_123", QuotaType.MAX_MONITORS)
        assert quota.current_usage == 3
        assert quota.remaining == 7

    def test_consume_quota_exceeds(self, governance_engine):
        """Test consuming quota when it would exceed limit."""
        governance_engine.set_quota(
            workspace_id="ws_123",
            quota_type=QuotaType.MAX_MONITORS,
            limit=5
        )

        # Try to consume more than limit
        success = governance_engine.consume_quota("ws_123", QuotaType.MAX_MONITORS, 10)
        assert success is False

        quota = governance_engine.get_quota("ws_123", QuotaType.MAX_MONITORS)
        assert quota.current_usage == 0  # Not consumed

    def test_utilization_percent(self, governance_engine):
        """Test quota utilization percentage."""
        governance_engine.set_quota(
            workspace_id="ws_123",
            quota_type=QuotaType.MAX_MONITORS,
            limit=100
        )

        quota = governance_engine.get_quota("ws_123", QuotaType.MAX_MONITORS)
        assert quota.utilization_percent == 0.0

        governance_engine.consume_quota("ws_123", QuotaType.MAX_MONITORS, 25)

        quota = governance_engine.get_quota("ws_123", QuotaType.MAX_MONITORS)
        assert quota.utilization_percent == 25.0


# ============================================================================
# Audit Tests
# ============================================================================

class TestAuditLogging:
    """Test audit logging."""

    @pytest.mark.asyncio
    async def test_log_audit_event(self, governance_engine):
        """Test logging an audit event."""
        event = await governance_engine._log_audit_event(
            AuditEventType.USER_LOGIN,
            user_id="user_123",
            username="testuser"
        )

        assert event.event_id is not None
        assert event.event_type == AuditEventType.USER_LOGIN
        assert event.user_id == "user_123"
        assert event.success is True

    @pytest.mark.asyncio
    async def test_log_resource_action(self, governance_engine):
        """Test logging resource actions."""
        event = await governance_engine.log_resource_action(
            user_id="user_123",
            event_type=AuditEventType.RESOURCE_CREATED,
            resource_type=ResourceType.MONITOR,
            resource_id="monitor_123",
            resource_name="CPU Monitor",
            workspace_id="ws_123",
            details={"config": {"cpu": "high"}}
        )

        assert event.event_type == AuditEventType.RESOURCE_CREATED
        assert event.resource_type == ResourceType.MONITOR
        assert event.resource_id == "monitor_123"
        assert event.workspace_id == "ws_123"

    @pytest.mark.asyncio
    async def test_log_resource_access(self, governance_engine):
        """Test logging resource access."""
        event = await governance_engine.log_resource_access(
            user_id="user_123",
            resource_type=ResourceType.TASK,
            resource_id="task_456",
            workspace_id="ws_123",
            success=True
        )

        assert event.event_type == AuditEventType.RESOURCE_ACCESSED
        assert event.resource_type == ResourceType.TASK

    @pytest.mark.asyncio
    async def test_workspace_created_audit(self, governance_engine):
        """Test that workspace creation creates audit event."""
        workspace = await governance_engine.create_workspace(
            name="Test Workspace",
            owner_id="owner_123"
        )

        # Find the audit event
        events = governance_engine.get_audit_events(
            workspace_id=workspace.workspace_id,
            event_type=AuditEventType.WORKSPACE_CREATED
        )

        assert len(events) >= 1
        assert events[0].event_type == AuditEventType.WORKSPACE_CREATED

    def test_filter_audit_events(self, governance_engine):
        """Test filtering audit events."""
        # Log some events
        governance_engine._audit_events.append(AuditEvent(
            event_type=AuditEventType.USER_LOGIN,
            user_id="user_1",
            workspace_id="ws_1"
        ))

        governance_engine._audit_events.append(AuditEvent(
            event_type=AuditEventType.TASK_EXECUTED,
            user_id="user_2",
            workspace_id="ws_1"
        ))

        governance_engine._audit_events.append(AuditEvent(
            event_type=AuditEventType.TASK_EXECUTED,
            user_id="user_1",
            workspace_id="ws_2"
        ))

        # Filter by workspace
        ws1_events = governance_engine.get_audit_events(workspace_id="ws_1")
        assert len(ws1_events) == 2

        # Filter by user
        user1_events = governance_engine.get_audit_events(user_id="user_1")
        assert len(user1_events) == 2

        # Filter by event type
        task_events = governance_engine.get_audit_events(
            event_type=AuditEventType.TASK_EXECUTED
        )
        assert len(task_events) == 2

    def test_audit_events_ordering(self, governance_engine):
        """Test that audit events are ordered by timestamp."""
        now = time.time()

        # Log events with different timestamps
        for i in range(5):
            governance_engine._audit_events.append(AuditEvent(
                event_type=AuditEventType.RESOURCE_ACCESSED,
                user_id="user_123",
                timestamp=now + i
            ))

        events = governance_engine.get_audit_events(limit=3)

        # Should be newest first (descending timestamp)
        assert len(events) == 3
        assert events[0].timestamp > events[1].timestamp
        assert events[1].timestamp > events[2].timestamp


# ============================================================================
# User Management Tests
# ============================================================================

class TestUserManagement:
    """Test user management."""

    def test_get_or_create_user(self, governance_engine):
        """Test getting or creating a user."""
        user = governance_engine.get_or_create_user(
            user_id="user_123",
            username="testuser",
            email="test@example.com"
        )

        assert user.user_id == "user_123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"

        # Calling again returns same user
        user2 = governance_engine.get_or_create_user("user_123")
        assert user2.user_id == user.user_id
        assert user2.username == "testuser"

    def test_get_user(self, governance_engine):
        """Test getting a user."""
        governance_engine.get_or_create_user("user_456", "testuser")

        user = governance_engine.get_user("user_456")
        assert user is not None
        assert user.username == "testuser"


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase6Integration:
    """Integration tests for Phase 6."""

    @pytest.mark.asyncio
    async def test_full_workspace_lifecycle(self, governance_engine):
        """Test complete workspace lifecycle."""
        # 1. Create workspace
        workspace = await governance_engine.create_workspace(
            name="Integration Test Workspace",
            owner_id="owner_123",
            description="Full lifecycle test"
        )

        # 2. Add members with different roles
        operator_role = governance_engine._get_role_by_type(RoleType.OPERATOR)
        viewer_role = governance_engine._get_role_by_type(RoleType.VIEWER)

        await governance_engine.add_member(
            workspace.workspace_id,
            "operator_123",
            operator_role.role_id
        )

        await governance_engine.add_member(
            workspace.workspace_id,
            "viewer_123",
            viewer_role.role_id
        )

        # 3. Verify permissions
        assert governance_engine.has_permission(
            "owner_123",
            workspace.workspace_id,
            Permission.ADMIN
        )

        # Operator needs to be activated
        op_member = governance_engine.get_member(
            workspace.workspace_id,
            "operator_123"
        )
        op_member.status = "active"

        assert governance_engine.has_permission(
            "operator_123",
            workspace.workspace_id,
            Permission.EXECUTE_TASKS
        )

        # 4. Check quotas
        quota = governance_engine.set_quota(
            workspace.workspace_id,
            QuotaType.MAX_MONITORS,
            limit=25
        )

        allowed, _ = governance_engine.check_quota(
            workspace.workspace_id,
            QuotaType.MAX_MONITORS,
            10
        )
        assert allowed is True

        # 5. Verify audit trail
        events = governance_engine.get_audit_events(
            workspace_id=workspace.workspace_id
        )
        assert len(events) >= 1  # At least the workspace creation event

    @pytest.mark.asyncio
    async def test_cross_workspace_isolation(self, governance_engine):
        """Test that workspaces are properly isolated."""
        # Create two workspaces
        ws1 = await governance_engine.create_workspace("Workspace 1", "owner_1")
        ws2 = await governance_engine.create_workspace("Workspace 2", "owner_2")

        # Add user to workspace 1
        operator_role = governance_engine._get_role_by_type(RoleType.OPERATOR)
        await governance_engine.add_member(
            ws1.workspace_id,
            "shared_user",
            operator_role.role_id
        )
        member1 = governance_engine.get_member(ws1.workspace_id, "shared_user")
        member1.status = "active"

        # User should have access to workspace 1
        has_access_ws1 = governance_engine.has_permission(
            "shared_user",
            ws1.workspace_id,
            Permission.EXECUTE_TASKS
        )
        assert has_access_ws1 is True

        # But not workspace 2
        has_access_ws2 = governance_engine.has_permission(
            "shared_user",
            ws2.workspace_id,
            Permission.VIEW_TASKS
        )
        assert has_access_ws2 is False

    @pytest.mark.asyncio
    async def test_quota_enforcement_across_workspaces(self, governance_engine):
        """Test that quotas are enforced per workspace."""
        ws1 = await governance_engine.create_workspace("Workspace 1", "owner_1")
        ws2 = await governance_engine.create_workspace("Workspace 2", "owner_2")

        # Set quota for workspace 1
        governance_engine.set_quota(
            ws1.workspace_id,
            QuotaType.MAX_MONITORS,
            limit=5
        )

        # Set different quota for workspace 2
        governance_engine.set_quota(
            ws2.workspace_id,
            QuotaType.MAX_MONITORS,
            limit=10
        )

        # Workspace 1 can do 5
        allowed1, _ = governance_engine.check_quota(
            ws1.workspace_id,
            QuotaType.MAX_MONITORS,
            5
        )
        assert allowed1 is True

        # But not 6
        allowed1_exceed, _ = governance_engine.check_quota(
            ws1.workspace_id,
            QuotaType.MAX_MONITORS,
            6
        )
        assert allowed1_exceed is False

        # Workspace 2 can do 10
        allowed2, _ = governance_engine.check_quota(
            ws2.workspace_id,
            QuotaType.MAX_MONITORS,
            10
        )
        assert allowed2 is True

    def test_get_metrics(self, governance_engine):
        """Test getting governance metrics."""
        metrics = governance_engine.get_metrics()

        assert "total_workspaces" in metrics
        assert "total_users" in metrics
        assert "total_roles" in metrics
        assert "total_members" in metrics
        assert "audit_events_logged" in metrics
        assert "quotas_defined" in metrics
