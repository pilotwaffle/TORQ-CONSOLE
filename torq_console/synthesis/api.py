from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from torq_console.synthesis.models import GenerateSynthesisRequest, SynthesisType
from torq_console.synthesis.service import SynthesisService


router = APIRouter(prefix="/api/workspaces/{workspace_id}/syntheses", tags=["workspace-syntheses"])


def get_synthesis_service() -> SynthesisService:
    from torq_console.dependencies import get_optional_llm_client, get_supabase_client
    from torq_console.workspace.service import WorkspaceService

    supabase = get_supabase_client()
    workspace_service = WorkspaceService(supabase, get_optional_llm_client())
    return SynthesisService(supabase, workspace_service, get_optional_llm_client())


@router.post("/generate")
async def generate_syntheses(workspace_id: str, payload: GenerateSynthesisRequest, service: SynthesisService = Depends(get_synthesis_service)):
    return await service.generate_syntheses(workspace_id, payload)


@router.get("")
async def list_syntheses(workspace_id: str, service: SynthesisService = Depends(get_synthesis_service)):
    return await service.list_syntheses(workspace_id)


@router.get("/latest")
async def get_latest_synthesis(workspace_id: str, type: SynthesisType, service: SynthesisService = Depends(get_synthesis_service)):
    synthesis = await service.get_latest_synthesis(workspace_id, type)
    if not synthesis:
        raise HTTPException(status_code=404, detail="Synthesis not found")
    return synthesis


@router.post("/regenerate")
async def regenerate_syntheses(workspace_id: str, payload: GenerateSynthesisRequest, service: SynthesisService = Depends(get_synthesis_service)):
    payload.force_regenerate = True
    return await service.generate_syntheses(workspace_id, payload)
