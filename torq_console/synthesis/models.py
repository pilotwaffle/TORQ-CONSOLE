from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SynthesisType(str, Enum):
    SUMMARY = "summary"
    INSIGHTS = "insights"
    RISKS = "risks"
    CONTRADICTIONS = "contradictions"
    NEXT_ACTIONS = "next_actions"
    EXECUTIVE_BRIEF = "executive_brief"


class WorkspaceSynthesisRead(BaseModel):
    synthesis_id: str
    workspace_id: str
    synthesis_type: SynthesisType
    content: Dict[str, Any]
    source_model: Optional[str] = None
    generated_by: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime


class GenerateSynthesisRequest(BaseModel):
    types: List[SynthesisType] = Field(default_factory=lambda: [SynthesisType.SUMMARY])
    model: Optional[str] = None
    force_regenerate: bool = False


class GenerateSynthesisResponse(BaseModel):
    workspace_id: str
    results: List[WorkspaceSynthesisRead]
