from __future__ import annotations

from typing import Any, Dict, List, Optional

from torq_console.synthesis.detectors import detect_contradiction_candidates, detect_unresolved_questions, suggest_next_actions
from torq_console.synthesis.models import GenerateSynthesisRequest, GenerateSynthesisResponse, SynthesisType, WorkspaceSynthesisRead
from torq_console.synthesis.prompts import build_synthesis_prompt
from torq_console.workspace.service import WorkspaceService


class SynthesisService:
    def __init__(self, supabase_client: Any, workspace_service: WorkspaceService, llm_client: Optional[Any] = None):
        self.supabase = supabase_client
        self.workspace_service = workspace_service
        self.llm_client = llm_client

    async def list_syntheses(self, workspace_id: str) -> List[WorkspaceSynthesisRead]:
        result = (
            self.supabase.table("workspace_syntheses")
            .select("*")
            .eq("workspace_id", workspace_id)
            .order("created_at", desc=True)
            .execute()
        )
        return [WorkspaceSynthesisRead.model_validate(row) for row in result.data]

    async def get_latest_synthesis(self, workspace_id: str, synthesis_type: SynthesisType) -> Optional[WorkspaceSynthesisRead]:
        result = (
            self.supabase.table("workspace_syntheses")
            .select("*")
            .eq("workspace_id", workspace_id)
            .eq("synthesis_type", synthesis_type.value)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        return WorkspaceSynthesisRead.model_validate(result.data[0])

    async def generate_syntheses(self, workspace_id: str, request: GenerateSynthesisRequest) -> GenerateSynthesisResponse:
        grouped = await self.workspace_service.list_entries_grouped(workspace_id)
        grouped_dict = {
            "facts": [e.model_dump() for e in grouped.facts],
            "hypotheses": [e.model_dump() for e in grouped.hypotheses],
            "questions": [e.model_dump() for e in grouped.questions],
            "decisions": [e.model_dump() for e in grouped.decisions],
            "artifacts": [e.model_dump() for e in grouped.artifacts],
            "notes": [e.model_dump() for e in grouped.notes],
        }

        detector_output = {
            "unresolved_questions": detect_unresolved_questions(grouped_dict),
            "contradictions": detect_contradiction_candidates(grouped_dict),
            "next_actions": suggest_next_actions(grouped_dict),
        }

        results = []
        for synthesis_type in request.types:
            if not request.force_regenerate:
                existing = await self.get_latest_synthesis(workspace_id, synthesis_type)
                if existing:
                    results.append(existing)
                    continue

            content = await self._generate_content(synthesis_type, grouped_dict, detector_output, request.model)
            version = await self._next_version(workspace_id, synthesis_type)
            created = await self._persist_synthesis(
                workspace_id=workspace_id,
                synthesis_type=synthesis_type,
                content=content,
                source_model=request.model or "heuristic-or-default",
                generated_by="reasoning_synthesis_engine",
                version=version,
            )
            results.append(created)

        return GenerateSynthesisResponse(workspace_id=workspace_id, results=results)

    async def _generate_content(self, synthesis_type: SynthesisType, grouped_entries: Dict[str, Any], detector_output: Dict[str, Any], model: Optional[str]) -> Dict[str, Any]:
        if self.llm_client is None:
            return self._fallback_content(synthesis_type, grouped_entries, detector_output)

        prompt = build_synthesis_prompt(synthesis_type.value, grouped_entries, detector_output)
        try:
            response = await self.llm_client.messages.create(
                model=model or "claude-sonnet-4-6",
                max_tokens=900,
                temperature=0.2,
                system="You synthesize reasoning artifacts into grounded strategic outputs.",
                messages=[{"role": "user", "content": prompt}],
            )
            text_blocks = [b.text for b in response.content if getattr(b, "type", None) == "text"]
            text = "".join(text_blocks).strip()
            return {"text": text}
        except Exception:
            return self._fallback_content(synthesis_type, grouped_entries, detector_output)

    def _fallback_content(self, synthesis_type: SynthesisType, grouped_entries: Dict[str, Any], detector_output: Dict[str, Any]) -> Dict[str, Any]:
        if synthesis_type == SynthesisType.SUMMARY:
            return {"summary": f"Workspace contains {len(grouped_entries['facts'])} facts, {len(grouped_entries['hypotheses'])} hypotheses, {len(grouped_entries['questions'])} questions, and {len(grouped_entries['decisions'])} decisions."}
        if synthesis_type == SynthesisType.CONTRADICTIONS:
            return {"contradictions": detector_output["contradictions"]}
        if synthesis_type == SynthesisType.NEXT_ACTIONS:
            return {"next_actions": detector_output["next_actions"]}
        if synthesis_type == SynthesisType.INSIGHTS:
            return {"insights": ["Key facts and decisions have been captured.", "Workspace is ready for human or agent review."]}
        if synthesis_type == SynthesisType.RISKS:
            return {"risks": detector_output["unresolved_questions"]}
        if synthesis_type == SynthesisType.EXECUTIVE_BRIEF:
            return {"brief": "This workspace reflects the current state of reasoning, decisions, and unresolved questions for executive review."}
        return {"text": "No synthesis available."}

    async def _next_version(self, workspace_id: str, synthesis_type: SynthesisType) -> int:
        latest = await self.get_latest_synthesis(workspace_id, synthesis_type)
        return 1 if latest is None else latest.version + 1

    async def _persist_synthesis(self, workspace_id: str, synthesis_type: SynthesisType, content: Dict[str, Any], source_model: str, generated_by: str, version: int) -> WorkspaceSynthesisRead:
        payload = {
            "workspace_id": workspace_id,
            "synthesis_type": synthesis_type.value,
            "content": content,
            "source_model": source_model,
            "generated_by": generated_by,
            "version": version,
        }
        result = self.supabase.table("workspace_syntheses").insert(payload).execute()
        return WorkspaceSynthesisRead.model_validate(result.data[0])
