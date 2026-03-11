from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import (
    WorkspaceCreate,
    WorkspaceEntryCreate,
    WorkspaceEntryRead,
    WorkspaceEntryStatus,
    WorkspaceEntryUpdate,
    WorkspaceGroupedEntries,
    WorkspaceRead,
    WorkspaceSummaryResponse,
)


class WorkspaceService:
    def __init__(self, supabase_client: Any, llm_client: Optional[Any] = None):
        self.supabase = supabase_client
        self.llm_client = llm_client

    async def create_workspace(self, payload: WorkspaceCreate) -> WorkspaceRead:
        result = self.supabase.table("workspaces").insert(payload.model_dump()).execute()
        return WorkspaceRead.model_validate(result.data[0])

    async def get_workspace(self, workspace_id: str) -> Optional[WorkspaceRead]:
        result = self.supabase.table("workspaces").select("*").eq("workspace_id", workspace_id).limit(1).execute()
        if not result.data:
            return None
        return WorkspaceRead.model_validate(result.data[0])

    async def get_workspace_by_scope(self, scope_type: str, scope_id: str, tenant_id: str = "default") -> Optional[WorkspaceRead]:
        """
        Get a workspace by scope. Returns None if not found.

        Unlike get_or_create_workspace, this will NOT create a new workspace.
        """
        result = (
            self.supabase.table("workspaces")
            .select("*")
            .eq("tenant_id", tenant_id)
            .eq("scope_type", scope_type)
            .eq("scope_id", scope_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        return WorkspaceRead.model_validate(result.data[0])

    async def get_or_create_workspace(
        self,
        scope_type: str,
        scope_id: str,
        tenant_id: str = "default",
        title: Optional[str] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> WorkspaceRead:
        existing = (
            self.supabase.table("workspaces")
            .select("*")
            .eq("tenant_id", tenant_id)
            .eq("scope_type", scope_type)
            .eq("scope_id", scope_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            return WorkspaceRead.model_validate(existing.data[0])
        # Create new workspace with provided metadata
        create_payload = WorkspaceCreate(
            scope_type=scope_type,
            scope_id=scope_id,
            tenant_id=tenant_id,
            title=title or f"Workspace for {scope_type}:{scope_id}",
            description=description,
            created_by=created_by
        )
        return await self.create_workspace(create_payload)

    async def add_entry(self, workspace_id: str, entry: WorkspaceEntryCreate, tenant_id: str = "default") -> WorkspaceEntryRead:
        payload = entry.model_dump()
        payload["workspace_id"] = workspace_id
        payload["tenant_id"] = tenant_id
        result = self.supabase.table("working_memory_entries").insert(payload).execute()
        return WorkspaceEntryRead.model_validate(result.data[0])

    async def get_entry(self, workspace_id: str, memory_id: str) -> Optional[WorkspaceEntryRead]:
        result = (
            self.supabase.table("working_memory_entries")
            .select("*")
            .eq("workspace_id", workspace_id)
            .eq("memory_id", memory_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        return WorkspaceEntryRead.model_validate(result.data[0])

    async def update_entry(self, workspace_id: str, memory_id: str, update: WorkspaceEntryUpdate) -> Optional[WorkspaceEntryRead]:
        payload = update.model_dump(exclude_none=True)
        result = (
            self.supabase.table("working_memory_entries")
            .update(payload)
            .eq("workspace_id", workspace_id)
            .eq("memory_id", memory_id)
            .execute()
        )
        if not result.data:
            return None
        return WorkspaceEntryRead.model_validate(result.data[0])

    async def resolve_entry(self, workspace_id: str, memory_id: str) -> Optional[WorkspaceEntryRead]:
        return await self.update_entry(workspace_id, memory_id, WorkspaceEntryUpdate(status=WorkspaceEntryStatus.RESOLVED))

    async def list_entries(self, workspace_id: str) -> List[WorkspaceEntryRead]:
        result = self.supabase.table("working_memory_entries").select("*").eq("workspace_id", workspace_id).order("created_at").execute()
        return [WorkspaceEntryRead.model_validate(row) for row in result.data]

    async def list_entries_grouped(self, workspace_id: str) -> WorkspaceGroupedEntries:
        entries = await self.list_entries(workspace_id)
        grouped = defaultdict(list)
        for entry in entries:
            grouped[entry.entry_type.value].append(entry)
        return WorkspaceGroupedEntries(
            workspace_id=workspace_id,
            facts=grouped["fact"],
            hypotheses=grouped["hypothesis"],
            questions=grouped["question"],
            decisions=grouped["decision"],
            artifacts=grouped["artifact"],
            notes=grouped["note"],
        )

    async def summarize_workspace(self, workspace_id: str, model: Optional[str] = None) -> WorkspaceSummaryResponse:
        grouped = await self.list_entries_grouped(workspace_id)
        summary = self._fallback_summary(grouped)
        if self.llm_client is not None:
            try:
                response = await self.llm_client.messages.create(
                    model=model or "claude-sonnet-4-6",
                    max_tokens=600,
                    temperature=0.2,
                    system="Summarize collaborative workspace state clearly and concisely.",
                    messages=[{"role": "user", "content": self._build_prompt(grouped)}],
                )
                text_blocks = [b.text for b in response.content if getattr(b, "type", None) == "text"]
                summary = "".join(text_blocks).strip() or summary
            except Exception:
                pass
        return WorkspaceSummaryResponse(
            workspace_id=workspace_id,
            summary=summary,
            facts_count=len(grouped.facts),
            hypotheses_count=len(grouped.hypotheses),
            questions_count=len(grouped.questions),
            decisions_count=len(grouped.decisions),
            generated_at=datetime.now(timezone.utc),
        )

    def _build_prompt(self, grouped: WorkspaceGroupedEntries) -> str:
        return f"""Summarize this shared cognitive workspace.

Facts: {[e.content for e in grouped.facts]}
Hypotheses: {[e.content for e in grouped.hypotheses]}
Questions: {[e.content for e in grouped.questions]}
Decisions: {[e.content for e in grouped.decisions]}
Artifacts: {[e.content for e in grouped.artifacts]}

Return:
1. Current understanding
2. Key unresolved questions
3. Most important decisions
"""

    def _fallback_summary(self, grouped: WorkspaceGroupedEntries) -> str:
        lines = []
        if grouped.facts:
            lines.append(f"Facts: {len(grouped.facts)} recorded.")
        if grouped.hypotheses:
            lines.append(f"Hypotheses: {len(grouped.hypotheses)} active.")
        unresolved = [q for q in grouped.questions if q.status != WorkspaceEntryStatus.RESOLVED]
        if unresolved:
            lines.append(f"Questions: {len(unresolved)} unresolved.")
        if grouped.decisions:
            lines.append(f"Decisions: {len(grouped.decisions)} tracked.")
        return " ".join(lines) or "Workspace is currently empty."
