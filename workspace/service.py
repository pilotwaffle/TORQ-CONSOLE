"""
Shared Cognitive Workspace - Service Layer

Business logic for workspace and entry management.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .models import (
    WorkspaceCreate,
    WorkspaceEntryCreate,
    WorkspaceEntryUpdate,
    WorkspaceResponse,
    WorkspaceEntryResponse,
    WorkspaceEntriesResponse,
    WorkspaceSummaryResponse,
    WorkspaceEntryType,
    WorkspaceEntryStatus,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Database Configuration
# ============================================================================

# TODO: Move to config
DATABASE_URL = "postgresql://postgres.torq_console:@localhost:5432/torq_console"

engine = create_async_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ============================================================================
# Workspace Service
# ============================================================================

class WorkspaceService:
    """
    Service for managing workspaces and working memory entries.
    """

    async def create_workspace(self, payload: WorkspaceCreate) -> WorkspaceResponse:
        """
        Create a new workspace.

        Args:
            payload: Workspace creation request

        Returns:
            Created workspace response
        """
        async with AsyncSessionLocal() as session:
            # Use the get_or_create_workspace function for idempotency
            result = await session.execute(
                text("SELECT get_or_create_workspace(:scope_type, :scope_id, :title, :created_by) AS workspace_id"),
                {
                    "scope_type": payload.scope_type,
                    "scope_id": payload.scope_id,
                    "title": payload.title,
                    "created_by": payload.created_by,
                }
            )
            workspace_id = (result.scalar_one(),)

            await session.commit()

            # Fetch and return the workspace
            return await self._get_workspace_by_id(session, workspace_id)

    async def get_workspace(self, workspace_id: str) -> Optional[WorkspaceResponse]:
        """
        Get a workspace by ID.

        Args:
            workspace_id: Workspace UUID

        Returns:
            Workspace response or None
        """
        async with AsyncSessionLocal() as session:
            return await self._get_workspace_by_id(session, workspace_id)

    async def _get_workspace_by_id(
        self, session: AsyncSession, workspace_id: str
    ) -> Optional[WorkspaceResponse]:
        """Internal method to fetch workspace with entry count."""
        result = await session.execute(
            text("""
                SELECT
                    w.workspace_id,
                    w.scope_type,
                    w.scope_id,
                    w.title,
                    w.description,
                    w.created_by,
                    w.created_at,
                    w.updated_at,
                    COALESCE(e.count, 0) as entry_count
                FROM workspaces w
                LEFT JOIN (
                    SELECT workspace_id, COUNT(*) as count
                    FROM working_memory_entries
                    WHERE deleted_at IS NULL
                    GROUP BY workspace_id
                ) e ON e.workspace_id = w.workspace_id
                WHERE w.workspace_id = :workspace_id
            """),
            {"workspace_id": workspace_id}
        )

        row = result.fetchone()
        if not row:
            return None

        return WorkspaceResponse(
            workspace_id=row[0],
            scope_type=row[1],
            scope_id=row[2],
            title=row[3],
            description=row[4],
            created_by=row[5],
            created_at=row[6],
            updated_at=row[7],
            entry_count=row[8]
        )

    async def get_workspace_by_scope(
        self, scope_type: str, scope_id: str
    ) -> Optional[WorkspaceResponse]:
        """
        Get or create a workspace by scope.

        Args:
            scope_type: Type of scope
            scope_id: Scope identifier

        Returns:
            Workspace response
        """
        async with AsyncSessionLocal() as session:
            # Try to get existing
            result = await session.execute(
                text("""
                    SELECT workspace_id
                    FROM workspaces
                    WHERE scope_type = :scope_type AND scope_id = :scope_id
                """),
                {"scope_type": scope_type, "scope_id": scope_id}
            )

            existing_id = result.scalar_one()

            if existing_id:
                return await self._get_workspace_by_id(session, existing_id)

            # Create new workspace
            result = await session.execute(
                text("SELECT get_or_create_workspace(:scope_type, :scope_id, :title, :created_by) AS workspace_id"),
                {
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                    "title": f"Workspace for {scope_type}:{scope_id}",
                    "created_by": "system"
                }
            )
            workspace_id = result.scalar_one()

            await session.commit()

            return await self._get_workspace_by_id(session, workspace_id)

    async def add_entry(
        self,
        workspace_id: str,
        entry: WorkspaceEntryCreate
    ) -> WorkspaceEntryResponse:
        """
        Add an entry to a workspace.

        Args:
            workspace_id: Workspace UUID
            entry: Entry to add

        Returns:
            Created entry response
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    INSERT INTO working_memory_entries
                    (workspace_id, entry_type, content, source_agent, confidence)
                    VALUES (:workspace_id, :entry_type, :content::jsonb, :source_agent, :confidence)
                    RETURNING
                        memory_id, workspace_id, entry_type, content, source_agent, confidence, status, created_at, updated_at
                """),
                {
                    "workspace_id": workspace_id,
                    "entry_type": entry.entry_type.value,
                    "content": entry.content,
                    "source_agent": entry.source_agent,
                    "confidence": entry.confidence,
                }
            )

            row = result.fetchone()
            await session.commit()

            return WorkspaceEntryResponse(
                memory_id=row[0],
                workspace_id=row[1],
                entry_type=row[2],
                content=row[3],
                source_agent=row[4],
                confidence=row[5],
                status=row[6],
                created_at=row[7],
                updated_at=row[8],
            )

    async def update_entry(
        self,
        workspace_id: str,
        memory_id: str,
        update: WorkspaceEntryUpdate
    ) -> Optional[WorkspaceEntryResponse]:
        """
        Update a workspace entry.

        Args:
            workspace_id: Workspace UUID
            memory_id: Entry UUID
            update: Update payload

        Returns:
            Updated entry or None
        """
        async with AsyncSessionLocal() as session:
            # Build update clauses dynamically
            updates = []
            params = {"workspace_id": workspace_id, "memory_id": memory_id}

            if update.content is not None:
                updates.append("content = :content::jsonb")
                params["content"] = update.content

            if update.confidence is not None:
                updates.append("confidence = :confidence")
                params["confidence"] = update.confidence

            if update.status is not None:
                updates.append("status = :status")
                params["status"] = update.status.value

            if not updates:
                return await self.get_entry(workspace_id, memory_id)

            updates.append("updated_at = NOW()")

            query = f"""
                UPDATE working_memory_entries
                SET {', '.join(updates)}
                WHERE workspace_id = :workspace_id AND memory_id = :memory_id
                RETURNING memory_id, workspace_id, entry_type, content, source_agent, confidence, status, created_at, updated_at
            """

            result = await session.execute(text(query), params)
            row = result.fetchone()

            if not row:
                return None

            await session.commit()

            return WorkspaceEntryResponse(
                memory_id=row[0],
                workspace_id=row[1],
                entry_type=row[2],
                content=row[3],
                source_agent=row[4],
                confidence=row[5],
                status=row[6],
                created_at=row[7],
                updated_at=row[8],
            )

    async def resolve_question(
        self,
        workspace_id: str,
        memory_id: str,
        resolution: Dict[str, Any]
    ) -> Optional[WorkspaceEntryResponse]:
        """
        Resolve a question entry with an answer.

        Args:
            workspace_id: Workspace UUID
            memory_id: Question entry UUID
            resolution: Resolution data

        Returns:
            Updated entry or None
        """
        return await self.update_entry(
            workspace_id,
            memory_id,
            WorkspaceEntryUpdate(
                content={
                    "question": (await self.get_entry(workspace_id, memory_id)).content,
                    "resolution": resolution
                },
                status=WorkspaceEntryStatus.RESOLVED
            )
        )

    async def get_entry(
        self,
        workspace_id: str,
        memory_id: str
    ) -> Optional[WorkspaceEntryResponse]:
        """
        Get a specific entry.

        Args:
            workspace_id: Workspace UUID
            memory_id: Entry UUID

        Returns:
            Entry response or None
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT memory_id, workspace_id, entry_type, content, source_agent, confidence, status, created_at, updated_at
                    FROM working_memory_entries
                    WHERE workspace_id = :workspace_id AND memory_id = :memory_id AND deleted_at IS NULL
                """),
                {"workspace_id": workspace_id, "memory_id": memory_id}
            )

            row = result.fetchone()
            if not row:
                return None

            return WorkspaceEntryResponse(
                memory_id=row[0],
                workspace_id=row[1],
                entry_type=row[2],
                content=row[3],
                source_agent=row[4],
                confidence=row[5],
                status=row[6],
                created_at=row[7],
                updated_at=row[8],
            )

    async def list_entries(
        self,
        workspace_id: str,
        entry_type: Optional[WorkspaceEntryType] = None,
        status: Optional[WorkspaceEntryStatus] = None
    ) -> WorkspaceEntriesResponse:
        """
        List all entries in a workspace, grouped by type.

        Args:
            workspace_id: Workspace UUID
            entry_type: Optional filter by entry type
            status: Optional filter by status

        Returns:
            Grouped entries response
        """
        async with AsyncSessionLocal() as session:
            conditions = ["workspace_id = :workspace_id", "deleted_at IS NULL"]
            params = {"workspace_id": workspace_id}

            if entry_type:
                conditions.append("entry_type = :entry_type")
                params["entry_type"] = entry_type.value

            if status:
                conditions.append("status = :status")
                params["status"] = status.value

            where_clause = " AND ".join(conditions)

            result = await session.execute(
                text(f"""
                    SELECT memory_id, workspace_id, entry_type, content, source_agent, confidence, status, created_at, updated_at
                    FROM working_memory_entries
                    WHERE {where_clause}
                    ORDER BY created_at ASC
                """),
                params
            )

            rows = result.fetchall()

            # Group by entry type
            entries: Dict[str, List[WorkspaceEntryResponse]] = {
                "fact": [],
                "hypothesis": [],
                "question": [],
                "decision": [],
                "artifact": [],
                "note": [],
            }

            for row in rows:
                entry = WorkspaceEntryResponse(
                    memory_id=row[0],
                    workspace_id=row[1],
                    entry_type=row[2],
                    content=row[3],
                    source_agent=row[4],
                    confidence=row[5],
                    status=row[6],
                    created_at=row[7],
                    updated_at=row[8],
                )
                entries[entry.entry_type].append(entry)

            return WorkspaceEntriesResponse(
                workspace_id=workspace_id,
                facts=entries["fact"],
                hypotheses=entries["hypothesis"],
                questions=entries["question"],
                decisions=entries["decision"],
                artifacts=entries["artifact"],
                notes=entries["note"],
                total=len(rows)
            )

    async def delete_entry(
        self,
        workspace_id: str,
        memory_id: str
    ) -> bool:
        """
        Soft delete an entry.

        Args:
            workspace_id: Workspace UUID
            memory_id: Entry UUID

        Returns:
            True if deleted, False otherwise
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    UPDATE working_memory_entries
                    SET deleted_at = NOW()
                    WHERE workspace_id = :workspace_id AND memory_id = :memory_id
                """),
                {"workspace_id": workspace_id, "memory_id": memory_id}
            )

            await session.commit()
            return result.rowcount > 0


# ============================================================================
# Singleton instance
# ============================================================================

workspace_service = WorkspaceService()
